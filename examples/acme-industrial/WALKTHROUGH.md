# Walkthrough: One Full Turn with Acme Industrial Corp

This example traces a single user question through the complete Council of
Managers pattern: anchor injection → propose → critique → PROVISIONAL gate →
human approval → anchor update.

*All entities and figures are fictional. Nothing here is legal or tax advice.*

---

## Setup

- **Anchor:** `examples/acme-industrial/ANCHOR.md` (v0.5.0, CANONICAL)
- **Skills loaded:** `council_precedent_review.md`, `ledger_provisional_audit.md`
- **Proposer model:** any LLM (e.g., `claude-sonnet-4-6`)
- **Critic model:** any different LLM family (e.g., `gemini-2.5-flash`)
- **Surface:** `api` (markdown output)

---

## Step 1: User question

Jordan (the operator) asks via the compliance dashboard:

> "We just shipped a $12,000 order to a customer in Indiana last week.
> Does Acme Performance need to register for Indiana sales tax?"

---

## Step 2: Orchestrator — context assembly

The orchestrator calls the `council_precedent_review` skill with:

```python
skill_input = {
    "TURN_QUESTION": "We just shipped a $12,000 order to a customer in Indiana...",
    "ANCHOR_PATH": "examples/acme-industrial/ANCHOR.md",
    "HISTORY_TURNS": [],   # first question in this thread
    "SURFACE": "api"
}
```

The skill loads the anchor. The proposer's system prompt now includes:

```
[STATE ANCHOR — Acme Industrial Corp Compliance — v0.5.0 — CANONICAL]

# ENTITIES
## Acme Industrial Corp (AIC)
...

## Acme Performance LLC (AP)
- Entity type: LLC taxed as sole proprietorship
- Revenue: ~$180K/yr gross
- State: Ohio — registered as foreign LLC in two additional states
...

# OPEN POSITIONS
1. 2026-01-15 · AP multi-state nexus: AP shipped to customers in MI and IN
   last year. Need to determine whether economic nexus thresholds were crossed
   and whether retroactive registration is required.
   Blocked on: M. Chen's nexus analysis (requested 2026-01-15, ETA TBD).
...

# CANONICAL RULINGS
R-004 · AIC and AP must maintain strict operational separation...
...
```

The proposer immediately has the entity structure, the existing Open Position
about nexus, and the canonical rulings — without Jordan re-explaining any of it.

---

## Step 3: Proposer answer

The proposer answers:

> **Short answer: Possibly yes — and retroactively.**
>
> Indiana uses economic nexus: if you made more than $100,000 in sales or
> 200 transactions in Indiana in the prior or current calendar year, you must
> register. A single $12,000 order doesn't by itself cross the dollar threshold,
> but your anchor flags that AP shipped to Indiana customers **last year** (Open
> Position #1, under M. Chen's analysis). If last year's Indiana sales exceeded
> $100K or 200 transactions, AP is already past the nexus threshold and the
> registration is retroactively required.
>
> **What to do now:**
> 1. Pull AP's Indiana sales data for 2024 and 2025 YTD.
> 2. If 2024 Indiana revenue exceeded $100K or 200 transactions: register
>    immediately, pay any back tax + interest, and consider voluntary disclosure
>    to minimize penalties.
> 3. If below threshold: register prospectively if you expect to keep selling
>    into Indiana.
>
> Note: AP is already registered as a foreign LLC in two additional states
> (per anchor). Confirm whether Indiana is one of them — LLC registration ≠
> sales tax registration.
>
> RULING_IMPLIED: yes
> SUPERSEDES: none
> SCOPE: AP, [sales-tax, indiana, nexus]

---

## Step 4: Critic verification

The critic model (different family from proposer) receives the proposer's
answer and the anchor. It responds:

```json
{
  "risk": "low",
  "notes": "Indiana economic nexus threshold ($100K or 200 transactions) is
            correctly cited per current Indiana law. The proposer correctly
            references Open Position #1 and the existing LLC registration note
            from the anchor. The recommendation to pull sales data before
            registering is sound. No material claims contradict the anchor.",
  "unverified_claims": [
    "Voluntary disclosure availability and penalty structure — not verifiable
     without current Indiana DOR guidance. Proposer should hedge this."
  ]
}
```

`risk: low` — no re-prompt needed. The unverified claim about voluntary
disclosure is noted but doesn't change the core answer.

---

## Step 5: Ruling detection

The orchestrator parses the `RULING_IMPLIED: yes` block from the proposer's
answer. It calls the `ledger_provisional_audit` skill:

```python
audit_input = {
    "PROPOSED_DIFF": """
R-006 · 2026-03-20 · AP · [sales-tax, indiana, nexus] · AP must verify
        2024 Indiana sales against the $100K / 200-transaction economic nexus
        threshold before determining registration obligation. If threshold was
        crossed in 2024, registration is retroactively required. Pull sales
        data before next Indiana shipment.
        Source: compliance-session/2026-03-20/turn-001
        Supersedes: none
""",
    "SUPERSEDES_IDS": [],
    "SOURCE_TURN_REF": "compliance-session/2026-03-20/turn-001",
    "ANCHOR_PATH": "examples/acme-industrial/ANCHOR.md",
    "PROVISIONAL_DIR": "anchor_provisional/"
}
```

---

## Step 6: Provisional audit

The `ledger_provisional_audit` skill runs:

**1. Staging:** Writes `anchor_provisional/a3f9b2c1-...md`:

```yaml
---
type: provisional_ruling
provisional_id: a3f9b2c1-4d82-4e71-b1f3-9c8d3a2e6f01
source_turn: compliance-session/2026-03-20/turn-001
supersedes: []
proposed_at: 2026-03-20T14:22:07Z
status: pending_audit
---

R-006 · 2026-03-20 · AP · [sales-tax, indiana, nexus] · AP must verify...
```

**2. Self-check:** Proposer re-reads the anchor and confirms:
> "yes because Open Position #1 already flags the Indiana nexus question as
> unresolved, and this ruling correctly captures the standard economic nexus
> threshold and the required data-pull before deciding."

**3. Consistency check:** Scope `AP, [sales-tax, indiana, nexus]` — no overlap
with R-001 through R-005. Result: `"no conflicts detected"`.

**4. Supersede check:** `SUPERSEDES_IDS` is empty. Result: `"no supersedes declared"`.

**5. Critic cross-read:** Ruling involves a compliance obligation — triggers
high-stakes check. Critic confirms the Indiana nexus threshold and flags that
voluntary disclosure terms vary by year; ruling appropriately avoids specifying
penalty terms. Result: passes.

**Output:**
```json
{
  "provisional_id": "a3f9b2c1-...",
  "provisional_path": "anchor_provisional/a3f9b2c1-....md",
  "council_audit": {
    "self_check": "yes because Open Position #1 already flags this...",
    "consistency_check": "no conflicts detected",
    "supersede_check": "no supersedes declared",
    "critic_cross_read": "Indiana $100K threshold correctly stated..."
  },
  "ready_for_human_review": true,
  "blocking_reason": null
}
```

---

## Step 7: Human audit queue

The dashboard shows Jordan a pending provisional diff:

```
PROVISIONAL QUEUE — 1 item

R-006 (new) · AP · [sales-tax, indiana, nexus]
  "AP must verify 2024 Indiana sales against the $100K / 200-transaction
   economic nexus threshold before determining registration obligation..."

  Self-check:   ✓ Proposer confirmed
  Consistency:  ✓ No conflicts
  Supersedes:   n/a
  Critic:       ✓ Passed

  [ APPROVE ]   [ EDIT + APPROVE ]   [ REJECT ]
```

Jordan reviews, recognizes this accurately captures the discussion, and clicks
**APPROVE**.

---

## Step 8: Anchor update

The approval flow:
1. Appends R-006 to the CANONICAL RULINGS section of `ANCHOR.md`
2. Bumps version from `0.5.0` to `0.6.0`
3. Updates `last_canonical_audit: 2026-03-20` and `last_canonical_auditor: J. Rivera`
4. Archives the provisional diff to `anchor_history/v0.6.0/a3f9b2c1-....md`
5. Removes the file from `anchor_provisional/`
6. Commits with message: `chore(anchor): approve R-006 (AP indiana nexus)`

---

## Step 9: Next session — same question answered differently

Three months later, a team member asks via the same system:

> "Do we need to register for Indiana sales tax for AP?"

The orchestrator loads the anchor (now v0.6.0). The proposer sees R-006 in
CANONICAL RULINGS. Without any context from the March session, it answers:

> "Per R-006 (2026-03-20), AP is required to verify 2024 Indiana sales data
> against the $100K / 200-transaction economic nexus threshold before
> determining registration obligation. Has that data pull happened yet? If
> yes, I can advise based on the results. If the threshold was crossed, you
> need to register retroactively."

The decision persists. The reasoning is citable. The new session doesn't start
from scratch.

---

## What the walkthrough demonstrates

| Pattern | Where it appeared |
|---------|------------------|
| State Anchor | Step 2 — entity facts, Open Position #1, R-001..R-005 injected without Jordan re-explaining |
| council_precedent_review skill | Steps 3-4 — proposer answers, critic verifies |
| RULING_IMPLIED detection | Step 5 — orchestrator parses the trailing block |
| ledger_provisional_audit skill | Step 6 — staging, self-check, consistency, supersede, critic |
| [PROVISIONAL] gate | Steps 6-8 — human reviews before anchor is modified |
| Anchor update + version bump | Step 8 — approval triggers atomic anchor write |
| Durable precedent | Step 9 — ruling survives to next session without re-derivation |
