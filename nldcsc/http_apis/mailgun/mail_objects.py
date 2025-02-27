from typing import List, Any, Optional

from pydantic import BaseModel


class EmailAttachment(BaseModel):
    Name: str
    Content: str
    ContentType: str = "text/plain"

    # {
    #     "Name": "readme.txt",
    #     "Content": "dGVzdCBjb250ZW50",
    #     "ContentType": "text/plain",
    # }


class Email(BaseModel):
    From: List[str] | str
    To: List[str] | str
    Subject: str
    Cc: Optional[List[str] | str] = None
    Bcc: Optional[List[str] | str] = None
    Headers: Optional[dict[str, str]] = None
    Attachments: Optional[List[EmailAttachment]] = None
    TemplateData: dict[str, Any]
    Send_at: Optional[int] = None

    # {
    #     "From": "sender@example.com",
    #     "To": "receiver@example.com",
    #     "Cc": "copied@example.com",
    #     "Bcc": "blank-copied@example.com",
    #     "Subject": "Test subject",
    #     "Headers": {"Name": "CUSTOM-HEADER", "Value": "value"},
    #     "Attachments": [
    #         {
    #             "Name": "readme.txt",
    #             "Content": "dGVzdCBjb250ZW50",
    #             "ContentType": "text/plain",
    #         },
    #         {
    #             "Name": "report.pdf",
    #             "Content": "dGVzdCBjb250ZW50",
    #             "ContentType": "application/octet-stream",
    #         },
    #     ],
    #     "TemplateData": {
    #         "date": "2025-08",
    #         "departments": [
    #             {
    #                 "title": "MT",
    #                 "content": "Lorem ipsum odor amet, consectetuer adipiscing elit.",
    #             },
    #             {
    #                 "title": "Basic Monitoring",
    #                 "content": "Lorem ipsum odor amet, consectetuer adipiscing elit. Sapien blandit "
    #                            "sagittis laoreet sociosqu congue vulputate urna vehicula.",
    #             },
    #         ],
    #     },
    #     "Send_at": 1740145440,
    # }


class BatchTemplate(Email):
    Template: str


class BatchEmail(BaseModel):
    Messages: List[BatchTemplate]

    # {
    #     "Messages": [
    #         {
    #             "Template": "weekbrief",
    #             "From": "sender@example.com",
    #             "To": "receiver@example.com",
    #             "Cc": "copied@example.com",
    #             "Bcc": "blank-copied@example.com",
    #             "Subject": "Test subject",
    #             "Headers": {"Name": "CUSTOM-HEADER", "Value": "value"},
    #             "Attachments": [
    #                 {
    #                     "Name": "readme.txt",
    #                     "Content": "dGVzdCBjb250ZW50",
    #                     "ContentType": "text/plain",
    #                 },
    #                 {
    #                     "Name": "report.pdf",
    #                     "Content": "dGVzdCBjb250ZW50",
    #                     "ContentType": "application/octet-stream",
    #                 },
    #             ],
    #             "TemplateData": {
    #                 "date": "2025-08",
    #                 "departments": [
    #                     {
    #                         "title": "MT",
    #                         "content": "Lorem ipsum odor amet, consectetuer adipiscing elit.",
    #                     },
    #                     {
    #                         "title": "Basic Monitoring",
    #                         "content": "Lorem ipsum odor amet, consectetuer adipiscing elit. Sapien blandit "
    #                         "sagittis laoreet sociosqu congue vulputate urna vehicula.",
    #                     },
    #                 ],
    #             },
    #             "Send_at": 1740145440,
    #         },
    #         {
    #             "Template": "weekbrief2",
    #             "From": "sender@example.com",
    #             "To": "receiver@example.com",
    #             "Cc": "copied@example.com",
    #             "Bcc": "blank-copied@example.com",
    #             "Subject": "Test subject",
    #             "Headers": {"Name": "CUSTOM-HEADER", "Value": "value"},
    #             "Attachments": [
    #                 {
    #                     "Name": "readme.txt",
    #                     "Content": "dGVzdCBjb250ZW50",
    #                     "ContentType": "text/plain",
    #                 },
    #                 {
    #                     "Name": "report.pdf",
    #                     "Content": "dGVzdCBjb250ZW50",
    #                     "ContentType": "application/octet-stream",
    #                 },
    #             ],
    #             "TemplateData": {
    #                 "date": "2025-08",
    #                 "departments": [
    #                     {
    #                         "title": "MT",
    #                         "content": "Lorem ipsum odor amet, consectetuer adipiscing elit.",
    #                     },
    #                     {
    #                         "title": "Basic Monitoring",
    #                         "content": "Lorem ipsum odor amet, consectetuer adipiscing elit. Sapien blandit "
    #                         "sagittis laoreet sociosqu congue vulputate urna vehicula.",
    #                     },
    #                 ],
    #             },
    #         },
    #     ]
    # }
