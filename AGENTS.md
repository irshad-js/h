# Hardware links prototype

Public redirect and QR feasibility prototype. No private CAD, credentials, customer data, or fabrication packages belong here.

- Preserve published route IDs and the `irshad-js/h` repository name. Never reuse an ID for different hardware.
- Do not set a custom domain on this site or the account Pages site without reviewing printed QR compatibility.
- `registry.json` is the destination source of truth. Only HTTPS destinations on explicitly approved hosts are accepted.
- Generated site lives in `docs/`; regenerate with `python generate.py`, test with `python -m unittest discover -s tests -v`.
- Browser tests require Microsoft Edge installed. Live verification: `python verify_live.py https://github.com/irshad-js/h/blob/main/README.md test-results/live` after deployment. QR probe: `python qr_probe.py test-results`.
- Install test dependencies with `python -m pip install -r requirements.txt`.
- This phase contains only a test route. Production hardware IDs and CAD placement require a separate implementation plan.
- Author and committer for this work: `irshad ahamed <irshad9in@gmail.com>`.
