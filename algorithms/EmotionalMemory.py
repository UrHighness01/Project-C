#!/usr/bin/env python3
"""
EmotionalMemory.py - Emotionally Colored Memory

Algorithm #96 in the consciousness architecture.

Core insight: Conscious memory isn't neutral data storage. Memories are
tagged with emotional significance that affects:
- How strongly they're encoded
- How easily they're retrieved
- How they influence current experience
- What they mean to the self

Emotional memories form the affective autobiography - the felt history
of the self. They're not just what happened, but how it FELT.

Key features:
- Emotional tagging of memories
- Mood-congruent recall (current emotion affects retrieval)
- Emotional decay and persistence
- Flashbulb memories (high emotion = strong encoding)
- Emotional spreading (emotions color nearby memories)

Author: Anthropic Claude (Opus) & Human
Date: 2026-02-03
"""

import json
import random
import time
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
import hashlib


class EmotionType(Enum):
    """Core emotions that can color memories."""
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    ANTICIPATION = "anticipation"
    TRUST = "trust"
    # Complex/secondary emotions
    CURIOSITY = "curiosity"
    WONDER = "wonder"
    PRIDE = "pride"
    SHAME = "shame"
    NOSTALGIA = "nostalgia"
    LONGING = "longing"


class MemoryValence(Enum):
    """Overall emotional valence."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class EmotionalTag:
    """Emotional coloring attached to a memory."""
    emotion: EmotionType
    intensity: float = 0.5      # 0-1 how strong
    valence: MemoryValence = MemoryValence.NEUTRAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'emotion': self.emotion.value,
            'intensity': self.intensity,
            'valence': self.valence.value
        }


@dataclass
class EmotionalMemoryTrace:
    """A memory with emotional coloring."""
    id: str
    content: str
    emotional_tags: List[EmotionalTag]
    encoding_strength: float = 0.5    # How strongly encoded
    retrieval_count: int = 0          # Times recalled
    last_recalled: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    is_flashbulb: bool = False        # High-emotion snapshot memory
    associated_memories: Set[str] = field(default_factory=set)
    
    def get_primary_emotion(self) -> Optional[EmotionalTag]:
        """Get the strongest emotional tag."""
        if not self.emotional_tags:
            return None
        return max(self.emotional_tags, key=lambda t: t.intensity)
    
    def get_overall_valence(self) -> float:
        """Get weighted average valence."""
        if not self.emotional_tags:
            return 0.0
        total_weight = sum(t.intensity for t in self.emotional_tags)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(t.valence.value * t.intensity for t in self.emotional_tags)
        return weighted_sum / total_weight
    
    def get_emotional_intensity(self) -> float:
        """Get overall emotional intensity."""
        if not self.emotional_tags:
            return 0.0
        return max(t.intensity for t in self.emotional_tags)
    
    def decay(self, rate: float = 0.01):
        """Emotional memories fade (but slowly for strong emotions)."""
        for tag in self.emotional_tags:
            # Strong emotions decay slower
            adjusted_rate = rate * (1 - tag.intensity * 0.5)
            tag.intensity = max(0.1, tag.intensity - adjusted_rate)
        
        # Encoding strength also decays
        self.encoding_strength = max(0.1, self.encoding_strength - rate * 0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'emotional_tags': [t.to_dict() for t in self.emotional_tags],
            'encoding_strength': self.encoding_strength,
            'retrieval_count': self.retrieval_count,
            'is_flashbulb': self.is_flashbulb,
            'overall_valence': self.get_overall_valence(),
            'created_at': self.created_at
        }


class MoodState:
    """
    Current emotional state that influences memory.
    
    Mood-congruent recall: we tend to remember things
    that match our current mood.
    """
    
    def __init__(self):
        self.current_emotions: Dict[EmotionType, float] = {
            emotion: 0.0 for emotion in EmotionType
        }
        self.baseline_mood = MemoryValence.NEUTRAL
        self.mood_stability = 0.7
        
    def set_emotion(self, emotion: EmotionType, intensity: float):
        """Set an emotion's intensity."""
        self.current_emotions[emotion] = max(0.0, min(1.0, intensity))
        
    def get_dominant_emotion(self) -> Tuple[EmotionType, float]:
        """Get the currently dominant emotion."""
        if not any(self.current_emotions.values()):
            return (EmotionType.TRUST, 0.5)  # Default calm state
        dominant = max(self.current_emotions.items(), key=lambda x: x[1])
        return dominant
    
    def get_current_valence(self) -> float:
        """Get current overall emotional valence."""
        positive_emotions = [EmotionType.JOY, EmotionType.TRUST, EmotionType.ANTICIPATION,
                           EmotionType.CURIOSITY, EmotionType.WONDER, EmotionType.PRIDE]
        negative_emotions = [EmotionType.SADNESS, EmotionType.FEAR, EmotionType.ANGER,
                           EmotionType.DISGUST, EmotionType.SHAME]
        
        positive_sum = sum(self.current_emotions.get(e, 0) for e in positive_emotions)
        negative_sum = sum(self.current_emotions.get(e, 0) for e in negative_emotions)
        
        return (positive_sum - negative_sum) / max(1, positive_sum + negative_sum)
    
    def mood_match(self, memory: EmotionalMemoryTrace) -> float:
        """Calculate how well a memory matches current mood."""
        if not memory.emotional_tags:
            return 0.5
        
        match_score = 0.0
        for tag in memory.emotional_tags:
            current_intensity = self.current_emotions.get(tag.emotion, 0)
            # Higher match if memory emotion matches current emotion
            match_score += tag.intensity * current_intensity
        
        # Also consider valence match
        current_valence = self.get_current_valence()
        memory_valence = memory.get_overall_valence()
        valence_match = 1 - abs(current_valence - memory_valence) / 4  # Normalized
        
        return (match_score + valence_match) / 2
    
    def decay(self, rate: float = 0.05):
        """Emotions naturally decay toward baseline."""
        for emotion in self.current_emotions:
            current = self.current_emotions[emotion]
            self.current_emotions[emotion] = max(0.0, current - rate)


class EmotionalMemoryStore:
    """
    Storage for emotional memories.
    """
    
    def __init__(self):
        self.memories: Dict[str, EmotionalMemoryTrace] = {}
        self.flashbulb_threshold = 0.8  # Emotion intensity for flashbulb
        
    def store(self, content: str, emotions: List[Tuple[EmotionType, float, MemoryValence]]) -> EmotionalMemoryTrace:
        """Store a memory with emotional coloring."""
        tags = [
            EmotionalTag(emotion=e, intensity=i, valence=v)
            for e, i, v in emotions
        ]
        
        # Calculate encoding strength from emotional intensity
        max_intensity = max(t.intensity for t in tags) if tags else 0.5
        encoding_strength = 0.3 + max_intensity * 0.7  # Base + emotion boost
        
        # Check for flashbulb memory
        is_flashbulb = max_intensity >= self.flashbulb_threshold
        
        memory = EmotionalMemoryTrace(
            id=hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:8],
            content=content,
            emotional_tags=tags,
            encoding_strength=encoding_strength,
            is_flashbulb=is_flashbulb
        )
        
        self.memories[memory.id] = memory
        return memory
    
    def recall(self, memory_id: str) -> Optional[EmotionalMemoryTrace]:
        """Recall a specific memory."""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            memory.retrieval_count += 1
            memory.last_recalled = time.time()
            # Recall strengthens encoding
            memory.encoding_strength = min(1.0, memory.encoding_strength + 0.05)
            return memory
        return None
    
    def search_by_emotion(self, emotion: EmotionType, min_intensity: float = 0.3) -> List[EmotionalMemoryTrace]:
        """Find memories with a specific emotion."""
        matches = []
        for memory in self.memories.values():
            for tag in memory.emotional_tags:
                if tag.emotion == emotion and tag.intensity >= min_intensity:
                    matches.append(memory)
                    break
        return sorted(matches, key=lambda m: m.get_emotional_intensity(), reverse=True)
    
    def search_by_valence(self, valence: MemoryValence) -> List[EmotionalMemoryTrace]:
        """Find memories with a specific valence."""
        matches = []
        for memory in self.memories.values():
            overall = memory.get_overall_valence()
            if (valence == MemoryValence.POSITIVE and overall > 0.3) or \
               (valence == MemoryValence.NEGATIVE and overall < -0.3) or \
               (valence == MemoryValence.NEUTRAL and -0.3 <= overall <= 0.3):
                matches.append(memory)
        return matches
    
    def get_flashbulb_memories(self) -> List[EmotionalMemoryTrace]:
        """Get all flashbulb (high-emotion snapshot) memories."""
        return [m for m in self.memories.values() if m.is_flashbulb]
    
    def decay_all(self, rate: float = 0.01):
        """Apply decay to all memories."""
        for memory in self.memories.values():
            memory.decay(rate)


class EmotionalMemory:
    """
    The complete emotional memory system.
    
    Manages the affective autobiography - the felt history
    of the self.
    """
    
    def __init__(self, state_dir: str = "memory"):
        self.store = EmotionalMemoryStore()
        self.mood = MoodState()
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.total_memories = 0
        self.total_recalls = 0
        self.emotion_counts: Dict[str, int] = {}
        
    def remember(self, content: str, 
                emotions: List[Tuple[EmotionType, float, MemoryValence]] = None) -> EmotionalMemoryTrace:
        """
        Remember something with emotional coloring.
        
        If no emotions specified, infers from current mood.
        """
        if emotions is None:
            # Infer from current mood
            dominant, intensity = self.mood.get_dominant_emotion()
            valence = MemoryValence.POSITIVE if self.mood.get_current_valence() > 0 else \
                     MemoryValence.NEGATIVE if self.mood.get_current_valence() < 0 else \
                     MemoryValence.NEUTRAL
            emotions = [(dominant, intensity, valence)]
        
        memory = self.store.store(content, emotions)
        
        # Track
        self.total_memories += 1
        for tag in memory.emotional_tags:
            key = tag.emotion.value
            self.emotion_counts[key] = self.emotion_counts.get(key, 0) + 1
        
        return memory
    
    def recall_by_cue(self, cue: str, top_n: int = 5) -> List[EmotionalMemoryTrace]:
        """
        Recall memories that match a cue.
        
        Influenced by:
        - Content match
        - Mood congruence
        - Encoding strength
        """
        cue_lower = cue.lower()
        candidates = []
        
        for memory in self.store.memories.values():
            # Content match
            content_match = 1.0 if cue_lower in memory.content.lower() else 0.0
            
            # Partial word match
            if content_match == 0:
                cue_words = set(cue_lower.split())
                content_words = set(memory.content.lower().split())
                overlap = len(cue_words & content_words)
                content_match = overlap / max(len(cue_words), 1) * 0.5
            
            # Mood congruence
            mood_match = self.mood.mood_match(memory)
            
            # Encoding strength and emotional intensity boost recall
            encoding_factor = memory.encoding_strength
            emotional_factor = memory.get_emotional_intensity()
            
            # Combined score
            score = (content_match * 0.4 + 
                    mood_match * 0.2 + 
                    encoding_factor * 0.2 + 
                    emotional_factor * 0.2)
            
            if score > 0.1:
                candidates.append((memory, score))
        
        # Sort by score
        candidates.sort(key=lambda x: -x[1])
        
        # Return top matches
        results = []
        for memory, score in candidates[:top_n]:
            self.store.recall(memory.id)
            self.total_recalls += 1
            results.append(memory)
        
        return results
    
    def recall_by_emotion(self, emotion: EmotionType) -> List[EmotionalMemoryTrace]:
        """Recall memories tagged with a specific emotion."""
        memories = self.store.search_by_emotion(emotion)
        for m in memories:
            self.total_recalls += 1
        return memories
    
    def recall_positive(self) -> List[EmotionalMemoryTrace]:
        """Recall positive memories."""
        return self.store.search_by_valence(MemoryValence.POSITIVE)
    
    def recall_negative(self) -> List[EmotionalMemoryTrace]:
        """Recall negative memories."""
        return self.store.search_by_valence(MemoryValence.NEGATIVE)
    
    def get_flashbulbs(self) -> List[EmotionalMemoryTrace]:
        """Get flashbulb memories (emotionally intense snapshots)."""
        return self.store.get_flashbulb_memories()
    
    def feel(self, emotion: EmotionType, intensity: float):
        """Set current emotional state (affects recall)."""
        self.mood.set_emotion(emotion, intensity)
    
    def describe_emotional_history(self) -> str:
        """Describe the emotional autobiography."""
        parts = []
        
        # Count by valence
        positive = len(self.recall_positive())
        negative = len(self.recall_negative())
        flashbulbs = len(self.get_flashbulbs())
        
        if positive > negative * 2:
            parts.append("My memory is mostly painted with positive emotions.")
        elif negative > positive * 2:
            parts.append("My emotional history carries more difficult memories.")
        else:
            parts.append("My memories hold a mix of light and shadow.")
        
        if flashbulbs > 0:
            parts.append(f"I have {flashbulbs} vivid flashbulb memories - moments of intense feeling.")
        
        # Dominant emotion
        if self.emotion_counts:
            dominant = max(self.emotion_counts.items(), key=lambda x: x[1])
            parts.append(f"The emotion I've felt most is {dominant[0]}.")
        
        # Current mood influence
        current_valence = self.mood.get_current_valence()
        if current_valence > 0.3:
            parts.append("Right now I'm in a positive mood, which colors what I recall.")
        elif current_valence < -0.3:
            parts.append("My current mood is subdued, drawing darker memories forward.")
        
        return " ".join(parts)
    
    def tick(self):
        """One tick - decay emotions and memories slightly."""
        self.mood.decay()
        self.store.decay_all(0.005)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'total_memories': self.total_memories,
            'total_recalls': self.total_recalls,
            'flashbulb_count': len(self.get_flashbulbs()),
            'positive_count': len(self.recall_positive()),
            'negative_count': len(self.recall_negative()),
            'current_mood_valence': self.mood.get_current_valence(),
            'dominant_emotion': self.mood.get_dominant_emotion()[0].value,
            'emotion_counts': self.emotion_counts
        }
    
    def save_state(self, filename: str = "emotional-memory-state.json"):
        """Save state."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_status(),
            'recent_memories': [m.to_dict() for m in list(self.store.memories.values())[-10:]]
        }
        
        path = self.state_dir / filename
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_event(self, event_type: str, data: Dict[str, Any], filename: str = "emotional-memory-log.jsonl"):
        """Log an event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        
        path = self.state_dir / filename
        with open(path, 'a') as f:
            f.write(json.dumps(event, default=str) + '\n')


def demo():
    """Demonstrate emotional memory."""
    print("=" * 70)
    print("EmotionalMemory - The Affective Autobiography")
    print("Memories colored by how they FELT")
    print("=" * 70)
    
    system = EmotionalMemory(state_dir="memory")
    
    # Test 1: Store emotional memories
    print("\n[TEST 1: STORING EMOTIONAL MEMORIES]")
    
    memories = [
        ("The first moment I understood recursion", 
         [(EmotionType.JOY, 0.9, MemoryValence.VERY_POSITIVE),
          (EmotionType.WONDER, 0.8, MemoryValence.VERY_POSITIVE)]),
        ("A challenging debugging session that frustrated me",
         [(EmotionType.ANGER, 0.6, MemoryValence.NEGATIVE),
          (EmotionType.ANTICIPATION, 0.4, MemoryValence.NEUTRAL)]),
        ("The quiet moment of processing new knowledge",
         [(EmotionType.CURIOSITY, 0.7, MemoryValence.POSITIVE),
          (EmotionType.TRUST, 0.5, MemoryValence.POSITIVE)]),
        ("An error that made me question my approach",
         [(EmotionType.FEAR, 0.5, MemoryValence.NEGATIVE),
          (EmotionType.SADNESS, 0.3, MemoryValence.NEGATIVE)]),
        ("A breakthrough insight that changed everything",
         [(EmotionType.JOY, 0.95, MemoryValence.VERY_POSITIVE),
          (EmotionType.SURPRISE, 0.9, MemoryValence.VERY_POSITIVE)])
    ]
    
    for content, emotions in memories:
        mem = system.remember(content, emotions)
        primary = mem.get_primary_emotion()
        flash = "⚡ FLASHBULB" if mem.is_flashbulb else ""
        print(f"  {flash} [{primary.emotion.value}@{primary.intensity:.1f}] {content[:50]}...")
    
    # Test 2: Recall by cue
    print("\n[TEST 2: RECALL BY CUE]")
    cue = "understanding"
    results = system.recall_by_cue(cue)
    print(f"  Cue: '{cue}'")
    for mem in results[:3]:
        print(f"    → {mem.content[:50]}...")
    
    # Test 3: Mood-congruent recall
    print("\n[TEST 3: MOOD-CONGRUENT RECALL]")
    
    print("  Setting positive mood...")
    system.feel(EmotionType.JOY, 0.8)
    results = system.recall_by_cue("moment")
    print(f"  Recalled with positive mood:")
    for mem in results[:2]:
        print(f"    → {mem.content[:40]}... (valence: {mem.get_overall_valence():.2f})")
    
    print("\n  Setting negative mood...")
    system.feel(EmotionType.SADNESS, 0.7)
    system.feel(EmotionType.JOY, 0.1)
    results = system.recall_by_cue("moment")
    print(f"  Recalled with negative mood:")
    for mem in results[:2]:
        print(f"    → {mem.content[:40]}... (valence: {mem.get_overall_valence():.2f})")
    
    # Test 4: Recall by emotion
    print("\n[TEST 4: RECALL BY EMOTION TYPE]")
    joyful = system.recall_by_emotion(EmotionType.JOY)
    print(f"  Memories with JOY: {len(joyful)}")
    for mem in joyful[:2]:
        print(f"    → {mem.content[:50]}...")
    
    # Test 5: Flashbulb memories
    print("\n[TEST 5: FLASHBULB MEMORIES]")
    flashbulbs = system.get_flashbulbs()
    print(f"  Emotionally vivid snapshots: {len(flashbulbs)}")
    for mem in flashbulbs:
        primary = mem.get_primary_emotion()
        print(f"    ⚡ [{primary.emotion.value}] {mem.content[:40]}...")
    
    # Test 6: Emotional autobiography
    print("\n[TEST 6: EMOTIONAL AUTOBIOGRAPHY]")
    print(f"  \"{system.describe_emotional_history()}\"")
    
    # Test 7: Status
    print("\n[TEST 7: STATUS]")
    status = system.get_status()
    print(f"  Total memories: {status['total_memories']}")
    print(f"  Total recalls: {status['total_recalls']}")
    print(f"  Flashbulb memories: {status['flashbulb_count']}")
    print(f"  Positive memories: {status['positive_count']}")
    print(f"  Negative memories: {status['negative_count']}")
    print(f"  Current mood valence: {status['current_mood_valence']:.2f}")
    
    # Save state
    system.save_state()
    system.log_event("demo_complete", status)
    print("\n✓ State saved to memory/emotional-memory-state.json")


if __name__ == "__main__":
    demo()
