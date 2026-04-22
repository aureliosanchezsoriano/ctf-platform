import os
import threading
import requests
from flask import Flask, request
from http.server import HTTPServer, BaseHTTPRequestHandler

app = Flask(__name__)
FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
nav a{color:#aaa;text-decoration:none}nav a:hover{color:#fff}
.box{background:#16213e;padding:16px;border-radius:8px;margin-bottom:16px}
input[type=text]{width:100%;padding:8px;background:#0f3460;border:1px solid #444;color:#eee;
border-radius:4px;box-sizing:border-box;margin-bottom:8px;font-family:monospace}
button{padding:8px 16px;background:#e94560;border:none;color:white;border-radius:4px;cursor:pointer}
pre{background:#0a0a1a;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px;
white-space:pre-wrap;word-break:break-all;max-height:300px;overflow-y:auto}
.error{color:#e94560}
.label{color:#aaa;font-size:12px;margin-bottom:4px}
</style>
"""

NAV = '<nav><strong style="color:#e94560">URLFetcher</strong><a href="/">Home</a><a href="/fetch">Fetch</a></nav>'


# ── Internal API server (only accessible from localhost) ──────────────────────

class InternalAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/secret":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"INTERNAL SECRET: {FLAG}".encode())
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")

    def log_message(self, format, *args):
        pass  # suppress access logs


def run_internal_api():
    server = HTTPServer(("127.0.0.1", 8080), InternalAPIHandler)
    server.serve_forever()


# ── Main app ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return f"""<!DOCTYPE html><html><head><title>URLFetcher</title>{STYLE}</head><body>
    {NAV}
    <div class="box">
        <h2>URL Fetcher</h2>
        <p>This tool fetches any URL and displays the response. Useful for previewing external content.</p>
        <p style="color:#aaa;font-size:13px">
            Try fetching <code>https://example.com</code> to see it in action.
        </p>
        <a href="/fetch" style="color:#4af">Go to fetcher</a>
    </div>
    <div class="box">
        <p style="color:#aaa;font-size:12px">
            Note: this server also runs an internal monitoring API on port 8080.
            It is only accessible from localhost and contains sensitive information.
        </p>
    </div>
    </body></html>"""


@app.route("/fetch", methods=["GET", "POST"])
def fetch():
    result = None
    error = None
    fetched_url = ""

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        fetched_url = url

        if not url:
            error = "Please enter a URL"
        else:
            try:
                # INTENTIONALLY VULNERABLE — no SSRF protection
                # Should blocklist: 127.0.0.1, localhost, 169.254.x.x, 10.x.x.x, etc.
                resp = requests.get(url, timeout=5, allow_redirects=True)
                result = resp.text[:2000]  # limit output size
            except requests.exceptions.ConnectionError:
                error = f"Could not connect to: {url}"
            except requests.exceptions.Timeout:
                error = f"Request timed out: {url}"
            except Exception as e:
                error = f"Error: {e}"

    return f"""<!DOCTYPE html><html><head><title>Fetch</title>{STYLE}</head><body>
    {NAV}
    <div class="box">
        <h2>Fetch a URL</h2>
        <form method="POST">
            <div class="label">URL to fetch:</div>
            <input type="text" name="url" value="{fetched_url}"
                placeholder="https://example.com">
            <button type="submit">Fetch</button>
        </form>
    </div>
    {"<div class='box'><div class='label'>Response:</div><pre>" + result + "</pre></div>" if result else ""}
    {"<div class='box'><p class='error'>" + error + "</p></div>" if error else ""}
    </body></html>"""


if __name__ == "__main__":
    # Start internal API in background thread
    t = threading.Thread(target=run_internal_api, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
