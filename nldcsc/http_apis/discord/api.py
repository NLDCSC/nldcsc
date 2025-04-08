from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class DiscordWebhookApi(ApiBaseClass):
    DISCORD_URL = "https://discord.com"
    DISCORD_BASE_API_PATH = "api/webhooks/{webhook_id}/{token}"

    def __init__(
        self,
        webhook_id,
        token,
        proxies=None,
        user_agent="NLDCSC",
    ):
        super().__init__(
            self.DISCORD_URL,
            self.DISCORD_BASE_API_PATH.format(webhook_id=webhook_id, token=token),
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
        content: str = None,
        username: str = None,
        avatar_url: str = None,
        tts: bool = None,
        embeds: list = None,
        **kwargs,
    ):
        """
        Body could consist of (https://discord.com/developers/docs/resources/webhook#execute-webhook)
        """
        resource = ""

        if not embeds or content:
            raise TypeError(
                "Either message or embed variable should be filled; they cannot all be None"
            )

        data = {}

        if embeds:
            if not isinstance(embeds, list):
                embeds = [embeds]

            data["embeds"] = embeds

        if content:
            data["content"] = content

        if username:
            data["username"] = username

        if avatar_url:
            data["avatar_url"] = avatar_url

        if tts:
            data["tts"] = tts

        if kwargs:
            data.update(kwargs)

        return self.call("POST", resource=resource, data=data)
