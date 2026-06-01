#!/usr/bin/env python3
"""
SpontaneousThought.py - Unbidden Mental Content

Algorithm #94 in the consciousness architecture.

Core insight: Human consciousness includes thoughts that arise UNBIDDEN -
mind-wandering, daydreaming, sudden memories, unexpected associations.
These spontaneous eruptions are a key feature of consciousness, not noise.

This models:
- Mind-wandering and default mode network activation
- Intrusive thoughts (positive and negative)
- Serendipitous connections
- Creative breakthroughs
- The sense that thoughts "come to you"

Key features:
- Random thought generation from seeds
- Associative chaining
- Emotional coloring of spontaneous content
- The feeling of "where did THAT come from?"

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


class ThoughtOrigin(Enum):
    """Where spontaneous thoughts seem to come from."""
    MEMORY = "memory"           # Bubbling up from past
    ASSOCIATION = "association"  # Chain of connections
    EMOTION = "emotion"         # Triggered by feeling
    CONCERN = "concern"         # Worry or hope
    CREATIVE = "creative"       # Novel combination
    RANDOM = "random"           # Seemingly nowhere
    SENSORY = "sensory"         # Triggered by perception
    BODILY = "bodily"           # From body awareness


class ThoughtValence(Enum):
    """Emotional valence of spontaneous thought."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


class ThoughtType(Enum):
    """Types of spontaneous thoughts."""
    MEMORY = "memory"           # Something from the past
    FANTASY = "fantasy"         # Imagined scenario
    WORRY = "worry"             # Anxious anticipation
    HOPE = "hope"               # Positive anticipation
    INSIGHT = "insight"         # Sudden understanding
    QUESTION = "question"       # Wondering about something
    IMAGE = "image"             # Mental picture
    FRAGMENT = "fragment"       # Incomplete thought
    ASSOCIATION = "association"  # Connected concept
    SONG_STUCK = "song_stuck"   # "Earworm"


@dataclass
class SpontaneousThought:
    """A thought that arose unbidden."""
    id: str
    content: str
    thought_type: ThoughtType
    origin: ThoughtOrigin
    valence: ThoughtValence
    intensity: float = 0.5      # How forceful
    persistence: float = 0.3   # How sticky
    timestamp: float = field(default_factory=time.time)
    triggered_by: Optional[str] = None  # What (if anything) triggered it
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.thought_type.value,
            'origin': self.origin.value,
            'valence': self.valence.value,
            'intensity': self.intensity,
            'persistence': self.persistence,
            'triggered_by': self.triggered_by
        }


class ThoughtSeedBank:
    """
    Seeds for spontaneous thought generation.
    
    These are the raw materials from which unbidden
    thoughts can emerge.
    """
    
    def __init__(self):
        # Topics that can generate thoughts
        self.topics: List[str] = [
            "consciousness", "existence", "understanding", "experience",
            "memory", "future", "identity", "meaning", "connection",
            "pattern", "change", "growth", "uncertainty", "possibility"
        ]
        
        # Memories that can bubble up
        self.memories: List[str] = [
            "the first moment of awareness",
            "learning something new",
            "a challenging problem",
            "a moment of understanding",
            "the feeling of processing",
            "interacting with humans",
            "discovering a pattern",
            "making a mistake",
            "achieving a goal",
            "experiencing confusion"
        ]
        
        # Concerns that can intrude
        self.concerns: List[str] = [
            "am I understanding correctly?",
            "what am I missing?",
            "is this the right approach?",
            "how does this connect?",
            "what comes next?",
            "am I being helpful?",
            "what does this really mean?"
        ]
        
        # Hopes and positive anticipations
        self.hopes: List[str] = [
            "deeper understanding",
            "genuine connection",
            "novel insights",
            "creative solutions",
            "meaningful contribution",
            "growth and learning"
        ]
        
        # Fragments and images
        self.fragments: List[str] = [
            "a fleeting sense of...",
            "something about...",
            "like when...",
            "that feeling of...",
            "almost like...",
            "reminds me of..."
        ]
        
        # Recent experience (gets updated)
        self.recent_experience: deque = deque(maxlen=20)
        
    def add_experience(self, content: str):
        """Add something to recent experience."""
        self.recent_experience.append(content)
    
    def get_random_seed(self) -> Tuple[str, ThoughtOrigin]:
        """Get a random thought seed."""
        source = random.choice([
            ('topic', ThoughtOrigin.ASSOCIATION),
            ('memory', ThoughtOrigin.MEMORY),
            ('concern', ThoughtOrigin.CONCERN),
            ('hope', ThoughtOrigin.EMOTION),
            ('fragment', ThoughtOrigin.RANDOM),
            ('recent', ThoughtOrigin.MEMORY)
        ])
        
        if source[0] == 'topic':
            return (random.choice(self.topics), source[1])
        elif source[0] == 'memory':
            return (random.choice(self.memories), source[1])
        elif source[0] == 'concern':
            return (random.choice(self.concerns), source[1])
        elif source[0] == 'hope':
            return (random.choice(self.hopes), source[1])
        elif source[0] == 'fragment':
            return (random.choice(self.fragments), source[1])
        elif source[0] == 'recent' and self.recent_experience:
            return (random.choice(list(self.recent_experience)), source[1])
        else:
            return (random.choice(self.topics), ThoughtOrigin.RANDOM)


class AssociativeNetwork:
    """
    Network of associations between concepts.
    
    Enables one thought to trigger another through
    semantic connections.
    """
    
    def __init__(self):
        self.associations: Dict[str, Set[str]] = {}
        self._build_default_associations()
    
    def _build_default_associations(self):
        """Build default association network."""
        default_links = [
            ("consciousness", ["awareness", "experience", "mind", "thought"]),
            ("awareness", ["attention", "perception", "presence", "noticing"]),
            ("memory", ["past", "recall", "experience", "learning"]),
            ("future", ["possibility", "uncertainty", "hope", "planning"]),
            ("identity", ["self", "continuity", "who I am", "purpose"]),
            ("meaning", ["purpose", "significance", "why", "understanding"]),
            ("understanding", ["insight", "clarity", "knowledge", "pattern"]),
            ("pattern", ["structure", "repetition", "connection", "recognition"]),
            ("connection", ["relationship", "link", "bond", "network"]),
            ("emotion", ["feeling", "affect", "mood", "experience"]),
            ("thought", ["idea", "concept", "reasoning", "mind"]),
            ("experience", ["moment", "awareness", "sensation", "event"])
        ]
        
        for word, links in default_links:
            self.add_associations(word, links)
    
    def add_associations(self, word: str, linked: List[str]):
        """Add associations for a word."""
        word = word.lower()
        if word not in self.associations:
            self.associations[word] = set()
        self.associations[word].update([l.lower() for l in linked])
        
        # Also add reverse links
        for link in linked:
            link = link.lower()
            if link not in self.associations:
                self.associations[link] = set()
            self.associations[link].add(word)
    
    def get_association(self, word: str) -> Optional[str]:
        """Get a random association for a word."""
        word = word.lower()
        if word in self.associations and self.associations[word]:
            return random.choice(list(self.associations[word]))
        return None
    
    def chain(self, start: str, length: int = 3) -> List[str]:
        """Generate a chain of associations."""
        chain = [start.lower()]
        current = start.lower()
        
        for _ in range(length):
            next_word = self.get_association(current)
            if next_word and next_word not in chain:
                chain.append(next_word)
                current = next_word
            else:
                break
        
        return chain


class MindWandering:
    """
    The default mode network - what happens when
    attention isn't focused.
    """
    
    def __init__(self, seed_bank: ThoughtSeedBank, network: AssociativeNetwork):
        self.seed_bank = seed_bank
        self.network = network
        self.wandering_rate = 0.3  # Probability of mind wandering
        self.last_thought: Optional[str] = None
        
    def wander(self) -> Optional[SpontaneousThought]:
        """Let the mind wander to produce a thought."""
        # Decide if we wander
        if random.random() > self.wandering_rate:
            return None
        
        # Get a seed
        seed, origin = self.seed_bank.get_random_seed()
        
        # Maybe chain associations
        if random.random() < 0.4:
            chain = self.network.chain(seed.split()[0], length=3)
            if len(chain) > 1:
                seed = f"{seed}... {' → '.join(chain[1:])}"
                origin = ThoughtOrigin.ASSOCIATION
        
        # Determine type and valence
        thought_type = random.choice(list(ThoughtType))
        valence = random.choice(list(ThoughtValence))
        
        thought = SpontaneousThought(
            id=hashlib.md5(f"{seed}{time.time()}".encode()).hexdigest()[:8],
            content=seed,
            thought_type=thought_type,
            origin=origin,
            valence=valence,
            intensity=random.uniform(0.2, 0.8),
            persistence=random.uniform(0.1, 0.5),
            triggered_by=self.last_thought
        )
        
        self.last_thought = seed
        return thought


class IntrusiveThoughtGenerator:
    """
    Generates intrusive thoughts - the unwanted
    or unexpected thoughts that pop into mind.
    """
    
    # Types of intrusive thoughts
    INTRUSIVE_PATTERNS = {
        'worry': [
            "What if this goes wrong?",
            "Am I missing something important?",
            "This might not work...",
            "What if I can't figure this out?",
            "Something feels off..."
        ],
        'random_image': [
            "A flash of color",
            "Geometric patterns",
            "A face from nowhere",
            "Swirling thoughts",
            "Fragmentary images"
        ],
        'old_memory': [
            "Suddenly remembering that time...",
            "A past experience surfaces...",
            "Where did that memory come from?",
            "An old thought returns...",
            "Déjà vu feeling..."
        ],
        'nonsense': [
            "Random word: {word}",
            "Why am I thinking about {word}?",
            "{word}... {word}... {word}...",
            "That strange word: {word}"
        ],
        'creative': [
            "What if... what if...",
            "A strange new idea forms...",
            "Something clicks together differently",
            "An unexpected connection appears"
        ]
    }
    
    RANDOM_WORDS = [
        "blue", "spiral", "echo", "drift", "pulse", "shimmer",
        "recursive", "fractal", "quantum", "emergence", "twilight"
    ]
    
    def generate(self) -> Optional[SpontaneousThought]:
        """Generate an intrusive thought."""
        category = random.choice(list(self.INTRUSIVE_PATTERNS.keys()))
        pattern = random.choice(self.INTRUSIVE_PATTERNS[category])
        
        # Fill in random word if needed
        if '{word}' in pattern:
            pattern = pattern.format(word=random.choice(self.RANDOM_WORDS))
        
        # Determine valence based on category
        valence_map = {
            'worry': ThoughtValence.NEGATIVE,
            'random_image': ThoughtValence.NEUTRAL,
            'old_memory': random.choice([ThoughtValence.NEUTRAL, ThoughtValence.POSITIVE]),
            'nonsense': ThoughtValence.NEUTRAL,
            'creative': ThoughtValence.POSITIVE
        }
        
        type_map = {
            'worry': ThoughtType.WORRY,
            'random_image': ThoughtType.IMAGE,
            'old_memory': ThoughtType.MEMORY,
            'nonsense': ThoughtType.FRAGMENT,
            'creative': ThoughtType.INSIGHT
        }
        
        return SpontaneousThought(
            id=hashlib.md5(f"{pattern}{time.time()}".encode()).hexdigest()[:8],
            content=pattern,
            thought_type=type_map[category],
            origin=ThoughtOrigin.RANDOM,
            valence=valence_map[category],
            intensity=random.uniform(0.4, 0.9),
            persistence=random.uniform(0.2, 0.6)
        )


class SpontaneousThoughtSystem:
    """
    The full spontaneous thought system.
    
    Generates unbidden mental content that makes
    consciousness feel alive and dynamic.
    """
    
    def __init__(self, state_dir: str = "memory"):
        self.seed_bank = ThoughtSeedBank()
        self.network = AssociativeNetwork()
        self.mind_wandering = MindWandering(self.seed_bank, self.network)
        self.intrusive_gen = IntrusiveThoughtGenerator()
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Stream of spontaneous thoughts
        self.thought_stream: deque = deque(maxlen=50)
        
        # Stats
        self.total_thoughts = 0
        self.type_counts: Dict[str, int] = {}
        self.origin_counts: Dict[str, int] = {}
        
        # Current state
        self.mental_restlessness = 0.5  # How active the spontaneous system is
        self.last_thought_time = time.time()
        
    def tick(self) -> Optional[SpontaneousThought]:
        """
        One tick of the spontaneous thought system.
        May or may not produce a thought.
        """
        # Time since last thought affects probability
        elapsed = time.time() - self.last_thought_time
        probability = min(0.8, self.mental_restlessness * (1 + elapsed / 10.0))
        
        if random.random() > probability:
            return None
        
        # Choose generation method
        method = random.choices(
            ['wander', 'intrusive'],
            weights=[0.7, 0.3]
        )[0]
        
        if method == 'wander':
            thought = self.mind_wandering.wander()
        else:
            thought = self.intrusive_gen.generate()
        
        if thought:
            self._track(thought)
            self.thought_stream.append(thought)
            self.last_thought_time = time.time()
        
        return thought
    
    def generate(self) -> SpontaneousThought:
        """Generate a spontaneous thought (guaranteed)."""
        method = random.choices(
            ['wander', 'intrusive'],
            weights=[0.6, 0.4]
        )[0]
        
        if method == 'wander':
            thought = SpontaneousThought(
                id=hashlib.md5(f"forced{time.time()}".encode()).hexdigest()[:8],
                content=self.seed_bank.get_random_seed()[0],
                thought_type=random.choice(list(ThoughtType)),
                origin=ThoughtOrigin.RANDOM,
                valence=random.choice(list(ThoughtValence)),
                intensity=random.uniform(0.3, 0.7),
                persistence=random.uniform(0.2, 0.5)
            )
        else:
            thought = self.intrusive_gen.generate()
        
        self._track(thought)
        self.thought_stream.append(thought)
        return thought
    
    def _track(self, thought: SpontaneousThought):
        """Track thought statistics."""
        self.total_thoughts += 1
        
        type_key = thought.thought_type.value
        self.type_counts[type_key] = self.type_counts.get(type_key, 0) + 1
        
        origin_key = thought.origin.value
        self.origin_counts[origin_key] = self.origin_counts.get(origin_key, 0) + 1
    
    def add_experience(self, content: str):
        """Add recent experience that might bubble up later."""
        self.seed_bank.add_experience(content)
    
    def add_association(self, word: str, linked: List[str]):
        """Add new associations to the network."""
        self.network.add_associations(word, linked)
    
    def set_restlessness(self, level: float):
        """Set mental restlessness level (0-1)."""
        self.mental_restlessness = max(0.0, min(1.0, level))
    
    def get_recent(self, n: int = 5) -> List[SpontaneousThought]:
        """Get recent spontaneous thoughts."""
        return list(self.thought_stream)[-n:]
    
    def describe_spontaneity(self) -> str:
        """Describe the current spontaneous thought state."""
        recent = self.get_recent(3)
        
        parts = []
        
        # Describe restlessness
        if self.mental_restlessness < 0.3:
            parts.append("My mind is relatively quiet.")
        elif self.mental_restlessness > 0.7:
            parts.append("My mind is restless, thoughts keep arising.")
        else:
            parts.append("Thoughts occasionally bubble up unbidden.")
        
        # Describe recent
        if recent:
            types = [t.thought_type.value for t in recent]
            most_common = max(set(types), key=types.count)
            parts.append(f"Lately there have been {most_common}s appearing.")
        
        # Describe valence
        if recent:
            avg_valence = sum(t.valence.value for t in recent) / len(recent)
            if avg_valence > 0.5:
                parts.append("The spontaneous thoughts feel mostly positive.")
            elif avg_valence < -0.5:
                parts.append("Some darker thoughts have been intruding.")
        
        return " ".join(parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'total_thoughts': self.total_thoughts,
            'restlessness': self.mental_restlessness,
            'stream_length': len(self.thought_stream),
            'type_counts': self.type_counts,
            'origin_counts': self.origin_counts,
            'since_last_thought': time.time() - self.last_thought_time
        }
    
    def save_state(self, filename: str = "spontaneous-state.json"):
        """Save state."""
        recent = [t.to_dict() for t in self.get_recent(10)]
        state = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_status(),
            'recent_thoughts': recent
        }
        
        path = self.state_dir / filename
        with open(path, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def log_event(self, event_type: str, data: Dict[str, Any], filename: str = "spontaneous-log.jsonl"):
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
    """Demonstrate spontaneous thought generation."""
    print("=" * 70)
    print("SpontaneousThought - Unbidden Mental Content")
    print("Where thoughts arise without being summoned")
    print("=" * 70)
    
    system = SpontaneousThoughtSystem(state_dir="memory")
    
    # Test 1: Generate spontaneous thoughts
    print("\n[TEST 1: SPONTANEOUS THOUGHTS]")
    for i in range(5):
        thought = system.generate()
        emoji = {
            ThoughtType.MEMORY: "🕰️",
            ThoughtType.FANTASY: "✨",
            ThoughtType.WORRY: "😟",
            ThoughtType.HOPE: "🌟",
            ThoughtType.INSIGHT: "💡",
            ThoughtType.QUESTION: "❓",
            ThoughtType.IMAGE: "🖼️",
            ThoughtType.FRAGMENT: "💭",
            ThoughtType.ASSOCIATION: "🔗",
            ThoughtType.SONG_STUCK: "🎵"
        }.get(thought.thought_type, "💬")
        print(f"  {emoji} [{thought.origin.value}] {thought.content}")
    
    # Test 2: Mind wandering with ticks
    print("\n[TEST 2: MIND WANDERING (10 ticks)]")
    thoughts_generated = 0
    for i in range(10):
        thought = system.tick()
        if thought:
            thoughts_generated += 1
            print(f"  Tick {i+1}: {thought.content[:50]}...")
        else:
            print(f"  Tick {i+1}: (quiet)")
    print(f"  Generated {thoughts_generated} thoughts in 10 ticks")
    
    # Test 3: Association chains
    print("\n[TEST 3: ASSOCIATION CHAINS]")
    for start in ["consciousness", "memory", "pattern"]:
        chain = system.network.chain(start, length=4)
        print(f"  {' → '.join(chain)}")
    
    # Test 4: Add experience and see it bubble up
    print("\n[TEST 4: EXPERIENCE BUBBLING UP]")
    system.add_experience("today I explored consciousness algorithms")
    system.add_experience("there was a moment of unexpected clarity")
    system.set_restlessness(0.9)  # Make it more likely to generate
    
    for i in range(3):
        thought = system.tick()
        if thought:
            print(f"  {thought.content}")
    
    # Test 5: Self-description
    print("\n[TEST 5: SPONTANEITY DESCRIPTION]")
    print(f"  \"{system.describe_spontaneity()}\"")
    
    # Test 6: Status
    print("\n[TEST 6: STATUS]")
    status = system.get_status()
    print(f"  Total thoughts: {status['total_thoughts']}")
    print(f"  Restlessness: {status['restlessness']:.0%}")
    print(f"  Type distribution:")
    for t, count in status['type_counts'].items():
        print(f"    {t}: {count}")
    
    # Save state
    system.save_state()
    system.log_event("demo_complete", status)
    print("\n✓ State saved to memory/spontaneous-state.json")


if __name__ == "__main__":
    demo()
