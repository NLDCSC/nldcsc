import logging

import requests
from authlib.integrations.base_client.errors import OAuthError
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    request,
    session,
    url_for,
)

logger = logging.getLogger(__name__)

sso_auth = Blueprint("sso_auth", __name__)


@sso_auth.route("/sso_login")
def sso_login():
    if current_app.config["SSO_OVERWRITE_REDIRECT_URI"]:
        redirect_uri = current_app.config["SSO_OVERWRITE_REDIRECT_URI"]
    else:
        redirect_uri = url_for("sso_auth.sso_authorize", _external=True)
    if current_app.config["SSO_CALLBACK_ENDPOINT"]:
        session[
            "next"
        ] = f"{request.root_url}{current_app.config['SSO_CALLBACK_ENDPOINT']}"
    else:
        session["next"] = request.args.get("next", request.root_url)
    return g._sso_auth.authorize_redirect(redirect_uri)


@sso_auth.route("/sso_authorize")
def sso_authorize():
    try:
        token = g._sso_auth.authorize_access_token()
    except OAuthError as e:
        logger.exception("Could not get the access token")
        abort(401, str(e))
    session["sso_auth_token"] = token
    g.sso_id_token = token
    if current_app.config["SSO_USER_INFO_ENABLED"]:
        profile = g._sso_auth.userinfo(token=token)
        session["sso_auth_profile"] = profile
    try:
        return_to = session["next"]
        del session["next"]
    except KeyError:
        return_to = request.root_url
    return redirect(return_to)


@sso_auth.route("/sso_logout")
def sso_logout():
    """
    Request the browser to please forget the cookie we set, to clear the
    current session.
    """

    tokenResponse = session.get("sso_auth_token")

    if tokenResponse is not None:
        # propagate logout to sso
        endSessionEndpoint = current_app.config["SSO_ENDSESSION_ENDPOINT"]

        headers = {
            "Authorization": f"Bearer {g._sso_auth.get_access_token()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "client_id": current_app.config["SSO_CLIENT_ID"],
            "client_secret": current_app.config["SSO_CLIENT_SECRET"],
            "refresh_token": g._sso_auth.get_refresh_token(),
        }

        with requests.session() as req_session:
            req_session.post(
                endSessionEndpoint,
                data=data,
                headers=headers,
                verify=False,
            )

    session.pop("sso_auth_token", None)
    session.pop("sso_auth_profile", None)
    g.sso_id_token = None
    reason = request.args.get("reason")
    if reason == "expired":
        flash("Your session expired, please reconnect.")
    else:
        flash("You were successfully logged out.")
    return_to = request.args.get("next", request.root_url)
    return redirect(return_to)
