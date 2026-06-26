# Scaffold

`orchestrator.py` is an ~80-line structural sketch of the Council of Managers
orchestrator. It shows the wiring without requiring any LLM API setup.

## What it does

- Loads the State Anchor from `ANCHOR_PATH`
- Loads the `council_precedent_review` skill from `skills/`
- Assembles the system prompt (anchor + skill + history)
- Calls `call_proposer()` (stub — replace with your SDK)
- Calls `call_critic()` (stub — replace with your SDK)
- Detects the `RULING_IMPLIED` block in the proposer's answer
- If `RULING_IMPLIED: yes` — calls `ledger_provisional_audit` logic and
  stages a provisional diff in `anchor_provisional/`

## Quick start

```bash
python scaffold/orchestrator.py --demo
```

This prints a summary of the anchor and available skills without making any API calls.

## Wiring in your LLM SDK

Replace the three stub functions in `orchestrator.py`:

### call_proposer (Anthropic example)

```python
import anthropic

client = anthropic.Anthropic()

def call_proposer(system_prompt: str, user_question: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_question}]
    )
    answer = response.content[0].text
    return {"answer": answer}
```

### call_critic (Google Gemini example)

```python
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
critic_model = genai.GenerativeModel("gemini-2.5-flash")

def call_critic(proposer_answer: str, anchor_context: str) -> dict:
    prompt = (
        f"ANCHOR:\n{anchor_context}\n\n"
        f"PROPOSER ANSWER:\n{proposer_answer}\n\n"
        "Verify every material claim against the anchor's CANONICAL RULINGS. "
        "Flag unverifiable claims. Assess risk: low / medium / high. "
        "Respond as JSON: {risk, notes, unverified_claims}"
    )
    response = critic_model.generate_content(prompt)
    import json
    return json.loads(response.text)
```

### call_self_check (re-prompt the proposer)

```python
def call_self_check(proposer_model_fn, proposed_diff: str, anchor_text: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=f"ANCHOR:\n{anchor_text}",
        messages=[{
            "role": "user",
            "content": (
                f"You proposed this ruling:\n\n{proposed_diff}\n\n"
                "Reading the full anchor fresh: do you still stand behind it? "
                "One sentence: 'yes because X' or 'no because Y.'"
            )
        }]
    )
    return response.content[0].text
```

## Running a live question

```bash
export ANTHROPIC_API_KEY=sk-...
export GEMINI_API_KEY=...
python scaffold/orchestrator.py "Does Acme Performance need to register for Indiana sales tax?"
```

The output is a JSON object with `answer`, `critic`, `implies_new_ruling`,
and `provisional` (if a ruling was staged).

## Extending the scaffold

- **Add web search:** attach a tool to `call_proposer()` using your provider's
  tool-use API. The skill's `research_path` field tracks whether search was used.
- **Add a real audit store:** replace the file-based provisional staging with
  a Postgres table (`precedent_ledger` schema in ARCHITECTURE.md).
- **Add a human approval UI:** build a simple CLI or web panel that reads from
  `anchor_provisional/`, shows the diff + audit object, and runs the anchor
  update on approval.
- **Multi-domain:** instantiate one anchor per domain, one orchestrator per
  domain. Domains share the same skill files.
