# Mermaid Diagram Guidance

Use plain `flowchart` for C4-style diagrams (renders everywhere). Mermaid's experimental `C4Context` syntax is fine only if the user's renderer supports it.

## Conventions
| Element | Style |
|---|---|
| Person / external party | `(["Name<br/>role"])` |
| Our system / container | `["Name<br/>[Tech]<br/>purpose"]` |
| Database | `[("Name<br/>[SQL Server]")]` |
| Queue / topic | `[/"Name<br/>[Service Bus]"/]` |
| Boundary | `subgraph` with a title |
| Arrow | Label with intent + protocol: `-->|"Sends FWB (Cargo-XML/HTTPS)"|` |
Keep ≤ 12 boxes per diagram; split otherwise.

## C4 L1 context example
```mermaid
flowchart LR
  fwd(["Forwarder<br/>books shipments"]) -->|"Bookings, FWB (HTTPS/XML)"| ccs["Cargo Community System"]
  ccs -->|"FFR/FWB (Cargo-IMP via SITA/Type-B)"| airline["Airline host system"]
  ccs -->|"Manifest (customs XML)"| customs["Customs authority"]
  gha(["Ground handler"]) -->|"Acceptance, FSU (API)"| ccs
```

## C4 L2 container example
```mermaid
flowchart LR
  subgraph ccs["Cargo Community System"]
    web["Web app<br/>[Angular]"] --> api["Booking API<br/>[.NET 8]"]
    api --> db[("Bookings DB<br/>[SQL Server]")]
    api --> outbox[/"Outbox relay"/]
    outbox --> bus[/"Event bus<br/>[Service Bus / Kafka]"/]
    bus --> tx["Message translator<br/>[Java]"]
  end
  tx -->|"Cargo-IMP / Cargo-XML"| airline["Airline host"]
```

## Sequence for a key flow
```mermaid
sequenceDiagram
  participant F as Forwarder
  participant API as Booking API
  participant DB as DB (+outbox)
  participant BUS as Event bus
  participant TX as Translator
  F->>API: POST /bookings (Idempotency-Key)
  API->>DB: insert booking + outbox row (one tx)
  API-->>F: 202 Accepted (bookingId)
  DB-->>BUS: relay publishes BookingCreated
  BUS->>TX: BookingCreated
  TX->>TX: map to FFR, dedupe by messageId
```

## Checklist
- Every box: name + technology; every arrow: what + protocol
- Sync vs async visually distinct (label "async" or use queue nodes)
- Trust boundaries shown with `subgraph`
- Diagram matches the text (same names)
