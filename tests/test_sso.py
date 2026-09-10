import warnings

import jwt
import mock
import pytest
import requests
from authlib.integrations.base_client import InvalidTokenError
from authlib.integrations.base_client.errors import OAuthError
from authlib.oauth2.rfc6749 import OAuth2Token
from flask import Flask, g, get_flashed_messages, request, session, url_for
from urllib3.exceptions import InsecureRequestWarning
from werkzeug.exceptions import HTTPException

from nldcsc.sso.flask_sso import IntrospectTokenValidator, SSOConnection
from nldcsc.sso.flask_sso.sso_views import (
    sso_auth,
    sso_authorize,
    sso_login,
    sso_logout,
)
from nldcsc.sso.monkey_patch.ssl_verification import (
    do_ssl_verification,
    old_merge_environment_settings,
    ssl_verification,
)


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    return app


@pytest.fixture
def mocked_discovery():
    with mock.patch.object(
        SSOConnection,
        "get_config_setting",
        return_value="https://issuer.example/mocked-endpoint",
    ) as m:
        yield m


class TestInit:
    def test_without_app_leaves_app_and_oauth_none(self):
        sso = SSOConnection()

        assert sso.app is None
        assert sso.oauth is None

    def test_registers_bearer_introspect_validator(self):
        sso = SSOConnection()

        assert isinstance(
            sso.accept_token._token_validators["bearer"], IntrospectTokenValidator
        )

    def test_names_logger_after_module(self):
        sso = SSOConnection()

        assert sso.logger.name == "nldcsc.sso.flask_sso"

    def test_with_app_calls_init_app(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        assert sso.app is flask_app
        assert sso.oauth is not None


class TestIntrospectTokenValidator:
    def test_raises_when_introspection_endpoint_missing(self, flask_app):
        validator = IntrospectTokenValidator()

        with flask_app.test_request_context("/"):
            g._sso_auth = mock.Mock()
            g._sso_auth.load_server_metadata.return_value = {}

            with pytest.raises(
                RuntimeError,
                match=(
                    "Can't validate the token because the server does not support "
                    "introspection."
                ),
            ):
                validator.introspect_token("token123")

    def test_returns_json_response_from_introspection_endpoint(self, flask_app):
        validator = IntrospectTokenValidator()

        with flask_app.test_request_context("/"):
            oauth_mock = mock.MagicMock()
            oauth_mock.load_server_metadata.return_value = {
                "introspection_endpoint": "https://issuer.example/introspect"
            }
            session_mock = mock.Mock()
            session_mock.introspect_token.return_value.json.return_value = {
                "active": True
            }
            oauth_mock._get_oauth_client.return_value.__enter__.return_value = (
                session_mock
            )
            g._sso_auth = oauth_mock

            result = validator.introspect_token("token123")

        assert result == {"active": True}
        session_mock.introspect_token.assert_called_once_with(
            "https://issuer.example/introspect", token="token123"
        )


class TestInitApp:
    def test_sets_default_client_credentials(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_CLIENT_ID"] == "sso-client"
        assert flask_app.config["SSO_CLIENT_SECRET"] == "secret!"

    def test_default_scopes_include_openid_profile_email(
        self, flask_app, mocked_discovery
    ):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_SCOPES"] == ["openid", "profile", "email"]

    def test_raises_when_openid_scope_missing(self, flask_app, mocked_discovery):
        flask_app.config["SSO_SCOPES"] = ["profile", "email"]

        with pytest.raises(ValueError, match="openid"):
            SSOConnection(flask_app)

    def test_defaults_code_challenge_method_to_s256(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_CODE_CHALLENGE_METHOD"] == "S256"

    def test_defaults_user_info_enabled_true(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_USER_INFO_ENABLED"] is True

    def test_registers_blueprint_routes_under_prefix(self, flask_app, mocked_discovery):
        SSOConnection(flask_app, prefix="/auth")

        rules = {rule.rule for rule in flask_app.url_map.iter_rules()}

        assert "/auth/sso_login" in rules
        assert "/auth/sso_authorize" in rules
        assert "/auth/sso_logout" in rules

    def test_registers_before_request_hook(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.before_request_funcs[None]

    def test_looks_up_userinfo_and_endsession_endpoints_via_discovery(
        self, flask_app, mocked_discovery
    ):
        SSOConnection(flask_app)

        mocked_discovery.assert_any_call("userinfo_endpoint")
        mocked_discovery.assert_any_call("end_session_endpoint")

    def test_registers_oauth_client_with_configured_scopes_and_method(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        assert sso.oauth.sso.client_id == flask_app.config["SSO_CLIENT_ID"]
        assert sso.oauth.sso.client_kwargs["scope"] == "openid profile email"
        assert sso.oauth.sso.client_kwargs["code_challenge_method"] == "S256"
        assert (
            sso.oauth.sso.client_kwargs["token_endpoint_auth_method"]
            == "client_secret_post"
        )

    def test_configures_redis_backed_session_when_enabled(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("REDIS_SESSION_STORAGE", "True")

        with mock.patch("nldcsc.sso.flask_sso.redis.from_url") as from_url, mock.patch(
            "nldcsc.sso.flask_sso.Session"
        ) as session_cls:
            SSOConnection(flask_app)

        assert flask_app.config["SESSION_TYPE"] == "redis"
        from_url.assert_called_once()
        session_cls.assert_called_once_with(flask_app)

    def test_skips_redis_session_setup_by_default(self, flask_app, mocked_discovery):
        with mock.patch("nldcsc.sso.flask_sso.Session") as session_cls:
            SSOConnection(flask_app)

        session_cls.assert_not_called()
        assert "SESSION_TYPE" not in flask_app.config

    def test_stores_redis_client_and_starts_flask_session_when_enabled(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("REDIS_SESSION_STORAGE", "True")
        monkeypatch.setenv("REDIS_URL", "redis://custom-host:1234/")

        with mock.patch("nldcsc.sso.flask_sso.redis.from_url") as from_url, mock.patch(
            "nldcsc.sso.flask_sso.Session"
        ) as session_cls:
            SSOConnection(flask_app)

        from_url.assert_called_once_with("redis://custom-host:1234/")
        assert flask_app.config["SESSION_REDIS"] is from_url.return_value
        session_cls.assert_called_once_with(flask_app)

    def test_defaults_redis_url_when_not_configured(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("REDIS_SESSION_STORAGE", "True")
        monkeypatch.delenv("REDIS_URL", raising=False)

        with mock.patch("nldcsc.sso.flask_sso.redis.from_url") as from_url, mock.patch(
            "nldcsc.sso.flask_sso.Session"
        ):
            SSOConnection(flask_app)

        from_url.assert_called_once_with("redis://redis:6379/")

    def test_registers_oauth_client_secret_and_update_token_callback(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        assert sso.oauth.sso.client_secret == flask_app.config["SSO_CLIENT_SECRET"]
        assert sso.oauth.sso._server_metadata_url == flask_app.config[
            "SSO_DISCOVERY_URL"
        ]
        assert sso.oauth.sso._update_token == sso._update_token

    def test_registers_exact_before_request_callback(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        assert sso._before_request in flask_app.before_request_funcs[None]

    @pytest.mark.parametrize(
        ("env_var", "config_key", "value"),
        [
            ("SSO_CLIENT_ID", "SSO_CLIENT_ID", "custom-client-id"),
            ("SSO_CLIENT_SECRET", "SSO_CLIENT_SECRET", "custom-client-secret"),
            ("SSO_ISSUER", "SSO_ISSUER", "https://issuer.example/custom"),
            (
                "SSO_DISCOVERY_URL",
                "SSO_DISCOVERY_URL",
                "https://issuer.example/custom/.well-known/openid-configuration",
            ),
            (
                "SSO_CODE_CHALLENGE_METHOD",
                "SSO_CODE_CHALLENGE_METHOD",
                "plain",
            ),
            (
                "SSO_OVERWRITE_REDIRECT_URI",
                "SSO_OVERWRITE_REDIRECT_URI",
                "https://issuer.example/callback",
            ),
            ("SSO_CALLBACK_ENDPOINT", "SSO_CALLBACK_ENDPOINT", "app/callback"),
            (
                "SSO_TOKEN_ENDPOINT_AUTH_METHOD",
                "SSO_TOKEN_ENDPOINT_AUTH_METHOD",
                "client_secret_basic",
            ),
        ],
    )
    def test_reads_config_value_from_its_matching_env_var(
        self, flask_app, mocked_discovery, monkeypatch, env_var, config_key, value
    ):
        monkeypatch.setenv(env_var, value)

        SSOConnection(flask_app)

        assert flask_app.config[config_key] == value

    def test_reads_userinfo_endpoint_from_its_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv(
            "SSO_USERINFO_ENDPOINT", "https://issuer.example/custom-userinfo"
        )

        SSOConnection(flask_app)

        assert (
            flask_app.config["SSO_USERINFO_ENDPOINT"]
            == "https://issuer.example/custom-userinfo"
        )

    def test_reads_endsession_endpoint_from_its_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv(
            "SSO_ENDSESSION_ENDPOINT", "https://issuer.example/custom-logout"
        )

        SSOConnection(flask_app)

        assert (
            flask_app.config["SSO_ENDSESSION_ENDPOINT"]
            == "https://issuer.example/custom-logout"
        )

    def test_reads_scopes_from_their_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_SCOPES", '["openid", "email"]')

        SSOConnection(flask_app)

        assert flask_app.config["SSO_SCOPES"] == ["openid", "email"]

    def test_reads_discovery_kwargs_from_their_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_DISCOVERY_KWARGS", '{"timeout": 7}')

        SSOConnection(flask_app)

        assert flask_app.config["SSO_DISCOVERY_KWARGS"] == {"timeout": 7}

    def test_defaults_discovery_kwargs_to_empty_dict(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_DISCOVERY_KWARGS"] == {}

    def test_defaults_issuer_to_empty_string(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_ISSUER"] == ""

    def test_builds_discovery_url_from_issuer_by_default(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_ISSUER", "https://issuer.example")

        SSOConnection(flask_app)

        assert (
            flask_app.config["SSO_DISCOVERY_URL"]
            == "https://issuer.example/.well-known/openid-configuration"
        )

    def test_defaults_overwrite_redirect_uri_to_none(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_OVERWRITE_REDIRECT_URI"] is None

    def test_defaults_callback_endpoint_to_none(self, flask_app, mocked_discovery):
        SSOConnection(flask_app)

        assert flask_app.config["SSO_CALLBACK_ENDPOINT"] is None

    def test_defaults_token_endpoint_auth_method_to_client_secret_post(
        self, flask_app, mocked_discovery
    ):
        SSOConnection(flask_app)

        assert (
            flask_app.config["SSO_TOKEN_ENDPOINT_AUTH_METHOD"] == "client_secret_post"
        )

    def test_reads_tls_verification_from_its_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_TLS_VERIFICATION", "False")

        SSOConnection(flask_app)

        assert flask_app.config["SSO_TLS_VERIFICATION"] is False

    def test_raises_when_openid_scope_missing_from_env_var_scopes(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_SCOPES", '["profile", "email"]')

        with pytest.raises(ValueError) as excinfo:
            SSOConnection(flask_app)

        assert str(excinfo.value) == 'The value "openid" must be in the SSO_SCOPES'

    def test_reads_user_info_enabled_from_its_env_var(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.setenv("SSO_USER_INFO_ENABLED", "False")

        SSOConnection(flask_app)

        assert flask_app.config["SSO_USER_INFO_ENABLED"] is False

    def test_defaults_tls_verification_to_true(
        self, flask_app, mocked_discovery, monkeypatch
    ):
        monkeypatch.delenv("SSO_TLS_VERIFICATION", raising=False)

        SSOConnection(flask_app)

        assert flask_app.config["SSO_TLS_VERIFICATION"] is True


class TestBeforeRequest:
    def test_sets_g_sso_auth_and_delegates_to_check_token_expiry(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            with mock.patch.object(
                sso, "check_token_expiry", return_value="sentinel"
            ) as check:
                result = sso._before_request()

            assert g._sso_auth is sso.oauth.sso
        check.assert_called_once()
        assert result == "sentinel"


class TestCheckTokenExpiry:
    def test_returns_none_when_no_token_in_session(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            assert sso.check_token_expiry() is None

    def test_returns_none_on_logout_path_to_avoid_redirect_loop(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/sso_logout"):
            session["sso_auth_token"] = {"access_token": "abc", "token_type": "Bearer"}

            assert sso.check_token_expiry() is None

    def test_returns_none_when_token_still_active(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/protected"):
            session["sso_auth_token"] = {"access_token": "abc", "token_type": "Bearer"}

            with mock.patch.object(sso, "ensure_active_token", return_value=None):
                assert sso.check_token_expiry() is None

    def test_redirects_to_logout_when_token_refresh_fails(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/protected"):
            session["sso_auth_token"] = {"access_token": "abc", "token_type": "Bearer"}

            with mock.patch.object(
                sso, "ensure_active_token", side_effect=InvalidTokenError()
            ):
                response = sso.check_token_expiry()

        assert response.status_code == 302
        assert response.location == "/sso_logout?reason=expired"

    def test_aborts_500_on_unexpected_error(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/protected"):
            session["sso_auth_token"] = {"access_token": "abc", "token_type": "Bearer"}

            with mock.patch(
                "nldcsc.sso.flask_sso.OAuth2Token.from_dict",
                side_effect=ValueError("bad token"),
            ):
                with pytest.raises(HTTPException) as excinfo:
                    sso.check_token_expiry()

        assert excinfo.value.code == 500


class TestEnsureActiveToken:
    def test_returns_refreshed_token_result(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)
        token = OAuth2Token({"access_token": "abc", "token_type": "Bearer"})
        session_mock = mock.Mock()
        session_mock.ensure_active_token.return_value = token

        with mock.patch.object(
            sso.oauth.sso, "load_server_metadata", return_value={}
        ), mock.patch.object(sso.oauth.sso, "_get_oauth_client") as get_client:
            get_client.return_value.__enter__.return_value = session_mock

            result = sso.ensure_active_token(token)

        assert result is token

    def test_raises_invalid_token_error_when_ensure_returns_none(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)
        token = OAuth2Token({"access_token": "abc", "token_type": "Bearer"})
        session_mock = mock.Mock()
        session_mock.ensure_active_token.return_value = None

        with mock.patch.object(
            sso.oauth.sso, "load_server_metadata", return_value={}
        ), mock.patch.object(sso.oauth.sso, "_get_oauth_client") as get_client:
            get_client.return_value.__enter__.return_value = session_mock

            with pytest.raises(InvalidTokenError):
                sso.ensure_active_token(token)


class TestUserLoggedIn:
    def test_true_when_token_in_session(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {"access_token": "abc"}

            assert sso.user_loggedin is True

    def test_false_when_no_token(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            assert sso.user_loggedin is False


class TestUserGetInfo:
    def test_returns_profile_when_logged_in(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {"access_token": "abc"}
            session["sso_auth_profile"] = {"sub": "123"}

            assert sso.user_getinfo() == {"sub": "123"}

    def test_defaults_to_empty_dict_when_profile_missing(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {"access_token": "abc"}

            assert sso.user_getinfo() == {}

    def test_aborts_401_when_not_logged_in(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            with pytest.raises(HTTPException) as excinfo:
                sso.user_getinfo()

        assert excinfo.value.code == 401
        assert excinfo.value.description == "User was not authenticated"


class TestUserGetField:
    def test_returns_requested_field(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_profile"] = {"email": "jdoe@example.com"}

            assert sso.user_getfield("email") == "jdoe@example.com"

    def test_raises_attribute_error_when_field_missing(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_profile"] = {}

            with pytest.raises(AttributeError, match="email"):
                sso.user_getfield("email")

    def test_raises_attribute_error_when_profile_entirely_absent(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            with pytest.raises(
                AttributeError,
                match="Could not retrieve email from sso_auth_profile",
            ):
                sso.user_getfield("email")


class TestGetConfigSetting:
    def _bare_connection(self, flask_app):
        sso = SSOConnection.__new__(SSOConnection)
        sso.app = flask_app
        return sso

    def test_returns_parsed_field_from_discovery_document(self, flask_app):
        flask_app.config["SSO_DISCOVERY_URL"] = (
            "https://issuer.example/.well-known/openid-configuration"
        )
        flask_app.config["SSO_DISCOVERY_KWARGS"] = {}
        sso = self._bare_connection(flask_app)

        response = mock.Mock()
        response.json.return_value = {
            "userinfo_endpoint": "https://issuer.example/userinfo"
        }
        with mock.patch("nldcsc.sso.flask_sso.requests.session") as session_ctor:
            session_ctor.return_value.__enter__.return_value.get.return_value = (
                response
            )

            result = sso.get_config_setting("userinfo_endpoint")

        assert result == "https://issuer.example/userinfo"

    def test_passes_discovery_kwargs_and_disables_verification(self, flask_app):
        flask_app.config["SSO_DISCOVERY_URL"] = (
            "https://issuer.example/.well-known/openid-configuration"
        )
        flask_app.config["SSO_DISCOVERY_KWARGS"] = {"timeout": 5}
        sso = self._bare_connection(flask_app)

        response = mock.Mock()
        response.json.return_value = {
            "end_session_endpoint": "https://issuer.example/logout"
        }
        with mock.patch("nldcsc.sso.flask_sso.requests.session") as session_ctor:
            get_mock = session_ctor.return_value.__enter__.return_value.get
            get_mock.return_value = response

            sso.get_config_setting("end_session_endpoint")

        get_mock.assert_called_once_with(
            "https://issuer.example/.well-known/openid-configuration",
            verify=False,
            timeout=5,
        )

    def test_reraises_exception_from_request(self, flask_app):
        flask_app.config["SSO_DISCOVERY_URL"] = (
            "https://issuer.example/.well-known/openid-configuration"
        )
        flask_app.config["SSO_DISCOVERY_KWARGS"] = {}
        sso = self._bare_connection(flask_app)

        with mock.patch("nldcsc.sso.flask_sso.requests.session") as session_ctor:
            session_ctor.return_value.__enter__.return_value.get.side_effect = (
                ConnectionError("boom")
            )

            with pytest.raises(ConnectionError, match="boom"):
                sso.get_config_setting("userinfo_endpoint")


class TestTokenAccessors:
    def test_get_access_token_returns_value_from_session(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {"access_token": "abc123"}

            assert sso.get_access_token() == "abc123"

    def test_get_access_token_returns_none_when_no_token(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            assert sso.get_access_token() is None

    def test_get_refresh_token_returns_value_from_session(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {"refresh_token": "refresh123"}

            assert sso.get_refresh_token() == "refresh123"

    def test_get_refresh_token_returns_none_when_no_token_in_session(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            assert sso.get_refresh_token() is None


class TestExtractJwtPayload:
    def test_decodes_payload_without_verifying_signature(self):
        token = jwt.encode({"sub": "123"}, "a-sufficiently-long-test-signing-secret", algorithm="HS256")

        assert SSOConnection.extract_jwt_payload(token) == {"sub": "123"}


class TestAccessTokenGetField:
    def test_returns_requested_field_from_access_token(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)
        token = jwt.encode(
            {"sub": "123", "email": "jdoe@example.com"}, "a-sufficiently-long-test-signing-secret", algorithm="HS256"
        )

        with mock.patch.object(sso, "get_access_token", return_value=token):
            assert sso.access_token_getfield("email") == "jdoe@example.com"

    def test_raises_attribute_error_when_field_missing(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)
        token = jwt.encode({"sub": "123"}, "a-sufficiently-long-test-signing-secret", algorithm="HS256")

        with mock.patch.object(sso, "get_access_token", return_value=token):
            with pytest.raises(AttributeError, match="email"):
                sso.access_token_getfield("email")


class TestRequireLogin:
    def test_calls_view_when_logged_in(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        @sso.require_login
        def view():
            return "secret-content"

        with flask_app.test_request_context("/protected"):
            session["sso_auth_token"] = {"access_token": "abc"}

            assert view() == "secret-content"

    def test_redirects_to_login_with_next_when_not_logged_in(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        @sso.require_login
        def view():
            return "secret-content"

        with flask_app.test_request_context("/protected"):
            response = view()

        assert response.status_code == 302
        assert "/sso_login" in response.location
        assert "next=" in response.location

    def test_preserves_view_function_name(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        @sso.require_login
        def my_view():
            return "ok"

        assert my_view.__name__ == "my_view"


class TestLogout:
    def test_posts_end_session_request_and_clears_session(
        self, flask_app, mocked_discovery
    ):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            session["sso_auth_token"] = {
                "access_token": "abc",
                "refresh_token": "refresh123",
            }
            session["sso_auth_profile"] = {"sub": "123"}

            with mock.patch("nldcsc.sso.flask_sso.requests.session") as session_ctor:
                post_mock = session_ctor.return_value.__enter__.return_value.post

                sso.logout()

            post_mock.assert_called_once_with(
                flask_app.config["SSO_ENDSESSION_ENDPOINT"],
                data={
                    "client_id": flask_app.config["SSO_CLIENT_ID"],
                    "client_secret": flask_app.config["SSO_CLIENT_SECRET"],
                    "refresh_token": "refresh123",
                },
                headers={
                    "Authorization": "Bearer abc",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                verify=False,
            )
            assert "sso_auth_token" not in session
            assert "sso_auth_profile" not in session
            assert g.sso_id_token is None

    def test_swallows_type_error(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        with flask_app.test_request_context("/"):
            with mock.patch.object(
                sso, "get_access_token", side_effect=TypeError("boom")
            ):
                sso.logout()


class TestUpdateToken:
    def test_stores_token_in_session_and_g(self, flask_app):
        token = {"access_token": "abc"}

        with flask_app.test_request_context("/"):
            SSOConnection._update_token(token)

            assert session["sso_auth_token"] == token
            assert g.sso_id_token == token


class TestRepr:
    def test_repr(self, flask_app, mocked_discovery):
        sso = SSOConnection(flask_app)

        assert repr(sso) == "<< SSOConnection >>"


class TestSsoLogin:
    def _make_app(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.register_blueprint(sso_auth)
        app.config["SSO_OVERWRITE_REDIRECT_URI"] = None
        app.config["SSO_CALLBACK_ENDPOINT"] = None
        return app

    def test_builds_redirect_uri_from_url_for_when_not_overridden(self):
        app = self._make_app()

        with app.test_request_context("/sso_login?next=/dashboard"):
            g._sso_auth = mock.Mock()
            expected_uri = url_for("sso_auth.sso_authorize", _external=True)

            sso_login()

            g._sso_auth.authorize_redirect.assert_called_once_with(expected_uri)
            assert session["next"] == "/dashboard"

    def test_uses_overwrite_redirect_uri_when_configured(self):
        app = self._make_app()
        app.config["SSO_OVERWRITE_REDIRECT_URI"] = "https://override.example/cb"

        with app.test_request_context("/sso_login"):
            g._sso_auth = mock.Mock()

            sso_login()

            g._sso_auth.authorize_redirect.assert_called_once_with(
                "https://override.example/cb"
            )

    def test_uses_callback_endpoint_for_next_when_configured(self):
        app = self._make_app()
        app.config["SSO_CALLBACK_ENDPOINT"] = "app/callback"

        with app.test_request_context("/sso_login"):
            g._sso_auth = mock.Mock()

            sso_login()

            assert session["next"] == f"{request.root_url}app/callback"

    def test_defaults_next_to_root_url_without_query_param(self):
        app = self._make_app()

        with app.test_request_context("/sso_login"):
            g._sso_auth = mock.Mock()

            sso_login()

            assert session["next"] == request.root_url


class TestSsoAuthorize:
    def _make_app(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.register_blueprint(sso_auth)
        app.config["SSO_USER_INFO_ENABLED"] = True
        return app

    def test_stores_token_and_profile_then_redirects_to_next(self):
        app = self._make_app()
        token = {"access_token": "abc"}
        profile = {"sub": "123"}

        with app.test_request_context("/sso_authorize"):
            g._sso_auth = mock.Mock()
            g._sso_auth.authorize_access_token.return_value = token
            g._sso_auth.userinfo.return_value = profile
            session["next"] = "/dashboard"

            response = sso_authorize()

            assert session["sso_auth_token"] == token
            assert session["sso_auth_profile"] == profile
            assert g.sso_id_token == token
            assert "next" not in session

        assert response.status_code == 302
        assert response.location == "/dashboard"

    def test_falls_back_to_root_url_when_next_missing(self):
        app = self._make_app()

        with app.test_request_context("/sso_authorize"):
            g._sso_auth = mock.Mock()
            g._sso_auth.authorize_access_token.return_value = {"access_token": "abc"}
            g._sso_auth.userinfo.return_value = {}
            expected_root = request.root_url

            response = sso_authorize()

        assert response.location == expected_root

    def test_skips_userinfo_when_disabled(self):
        app = self._make_app()
        app.config["SSO_USER_INFO_ENABLED"] = False

        with app.test_request_context("/sso_authorize"):
            g._sso_auth = mock.Mock()
            g._sso_auth.authorize_access_token.return_value = {"access_token": "abc"}

            sso_authorize()

            g._sso_auth.userinfo.assert_not_called()
            assert "sso_auth_profile" not in session

    def test_aborts_401_on_oauth_error(self):
        app = self._make_app()

        with app.test_request_context("/sso_authorize"):
            g._sso_auth = mock.Mock()
            g._sso_auth.authorize_access_token.side_effect = OAuthError(
                "invalid_grant"
            )

            with pytest.raises(HTTPException) as excinfo:
                sso_authorize()

        assert excinfo.value.code == 401


class TestSsoLogout:
    def _make_app(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.register_blueprint(sso_auth)
        app.config["SSO_ENDSESSION_ENDPOINT"] = "https://issuer.example/end-session"
        app.config["SSO_CLIENT_ID"] = "client-id"
        app.config["SSO_CLIENT_SECRET"] = "client-secret"
        return app

    def test_clears_session_and_flashes_default_message_without_token(self):
        app = self._make_app()

        with app.test_request_context("/sso_logout"):
            g._sso_auth = mock.Mock()
            expected_root = request.root_url

            response = sso_logout()

            assert get_flashed_messages() == ["You were successfully logged out."]
            assert "sso_auth_token" not in session

        assert response.location == expected_root

    def test_flashes_expired_message_when_reason_is_expired(self):
        app = self._make_app()

        with app.test_request_context("/sso_logout?reason=expired"):
            g._sso_auth = mock.Mock()

            sso_logout()

            assert get_flashed_messages() == ["Your session expired, please reconnect."]

    def test_propagates_logout_to_end_session_endpoint_when_token_present(self):
        app = self._make_app()

        with app.test_request_context("/sso_logout"):
            session["sso_auth_token"] = {"access_token": "abc"}
            g._sso_auth = mock.Mock()
            g._sso_auth.get_access_token.return_value = "abc"
            g._sso_auth.get_refresh_token.return_value = "refresh123"

            with mock.patch(
                "nldcsc.sso.flask_sso.sso_views.requests.session"
            ) as session_ctor:
                post_mock = session_ctor.return_value.__enter__.return_value.post

                sso_logout()

            post_mock.assert_called_once_with(
                "https://issuer.example/end-session",
                data={
                    "client_id": "client-id",
                    "client_secret": "client-secret",
                    "refresh_token": "refresh123",
                },
                headers={
                    "Authorization": "Bearer abc",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                verify=False,
            )
            assert "sso_auth_token" not in session
            assert g.sso_id_token is None

    def test_logs_warning_and_continues_when_auth_helper_missing_attribute(self):
        app = self._make_app()

        with app.test_request_context("/sso_logout"):
            session["sso_auth_token"] = {"access_token": "abc"}
            g._sso_auth = mock.Mock(spec=[])

            response = sso_logout()

        assert response is not None

    def test_redirects_to_next_query_param(self):
        app = self._make_app()

        with app.test_request_context("/sso_logout?next=/goodbye"):
            g._sso_auth = mock.Mock()

            response = sso_logout()

        assert response.location == "/goodbye"


class TestDoSslVerification:
    def test_forces_verify_according_to_cert_check(self):
        http_session = requests.Session()

        with do_ssl_verification(cert_check=False):
            settings = http_session.merge_environment_settings(
                "https://example.com", {}, True, True, None
            )

        assert settings["verify"] is False

    def test_restores_original_merge_environment_settings_after_exit(self):
        with do_ssl_verification(cert_check=True):
            pass

        assert (
            requests.Session.merge_environment_settings
            == old_merge_environment_settings
        )

    def test_closes_adapters_opened_during_context(self):
        http_session = requests.Session()
        adapter = mock.Mock()

        with mock.patch.object(http_session, "get_adapter", return_value=adapter):
            with do_ssl_verification(cert_check=True):
                http_session.merge_environment_settings(
                    "https://example.com", {}, True, True, None
                )

        adapter.close.assert_called_once()

    def test_suppresses_insecure_request_warning_inside_context(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            with do_ssl_verification(cert_check=True):
                warnings.warn("insecure", InsecureRequestWarning)

    def test_swallows_errors_while_closing_adapters(self):
        http_session = requests.Session()
        adapter = mock.Mock()
        adapter.close.side_effect = RuntimeError("boom")

        with mock.patch.object(http_session, "get_adapter", return_value=adapter):
            with do_ssl_verification(cert_check=True):
                http_session.merge_environment_settings(
                    "https://example.com", {}, True, True, None
                )


class TestSslVerification:
    def test_works_as_bare_decorator_without_parentheses(self):
        @ssl_verification
        def f():
            return "value"

        assert f() == "value"

    def test_works_as_decorator_with_parentheses(self):
        @ssl_verification()
        def f():
            return "value"

        assert f() == "value"

    def test_preserves_wrapped_function_name(self):
        @ssl_verification
        def my_func():
            return None

        assert my_func.__name__ == "my_func"

    def test_passes_args_and_kwargs_through(self):
        @ssl_verification
        def f(a, b, c=None):
            return a, b, c

        assert f(1, 2, c=3) == (1, 2, 3)

    def test_applies_do_ssl_verification_during_call(self):
        calls = []

        @ssl_verification
        def f():
            calls.append(
                requests.Session.merge_environment_settings
                == old_merge_environment_settings
            )
            return None

        f()

        assert calls == [False]
