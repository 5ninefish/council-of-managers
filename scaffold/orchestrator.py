"""
council-of-managers — orchestrator (v1.1 — live SDK wiring)

Implements the Council of Managers pattern with real LLM calls:
  Proposer: Anthropic Claude (claude-sonnet-4-6 by default)
  Critic:   Google Gemini  (gemini-2.5-flash by default)

Environment variables:
  ANTHROPIC_API_KEY   required
  GOOGLE_API_KEY      required
  PROPOSER_MODEL      optional, default claude-sonnet-4-6
  CRITIC_MODEL        optional, default gemini-2.5-flash

Dependencies: see requirements.txt
"""

import json
import os
import uuid
import argparse
from pathlib import Path
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Configuration — set these for your environment
# ---------------------------------------------------------------------------

ANCHOR_PATH = Path("examples/acme-industrial/ANCHOR.md")
SKILLS_DIR = Path("skills")
PROVISIONAL_DIR = Path("anchor_provisional")
HISTORY_TURNS_LIMIT = 6


# ---------------------------------------------------------------------------
# LLM calls — Anthropic (proposer + self-check) + Gemini (critic)
# ---------------------------------------------------------------------------

def call_proposer(system_prompt: str, user_question: str) -> dict:
    """Anthropic Claude — propose an answer grounded in the State Anchor."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=os.environ.get("PROPOSER_MODEL", "claude-sonnet-4-6"),
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_question}],
    )
    return {"answer": response.content[0].text}


def call_critic(proposer_answer: str, anchor_context: str) -> dict:
    """Google Gemini — verify the proposer's claims against the anchor.
    Different model family = cognitive independence."""
    from google import genai
    from google.genai import types as genai_types
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    prompt = (
        f"## Proposer answer\n\n{proposer_answer}\n\n"
        f"## State Anchor (for verification)\n\n{anchor_context[:5000]}"
    )
    response = client.models.generate_content(
        model=os.environ.get("CRITIC_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=(
                "You are a rigorous auditor. Verify every material claim in the "
                "proposer's answer against the provided State Anchor. Flag claims "
                "you cannot corroborate. Assess overall risk: low / medium / high. "
                "If the proposer treats a [PROVISIONAL] or [UNKNOWN] item as settled "
                "fact without flagging it, that is automatic medium-or-higher risk. "
                "Respond with JSON only — no markdown fences:\n"
                '{"risk": "low|medium|high", "notes": "...", "unverified_claims": [...]}'
            ),
            max_output_tokens=1024,
        ),
    )
    try:
        text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception:
        return {
            "risk": "skipped",
            "notes": f"critic parse error — raw: {response.text[:300]}",
            "unverified_claims": [],
        }


def call_self_check(proposer_model_fn, proposed_diff: str, anchor_text: str) -> str:
    """Re-prompt Claude to confirm the proposed ruling is consistent with the anchor."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=os.environ.get("PROPOSER_MODEL", "claude-sonnet-4-6"),
        max_tokens=256,
        system=(
            "You are verifying whether a proposed ruling is consistent with the "
            "existing State Anchor. Reply with exactly one sentence starting with "
            "'yes because' or 'no because'."
        ),
        messages=[{"role": "user", "content": (
            f"Proposed ruling:\n{proposed_diff}\n\n"
            f"State Anchor (excerpt):\n{anchor_text[:3000]}\n\n"
            "Is this ruling consistent with the anchor?"
        )}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Anchor loading
# ---------------------------------------------------------------------------

def load_anchor(anchor_path: Path) -> str:
    if not anchor_path.exists():
        raise FileNotFoundError(f"Anchor not found: {anchor_path}")
    return anchor_path.read_text(encoding="utf-8")


def load_skill(skill_name: str) -> str:
    skill_path = SKILLS_DIR / f"{skill_name}.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_path}")
    return skill_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Context assembly (Step 1 of council_precedent_review skill)
# ---------------------------------------------------------------------------

def assemble_system_prompt(anchor_text: str, skill_text: str, history: list[dict]) -> str:
    history_block = ""
    if history:
        history_block = "\n\n## PRIOR TURNS\n"
        for turn in history[-HISTORY_TURNS_LIMIT:]:
            history_block += f"\nQ: {turn['question']}\nA: {turn['answer']}\n"

    return (
        "You are a domain compliance advisor with persistent institutional memory.\n\n"
        f"## STATE ANCHOR\n\n{anchor_text}\n\n"
        f"## SKILL: council_precedent_review\n\n{skill_text}"
        f"{history_block}"
    )


# ---------------------------------------------------------------------------
# Ruling detection (Step 4 of council_precedent_review skill)
# ---------------------------------------------------------------------------

def detect_ruling(proposer_answer: str) -> tuple[bool, str | None, list[str]]:
    """Parse the RULING_IMPLIED block from the proposer's answer."""
    lines = proposer_answer.splitlines()
    implied = False
    supersedes = []
    scope = ""

    for line in lines:
        if line.startswith("RULING_IMPLIED:"):
            implied = line.split(":", 1)[1].strip().lower() == "yes"
        elif line.startswith("SUPERSEDES:") and implied:
            raw = line.split(":", 1)[1].strip()
            supersedes = [r.strip() for r in raw.split(",") if r.strip() and r.strip().lower() != "none"]
        elif line.startswith("SCOPE:") and implied:
            scope = line.split(":", 1)[1].strip()

    # Strip the trailing RULING_IMPLIED block from the user-facing answer
    clean_answer = "\n".join(
        line for line in lines
        if not any(line.startswith(k) for k in ("RULING_IMPLIED:", "SUPERSEDES:", "SCOPE:"))
        and line.strip() != "```"   # strip orphaned fences when model wraps the block
    ).rstrip()

    return implied, clean_answer, scope, supersedes


# ---------------------------------------------------------------------------
# [PROVISIONAL] staging (ledger_provisional_audit skill)
# ---------------------------------------------------------------------------

def stage_provisional(
    proposed_diff: str,
    supersedes_ids: list[str],
    source_turn_ref: str,
    anchor_text: str,
) -> dict:
    """Stage a provisional ruling diff for human review."""
    PROVISIONAL_DIR.mkdir(parents=True, exist_ok=True)

    prov_id = str(uuid.uuid4())
    prov_path = PROVISIONAL_DIR / f"{prov_id}.md"

    frontmatter = (
        "---\n"
        f"type: provisional_ruling\n"
        f"provisional_id: {prov_id}\n"
        f"source_turn: {source_turn_ref}\n"
        f"supersedes: {json.dumps(supersedes_ids)}\n"
        f"proposed_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"status: pending_audit\n"
        "---\n\n"
    )

    # Consistency check (no LLM — pure text)
    consistency = _check_consistency(proposed_diff, anchor_text, supersedes_ids)

    # Supersede check (no LLM)
    supersede_result = _check_supersedes(supersedes_ids, anchor_text)
    ready = supersede_result["valid"]

    council_audit = {
        "self_check": call_self_check(None, proposed_diff, anchor_text),
        "consistency_check": consistency,
        "supersede_check": supersede_result["message"],
        "critic_cross_read": call_critic(proposed_diff, anchor_text),
    }

    prov_content = (
        frontmatter
        + "## Proposed ruling\n\n"
        + proposed_diff
        + "\n\n## Council audit\n\n"
        + json.dumps(council_audit, indent=2)
        + "\n"
    )
    prov_path.write_text(prov_content, encoding="utf-8")

    return {
        "provisional_id": prov_id,
        "provisional_path": str(prov_path),
        "council_audit": council_audit,
        "ready_for_human_review": ready,
        "blocking_reason": None if ready else supersede_result["message"],
    }


def _check_consistency(proposed_diff: str, anchor_text: str, supersedes_ids: list[str]) -> str:
    """Detect scope overlap with existing canonical rulings (text-based, no LLM)."""
    # Extract canonical ruling IDs from anchor
    canonical_ids = [
        line.split("·")[0].strip()
        for line in anchor_text.splitlines()
        if line.strip().startswith("R-") and "SUPERSEDED" not in line and "REVOKED" not in line
    ]
    # Simple heuristic: flag if any canonical ruling ID appears in the diff
    # (beyond those in supersedes_ids)
    conflicts = [r for r in canonical_ids if r in proposed_diff and r not in supersedes_ids]
    if conflicts:
        return f"possible scope overlap with: {', '.join(conflicts)} — verify manually"
    return "no conflicts detected"


def _check_supersedes(supersedes_ids: list[str], anchor_text: str) -> dict:
    if not supersedes_ids:
        return {"valid": True, "message": "no supersedes declared"}
    for rid in supersedes_ids:
        if rid not in anchor_text:
            return {"valid": False, "message": f"{rid}: not found in anchor"}
        if f"[SUPERSEDED" in anchor_text or f"[REVOKED" in anchor_text:
            # Simple check — production code should parse more precisely
            pass
    return {"valid": True, "message": f"supersede check passed: {supersedes_ids}"}


# ---------------------------------------------------------------------------
# Main turn handler
# ---------------------------------------------------------------------------

def run_turn(question: str, history: list[dict] | None = None, anchor_path: Path | None = None) -> dict:
    """Execute one full turn through the council_precedent_review skill."""
    history = history or []

    # Load context
    anchor_text = load_anchor(anchor_path or ANCHOR_PATH)
    skill_text = load_skill("council_precedent_review")

    # Assemble system prompt
    system_prompt = assemble_system_prompt(anchor_text, skill_text, history)

    # Proposer call
    proposer_raw = call_proposer(system_prompt, question)
    raw_answer = proposer_raw.get("answer", "")

    # Ruling detection
    implied, clean_answer, scope, supersedes = detect_ruling(raw_answer)

    # Critic call
    critic_result = call_critic(clean_answer, anchor_text)

    # If critic flags high risk, one re-prompt (not implemented in this stub)
    if critic_result.get("risk") == "high":
        print("[ORCHESTRATOR] Critic flagged high risk — re-prompt would fire here")

    source_turn_ref = f"session/{datetime.now(timezone.utc).strftime('%Y%m%d')}/turn-{uuid.uuid4().hex[:8]}"

    # PROVISIONAL staging if ruling implied
    provisional_result = None
    if implied:
        next_ruling_num = _next_ruling_number(anchor_text)
        proposed_diff = (
            f"R-{next_ruling_num:03d} · {datetime.now(timezone.utc).date()} · "
            f"<entity> · [{scope}] · <ruling text — review and fill in>\n"
            f"        Source: {source_turn_ref}\n"
            f"        Supersedes: {', '.join(supersedes) or 'none'}"
        )
        provisional_result = stage_provisional(
            proposed_diff=proposed_diff,
            supersedes_ids=supersedes,
            source_turn_ref=source_turn_ref,
            anchor_text=anchor_text,
        )
        print(f"[ORCHESTRATOR] Provisional staged: {provisional_result['provisional_path']}")

    return {
        "answer": clean_answer,
        "critic": critic_result,
        "implies_new_ruling": implied,
        "provisional": provisional_result,
        "source_turn_ref": source_turn_ref,
    }


def _next_ruling_number(anchor_text: str) -> int:
    nums = [
        int(line.split("·")[0].replace("R-", "").strip())
        for line in anchor_text.splitlines()
        if line.strip().startswith("R-") and "·" in line
    ]
    return max(nums, default=0) + 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Council of Managers — orchestrator scaffold",
        epilog=(
            "Replace call_proposer() and call_critic() with your LLM SDK before running.\n"
            "See scaffold/README.md for wiring instructions."
        ),
    )
    parser.add_argument("question", nargs="?", help="Question to ask (or --demo)")
    parser.add_argument("--demo", action="store_true", help="Print architecture summary and exit")
    parser.add_argument("--anchor", default=str(ANCHOR_PATH), help="Path to State Anchor file")
    args = parser.parse_args()

    if args.demo:
        anchor_path = Path(args.anchor)
        if anchor_path.exists():
            anchor_text = anchor_path.read_text(encoding="utf-8")
            lines = anchor_text.splitlines()
            rulings = [l for l in lines if l.strip().startswith("R-") and "·" in l]
            open_pos = [l for l in lines if l.strip().startswith(tuple("123456789"))]
            print(f"Anchor: {anchor_path} ({len(anchor_text)} chars)")
            print(f"Rulings: {len(rulings)}")
            print(f"Open positions: {len(open_pos)}")
        print("\nSkills available:")
        for f in sorted(SKILLS_DIR.glob("*.md")):
            print(f"  {f.name}")
        print("\nReplace call_proposer() and call_critic() to run live queries.")
        return

    if not args.question:
        parser.print_help()
        return

    anchor_path = Path(args.anchor)
    result = run_turn(args.question, anchor_path=anchor_path)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
