# API Deprecation Policy

This document describes the deprecation policy for Aragora APIs, including timeline, communication, and migration guidance.

## Table of Contents

- [Overview](#overview)
- [Deprecation Lifecycle](#deprecation-lifecycle)
- [HTTP Headers](#http-headers)
- [Versioning Rules](#versioning-rules)
- [Migration Timeline](#migration-timeline)
- [Developer Guide](#developer-guide)
- [FAQ](#faq)

---

## Overview

Aragora follows a predictable deprecation policy to ensure API stability while enabling evolution. When an endpoint or feature is deprecated:

1. It continues to work normally
2. Deprecation headers are added to responses
3. Documentation is updated
4. After the sunset date, the endpoint returns `410 Gone`

---

## Deprecation Lifecycle

### Phase 1: Announcement

- Deprecation notice added to release notes
- Documentation updated with migration guidance
- `Deprecation: true` header added to responses

### Phase 2: Warning Period (90+ days)

- Endpoint continues to function normally
- Deprecation headers included in all responses
- Sunset date announced via `Sunset` header
- Monitoring of deprecated endpoint usage

### Phase 3: Sunset

- Endpoint returns `410 Gone` status
- Response includes replacement information
- Endpoint removed from documentation

---

## HTTP Headers

### Request Headers

No special headers required. Deprecated endpoints accept normal requests.

### Response Headers

| Header | Description | Example |
|--------|-------------|---------|
| `Deprecation` | Indicates deprecation status | `true` or `2026-01-01` |
| `Sunset` | When endpoint will be removed | `Sat, 01 Jun 2026 00:00:00 GMT` |
| `Link` | Replacement endpoint | `</api/v2/debates>; rel="successor-version"` |

### Example Response

```http
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: true
Sunset: Sat, 01 Jun 2026 00:00:00 GMT
Link: </api/v2/debates>; rel="successor-version"

{"debates": [...]}
```

### Sunset Response (410 Gone)

After the sunset date:

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "ENDPOINT_SUNSET",
    "message": "This endpoint has been removed.",
    "replacement": "/api/v2/debates",
    "suggestion": "Use /api/v2/debates instead"
  }
}
```

---

## Versioning Rules

### Major Versions (v1 → v2)

Major versions may contain breaking changes:
- Removed endpoints
- Changed response formats
- Modified authentication requirements
- Changed error formats

**Policy**: 90-day minimum migration window between major versions.

### Minor Versions

Minor versions add features without breaking changes:
- New endpoints
- New optional response fields
- New optional request parameters
- Performance improvements

**Policy**: No deprecation period required.

### Patch Versions

Patch versions fix bugs only:
- Security fixes
- Bug corrections
- Documentation updates

**Policy**: Deployed immediately.

---

## Migration Timeline

### Standard Deprecation

| Day | Action |
|-----|--------|
| 0 | Deprecation announced, headers added |
| 30 | First reminder in release notes |
| 60 | Usage statistics reviewed |
| 90 | Sunset date reached, endpoint returns 410 |

### Extended Deprecation (High-Impact)

For widely-used endpoints:

| Day | Action |
|-----|--------|
| 0 | Deprecation announced |
| 90 | Usage reviewed, sunset date set |
| 180 | Final reminder |
| 270 | Sunset |

### Emergency Deprecation

For security issues:
- Immediate deprecation notice
- 7-day minimum warning (security permitting)
- Sunset with security patch

---

## Developer Guide

### Detecting Deprecation

#### Python

```python
import requests

response = requests.get("https://api.aragora.io/api/debates")

# Check deprecation headers
if response.headers.get("Deprecation"):
    print("Warning: This endpoint is deprecated")
    sunset = response.headers.get("Sunset")
    replacement = response.headers.get("Link")
    print(f"Sunset: {sunset}")
    print(f"Replacement: {replacement}")
```

#### JavaScript

```javascript
const response = await fetch('https://api.aragora.io/api/debates');

if (response.headers.get('Deprecation')) {
  console.warn('Warning: This endpoint is deprecated');
  console.warn('Sunset:', response.headers.get('Sunset'));
  console.warn('Replacement:', response.headers.get('Link'));
}
```

### Handling Sunset

```python
response = requests.get("https://api.aragora.io/api/old-endpoint")

if response.status_code == 410:
    error = response.json()["error"]
    replacement = error.get("replacement")
    if replacement:
        # Retry with replacement endpoint
        response = requests.get(f"https://api.aragora.io{replacement}")
```

### Migration Checklist

1. [ ] Identify deprecated endpoints in your codebase
2. [ ] Review replacement documentation
3. [ ] Update API calls to new endpoints
4. [ ] Test with staging environment
5. [ ] Deploy changes before sunset date
6. [ ] Monitor for 410 errors in production

---

## What Gets Deprecated

### Endpoints

- Changed URL structure
- Merged into other endpoints
- Replaced by improved versions

### Response Fields

- Fields moved to different location
- Fields renamed for consistency
- Fields replaced with better alternatives

### Request Parameters

- Parameters renamed
- Parameters moved to different location
- Parameters replaced with better alternatives

### Features

- Experimental features not promoted to stable
- Features replaced by better alternatives
- Features with security concerns

---

## What Does NOT Get Deprecated

### Without Major Version

- Required response fields
- Required request parameters
- Authentication methods
- Error code meanings
- Rate limit behavior

These require a major version bump (v1 → v2).

---

## Notifications

### Release Notes

All deprecations are announced in release notes with:
- Affected endpoints/features
- Sunset date
- Migration instructions
- Replacement information

### API Responses

Deprecation headers are added immediately when deprecation is announced.

### Documentation

- Deprecated items marked with warning banner
- Migration guide linked
- Examples updated to show new approach

---

## FAQ

### Q: Can I request a deprecation extension?

Yes, contact support with:
- Your use case
- Why you need more time
- Your migration plan

Extensions are granted case-by-case for legitimate needs.

### Q: Will deprecated endpoints perform differently?

No. Deprecated endpoints perform identically until sunset. The only difference is the added headers.

### Q: How do I know if I'm using deprecated endpoints?

1. Check response headers for `Deprecation`
2. Search your codebase for deprecated endpoint URLs
3. Review the deprecation log at `/api/system/deprecations`

### Q: What happens at sunset?

The endpoint returns:
- HTTP status `410 Gone`
- JSON error with replacement information
- No data processing occurs

### Q: Are there any exceptions to the policy?

Security issues may require faster deprecation. We'll communicate urgency and provide alternatives as quickly as possible.

---

## Implementation Details

### Server-Side

```python
from aragora.server.deprecation import deprecated, add_deprecation_headers

@deprecated(
    sunset="2026-06-01",
    replacement="/api/v2/debates",
    category="api"
)
def _handle_v1_debates(self, handler):
    # Normal processing
    result = self._do_work()

    # Headers are automatically added by the decorator
    return result
```

### Manual Header Addition

```python
from aragora.server.deprecation import add_deprecation_headers

def handle_legacy_endpoint(self, handler):
    result = self._do_work()

    headers = add_deprecation_headers(
        result.headers,
        sunset="2026-06-01",
        replacement="/api/v2/endpoint"
    )

    return HandlerResult(
        status_code=200,
        body=json.dumps(data).encode(),
        headers=headers,
    )
```

---

## See Also

- [API_VERSIONING.md](./API_VERSIONING.md) - Version negotiation
- [API_REFERENCE.md](./API_REFERENCE.md) - Endpoint documentation
- [CHANGELOG.md](./CHANGELOG.md) - Release notes
