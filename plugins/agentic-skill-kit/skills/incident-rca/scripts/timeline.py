#!/usr/bin/env python3
"""Build a sorted UTC + IST incident timeline and compute TTD / TTR.

Parses lines that START with a timestamp, e.g.
    2026-09-21 14:05 IST  Alert: FWB queue backlog > 500
    [2026-09-21 08:40:12 UTC] Ops detected failed EDI to airline
    2026-09-21T09:10:00Z  Fix deployed, queue resolved
    2026-09-21T14:05:00+05:30 Customer reports AWB status stale
Accepted zones: Z, UTC, GMT, IST, +HH:MM / +HHMM. No zone = --default-tz.
Lines without a timestamp are appended to the previous event (continuation).

Metrics (keywords are case-insensitive regexes, first match wins except resolve = last match):
    Start   = first event matching --start-kw, else the earliest event
    TTD     = Detected - Start
    TTR     = Resolved - Start;  Detect-to-resolve = Resolved - Detected

Usage:
    python timeline.py incident.txt
    cat chat.txt | python timeline.py - --default-tz UTC
    python timeline.py log.txt --detect-kw "detected|alert" --resolve-kw "resolved|restored"
"""
import argparse
import re
import sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")
UTC = timezone.utc
TS = re.compile(
    r"^\s*\[?(?P<date>\d{4}-\d{2}-\d{2})[T ](?P<time>\d{1,2}:\d{2}(?::\d{2})?)(?:\.\d+)?"
    r"\s*(?P<tz>Z|UTC|GMT|IST|[+-]\d{2}:?\d{2})?\]?\s*[-:|]?\s*(?P<text>.*)$",
    re.I,
)


def parse_tz(tz):
    if tz is None:
        return None
    t = tz.upper()
    if t in ("Z", "UTC", "GMT"):
        return UTC
    if t == "IST":
        return IST
    sign = 1 if t[0] == "+" else -1
    digits = t[1:].replace(":", "")
    return timezone(sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:])))


def parse(lines, default_tz):
    events, skipped = [], 0
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        m = TS.match(line)
        if not m:
            if events:
                events[-1]["text"] += " " + line.strip()
            else:
                skipped += 1
            continue
        fmt = "%Y-%m-%d %H:%M:%S" if m["time"].count(":") == 2 else "%Y-%m-%d %H:%M"
        naive = datetime.strptime(f"{m['date']} {m['time']}", fmt)
        tz = parse_tz(m["tz"]) or default_tz
        events.append({"dt": naive.replace(tzinfo=tz).astimezone(UTC),
                       "text": m["text"].strip(), "zone_given": bool(m["tz"])})
    events.sort(key=lambda e: e["dt"])  # stable: keeps input order for ties
    return events, skipped


def find(events, pattern, last=False):
    rx = re.compile(pattern, re.I)
    hits = [e for e in events if rx.search(e["text"])]
    return (hits[-1] if last else hits[0]) if hits else None


def fmt_delta(a, b):
    if not a or not b:
        return "TBD (marker not found)"
    secs = int((b["dt"] - a["dt"]).total_seconds())
    if secs < 0:
        return f"CHECK: negative ({secs // 60} min), markers out of order"
    h, rem = divmod(secs, 3600)
    return f"{h}h {rem // 60:02d}m ({secs // 60} min)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="input file, or - for stdin")
    ap.add_argument("--default-tz", default="IST", help="zone for timestamps without one (IST, UTC, +05:30). Default IST")
    ap.add_argument("--start-kw", default=r"impact start|started|began|first (error|alert|report)")
    ap.add_argument("--detect-kw", default=r"detected|alert(ed)?\b|paged|noticed")
    ap.add_argument("--resolve-kw", default=r"resolved|restored|recovered|mitigated")
    a = ap.parse_args()

    default_tz = parse_tz(a.default_tz)
    if default_tz is None:
        sys.exit("--default-tz must be IST, UTC, Z, GMT or +HH:MM")
    src = sys.stdin if a.file == "-" else open(a.file, encoding="utf-8")
    events, skipped = parse(src, default_tz)
    if not events:
        sys.exit("No timestamped lines found. Expected lines starting with YYYY-MM-DD HH:MM [zone].")

    start = find(events, a.start_kw) or events[0]
    detected = find(events, a.detect_kw)
    resolved = find(events, a.resolve_kw, last=True)
    marks = [(start, "START"), (detected, "DETECTED"), (resolved, "RESOLVED")]

    print("| # | UTC | IST | Event | Marker |")
    print("|---|---|---|---|---|")
    for i, e in enumerate(events, 1):
        u, s = e["dt"], e["dt"].astimezone(IST)
        flag = "" if e["zone_given"] else f" _(zone assumed {a.default_tz})_"
        text = e["text"].replace("|", "/") + flag
        mk = " / ".join(label for ev, label in marks if ev is e)
        print(f"| {i} | {u:%Y-%m-%d %H:%M} | {s:%Y-%m-%d %H:%M} | {text} | {mk} |")

    print("\n| Metric | Value |")
    print("|---|---|")
    print(f"| Start (UTC) | {start['dt']:%Y-%m-%d %H:%M} |")
    print(f"| Time to detect (TTD) | {fmt_delta(start, detected)} |")
    print(f"| Time to resolve (TTR, from start) | {fmt_delta(start, resolved)} |")
    print(f"| Detect to resolve | {fmt_delta(detected, resolved)} |")
    notes = []
    if skipped:
        notes.append(f"{skipped} line(s) before the first timestamp were ignored")
    naive = sum(not e["zone_given"] for e in events)
    if naive:
        notes.append(f"{naive} event(s) had no zone; assumed {a.default_tz}")
    for n in notes:
        print(f"\nNote: {n}.")


if __name__ == "__main__":
    main()
