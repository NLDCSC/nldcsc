from unittest.mock import Mock

import jwt
import pytest
import requests
from flask import Flask, session

from nldcsc.sso.flask_sso import SSOConnection
from nldcsc.sso.monkey_patch.ssl_verification import (
    do_ssl_verification,
    ssl_verification,
)


class OAuthClient:
    def __init__(self):
        self.authorize_redirect = Mock(return_value="login redirect")
        self.authorize_access_token = Mock(return_value={"access_token": "token"})
        self.userinfo = Mock(return_value={"name": "Ada"})
        self.load_server_metadata = Mock(return_value={})
        self.ensure_active_token = Mock(return_value=True)

    def _get_oauth_client(self, **metadata):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class OAuthFactory:
    def __init__(self, app):
        self.sso = OAuthClient()

    def register(self, **kwargs):
        self.registered = kwargs
        return self.sso


@pytest.fixture
def sso_app(monkeypatch):
    monkeypatch.setattr("nldcsc.sso.flask_sso.OAuth", OAuthFactory)
    monkeypatch.setattr(
        SSOConnection,
        "get_config_setting",
        Mock(return_value="https://issuer.test/endpoint"),
    )
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config.update(
        SSO_DISCOVERY_URL="https://issuer.test/.well-known",
        SSO_USERINFO_ENDPOINT="https://issuer.test/userinfo",
        SSO_ENDSESSION_ENDPOINT="https://issuer.test/logout",
        SSO_SCOPES=["openid", "profile"],
        SSO_OVERWRITE_REDIRECT_URI="https://app.test/callback",
        SSO_CALLBACK_ENDPOINT=None,
        SSO_USER_INFO_ENABLED=True,
    )
    connection = SSOConnection(app, prefix="/auth")
    return app, connection, connection.oauth.sso


def test_ssl_context_overrides_verification_and_restores_requests(monkeypatch):
    original = requests.Session.merge_environment_settings
    adapter = Mock()
    session_obj = requests.Session()
    monkeypatch.setattr(session_obj, "get_adapter", Mock(return_value=adapter))

    with do_ssl_verification(cert_check=False):
        settings = session_obj.merge_environment_settings(
            "https://example.test", {}, False, True, None
        )
        assert settings["verify"] is False

    assert requests.Session.merge_environment_settings is original
    adapter.close.assert_called_once()


def test_ssl_decorator_returns_wrapped_function_result(monkeypatch):
    monkeypatch.setenv("SSO_TLS_VERIFICATION", "False")

    @ssl_verification
    def operation(value):
        return value * 2

    assert operation(4) == 8
    assert operation.__name__ == "operation"


def test_sso_initializes_config_and_oauth_client(sso_app):
    app, connection, oauth_client = sso_app

    assert connection.app is app
    assert app.config["SSO_CLIENT_ID"] == "sso-client"
    assert app.config["SSO_SCOPES"] == ["openid", "profile"]
    assert connection.oauth.registered["client_kwargs"]["scope"] == "openid profile"
    assert repr(connection) == "<< SSOConnection >>"
    assert oauth_client is connection.oauth.sso


def test_sso_rejects_scopes_without_openid(monkeypatch):
    monkeypatch.setattr("nldcsc.sso.flask_sso.OAuth", OAuthFactory)
    monkeypatch.setattr(
        SSOConnection,
        "get_config_setting",
        Mock(return_value="https://issuer.test/endpoint"),
    )
    app = Flask(__name__)
    app.config.update(
        SSO_DISCOVERY_URL="https://issuer.test/.well-known",
        SSO_USERINFO_ENDPOINT="https://issuer.test/userinfo",
        SSO_ENDSESSION_ENDPOINT="https://issuer.test/logout",
        SSO_SCOPES=["profile"],
    )

    with pytest.raises(ValueError, match="openid"):
        SSOConnection(app)


def test_login_guard_and_user_session_helpers(sso_app):
    app, connection, _ = sso_app

    @connection.require_login
    def private_page():
        return "private"

    app.add_url_rule("/private", view_func=private_page)
    client = app.test_client()

    response = client.get("/private")
    assert response.status_code == 302
    assert "/auth/sso_login" in response.location

    with client.session_transaction() as browser_session:
        browser_session["sso_auth_token"] = {
            "access_token": "token",
            "refresh_token": "refresh",
        }
        browser_session["sso_auth_profile"] = {"name": "Ada"}

    response = client.get("/private")
    assert response.data == b"private"

    with app.test_request_context("/"):
        session["sso_auth_token"] = {
            "access_token": "token",
            "refresh_token": "refresh",
        }
        session["sso_auth_profile"] = {"name": "Ada"}
        assert connection.user_loggedin is True
        assert connection.user_getinfo() == {"name": "Ada"}
        assert connection.user_getfield("name") == "Ada"
        assert connection.get_access_token() == "token"
        assert connection.get_refresh_token() == "refresh"


def test_user_helpers_report_missing_authentication_and_fields(sso_app):
    app, connection, _ = sso_app

    with app.test_request_context("/"):
        with pytest.raises(Exception) as error:
            connection.user_getinfo()
        assert getattr(error.value, "code", None) == 401
        with pytest.raises(AttributeError, match="missing"):
            connection.user_getfield("missing")


def test_access_token_fields_are_read_from_unsigned_jwt(sso_app):
    app, connection, _ = sso_app
    token = jwt.encode({"role": "admin"}, "x" * 32, algorithm="HS256")

    with app.test_request_context("/"):
        session["sso_auth_token"] = {"access_token": token}
        assert connection.access_token_getfield("role") == "admin"
        with pytest.raises(AttributeError, match="missing"):
            connection.access_token_getfield("missing")


def test_login_and_authorize_routes_store_tokens_and_profile(sso_app):
    app, _, oauth_client = sso_app
    client = app.test_client()

    response = client.get("/auth/sso_login?next=%2Fwelcome")
    assert response.data == b"login redirect"
    oauth_client.authorize_redirect.assert_called_once_with("https://app.test/callback")

    response = client.get("/auth/sso_authorize")
    assert response.status_code == 302
    assert response.location == "/welcome"
    oauth_client.authorize_access_token.assert_called_once()
    oauth_client.userinfo.assert_called_once_with(token={"access_token": "token"})
