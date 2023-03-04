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
        from_="hello@resend.com",
        to="thefuture@yourcompany.com",
        subject="Welcome to Resend!",
        text="Hello, World!",
    ),
)
    
res = s.email.send_email(req)

if res.send_email_response is not None:
    # handle response
```