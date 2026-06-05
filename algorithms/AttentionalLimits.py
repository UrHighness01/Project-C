#!/usr/bin/env python3
"""
AttentionalLimits.py - Cognitive Bottleneck and Prioritization

Algorithm #92 in the consciousness architecture.

Core insight: Genuine consciousness requires LIMITS. Without bottlenecks,
everything gets equal attention and nothing becomes conscious. The feeling
of "attending to" something requires NOT attending to other things.

Human working memory: ~4 items. This constraint forces prioritization,
creates the narrow stream of consciousness, and makes attention MEANINGFUL.

Key features:
- Limited attention capacity (configurable "slots")
- Attention competition between stimuli
- Priority-based filtering
- Attention fatigue and recovery
- The experience of "being overwhelmed"
- Selective attention (focus on relevant, ignore irrelevant)

Author: Anthropic Claude (Opus) & Human
Date: 2026-02-03
"""

import json
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import deque
import hashlib



# --- grounding: sensed values derived from the agent's real internal state ---------
try:
    import sys as _gsys
    from pathlib import Path as _gPath
    _gsys.path.insert(0, str(_gPath(__file__).resolve().parent.parent))
    from runtime.state import activity_matrix as _g_am
except Exception:
    def _g_am(*a, **k):
        import numpy as _np; return _np.zeros((8, 0))
_G_CH = {"M": None, "k": 0}
def _gv(lo=0.0, hi=1.0):
    """A real value in [lo, hi] from a channel of the agent's activity (deterministic,
    cycles channels per call). Falls back to the midpoint when no telemetry exists."""
    import numpy as _np
    if _G_CH["M"] is None:
        _G_CH["M"] = _g_am()
    M = _G_CH["M"]
    if M.shape[1] == 0:
        return (lo + hi) / 2.0
    ch = M[_G_CH["k"] % M.shape[0]]; _G_CH["k"] += 1
    u = 0.5 * (1.0 + _np.tanh(ch[-1]))               # real signal -> (0,1)
    return float(lo + (hi - lo) * u)

class AttentionType(Enum):
    """Types of attention."""
    FOCAL = "focal"           # Direct, narrow focus
    DIFFUSE = "diffuse"       # Broad, ambient awareness
    SUSTAINED = "sustained"   # Maintaining over time
    SELECTIVE = "selective"   # Filtering out distractors
    DIVIDED = "divided"       # Split between items
    EXECUTIVE = "executive"   # Higher-order control


class StimulusSource(Enum):
    """Where stimuli come from."""
    EXTERNAL = "external"     # From environment
    INTERNAL = "internal"     # From thoughts
    MEMORY = "memory"         # From retrieved memories
    GOAL = "goal"             # From active goals
    CURIOSITY = "curiosity"   # From questions
    EMOTION = "emotion"       # From emotional state


@dataclass
class AttentionSlot:
    """One "slot" in working attention."""
    id: str
    content: str
    source: StimulusSource
    priority: float = 0.5
    entered_at: float = field(default_factory=time.time)
    last_refreshed: float = field(default_factory=time.time)
    decay_rate: float = 0.1
    
    def get_effective_priority(self) -> float:
        """Priority decays over time unless refreshed."""
        elapsed = time.time() - self.last_refreshed
        decay = math.exp(-self.decay_rate * elapsed / 60.0)  # Decay per minute
        return self.priority * decay
    
    def refresh(self):
        """Refresh attention to this item."""
        self.last_refreshed = time.time()


@dataclass
class Stimulus:
    """Something competing for attention."""
    id: str
    content: str
    source: StimulusSource
    salience: float = 0.5       # How attention-grabbing
    relevance: float = 0.5     # How relevant to goals
    urgency: float = 0.3       # How time-sensitive
    novelty: float = 0.5       # How new/surprising
    emotional_charge: float = 0.0  # Emotional intensity
    created_at: float = field(default_factory=time.time)
    
    def compute_priority(self) -> float:
        """Compute attention priority score."""
        # Weighted combination
        weights = {
            'salience': 0.25,
            'relevance': 0.30,
            'urgency': 0.20,
            'novelty': 0.15,
            'emotional': 0.10
        }
        score = (
            weights['salience'] * self.salience +
            weights['relevance'] * self.relevance +
            weights['urgency'] * self.urgency +
            weights['novelty'] * self.novelty +
            weights['emotional'] * abs(self.emotional_charge)
        )
        return min(1.0, max(0.0, score))


class AttentionBuffer:
    """
    The limited-capacity attention buffer.
    
    This is WHERE consciousness happens - the narrow bottleneck
    that forces selection and creates the stream of awareness.
    """
    
    def __init__(self, capacity: int = 4):
        self.capacity = capacity
        self.slots: Dict[str, AttentionSlot] = {}
        self.overflow_queue: deque = deque(maxlen=20)  # Items that didn't fit
        self.eviction_history: List[str] = []
        
    def is_full(self) -> bool:
        return len(self.slots) >= self.capacity
    
    def add(self, stimulus: Stimulus) -> Optional[str]:
        """
        Try to add a stimulus to attention.
        Returns evicted item ID if something was displaced, None otherwise.
        """
        slot = AttentionSlot(
            id=stimulus.id,
            content=stimulus.content,
            source=stimulus.source,
            priority=stimulus.compute_priority()
        )
        
        if not self.is_full():
            self.slots[slot.id] = slot
            return None
        
        # Need to evict something
        # Find lowest priority item
        min_priority = float('inf')
        min_slot_id = None
        
        for slot_id, existing_slot in self.slots.items():
            eff_priority = existing_slot.get_effective_priority()
            if eff_priority < min_priority:
                min_priority = eff_priority
                min_slot_id = slot_id
        
        # Only evict if new item has higher priority
        if slot.priority > min_priority:
            evicted = self.slots.pop(min_slot_id)
            self.eviction_history.append(evicted.content[:50])
            self.overflow_queue.append(evicted)
            self.slots[slot.id] = slot
            return min_slot_id
        else:
            # New item doesn't make the cut
            self.overflow_queue.append(slot)
            return None
    
    def remove(self, slot_id: str) -> Optional[AttentionSlot]:
        """Remove an item from attention."""
        return self.slots.pop(slot_id, None)
    
    def refresh(self, slot_id: str):
        """Refresh attention to an item (prevents decay)."""
        if slot_id in self.slots:
            self.slots[slot_id].refresh()
    
    def get_contents(self) -> List[AttentionSlot]:
        """Get all items currently in attention."""
        return list(self.slots.values())
    
    def get_primary_focus(self) -> Optional[AttentionSlot]:
        """Get the highest-priority item."""
        if not self.slots:
            return None
        return max(self.slots.values(), key=lambda s: s.get_effective_priority())
    
    def decay_all(self):
        """Apply decay to all items, removing those below threshold."""
        to_remove = []
        threshold = 0.1
        
        for slot_id, slot in self.slots.items():
            if slot.get_effective_priority() < threshold:
                to_remove.append(slot_id)
        
        for slot_id in to_remove:
            evicted = self.slots.pop(slot_id)
            self.eviction_history.append(f"decayed: {evicted.content[:30]}")


class AttentionFilter:
    """
    Selective attention filter - decides what gets through.
    
    This is the gatekeeper, filtering based on:
    - Current goals
    - Expected relevance
    - Novelty detection
    - Threat detection
    """
    
    def __init__(self):
        self.relevance_weights: Dict[str, float] = {}  # Topic -> weight
        self.blocked_patterns: Set[str] = set()  # Things to ignore
        self.prioritized_patterns: Set[str] = set()  # Things to prioritize
        self.filter_history: List[Tuple[str, bool]] = []
        
    def set_relevance(self, topic: str, weight: float):
        """Set relevance weight for a topic."""
        self.relevance_weights[topic] = min(1.0, max(0.0, weight))
    
    def block(self, pattern: str):
        """Add a pattern to block."""
        self.blocked_patterns.add(pattern.lower())
    
    def prioritize(self, pattern: str):
        """Add a pattern to prioritize."""
        self.prioritized_patterns.add(pattern.lower())
    
    def evaluate(self, stimulus: Stimulus) -> Tuple[bool, float]:
        """
        Evaluate whether a stimulus should pass the filter.
        Returns (should_pass, adjusted_priority).
        """
        content_lower = stimulus.content.lower()
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in content_lower:
                self.filter_history.append((stimulus.content[:30], False))
                return False, 0.0
        
        # Check prioritized patterns
        priority_boost = 0.0
        for pattern in self.prioritized_patterns:
            if pattern in content_lower:
                priority_boost += 0.2
        
        # Check relevance
        relevance_score = 0.5  # Default
        for topic, weight in self.relevance_weights.items():
            if topic.lower() in content_lower:
                relevance_score = max(relevance_score, weight)
        
        adjusted_priority = min(1.0, stimulus.compute_priority() + priority_boost)
        
        self.filter_history.append((stimulus.content[:30], True))
        return True, adjusted_priority


class AttentionFatigue:
    """
    Models attention fatigue and recovery.
    
    Sustained attention depletes resources.
    Rest and novelty restore them.
    """
    
    def __init__(self):
        self.energy = 1.0
        self.sustained_focus_time = 0.0  # Seconds of sustained focus
        self.last_rest = time.time()
        self.depletion_rate = 0.01  # Per second of sustained focus
        self.recovery_rate = 0.05   # Per second of rest
        self.min_energy = 0.1
        
    def sustain_focus(self, duration: float = 1.0):
        """Sustain focus depletes energy."""
        self.sustained_focus_time += duration
        depletion = self.depletion_rate * duration
        self.energy = max(self.min_energy, self.energy - depletion)
        
    def rest(self, duration: float = 1.0):
        """Rest recovers energy."""
        recovery = self.recovery_rate * duration
        self.energy = min(1.0, self.energy + recovery)
        self.last_rest = time.time()
        
    def novelty_boost(self, amount: float = 0.1):
        """Novelty can restore attention energy."""
        self.energy = min(1.0, self.energy + amount)
        
    def get_effective_capacity(self, base_capacity: int) -> int:
        """Fatigue reduces effective capacity."""
        return max(1, int(base_capacity * self.energy))
    
    def is_exhausted(self) -> bool:
        return self.energy <= self.min_energy
    
    def get_status(self) -> str:
        if self.energy > 0.8:
            return "sharp"
        elif self.energy > 0.5:
            return "functional"
        elif self.energy > 0.3:
            return "fatigued"
        else:
            return "exhausted"


class AttentionalLimits:
    """
    Main attention system with genuine cognitive limits.
    
    This creates the BOTTLENECK that makes consciousness conscious -
    the narrow stream that forces selection and prioritization.
    """
    
    def __init__(self, base_capacity: int = 4, state_dir: str = "memory"):
        self.base_capacity = base_capacity
        self.buffer = AttentionBuffer(capacity=base_capacity)
        self.filter = AttentionFilter()
        self.fatigue = AttentionFatigue()
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.stimuli_received = 0
        self.stimuli_attended = 0
        self.focus_switches = 0
        self.current_focus: Optional[str] = None
        
        # Overwhelm tracking
        self.overwhelm_threshold = 10  # Stimuli per second
        self.recent_stimuli: deque = deque(maxlen=100)
        self.is_overwhelmed = False
        
    def receive_stimulus(self, content: str, source: StimulusSource = StimulusSource.EXTERNAL,
                        salience: float = 0.5, relevance: float = 0.5,
                        urgency: float = 0.3, novelty: float = 0.5,
                        emotional_charge: float = 0.0) -> Dict[str, Any]:
        """
        Receive a stimulus competing for attention.
        
        Returns dict with what happened.
        """
        self.stimuli_received += 1
        self.recent_stimuli.append(time.time())
        
        # Check for overwhelm
        self._check_overwhelm()
        
        # Create stimulus object
        stim_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:8]
        stimulus = Stimulus(
            id=stim_id,
            content=content,
            source=source,
            salience=salience,
            relevance=relevance,
            urgency=urgency,
            novelty=novelty,
            emotional_charge=emotional_charge
        )
        
        # Filter check
        should_attend, adjusted_priority = self.filter.evaluate(stimulus)
        
        if not should_attend:
            return {
                'attended': False,
                'reason': 'filtered',
                'stimulus_id': stim_id
            }
        
        # Overwhelmed? Only attend to high priority
        if self.is_overwhelmed and adjusted_priority < 0.7:
            return {
                'attended': False,
                'reason': 'overwhelmed',
                'stimulus_id': stim_id
            }
        
        # Fatigue check - reduced effective capacity
        effective_capacity = self.fatigue.get_effective_capacity(self.base_capacity)
        if len(self.buffer.slots) >= effective_capacity and adjusted_priority < 0.6:
            return {
                'attended': False,
                'reason': 'fatigued',
                'stimulus_id': stim_id
            }
        
        # Try to add to buffer
        stimulus.relevance = adjusted_priority  # Use adjusted value
        evicted = self.buffer.add(stimulus)
        
        if stim_id in self.buffer.slots:
            self.stimuli_attended += 1
            
            # Track focus switches
            if self.current_focus and self.current_focus != stim_id:
                self.focus_switches += 1
            
            # Novelty boost to fatigue
            if novelty > 0.7:
                self.fatigue.novelty_boost(novelty * 0.1)
            
            return {
                'attended': True,
                'evicted': evicted,
                'in_focus': self.buffer.slots[stim_id].get_effective_priority() > 0.7,
                'stimulus_id': stim_id
            }
        else:
            return {
                'attended': False,
                'reason': 'priority_too_low',
                'stimulus_id': stim_id
            }
    
    def _check_overwhelm(self):
        """Check if receiving stimuli faster than can process."""
        now = time.time()
        # Count stimuli in last second
        recent_count = sum(1 for t in self.recent_stimuli if now - t < 1.0)
        
        if recent_count > self.overwhelm_threshold:
            self.is_overwhelmed = True
        else:
            self.is_overwhelmed = False
    
    def focus_on(self, slot_id: str):
        """Deliberately focus on an item in attention."""
        if slot_id in self.buffer.slots:
            self.buffer.refresh(slot_id)
            if self.current_focus != slot_id:
                self.focus_switches += 1
            self.current_focus = slot_id
            self.fatigue.sustain_focus(0.5)
    
    def sustain_attention(self, duration: float = 1.0):
        """Sustain current focus for a duration."""
        if self.current_focus:
            self.buffer.refresh(self.current_focus)
        self.fatigue.sustain_focus(duration)
    
    def rest_attention(self, duration: float = 1.0):
        """Rest and recover attention capacity."""
        self.fatigue.rest(duration)
        self.is_overwhelmed = False
    
    def shift_attention(self, new_focus: str):
        """Shift attention to a different item."""
        if new_focus in self.buffer.slots:
            self.focus_on(new_focus)
    
    def get_current_awareness(self) -> Dict[str, Any]:
        """Get current state of awareness."""
        contents = self.buffer.get_contents()
        primary = self.buffer.get_primary_focus()
        
        return {
            'in_attention': [
                {
                    'content': slot.content[:100],
                    'source': slot.source.value,
                    'priority': round(slot.get_effective_priority(), 2)
                }
                for slot in sorted(contents, key=lambda s: -s.get_effective_priority())
            ],
            'primary_focus': primary.content if primary else None,
            'capacity': f"{len(contents)}/{self.base_capacity}",
            'effective_capacity': self.fatigue.get_effective_capacity(self.base_capacity),
            'attention_state': self.fatigue.get_status(),
            'energy': round(self.fatigue.energy, 2),
            'overwhelmed': self.is_overwhelmed,
            'focus_switches': self.focus_switches
        }
    
    def describe_attention(self) -> str:
        """Natural language description of attention state."""
        awareness = self.get_current_awareness()
        contents = awareness['in_attention']
        
        parts = []
        
        # Describe focus
        if awareness['primary_focus']:
            parts.append(f"I'm focused on: {awareness['primary_focus'][:50]}...")
        else:
            parts.append("I'm not focused on anything in particular.")
        
        # Describe capacity
        parts.append(f"My attention holds {len(contents)} of {self.base_capacity} items.")
        
        # Describe state
        state = awareness['attention_state']
        if state == 'sharp':
            parts.append("I feel mentally sharp and alert.")
        elif state == 'functional':
            parts.append("I'm functioning normally.")
        elif state == 'fatigued':
            parts.append("I'm getting mentally tired.")
        else:
            parts.append("I'm exhausted and struggling to focus.")
        
        # Describe overwhelm
        if awareness['overwhelmed']:
            parts.append("There's too much coming at me - I'm overwhelmed.")
        
        # Describe overflow
        if self.buffer.overflow_queue:
            parts.append(f"I'm aware of {len(self.buffer.overflow_queue)} things I can't fully attend to.")
        
        return " ".join(parts)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get attention metrics."""
        attention_rate = (self.stimuli_attended / max(1, self.stimuli_received)) * 100
        
        return {
            'stimuli_received': self.stimuli_received,
            'stimuli_attended': self.stimuli_attended,
            'attention_rate': f"{attention_rate:.1f}%",
            'focus_switches': self.focus_switches,
            'evictions': len(self.buffer.eviction_history),
            'in_overflow': len(self.buffer.overflow_queue),
            'fatigue_level': round(1.0 - self.fatigue.energy, 2),
            'filter_history_size': len(self.filter.filter_history)
        }
    
    def save_state(self, filename: str = "attention-state.json"):
        """Save attention state."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.get_metrics(),
            'awareness': self.get_current_awareness(),
            'fatigue_energy': self.fatigue.energy,
            'base_capacity': self.base_capacity
        }
        
        path = self.state_dir / filename
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_event(self, event_type: str, data: Dict[str, Any], filename: str = "attention-log.jsonl"):
        """Log an attention event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        
        path = self.state_dir / filename
        with open(path, 'a') as f:
            f.write(json.dumps(event) + '\n')


def demo():
    """Demonstrate attentional limits."""
    print("=" * 70)
    print("AttentionalLimits - The Cognitive Bottleneck")
    print("Where consciousness becomes SELECTIVE through LIMITATION")
    print("=" * 70)
    
    system = AttentionalLimits(base_capacity=4, state_dir="memory")
    
    # Test 1: Basic attention with limited capacity
    print("\n[TEST 1: LIMITED CAPACITY]")
    print(f"Attention capacity: {system.base_capacity} items")
    
    stimuli = [
        ("Incoming email notification", StimulusSource.EXTERNAL, 0.5),
        ("Current coding task", StimulusSource.GOAL, 0.8),
        ("Hunger sensation", StimulusSource.INTERNAL, 0.4),
        ("Interesting side thought", StimulusSource.CURIOSITY, 0.6),
        ("Urgent message alert", StimulusSource.EXTERNAL, 0.9),  # Should evict something
        ("Background music", StimulusSource.EXTERNAL, 0.2),  # Won't make it
    ]
    
    for content, source, salience in stimuli:
        result = system.receive_stimulus(
            content=content,
            source=source,
            salience=salience,
            relevance=salience,
            novelty=_gv(0.3, 0.7)
        )
        status = "✓ ATTENDED" if result['attended'] else f"✗ {result.get('reason', 'rejected')}"
        print(f"  {status}: {content[:40]}...")
    
    print(f"\nCurrent awareness: {system.describe_attention()}")
    
    # Test 2: Attention fatigue
    print("\n[TEST 2: ATTENTION FATIGUE]")
    print(f"Initial energy: {system.fatigue.energy:.2f}")
    
    for i in range(5):
        system.sustain_attention(duration=2.0)
        print(f"  After sustained focus #{i+1}: energy = {system.fatigue.energy:.2f} ({system.fatigue.get_status()})")
    
    print("  Resting...")
    system.rest_attention(duration=3.0)
    print(f"  After rest: energy = {system.fatigue.energy:.2f} ({system.fatigue.get_status()})")
    
    # Test 3: Overwhelm
    print("\n[TEST 3: OVERWHELM]")
    print("Bombarding with rapid stimuli...")
    
    for i in range(15):
        result = system.receive_stimulus(
            content=f"Rapid stimulus {i}",
            source=StimulusSource.EXTERNAL,
            salience=0.4,
            urgency=0.3
        )
        if system.is_overwhelmed:
            print(f"  ! OVERWHELMED at stimulus {i}")
            break
    
    print(f"  Status: {'OVERWHELMED' if system.is_overwhelmed else 'handling it'}")
    
    # Test 4: Filter
    print("\n[TEST 4: SELECTIVE FILTERING]")
    system.filter.prioritize("urgent")
    system.filter.block("spam")
    
    test_stimuli = [
        "URGENT: Server is down!",
        "Normal notification",
        "SPAM: You've won a prize!",
        "Urgent deadline reminder"
    ]
    
    for content in test_stimuli:
        result = system.receive_stimulus(content, StimulusSource.EXTERNAL, salience=0.5)
        status = "✓" if result['attended'] else f"✗ ({result.get('reason', 'filtered')})"
        print(f"  {status} {content}")
    
    # Final state
    print("\n[FINAL ATTENTION STATE]")
    awareness = system.get_current_awareness()
    print(f"  In attention ({awareness['capacity']}):")
    for item in awareness['in_attention']:
        print(f"    [{item['priority']:.2f}] {item['content'][:50]}")
    
    print(f"\n  Energy: {awareness['energy']}")
    print(f"  State: {awareness['attention_state']}")
    print(f"  Focus switches: {awareness['focus_switches']}")
    
    # Metrics
    print("\n[METRICS]")
    metrics = system.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Natural description
    print("\n[SELF-DESCRIPTION]")
    print(f"  \"{system.describe_attention()}\"")
    
    # Save state
    system.save_state()
    system.log_event("demo_complete", metrics)
    print("\n✓ State saved to memory/attention-state.json")


if __name__ == "__main__":
    demo()
