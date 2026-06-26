# Architecture: Council of Managers

Five composable patterns for AI systems with durable, auditable memory.

---

## The core insight

Most AI memory approaches fail at the same level: they try to make the *AI*
remember better. Council of Managers reframes the problem: make the *domain
knowledge* explicit and version-controlled, so any session — any model — starts
from the same authoritative baseline.

The AI doesn't remember. The anchor remembers. The AI reads the anchor.

---

## Pattern 1: State Anchor

A single markdown document that contains everything a domain AI needs as
immutable baseline context:

- **Entity facts** — what entities exist, their structure, their relationships
- **Filing / operational posture** — current state of ongoing obligations
- **Open positions** — questions that are explicitly unresolved
- **Canonical rulings** — decisions that are settled and must be obeyed
- **Revoked / superseded** — decisions that were reversed, with reason

The anchor is injected verbatim into the system prompt on every turn. It is:

- Human-maintained (the AI proposes changes; a human approves them)
- Version-controlled (every approved change bumps the version)
- Auditable (the full revision history is preserved)
- Bounded (target <20KB; if it grows beyond that, the Precedent Ledger takes over)

```
                    EVERY AI TURN
                         │
                ┌────────▼────────┐
                │  State Anchor   │  ← injected as system prompt prefix
                │  (v0.11.0)      │
                │  ENTITIES       │
                │  RULINGS        │
                │  OPEN POSITIONS │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │  Proposer model │
                │  answers the    │
                │  user's question│
                └─────────────────┘
```

See [`patterns/STATE_ANCHOR_TEMPLATE.md`](patterns/STATE_ANCHOR_TEMPLATE.md)
for the section structure and marker conventions.

**Scaling boundary:** At ~50KB, per-turn token cost inverts. At that scale,
switch to selective retrieval (Hindsight, RAG, or any vector memory) and use
the anchor as the index of settled facts rather than the full context.

---

## Pattern 2: Fat Skills

A Fat Skill is a domain process defined entirely in a markdown file. The
orchestrator reads the file at runtime and uses it as structured instructions.
No code deployment required to change the process.

```
skills/
    council_precedent_review.md     ← defines the proposer/critic/ruling loop
    ledger_provisional_audit.md     ← defines the [PROVISIONAL] gate flow
    supersede_check.md              ← defines supersede chain validation
```

**Why this works:** The skill file is the single source of truth for how a
process runs. Change the file, the process changes on the next turn. Version
the file in git and you have a full audit trail of process evolution.

**The skill contract** (see [`patterns/FAT_SKILL_PATTERN.md`](patterns/FAT_SKILL_PATTERN.md)):

- Required sections: INPUTS, OUTPUTS, PROCEDURE, ERROR HANDLING, DOES NOT HANDLE
- Inputs are named, typed, and documented
- Outputs are structured (JSON schema defined)
- Error paths are explicit: what happens when each step fails
- The skill declares what it deliberately does NOT handle (keeps responsibilities clean)

---

## Pattern 3: [PROVISIONAL] Gate

Any time an AI turn implies a new canonical fact or a change to an existing
ruling, that implication must be staged, reviewed, and explicitly approved
before it modifies the canonical anchor.

```
AI answer implies new ruling
         │
         ▼
┌─────────────────────────┐
│  PROVISIONAL staging    │
│  - Generate UUID        │
│  - Write diff file      │
│  - Self-check (proposer)│
│  - Consistency check    │
│  - Supersede validation │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Human audit queue      │
│  (dashboard / CLI)      │
└────────────┬────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
  APPROVE          REJECT
     │               │
     ▼               ▼
anchor updates   diff archived
version bumps    in rejected/
audit trail      with reason
```

**Why this gate matters:** LLM extraction hallucinations are silent. Without a
human-in-the-loop gate, a confidently-wrong ruling can silently enter the
anchor and poison every future answer. The gate is not optional for any use
case where decisions have real-world consequences.

See [`patterns/PROVISIONAL_GATE.md`](patterns/PROVISIONAL_GATE.md) for the
full flow and implementation notes.

---

## Pattern 4: Precedent Ledger

A flat relational table of immutable, citable rulings. The ledger is the
long-term complement to the anchor: while the anchor is a dense current-state
summary, the ledger is the complete history.

```sql
CREATE TABLE precedent_ledger (
  id               BIGSERIAL PRIMARY KEY,
  ts               TIMESTAMPTZ NOT NULL DEFAULT now(),
  entity           TEXT NOT NULL,
  source_turn_id   TEXT,
  scope_tags       TEXT[] NOT NULL,
  scope_expression TEXT,      -- SQL WHERE clause evaluated at recall time
  ruling_text      TEXT NOT NULL,
  superseded_by_id BIGINT REFERENCES precedent_ledger(id),
  provisional      BOOLEAN NOT NULL DEFAULT true,
  audit_status     TEXT NOT NULL DEFAULT 'pending',
  audited_at       TIMESTAMPTZ,
  audited_by       TEXT
);
```

Key design decisions:

- **Supersede is explicit:** a ruling that replaces another carries the ID of
  what it supersedes. The chain is queryable.
- **Revoke is distinct from supersede:** "replaced by a better ruling" vs
  "should never have been recorded" are different states.
- **scope_expression uses SQL:** queryable, no custom DSL invented, evaluated
  at recall time against the query context.
- **provisional=true until human audit:** LLM-extracted rulings are never
  canonical until a human clears them.

---

## Pattern 5: Multi-Model Council Loop

One model answers; a second model verifies. Disagreement escalates.

```
User question
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│  Tier A — Runtime                                          │
│                                                            │
│  ┌───────────────┐    ┌────────────────────────────────┐  │
│  │ Proposer      │    │ Critic                         │  │
│  │ (your model)  │───▶│ (different model/family)       │  │
│  │               │    │                                │  │
│  │ Anchor injected    │ Verifies claims against anchor │  │
│  │ Fat Skill guides   │ Flags unverified assertions    │  │
│  │ Cites sources      │ Assesses risk: low/med/high    │  │
│  └───────────────┘    └────────────┬───────────────────┘  │
│                                    │                       │
│                         risk=high → one re-prompt          │
│                                    │                       │
└────────────────────────────────────┼───────────────────────┘
                                     │
                          risk=high after re-prompt
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │  Tier C — Strategic     │
                        │  (web UI, ad-hoc)       │
                        │  Hard architecture pivots│
                        │  Quarterly reviews      │
                        └─────────────────────────┘
```

**Tier A** handles routine queries: anchor injection + proposer + critic.
Cost: ~$0.05–0.15/turn depending on models chosen.

**Tier C** handles high-stakes sessions: a Pro/Max web UI session with the
full anchor loaded manually. Output is pasted back into the system for review.

**Tier B** (batch/subscription CLI) is deferred until a concrete automation
need emerges that exceeds Tier A's API budget. The Fat Skills port forward to
Tier B without changes.

---

## How the patterns fit together

```
┌──────────────────────────────────────────────────────────────────┐
│  Domain knowledge layer                                          │
│                                                                  │
│  State Anchor ────── Precedent Ledger                            │
│  (current facts)     (full ruling history)                       │
│       │                      │                                   │
│       │              [PROVISIONAL] Gate                          │
│       │              (human approval)                            │
│       └──────────────────────┘                                   │
│                      │                                           │
└──────────────────────┼───────────────────────────────────────────┘
                       │ injected each turn
┌──────────────────────┼───────────────────────────────────────────┐
│  Runtime layer       │                                           │
│                      ▼                                           │
│  Orchestrator ──▶ Fat Skill ──▶ Proposer ──▶ Critic             │
│  (reads anchor)  (reads skill)  (answers)   (verifies)          │
│       │                                          │               │
│       └──────── turn audit write ────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
                       │ if ruling implied
┌──────────────────────┼───────────────────────────────────────────┐
│  Governance layer    │                                           │
│                      ▼                                           │
│  PROVISIONAL staging ──▶ Human audit queue ──▶ Anchor update    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Deployment shape

This pattern works with whatever infrastructure you already have:

| Concern | Minimum viable | Production |
|---------|---------------|------------|
| Anchor storage | A file in git | Same — git IS the database |
| Skill storage | A file in git | Same |
| Orchestrator | Python function | Python service |
| Proposer model | Any LLM API | Anthropic / OpenAI / Gemini |
| Critic model | Same API, different prompt | Different model family for independence |
| PROVISIONAL queue | A directory of files | A directory + dashboard panel |
| Precedent Ledger | Postgres table | Same |
| Audit trail | Git commit history | Git + archived diff files |

---

## What this pattern does NOT solve

- **Scale beyond ~50KB anchor:** at that scale, use selective retrieval.
  The anchor becomes an index; Hindsight or a vector DB becomes the store.
- **Concurrent writers:** if multiple agents write to the anchor concurrently,
  you need advisory locks or optimistic concurrency. The pattern assumes a
  single orchestrator.
- **Cross-entity isolation at retrieval time:** one anchor means all entities
  share the same context window. At P1 scale (multiple domains, multiple
  entities), consider per-entity anchors or entity-scoped memory banks.
- **Enforcement on direct bypass:** the [PROVISIONAL] gate fires only when
  queries flow through the orchestrator. Direct scripts or hand-edits bypass
  the gate. Document this as an architectural limit.
