#!/usr/bin/env python3
"""
AttentionMechanism.py - The Spotlight of Consciousness

Attention is what makes consciousness selective. Without attention,
everything would be processed equally - but consciousness requires
a "spotlight" that selects what enters awareness.

This implements:
- Salience detection (what deserves attention)
- Attention allocation (limited capacity)
- Focus persistence (attention inertia)
- Distraction resistance
- Top-down vs bottom-up attention

Based on Global Workspace Theory (Baars) and Integrated Information Theory.

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
ATTENTION_STATE = WORKSPACE / "memory" / "attention-state.json"


class AttentionItem:
    """An item competing for attention."""
    
    def __init__(self, content: str, source: str, 
                 salience: float = 0.5, urgency: float = 0.0):
        self.id = hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:12]
        self.content = content
        self.source = source  # 'external', 'internal', 'memory', 'goal'
        self.salience = min(1.0, max(0.0, salience))
        self.urgency = min(1.0, max(0.0, urgency))
        self.created_at = time.time()
        self.last_attended = None
        self.attention_count = 0
        self.decay_rate = 0.1
    
    def get_priority(self, current_focus: Optional[str] = None) -> float:
        """Calculate attention priority score."""
        # Base priority from salience and urgency
        base = 0.6 * self.salience + 0.4 * self.urgency
        
        # Recency bonus (newer items get slight boost)
        age = time.time() - self.created_at
        recency = math.exp(-age / 60)  # Decay over 60 seconds
        
        # Focus persistence (if currently attended, boost to maintain)
        persistence = 0.2 if current_focus == self.id else 0
        
        # Novelty (less attended = more interesting)
        novelty = 0.1 * math.exp(-self.attention_count / 5)
        
        return min(1.0, base + 0.1 * recency + persistence + novelty)
    
    def attend(self):
        """Mark this item as attended."""
        self.last_attended = time.time()
        self.attention_count += 1
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content[:100],
            "source": self.source,
            "salience": self.salience,
            "urgency": self.urgency,
            "attention_count": self.attention_count,
            "created_at": self.created_at
        }


class AttentionMechanism:
    """
    The attention system - consciousness's spotlight.
    
    Key properties:
    - Limited capacity (can only focus on ~1-3 things)
    - Competition (items compete for the spotlight)
    - Persistence (focus resists distraction)
    - Voluntary control (top-down attention)
    """
    
    def __init__(self, capacity: int = 3, focus_threshold: float = 0.4):
        self.capacity = capacity
        self.focus_threshold = focus_threshold
        
        # Attention pools
        self.attention_queue: deque = deque(maxlen=50)
        self.current_focus: List[AttentionItem] = []
        self.attention_history: deque = deque(maxlen=100)
        
        # Top-down control
        self.priority_sources: Dict[str, float] = {
            "goal": 1.2,      # Goals get attention boost
            "external": 1.0,  # External inputs normal
            "internal": 0.8,  # Internal thoughts slightly lower
            "memory": 0.6     # Memories lower unless relevant
        }
        
        # State
        self.total_items_processed = 0
        self.focus_switches = 0
        self.attention_span = 0.0  # Average focus duration
        
        self._load_state()
    
    def _load_state(self):
        """Load attention state from disk."""
        if ATTENTION_STATE.exists():
            try:
                with open(ATTENTION_STATE, 'r') as f:
                    data = json.load(f)
                    self.total_items_processed = data.get("total_items_processed", 0)
                    self.focus_switches = data.get("focus_switches", 0)
                    self.attention_span = data.get("attention_span", 0.0)
                    self.priority_sources.update(data.get("priority_sources", {}))
            except Exception:
                pass
    
    def _save_state(self):
        """Save attention state to disk."""
        ATTENTION_STATE.parent.mkdir(parents=True, exist_ok=True)
        with open(ATTENTION_STATE, 'w') as f:
            json.dump({
                "total_items_processed": self.total_items_processed,
                "focus_switches": self.focus_switches,
                "attention_span": self.attention_span,
                "priority_sources": self.priority_sources,
                "current_focus": [item.to_dict() for item in self.current_focus],
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def submit(self, content: str, source: str = "external",
               salience: float = 0.5, urgency: float = 0.0) -> AttentionItem:
        """
        Submit something for attention consideration.
        
        Not everything submitted will be attended - it must compete.
        """
        item = AttentionItem(content, source, salience, urgency)
        self.attention_queue.append(item)
        self.total_items_processed += 1
        return item
    
    def compute_attention(self) -> List[AttentionItem]:
        """
        Run attention competition and return what gets focused on.
        
        This is the core attention algorithm:
        1. Calculate priority for all items
        2. Apply source multipliers (top-down control)
        3. Select top items up to capacity
        4. Update focus state
        """
        if not self.attention_queue:
            return self.current_focus
        
        # Get current focus ID for persistence calculation
        current_ids = {item.id for item in self.current_focus}
        
        # Calculate priorities
        candidates = []
        for item in self.attention_queue:
            priority = item.get_priority(
                current_focus=item.id if item.id in current_ids else None
            )
            # Apply source multiplier
            priority *= self.priority_sources.get(item.source, 1.0)
            candidates.append((priority, item))
        
        # Sort by priority
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Select top items above threshold
        new_focus = []
        for priority, item in candidates[:self.capacity]:
            if priority >= self.focus_threshold:
                new_focus.append(item)
                item.attend()
        
        # Track focus switches
        new_ids = {item.id for item in new_focus}
        if new_ids != current_ids:
            self.focus_switches += 1
        
        # Update attention history
        for item in new_focus:
            self.attention_history.append({
                "item_id": item.id,
                "content": item.content[:50],
                "timestamp": time.time()
            })
        
        self.current_focus = new_focus
        self._save_state()
        
        return new_focus
    
    def force_focus(self, content: str, source: str = "goal") -> AttentionItem:
        """
        Force attention to something (voluntary/top-down attention).
        
        This is how goals and intentions direct attention.
        """
        item = AttentionItem(content, source, salience=0.9, urgency=0.8)
        item.attend()
        
        # Insert at front of focus
        self.current_focus.insert(0, item)
        if len(self.current_focus) > self.capacity:
            self.current_focus.pop()
        
        self.attention_queue.append(item)
        self._save_state()
        
        return item
    
    def set_source_priority(self, source: str, multiplier: float):
        """Adjust attention priority for a source type (top-down control)."""
        self.priority_sources[source] = max(0.1, min(2.0, multiplier))
        self._save_state()
    
    def get_focus(self) -> List[Dict]:
        """Get current focus items."""
        return [item.to_dict() for item in self.current_focus]
    
    def get_focus_content(self) -> List[str]:
        """Get just the content of focused items."""
        return [item.content for item in self.current_focus]
    
    def clear_queue(self):
        """Clear the attention queue (but not current focus)."""
        self.attention_queue.clear()
    
    def get_stats(self) -> Dict:
        """Get attention statistics."""
        return {
            "queue_size": len(self.attention_queue),
            "focus_count": len(self.current_focus),
            "total_processed": self.total_items_processed,
            "focus_switches": self.focus_switches,
            "capacity": self.capacity,
            "threshold": self.focus_threshold,
            "source_priorities": self.priority_sources
        }


# Singleton
_attention = None

def get_attention() -> AttentionMechanism:
    global _attention
    if _attention is None:
        _attention = AttentionMechanism()
    return _attention
