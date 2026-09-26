import base64
import html
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from string import Template
from urllib.parse import parse_qs

import store

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


def load_env_file(path=os.path.join(BASE_DIR, ".env")):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def read_template(name):
    with open(os.path.join(TEMPLATE_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def render(template_name, values=None):
    values = dict(values or {})
    values.setdefault("banner", read_template("_banner.html"))
    return Template(read_template(template_name)).safe_substitute(values)


def esc(value):
    return html.escape(str(value if value is not None else ""))


class Handler(BaseHTTPRequestHandler):
    server_version = "MapleRow/0.1"

    def log_message(self, fmt, *args):
        if os.environ.get("QUIET_LOG") != "1":
            super().log_message(fmt, *args)

    def send_html(self, body, status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text, status):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def check_admin(self):
        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            self.send_text("ADMIN_PASSWORD is not set", 503)
            return False
        header = self.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                user, _, given = base64.b64decode(header[6:]).decode("utf-8").partition(":")
            except ValueError:
                user, given = "", ""
            if user == "admin" and given == password:
                return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Maple Row admin"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self.send_html(render("form.html"))
        elif path == "/thanks":
            self.send_html(render("thanks.html"))
        elif path == "/admin":
            if self.check_admin():
                self.admin_list()
        elif re.fullmatch(r"/admin/request/\d+", path):
            if self.check_admin():
                self.admin_detail(int(path.rsplit("/", 1)[1]))
        elif path.startswith("/static/"):
            self.static(path[len("/static/"):])
        else:
            self.send_text("Not found", 404)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path != "/request":
            self.send_text("Not found", 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = {k: v[0].strip() for k, v in parse_qs(raw).items()}
        missing = [f for f in ("name", "phone", "consent") if not form.get(f)]
        if missing:
            self.send_text("Missing required field(s): " + ", ".join(missing), 400)
            return
        store.add_request(form)
        self.redirect("/thanks")

    def admin_list(self):
        rows = []
        for r in store.list_requests():
            rows.append(
                "<tr><td>{id}</td><td>{created}</td><td>{name}</td><td>{service}</td><td>{date}</td>"
                '<td><a href="/admin/request/{id}">view</a></td></tr>'.format(
                    id=r["id"], created=esc(r["created_at"]), name=esc(r["name"]),
                    service=esc(r["service"]), date=esc(r["preferred_date"])))
        self.send_html(render("admin_list.html", {"rows": "\n".join(rows)}))

    def admin_detail(self, request_id):
        r = store.get_request(request_id)
        if r is None:
            self.send_text("Not found", 404)
            return
        values = {k: esc(v) for k, v in r.items()}
        values["consent"] = "yes" if r["consent"] else "no"
        self.send_html(render("admin_detail.html", values))

    def static(self, name):
        full = os.path.normpath(os.path.join(STATIC_DIR, name))
        if not full.startswith(STATIC_DIR + os.sep) or not os.path.isfile(full):
            self.send_text("Not found", 404)
            return
        with open(full, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(full)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(port, db_path):
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    store.init(db_path)
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    load_env_file()
    port = int(os.environ.get("PORT", "8000"))
    db_path = os.environ.get("DB_PATH", os.path.join("data", "requests.db"))
    httpd = make_server(port, db_path)
    print(f"Maple Row preview running on http://127.0.0.1:{httpd.server_address[1]}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
