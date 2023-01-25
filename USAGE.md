<!-- Start SDK Example Usage -->
```python
import sdk
from sdk.models import operations, shared

s = sdk.SDK()
s.config_security(
    security=shared.Security(
        bearer_auth=shared.SchemeBearerAuth(
            authorization="Bearer YOUR_BEARER_TOKEN_HERE",
        ),
    )
)
    
req = operations.SendEmailRequest(
    request=shared.Email(
        bcc="sit",
        cc="voluptas",
        from_="culpa",
        html="expedita",
        react="consequuntur",
        reply_to="dolor",
        subject="expedita",
        text="voluptas",
        to="fugit",
    ),
)
    
res = s.emails.send_email(req)

if res.send_email_response is not None:
    # handle response
```
<!-- End SDK Example Usage -->