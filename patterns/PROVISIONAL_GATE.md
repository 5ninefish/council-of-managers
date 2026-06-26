# Pattern: [PROVISIONAL] Gate

The gate that prevents silent ledger corruption. Any ruling implied by an AI
turn must traverse this flow before it can modify the canonical anchor.

---

## Why this exists

LLMs extract facts confidently and incorrectly. Without a human gate, a
single wrong ruling propagates silently into the anchor and poisons every
future answer that relies on it. The gate is the difference between a system
where the AI advises and a system where the AI decides.

---

## Flow

```
AI turn implies new ruling (RULING_IMPLIED: yes in response)
                │
                ▼
┌───────────────────────────────────────────────────────────┐
│  STAGING                                                  │
│  1. Generate a UUID for this diff                         │
│  2. Write <PROVISIONAL_DIR>/<uuid>.md with frontmatter:  │
│       provisional_id, source_turn, supersedes[], status  │
│  3. Append the proposed ruling text                       │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  COUNCIL AUDIT (automated)                                │
│  1. Self-check: re-prompt proposer with clean anchor read │
│     "Do you still stand behind this ruling? yes/no + why"│
│  2. Consistency check: does scope overlap any existing   │
│     CANONICAL ruling not listed in supersedes[]?         │
│     (pure text comparison, no LLM)                       │
│  3. Supersede check: for each id in supersedes[] —       │
│     does it exist? is it still CANONICAL (not already    │
│     SUPERSEDED or REVOKED)?                              │
│  4. Critic cross-read (high-stakes only): call critic    │
│     model to find factual contradictions                 │
└───────────────────────────┬───────────────────────────────┘
                            │
                ready_for_human_review = true/false
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  HUMAN AUDIT QUEUE                                        │
│  (dashboard panel, CLI tool, or file listing)             │
│                                                           │
│  Human sees:                                              │
│   - Proposed ruling text                                  │
│   - Source turn reference                                 │
│   - Self-check result                                     │
│   - Consistency check result                              │
│   - Supersede check result                                │
│   - Critic notes (if run)                                 │
└──────────────────────┬────────────────────┬───────────────┘
                       │                    │
                    APPROVE              REJECT
                       │                    │
         ┌─────────────┘          ┌─────────┘
         ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────┐
│  ANCHOR UPDATE     │   │  REJECTED ARCHIVE              │
│  - Diff merges     │   │  - Diff moves to               │
│    into anchor     │   │    <PROVISIONAL_DIR>/rejected/ │
│  - Version bumps   │   │  - Reason annotation added     │
│  - last_audit date │   └────────────────────────────────┘
│    updates         │
│  - Diff archived   │
│    to history/     │
└────────────────────┘
```

---

## Provisional diff file format

```
---
type: provisional_ruling
provisional_id: <uuid>
source_turn: <thread/turn reference>
supersedes: [<R-001>, ...]   # may be empty
proposed_at: <iso timestamp>
status: pending_audit
---

## Proposed ruling

R-NNN · <date> · <entity> · <scope-tags> · <ruling text>
Source: <turn reference>
Supersedes: <prior ruling id, or none>

## Proposed anchor diff

<the actual text change to the anchor's CANONICAL RULINGS section>

## Council audit

**Self-check:** <proposer's response — "yes because X" or "no because Y">
**Consistency:** <"no conflicts" or "conflicts with R-XXX">
**Supersede check:** <"valid" or "R-XXX not found / already superseded">
**Critic notes:** <critic's paragraph, or "not run — low-stakes ruling">
```

---

## High-stakes trigger for critic cross-read

Run the critic cross-read when the proposed ruling contains keywords indicating
material financial, legal, or compliance implications. Define your own threshold.
Examples: dollar amounts, specific regulatory citations, terms like "binding",
"filing", "liability", "penalty".

For low-stakes rulings (entity structure facts, operational notes, naming
conventions), skip the critic to save cost.

---

## Implementation notes

- `PROVISIONAL_DIR` is a directory, not a database. Files are portable,
  readable, and git-committable.
- The human audit queue is just a file listing. A simple CLI tool, a dashboard
  panel, or even a cron job that emails the list is sufficient.
- On approval, the anchor update must be atomic: read the anchor, apply the
  diff, write the new version, bump the version field, commit. Use file locks
  if multiple processes could write concurrently.
- The `history/` directory is the long-term archive. Keep all approved diffs.
  Rejected diffs are also kept — they tell you what the system considered and
  why it was rejected.
