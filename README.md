# Permanent Vinyaan hardware links

Public hardware information and permanent QR entry points owned by irshad-js.

Hardware index: https://irshad-js.github.io/h/

Printed QR codes encode `https://irshad-js.github.io/h/<ID>/`. Each immutable ID identifies a hardware revision; `registry.json` selects its current HTTPS destination. The first 18 destinations are reviewed information pages under `/h/info/<ID>/`, generated from `hardware.json`. Update destinations when product pages move; retain IDs and information pages indefinitely.

| IDs | Hardware |
|---|---|
| 001–003 | Vinyan, Arivaan, Vaghan |
| 004–007 | BH1750, BMP280, DHT11, 10 mm LED |
| 008–011 | OLED, potentiometer, push button, soil moisture |
| 012–014 | USB-C PD supply, ultrasonic carrier, WS2812B RGB |
| 015–018 | 16×8 0402, 16×8 0805, 8×8 0402, 8×8 0805 matrices |

The original `test` route remains available.

## Redirect behavior

GitHub Pages publishes `main:/docs`. Entry pages forward using `location.replace`, with a keyboard-accessible fallback link when scripts are disabled. Parameters and fragments cannot choose a destination. Unknown IDs receive a helpful 404. Information strings render as escaped text; no analytics, remote images or third-party scripts run.

Only HTTPS destinations on approved hosts are accepted. Numeric IDs require retained information pages. CI rejects removed/reassigned published identities and generated-file drift. No runtime database or forwarding service is required.

## Stability and destination changes

- Preserve GitHub account `irshad-js`, repository `h` and published route paths.
- Keep custom domains unset on this project and the account Pages site: account domains can affect project sites.
- Change only `url` when a destination moves. Hardware `name` and `revision` remain the identity of the printed code; future revisions get new IDs.
- Generate, test, deploy, then verify the printed URL. Pages is static hosting, not an HTTP 302/307 service. Observed cache header: `max-age=600`; keep previous destinations reachable during transitions and allow caches to expire.
- Retain GitHub information pages after external destinations change.

## Development and verification

Python 3.11+:

```sh
python -m pip install -r requirements.txt
python generate.py
python generate.py --check --against previous-registry.json
python -m unittest discover -s tests -v
python verify_live.py test-results/live
```

Windows tests use installed Edge. Elsewhere install Chromium with `python -m playwright install --with-deps chromium`. Run live checks after Pages deployment succeeds. Every permanent/test route is checked, including parameter handling, information destinations, mobile keyboard fallback and custom 404.

`qr_probe.py` generates digital test assets. `kicad_probe.py` uses KiCad's Python to generate a disposable coupon. Production footprints and PCB updates belong to private `HW/common_blocks`: Q error correction, 0.35 mm modules, four-module quiet zone. Three-digit URLs produce a 14.35 mm square before labels and extra clearances.

## Physical qualification

Sizes are qualification candidates. Fabrication requires board-specific clearances, assembled visibility, manufacturer capability and five consecutive correct scans on both Android and iPhone for each fabricated board. Software decoding and deployment cannot establish fabrication approval. Existing electrical and hardware release blockers remain applicable.

Copyright 2026 irshad ahamed. All rights reserved. See LICENSE, NOTICE and SECURITY.md.
