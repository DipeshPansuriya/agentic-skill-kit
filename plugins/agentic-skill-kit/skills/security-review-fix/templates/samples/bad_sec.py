# Deliberately VULNERABLE sample for sec_scan.py - fake secrets, do not copy.
import hashlib
import pickle
import random

import requests
import yaml

DB_PASSWORD = "Wh@tever123"                                                # hardcoded-password
SERVICE_TOKEN = "__FAKE_JWT__"  # jwt-token
PRIVATE_KEY = """__FAKE_KEY_BEGIN__
MIIEFAKEFAKEFAKEFAKE
__FAKE_KEY_END__"""


def find_awb(cur, awb_no):
    cur.execute(f"SELECT id, status FROM awb WHERE awb_no = '{awb_no}'")     # sql-injection
    cur.execute("UPDATE awb SET status = '%s' WHERE id = 1" % awb_no)          # sql-injection


def load(blob, text):
    obj = pickle.loads(blob)                                                   # insecure-deserialize
    cfg = yaml.load(text, Loader=yaml.Loader)                                  # yaml-unsafe-load
    return eval(text)                                                          # code-eval


def call_customs():
    return requests.get("https://customs.example.test", verify=False)          # tls-verify-off


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()                          # weak-password-hash


def session_token():
    return "".join(random.choices("abcdef0123456789", k=32))  # session token  insecure-random


def audit(user, password):
    print(f"login {user} password={password}")                                 # sensitive-logging


app.run(host="0.0.0.0", debug=True)                                            # debug-enabled
