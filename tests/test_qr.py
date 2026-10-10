import unittest
import json
from PIL import Image, ImageFilter, ImageOps
import qrcode
import zxingcpp
from generate import BASE, ROOT


class QRTests(unittest.TestCase):
    def test_production_payloads_and_transformations(self):
        data = json.loads((ROOT / 'registry.json').read_text(encoding='utf-8'))
        for key in data['routes']:
            if not key.isdecimal(): continue
            url = f'{BASE}/{key}/'
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=8, border=4)
            qr.add_data(url); qr.make(fit=True)
            self.assertEqual(qr.version, 4)
            self.assertEqual(len(qr.get_matrix()), 41)
            source = qr.make_image().convert('RGB')
            cases = [source, source.rotate(90), source.rotate(180), source.rotate(270),
                     ImageOps.invert(source), ImageOps.mirror(source),
                     source.filter(ImageFilter.GaussianBlur(.8)),
                     source.resize((164, 164), Image.Resampling.LANCZOS)]
            for index, img in enumerate(cases):
                with self.subTest(id=key, case=index):
                    result = zxingcpp.read_barcode(img)
                    self.assertIsNotNone(result)
                    self.assertEqual(result.text, url)
