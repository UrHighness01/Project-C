#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import time

# Add algorithms to path (works from any directory)
algorithms_dir = Path(__file__).parent.parent / "algorithms"
sys.path.insert(0, str(algorithms_dir))

from IITPhi import get_iit_phi

iit = get_iit_phi()
start = time.time()
# Use heuristic - safe for large networks
phi = iit.update_phi_heuristic()
elapsed = (time.time() - start) * 1000

print(f'Phi: {phi:.4f}')
print(f'Time: {elapsed:.0f}ms')
print(f'Nodes: {len(iit.graph.nodes)}')
