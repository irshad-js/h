"""Real browser checks against local generated HTML, with network targets stubbed."""
import functools
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import tempfile
import threading
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from generate import ROOT, generate


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / 'h'
        cls.data = json.loads((ROOT / 'registry.json').read_text(encoding='utf-8'))
        cls.data['routes']['test'] = {'name': 'Test board', 'revision': 'Prototype', 'url': 'https://github.com/irshad-js/h'}
        generate(cls.data, cls.out)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=cls.tmp.name))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}/h/'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='msedge' if sys.platform == 'win32' else None, headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.tmp.cleanup()

    def context(self, **kwargs):
        context = self.browser.new_context(**kwargs)
        context.route('https://github.com/**', lambda route: route.fulfill(body='<title>Destination</title><h1>Destination</h1>'))
        self.addCleanup(context.close)
        return context

    def test_redirect_ignores_query_and_replaces_history(self):
        page = self.context().new_page()
        page.goto(self.base)
        page.goto(self.base + 'test/?url=https://evil.example/#https://evil.example/')
        page.wait_for_url('https://github.com/irshad-js/h')
        page.go_back(); page.wait_for_url(self.base)

    def test_no_javascript_keyboard_fallback(self):
        page = self.context(java_script_enabled=False, viewport={'width': 320, 'height': 640}).new_page()
        page.goto(self.base + 'test/')
        self.assertTrue(page.get_by_role('heading', name='Test board').is_visible())
        page.keyboard.press('Tab')
        self.assertEqual(page.locator(':focus').get_attribute('id'), 'destination')
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        page.keyboard.press('Enter'); page.wait_for_url('https://github.com/irshad-js/h')

    def test_unknown_route_and_help(self):
        page = self.context().new_page()
        response = page.goto(self.base + 'unregistered/')
        self.assertEqual(response.status, 404)
        page.goto(self.base + '404.html')
        self.assertTrue(page.get_by_role('heading', name='Unknown hardware ID').is_visible())
        self.assertTrue(page.get_by_role('link', name='Hardware index').is_visible())

    def test_destination_changes_same_url(self):
        page = self.context().new_page()
        try:
            self.data['routes']['test']['url'] = 'https://github.com/irshad-js/h/blob/main/README.md'
            generate(self.data, self.out)
            page.goto(self.base + 'test/')
            page.wait_for_url(self.data['routes']['test']['url'])
        finally:
            self.data['routes']['test']['url'] = 'https://github.com/irshad-js/h'
            generate(self.data, self.out)

    def test_production_information_and_mobile_access(self):
        context = self.context(viewport={'width': 320, 'height': 640})
        # Map the generated site origin so actual same-origin production redirects run.
        def serve(route):
            path = self.out / route.request.url.split('/h/', 1)[1]
            route.fulfill(path=str(path / 'index.html' if path.is_dir() else path))
        context.route('https://irshad-js.github.io/h/**', serve)
        page = context.new_page()
        for key, item in self.data['routes'].items():
            if not key.isdecimal(): continue
            page.goto(self.base + key + '/')
            page.wait_for_url(item['url'])
            self.assertTrue(page.get_by_role('heading', name=item['name'], exact=True).is_visible())
            self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
