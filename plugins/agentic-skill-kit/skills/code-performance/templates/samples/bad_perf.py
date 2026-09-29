# Deliberately BAD sample for perf_smells.py - do not copy.
import re
import time
import requests
import pandas as pd


def enrich(awbs, blocked_ids):
    report = ""
    for awb in awbs:
        resp = requests.get(f"https://rates.example.test/{awb['id']}")  # io-in-loop
        if awb["id"] in blocked_ids:                                     # linear-lookup-loop
            continue
        pattern = re.compile(r"^\d{3}-\d{8}$")                           # regex-in-loop
        report += awb["number"] + "\n"                                   # string-concat-loop
        print("done", awb["number"])                                     # log-in-loop
    return report


def validate(awb_no):
    return re.compile(r"^\d{3}-\d{8}$").match(awb_no)                   # regex-per-call


async def handler(request):
    time.sleep(1)                                                        # blocking-in-async
    data = requests.post("https://customs.example.test", json={})        # blocking-in-async
    return data


def totals(df: pd.DataFrame):
    total = 0
    for _, row in df.iterrows():                                         # pandas-iterrows
        total += row["weight"] * row["rate"]
    return total


def ids(cur):
    cur.execute("SELECT * FROM shipment")                                # select-star
    return [requests.get(u) for u in ["a", "b"]]                         # io-in-loop (comprehension)
