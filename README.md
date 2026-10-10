# Hardware links — feasibility prototype

Stable public entry points for printed hardware QR codes, owned by irshad-js.

**Prototype only. No PCB sources changed; no production IDs assigned.**

Test URL: https://irshad-js.github.io/h/test/

`registry.json` maps immutable IDs to current HTTPS destinations. Run `python generate.py` to generate the site under `docs/`. GitHub Pages publishes `main:/docs`. Each page forwards with `location.replace`, with a visible accessible link if scripts are disabled. Query strings cannot select destinations. Unknown IDs return a helpful 404. No analytics or third-party scripts.

## Stability constraints

- Preserve GitHub account, repository name `h`, and published paths indefinitely.
- Do not configure a custom domain on this project **or the account Pages site**: account-level domains can affect project Pages URLs.
- Change registry destinations when product pages move; retain old hardware IDs permanently.
- GitHub Pages is static hosting, not an HTTP 302/307 service. Its CDN can cache old HTML temporarily; destination changes are not guaranteed instantaneous. Never fabricate a QR until its route is deployed and verified.
- A phone still needs internet access. Physical silk, solder-mask contrast, camera focus, assembly obstructions and enclosure visibility require fabricated-sample testing.
- Production approval needs model/revision mapping, destination pages, fab silk capability and real camera checks. No unit tracking is proposed.

## Reproduce

Python 3.11+:

```sh
python -m pip install -r requirements.txt
python generate.py
python -m unittest discover -s tests -v
python qr_probe.py test-results
python verify_live.py https://github.com/irshad-js/h/blob/main/README.md test-results/live
```

Browser tests use installed Microsoft Edge (`channel='msedge'`) in headless mode. The live test requires successful Pages deployment first. `kicad_probe.py` runs with KiCad 10's bundled Python and takes the generated `matrix.json` plus an output PCB path. It generates an isolated 20 mm coupon, never modifies existing boards.

QR test sizes use 0.35 mm modules **as an experiment**, including a four-module quiet zone on every side. The short test/model URL at Q error correction produces a 14.35 mm square; the longer `hardware-links` URL produces 15.75 mm. Dimensions exclude human-readable labels and extra component/edge clearances. These are not yet approved fabrication dimensions.

Automated QR decoding proves the encoded payload survives the tested digital transformations; it does not qualify a PCB manufacturer or camera.

Copyright 2026 irshad ahamed. All rights reserved.
