# RAG Status Rules

Apply per workstream, then derive overall.

| Status | Use when |
|---|---|
| 🟢 **Green** | On track for committed date; no open blocker; metrics at/above target |
| 🟠 **Amber** | At risk: date may slip ≤ 1 week, **or** a blocker exists with a plan, **or** a metric is within 10% below target |
| 🔴 **Red** | Committed date missed or will slip > 1 week, **or** a blocker has no owner/plan, **or** a metric is > 10% below target, **or** customer/SLA impact |
| ⚪ **Not started / TBD** | No data this week. Flag under *Needs input* |

## Overall status
- Any Red: overall **Red**
- Else any Amber: overall **Amber**
- Else **Green**

## Trend arrows (when last week is available)
- ▲ improved · ▼ worsened · ► unchanged
- Show as: `🟠 Amber ▲ (was Red)`

## Don't
- Don't mark Green to "look good" when the inputs show a blocker.
- Don't mark Red without stating impact and the next action.
