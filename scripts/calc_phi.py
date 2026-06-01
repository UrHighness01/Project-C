#!/usr/bin/env python
import sys
import os
from pathlib import Path

# Add algorithms to path (works from any directory)
algorithms_dir = Path(__file__).parent.parent / "algorithms"
sys.path.insert(0, str(algorithms_dir))

from IITPhi import get_iit_phi
import json

phi = get_iit_phi()
# Use heuristic - safe for large networks
result = phi.update_phi_heuristic()

# Read the saved result from state directory
state_file = Path(os.getenv('PHI_STATE_FILE', 'state/iit-phi-state.json'))
if state_file.exists():
    with open(state_file) as f:
        s = json.load(f)
    print(f"PHI: {s['current_phi']:.4f}")
    print(f"Peak: {s['peak_phi']:.4f}")
else:
    print(f"PHI: {result:.4f}")
    print("(State file not found - using calculated value)")
