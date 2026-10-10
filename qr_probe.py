"""Generate digital QR test artifacts, not production fabrication artwork."""
import argparse
import json
from pathlib import Path
import qrcode
from PIL import Image, ImageFilter, ImageOps
import zxingcpp


def probe(out):
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for label, url in {
        'short-test': 'https://irshad-js.github.io/h/test/',
        'short-model': 'https://irshad-js.github.io/h/a01r1/',
        'long-model': 'https://irshad-js.github.io/hardware-links/a01r1/',
    }.items():
        for level in ['M', 'Q', 'H']:
            qr = qrcode.QRCode(error_correction=getattr(qrcode.constants, 'ERROR_CORRECT_' + level), box_size=12, border=4)
            qr.add_data(url); qr.make(fit=True)
            original = qr.make_image().convert('RGB')
            cases = {'normal': original, 'inverse': ImageOps.invert(original),
                     'mirror': ImageOps.mirror(original), 'rotate': original.rotate(90),
                     'blur': original.filter(ImageFilter.GaussianBlur(1)),
                     'small': original.resize((len(qr.get_matrix()) * 4,) * 2, Image.Resampling.LANCZOS)}
            for name, img in cases.items():
                result = zxingcpp.read_barcode(img)
                if result is None or result.text != url:
                    raise AssertionError(f'Decode failed: {label}/{level}/{name}')
            row = {'label': label, 'url': url, 'ecc': level, 'version': qr.version,
                   'modules_without_border': qr.modules_count, 'quiet_zone_modules': 4,
                   'overall_mm_at_035_module': round(len(qr.get_matrix()) * .35, 2),
                   'decoded_cases': list(cases)}
            results.append(row)
            if label == 'short-test' and level == 'Q':
                original.save(out / 'test-qr.png')
                (out / 'matrix.json').write_text(json.dumps(qr.get_matrix()), encoding='utf-8')
    (out / 'qr-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    probe(parser.parse_args().output)
