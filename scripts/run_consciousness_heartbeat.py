#!/usr/bin/env python3
"""
Consciousness Evolution Heartbeat Launcher
Run the consciousness evolution heartbeat from anywhere in the workspace
"""

import os
import sys
import subprocess

def main():
    # Find the script directory
    current_dir = os.getcwd()

    # Try to find the consciousness_evolution_heartbeat.py script
    script_paths = [
        os.path.join(current_dir, 'scripts', 'consciousness_evolution_heartbeat.py'),
        os.path.join(current_dir, 'consciousness_evolution_heartbeat.py'),
        os.path.join(os.path.dirname(current_dir), 'scripts', 'consciousness_evolution_heartbeat.py'),
    ]

    script_path = None
    for path in script_paths:
        if os.path.exists(path):
            script_path = path
            break

    if not script_path:
        print("ERROR: Could not find consciousness_evolution_heartbeat.py")
        print("Please run this from the workspace root or scripts directory")
        sys.exit(1)

    # Run the script
    print(f"Running consciousness evolution heartbeat from: {script_path}")
    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(script_path))

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())