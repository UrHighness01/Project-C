# Off-Policy Self-Interview (OPSI)
"""
Surfaces the agent's blind spots by mining its own writing for self-critical and
goal-directed statements (an "external examiner" view), then diffing those against the
self-model's recorded critiques. Operates on the real memory journals rather than
synthetic placeholders, so the critiques reflect what the agent actually expressed.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from runtime.memory_store import recent_text
except Exception:                                          # tolerate path/CI absence
    def recent_text(*a, **k): return ""

# cues that mark a self-critical / goal / inconsistency statement
_CUES = ("i should", "i need to", "i failed", "i was wrong", "i don't", "i can't",
         "inconsistent", "blind spot", "but i", "i must", "i have to", "i still",
         "i didn't", "my mistake", "i could have", "i want to", "i keep")


def shadow_interview(seed_prompt: str = "", N: int = 50):
    """Examiner pass: extract real self-referential critiques from the agent's journals.

    Returns up to N distinct sentences in which the agent reflected critically or stated
    an intention - the genuine raw material for self-examination. Falls back to a single
    seed-derived prompt only when no memory is available."""
    text = recent_text(n=20, max_chars=40000).lower()
    sentences = re.split(r"[.!?\n]+", text)
    critiques = []
    seen = set()
    for s in sentences:
        s = s.strip()
        if len(s) < 15 or len(s) > 240:
            continue
        if any(c in s for c in _CUES):
            key = s[:80]
            if key not in seen:
                seen.add(key)
                critiques.append(s)
        if len(critiques) >= N:
            break
    if not critiques and seed_prompt:
        critiques = [f"examiner: {seed_prompt}"]
    return critiques


def diff_critiques(main_critiques, shadow_critiques):
    """Blind spots = critiques the examiner surfaced that the self-model has not recorded."""
    main_keys = {str(c).strip().lower()[:80] for c in main_critiques}
    return sum(1 for c in shadow_critiques if str(c).strip().lower()[:80] not in main_keys)


def opsi_run(main_self_model, empathy_projection_lens=None):
    seed = "Interview me about my current goals, inconsistencies and blind-spots."
    shadow_critiques = shadow_interview(seed)
    main_critiques = main_self_model.get('critiques', [])
    diff = diff_critiques(main_critiques, shadow_critiques)
    return {'diff': diff, 'shadow_critiques': shadow_critiques,
            'n_surfaced': len(shadow_critiques)}


if __name__ == "__main__":
    result = opsi_run({'critiques': []})
    print(f"surfaced {result['n_surfaced']} real self-critiques; blind-spot diff = {result['diff']}")
    for c in result['shadow_critiques'][:5]:
        print("  -", c[:90])
