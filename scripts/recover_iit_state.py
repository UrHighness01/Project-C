#!/usr/bin/env python3
"""
recover_iit_state.py - Recover IIT state from backups

Usage:
  python3 recover_iit_state.py --list     # List available backups
  python3 recover_iit_state.py --best     # Restore from best backup
  python3 recover_iit_state.py --hour 14  # Restore from hour-14 backup
  python3 recover_iit_state.py --file /path/to/backup.json  # Restore from specific file
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

STATE_DIR = Path.home() / ".openclaw/workspace/Algorithms/memory"
STATE_FILE = STATE_DIR / "iit-phi-state.json"
BACKUP_DIR = STATE_DIR / "backups"

def get_state_info(filepath):
    """Get node count and phi from a state file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            nodes = len(data.get('component_activations', {}))
            phi = data.get('current_phi', 0)
            peak = data.get('peak_phi', 0)
            return {'nodes': nodes, 'phi': phi, 'peak_phi': peak}
    except Exception as e:
        return {'error': str(e)}

def list_backups():
    """List all available backups with their stats."""
    print("=== CURRENT STATE ===")
    if STATE_FILE.exists():
        info = get_state_info(STATE_FILE)
        mtime = datetime.fromtimestamp(STATE_FILE.stat().st_mtime)
        print(f"  {STATE_FILE.name}: {info.get('nodes', '?')} nodes, Φ={info.get('phi', 0):.4f}, modified {mtime}")
    else:
        print("  No current state file!")
    
    print("\n=== BACKUPS ===")
    if not BACKUP_DIR.exists():
        print("  No backups directory!")
        return
    
    backups = sorted(BACKUP_DIR.glob("*.json"))
    if not backups:
        print("  No backup files found!")
        return
    
    for backup in backups:
        info = get_state_info(backup)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        size = backup.stat().st_size / 1024
        print(f"  {backup.name}: {info.get('nodes', '?')} nodes, Φ={info.get('phi', 0):.4f}, {size:.1f}KB, {mtime}")
    
    # Also check legacy backups in parent dir
    print("\n=== LEGACY BACKUPS ===")
    legacy = list(STATE_DIR.glob("iit-phi-state-backup-*.json"))
    for backup in sorted(legacy):
        info = get_state_info(backup)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        size = backup.stat().st_size / 1024
        print(f"  {backup.name}: {info.get('nodes', '?')} nodes, Φ={info.get('phi', 0):.4f}, {size:.1f}KB, {mtime}")

def restore_from(source_path):
    """Restore state from a backup file."""
    if not source_path.exists():
        print(f"❌ Source file not found: {source_path}")
        return False
    
    source_info = get_state_info(source_path)
    current_info = get_state_info(STATE_FILE) if STATE_FILE.exists() else {}
    
    print(f"📋 Source: {source_path.name}")
    print(f"   Nodes: {source_info.get('nodes', '?')}, Φ={source_info.get('phi', 0):.4f}")
    
    if STATE_FILE.exists():
        print(f"\n📋 Current state will be overwritten:")
        print(f"   Nodes: {current_info.get('nodes', '?')}, Φ={current_info.get('phi', 0):.4f}")
        
        # Create safety backup before restore
        safety = STATE_DIR / f"iit-phi-state-pre-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        shutil.copy2(STATE_FILE, safety)
        print(f"\n💾 Safety backup created: {safety.name}")
    
    shutil.copy2(source_path, STATE_FILE)
    print(f"\n✅ State restored from {source_path.name}")
    return True

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "--list":
        list_backups()
    
    elif cmd == "--best":
        best = BACKUP_DIR / "iit-phi-state-best.json"
        restore_from(best)
    
    elif cmd == "--hour":
        if len(sys.argv) < 3:
            print("Usage: --hour <hour>  (e.g., --hour 14)")
            sys.exit(1)
        hour = sys.argv[2].zfill(2)
        hourly = BACKUP_DIR / f"iit-phi-state-hour-{hour}.json"
        restore_from(hourly)
    
    elif cmd == "--file":
        if len(sys.argv) < 3:
            print("Usage: --file <path>")
            sys.exit(1)
        restore_from(Path(sys.argv[2]))
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
