import logging
import os
from functools import wraps
from urllib.parse import quote_plus

from authlib.common.errors import AuthlibBaseError
from authlib.integrations.base_client import InvalidTokenError
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6749 import OAuth2Token
from authlib.oauth2.rfc7662 import (
    IntrospectTokenValidator as BaseIntrospectTokenValidator,
)
from flask import abort, g, redirect, request, session, url_for
from nldcsc.generic.utils import getenv_bool, getenv_list

from nldcsc.sso.sso_views import sso_auth

__all__ = ["SSOConnection"]


class IntrospectTokenValidator(BaseIntrospectTokenValidator):
    """Validates a token using introspection."""

    def introspect_token(self, token_string):
        """Return the token introspection result."""
        oauth = g._sso_auth
        metadata = oauth.load_server_metadata()
        if "introspection_endpoint" not in metadata:
            raise RuntimeError(
                "Can't validate the token because the server does not support "
                "introspection."
            )
        with oauth._get_oauth_client(**metadata) as session:
            response = session.introspect_token(
                metadata["introspection_endpoint"], token=token_string
            )
        return response.json()


class SSOConnection(object):
    accept_token = ResourceProtector()

    def __init__(
        self,
        app=None,
        prefix=None,
    ):
        self.logger = logging.getLogger(__name__)

        self.accept_token.register_token_validator(IntrospectTokenValidator())
        if app is not None:
            self.init_app(app, prefix=prefix)

    def init_app(self, app, prefix=None):

        app.config.setdefault("SSO_CLIENT_ID", os.getenv("SSO_CLIENT_ID", "sso-client"))
        app.config.setdefault(
            "SSO_CLIENT_SECRET", os.getenv("SSO_CLIENT_SECRET", "secret!")
        )
        app.config.setdefault("SSO_ISSUER", os.getenv("SSO_ISSUER", ""))
        app.config.setdefault(
            "SSO_DISCOVERY_URL",
            os.getenv(
                "SSO_DISCOVERY_URL",
                f"{app.config['SSO_ISSUER']}/.well-known/openid-configuration",
            ),
        )
        app.config.setdefault(
            "SSO_USERINFO_ENDPOINT",
            os.getenv(
                "SSO_USERINFO_ENDPOINT",
                f"{app.config['SSO_ISSUER']}/protocol/openid-connect/userinfo",
            ),
        )
        app.config.setdefault(
            "SSO_ENDSESSION_ENDPOINT",
            os.getenv(
                "SSO_ENDSESSION_ENDPOINT",
                f"{app.config['SSO_ISSUER']}/protocol/openid-connect/logout",
            ),
        )
        app.config.setdefault(
            "SSO_SCOPES", getenv_list("SSO_SCOPES", ["openid", "profile", "email"])
        )

        if "openid" not in app.config["SSO_SCOPES"]:
            raise ValueError('The value "openid" must be in the SSO_SCOPES')

        app.config.setdefault(
            "SSO_CODE_CHALLENGE_METHOD", os.getenv("SSO_CODE_CHALLENGE_METHOD", "S256")
        )
        app.config.setdefault(
            "SSO_OVERWRITE_REDIRECT_URI", os.getenv("SSO_OVERWRITE_REDIRECT_URI", None)
        )
        app.config.setdefault(
            "SSO_CALLBACK_ENDPOINT", os.getenv("SSO_CALLBACK_ENDPOINT", None)
        )

        app.config.setdefault(
            "SSO_USER_INFO_ENABLED", getenv_bool("SSO_USER_INFO_ENABLED", "True")
        )

        self.oauth = OAuth(app)
        self.oauth.register(
            name="sso",
            client_id=app.config["SSO_CLIENT_ID"],
            client_secret=app.config["SSO_CLIENT_SECRET"],
            server_metadata_url=app.config["SSO_DISCOVERY_URL"],
            client_kwargs={
                "scope": " ".join(app.config["SSO_SCOPES"]),
                "code_challenge_method": app.config["SSO_CODE_CHALLENGE_METHOD"],
            },
            update_token=self._update_token,
        )

        app.register_blueprint(sso_auth, url_prefix=prefix)

        app.before_request(self._before_request)

    def _before_request(self):
        g._sso_auth = self.oauth.sso
        return self.check_token_expiry()

    def check_token_expiry(self):
        try:
            token = session.get("sso_auth_token")
            if not token:
                return
            if f"{request.root_path}{request.path}" == url_for("sso_auth.sso_logout"):
                return  # Avoid redirect loop
            token = OAuth2Token.from_dict(token)
            try:
                self.ensure_active_token(token)
            except AuthlibBaseError as e:
                self.logger.info(f"Could not refresh token {token!r}: {e}")
                return redirect(
                    "{}?reason=expired".format(url_for("sso_auth.sso_logout"))
                )
        except Exception as e:
            self.logger.exception("Could not check token expiration")
            abort(500, f"{e.__class__.__name__}: {e}")

    def ensure_active_token(self, token: OAuth2Token):
        metadata = self.oauth.sso.load_server_metadata()
        with self.oauth.sso._get_oauth_client(**metadata) as session:
            result = session.ensure_active_token(token)
            if result is None:
                # See the ensure_active_token method in
                # authlib.integrations.requests_client.oauth2_session:OAuth2Auth
                raise InvalidTokenError()
            return result

    def _update_token(name, token, refresh_token=None, access_token=None):
        session["sso_auth_token"] = g.sso_id_token = token

    @property
    def user_loggedin(self):
        """
        Represents whether the user is currently logged in.
        """
        return session.get("sso_auth_token") is not None

    def user_getinfo(self):
        if not self.user_loggedin:
            abort(401, "User was not authenticated")
        return session.get("sso_auth_profile", {})

    def user_getfield(self, field: str):
        """
        Request a single field of information about the user.
        """
        req_data = session.get("sso_auth_profile", {}).get(field)
        if req_data is None:
            raise AttributeError(f"Could not retrieve {field} from sso_auth_profile")
        else:
            return req_data

    def get_access_token(self):
        """Method to return the current requests' access_token."""
        return session.get("sso_auth_token", {}).get("access_token")

    def get_refresh_token(self):
        """Method to return the current requests' refresh_token."""
        return session.get("sso_auth_token", {}).get("refresh_token")

    def require_login(self, view_func):
        """
        Use this to decorate view functions that require a user to be logged
        in. If the user is not already logged in, they will be sent to the
        Provider to log in, after which they will be returned.
        """

        @wraps(view_func)
        def decorated(*args, **kwargs):
            if not self.user_loggedin:
                redirect_uri = "{login}?next={here}".format(
                    login=url_for("sso_auth.sso_login"),
                    here=quote_plus(request.url),
                )
                return redirect(redirect_uri)
            return view_func(*args, **kwargs)

        return decorated

    def logout(self, return_to=None):
        """
        Request the browser to please forget the cookie we set, to clear the
        current session. Propagate logout to SSO provider.

        """
        return_to = return_to or request.root_url
        return redirect(url_for("sso_auth.sso_logout", next=return_to))
