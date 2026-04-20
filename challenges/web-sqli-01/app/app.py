import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Flag is injected at container startup via environment variable
FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")

DB_PATH = "/tmp/challenge.db"

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #16213e; padding: 2rem; border-radius: 8px; width: 320px; }
        h2 { color: #0f3460; text-align: center; color: #e94560; }
        input { width: 100%; padding: 8px; margin: 8px 0; background: #0f3460; border: 1px solid #e94560; color: #eee; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #e94560; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .error { color: #e94560; font-size: 0.85rem; margin-top: 8px; }
        .flag { color: #0f0; font-size: 1.1rem; word-break: break-all; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🔒 Admin Login</h2>
        <form method="POST">
            <input name="username" placeholder="Username" autocomplete="off">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        {% if flag %}<p class="flag">{{ flag }}</p>{% endif %}
    </div>
</body>
</html>
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    conn.execute("DELETE FROM users")
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'sup3rs3cr3t!')")
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    flag = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = sqlite3.connect(DB_PATH)
        # INTENTIONALLY VULNERABLE — do not use in production
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        try:
            cursor = conn.execute(query)
            user = cursor.fetchone()
            if user:
                flag = FLAG
            else:
                error = "Invalid credentials"
        except sqlite3.OperationalError as e:
            error = f"Database error: {e}"
        finally:
            conn.close()

    return render_template_string(LOGIN_HTML, error=error, flag=flag)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
