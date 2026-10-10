"""Generate static, reviewable Pages redirects. No runtime registry service."""
import html
import argparse
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
BASE = "https://irshad-js.github.io/h"


def validate_url(url, hosts):
    if not isinstance(url, str) or not url or len(url) > 2048:
        raise ValueError("Invalid URL")
    if any(ord(c) < 33 or ord(c) > 126 for c in url) or "\\" in url:
        raise ValueError("URL must be printable ASCII without spaces or backslashes")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in hosts
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ValueError("Destination must use HTTPS on an approved host")
    return parsed


def load_information():
    return json.loads((ROOT / 'hardware.json').read_text(encoding='utf-8'))


def validate(data, information=None):
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
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", key) or key in {"assets", "docs", "info"}:
            raise ValueError("Invalid route ID")
        if not isinstance(item, dict) or set(item) != {"name", "revision", "url"}:
            raise ValueError("Invalid route fields")
        if any(not isinstance(v, str) or not v or len(v) > 2048 for v in item.values()):
            raise ValueError("Invalid route value")
        parsed = validate_url(item['url'], hosts)
        if parsed.hostname == "irshad-js.github.io" and parsed.path.startswith("/h/"):
            if not re.fullmatch(r'/h/info/[0-9]{3}/', parsed.path) or parsed.query or parsed.fragment:
                raise ValueError("Redirect loop or unknown local information page")
            information = load_information() if information is None else information
            if parsed.path.split('/')[-2] not in information:
                raise ValueError("Missing local information page")
    information = load_information() if information is None else information
    if not isinstance(information, dict):
        raise ValueError('Invalid information registry')
    for key, info in information.items():
        if not isinstance(key, str) or not re.fullmatch(r'[0-9]{3}', key) or key not in routes:
            raise ValueError('Information page requires a registered numeric ID')
        if not isinstance(info, dict) or set(info) != {'purpose', 'power', 'connectors', 'notes', 'links'}:
            raise ValueError('Invalid information fields')
        for field in ['purpose', 'power']:
            if not isinstance(info[field], str) or not info[field] or len(info[field]) > 4096:
                raise ValueError('Invalid information text')
        for field in ['connectors', 'notes']:
            if not isinstance(info[field], list) or any(not isinstance(v, str) or not v or len(v) > 4096 for v in info[field]):
                raise ValueError('Invalid information list')
        if not isinstance(info['links'], list):
            raise ValueError('Invalid usage links')
        for link in info['links']:
            if not isinstance(link, dict) or set(link) != {'label', 'url'} or not isinstance(link['label'], str) or not link['label']:
                raise ValueError('Invalid usage link')
            validate_url(link['url'], hosts)
    for key in routes:
        if key.isdecimal() and key not in information:
            raise ValueError('Numeric routes require a retained information page')
    return routes


def validate_history(data, previous):
    for key, old in previous['routes'].items():
        new = data['routes'].get(key)
        if new is None or any(new[field] != old[field] for field in ['name', 'revision']):
            raise ValueError(f'Published ID removed or reassigned: {key}')


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


def generate(data, out, information=None):
    information = load_information() if information is None else information
    routes = validate(data, information)  # Validate everything before writing anything.
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
    for key, info in information.items():
        item = routes[key]
        def items(values):
            return '<ul>' + ''.join('<li>' + html.escape(v) + '</li>' for v in values) + '</ul>'
        links = '<ul>' + ''.join(f'<li><a href="{html.escape(v["url"], quote=True)}">{html.escape(v["label"])}</a></li>' for v in info['links']) + '</ul>'
        body = (f'<h1>{html.escape(item["name"])}</h1><p>Hardware ID: {key} · PCB revision: {html.escape(item["revision"])}</p>'
                + '<h2>Purpose</h2><p>' + html.escape(info['purpose']) + '</p>'
                + '<h2>Power and connection limits</h2><p>' + html.escape(info['power']) + '</p>'
                + '<h2>Connectors</h2>' + items(info['connectors'])
                + '<h2>Usage and revision notes</h2>' + items(info['notes'])
                + '<h2>Further information</h2>' + links
                + '<p><a href="/h/">Hardware index</a></p>')
        folder = out / 'info' / key
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'index.html').write_text(page(item['name'], body), encoding='utf-8')
    (out / "index.html").write_text(page("Vinyaan hardware information", '<h1>Vinyaan hardware information</h1><p>Find connection guidance for your hardware revision.</p><ul>' + "".join(index) + '</ul>'), encoding="utf-8")
    (out / "404.html").write_text(page("Unknown hardware ID", '<h1>Unknown hardware ID</h1><p>Check the printed board ID.</p><a href="/h/">Hardware index</a>'), encoding="utf-8")
    (out / "redirect.js").write_text('"use strict";\n// Destination comes only from the generated, reviewed link. Ignore URL parameters.\nwindow.location.replace(document.getElementById("destination").href);\n', encoding="utf-8")
    (out / "style.css").write_text('html{color-scheme:light dark;font:1.125rem/1.6 system-ui}body{margin:2rem auto;padding:0 1rem;max-width:44rem;overflow-wrap:anywhere}a{color:#0645ad}a:focus-visible{outline:3px solid;outline-offset:4px}@media(prefers-color-scheme:dark){a{color:#9cc9ff}}\n', encoding="utf-8")
    (out / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--against', type=Path, help='Previously published registry; reject removed/reassigned IDs')
    args = parser.parse_args()
    data = json.loads((ROOT / 'registry.json').read_text(encoding='utf-8'))
    if args.against:
        validate_history(data, json.loads(args.against.read_text(encoding='utf-8')))
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(data, out)
            expected = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            actual = {p.relative_to(ROOT / 'docs'): p.read_bytes() for p in (ROOT / 'docs').rglob('*') if p.is_file()}
            if expected != actual:
                raise SystemExit('Generated docs drift; run python generate.py')
        print('Registry and generated docs verified')
    else:
        generate(data, ROOT / 'docs')
