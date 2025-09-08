from functools import wraps
from pathlib import Path

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


def recreate_session(f):
    """Recreate the otrs session if it is no longer valid."""

    @wraps(f)
    def wrapped(*args, **kwargs):

        if args[0].session_id is None:
            args[0].create_session()

        response = f(*args, **kwargs)
        if response.get("Error"):
            # TicketSearch.AuthFail, TicketUpdate.AuthFail, etc
            if ".AuthFail" in response.get("Error", {}).get("ErrorCode"):
                args[0].create_session()
                response = f(*args, **kwargs)
                if response.get("Error"):
                    raise Exception(response)
            else:
                raise Exception(response)
        return response

    return wrapped


class Otrs(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str,
        auth: tuple = None,
        proxies: dict = None,
        verify: bool | str | None = None,
        user_agent: str = "DevOps",
        save_session_id: bool = False,
        **kwargs,
    ):
        super().__init__(
            baseurl=baseurl,
            api_path=api_path,
            verify=verify,
            proxies=proxies,
            user_agent=user_agent,
            **kwargs,
        )
        self._auth = auth
        self.set_header_field(field="Content-Type", value="application/json")
        self.save_session_id = save_session_id
        self.session_id_path = Path("data/.session_id")
        # If saving is off, then don't use either.
        if self.save_session_id and self.session_id_path.exists():
            self.session_id = self.session_id_path.read_text().strip()
        else:
            self.session_id = None

    def create_session(self):
        resource = "GenericTicketConnectorREST/Session"
        response = self.call(
            method=self.methods.POST,
            resource=resource,
            data={"UserLogin": self._auth[0], "Password": self._auth[1]},
        )
        try:
            self.session_id = response["SessionID"]
            if self.save_session_id:
                self.session_id_path.write_text(self.session_id)
        except Exception:
            raise Exception(f"Error creating session: {response.content}")

    @recreate_session
    def search_ticket(self, **kwargs) -> dict:
        """ "
        TODO: Link docs with all params
        Example params:
        Title='%'+test+'%',
        TicketCreateTimeNewerDate=ts_start,
        SortBy= 'Created',
        OrderBy='Up',
        StateType = ['Open', 'New'],
        # Due to the sorting, If over 25 -> next iteration will catch next batch
        Limit = 25
        """

        resource = "GenericTicketConnectorREST/TicketSearch"

        query_data = {"SessionID": self.session_id}
        query_data.update(**kwargs)
        return self.call(
            method=self.methods.POST,
            resource=resource,
            data=query_data,
        )

    @recreate_session
    def get_ticket(
        self,
        ticket_id: str,
        articles: bool = False,
        attachments: bool = False,
        dynamic_fields: bool = False,
        html_body_as_attachment: bool = False,
    ) -> dict:

        params = {
            "SessionID": self.session_id,
            "AllArticles": int(articles),
            "Attachments": int(attachments),
            "DynamicFields": int(dynamic_fields),
            "HTMLBodyAsAttachment": int(html_body_as_attachment),
        }
        resource = f"GenericTicketConnectorREST/Ticket/{ticket_id}"
        return self.call(
            method=self.methods.GET,
            resource=resource,
            data=params,
        )

    @recreate_session
    def create_ticket(self, ticket: dict, article: dict, dynamic_fields: list = None):
        # https://otrscommunityedition.com/doc/api/otrs/6.0/Perl/Kernel/GenericInterface/Operation/Ticket/TicketCreate.pm.html
        # "Ticket": {
        #    "Title": "test",
        #    "CustomerUser": "test@test.com",
        #    "QueueID": 28,
        #    "Type": "out",
        #    "State": "new",
        #    "Priority": "1 very low",
        # },
        # "Article": {
        #    "Subject": "Test",
        #    "Body": "this is a test",
        #    "ContentType": "text/plain; charset=utf-8",
        # }

        resource = "GenericTicketConnectorREST/Ticket"
        query_data = {
            "SessionID": self.session_id,
            "Ticket": ticket,
            "Article": article,
        }
        if dynamic_fields:
            query_data["DynamicField"] = dynamic_fields

        return self.call(
            method=self.methods.POST,
            resource=resource,
            data=query_data,
        )

    @recreate_session
    def update_ticket(
        self,
        ticket_id: str | None = None,
        ticket_number: int | None = None,
        ticket: dict | None = None,
        article: dict | None = None,
        dynamic_fields: list | None = None,
    ):
        # https://otrscommunityedition.com/doc/api/otrs/6.0/Perl/Kernel/GenericInterface/Operation/Ticket/TicketUpdate.pm.html

        query_data = {"SessionID": self.session_id}

        if ticket_number is not None:
            # The endpoint is not recognized without the /0 but it does nothing.
            resource = "GenericTicketConnectorREST/Ticket/0"
            query_data["TicketNumber"] = ticket_number
        elif ticket_id is not None:
            resource = f"GenericTicketConnectorREST/Ticket/{ticket_id}"
        else:
            raise Exception("MAX one of ticket_id or ticket_number must be provided.")

        if ticket is not None:
            query_data["Ticket"] = ticket
        if article is not None:
            query_data["Article"] = article
        if dynamic_fields is not None:
            query_data["DynamicField"] = dynamic_fields

        return self.call(
            method=self.methods.PATCH,
            resource=resource,
            data=query_data,
        )
