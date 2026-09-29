# Email Templates

Placeholders in [brackets]. Unknown value → "TBD" in the draft + Needs input.

## 1. Shipment status
**Subject:** Shipment update: AWB [no.] [origin]-[dest] – [status]
Dear [name],
Please find the latest status of your shipment:
- AWB: [no.] · Pieces/weight: [x pcs / y kg]
- Flight: [flight/date] · Status: [status] at [station], [time zone]
- Next milestone: [milestone, time or TBD]
Regards, [sender]

## 2. Delay / exception
**Subject:** Delay notice: AWB [no.] / [flight] – next update [time]
Dear [name],
AWB [no.] ([pcs/kg]) planned on [flight/date] has been [offloaded / held / short-shipped] at [station]. We apologise for the inconvenience.
- Reason (as known): [fact]
- Revised plan: [new flight/ETA or "being confirmed"]
- Next update: [time, zone]
[Ask, if any.]
Regards, [sender]

## 3. Incident notice
**Subject:** [Service] incident – [impact] – next update [time]
Dear [name],
Since [start time, zone] [service] is [impact in customer terms]. We apologise for the disruption.
- Affected: [stations / message types / users]
- Workaround: [if any, else None]
- Status: [investigating / fix in progress / monitoring]
- Next update: [time, zone]
Regards, [sender]

## 4. Go-live announcement
**Subject:** Go-live: [module/partner] live at [station] from [date]
Dear [name],
We are pleased to confirm that [module/partner] is live at [station] from [date, time, zone].
- What changes: [1–3 bullets]
- Action for you: [if any, else None]
- Support contact: [contact]
Regards, [sender]

## 5. Maintenance window
**Subject:** Planned maintenance: [system] [date] [start–end, zone]
Dear [name],
[System] will be unavailable on [date] from [start] to [end] [zone] for [purpose, customer terms].
- Impact: [what users cannot do]
- Before the window: [action or None]
- We will confirm completion by [time or TBD].
Regards, [sender]

## 6. Request follow-up
**Subject:** Reminder: [item] needed by [date]
Dear [name],
Following up on [item] requested on [date]. We need it by [date] to [reason / milestone].
[Specific list of what is missing.]
Regards, [sender]

---

## Example (fake data)
**Input:** "AWB 999-12345675, 12 pcs 480 kg, BOM-FRA on XY 102 11 Mar offloaded at BOM, space issue. Rebooked XY 104 13 Mar, not confirmed yet. Tell Meera at FastTrack Forwarding, next update 18:00 IST."

**Output:**
**Subject:** Delay notice: AWB 999-12345675 / XY 102 – next update 18:00 IST
Dear Meera,
AWB 999-12345675 (12 pcs / 480 kg) planned on XY 102, 11 Mar, BOM-FRA, has been offloaded at BOM due to space constraints. We apologise for the inconvenience.
- Revised plan: rebooking on XY 104, 13 Mar, being confirmed
- Next update: 18:00 IST
Regards, [sender]

*Needs input: sender name; confirmation of XY 104 before promising it.*
