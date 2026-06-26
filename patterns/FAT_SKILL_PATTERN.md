# Pattern: Fat Skills

A Fat Skill is a domain process defined entirely in a markdown file and consumed
as structured runtime instructions by an orchestrator.

The name comes from the contrast with "thin skills" (a function name + a one-line
description). A Fat Skill carries the full procedure: inputs, outputs, step-by-step
process, error handling, and an explicit boundary for what it does NOT handle.

---

## Why markdown, not code

When you define a process in code, changing it requires a deployment. When you
define it in markdown, changing it requires editing a file. For processes that
evolve based on domain knowledge (how to evaluate a ruling, how to structure a
critique, when to escalate), markdown is the right level of abstraction.

The markdown file is also the documentation. There is no gap between what the
system does and what the file says it does.

---

## The Fat Skill contract

Every Fat Skill must have these sections, in this order:

### Required frontmatter

```yaml
---
type: skill
name: <snake_case_name>
version: <semver>
parameters:
  - PARAM_ONE       # short description on same line
  - PARAM_TWO
status: <DRAFT | STABLE | DEPRECATED>
---
```

### Required sections

| Section | Purpose |
|---------|---------|
| `## INPUTS` | Named, typed parameters with descriptions |
| `## OUTPUTS` | JSON schema of what the skill returns |
| `## PROCEDURE` | Numbered steps, each with sub-steps |
| `## ERROR HANDLING` | What to do when each step fails |
| `## DOES NOT HANDLE` | Explicit boundary — what the orchestrator or another skill handles |

### Optional sections

| Section | Purpose |
|---------|---------|
| `## VERSION HISTORY` | Changelog in descending order |
| `## EXAMPLES` | Concrete input/output pairs |

---

## INPUTS section format

```markdown
## INPUTS

- `PARAM_NAME` (type): description of what this parameter contains and where
  it comes from. Include expected format, constraints, or example values.
- `PARAM_NAME` (type): description.
```

Types: `string`, `path`, `list`, `json`, `boolean`, `enum: val1 | val2`.

---

## OUTPUTS section format

```markdown
## OUTPUTS

A single JSON object written to stdout:

{
  "field_name": <type>,               // description
  "nested": {
    "subfield": <type>                // description
  },
  "array_field": [<type>, ...]        // description
}
```

Define every field. If a field can be null, say so and say when.

---

## PROCEDURE section format

```markdown
## PROCEDURE

### 1. STEP NAME

One sentence describing what this step does and why.

- Sub-action 1: concrete instruction to the orchestrator/model
- Sub-action 2: include model instructions verbatim when they matter
- Output: what gets written/returned from this step

### 2. NEXT STEP NAME

...
```

Number steps. Name them in SCREAMING_SNAKE or Title Case — makes them
referenceable ("the CRITIQUE step" in conversation or in error messages).

---

## ERROR HANDLING section format

```markdown
## ERROR HANDLING

- <Step> fails: <what to do — skip / fall back / return error / retry once>
- <Step> returns empty: <behavior>
- <External call> times out: <behavior>
```

Every external call (LLM, web search, file read) needs an error path. "Fails"
is not a valid error path — specify the behavior.

---

## DOES NOT HANDLE section format

```markdown
## DOES NOT HANDLE

- <Thing 1> — that's the orchestrator's responsibility
- <Thing 2> — that's the <other-skill-name> skill
- <Thing 3> — that's the dashboard's responsibility
```

This section is as important as the others. It prevents scope creep and makes
the skill's boundary explicit. When a new engineer (or a new AI session) reads
the skill, they should immediately know what they can't rely on it for.

---

## Worked example skeleton

```markdown
---
type: skill
name: contract_review
version: 0.1.0
parameters:
  - CONTRACT_TEXT      # full text of the contract to review
  - ANCHOR_PATH        # path to the domain State Anchor
  - REVIEW_DEPTH       # "quick" | "thorough"
status: DRAFT
---

# Skill: contract_review

Reviews a contract against the domain anchor's canonical rulings and flags
conflicts, missing protections, and clauses that imply new rulings.

## INPUTS

- `CONTRACT_TEXT` (string): full text of the contract.
- `ANCHOR_PATH` (path): location of the canonical State Anchor markdown file.
- `REVIEW_DEPTH` (enum: quick | thorough): "quick" checks only canonical ruling
  conflicts. "thorough" additionally checks for missing protective clauses.

## OUTPUTS

{
  "conflicts": [
    {
      "ruling_id": "<R-NNN>",
      "clause_text": "<excerpt>",
      "conflict_description": "<one sentence>"
    }
  ],
  "missing_protections": ["<description>", ...],   // thorough only; [] for quick
  "implies_new_rulings": true | false,
  "proposed_rulings": ["<description>", ...]        // if implies_new_rulings=true
}

## PROCEDURE

### 1. LOAD CONTEXT

Load the State Anchor from `ANCHOR_PATH`. Extract the CANONICAL RULINGS section.
These rulings are the baseline for conflict detection.

### 2. CONFLICT SCAN

For each ruling in CANONICAL RULINGS:
- Search `CONTRACT_TEXT` for clauses that contradict the ruling.
- If found, add an entry to `conflicts` with the ruling ID, the clause excerpt,
  and a one-sentence description of the conflict.

### 3. PROTECTION SCAN (thorough only)

If `REVIEW_DEPTH` is "thorough":
- Check for these common missing protections: <list for your domain>
- Add each missing protection to `missing_protections`.

### 4. RULING IMPLICATIONS

Scan for clauses that imply facts not yet in the anchor.
If found, set `implies_new_rulings: true` and list descriptions in
`proposed_rulings`. The orchestrator routes these to the PROVISIONAL gate.

## ERROR HANDLING

- Anchor file not found: return error `{"error": "anchor_not_found", ...}`
- Contract text empty: return `{"conflicts": [], "missing_protections": [], ...}`
- Model call fails: retry once, then return error `{"error": "model_failure", ...}`

## DOES NOT HANDLE

- The PROVISIONAL gate for implied rulings — the orchestrator does that
- Audit trail writes — the orchestrator does that
- Cost tracking — the orchestrator does that

## VERSION HISTORY

- 0.1.0 — initial draft
```

---

## Versioning discipline

- Bump patch (0.1.x) for procedure clarifications that don't change the output schema.
- Bump minor (0.x.0) for new output fields or new procedure steps.
- Bump major (x.0.0) for breaking changes to the output schema or input contract.
- Mark deprecated skills with `status: DEPRECATED` and a note in VERSION HISTORY
  explaining what replaced them.
