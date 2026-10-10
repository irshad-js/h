# Permanent hardware links

Public hardware information and permanent QR redirects. No private CAD, source hashes, placement coordinates, credentials, customer data, or fabrication packages belong here.

- Preserve published route IDs and the `irshad-js/h` repository name. Never reuse an ID for different hardware.
- Do not set a custom domain on this site or the account Pages site without reviewing printed QR compatibility.
- `registry.json` is the destination source of truth. Only HTTPS destinations on explicitly approved hosts are accepted.
- Public information comes from reviewed text in `hardware.json`. Escape strings and retain information pages after a destination changes.
- Generated site lives in `docs/`; regenerate with `python generate.py`, test with `python -m unittest discover -s tests -v`.
- Browser tests use Edge on Windows or Playwright Chromium elsewhere. Live verification: `python verify_live.py test-results/live` after deployment. QR probe: `python qr_probe.py test-results`.
- Install test dependencies with `python -m pip install -r requirements.txt`.
- Run `python generate.py --check --against <previous-registry.json>` before publishing; removed/reassigned IDs and generated drift fail. CI checks against the previous push/PR base.
- Private `HW/common_blocks` owns placement and physical qualification; publishing an information page never establishes fabrication approval.
- Author and committer for this work: `irshad ahamed <irshad9in@gmail.com>`.
