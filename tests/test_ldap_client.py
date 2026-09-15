import ldap
import mock
import pytest

from nldcsc.auth.ldap_client import LDAPClient


@pytest.fixture
def client():
    return LDAPClient(
        url="ldap://localhost:389",
        username="jdoe",
        password="secret",
        ldap_user_base="ou=users,dc=example,dc=com",
        ldap_ipa_admin_groups=["cn=admins,dc=example,dc=com"],
        ldap_ipa_superuser_groups=["cn=superusers,dc=example,dc=com"],
        ldap_ipa_groups=["cn=users,dc=example,dc=com"],
    )


class TestInit:
    def test_builds_bind_dn_from_template_and_user_base(self, client):
        assert client.ldap_username == "uid=jdoe,ou=users,dc=example,dc=com"

    def test_converts_group_lists_to_bytes(self, client):
        assert client.ldap_ipa_admin_groups == [b"cn=admins,dc=example,dc=com"]
        assert client.ldap_ipa_superuser_groups == [b"cn=superusers,dc=example,dc=com"]

    def test_combines_admin_superuser_and_plain_groups(self, client):
        assert client.ldap_ipa_groups == [
            b"cn=admins,dc=example,dc=com",
            b"cn=superusers,dc=example,dc=com",
            b"cn=users,dc=example,dc=com",
        ]

    def test_defaults_additional_fields_to_empty_list(self, client):
        assert client.additional_fields == []

    def test_starts_with_no_admin_or_superuser_verdict(self, client):
        assert client.is_admin is None
        assert client.is_superuser is None

    def test_defaults_ca_cert_verify_to_true(self, client):
        assert client.ldap_ca_cert_verify is True

    def test_names_logger_after_module(self, client):
        assert client.logger.name == "nldcsc.auth.ldap_client"

    def test_uses_explicit_ca_cert_file_over_env_var(self, monkeypatch):
        monkeypatch.setenv("LDAP_CACERTFILE", "/env/ca.pem")

        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
            ldap_ca_cert_file="/explicit/ca.pem",
        )

        assert client.ldap_ca_cert_file == "/explicit/ca.pem"

    def test_falls_back_to_env_var_when_ca_cert_file_not_given(self, monkeypatch):
        monkeypatch.setenv("LDAP_CACERTFILE", "/env/ca.pem")

        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
        )

        assert client.ldap_ca_cert_file == "/env/ca.pem"

    def test_ca_cert_file_is_none_when_not_given_and_no_env_var(self, monkeypatch):
        monkeypatch.delenv("LDAP_CACERTFILE", raising=False)

        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
        )

        assert client.ldap_ca_cert_file is None


class TestConvertToBytes:
    def test_encodes_each_string_as_utf8_bytes(self):
        assert LDAPClient.convert_to_bytes(["a", "b"]) == [b"a", b"b"]

    def test_returns_empty_list_for_empty_input(self):
        assert LDAPClient.convert_to_bytes([]) == []


class TestCreateConnection:
    def test_initializes_binds_and_returns_connection(self, client):
        conn = mock.Mock()

        with mock.patch(
            "nldcsc.auth.ldap_client.ldap.initialize", return_value=conn
        ) as initialize:
            result = client.create_connection()

        initialize.assert_called_once_with("ldap://localhost:389", bytes_mode=False)
        assert conn.protocol_version == ldap.VERSION3
        conn.simple_bind_s.assert_called_once_with(
            "uid=jdoe,ou=users,dc=example,dc=com", "secret"
        )
        assert result is conn

    def test_reraises_server_down_from_initialize(self, client):
        with mock.patch(
            "nldcsc.auth.ldap_client.ldap.initialize", side_effect=ldap.SERVER_DOWN
        ):
            with pytest.raises(ldap.SERVER_DOWN):
                client.create_connection()

    def test_unbinds_and_reraises_when_bind_fails(self, client):
        conn = mock.Mock()
        conn.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS

        with mock.patch("nldcsc.auth.ldap_client.ldap.initialize", return_value=conn):
            with pytest.raises(ldap.INVALID_CREDENTIALS):
                client.create_connection()

        conn.unbind.assert_called_once()

    def test_sets_tls_options_when_ca_cert_file_configured(self):
        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
            ldap_ca_cert_file="/explicit/ca.pem",
        )
        conn = mock.Mock()

        with mock.patch("nldcsc.auth.ldap_client.ldap.initialize", return_value=conn):
            client.create_connection()

        conn.set_option.assert_any_call(
            ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND
        )
        conn.set_option.assert_any_call(ldap.OPT_X_TLS_CACERTFILE, "/explicit/ca.pem")
        conn.set_option.assert_any_call(ldap.OPT_X_TLS_NEWCTX, 0)

    def test_disables_cert_verification_when_no_cert_file_and_verify_false(self):
        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
            ldap_ca_cert_file=None,
            ldap_ca_cert_verify=False,
        )
        conn = mock.Mock()

        with mock.patch("nldcsc.auth.ldap_client.ldap.initialize", return_value=conn):
            client.create_connection()

        conn.set_option.assert_any_call(
            ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER
        )
        conn.set_option.assert_any_call(ldap.OPT_X_TLS_NEWCTX, 0)

    def test_skips_tls_options_when_no_cert_file_and_verify_true(self):
        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=[],
            ldap_ca_cert_file=None,
            ldap_ca_cert_verify=True,
        )
        conn = mock.Mock()

        with mock.patch("nldcsc.auth.ldap_client.ldap.initialize", return_value=conn):
            client.create_connection()

        tls_options = {
            call_args.args[0]
            for call_args in conn.set_option.call_args_list
            if call_args.args[0] in (ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEWCTX)
        }
        assert tls_options == set()


class TestLdapConnectionContextManager:
    def test_yields_connection_and_unbinds_on_success(self, client):
        conn = mock.Mock()

        with mock.patch.object(client, "create_connection", return_value=conn):
            with client.ldap_connection() as yielded:
                assert yielded is conn
                conn.unbind.assert_not_called()

        conn.unbind.assert_called_once()

    def test_unbinds_and_reraises_when_body_raises(self, client):
        conn = mock.Mock()

        with mock.patch.object(client, "create_connection", return_value=conn):
            with pytest.raises(ValueError, match="boom"):
                with client.ldap_connection():
                    raise ValueError("boom")

        conn.unbind.assert_called_once()


class TestValidateCredentials:
    def test_returns_true_when_bind_succeeds(self, client):
        conn = mock.Mock()

        with mock.patch.object(client, "create_connection", return_value=conn):
            assert client.validate_credentials() is True

    def test_returns_false_on_invalid_credentials(self, client):
        with mock.patch.object(
            client, "create_connection", side_effect=ldap.INVALID_CREDENTIALS
        ):
            assert client.validate_credentials() is False

    def test_returns_false_when_unwilling_to_perform(self, client):
        with mock.patch.object(
            client, "create_connection", side_effect=ldap.UNWILLING_TO_PERFORM
        ):
            assert client.validate_credentials() is False


class TestValidateUser:
    def _search_result(self, member_of=None, display_name=b"John Doe", extra=None):
        fields = {}
        if display_name is not None:
            fields["displayName"] = [display_name]
        if member_of is not None:
            fields["memberOf"] = member_of
        if extra:
            fields.update(extra)
        return [("uid=jdoe,ou=users,dc=example,dc=com", fields)]

    def _connection_with_results(self, results):
        conn = mock.Mock()
        conn.search_s.return_value = results
        return conn

    def test_returns_false_when_no_matching_entry(self, client):
        conn = self._connection_with_results([])

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert (found, fields) == (False, None)

    def test_returns_false_when_multiple_matching_entries(self, client):
        entry = self._search_result()[0]
        conn = self._connection_with_results([entry, entry])

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert (found, fields) == (False, None)

    def test_returns_false_when_not_member_of_any_ipa_group(self, client):
        conn = self._connection_with_results(
            self._search_result(member_of=[b"cn=other,dc=example,dc=com"])
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert (found, fields) == (False, None)
        assert client.is_admin is None
        assert client.is_superuser is None

    def test_grants_access_when_member_of_plain_group(self, client):
        conn = self._connection_with_results(
            self._search_result(member_of=[b"cn=users,dc=example,dc=com"])
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert found is True
        assert fields == "John Doe"
        assert client.is_admin is False
        assert client.is_superuser is False

    def test_marks_admin_when_member_of_admin_group(self, client):
        conn = self._connection_with_results(
            self._search_result(member_of=[b"cn=admins,dc=example,dc=com"])
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, _ = client.validate_user()

        assert found is True
        assert client.is_admin is True
        assert client.is_superuser is False

    def test_marks_superuser_when_member_of_superuser_group(self, client):
        conn = self._connection_with_results(
            self._search_result(member_of=[b"cn=superusers,dc=example,dc=com"])
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, _ = client.validate_user()

        assert found is True
        assert client.is_admin is False
        assert client.is_superuser is True

    def test_falls_back_to_username_when_display_name_missing(self, client):
        conn = self._connection_with_results(
            self._search_result(
                member_of=[b"cn=users,dc=example,dc=com"], display_name=None
            )
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert found is True
        assert fields == "jdoe"

    def test_queries_using_escaped_username_and_configured_fields(self, client):
        conn = self._connection_with_results(
            self._search_result(member_of=[b"cn=users,dc=example,dc=com"])
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            client.validate_user()

        conn.search_s.assert_called_once_with(
            "ou=users,dc=example,dc=com",
            ldap.SCOPE_SUBTREE,
            "uid=jdoe",
            attrlist=["memberOf", "displayName"],
        )

    def test_includes_single_valued_additional_field_in_returned_fields(self):
        client = LDAPClient(
            url="ldap://localhost:389",
            username="jdoe",
            password="secret",
            ldap_user_base="ou=users,dc=example,dc=com",
            ldap_ipa_admin_groups=[],
            ldap_ipa_superuser_groups=[],
            ldap_ipa_groups=["cn=users,dc=example,dc=com"],
            additional_fields=["mail"],
        )
        conn = self._connection_with_results(
            self._search_result(
                member_of=[b"cn=users,dc=example,dc=com"],
                extra={"mail": [b"jdoe@example.com"]},
            )
        )

        with mock.patch.object(client, "create_connection", return_value=conn):
            found, fields = client.validate_user()

        assert found is True
        assert fields == {
            "displayName": "John Doe",
            "mail": "jdoe@example.com",
        }
