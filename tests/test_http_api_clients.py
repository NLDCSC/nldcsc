import base64
from unittest.mock import Mock

import pytest
import requests

from nldcsc.http_apis.confluence.client import ConfluenceClient
from nldcsc.http_apis.discord.api import DiscordWebhookApi
from nldcsc.http_apis.mailgun.mail_objects import Email, EmailAttachment
from nldcsc.http_apis.mailgun.mailgun_api import MailgunAPI
from nldcsc.http_apis.nexpose.helpers import filter_from_args
from nldcsc.http_apis.nexpose.objects import NexposeFilterOperator
from nldcsc.http_apis.otrs.otrs_api import Otrs
from nldcsc.http_apis.providentia.providentia_api import ProvidentiaApi
from nldcsc.http_apis.slack.api import SlackWebhookApi


def test_webhook_clients_validate_payloads_and_build_requests():
    discord = DiscordWebhookApi("webhook", "token")
    discord.call = Mock(return_value={"ok": True})
    assert discord._build_url("") == (
        "https://discord.com/api/webhooks/webhook/token"
    )
    assert discord.post_to_webhook(
        embeds={"title": "alert"}, username="bot", tts=True, allowed_mentions={}
    ) == {"ok": True}
    assert discord.call.call_args.kwargs["data"] == {
        "embeds": [{"title": "alert"}],
        "username": "bot",
        "tts": True,
        "allowed_mentions": {},
    }

    with pytest.raises(TypeError, match="Either message or embed"):
        discord.post_to_webhook()

    slack = SlackWebhookApi("workspace", "hook", "token")
    slack.call = Mock(return_value="ok")
    assert slack._build_url("") == (
        "https://hooks.slack.com/services/workspace/hook/token"
    )
    assert slack.post_to_webhook("hello") == "ok"
    assert slack.call.call_args.kwargs["data"] == {"text": "hello"}
    assert slack.post_to_webhook("hello", blocks=[]) == "ok"
    assert slack.call.call_args.kwargs["data"] == {"blocks": [], "text": "hello"}
    with pytest.raises(TypeError, match="Either message or embed"):
        slack.post_to_webhook()


def test_providentia_methods_map_to_environment_endpoints():
    api = ProvidentiaApi("https://providentia.test", api_key="key")
    api.call = Mock(return_value={})

    api.environments()
    api.environment("prod")
    api.environment_hosts("prod")
    api.environment_hosts_id("prod", "host-1")
    api.environment_inventory("prod")
    api.environment_networks("prod")
    api.environment_tags("prod")
    api.environment_actors("prod")
    api.environment_services("prod")
    api.environment_services_id("prod", "svc-1")

    assert [call.args[1] for call in api.call.call_args_list] == [
        "",
        "/prod",
        "/prod/hosts",
        "/prod/hosts/host-1",
        "/prod/inventory",
        "/prod/networks",
        "/prod/tags",
        "/prod/actors",
        "/prod/services",
        "/prod/services/svc-1",
    ]
    assert api.headers["Authorization"]


def test_confluence_client_sets_token_and_queries_with_cql():
    api = ConfluenceClient("https://wiki.test", token="token")
    api.call = Mock(return_value={"results": []})

    assert api.search("type=page") == {"results": []}
    api.call.assert_called_once_with(
        api.methods.GET, "search", params={"cql": "type=page"}
    )
    assert api.headers["Authorization"]
    api.close()


def test_mailgun_ping_and_application_methods(monkeypatch, tmp_path):
    api = MailgunAPI("https://mail.test", api_key="key")
    api.call = Mock(return_value={"ApplicationName": "mail"})

    assert api.ping() is True
    assert api.get_applications_list()["ApplicationName"] == "mail"
    api.get_application_template_list("alerts")
    api.create_application("alerts")
    api.delete_application("alerts")
    api.get_application_template("alerts", "weekly")
    api.get_queue_length()
    api.get_queue_schedule()
    api.get_queue_items()
    api.get_queue_item("item-1")
    api.delete_queue_item("item-1")

    template = tmp_path / "template.mjml"
    template.write_text("<mjml>hello</mjml>")
    api.create_application_template("alerts", "weekly", template)
    api.update_application_template("alerts", "weekly", template)
    expected_content = base64.b64encode(b"<mjml>hello</mjml>").decode()
    assert api.call.call_args.kwargs["data"] == {
        "mjml_content": expected_content,
        "template": "weekly",
    }

    output = tmp_path / "download.mjml"
    api.get_application_template = Mock(
        return_value={"mjml_content": expected_content}
    )
    assert api.download_application_template("alerts", "weekly", output) is True
    assert output.read_bytes() == b"<mjml>hello</mjml>"
    api.get_application_template.return_value = {}
    assert api.download_application_template("alerts", "weekly", output) is False
    api.get_application_template.return_value = {"errors": "invalid"}
    with pytest.raises(RuntimeError, match="invalid"):
        api.download_application_template("alerts", "weekly", output)


def test_mailgun_template_loading_and_email_sending(tmp_path):
    api = MailgunAPI("https://mail.test")
    api.call = Mock(return_value={"sent": True})
    template = tmp_path / "template.html"
    template.write_text("hello")

    assert MailgunAPI.fetch_template_from_location(template) == "hello"
    with pytest.raises(FileNotFoundError, match="not found"):
        MailgunAPI.fetch_template_from_location(tmp_path / "missing")

    email = Email(
        From="sender@example.test",
        To="recipient@example.test",
        Subject="Notice",
        TemplateData={"name": "Ada"},
        Attachments=[EmailAttachment(Name="a.txt", Content="YQ==")],
    )
    api.send_mail_with_template("alerts", "welcome", email.model_dump())
    api.send_batch_with_template("alerts", [email.model_dump()])


def test_mailgun_connection_errors_are_decoded_and_ping_fails(tmp_path):
    api = MailgunAPI("https://mail.test")
    api.call = Mock(side_effect=ConnectionError("offline"))
    template = tmp_path / "template.mjml"
    template.write_text("<mjml/>")

    assert api.ping() is False
    api.call.side_effect = requests.exceptions.ConnectionError('{"error":"offline"}')
    assert api.get_application_template_list("alerts") == {"error": "offline"}
    assert api.delete_application("alerts") == {"error": "offline"}
    assert api.get_application_template("alerts", "weekly") == {"error": "offline"}
    assert api.delete_application_template("alerts", "weekly") == {"error": "offline"}
    assert api.create_application_template("alerts", "weekly", template) == {
        "error": "offline"
    }


def test_otrs_creates_session_and_retries_auth_failures(tmp_path):
    api = Otrs("https://otrs.test", "api", auth=("user", "password"))
    api.session_id_path = tmp_path / "session"
    api.save_session_id = True
    api.call = Mock(side_effect=[{"SessionID": "first"}, {"SessionID": "second"}])

    api.create_session()
    assert api.session_id == "first"
    assert api.session_id_path.read_text() == "first"

    api.session_id = "first"
    api.call = Mock(
        side_effect=[
            {"Error": {"ErrorCode": "TicketSearch.AuthFail"}},
            {"SessionID": "second"},
            {"TicketSearch": []},
        ]
    )
    assert api.search_ticket(Title="problem") == {"TicketSearch": []}
    assert api.session_id == "second"
    assert api.call.call_count == 3


def test_otrs_ticket_methods_and_argument_validation():
    api = Otrs("https://otrs.test", "api", auth=("user", "password"))
    api.session_id = "session"
    api.call = Mock(return_value={"ok": True})

    api.search_ticket(Title="problem")
    api.get_ticket("12", articles=True, attachments=True)
    api.create_ticket(
        {"Title": "problem"},
        {"Subject": "report"},
        dynamic_fields=[{"Name": "severity", "Value": "high"}],
    )
    api.update_ticket(ticket_id="12", ticket={"State": "closed"})
    api.update_ticket(ticket_number=42, article={"Body": "resolved"})

    assert api.call.call_args_list[0].kwargs["data"] == {
        "SessionID": "session",
        "Title": "problem",
    }
    assert api.call.call_args_list[1].kwargs["data"]["AllArticles"] == 1
    assert api.call.call_args_list[2].kwargs["data"]["DynamicField"]
    assert api.call.call_args_list[3].kwargs["resource"].endswith("/Ticket/12")
    assert api.call.call_args_list[4].kwargs["resource"].endswith("/Ticket/0")
    with pytest.raises(Exception, match="MAX one"):
        api.update_ticket(ticket={"State": "closed"})


def test_otrs_recreate_session_raises_non_auth_errors():
    api = Otrs("https://otrs.test", "api", auth=("user", "password"))
    api.session_id = "session"
    api.call = Mock(return_value={"Error": {"ErrorCode": "TicketSearch.NotFound"}})

    with pytest.raises(Exception):
        api.search_ticket()


def test_nexpose_filter_builder_requires_a_value_or_range():
    with pytest.raises(ValueError, match="value, upper or lower required"):
        filter_from_args("risk", NexposeFilterOperator.IS)

    assert filter_from_args("risk", NexposeFilterOperator.IS, value="critical") == {
        "field": "risk",
        "operator": NexposeFilterOperator.IS,
        "value": "critical",
    }
    assert filter_from_args(
        "created",
        NexposeFilterOperator.IN_RANGE,
        lower="2025-01-01",
        upper="2025-12-31",
    ) == {
        "field": "created",
        "operator": NexposeFilterOperator.IN_RANGE,
        "upper": "2025-12-31",
        "lower": "2025-01-01",
    }
