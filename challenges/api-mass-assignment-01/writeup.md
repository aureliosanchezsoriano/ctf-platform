# Mass Assignment — Escalate via API

## Vulnerability
The PUT /api/users/me endpoint updates user fields without restricting which
fields can be modified:

```python
allowed_fields = {"bio"}  # role is NOT allowed
updates = {k: v for k, v in data.items() if k in allowed_fields}
```

## OWASP Reference
A01:2021 — Broken Access Control (Mass Assignment)
