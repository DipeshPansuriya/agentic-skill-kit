# Categories & Tone

## Category rules
| Category | Put here when | Commit types | Client wording pattern |
|---|---|---|---|
| **Breaking / Action required** | Reader must change something: API/EDI format, config, login, removed feature, data format | any with `!` or `BREAKING CHANGE` | "Action required by DATE: ... If not, ..." |
| **New** | New capability a user can see or call | feat | "You can now ..." |
| **Improved** | Existing capability faster, easier, clearer | perf, some feat/refactor with visible effect | "... is now faster / simpler ..." |
| **Fixed** | Defect corrected | fix, revert | "Fixed: ... no longer ..." |
| **Known issues** | Open defects shipped knowingly | (from ticket list) | "... Workaround: ..." |
| Internal only | No user-visible change | refactor, docs, chore, build, ci, test, style | Omit from client variant |

## Rewrite examples (fake data)
| Internal | Client |
|---|---|
| CCS-1412 edo: issue e-DO online after payment | You can now receive your delivery order online as soon as charges are paid. |
| CCS-1398 fwb: retry on TLS handshake failure | Fixed: air waybill data now reaches airlines reliably after brief network interruptions. |
| perf(search): index on awb_no | AWB search results now load up to 3x faster. |

## Tone
- Client: positive, plain, second person, no jargon (say "air waybill data", not "FWB", unless the audience is an airline/IT team).
- Internal: terse, factual, IDs first.
- Never say "minor bug fixes" alone; name the area.

## Internal-only sections
| Section | Content |
|---|---|
| Config changes | Key, old value, new value, environment |
| DB migrations | Script name, reversible Y/N, est. duration |
| Feature flags | Flag, default, who enables |
| Rollback | Steps or "Redeploy vX.Y.Z" + data caveats |
| Interface impact | API version, EDI message types, partners to notify |
