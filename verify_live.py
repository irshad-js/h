"""Verify all deployed QR routes after Pages deployment completes."""
import argparse
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from generate import BASE, ROOT

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
data = json.loads((ROOT / 'registry.json').read_text(encoding='utf-8'))
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge' if sys.platform == 'win32' else None, headless=True)
    with browser.new_context() as context:
        page = context.new_page()
        for key, item in data['routes'].items():
            url = f'{BASE}/{key}/'
            for suffix in ['', '?url=https://example.org/']:
                page.goto(url + suffix, wait_until='domcontentloaded')
                page.wait_for_url(item['url'], wait_until='domcontentloaded')
                if key.isdecimal():
                    assert page.get_by_role('heading', name=item['name'], exact=True).is_visible()
                results.append({'id': key, 'test': 'live_redirect', 'input': url + suffix, 'destination': page.url})
    with browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844}) as context:
        page = context.new_page()
        for key, item in data['routes'].items():
            response = page.goto(f'{BASE}/{key}/')
            link = page.get_by_role('link', name='Continue to hardware information')
            assert response.status == 200 and link.get_attribute('href') == item['url']
            page.keyboard.press('Tab')
            assert page.locator(':focus').get_attribute('id') == 'destination'
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            if key == '001': page.screenshot(path=str(args.output / 'live-fallback.png'))
            results.append({'id': key, 'test': 'live_nojs_keyboard_fallback', 'status': response.status,
                            'cache_control': response.headers.get('cache-control')})
        response = page.goto(f'{BASE}/nonexistent-probe-id/')
        assert response.status == 404
        assert page.get_by_role('heading', name='Unknown hardware ID').is_visible()
        results.append({'test': 'live_custom_404', 'status': response.status})
    browser.close()
(args.output / 'live-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'{len(results)} live checks passed for {len(data["routes"])} permanent/test routes')
