<!-- Start SDK Example Usage -->
```python
import resend
from resend.models import operations, shared

s = resend.Resend()
s.config_security(
    security=shared.Security(
        bearer_auth=shared.SchemeBearerAuth(
            authorization="Bearer YOUR_BEARER_TOKEN_HERE",
        ),
    )
)
   
req = operations.SendEmailRequest(
    request=shared.Email(
        bcc="unde",
        cc="deserunt",
        from_="porro",
        html="nulla",
        react="id",
        reply_to="vero",
        subject="perspiciatis",
        text="nulla",
        to="nihil",
    ),
)
    
res = s.emails.send_email(req)

if res.send_email_response is not None:
    # handle response
```
<!-- End SDK Example Usage -->