# Tone & Subject Rules

## Subject line patterns
| Scenario | Pattern |
|---|---|
| Shipment status | `Shipment update: AWB [no.] [origin]-[dest] – [status]` |
| Delay / exception | `Delay notice: AWB [no.] / [flight] – next update [time]` |
| Incident notice | `[Service] incident – [impact in 3-5 words] – next update [time]` |
| Go-live | `Go-live: [module/partner] live at [station] from [date]` |
| Maintenance | `Planned maintenance: [system] [date] [start–end, zone]` |
| Request follow-up | `Reminder: [item] needed by [date]` |
| Update to earlier mail | `Update 2: [original subject]` |
| Resolved | `Resolved: [original subject]` |

Rules: ≤ 80 chars where possible; key ID first; no "URGENT" unless the user asks; no emojis.

## Tone
| Do | Don't |
|---|---|
| "We apologise for the inconvenience this causes." (once) | "Sorry again…", "Deeply regret…" repeated |
| "The flight was offloaded due to capacity." | "The airline messed up." / "The GHA failed to…" |
| "Our team is investigating; next update by 16:00 IST." | "We will fix it soon." / "Should be resolved today." (unless given) |
| "Please share the FHL by 14 Mar." | "Kindly do the needful ASAP." |
| State impact in customer terms (shipments, bookings, messages) | Internal terms (pod restart, queue lag, Jira ID) |

## Recipient adjustments
| Recipient | Adjust |
|---|---|
| Client ops | Operational detail, IDs, times |
| Client management | Impact + action + next update; fewer IDs |
| Partner (GHA / airline / forwarder) | Neutral, fact-based; specific ask |

## Words to avoid unless given
guarantee, definitely, permanent fix, root cause (before RCA is confirmed), compensation, SLA credit.
