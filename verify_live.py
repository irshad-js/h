"""Exercise deployed Pages in a real browser. Run after deployment completes."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('expected')
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
url = 'https://irshad-js.github.io/h/test/'
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    with browser.new_context() as context:
        page = context.new_page()
        for suffix in ['', '?url=https://example.org/']:
            page.goto(url + suffix, wait_until='domcontentloaded')
            page.wait_for_url(args.expected, wait_until='domcontentloaded')
            results.append({'test': 'live_redirect', 'input': url + suffix, 'destination': page.url})
    with browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844}) as context:
        page = context.new_page()
        response = page.goto(url)
        link = page.get_by_role('link', name='Continue to hardware information')
        assert response.status == 200 and link.get_attribute('href') == args.expected
        page.keyboard.press('Tab')
        assert page.locator(':focus').get_attribute('id') == 'destination'
        page.screenshot(path=str(args.output / 'live-fallback.png'))
        results.append({'test': 'live_nojs_keyboard_fallback', 'status': response.status,
                        'cache_control': response.headers.get('cache-control')})
        response = page.goto('https://irshad-js.github.io/h/nonexistent-probe-id/')
        assert response.status == 404
        assert page.get_by_role('heading', name='Unknown hardware ID').is_visible()
        results.append({'test': 'live_custom_404', 'status': response.status})
    browser.close()
(args.output / 'live-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
