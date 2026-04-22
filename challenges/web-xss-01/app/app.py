import os
import sqlite3
from flask import Flask, request, g

app = Flask(__name__)

FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")
DB_PATH = "/tmp/xss.db"

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
nav a{color:#aaa;text-decoration:none}nav a:hover{color:#fff}
textarea{width:100%;padding:8px;background:#0f3460;border:1px solid #444;color:#eee;border-radius:4px;height:80px;resize:vertical}
input[type=text]{width:100%;padding:8px;background:#0f3460;border:1px solid #444;color:#eee;border-radius:4px;box-sizing:border-box}
button{padding:8px 16px;background:#e94560;border:none;color:white;border-radius:4px;cursor:pointer;margin-top:8px}
.comment{background:#16213e;padding:12px;border-radius:4px;margin-bottom:10px}
.comment .author{color:#e94560;font-size:12px;margin-bottom:4px}
.box{background:#16213e;padding:16px;border-radius:4px;margin-bottom:16px}
.collected{background:#0a2a0a;border:1px solid #1a6a1a;padding:12px;border-radius:4px;margin-top:10px;font-size:12px;word-break:break-all}
.flag-hint{background:#0f3460;padding:8px;border-radius:4px;font-size:12px;color:#aaa;margin-top:8px}
</style>
"""

NAV = """
<nav>
    <strong style="color:#e94560">SecBlog</strong>
    <a href="/">Home</a>
    <a href="/comments">Comments</a>
    <a href="/collect">Collector</a>
</nav>
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS comments
        (id INTEGER PRIMARY KEY, author TEXT, body TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS collected
        (id INTEGER PRIMARY KEY, data TEXT)""")
    # Pre-seed one comment from admin
    count = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO comments (author, body) VALUES (?, ?)",
                     ("admin", "Welcome to SecBlog! Feel free to leave comments."))
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


@app.route("/")
def index():
    return f"""<!DOCTYPE html><html><head><title>SecBlog</title>{STYLE}</head><body>{NAV}
    <div class="box">
        <h2>Welcome to SecBlog</h2>
        <p>A blog about web security. Leave a comment on the <a href="/comments">comments page</a>.</p>
        <p>The admin checks new comments regularly. Their session cookie contains something valuable...</p>
        <div class="flag-hint">
            Hint: the admin's cookie is set on the <strong>/comments</strong> page and is not HttpOnly.
            Check <a href="/collect">/collect</a> to receive exfiltrated data.
        </div>
    </div>
    </body></html>"""


@app.route("/comments", methods=["GET", "POST"])
def comments():
    conn = get_db()

    if request.method == "POST":
        author = request.form.get("author", "anonymous")[:32]
        body = request.form.get("body", "")
        if body.strip():
            conn.execute("INSERT INTO comments (author, body) VALUES (?, ?)", (author, body))
            conn.commit()

    rows = conn.execute("SELECT author, body FROM comments ORDER BY id DESC").fetchall()
    conn.close()

    # Build comments HTML — INTENTIONALLY does not escape body
    comments_html = ""
    for author, body in rows:
        comments_html += f"""
        <div class="comment">
            <div class="author">{author}</div>
            <div>{body}</div>
        </div>"""

    # Admin cookie is set on this page — not HttpOnly so JS can read it
    response_html = f"""<!DOCTYPE html><html>
    <head><title>Comments</title>{STYLE}
    <script>
    // Simulate admin reading comments — sets their session cookie
    document.cookie = "admin_session={FLAG}; path=/";
    </script>
    </head><body>{NAV}
    <div class="box">
        <h2>Leave a Comment</h2>
        <form method="POST">
            <input type="text" name="author" placeholder="Your name" style="margin-bottom:8px">
            <textarea name="body" placeholder="Write your comment... (HTML is supported!)"></textarea>
            <button type="submit">Post</button>
        </form>
    </div>
    <h3>Comments ({len(rows)})</h3>
    {comments_html}
    </body></html>"""

    return response_html


@app.route("/collect")
def collect():
    conn = get_db()
    data = request.args.get("data", "")
    if data:
        conn.execute("INSERT INTO collected (data) VALUES (?)", (data,))
        conn.commit()

    rows = conn.execute("SELECT data FROM collected ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    items_html = ""
    for (d,) in rows:
        items_html += f'<div class="collected">{d}</div>'

    return f"""<!DOCTYPE html><html><head><title>Collector</title>{STYLE}</head><body>{NAV}
    <div class="box">
        <h2>Data Collector</h2>
        <p style="color:#aaa;font-size:13px">Receives data exfiltrated via XSS. Last 5 entries shown.</p>
        {items_html if items_html else '<p style="color:#666">Nothing received yet.</p>'}
    </div>
    </body></html>"""


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
