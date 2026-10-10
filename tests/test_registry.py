import copy
import json
import tempfile
import unittest
from pathlib import Path
from generate import ROOT, generate, validate, validate_history


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

    def test_published_routes_cannot_be_removed_or_reassigned(self):
        for change in ['remove', 'name', 'revision']:
            candidate = copy.deepcopy(self.data)
            if change == 'remove': del candidate['routes']['001']
            else: candidate['routes']['001'][change] = 'Different hardware'
            with self.assertRaises(ValueError): validate_history(candidate, self.data)
        candidate = copy.deepcopy(self.data)
        candidate['routes']['001']['url'] = 'https://github.com/irshad-js/h'
        validate_history(candidate, self.data)

    def test_local_information_target_and_loop_rejection(self):
        for url in ['https://irshad-js.github.io/h/001/', 'https://irshad-js.github.io/h/info/999/',
                    'https://irshad-js.github.io/h/info/001/?url=evil', 'https://irshad-js.github.io/h/info/001/#evil']:
            candidate = copy.deepcopy(self.data)
            candidate['routes']['001']['url'] = url
            with self.assertRaises(ValueError): validate(candidate)

    def test_information_content_is_inert(self):
        info = json.loads((ROOT / 'hardware.json').read_text(encoding='utf-8'))
        info['001']['purpose'] = '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(self.data, out, info)
            content = (out / 'info/001/index.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;', content)
            self.assertNotIn('<script>', content)

    def test_every_hardware_id_has_information(self):
        info = json.loads((ROOT / 'hardware.json').read_text(encoding='utf-8'))
        self.assertEqual(set(info), {f'{i:03}' for i in range(1, 19)})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(self.data, out, info)
            for key in info:
                self.assertIn('Power and connection limits', (out / f'info/{key}/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__': unittest.main()
