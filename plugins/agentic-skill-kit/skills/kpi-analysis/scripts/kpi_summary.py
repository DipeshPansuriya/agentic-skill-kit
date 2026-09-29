#!/usr/bin/env python3
"""Weekly KPI summary: WoW change, vs target, anomaly flags, top movers (markdown).

Input: CSV (or .xlsx if openpyxl is installed) with columns
    week, metric, value [, target]
`week` must sort chronologically as text (e.g. 2026-W38 or 2026-09-14) or be a date.
Requires pandas.

Per metric, for the latest week (or every week with --all):
    WoW %      = (value - previous) / |previous| * 100
    vs target  = (value - target) / |target| * 100   (sign flipped for --lower-better metrics,
                 so positive always means better than target)
    z          = (value - mean of trailing N weeks) / std of trailing N weeks (current week excluded)
    Flags      = ANOMALY-Z if |z| > --z (default 2), ANOMALY-WOW if |WoW| > --wow (default 20),
                 MISSED-TARGET if worse than target, INSUFFICIENT-HISTORY if < 3 trailing weeks

Usage:
    python kpi_summary.py kpis.csv
    python kpi_summary.py kpis.csv --lower-better avg_dwell_hours,cost_per_kg --window 4
    python kpi_summary.py kpis.xlsx --all --wow 15 --z 2.5
"""
import argparse
import sys

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is required: pip install pandas")


def load(path):
    df = pd.read_excel(path) if path.lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"week", "metric", "value"} - set(df.columns)
    if missing:
        sys.exit(f"Missing column(s): {', '.join(sorted(missing))}. Need week,metric,value[,target].")
    if "target" not in df.columns:
        df["target"] = float("nan")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["target"] = pd.to_numeric(df["target"], errors="coerce")
    bad = df["value"].isna().sum()
    df = df.dropna(subset=["value"])
    dups = df.duplicated(subset=["metric", "week"]).sum()
    df = df.drop_duplicates(subset=["metric", "week"], keep="last")
    df["week"] = df["week"].astype(str)
    return df.sort_values(["metric", "week"]), int(bad), int(dups)


def analyse(df, window, z_lim, wow_lim, lower_better):
    rows = []
    for metric, g in df.groupby("metric", sort=True):
        g = g.reset_index(drop=True)
        sign = -1 if metric in lower_better else 1
        for i, r in g.iterrows():
            prev = g["value"].iloc[i - 1] if i > 0 else float("nan")
            wow = (r.value - prev) / abs(prev) * 100 if i > 0 and prev != 0 else float("nan")
            vs_t = sign * (r.value - r.target) / abs(r.target) * 100 if pd.notna(r.target) and r.target != 0 else float("nan")
            hist = g["value"].iloc[max(0, i - window):i]
            z = float("nan")
            if len(hist) >= 3 and hist.std(ddof=1) > 0:
                z = (r.value - hist.mean()) / hist.std(ddof=1)
            flags = []
            if pd.notna(z) and abs(z) > z_lim:
                flags.append("ANOMALY-Z")
            if pd.notna(wow) and abs(wow) > wow_lim:
                flags.append("ANOMALY-WOW")
            if pd.notna(vs_t) and vs_t < 0:
                flags.append("MISSED-TARGET")
            if len(hist) < 3:
                flags.append("INSUFFICIENT-HISTORY")
            rows.append(dict(metric=metric, week=r.week, value=r.value, prev=prev, wow=wow,
                             target=r.target, vs_t=vs_t, z=z, flags=flags,
                             direction="lower" if sign < 0 else "higher"))
    return pd.DataFrame(rows)


def f(x, fmt="{:,.2f}", suffix=""):
    return "n/a" if pd.isna(x) else fmt.format(x) + suffix


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--lower-better", default="", help="comma-separated metrics where lower is better")
    ap.add_argument("--window", type=int, default=4, help="trailing weeks for z-score (default 4)")
    ap.add_argument("--z", type=float, default=2.0, help="|z| anomaly threshold (default 2)")
    ap.add_argument("--wow", type=float, default=20.0, help="|WoW %%| anomaly threshold (default 20)")
    ap.add_argument("--all", action="store_true", help="print every week, not just the latest")
    ap.add_argument("--top", type=int, default=3, help="number of top movers (default 3)")
    a = ap.parse_args()

    lower = {m.strip() for m in a.lower_better.split(",") if m.strip()}
    df, bad, dups = load(a.file)
    if df.empty:
        sys.exit("No numeric rows found.")
    res = analyse(df, a.window, a.z, a.wow, lower)
    latest = res.groupby("metric").tail(1)
    show = res if a.all else latest

    print(f"**Latest week per metric** · window={a.window} · |z|>{a.z} · |WoW|>{a.wow}%\n")
    print("| Metric | Week | Value | Prev | WoW % | Target | vs Target % (+ = better) | z | Flags |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in show.itertuples():
        name = r.metric + (" (lower=better)" if r.direction == "lower" else "")
        print(f"| {name} | {r.week} | {f(r.value)} | {f(r.prev)} | {f(r.wow, '{:+.1f}')} | {f(r.target)} | "
              f"{f(r.vs_t, '{:+.1f}')} | {f(r.z, '{:+.2f}')} | {', '.join(r.flags) or 'OK'} |")

    has_wow = latest.dropna(subset=["wow"])
    movers = has_wow.loc[has_wow["wow"].abs().sort_values(ascending=False).index].head(a.top)
    print("\n**Top movers (latest week, by |WoW %|)**")
    if movers.empty:
        print("- None (no prior week to compare)")
    for r in movers.itertuples():
        better = (r.wow > 0) == (r.direction == "higher")
        print(f"- {r.metric}: {r.wow:+.1f}% ({'better' if better else 'worse'})")

    weeks = sorted(latest["week"].unique())
    notes = []
    if len(weeks) > 1:
        notes.append(f"metrics end on different weeks: {', '.join(weeks)}")
    if bad:
        notes.append(f"{bad} row(s) with non-numeric value dropped")
    if dups:
        notes.append(f"{dups} duplicate metric/week row(s); last one kept")
    for n in notes:
        print(f"\nNote: {n}.")


if __name__ == "__main__":
    main()
