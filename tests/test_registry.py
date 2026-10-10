import copy
import json
import tempfile
import unittest
from pathlib import Path
from generate import ROOT, generate, validate


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))

    def test_valid_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(self.data, out)
            first = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            generate(self.data, out)
            self.assertEqual(first, {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()})

    def test_reject_unsafe_destinations(self):
        for url in ['javascript:alert(1)', 'http://github.com/x', '//evil.example/x',
                    'https://github.com.evil.example/x', 'https://evil.example/x',
                    'https://github.com@evil.example/x', 'https://user@github.com/x',
                    'https://github.com:444/x', 'https://github.com\\@evil.example',
                    'https://github.com/\nfoo', 'https://github.com/ foo']:
            with self.subTest(url=url):
                self.data['routes']['test']['url'] = url
                with self.assertRaises(ValueError): validate(self.data)

    def test_reject_bad_structure(self):
        candidates = [None, [], {}, {**self.data, 'version': 99}, {**self.data, 'routes': {}},
                      {**self.data, 'allowed_hosts': ['*']},
                      {**self.data, 'routes': {'../escape': self.data['routes']['test']}},
                      {**self.data, 'routes': {'test': {'url': 'https://github.com/'}}}]
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError): validate(candidate)

    def test_escape_and_atomic_validation(self):
        self.data['routes']['test']['name'] = '<img src=x onerror=alert(1)>'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(self.data, out)
            path = out / 'test/index.html'
            before = path.read_bytes()
            self.assertIn(b'&lt;img', before)
            self.assertNotIn(b'<img', before)
            self.data['routes']['invalid'] = {'url': 'javascript:alert(1)'}
            with self.assertRaises(ValueError): generate(self.data, out)
            self.assertEqual(before, path.read_bytes())

    def test_new_destination_same_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(self.data, out)
            self.data['routes']['test']['url'] += '/blob/main/README.md'
            generate(self.data, out)
            self.assertIn('/blob/main/README.md', (out / 'test/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__': unittest.main()
