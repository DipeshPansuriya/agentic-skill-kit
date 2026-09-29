# Severity Scale (SEV1–SEV4)

Pick the **highest** row where any criterion matches. Quote the criterion in the report.

| Sev | Criteria (any one) | Logistics examples | Target TTD | Target TTR | RCA due |
|---|---|---|---|---|---|
| **SEV1** Critical | Full outage of a production system; data loss/corruption; security breach; regulatory filing blocked; multiple customers down | Cargo community system down at an airport; customs e-manifest (e.g. ICEGATE/ACAS) submissions failing; AWB data leak | ≤ 5 min | ≤ 1 h (mitigate) | 2 working days |
| **SEV2** High | Major function down or badly degraded for one or more customers; SLA breach; shipments delayed | FWB/FFM messages not reaching an airline; ULD tracking stale > 1 h; e-DO/gate-pass generation failing at one terminal | ≤ 15 min | ≤ 4 h | 5 working days |
| **SEV3** Medium | Partial degradation with workaround; single customer/user group; no SLA breach | Slow AWB search; one report failing; manual FSU workaround in place | ≤ 1 h | ≤ 1 working day | 10 working days (light RCA) |
| **SEV4** Low | Cosmetic or minor; no business impact | Wrong label on a screen; non-critical batch job retried OK | Next business day | Next release | Not required (ticket note) |

## Escalation modifiers
- Upgrade one level if: customer/regulator reported it before we detected it, or duration > 2x target TTR.
- Never downgrade after the fact because impact "turned out small"; record the severity at peak impact.

## Duration terms
| Term | From | To |
|---|---|---|
| TTD (time to detect) | Impact start | Detected / alerted |
| TTR (time to resolve) | Impact start | Service restored |
| Detect to resolve | Detected | Service restored |
