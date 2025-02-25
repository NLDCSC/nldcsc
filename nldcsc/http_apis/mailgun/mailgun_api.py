import base64
import json
import pathlib
from typing import List, Any

import requests

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class MailgunAPI(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str = None,
        proxies: dict = None,
        user_agent: str = "MailGun",
        api_key: str = "",
        **kwargs,
    ):
        super().__init__(
            baseurl=baseurl,
            api_path=api_path,
            proxies=proxies,
            user_agent=user_agent,
            **kwargs,
        )

        self.set_header_field("access-token", f"{api_key}")

    def ping(self) -> bool:
        resource = ""
        try:
            data = self.call(self.methods.GET, resource=resource, timeout=5)
            if "ApplicationName" in data:
                return True
        except ConnectionError:
            return False

    def get_applications_list(self) -> dict[str, List[str] | str]:
        resource = "applications"
        return self.call(self.methods.GET, resource=resource)

    def get_application_template_list(self, application: str) -> dict[str, List[str]]:
        resource = f"applications/{application}"
        try:
            return self.call(self.methods.GET, resource=resource)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def create_application(self, application: str) -> dict[str, str]:
        resource = f"applications/{application}"
        return self.call(self.methods.PUT, resource=resource)

    def delete_application(self, application: str) -> dict[str, str]:
        resource = f"applications/{application}"
        try:
            return self.call(self.methods.DELETE, resource=resource)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def get_application_template(
        self, application: str, template_name: str
    ) -> dict[str, str]:
        resource = f"applications/{application}/template/{template_name}"
        try:
            return self.call(self.methods.GET, resource=resource)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def download_application_template(
        self, application: str, template_name: str, output_path: pathlib.Path | str
    ) -> bool:
        template_data = self.get_application_template(application, template_name)

        if "errors" in template_data:
            raise RuntimeError(template_data["errors"])

        try:
            with open(output_path, "wb") as output_file:
                output_file.write(base64.b64decode(template_data["mjml_content"]))
            return True
        except KeyError:
            return False

    @staticmethod
    def fetch_template_from_location(location: str | pathlib.Path) -> str:
        try:
            with open(str(location), "r") as template:
                template_data = template.read()
            return template_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file {location} not found")

    def create_application_template(
        self, application: str, template_name: str, template_path: pathlib.Path | str
    ) -> dict[str, str]:
        template_data = self.fetch_template_from_location(template_path)

        resource = f"applications/{application}/template/{template_name}"
        data = {
            "mjml_content": base64.b64encode(template_data.encode()).decode("utf-8"),
            "template": f"{template_name}",
        }
        try:
            return self.call(self.methods.POST, resource=resource, data=data)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def update_application_template(
        self, application: str, template_name: str, template_path: pathlib.Path | str
    ) -> dict[str, str]:
        template_data = self.fetch_template_from_location(template_path)

        resource = f"applications/{application}/template/{template_name}"
        data = {
            "mjml_content": base64.b64encode(template_data.encode()).decode("utf-8"),
            "template": f"{template_name}",
        }
        try:
            return self.call(self.methods.PUT, resource=resource, data=data)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def delete_application_template(
        self, application: str, template_name: str
    ) -> dict[str, str]:
        resource = f"applications/{application}/template/{template_name}"
        try:
            return self.call(self.methods.DELETE, resource=resource)
        except requests.exceptions.ConnectionError as err:
            return json.loads(str(err))

    def get_queue_length(self) -> dict[str, int]:
        resource = "queue"
        return self.call(self.methods.GET, resource=resource)

    def get_queue_schedule(self) -> dict[str, List[str] | int]:
        resource = "queue/schedule"
        return self.call(self.methods.GET, resource=resource)

    def get_queue_items(self) -> dict[str, List[str] | int]:
        resource = "queue/items"
        return self.call(self.methods.GET, resource=resource)

    def get_queue_item(self, item_name: str) -> dict[str, Any]:
        resource = f"queue/items/{item_name}"
        return self.call(self.methods.GET, resource=resource)

    def delete_queue_item(self, item_name: str) -> dict[str, Any]:
        resource = f"queue/items/{item_name}"
        return self.call(self.methods.DELETE, resource=resource)

    def send_mail_with_template(
        self, application: str, template_name: str, email_data: dict[str, Any]
    ) -> dict[str, List[str] | str]:
        """
        Check ../mail_objects.py for structure of email_data --> class Email (pydantic dependency needed if used)
        """
        resource = f"emails/{application}/template/{template_name}"
        return self.call(self.methods.POST, resource=resource, data=email_data)

    def send_batch_with_template(
        self, application: str, email_data: List[dict[str, Any]]
    ) -> dict[str, List[str] | str]:
        """
        Check ../mail_objects.py for structure of email_data --> class BatchEmail (pydantic dependency needed if used)
        """
        resource = f"emails/{application}/batch"
        return self.call(self.methods.POST, resource=resource, data=email_data)
