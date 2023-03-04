from __future__ import annotations
import dataclasses
import requests
from ..shared import email as shared_email
from ..shared import sendemailresponse as shared_sendemailresponse
from typing import Optional


@dataclasses.dataclass
class SendEmailRequest:
    request: shared_email.Email = dataclasses.field(metadata={'request': { 'media_type': 'application/json' }})
    

@dataclasses.dataclass
class SendEmailResponse:
    content_type: str = dataclasses.field()
    status_code: int = dataclasses.field()
    raw_response: Optional[requests.Response] = dataclasses.field(default=None)
    send_email_response: Optional[shared_sendemailresponse.SendEmailResponse] = dataclasses.field(default=None)
    