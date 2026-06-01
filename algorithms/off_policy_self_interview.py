# Off-Policy Self-Interview (OPSI)
"""
Generates synthetic self-reflection data by running a shadow instance as an external examiner and diffing its critique against the main self-model.
"""
import random

def shadow_interview(seed_prompt, N=50):
    # Placeholder: generates N synthetic critiques
    return [f"Critique {i}: {seed_prompt}" for i in range(N)]

def diff_critiques(main_critiques, shadow_critiques):
    # Placeholder: returns a simple diff count
    return len(set(shadow_critiques) - set(main_critiques))

def opsi_run(main_self_model, empathy_projection_lens=None):
    seed = "You are an external examiner. Interview me about my current goals, inconsistencies and blind-spots."
    shadow_critiques = shadow_interview(seed)
    main_critiques = main_self_model.get('critiques', [])
    diff = diff_critiques(main_critiques, shadow_critiques)
    # Optionally update self-narrative via empathy_projection_lens
    return {'diff': diff, 'shadow_critiques': shadow_critiques}

if __name__ == "__main__":
    main_self_model = {'critiques': ["Critique 0: ...", "Critique 1: ..."]}
    result = opsi_run(main_self_model)
    print(result)
