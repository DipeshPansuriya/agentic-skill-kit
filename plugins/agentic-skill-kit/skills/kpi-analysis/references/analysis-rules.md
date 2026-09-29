# Analysis Rules

## Status per metric (latest week)
| Status | Rule (from `kpi_summary.py` flags) |
|---|---|
| 🔴 Anomaly | ANOMALY-Z or ANOMALY-WOW, and movement is in the worse direction |
| 🟠 Missed target | MISSED-TARGET only |
| 🔵 Positive anomaly | Anomaly in the better direction: still verify data (spike may be a data error) |
| 🟢 On target | No flags, at/above target |
| ⚪ Insufficient history | INSUFFICIENT-HISTORY (< 3 trailing weeks): report value only |

## Formulas (for explanation; the script computes them)
| Measure | Formula |
|---|---|
| WoW % | (this − last) / abs(last) × 100 |
| vs Target % | (value − target) / abs(target) × 100, sign flipped for lower-is-better, so + = better |
| z-score | (value − mean(trailing N)) / stdev(trailing N), current week excluded |

## Common logistics KPIs and direction
| Metric | Better | Typical note |
|---|---|---|
| On-time delivery / OTP % | Higher | Check flight delays, weather, peak |
| Dwell time (hrs) | Lower | Check customs holds, backlog, staffing |
| FWB/FSU message success % | Higher | Check partner endpoint, cert, mapping |
| AWB / shipment volume | Context | A spike is not "good" by itself; check data duplication |
| Build-up / breakdown TAT | Lower | Check shift roster, ULD availability |
| Customs clearance time | Lower | Check regulator system status |
| Billing accuracy % | Higher | Check tariff master changes |

## Reshaping wide exports
- One column per metric: melt to week, metric, value.
- One column per week: melt to metric, week, value.
- Targets in a separate sheet: join on metric (and week if weekly targets).
- Week labels: use ISO YYYY-Www or YYYY-MM-DD so text sort = time order.

## Narrative pattern
1. Headline: overall state in one line ("3 of 4 KPIs on target; dwell time spiked").
2. Worst issue with number, target, and change.
3. Notable positive.
4. Ask / next action with owner (TBD if unknown).
