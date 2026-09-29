#!/usr/bin/env python3
"""Render the deliberately-vulnerable samples into a temp folder for scanner tests.

The committed samples hold placeholders instead of secret-shaped strings, so the repo
never contains anything that looks like a real credential (and GitHub push protection
stays quiet). This script rebuilds the fake values at runtime.

Usage: python render_samples.py OUT_DIR   -> writes all samples (rendered) into OUT_DIR
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAKE = {  # assembled from parts so no secret-shaped literal exists in the repo
    "__FAKE_AWS_KEY_1__": "AK" + "IA" + "Q3EGRLZ7X9T4WB2M",
    "__FAKE_AWS_KEY_2__": "AK" + "IA" + "Z7Q4M2N8P5R3T6W9",
    "__FAKE_JWT__": "ey" + "JhbGciOiJIUzI1NiJ9" + ".ey" + "JzdWIiOiJmYWtlLXVzZXIifQ" + ".c2lnbmF0dXJlLWZha2UtMTIz",
    "__FAKE_KEY_BEGIN__": "-----BEGIN RSA " + "PRIVATE KEY-----",
    "__FAKE_KEY_END__": "-----END RSA " + "PRIVATE KEY-----",
}

if len(sys.argv) != 2:
    sys.exit(__doc__)
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for f in HERE.iterdir():
    if f.is_file() and f.name != Path(__file__).name:
        text = f.read_text(encoding="utf-8")
        for k, v in FAKE.items():
            text = text.replace(k, v)
        (out / f.name).write_text(text, encoding="utf-8")
print(f"Rendered samples into {out}")
