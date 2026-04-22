import os
import json
import base64
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")
SECRET = "supersecretkey123"

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
nav a{color:#aaa;text-decoration:none}
.box{background:#16213e;padding:16px;border-radius:8px;margin-bottom:16px}
input{width:100%;padding:8px;background:#0f3460;border:1px solid #444;color:#eee;border-radius:4px;box-sizing:border-box;margin-bottom:8px}
button{padding:8px 16px;background:#e94560;border:none;color:white;border-radius:4px;cursor:pointer}
.token{word-break:break-all;background:#0a0a1a;padding:12px;border-radius:4px;font-size:12px;color:#4af}
.flag{color:#0f0;font-size:1.1rem;word-break:break-all}
.error{color:#e94560}
pre{background:#0a0a1a;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px}
</style>
"""

USERS = {
    "guest": {"password": "guest123", "role": "guest"},
    "admin": {"password": "s3cr3t_adm1n_p4ss!", "role": "admin"},
}


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(username: str, role: str) -> str:
    import hmac, hashlib
    header = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url_encode(json.dumps({"sub": username, "role": role}).encode())
    signature = b64url_encode(
        hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def verify_token(token: str) -> dict | None:
    """
    INTENTIONALLY VULNERABLE — accepts algorithm=none.
    Does not verify signature when alg is none.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))

        alg = header.get("alg", "").lower()

        if alg == "none":
            # VULNERABILITY: skips signature verification
            return payload

        if alg == "hs256":
            import hmac, hashlib
            expected_sig = b64url_encode(
                hmac.new(SECRET.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(parts[2], expected_sig):
                return None
            return payload

        return None
    except Exception:
        return None


@app.route("/")
def index():
    return f"""<!DOCTYPE html><html><head><title>JWT App</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">JWT App</strong>
        <a href="/">Home</a>
        <a href="/login">Login</a>
        <a href="/admin">Admin Panel</a>
    </nav>
    <div class="box">
        <h2>JWT Authentication Demo</h2>
        <p>Login with <strong>guest / guest123</strong> to get a JWT token.</p>
        <p>The admin panel requires <code>role=admin</code> in the token.</p>
        <p>Can you forge a valid admin token?</p>
    </div>
    </body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    token = None
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            token = create_token(username, user["role"])
        else:
            error = "Invalid credentials"

    return f"""<!DOCTYPE html><html><head><title>Login</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">JWT App</strong>
        <a href="/">Home</a><a href="/login">Login</a><a href="/admin">Admin Panel</a>
    </nav>
    <div class="box">
        <h2>Login</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" value="guest">
            <input type="password" name="password" placeholder="Password" value="guest123">
            <button type="submit">Login</button>
        </form>
        {"<p class='error'>" + error + "</p>" if error else ""}
        {f'''<div style="margin-top:16px">
            <p style="color:#aaa;font-size:13px">Your token:</p>
            <div class="token">{token}</div>
            <p style="color:#aaa;font-size:12px;margin-top:8px">
                Use this token in the Authorization header or paste it at
                <a href="https://jwt.io" target="_blank">jwt.io</a> to inspect it.
            </p>
        </div>''' if token else ""}
    </div>
    </body></html>"""


@app.route("/admin")
def admin():
    auth = request.headers.get("Authorization", "")
    token_param = request.args.get("token", "")
    token = token_param or (auth.replace("Bearer ", "") if auth.startswith("Bearer ") else "")

    if not token:
        return f"""<!DOCTYPE html><html><head><title>Admin</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">JWT App</strong>
            <a href="/">Home</a><a href="/login">Login</a><a href="/admin">Admin Panel</a>
        </nav>
        <div class="box">
            <h2>Admin Panel</h2>
            <p class="error">No token provided.</p>
            <p style="color:#aaa;font-size:13px">
                Pass your token via:<br>
                <code>Authorization: Bearer &lt;token&gt;</code><br>
                or <code>/admin?token=&lt;token&gt;</code>
            </p>
        </div>
        </body></html>"""

    payload = verify_token(token)

    if not payload:
        return f"""<!DOCTYPE html><html><head><title>Admin</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">JWT App</strong>
            <a href="/">Home</a><a href="/login">Login</a><a href="/admin">Admin Panel</a>
        </nav>
        <div class="box">
            <h2>Admin Panel</h2>
            <p class="error">Invalid token.</p>
        </div>
        </body></html>"""

    if payload.get("role") != "admin":
        return f"""<!DOCTYPE html><html><head><title>Admin</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">JWT App</strong>
            <a href="/">Home</a><a href="/login">Login</a><a href="/admin">Admin Panel</a>
        </nav>
        <div class="box">
            <h2>Admin Panel</h2>
            <p class="error">Access denied. Your role is: {payload.get('role')}</p>
            <pre>{json.dumps(payload, indent=2)}</pre>
        </div>
        </body></html>"""

    return f"""<!DOCTYPE html><html><head><title>Admin</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">JWT App</strong>
        <a href="/">Home</a><a href="/login">Login</a><a href="/admin">Admin Panel</a>
    </nav>
    <div class="box">
        <h2>Admin Panel</h2>
        <p style="color:#4a4">Access granted. Welcome, {payload.get('sub')}.</p>
        <pre>{json.dumps(payload, indent=2)}</pre>
        <p>The flag is: <span class="flag">{FLAG}</span></p>
    </div>
    </body></html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
