---
type: skill
name: council_precedent_review
version: 0.1.0
parameters:
  - TURN_QUESTION         # the user's question this turn
  - ANCHOR_PATH           # path to current canonical State Anchor
  - HISTORY_TURNS         # array of previous turns in this thread (last N)
  - SURFACE               # 'api' | 'cli' | 'webhook'
status: STABLE
---

# Skill: council_precedent_review

Defines how the runtime processes a single user turn when a State Anchor is
active. The proposer answers; the critic verifies against the anchor and
citations. If the answer implies a new ruling, the PROVISIONAL gate is
triggered. The orchestrator reads this file at runtime — changing the council
process means editing this file, not redeploying code.

## INPUTS

- `TURN_QUESTION` (string): the user's question this turn.
- `ANCHOR_PATH` (path): location of the canonical State Anchor markdown file.
  The anchor's entity facts and canonical rulings are injected into the
  proposer's system prompt as the authoritative baseline.
- `HISTORY_TURNS` (list): up to N most recent turns in the same thread, each
  with `{question, proposer_answer, ts}` shape. Inject as prior context, not
  as raw audit JSON.
- `SURFACE` (enum): `api` | `cli` | `webhook`. Controls formatting of the
  final answer (e.g., markdown for API, plain text for CLI).

## OUTPUTS

```json
{
  "proposer_answer": "<markdown answer to the user>",
  "critic_result": {
    "risk": "low | medium | high | skipped",
    "notes": "<critic's reasoning>",
    "unverified_claims": ["<claim 1>", "<claim 2>"]
  },
  "citations": [
    {"url": "<url>", "title": "<title>", "retrieved_at": "<iso>"}
  ],
  "implies_new_ruling": true,
  "proposed_ruling_diff": "<markdown diff against anchor if implies_new_ruling=true; null otherwise>",
  "supersedes_ruling_ids": ["<R-001>", "..."],
  "cost_usd": 0.07,
  "research_path": "web_search | none"
}
```

## PROCEDURE

### 1. CONTEXT ASSEMBLY

Load the State Anchor from `ANCHOR_PATH`. Inject the ENTITIES, OPERATIONAL
POSTURE, OPEN POSITIONS, and CANONICAL RULINGS sections verbatim into the
proposer's system prompt as the entity-and-precedent baseline.

If the anchor has a DRAFT status note, include it in the system prompt:
"Anchor is DRAFT v<version>. Markers like [PROVISIONAL] and [UNKNOWN] are
present — surface explicitly if your answer relies on a marker'd item."

Append `HISTORY_TURNS` as prior conversation context (question + answer only,
not internal audit fields).

### 2. PROPOSE

Call the proposer model with:

- System prompt: your domain system prompt + injected anchor context + history
- User prompt: `TURN_QUESTION`
- Tools: web search (optional — configure per your stack)
- Token cap: set to your domain's typical answer length (e.g., 2048)

Instruct the proposer:

> Use the State Anchor as your source of truth for entity facts. If a fact is
> marked [PROVISIONAL] or [UNKNOWN], say so in your answer — never silently
> assume the marker is resolved. If your answer implies a new canonical ruling
> or supersedes an existing one, end your answer with this literal block:
>
> ```
> RULING_IMPLIED: <yes|no>
> SUPERSEDES: <R-NNN or none>
> SCOPE: <entity and scope tags>
> ```

### 3. CRITIQUE

Call the critic model (choose a different model family from the proposer for
cognitive independence) with:

- The full proposer answer
- The injected anchor context (same as proposer saw)
- Critic instruction:
  > Verify every material claim against the anchor's CANONICAL RULINGS or
  > against the proposer's citations. Flag claims you cannot corroborate as
  > `unverified_claims`. Assess overall risk: low / medium / high. If the
  > proposer asserts a [PROVISIONAL] or [UNKNOWN] item as settled fact without
  > flagging the marker, that is an automatic medium-or-higher risk.

Critic output schema:
```json
{ "risk": "low|medium|high", "notes": "...", "unverified_claims": [...] }
```

If critic emits `risk: high`, allow one re-prompt to the proposer with the
critic's specific concerns. No further loop.

### 4. RULING DETECTION

Parse the trailing `RULING_IMPLIED` block from the proposer answer.

- If `RULING_IMPLIED: yes`:
  - Construct a `proposed_ruling_diff` — a new R-NNN entry in the anchor's
    CANONICAL RULINGS section format.
  - Set `implies_new_ruling: true`, `supersedes_ruling_ids: [...]`.
  - Return this output; the **orchestrator** routes it to the
    `ledger_provisional_audit` skill.
- If `RULING_IMPLIED: no`:
  - Set `implies_new_ruling: false`, `proposed_ruling_diff: null`.

### 5. COST + RETURN

Compute `cost_usd` using your provider's pricing for the proposer and critic
calls (tokens in + tokens out + any search API calls).

Return the full JSON object to the orchestrator. The orchestrator handles:
- Turn audit writes to your audit store
- PROVISIONAL gate routing (if `implies_new_ruling: true`)
- Cost cap enforcement / budget tracking

## ERROR HANDLING

- Web search fails: proposer answers without citations; critic auto-flags
  unverified claims as `unverified_claims`. Set `research_path: "none"`.
- Critic call fails: return with `risk: "skipped"` in `critic_result`.
  Proposer answer still returned — don't block the user.
- Proposer call fails: return a structured error; do not write a turn audit.
- `ANCHOR_PATH` not found: return error immediately; do not call any model.

## DOES NOT HANDLE

- Anchor file reads/writes — the orchestrator does that before calling this skill
- Audit trail writes to your audit store — the orchestrator does that after
- PROVISIONAL gate flow — the orchestrator routes to `ledger_provisional_audit`
- Cost cap enforcement / budget guard — the orchestrator does that
- Session state / thread management — the orchestrator does that

## VERSION HISTORY

- 0.1.0 — initial release; generalized from Tax Panel reference implementation
