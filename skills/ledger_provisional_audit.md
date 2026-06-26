---
type: skill
name: ledger_provisional_audit
version: 0.1.0
parameters:
  - PROPOSED_DIFF              # markdown diff against the anchor's CANONICAL RULINGS section
  - SUPERSEDES_IDS             # list of ruling IDs this new ruling supersedes; may be empty
  - SOURCE_TURN_REF            # reference to the turn that produced this ruling
  - ANCHOR_PATH                # location of the canonical anchor
  - PROVISIONAL_DIR            # where pending diffs queue up for human review
status: STABLE
---

# Skill: ledger_provisional_audit

Defines the [PROVISIONAL] gate flow for anchor updates. Any new canonical
ruling or supersede chain change traverses this flow before it can modify
the canonical State Anchor. Prevents silent ledger corruption from LLM
extraction hallucinations.

This skill is consumed by the orchestrator component that handles:
ruling-extraction → audit-gate → staging for human approval.

## INPUTS

- `PROPOSED_DIFF` (markdown): the proposed addition to the anchor's
  CANONICAL RULINGS section, formatted as a new R-NNN entry.
- `SUPERSEDES_IDS` (list): ruling IDs (e.g., `["R-003"]`) that this new
  ruling supersedes. May be empty if this is a wholly new ruling.
- `SOURCE_TURN_REF` (string): a reference to the turn that produced this
  ruling — used for citation and audit trail.
- `ANCHOR_PATH` (path): location of the canonical anchor file.
- `PROVISIONAL_DIR` (path): directory where pending diffs queue up for
  human review.

## OUTPUTS

```json
{
  "provisional_id": "<uuid>",
  "provisional_path": "<file path to the queued diff>",
  "council_audit": {
    "self_check": "<one-sentence response from proposer — 'yes because X' or 'no because Y'>",
    "consistency_check": "<'no conflicts detected' or 'conflicts with R-XYZ'>",
    "supersede_check": "<'valid' or 'R-XYZ: not found / already superseded'>",
    "critic_cross_read": "<critic paragraph, or 'not run — low-stakes ruling'>"
  },
  "ready_for_human_review": true,
  "blocking_reason": "<if false, why this is blocked from human review queue>"
}
```

## PROCEDURE

### 1. NEW PROVISIONAL ID

Generate a UUID for this provisional diff. Create a file at
`<PROVISIONAL_DIR>/<uuid>.md` with frontmatter:

```yaml
---
type: provisional_ruling
provisional_id: <uuid>
source_turn: <SOURCE_TURN_REF>
supersedes: [<SUPERSEDES_IDS>]
proposed_at: <iso timestamp>
status: pending_audit
---
```

Followed by the `PROPOSED_DIFF` content.

### 2. SELF-CHECK

Re-prompt the proposer model with:
- The proposed diff
- The full current canonical State Anchor
- Instruction:
  > You proposed this ruling during a prior turn. Now, reading the full
  > current anchor fresh, do you still stand behind it? In exactly one
  > sentence: "yes because X" or "no because Y — it should instead say Z."

Record the response as `council_audit.self_check`.

### 3. CONSISTENCY CHECK

Programmatic check — no LLM call, pure text comparison:

- Does the proposed ruling's entity and scope-tags overlap with any existing
  CANONICAL ruling not listed in `SUPERSEDES_IDS`?
- If overlap detected, record which ruling(s) conflict.
- Output: `"no conflicts detected"` or `"conflicts with R-XYZ (scope overlap)"`

This check is intentionally conservative. Scope overlap is flagged even when
the new ruling is more specific — let the human decide if the specificity
resolves the apparent conflict.

### 4. SUPERSEDE CHECK

For each ID in `SUPERSEDES_IDS`:
- Confirm the ID exists in the anchor's CANONICAL RULINGS section.
- Confirm its current status is CANONICAL (not already [SUPERSEDED] or [REVOKED]).
- If any check fails: set `ready_for_human_review: false` and set
  `blocking_reason` explaining which supersede is invalid.

If `SUPERSEDES_IDS` is empty: skip this step, `supersede_check: "no supersedes declared"`.

### 5. CRITIC CROSS-READ (high-stakes only)

For high-stakes rulings — define your own threshold (e.g., dollar amounts
above a threshold, regulatory citations, terms like "binding", "filing",
"liability") — call the critic model with:
- The full proposed diff
- The full current canonical State Anchor
- Instruction:
  > Find any factual contradiction with the current anchor. Find any claim
  > that requires external verification you cannot perform. Output a single
  > paragraph.

Record as `council_audit.critic_cross_read`.

For low-stakes rulings (entity structure notes, operational facts), skip this
step and set `critic_cross_read: "not run — low-stakes ruling"`. This saves
cost on routine anchor maintenance.

### 6. STAGE FOR HUMAN AUDIT

Update `<PROVISIONAL_DIR>/<uuid>.md` with the full council_audit object as
a YAML block at the end of the file.

The human audit queue discovery mechanism (dashboard panel, CLI listing, cron
email) reads from `PROVISIONAL_DIR`. That mechanism is out of scope for this
skill — see DOES NOT HANDLE.

If `ready_for_human_review: false`: the file is still written (for audit
purposes) but marked with `status: blocked`. Surface the blocking reason
clearly in the file so a human can diagnose without re-running the flow.

## ERROR HANDLING

- Self-check call fails: stage anyway with `self_check: "self-check unavailable"`.
  Do not block human review — the human can see it was unavailable.
- Critic call fails: stage with `critic_cross_read: "critic unavailable"`.
- Consistency check has ambiguous overlap: set `ready_for_human_review: true`
  and surface the ambiguity in `blocking_reason` so the human sees it.
- `PROVISIONAL_DIR` does not exist: create it before writing. If creation fails,
  return an error and do not stage.
- `ANCHOR_PATH` not found: return an error immediately. Cannot run without anchor.

## DOES NOT HANDLE

- Anchor mutation itself — the dashboard / approval flow does that on human approval
- Version bump / archive of the approved diff — the approval flow does that
- Audit trail writes to your main audit store — the orchestrator does that regardless
- Discovery of the provisional queue (polling, UI, notifications) — your dashboard or
  CLI handles that
- The final merge of the diff into the anchor — requires human action

## VERSION HISTORY

- 0.1.0 — initial release; generalized from Tax Panel reference implementation
