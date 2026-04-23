import os
import json
import sqlite3
import hashlib
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")
DB_PATH = "/tmp/mass.db"

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
.box{background:#16213e;padding:16px;border-radius:8px;margin-bottom:16px}
pre{background:#0a0a1a;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px;white-space:pre-wrap}
code{background:#0a0a1a;padding:2px 6px;border-radius:3px;font-size:12px}
h2{color:#e94560}
h3{color:#aaa;font-size:14px}
.endpoint{border-left:3px solid #e94560;padding-left:12px;margin-bottom:16px}
.method{color:#4af;font-weight:bold}
</style>
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        bio TEXT DEFAULT '',
        role TEXT DEFAULT 'user'
    )""")
    conn.execute("DELETE FROM users")
    conn.execute("INSERT INTO users (username, password, bio, role) VALUES (?, ?, ?, ?)",
                 ("admin", hashlib.sha256(b"admin_secret_9x!").hexdigest(), "Platform administrator", "admin"))
    conn.commit()
    conn.close()


def get_user_by_token(token: str):
    if not token or not token.startswith("Bearer "):
        return None
    username = token.replace("Bearer ", "")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id, username, bio, role FROM users WHERE username = ?",
                       (username,)).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "username": row[1], "bio": row[2], "role": row[3]}


@app.route("/")
def index():
    return f"""<!DOCTYPE html><html><head><title>User API</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">UserAPI v1</strong></nav>
    <div class="box">
        <h2>REST API Documentation</h2>
        <p style="color:#aaa">A simple user management API. Authenticate with your username as Bearer token.</p>
    </div>

    <div class="box">
        <h3>Authentication</h3>
        <p style="color:#aaa;font-size:13px">Use your username as the Bearer token: <code>Authorization: Bearer yourusername</code></p>
    </div>

    <div class="box">
        <h3>Endpoints</h3>

        <div class="endpoint">
            <p><span class="method">POST</span> /api/register</p>
            <p style="color:#aaa;font-size:13px">Register a new user. Body: <code>{{"username": "...", "password": "..."}}</code></p>
        </div>

        <div class="endpoint">
            <p><span class="method">GET</span> /api/users/me</p>
            <p style="color:#aaa;font-size:13px">Get your profile. Requires authentication.</p>
        </div>

        <div class="endpoint">
            <p><span class="method">PUT</span> /api/users/me</p>
            <p style="color:#aaa;font-size:13px">Update your profile. Body: any user fields to update.</p>
        </div>

        <div class="endpoint">
            <p><span class="method">GET</span> /api/admin/secret</p>
            <p style="color:#aaa;font-size:13px">Admin only. Returns the flag.</p>
        </div>
    </div>

    <div class="box">
        <h3>Example</h3>
        <pre># Register
curl -X POST /api/register -H 'Content-Type: application/json' \\
     -d '{{"username":"hacker","password":"pass123"}}'

# Get profile
curl /api/users/me -H 'Authorization: Bearer hacker'

# Update profile
curl -X PUT /api/users/me -H 'Authorization: Bearer hacker' \\
     -H 'Content-Type: application/json' \\
     -d '{{"bio":"I am a hacker"}}'</pre>
    </div>
    </body></html>"""


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, hashlib.sha256(password.encode()).hexdigest()))
        conn.commit()
        return jsonify({"message": "registered", "username": username, "token": username}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "username taken"}), 409
    finally:
        conn.close()


@app.route("/api/users/me", methods=["GET"])
def get_me():
    user = get_user_by_token(request.headers.get("Authorization", ""))
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(user)


@app.route("/api/users/me", methods=["PUT"])
def update_me():
    user = get_user_by_token(request.headers.get("Authorization", ""))
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}

    # INTENTIONALLY VULNERABLE — does not filter the 'role' field
    # Should use: allowed = {'bio'}; data = {k: v for k, v in data.items() if k in allowed}
    allowed_fields = {"bio", "role"}  # 'role' should NOT be here
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify({"error": "nothing to update"}), 400

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user["username"]]

    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"UPDATE users SET {set_clause} WHERE username = ?", values)
    conn.commit()

    row = conn.execute("SELECT id, username, bio, role FROM users WHERE username = ?",
                       (user["username"],)).fetchone()
    conn.close()

    return jsonify({"id": row[0], "username": row[1], "bio": row[2], "role": row[3]})


@app.route("/api/admin/secret")
def admin_secret():
    user = get_user_by_token(request.headers.get("Authorization", ""))
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    if user["role"] != "admin":
        return jsonify({"error": "forbidden", "your_role": user["role"]}), 403
    return jsonify({"secret": FLAG, "message": "Welcome, admin."})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
