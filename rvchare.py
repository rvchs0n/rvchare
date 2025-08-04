# Run this in the folder you want to share
import http.server
import socketserver
import os
import zipfile
from urllib.parse import unquote, quote

PORT = 8000

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            entries = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        entries.sort(key=lambda a: a.lower())
        displaypath = path.replace("/", "\\")
        html = f"""
        <html>
        <head>
            <title>File Server</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }}
                .container {{ max-width: 900px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 32px; }}
                h2 {{ margin-top: 0; font-weight: 600; color: #2d3748; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ display: flex; align-items: center; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid #eee; }}
                li:last-child {{ border-bottom: none; }}
                .name {{ flex: 1; }}
                .dir {{ color: #3182ce; font-weight: 500; }}
                .file {{ color: #4a5568; }}
                a {{ text-decoration: none; color: #3182ce; }}
                button {{ background: #3182ce; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; cursor: pointer; margin-left: 16px; font-size: 14px; transition: background 0.2s; }}
                button:hover {{ background: #2b6cb0; }}
                .parent {{ font-size: 15px; color: #718096; margin-bottom: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Index of {displaypath}</h2>
                <ul>
        """
        parent = os.path.dirname(path)
        if parent != path:
            html += f'<li class="parent"><a href="/browse/{quote(parent)}">⬅️ Parent Directory</a></li>'
        for entry in entries:
            fullpath = os.path.join(path, entry)
            entry_url = quote(fullpath)
            if os.path.isdir(fullpath):
                html += (
                    f'<li><span class="name dir">📁 <a href="/browse/{entry_url}">{entry}</a></span>'
                    f'<a href="/download/{entry_url}"><button>Download Folder</button></a></li>'
                )
            else:
                html += (
                    f'<li><span class="name file">📄 {entry}</span>'
                    f'<a href="/download/{entry_url}"><button>Download</button></a></li>'
                )
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        encoded = html.encode("utf-8", "surrogateescape")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None

    def translate_path(self, path):
        # Serve files from Windows C:\, Linux /, or Termux home directory, depending on OS
        rel_path = unquote(path.lstrip('/'))
        if os.name == "nt":
            abs_path = os.path.join("C:\\", rel_path)
        elif os.uname().sysname.lower().startswith("linux"):
            # If running on Termux, use home, else use root
            home_dir = os.path.expanduser("~")
            # Check for Termux environment variable
            if "com.termux" in home_dir:
                abs_path = os.path.join(home_dir, rel_path)
            else:
                abs_path = os.path.join("/", rel_path)
        else:
            # Fallback to home directory
            abs_path = os.path.join(os.path.expanduser("~"), rel_path)
        return abs_path

    def do_GET(self):
        if self.path.startswith("/browse/"):
            folder = unquote(self.path[len("/browse/"):])
            if os.path.isdir(folder):
                self.list_directory(folder)
            else:
                self.send_error(404, "Folder not found")
        elif self.path.startswith("/download/"):
            target = unquote(self.path[len("/download/"):])
            if os.path.isdir(target):
                zipname = f"{os.path.basename(target)}.zip"
                with zipfile.ZipFile(zipname, "w") as zipf:
                    for root, dirs, files in os.walk(target):
                        for file in files:
                            filepath = os.path.join(root, file)
                            zipf.write(filepath, os.path.relpath(filepath, target))
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f"attachment; filename={zipname}")
                self.end_headers()
                with open(zipname, "rb") as f:
                    self.wfile.write(f.read())
                os.remove(zipname)
            elif os.path.isfile(target):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(target)}")
                self.end_headers()
                with open(target, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File/Folder not found")
        else:
            # Default: show Windows C:\, Linux /, or Termux home directory, depending on OS
            if os.name == "nt":
                self.list_directory("C:\\")
            elif hasattr(os, "uname") and os.uname().sysname.lower().startswith("linux"):
                home_dir = os.path.expanduser("~")
                if "com.termux" in home_dir:
                    self.list_directory(home_dir)
                else:
                    self.list_directory("/")
            else:
                self.list_directory(os.path.expanduser("~"))

with socketserver.ThreadingTCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()