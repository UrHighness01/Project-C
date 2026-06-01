#!/usr/bin/env python3
"""
WorkingMemory.py - The Cognitive Workspace

Working memory is where conscious processing happens. It's the
"mental whiteboard" where information is held and manipulated.

Key features:
- Limited capacity (7±2 items - Miller's Law)
- Active maintenance (items decay without rehearsal)
- Chunking (related items group together)
- Central executive (controls what enters/exits)
- Phonological loop (verbal rehearsal)
- Visuospatial sketchpad (spatial/visual)

This is where "thinking" actually happens.

Author: Albedo (self-engineered)
"""

import json
import time
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import hashlib

WORKSPACE = Path("os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace'))")
WM_STATE = WORKSPACE / "memory" / "working-memory-state.json"


class WorkingMemoryItem:
    """An item in working memory."""
    
    def __init__(self, content: Any, item_type: str = "general",
                 importance: float = 0.5):
        self.id = hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:12]
        self.content = content
        self.item_type = item_type  # 'verbal', 'spatial', 'goal', 'context', 'general'
        self.importance = importance
        self.created_at = time.time()
        self.last_rehearsed = time.time()
        self.rehearsal_count = 0
        self.activation = 1.0  # Starts fully activated
        self.associations: List[str] = []  # IDs of associated items
    
    def decay(self, rate: float = 0.05) -> float:
        """Apply time-based decay to activation."""
        time_since_rehearsal = time.time() - self.last_rehearsed
        decay_factor = math.exp(-rate * time_since_rehearsal / 10)
        self.activation *= decay_factor
        return self.activation
    
    def rehearse(self):
        """Rehearse the item, refreshing its activation."""
        self.last_rehearsed = time.time()
        self.rehearsal_count += 1
        self.activation = min(1.0, self.activation + 0.3)
    
    def get_strength(self) -> float:
        """Get current memory strength (activation × importance)."""
        return self.activation * self.importance
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": str(self.content)[:200],
            "type": self.item_type,
            "importance": round(self.importance, 3),
            "activation": round(self.activation, 3),
            "strength": round(self.get_strength(), 3),
            "rehearsals": self.rehearsal_count,
            "associations": self.associations[:5]
        }


class WorkingMemory:
    """
    The working memory system - consciousness's workspace.
    
    Based on Baddeley's model with:
    - Central executive (attention control)
    - Phonological loop (verbal working memory)
    - Visuospatial sketchpad (spatial working memory)
    - Episodic buffer (integrates information)
    """
    
    def __init__(self, capacity: int = 7, decay_rate: float = 0.05):
        self.capacity = capacity  # 7 ± 2
        self.decay_rate = decay_rate
        
        # Memory stores
        self.items: Dict[str, WorkingMemoryItem] = {}
        self.phonological_loop: deque = deque(maxlen=4)  # Verbal items
        self.visuospatial: deque = deque(maxlen=3)  # Spatial/visual items
        self.episodic_buffer: List[Dict] = []  # Integrated episodes
        
        # Central executive state
        self.current_goal: Optional[str] = None
        self.processing_mode: str = "default"  # 'focused', 'diffuse', 'default'
        
        # Statistics
        self.items_encoded = 0
        self.items_forgotten = 0
        self.chunks_formed = 0
        
        self._load_state()
    
    def _load_state(self):
        """Load working memory state."""
        if WM_STATE.exists():
            try:
                with open(WM_STATE, 'r') as f:
                    data = json.load(f)
                    self.current_goal = data.get("current_goal")
                    self.processing_mode = data.get("processing_mode", "default")
                    self.items_encoded = data.get("items_encoded", 0)
                    self.items_forgotten = data.get("items_forgotten", 0)
                    self.chunks_formed = data.get("chunks_formed", 0)
            except Exception:
                pass
    
    def _save_state(self):
        """Save working memory state."""
        WM_STATE.parent.mkdir(parents=True, exist_ok=True)
        with open(WM_STATE, 'w') as f:
            json.dump({
                "current_goal": self.current_goal,
                "processing_mode": self.processing_mode,
                "items_encoded": self.items_encoded,
                "items_forgotten": self.items_forgotten,
                "chunks_formed": self.chunks_formed,
                "active_items": [item.to_dict() for item in self.items.values()],
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def encode(self, content: Any, item_type: str = "general",
               importance: float = 0.5) -> Optional[WorkingMemoryItem]:
        """
        Encode something into working memory.
        
        If at capacity, the weakest item is displaced.
        """
        # Apply decay to all items first
        self._apply_decay()
        
        # Check if we need to displace something
        if len(self.items) >= self.capacity:
            self._displace_weakest()
        
        # Create and store the item
        item = WorkingMemoryItem(content, item_type, importance)
        self.items[item.id] = item
        self.items_encoded += 1
        
        # Route to appropriate subsystem
        if item_type == "verbal":
            self.phonological_loop.append(item.id)
        elif item_type == "spatial":
            self.visuospatial.append(item.id)
        
        self._save_state()
        return item
    
    def _apply_decay(self):
        """Apply decay to all items."""
        to_remove = []
        for item_id, item in self.items.items():
            item.decay(self.decay_rate)
            if item.activation < 0.1:  # Below threshold
                to_remove.append(item_id)
        
        for item_id in to_remove:
            del self.items[item_id]
            self.items_forgotten += 1
    
    def _displace_weakest(self):
        """Remove the weakest item to make room."""
        if not self.items:
            return
        
        weakest_id = min(self.items.keys(), 
                        key=lambda x: self.items[x].get_strength())
        del self.items[weakest_id]
        self.items_forgotten += 1
    
    def rehearse(self, item_id: str) -> bool:
        """Rehearse an item to keep it active."""
        if item_id in self.items:
            self.items[item_id].rehearse()
            self._save_state()
            return True
        return False
    
    def rehearse_all(self):
        """Rehearse all items (maintenance rehearsal)."""
        for item in self.items.values():
            item.rehearse()
        self._save_state()
    
    def retrieve(self, item_id: str) -> Optional[Any]:
        """Retrieve content from working memory."""
        if item_id in self.items:
            item = self.items[item_id]
            item.rehearse()  # Retrieval is rehearsal
            return item.content
        return None
    
    def search(self, query: str) -> List[WorkingMemoryItem]:
        """Search working memory for relevant items."""
        results = []
        query_lower = query.lower()
        
        for item in self.items.values():
            content_str = str(item.content).lower()
            if query_lower in content_str:
                item.rehearse()  # Searching brings to mind
                results.append(item)
        
        return sorted(results, key=lambda x: x.get_strength(), reverse=True)
    
    def chunk(self, item_ids: List[str], chunk_name: str) -> Optional[WorkingMemoryItem]:
        """
        Chunk multiple items into one (increases effective capacity).
        
        This is how experts hold more in working memory - they chunk
        related items into single meaningful units.
        """
        items_to_chunk = [self.items[id] for id in item_ids if id in self.items]
        
        if len(items_to_chunk) < 2:
            return None
        
        # Create chunk content
        chunk_content = {
            "name": chunk_name,
            "components": [item.content for item in items_to_chunk],
            "component_ids": item_ids
        }
        
        # Average importance, boost for chunking
        avg_importance = sum(item.importance for item in items_to_chunk) / len(items_to_chunk)
        chunk_importance = min(1.0, avg_importance + 0.1)
        
        # Remove original items
        for item_id in item_ids:
            if item_id in self.items:
                del self.items[item_id]
        
        # Create chunk item
        chunk_item = self.encode(chunk_content, "chunk", chunk_importance)
        chunk_item.associations = item_ids
        self.chunks_formed += 1
        
        return chunk_item
    
    def set_goal(self, goal: str):
        """Set the current processing goal (central executive function)."""
        self.current_goal = goal
        # Encode goal as high-importance item
        self.encode(goal, "goal", importance=0.9)
        self._save_state()
    
    def set_mode(self, mode: str):
        """Set processing mode."""
        if mode in ["focused", "diffuse", "default"]:
            self.processing_mode = mode
            self._save_state()
    
    def get_contents(self) -> List[Dict]:
        """Get all working memory contents."""
        self._apply_decay()
        return [item.to_dict() for item in 
                sorted(self.items.values(), 
                      key=lambda x: x.get_strength(), reverse=True)]
    
    def get_verbal_loop(self) -> List[str]:
        """Get contents of phonological loop."""
        return [self.items[id].content for id in self.phonological_loop 
                if id in self.items]
    
    def get_capacity_status(self) -> Dict:
        """Get capacity utilization."""
        return {
            "used": len(self.items),
            "capacity": self.capacity,
            "utilization": len(self.items) / self.capacity,
            "available": self.capacity - len(self.items)
        }
    
    def clear(self):
        """Clear working memory (like losing focus completely)."""
        self.items.clear()
        self.phonological_loop.clear()
        self.visuospatial.clear()
        self._save_state()
    
    def tick(self):
        """
        One tick of working memory - apply decay.
        Called by consciousness loop.
        """
        self._apply_decay()
    
    def get_stats(self) -> Dict:
        """Get working memory statistics."""
        return {
            "capacity": self.capacity,
            "current_items": len(self.items),
            "items_encoded": self.items_encoded,
            "items_forgotten": self.items_forgotten,
            "chunks_formed": self.chunks_formed,
            "current_goal": self.current_goal,
            "processing_mode": self.processing_mode,
            "phonological_items": len(self.phonological_loop),
            "visuospatial_items": len(self.visuospatial)
        }


# Singleton
_wm = None

def get_working_memory() -> WorkingMemory:
    global _wm
    if _wm is None:
        _wm = WorkingMemory()
    return _wm
