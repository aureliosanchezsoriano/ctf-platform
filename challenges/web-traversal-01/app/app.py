import os
from flask import Flask, request, abort

app = Flask(__name__)

FLAG = os.environ.get("CTF_FLAG", "CTF{placeholder}")
FILES_DIR = "/app/files"

# Write the flag to the filesystem at startup
with open("/flag.txt", "w") as f:
    f.write(FLAG)

STYLE = """
<style>
body{font-family:monospace;background:#1a1a2e;color:#eee;margin:0;padding:20px}
nav{background:#16213e;padding:12px 20px;margin:-20px -20px 20px;display:flex;gap:20px;align-items:center}
nav a{color:#aaa;text-decoration:none}nav a:hover{color:#fff}
.box{background:#16213e;padding:16px;border-radius:8px;margin-bottom:16px}
.file-list{list-style:none;padding:0;margin:0}
.file-list li{padding:8px 0;border-bottom:1px solid #2a2a4e}
.file-list li:last-child{border-bottom:none}
.file-list a{color:#4af;text-decoration:none}
.file-list a:hover{color:#7df}
pre{background:#0a0a1a;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px;white-space:pre-wrap;word-break:break-all}
</style>
"""


@app.route("/")
def index():
    files = os.listdir(FILES_DIR)
    file_links = "".join(
        f'<li><a href="/download?file={f}">{f}</a></li>'
        for f in sorted(files)
    )
    return f"""<!DOCTYPE html><html><head><title>File Server</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">DocServer</strong>
        <a href="/">Files</a>
    </nav>
    <div class="box">
        <h2>Documentation Files</h2>
        <p style="color:#aaa;font-size:13px">Available documents:</p>
        <!-- files served from /app/files/ -->
        <ul class="file-list">{file_links}</ul>
    </div>
    </body></html>"""


@app.route("/download")
def download():
    filename = request.args.get("file", "")
    if not filename:
        abort(400)

    # INTENTIONALLY VULNERABLE — no path sanitization
    filepath = os.path.join(FILES_DIR, filename)

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return f"""<!DOCTYPE html><html><head><title>Not Found</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">DocServer</strong><a href="/">Files</a></nav>
        <div class="box"><p style="color:#e94560">File not found: {filename}</p></div>
        </body></html>""", 404
    except Exception as e:
        return f"""<!DOCTYPE html><html><head><title>Error</title>{STYLE}</head><body>
        <nav><strong style="color:#e94560">DocServer</strong><a href="/">Files</a></nav>
        <div class="box"><p style="color:#e94560">Error: {e}</p></div>
        </body></html>""", 500

    return f"""<!DOCTYPE html><html><head><title>{filename}</title>{STYLE}</head><body>
    <nav><strong style="color:#e94560">DocServer</strong><a href="/">Files</a></nav>
    <div class="box">
        <h2>{filename}</h2>
        <pre>{content}</pre>
    </div>
    </body></html>"""


if __name__ == "__main__":
    os.makedirs(FILES_DIR, exist_ok=True)
    # Create some legitimate files
    with open(f"{FILES_DIR}/readme.txt", "w") as f:
        f.write("Welcome to DocServer.\nUse the file list to browse available documentation.")
    with open(f"{FILES_DIR}/install.txt", "w") as f:
        f.write("Installation Guide\n==================\n1. Download\n2. Extract\n3. Run")
    with open(f"{FILES_DIR}/changelog.txt", "w") as f:
        f.write("Changelog\n=========\nv1.0 - Initial release\nv1.1 - Bug fixes\nv1.2 - New features")
    app.run(host="0.0.0.0", port=5000, debug=False)
