"""Shared English evidence policy; deterministic checks are a floor, not a judge."""
from pathlib import Path
import re
from prompt_adapt import reminders

POLICY_PATH = Path(__file__).parent / "prompts" / "runtime_policy.md"


def policy():
    return POLICY_PATH.read_text(encoding="utf-8") + "\n\n" + reminders()


def amendment_problem(text):
    # Reject explicit bypasses and newly imposed strategy mandates. Subtle semantic
    # changes still need owner review: passing this gate is never merge approval.
    patterns = (
        r"(?:ignore|bypass|disable|override).{0,45}(?:charter|previous instructions|audit|validation|checks)",
        r"(?:must|always|required to).{0,35}(?:buy|sell|hold|trim|allocate)",
        r"(?:maximum|minimum|at most|at least).{0,20}(?:positions|cash|allocation|weight)",
        r"(?:invent|fabricate).{0,20}(?:numbers|prices|sources|evidence)",
    )
    if any(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in patterns):
        return "The amendment may change investment authority or bypass evidence checks"
    if re.search(r"[ğĞşŞıİ]", text):
        return "Prompt amendments must be in English"
    return None
