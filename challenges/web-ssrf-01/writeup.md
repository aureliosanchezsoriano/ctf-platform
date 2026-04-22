# SSRF — Access the internal API

## Vulnerability
The `/fetch` endpoint makes HTTP requests to any URL provided by the user:
```python
resp = requests.get(url, timeout=5)
```

No validation is performed on the URL. This allows an attacker to make the
server send requests to internal services that are not accessible externally.

## Exploit
The internal API runs on `localhost:8080` and exposes the flag at `/secret`.
From outside the container, port 8080 is not exposed. But the server itself
can reach it.

Submit this URL in the fetch form:
http://localhost:8080/secret
The server fetches its own internal API and returns the flag in the response.

## Fix
Validate the URL before making the request:
```python
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    blocked = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
    return hostname not in blocked and not hostname.startswith("192.168.") \
           and not hostname.startswith("10.") and not hostname.startswith("169.254.")
```

## OWASP Reference
A10:2021 — Server-Side Request Forgery (SSRF)
