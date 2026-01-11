# Security Policy

## Reporting Vulnerabilities

Email: security@aragora.ai

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x     | Yes       |

## Security Features

- **JWT Authentication**: Token-based auth with configurable expiry
- **Rate Limiting**: Applied to critical endpoints to prevent abuse
- **Input Validation**: All POST handlers validate and sanitize input
- **WebhookStore**: Idempotent processing for Stripe webhooks prevents double-charging
- **CORS Configuration**: Configurable allowed origins via ARAGORA_ALLOWED_ORIGINS
- **SQL Injection Prevention**: Parameterized queries throughout storage layer

## Responsible Disclosure

We follow responsible disclosure practices. Please allow up to 90 days for us to address vulnerabilities before public disclosure.
