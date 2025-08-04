# Run this in the folder you want to share

import http.server
import socketserver
import os
import zipfile
import sys
from urllib.parse import unquote, quote

def print_stylish_title():
    # Gradient color codes (white to blue)
    RESET = '\033[0m'
    BOLD = '\033[1m'
    COLORS = [
        '\033[97m', # White
        '\033[96m', # Bright Cyan
        '\033[94m', # Bright Blue
        '\033[34m', # Blue
        '\033[36m', # Cyan
    ]
    # Clean, stylish banner with gradient
    banner = [
        "\n           ┳┓┓┏┏┓┓┏┏┓┳┓┏┓           ",
        "           ┣┫┃┃┃ ┣┫┣┫┣┫┣            ",
        "           ┛┗┗┛┗┛┛┗┛┗┛┗┗┛           ",
        "",
        "                   by rvchs0n\n\n"
    ]
    for i, line in enumerate(banner):
        color = COLORS[min(i, len(COLORS)-1)]
        print(f"{BOLD}{color}{line}{RESET}")

print_stylish_title()
BRIGHT_CYAN = '\033[96m'
RESET = '\033[0m'
try:
    PORT = int(input(f"Enter port number (default 8000): {BRIGHT_CYAN}") or "8000")
    RESET
except Exception:
    print("Invalid port, using default 8000.")
    PORT = 8000

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Modern, colorful, organized terminal log using only title colors
        import datetime
        from sys import stdout
        # ANSI color codes matching the title
        RESET = '\033[0m'
        BOLD = '\033[1m'
        WHITE = '\033[97m'
        BRIGHT_CYAN = '\033[96m'
        BRIGHT_BLUE = '\033[94m'
        BLUE = '\033[34m'
        CYAN = '\033[36m'
        # Get time, client IP, method, path
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else 'Unknown'
        method = self.command if hasattr(self, 'command') else ''
        path = self.path if hasattr(self, 'path') else ''
        # Format log line with matching colors
        log_line = (
            f"{BOLD}{BRIGHT_CYAN}[{now}]{RESET} "
            f"{BOLD}{WHITE}{client_ip}{RESET} "
            f"{BOLD}{BRIGHT_BLUE}{method}{RESET} "
            f"{BOLD}{CYAN}{path}{RESET} "
            f"{BLUE}" + format % args + f"{RESET}"
        )
        print(log_line, file=stdout)
    def get_windows_drives(self):
        import string
        from ctypes import windll
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
        return drives

    def list_directory(self, path):
        # Universal storage root for all OS
        if (
            (os.name == "nt" and (path in ["", "/", "\\"] or path.replace("/", "") == "")) or
            (hasattr(os, "uname") and os.uname().sysname.lower().startswith("linux") and (path in ["", "/"])) or
            (os.name == "posix" and sys.platform == "darwin" and (path in ["", "/"])) or
            (sys.platform.startswith("android") and (path in ["", "/"]))
        ):
            # Windows: show drives
            if os.name == "nt":
                drives = self.get_windows_drives()
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
                        .parent {{ font-size: 15px, color: #718096; margin-bottom: 18px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Storage Drives</h2>
                        <ul>"""
                for drive in drives:
                    drive_url = quote(drive)
                    # Use a Unicode folder icon for cross-platform compatibility
                    html += f'<li><span class="name dir">📦 <a href="/browse/{drive_url}">{drive}</a></span></li>'
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
            # Mac/Linux/Android/iOS: show root or home
            else:
                # On Android, show /storage or home
                if sys.platform.startswith("android"):
                    root_path = "/storage"
                elif sys.platform == "darwin":
                    root_path = "/"
                elif hasattr(os, "uname") and os.uname().sysname.lower().startswith("linux"):
                    home_dir = os.path.expanduser("~")
                    if "com.termux" in home_dir:
                        root_path = home_dir
                    else:
                        root_path = "/"
                else:
                    root_path = os.path.expanduser("~")
                path = root_path
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
        # Add go back button except for root/drives
        if os.name == "nt":
            # Show 'Go Back to Storage Drives' first, then 'Go Back' below
            html += f'<li class="parent"><a href="/browse/">📦 Go Back to Storage Drives</a></li>'
            if parent != path and parent:
                html += f'<li class="parent"><a href="/browse/{quote(parent)}">⬅️ Go Back</a></li>'
        else:
            # ...existing code for non-Windows...
            if parent != path and parent:
                html += f'<li class="parent"><a href="/browse/{quote(parent)}">⬅️ Go Back</a></li>'
        for entry in entries:
            fullpath = os.path.join(path, entry)
            entry_url = quote(fullpath)
            if os.path.isdir(fullpath):
                html += (
                    f'<li><span class="name dir">📁 <a href="/browse/{entry_url}">{entry}</a></span>'
                    f'<a href="/download/{entry_url}"><button>Download Folder</button></a></li>'
                )
            else:
                ext = os.path.splitext(entry)[1].lower()
                if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    html += (
                        f'<li><span class="name file">'
                        f'<img src="/download/{entry_url}" style="height:64px;max-width:64px;object-fit:cover;border-radius:8px;margin-right:12px;vertical-align:middle;" alt="{entry}"/>'
                        f'{entry}</span>'
                        f'<a href="/download/{entry_url}"><button>Download</button></a></li>'
                    )
                elif ext in [".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"]:
                    html += (
                        f'<li><span class="name file">'
                        f'<video src="/download/{entry_url}" style="height:64px;max-width:64px;object-fit:cover;border-radius:8px;margin-right:12px;vertical-align:middle;" controls muted preload="metadata"></video>'
                        f'{entry}</span>'
                        f'<a href="/download/{entry_url}"><button>Download</button></a></li>'
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
        # If browsing root, show all drives on Windows
        if os.name == "nt" and (self.path in ["/browse/", "/browse", "/browse", "/browse//"]):
            self.list_directory("")
            return
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
            # Default: show all drives on Windows, or root/home on other OS
            if os.name == "nt":
                self.list_directory("")
            elif hasattr(os, "uname") and os.uname().sysname.lower().startswith("linux"):
                home_dir = os.path.expanduser("~")
                if "com.termux" in home_dir:
                    self.list_directory(home_dir)
                else:
                    self.list_directory("/")
            else:
                self.list_directory(os.path.expanduser("~"))

with socketserver.ThreadingTCPServer(("", PORT), CustomHandler) as httpd:
    # Define ANSI color codes to match the title
    RESET = '\033[0m'
    BOLD = '\033[1m'
    WHITE = '\033[97m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_BLUE = '\033[94m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    # Stylish, organized startup message using only title colors and a blue icon
    print(f"\n{BOLD}{BRIGHT_BLUE}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{RESET}")
    print(f"{BOLD}{WHITE}          {BRIGHT_BLUE}💧{WHITE}  File Server is LIVE!{RESET}")
    print(f"{BOLD}{BRIGHT_CYAN}         🔗  Listening on port:{RESET} {BOLD}{CYAN}{PORT}{RESET}")
    print(f"{BOLD}{BLUE}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET}\n")
    httpd.serve_forever()