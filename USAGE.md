<!-- Start SDK Example Usage -->
```python
import resend
from resend.models import operations, shared

s = resend.Resend()
s.config_security(
    security=shared.Security(
        bearer_auth="Bearer YOUR_BEARER_TOKEN_HERE",
    )
)
   
req = operations.SendEmailRequest(
    request=shared.Email(
        bcc="unde",
        cc="deserunt",
        from_="porro",
        html="nulla",
        reply_to="id",
        subject="vero",
        text="perspiciatis",
        to="nulla",
    ),
)
    
res = s.email.send_email(req)

if res.send_email_response is not None:
    # handle response
```
<!-- End SDK Example Usage -->