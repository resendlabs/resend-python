import dataclasses
from ..shared import email as shared_email
from ..shared import sendemailresponse as shared_sendemailresponse
from ..utils import retryconfig as utils_retryconfig
from typing import Optional


@dataclasses.dataclass
class SendEmailRequest:
    request: shared_email.Email = dataclasses.field(metadata={'request': { 'media_type': 'application/json' }})
    retries: Optional[utils.RetryConfig] = dataclasses.field(default=None)
    

@dataclasses.dataclass
class SendEmailResponse:
    content_type: str = dataclasses.field()
    status_code: int = dataclasses.field()
    send_email_response: Optional[shared_sendemailresponse.SendEmailResponse] = dataclasses.field(default=None)
    