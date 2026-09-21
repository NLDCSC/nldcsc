from typing import Any

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class SlackWebhookApi(ApiBaseClass):
    SLACK_URL = "https://hooks.slack.com"
    SLACK_BASE_API_PATH = "services/{workspace}/{webhook_id}/{token}"

    def __init__(
        self,
        workspace: str,
        webhook_id: str,
        token: str,
        proxies: dict[str, Any] | None = None,
        user_agent: str = "NLDCSC",
    ):
        super().__init__(
            self.SLACK_URL,
            self.SLACK_BASE_API_PATH.format(
                workspace=workspace, webhook_id=webhook_id, token=token
            ),
            proxies,
            user_agent,
        )

    def _build_url(self, resource: str, *args, **kwargs) -> str:
        """
        Internal method to build a url to use when executing commands
        """
        out = self.baseurl

        if self.api_path:
            out += f"/{self.api_path}"
        if resource:
            out += f"/{resource}"

        return out

    def post_to_webhook(
        self,
        text: str = None,
        blocks: list[dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Body could consist of (https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/#advanced_message_formatting)

        Text formatted as in: https://docs.slack.dev/messaging/formatting-message-text/
        """
        resource = ""

        if not text or blocks:
            raise TypeError(
                "Either message or embed variable should be filled; they cannot all be None"
            )

        data = {}

        if blocks:
            if not isinstance(blocks, list):
                blocks = [blocks]

            data["blocks"] = blocks

        if text:
            data["text"] = text

        if kwargs:
            data.update(kwargs)

        return self.call("POST", resource=resource, data=data)
