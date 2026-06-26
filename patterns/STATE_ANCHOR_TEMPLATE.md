# State Anchor Template

Copy this file to start your domain anchor. Replace all `<placeholder>` values.
Markers: `[UNKNOWN]` needs your input. `[PROVISIONAL]` extracted by AI, needs
your confirmation. `[CONFIRMED]` verified by you.

Target size: under 20KB. If you exceed 50KB, switch to a Precedent Ledger +
selective retrieval (see ARCHITECTURE.md "Scaling boundary").

---

```yaml
---
type: state_anchor
domain: <your-domain>          # e.g., "tax", "compliance", "operations"
version: 0.1.0
status: DRAFT
last_canonical_audit: PENDING
last_canonical_auditor: PENDING
generated_at: <date>
---
```

---

# ENTITIES

## <Primary Entity Name>
- **Legal name:** <name> [CONFIRMED]
- **Entity type:** <LLC / S-Corp / sole-prop / etc.> [CONFIRMED]
- **Owner(s):** <names and ownership percentages> [CONFIRMED]
- **State of formation:** <state> [CONFIRMED]
- **EIN / registration ID:** stored in `.env` as `<ENTITY>_EIN` [CONFIRMED]
  *(Keep sensitive IDs in .env, not in the anchor file)*
- **Fiscal year:** <Calendar year / other> [CONFIRMED]
- **Business model:** <one-line description> [CONFIRMED]
- **Key contact / advisor:** <name, role, firm> [CONFIRMED]
- **Notes:** [UNKNOWN]

## <Secondary Entity or Person>
- **Relationship to primary:** <description> [CONFIRMED]
- **Key facts:** [UNKNOWN]

*(Add as many entity sections as your domain requires)*

---

# OPERATIONAL POSTURE

Current state of ongoing obligations relevant to this domain.

- **<Obligation type>:** <current status, cadence, last action> [CONFIRMED]
- **<Obligation type>:** <current status> [PROVISIONAL]
- **<Obligation type>:** [UNKNOWN]

*(Examples: filing deadlines, licenses, recurring reviews, active contracts)*

---

# OPEN POSITIONS

Explicitly unresolved questions. Numbered for reference.

1. <date added> · <description of the open question> · **Blocked on:** <what's needed>
2. <date added> · <description> · **Target resolution:** <date or trigger>

*(Move items here when they can't be settled yet. Remove when resolved — add
the ruling to CANONICAL RULINGS instead.)*

---

# CANONICAL RULINGS

Settled decisions. Format: `R-NNN · date · entity-scope · ruling · source`.

```
R-001 · <date> · <entity> · <scope-tags> · <ruling in one clear sentence>
        Source: <link or reference to the session/document where this was decided>
        Supersedes: none

R-002 · <date> · <entity> · <scope-tags> · <ruling>
        Source: <reference>
        Supersedes: R-001
```

**Marker conventions:**
- No marker = canonical, in force
- `[PROVISIONAL]` = staged, awaiting human approval
- `[SUPERSEDED by R-NNN]` = replaced; kept for audit trail
- `[REVOKED]` = should never have been recorded; kept for audit trail

---

# REVOKED / SUPERSEDED

Rulings that are no longer in force. Kept here for the audit trail.

```
R-001 · <date originally added> · <original ruling text>
        SUPERSEDED by R-002 on <date> · Reason: <one sentence>

R-003 · <date originally added> · <original ruling text>
        REVOKED on <date> · Reason: <why it was never valid>
```

---

## Audit instructions

When you first fill in this template:

1. Work through every `[UNKNOWN]` — fill in what you know, leave a note for
   what you need to find out.
2. Confirm every `[PROVISIONAL]` — these were AI-extracted and may be wrong.
3. Once all markers are cleared, bump version to `1.0` and fill in
   `last_canonical_audit` and `last_canonical_auditor`.
4. From 1.0 forward, all changes go through the `[PROVISIONAL]` gate defined
   in `patterns/PROVISIONAL_GATE.md`.
