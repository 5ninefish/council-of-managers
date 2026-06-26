# Council of Managers

A pattern language for building AI systems that remember what they've decided —
and make future answers obey those decisions.

> **This is a workflow and memory architecture pattern. Nothing here is legal,
> tax, financial, or compliance advice.**

---

## The problem

You build an AI assistant for a complex domain — compliance, contracts, finance,
operations. It gives great answers in one session. Start a new session, and it
has no memory of anything: no entity facts, no prior rulings, no decisions that
should be settled by now.

You patch this with prompt-stuffing. The context window fills. RAG retrieval
hallucinations creep in. Distillation pipelines add latency and cost. The system
stays amnesiac at the level that matters most: *durable decisions that should
stick across months of use.*

## The pattern

**Council of Managers** is a set of composable patterns for giving AI systems
durable, auditable, human-governed memory. The core idea:

1. **State Anchor** — a curated markdown document of domain facts (entity
   structure, settled decisions, open positions), injected into every turn
   as the authoritative baseline. Human-maintained, version-controlled,
   always readable in one sitting.

2. **Fat Skills** — domain processes defined as markdown files, consumed as
   structured system prompts at runtime. Change the process by editing a file,
   not by redeploying code.

3. **[PROVISIONAL] gate** — any time an AI turn implies a new canonical fact
   or ruling, it gets staged as a provisional diff. A human reviews and approves
   before it merges into the anchor. No silent ledger corruption.

4. **Precedent Ledger** — immutable, dated, citable rulings. Future answers
   must reference the ledger. When a ruling is superseded, the chain is explicit.

5. **Multi-model council loop** — a proposer model answers, a critic model
   verifies against the anchor and citations. High-risk answers escalate to a
   strategic session. Cognitive diversity without framework bloat.

---

## Quick orientation (5 minutes)

```
Domain expert asks: "Does our Austin entity owe franchise tax this year?"

Orchestrator:
  1. Loads the State Anchor → knows entity structure, prior rulings, open questions
  2. Runs the council_precedent_review skill → proposer drafts answer, critic verifies
  3. Answer implies a new ruling → PROVISIONAL gate fires
  4. Human reviews the diff in the approval queue
  5. Approved → ruling merges into anchor with version bump and audit trail
  6. Next session: the same question gets the same answer, with citation
```

See [`examples/acme-industrial/WALKTHROUGH.md`](examples/acme-industrial/WALKTHROUGH.md)
for a full worked example using the fictional Acme Industrial Corp.

---

## What's in this repo

```
council-of-managers/
├── ARCHITECTURE.md                    # How the patterns fit together (read this second)
├── patterns/
│   ├── STATE_ANCHOR_TEMPLATE.md       # The anchor document structure
│   ├── PROVISIONAL_GATE.md            # The [PROVISIONAL] approval flow
│   └── FAT_SKILL_PATTERN.md           # The skill contract (inputs/outputs/failure)
├── skills/
│   ├── council_precedent_review.md    # Fat Skill: proposer/critic/ruling loop
│   └── ledger_provisional_audit.md    # Fat Skill: provisional gate flow
├── examples/
│   └── acme-industrial/
│       ├── ANCHOR.md                  # Example State Anchor (fictional entities)
│       └── WALKTHROUGH.md             # End-to-end worked example
├── scaffold/
│   ├── orchestrator.py                # Minimal Python scaffold (~80 lines)
│   └── README.md                      # How to use the scaffold
└── LICENSE                            # MIT
```

## Where to start

- **Understand the pattern:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **See it in action:** [`examples/acme-industrial/WALKTHROUGH.md`](examples/acme-industrial/WALKTHROUGH.md)
- **Build with it:** [`scaffold/orchestrator.py`](scaffold/orchestrator.py)
- **Define your own skills:** [`patterns/FAT_SKILL_PATTERN.md`](patterns/FAT_SKILL_PATTERN.md)

---

## What this is not

- Not a framework or library. Nothing to install. The patterns are structural.
- Not opinionated about which LLM provider you use. The skills reference
  `<proposer-model>` and `<critic-model>` as placeholders.
- Not a complete product. The scaffold shows the wiring; you write the
  domain-specific anchor content and skill procedures.

## Origin

This pattern emerged from building a multi-domain AI management system where
durable decisions needed to outlive individual sessions. The Tax Panel
reference implementation shipped first; Engine 1 (operations), Engine 2
(marketing), and a Trading Panel followed the same template.

The core insight: **the product is the Precedent Ledger, not better chat.**

---

MIT License. See [LICENSE](LICENSE).
