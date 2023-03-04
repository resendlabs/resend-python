<div align="center">
    <picture>
        <source srcset="https://user-images.githubusercontent.com/68016351/221072893-61d9e99a-ed2a-4f58-b167-0ff2cbea0614.svg" media="(prefers-color-scheme: dark)" width="500">
        <img src="https://user-images.githubusercontent.com/68016351/221070388-c5faf78a-d3b7-440b-a300-c2e7b635279b.svg" width="500">
    </picture>
   <p>Resend is the email platform for developers.</p>
   <a href="https://resend.com/docs/api-reference/concepts"><img src="https://img.shields.io/static/v1?label=Docs&message=API Ref&color=000000&style=for-the-badge" /></a>
   <a href="https://github.com/resendlabs/resend-python/actions"><img src="https://img.shields.io/github/actions/workflow/status/resendlabs/resend-python/speakeasy_sdk_generation.yaml?style=for-the-badge" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" /></a>
  <a href="https://github.com/resendlabs/resend-python/releases"><img src="https://img.shields.io/github/v/release/resendlabs/resend-python?sort=semver&style=for-the-badge" /></a>
</div>

<!-- Start SDK Installation -->
## SDK Installation

```bash
pip install resend-client-sdk-python
```
<!-- End SDK Installation -->

## Authentication

To authenticate you need to add an Authorization header with the contents of the header being Bearer re_123456789 where re_123456789 is your API Key. First, you need to get an API key, which is available in the [Resend Dashboard](https://resend.com/login).

```bash
Authorization: Bearer re_123
```

## SDK Example Usage
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

<!-- Start SDK Available Operations -->
## SDK Available Operations


### email

* `send_email` - Send an email
<!-- End SDK Available Operations -->

## Contributions

While we value open-source contributions to this SDK, this library is generated programmatically. Feel free to open a PR or a Github issue as a proof of concept and we'll do our best to include it in a future release !

### SDK Generated by [Speakeasy](https://docs.speakeasyapi.dev/docs/using-speakeasy/client-sdks)
