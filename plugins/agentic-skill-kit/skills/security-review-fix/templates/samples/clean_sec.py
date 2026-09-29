# Clean sample for sec_scan.py: expected 0 findings.
import json
import os
import secrets

import httpx
import yaml
from argon2 import PasswordHasher

DB_PASSWORD = os.environ["DB_PASSWORD"]
CA_BUNDLE = "/etc/ssl/certs/customs-ca.pem"
ph = PasswordHasher()


def find_awb(cur, awb_no):
    cur.execute("SELECT id, status FROM awb WHERE awb_no = %s", (awb_no,))


def load(text):
    return json.loads(text), yaml.safe_load(text)


def call_customs():
    return httpx.get("https://customs.example.test", verify=CA_BUNDLE, timeout=5)


def hash_pw(pw):
    return ph.hash(pw)


def session_token():
    return secrets.token_urlsafe(32)


def audit(user_id):
    print(f"login user_id={user_id}")
