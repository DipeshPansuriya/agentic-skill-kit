#!/usr/bin/env python3
"""Print ISO week number and Mon–Fri / Mon–Sun range for a date.

Usage: python week_info.py [YYYY-MM-DD]   (defaults to today)
"""
import sys
from datetime import date, timedelta

d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
year, week, _ = d.isocalendar()
monday = d - timedelta(days=d.weekday())
friday, sunday = monday + timedelta(days=4), monday + timedelta(days=6)
prev_monday = monday - timedelta(days=7)

print(f"ISO week:      W{week:02d} {year}")
print(f"Work week:     {monday:%a %d %b} – {friday:%a %d %b %Y}")
print(f"Full week:     {monday:%d %b} – {sunday:%d %b %Y}")
print(f"Previous week: W{prev_monday.isocalendar()[1]:02d} ({prev_monday:%d %b} – {prev_monday + timedelta(days=4):%d %b})")
print(f"Title:         W{week:02d} ({monday:%b %d} – {friday:%b %d} {friday.year})")
