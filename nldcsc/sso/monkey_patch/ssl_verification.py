import contextlib
import logging
import warnings
from functools import wraps

import requests
from urllib3.exceptions import InsecureRequestWarning

from nldcsc.generic.utils import getenv_bool

old_merge_environment_settings = requests.Session.merge_environment_settings


# noinspection TryExceptPass
@contextlib.contextmanager
def do_ssl_verification(cert_check: bool = getenv_bool("SSO_TLS_VERIFICATION", "True")):
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(
            self, url, proxies, stream, verify, cert
        )
        settings["verify"] = cert_check

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except Exception:
                pass


def ssl_verification(func=None):

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):

            logger = logging.getLogger(__name__)

            with do_ssl_verification(
                cert_check=getenv_bool("SSO_TLS_VERIFICATION", "True")
            ):
                logger.info(
                    f"Monkey patching SSL verification; "
                    f"setting verify: {getenv_bool('SSO_TLS_VERIFICATION', 'True')}"
                )

                return_value = func(*args, **kwargs)
                return return_value

        return inner

    if callable(func):
        return wrapper(func=func)
    return wrapper
