import pytest
import requests_mock

from nldcsc.http_apis.viper.auth import ViperTokenRenewed
from nldcsc.http_apis.viper.client import ViperClient
from nldcsc.http_apis.viper.collections.connectors import InvalidBatchResponse
from nldcsc.http_apis.viper.objects import BatchSearchQuery

BASE = "http://viper"
BATCH = f"{BASE}/v1/connectors/batch_search"
REFRESH = f"{BASE}/v1/auth/refresh_token"
SEARCH_ID = "2df85941-75fc-4689-9a67-b3e978826500"
TOKEN_FAILURE = {
    "error": {
        "code": "TOKEN_FAILURE",
        "message": "Token expired.",
        "request_id": "request",
        "status_code": 401,
    }
}


def token(access="first"):
    return {
        "access_token": access,
        "expires_in": 300,
        "refresh_token": "refresh",
        "refresh_expires_in": 1800,
        "token_type": "Bearer",
        "id_token": "id",
        "scope": "openid",
        "session_state": "state",
    }


def started(connector_id="storm", search_id=SEARCH_ID):
    return {
        "connector_id": connector_id,
        "status_code": 201,
        "search": {"id": search_id, "created": 1},
    }


@pytest.fixture
def mock():
    with requests_mock.Mocker() as mocker:
        mocker.post(f"{BASE}/v1/auth/login", json=token())
        yield mocker


@pytest.fixture
def client():
    return ViperClient(BASE, auth=("user", "password"))


def test_sends_searches_as_json_to_the_batch_route(client, mock):
    mock.post(BATCH, json={"searches": [started()]})

    client.v1.connectors.batch_search([BatchSearchQuery("storm", "hostname", "server")])

    assert mock.last_request.json() == {
        "searches": [
            {
                "connector_id": "storm",
                "field": "hostname",
                "value": "server",
                "page": 0,
                "size": 10,
            }
        ]
    }


def test_returns_typed_outcomes_with_normalised_search_ids(client, mock):
    disabled = {
        "connector_id": "snow",
        "status_code": 409,
        "error": {"code": "connector_disabled", "message": "Disabled."},
    }
    mock.post(
        BATCH, json={"searches": [started(search_id=SEARCH_ID.upper()), disabled]}
    )

    response = client.v1.connectors.batch_search(
        [{"connector_id": "storm"}, {"connector_id": "snow"}]
    )

    first, second = response.searches
    assert first.started and first.search.id == SEARCH_ID
    assert not second.started and second.error_code == "connector_disabled"


@pytest.mark.parametrize("status", [400, 599])
def test_accepts_every_error_status_viper_can_return(client, mock, status):
    mock.post(
        BATCH, json={"searches": [{"connector_id": "storm", "status_code": status}]}
    )

    response = client.v1.connectors.batch_search([{"connector_id": "storm"}])

    assert response.searches[0].status_code == status


@pytest.mark.parametrize(
    "reply",
    [
        {"searches": []},
        {"searches": [started("snow")]},
        {"searches": [{"connector_id": "storm", "status_code": 200}]},
        {"searches": [{"connector_id": "storm", "status_code": 600}]},
        {"searches": [{**started(), "error": "Unexpected."}]},
        {"searches": [{**started(), "search": {"id": "not-a-uuid", "created": 1}}]},
        {"searches": [{**started(), "search": {"id": SEARCH_ID, "created": True}}]},
        {
            "searches": [
                {
                    "connector_id": "storm",
                    "status_code": 403,
                    "search": started()["search"],
                }
            ]
        },
    ],
)
def test_rejects_any_reply_that_does_not_match_the_searches(client, mock, reply):
    mock.post(BATCH, json=reply)

    with pytest.raises(InvalidBatchResponse):
        client.v1.connectors.batch_search([{"connector_id": "storm"}])


def test_rejects_the_same_search_id_twice(client, mock):
    mock.post(BATCH, json={"searches": [started(), started()]})

    with pytest.raises(InvalidBatchResponse):
        client.v1.connectors.batch_search(
            [{"connector_id": "storm"}, {"connector_id": "storm"}]
        )


@pytest.mark.parametrize("count", [0, 21])
def test_refuses_zero_or_more_than_twenty_searches_without_sending(client, mock, count):
    with pytest.raises(ValueError):
        client.v1.connectors.batch_search([{"connector_id": "storm"}] * count)

    assert not mock.called


def test_token_failure_renews_token_but_never_resends_the_batch(client, mock):
    mock.post(BATCH, status_code=401, json=TOKEN_FAILURE)
    mock.post(REFRESH, json=token("second"))

    with pytest.raises(ViperTokenRenewed):
        client.v1.connectors.batch_search([{"connector_id": "storm"}])

    assert [request.path for request in mock.request_history] == [
        "/v1/auth/login",
        "/v1/connectors/batch_search",
        "/v1/auth/refresh_token",
    ]


def test_token_failure_still_resends_ordinary_reads(client, mock):
    status = f"{BASE}/v1/async_search/{SEARCH_ID}"
    mock.get(
        status,
        [{"status_code": 401, "json": TOKEN_FAILURE}, {"json": {"id": SEARCH_ID}}],
    )
    mock.post(REFRESH, json=token("second"))

    assert client.v1.async_search.get(SEARCH_ID).id == SEARCH_ID

    assert mock.last_request.headers["Authorization"] == "Bearer second"
