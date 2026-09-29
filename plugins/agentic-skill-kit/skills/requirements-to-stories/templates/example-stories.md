# Example (FAKE DATA)

**Input (client email):** "Forwarders should get the delivery order online once storage and handling are paid. No DO if anything is pending. Also send them an email. Needs to work for Mumbai and Delhi terminals by Q1."

## Epics
| Epic ID | Epic | Goal | Stories | REQ refs |
|---|---|---|---|---|
| EP-01 | e-DO issuance | Forwarders collect import cargo without counter visit | ST-01, ST-02, ST-03 | REQ-01..03 |

## Stories: EP-01 e-DO issuance
| ID | Title | User story | Points (hint) | Priority | Depends on |
|---|---|---|---|---|---|
| ST-01 | Issue e-DO after payment | As a forwarder, I want the e-DO issued online once charges are paid, so that I can collect cargo without visiting the counter. | 5: payment status integration | Must | Payment status API |
| ST-02 | Block e-DO with pending charges | As a GHA import agent, I want e-DO blocked while charges are pending, so that revenue is not lost. | 3: validation on known data | Must | ST-01 |
| ST-03 | Email e-DO to forwarder | As a forwarder, I want the e-DO emailed to me, so that I have it without logging in. | 2: existing mail service | Should | ST-01 |

### ST-02 Acceptance criteria
```gherkin
Scenario: Pending storage charge blocks e-DO
  Given AWB 000-00000000 has status "RCF" and storage charges "Pending"
  When the agent requests an e-DO
  Then the request is refused with reason "Charges pending"
  And no e-DO number is generated
```

## Open questions
| # | Question | Blocks | Ask |
|---|---|---|---|
| Q1 | Is partial payment ever allowed (credit customers)? | ST-02 | Client |
| Q2 | "Q1": which date, and are both terminals in the same release? | EP-01 | Client |
| Q3 | Email format: PDF attachment or link? | ST-03 | Client |
