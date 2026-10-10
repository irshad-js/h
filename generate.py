"""Generate static, reviewable Pages redirects. No runtime registry service."""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
BASE = "https://irshad-js.github.io/h"


def validate(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported registry version")
    hosts = data.get("allowed_hosts")
    if not isinstance(hosts, list) or not hosts or any(
        not isinstance(h, str) or not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", h)
        for h in hosts
    ):
        raise ValueError("Invalid approved hosts")
    routes = data.get("routes")
    if not isinstance(routes, dict) or not routes:
        raise ValueError("Empty registry")
    for key, item in routes.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", key) or key in {"assets", "docs"}:
            raise ValueError("Invalid route ID")
        if not isinstance(item, dict) or set(item) != {"name", "revision", "url"}:
            raise ValueError("Invalid route fields")
        if any(not isinstance(v, str) or not v or len(v) > 2048 for v in item.values()):
            raise ValueError("Invalid route value")
        url = item["url"]
        if any(ord(c) < 33 or ord(c) > 126 for c in url) or "\\" in url:
            raise ValueError("URL must be printable ASCII without spaces or backslashes")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in hosts
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError("Destination must use HTTPS on an approved host")
        if parsed.hostname == "irshad-js.github.io" and parsed.path.startswith("/h/"):
            raise ValueError("Redirect loop into registry")
    return routes


def page(title, body, redirect=False):
    script = '<script src="/h/redirect.js" defer></script>' if redirect else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'">
<title>{html.escape(title)}</title><link rel="stylesheet" href="/h/style.css">{script}</head>
<body><main>{body}</main></body></html>
'''


def generate(data, out):
    routes = validate(data)  # Validate everything before writing anything.
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for key, item in routes.items():
        target = html.escape(item["url"], quote=True)
        name, revision = html.escape(item["name"]), html.escape(item["revision"])
        body = f'<h1>{name}</h1><p>{revision}</p><p>Opening the current hardware page…</p><p><a id="destination" href="{target}">Continue to hardware information</a></p><p>Board ID: {key}</p><noscript><p>Automatic forwarding requires JavaScript. Use the link above.</p></noscript>'
        folder = out / key
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(page(item["name"], body, True), encoding="utf-8")
        index.append(f'<li><a href="/h/{key}/">{name}</a> — {revision}</li>')
    (out / "index.html").write_text(page("Hardware links", '<h1>Hardware links</h1><p>Feasibility prototype. No production boards registered.</p><ul>' + "".join(index) + '</ul>'), encoding="utf-8")
    (out / "404.html").write_text(page("Unknown hardware ID", '<h1>Unknown hardware ID</h1><p>Check the printed board ID.</p><a href="/h/">Hardware index</a>'), encoding="utf-8")
    (out / "redirect.js").write_text('"use strict";\n// Destination comes only from the generated, reviewed link. Ignore URL parameters.\nwindow.location.replace(document.getElementById("destination").href);\n', encoding="utf-8")
    (out / "style.css").write_text('html{color-scheme:light dark;font:1.125rem/1.6 system-ui}body{margin:2rem auto;padding:0 1rem;max-width:44rem}a{color:light-dark(#0645ad,#9cc9ff)}a:focus-visible{outline:3px solid;outline-offset:4px}\n', encoding="utf-8")
    (out / ".nojekyll").touch()


if __name__ == "__main__":
    generate(json.loads((ROOT / "registry.json").read_text(encoding="utf-8")), ROOT / "docs")
