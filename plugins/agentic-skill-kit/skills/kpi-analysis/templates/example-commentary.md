# Example (FAKE DATA): KPI Commentary, Import Terminal, 2026-W38 (vs W37)

Source: `templates/sample-kpi.csv`, run with `--lower-better avg_dwell_hours`.

**Headline:** 1 of 3 targeted KPIs on target; dwell time and on-time delivery both deteriorated sharply while volume jumped 24.9%.

## Flags & top movers
| Metric | Status | Change | vs Target | Likely driver | Next step |
|---|---|---|---|---|---|
| avg_dwell_hours | 🔴 Anomaly | +27.0% (worse) | −23.3% | TBD | Check customs holds and backlog for W38 |
| on_time_delivery_pct | 🔴 Anomaly | −3.9% (worse) | −4.0% | TBD | Check link to dwell spike |
| awb_volume | 🔵 Positive anomaly | +24.9% | n/a | TBD | Verify no duplicate AWBs in export |
| fwb_success_pct | 🟢 On target | +0.1% | +0.2% | | None |

## Narrative
W38 volume rose 24.9% to 15,990 AWBs. Dwell time spiked to 29.6 h (target 24 h, +27.0% WoW) and on-time delivery fell to 91.2% (target 95%). The two are likely linked but the driver is not in the data. FWB success held at 99.7%. Ask: confirm whether the volume jump is real and review import staffing for W39.
