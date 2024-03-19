import logging
import os
from contextlib import contextmanager
from typing import Any

import ldap
from ldap.filter import escape_filter_chars

from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class LDAPClient(object):
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        ldap_user_base: str = None,
        ldap_ipa_admin_groups: list = None,
        ldap_ipa_superuser_groups: list = None,
        ldap_ipa_groups: list = None,
        ldap_ca_cert_file: str = None,
    ):
        self._url = url
        self._username = username
        self._password = password
        self.ldap_user_base = ldap_user_base
        self.ldap_ipa_admin_groups = self.convert_to_bytes(ldap_ipa_admin_groups)
        self.ldap_ipa_superuser_groups = self.convert_to_bytes(
            ldap_ipa_superuser_groups
        )
        self.ldap_ipa_groups = (
            self.ldap_ipa_admin_groups
            + self.ldap_ipa_superuser_groups
            + self.convert_to_bytes(ldap_ipa_groups)
        )
        self.ldap_username = f"uid={self._username},{self.ldap_user_base}"
        self.is_admin = None
        self.is_superuser = None

        self.ldap_ca_cert_file = (
            ldap_ca_cert_file
            if ldap_ca_cert_file is not None
            else os.getenv("LDAP_CACERTFILE", None)
        )

        self.logger = logging.getLogger(__name__)

    def create_connection(self):
        """Create a connection over LDAP using the provided credentials.

        Raises:
            e: Cuts the connection if an error occurs.

        Returns:
            _type_: An LDAP connection instance.
        """
        try:
            ldap_connection = ldap.initialize(
                self._url,
                bytes_mode=False,
            )
            self.logger.info("Connection to server succeeded...")
        except ldap.SERVER_DOWN:
            raise

        # Set LDAP protocol version used
        ldap_connection.protocol_version = ldap.VERSION3

        if self.ldap_ca_cert_file is not None:
            # Force cert validation
            ldap_connection.set_option(
                ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND
            )
            # Set path name of file containing all trusted CA certificates
            ldap_connection.set_option(
                ldap.OPT_X_TLS_CACERTFILE, self.ldap_ca_cert_file
            )
            # Force libldap to create a new SSL context (must be last TLS option!)
            ldap_connection.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        try:
            ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
            ldap_connection.set_option(ldap.OPT_NETWORK_TIMEOUT, 2.0)
            ldap_connection.simple_bind_s(self.ldap_username, self._password)
            self.logger.info("Simple bind successful...")

        except Exception as e:
            ldap_connection.unbind()
            raise e
        return ldap_connection

    @contextmanager
    def ldap_connection(self):
        """Runs the create_connection method with supervision of the context manager.

        Yields:
            _type_: An LDAP connection instance.
        """
        conn = self.create_connection()
        try:
            yield conn
        except Exception as err:
            self.logger.error(f"Error on LDAP contextmanager: {err}")
            self.logger.exception(err)
            raise
        finally:
            conn.unbind()
            self.logger.info("Disconnected from LDAP server!")

    def validate_credentials(self) -> bool:
        try:
            with self.ldap_connection() as ldap_connection:
                self.logger.info("Connection to LDAP server successful!!!")
                pass
        except ldap.INVALID_CREDENTIALS:
            self.logger.warning(f"Wrong credentials provided... -> {self._username}")
            return False
        except ldap.UNWILLING_TO_PERFORM:
            self.logger.error(
                f"LDAP server is unwilling to bind, possibly locked... -> {self._username}"
            )
            # Too many log in attempts - locked
            return False

        return True

    def validate_user(self) -> tuple[bool, None] | tuple[bool, str | Any]:
        # Fields to return
        FIELDS = ["memberOf", "displayName"]

        query = f"uid={escape_filter_chars(self._username)}"
        # Get LDAP connection with account
        with self.ldap_connection() as ldap_connection:
            results = ldap_connection.search_s(
                self.ldap_user_base, ldap.SCOPE_SUBTREE, query, attrlist=FIELDS
            )

        if len(results) != 1:
            # Invalid account type or person was deleted between credential check and now.
            self.logger.warning(
                "Invalid account type or person was deleted between credential check and now!"
            )
            return False, None

        fields = results[0][1]
        username = fields.get("displayName")
        if username:
            username = username[0].decode("utf-8")
        else:
            # Should always be a username but just in case, return the id
            username = self._username
        # Check if user is in a required group
        if any(i in fields.get("memberOf", []) for i in self.ldap_ipa_groups):
            self.logger.info(f"User: {self._username} granted access; returning")
            self.is_admin = any(
                i in fields.get("memberOf", []) for i in self.ldap_ipa_admin_groups
            )
            self.is_superuser = any(
                i in fields.get("memberOf", []) for i in self.ldap_ipa_superuser_groups
            )
            return True, username
        else:
            self.logger.info(f"User: {self._username} denied access; returning")
            return False, None

    @staticmethod
    def convert_to_bytes(groups: list) -> list:
        return [group.encode(encoding="UTF-8", errors="strict") for group in groups]
