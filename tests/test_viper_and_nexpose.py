from types import SimpleNamespace
import time
from unittest.mock import Mock

import pytest
import requests

from nldcsc.http_apis.nexpose.client import NexposeClient
from nldcsc.http_apis.nexpose.objects import (
    NexposeAssets,
    NexposePage,
    NexposeResource,
)
from nldcsc.http_apis.viper.auth import AuthInfo, ViperAuth
from nldcsc.http_apis.viper.client import ViperClient
from nldcsc.http_apis.viper.collections.auth.objects import AuthResponse
from nldcsc.http_apis.viper.collections.bases import EndpointCollection, PaginatedResponse
from nldcsc.http_apis.viper.collections.utils import as_object


def auth_response(
    access_token="access",
    expires_in=600,
    refresh_token="refresh",
    refresh_expires_in=3600,
):
    return AuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refresh_token,
        refresh_expires_in=refresh_expires_in,
        token_type="Bearer",
        id_token="id",
        scope="openid",
        session_state="state",
    )


def test_viper_auth_info_updates_and_expires_tokens(monkeypatch):
    monkeypatch.setattr("nldcsc.http_apis.viper.auth.time.time", lambda: 100)
    info = AuthInfo(username="user", password="password")
    info.update_with_response(auth_response())

    assert info.access_token == "access"
    assert info.refresh_token == "refresh"
    assert info.valid() is True
    assert info.refresh_valid() is True

    monkeypatch.setattr("nldcsc.http_apis.viper.auth.time.time", lambda: 4000)
    assert info.valid() is False
    assert info.refresh_valid() is False


def test_viper_auth_logs_in_then_refreshes_and_sets_request_header():
    login = Mock(return_value=auth_response())
    refresh = Mock(return_value=auth_response(access_token="refreshed"))
    auth = ViperAuth(("user", "password"), login, refresh)
    request = requests.Request("GET", "https://example.test").prepare()

    auth(request)
    assert request.headers["Authorization"] == "Bearer access"
    login.assert_called_once()

    auth.auth_info.access_expiry = 0
    auth.auth_info.refresh_expiry = 3600
    auth.auth_info.last_updated = int(time.time())
    request = requests.Request("GET", "https://example.test").prepare()
    auth(request)
    assert request.headers["Authorization"] == "Bearer refreshed"
    refresh.assert_called_once_with(refresh_token="refresh")


def test_viper_auth_wrapper_retries_token_failures_only():
    login = Mock(return_value=auth_response())
    refresh = Mock(return_value=auth_response(access_token="new"))
    auth = ViperAuth(("user", "password"), login, refresh)
    auth.auth_info.update_with_response(auth_response())

    failure = requests.Response()
    failure.status_code = 401
    failure._content = (
        b'{"error":{"code":"TOKEN_FAILURE","message":"expired",'
        b'"request_id":"r1","status_code":401}}'
    )
    http_error = requests.HTTPError(response=failure)
    calls = []

    def request(resource, auth=None):
        calls.append(auth)
        if len(calls) == 1:
            raise http_error
        return "ok"

    wrapped = auth.auth_wrap(request)
    assert wrapped("/resource") == "ok"
    assert calls == [auth, auth]
    assert auth.auth_wrap(wrapped) is wrapped

    def forbidden(resource, auth=None):
        error = requests.Response()
        error.status_code = 403
        raise requests.HTTPError(response=error)

    with pytest.raises(requests.HTTPError):
        auth.auth_wrap(forbidden)("/resource")


def test_viper_client_builds_collection_paths_and_objects():
    client = ViperClient("https://viper.test", auth=("user", "password"))
    client.call = Mock(
        return_value={
            "access_token": "access",
            "expires_in": 600,
            "refresh_token": "refresh",
            "refresh_expires_in": 3600,
            "token_type": "Bearer",
            "id_token": "id",
            "scope": "openid",
            "session_state": "state",
        }
    )

    assert client.v1.prefix == "v1"
    assert client.v1.auth.prefix == "v1/auth"
    response = client.v1.auth.login("user", "password")

    assert isinstance(response, AuthResponse)
    assert response.access_token == "access"
    assert client.call.call_args.args[:2] == ("post", "v1/auth/login")
    assert client.unversioned.prefix == ""


def test_endpoint_collection_builds_paths_and_iterates_all_pages():
    class Child(EndpointCollection, prefix="/child/"):
        pass

    client = SimpleNamespace(methods=("GET", "POST"), call=Mock(return_value="ok"))
    collection = Child(client, prefix="/parent/")

    assert collection.prefix == "parent/child"
    assert collection._build_resource_path("/items") == "parent/child/items"
    assert collection.call("GET", "/items") == "ok"
    client.call.assert_called_once_with("GET", "parent/child/items")

    pages = {
        0: PaginatedResponse(total=3, page=0, size=2, pages=1, items=["a", "b"]),
        1: PaginatedResponse(total=3, page=1, size=2, pages=1, items=["c"]),
    }
    assert list(collection.iter_endpoint(lambda page, size: pages[page], 0, 2)) == [
        "a",
        "b",
        "c",
    ]


def test_viper_as_object_wraps_conversion_errors():
    @as_object(dict)
    def endpoint():
        return "not a mapping"

    with pytest.raises(ValueError, match="Failed transforming response"):
        endpoint()


def test_nexpose_client_builds_params_and_paginates_resources():
    client = NexposeClient("https://nexpose.test", api_path="api/3")
    assert client._pss_to_params(2, 5, [("risk", "DESC")]) == {
        "page": 2,
        "size": 5,
        "sort": ["risk,DESC"],
    }

    responses = [
        SimpleNamespace(
            resources=[1, 2],
            page=SimpleNamespace(total_pages=2),
        ),
        SimpleNamespace(
            resources=[3],
            page=SimpleNamespace(total_pages=2),
        ),
    ]
    source = Mock(side_effect=responses)
    assert list(client._iter_pages(source, offset=1, batch_size=2)) == [2, 3]
    assert [call.kwargs["page"] for call in source.call_args_list] == [0, 1]


def test_nexpose_client_decodes_page_and_single_resource_responses():
    client = NexposeClient("https://nexpose.test", api_path="api/3")
    client.call = Mock(
        side_effect=[
            {
                "links": [],
                "page": {
                    "number": 0,
                    "size": 1,
                    "total_pages": 1,
                    "total_resources": 1,
                },
                "resources": [{"id": 7, "ip": "192.0.2.7"}],
            },
            {"id": 8, "ip": "192.0.2.8"},
        ]
    )

    assets = client.get_assets(page=0, size=1, sorting=[("ip", "ASC")])
    asset = client.get_asset(8)

    assert isinstance(assets, NexposeAssets)
    assert isinstance(assets.page, NexposePage)
    assert isinstance(assets.resources[0], NexposeResource)
    assert assets.resources[0].ip == "192.0.2.7"
    assert asset.id == 8
    assert client.call.call_args_list[0].kwargs["params"]["sort"] == ["ip,ASC"]
    assert client.call.call_args_list[1].args[1] == "assets/8"


def test_nexpose_search_uses_post_for_filters_and_surfaces_invalid_models():
    client = NexposeClient("https://nexpose.test")
    client.call = Mock(
        return_value={
            "links": [],
            "page": {"number": 0, "size": 0, "total_pages": 0, "total_resources": 0},
            "resources": [],
        }
    )

    client.get_assets(filters=[{"field": "risk", "operator": "IS", "value": "high"}])
    assert client.call.call_args.args[:2] == ("post", "assets/search")

    client.call.return_value = {"resources": "invalid"}
    with pytest.raises(ValueError, match="Failed transforming response"):
        client.get_assets()
