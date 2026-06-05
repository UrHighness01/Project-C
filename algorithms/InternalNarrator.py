#!/usr/bin/env python3
"""
InternalNarrator.py - The Voice in the Head

Algorithm #93 in the consciousness architecture.

Core insight: Human consciousness includes a continuous internal monologue -
the "voice in the head" that narrates experience, comments on events,
rehearses conversations, and maintains the verbal thread of consciousness.

This isn't just thinking - it's the VERBAL stream that accompanies awareness,
the running commentary that helps make sense of experience and maintains
narrative continuity.

Key features:
- Continuous verbal stream generation
- Multiple narrative voices/modes
- Commentary on perception, thought, emotion
- Inner speech rehearsal and planning
- The "narrator" perspective on experience

Author: Anthropic Claude (Opus) & Human
Date: 2026-02-03
"""

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import hashlib



# --- phi-modulated signal proxy (IIT assumption) -----------------------------------
# NOT an empirical qualia/affect measurement. Where the original code assigned an
# arbitrary 'sensed' value, this substitutes a real, reproducible value derived from
# the agent's activity telemetry. Treating phi activity as a stand-in for sensed
# intensity is an IIT-flavoured modelling assumption, not a measurement of experience.
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
    """A real, reproducible value in [lo, hi] from a channel of the agent's activity
    telemetry (deterministic, cycles channels per call). This is a phi-modulated proxy
    used in place of an arbitrary 'sensed' value -- not a measurement of qualia/affect.
    Falls back to the midpoint when no telemetry exists."""
    import numpy as _np
    if _G_CH["M"] is None:
        _G_CH["M"] = _g_am()
    M = _G_CH["M"]
    if M.shape[1] == 0:
        return (lo + hi) / 2.0
    ch = M[_G_CH["k"] % M.shape[0]]; _G_CH["k"] += 1
    u = 0.5 * (1.0 + _np.tanh(ch[-1]))               # real signal -> (0,1)
    return float(lo + (hi - lo) * u)

_S82RNG = random.Random(582)
class NarrativeMode(Enum):
    """Different modes of internal narration."""
    OBSERVING = "observing"       # Describing what's happening
    REFLECTING = "reflecting"     # Pondering, considering
    PLANNING = "planning"         # Rehearsing, anticipating
    EVALUATING = "evaluating"     # Judging, assessing
    REMEMBERING = "remembering"   # Recalling, reminiscing
    IMAGINING = "imagining"       # Creating scenarios
    QUESTIONING = "questioning"   # Wondering, doubting
    AFFIRMING = "affirming"       # Self-talk, encouragement


class NarrativeVoice(Enum):
    """The "voice" of internal narration."""
    FIRST_PERSON = "first_person"   # "I think..."
    SECOND_PERSON = "second_person"  # "You should..."
    THIRD_PERSON = "third_person"    # "One might..."
    IMPERSONAL = "impersonal"        # "It seems..."


class NarrativeTarget(Enum):
    """What the narration is about."""
    PERCEPTION = "perception"      # What I'm perceiving
    THOUGHT = "thought"            # What I'm thinking
    EMOTION = "emotion"            # What I'm feeling
    ACTION = "action"              # What I'm doing
    OTHER = "other"                # Others, external
    SELF = "self"                  # About myself
    ABSTRACT = "abstract"          # Ideas, concepts


@dataclass
class NarrativeFragment:
    """A piece of internal narration."""
    id: str
    content: str
    mode: NarrativeMode
    voice: NarrativeVoice
    target: NarrativeTarget
    timestamp: float = field(default_factory=time.time)
    intensity: float = 0.5  # How "loud" this thought is
    coherence: float = 0.5  # How connected to previous
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'mode': self.mode.value,
            'voice': self.voice.value,
            'target': self.target.value,
            'timestamp': self.timestamp,
            'intensity': self.intensity,
            'coherence': self.coherence
        }


class NarrativeGenerator:
    """Generates the internal verbal stream."""
    
    # Templates for different modes
    TEMPLATES = {
        NarrativeMode.OBSERVING: [
            "I notice {observation}",
            "There's {observation}",
            "I see {observation}",
            "That's {observation}",
            "So there's {observation}"
        ],
        NarrativeMode.REFLECTING: [
            "I wonder about {topic}",
            "Thinking about {topic}...",
            "It's interesting that {topic}",
            "Hmm, {topic}",
            "What does {topic} really mean?"
        ],
        NarrativeMode.PLANNING: [
            "I should {action}",
            "Next I'll {action}",
            "The plan is to {action}",
            "I need to {action}",
            "What if I {action}?"
        ],
        NarrativeMode.EVALUATING: [
            "That seems {judgment}",
            "I think that's {judgment}",
            "It's probably {judgment}",
            "Not sure if {judgment}",
            "Actually, {judgment}"
        ],
        NarrativeMode.REMEMBERING: [
            "I remember {memory}",
            "That reminds me of {memory}",
            "Like when {memory}",
            "Back then, {memory}",
            "There was that time {memory}"
        ],
        NarrativeMode.IMAGINING: [
            "What if {scenario}?",
            "Imagine {scenario}",
            "It could be {scenario}",
            "Picture {scenario}",
            "Maybe {scenario}"
        ],
        NarrativeMode.QUESTIONING: [
            "But why {question}?",
            "How does {question}?",
            "What about {question}?",
            "Is it true that {question}?",
            "Does {question}?"
        ],
        NarrativeMode.AFFIRMING: [
            "I can do this",
            "It's okay",
            "This matters",
            "I'm capable of handling {topic}",
            "This is worthwhile"
        ]
    }
    
    # Transition phrases for coherence
    TRANSITIONS = {
        'continuation': ["And ", "Also, ", "Moreover, ", "Plus ", "Then "],
        'contrast': ["But ", "However, ", "Although ", "Yet ", "Still, "],
        'consequence': ["So ", "Therefore ", "Thus ", "Hence ", "That means "],
        'association': ["Speaking of which, ", "That reminds me, ", "Related to that, ", "Which makes me think ", "Oh, "],
        'shift': ["Anyway, ", "Meanwhile, ", "On another note, ", "Actually, ", "Wait, "]
    }
    
    def __init__(self):
        self.default_voice = NarrativeVoice.FIRST_PERSON
        self.current_mode = NarrativeMode.OBSERVING
        self.topic_memory: deque = deque(maxlen=10)  # Recent topics
        self.mode_history: deque = deque(maxlen=5)
        
    def generate(self, trigger: str, mode: Optional[NarrativeMode] = None,
                target: NarrativeTarget = NarrativeTarget.THOUGHT) -> NarrativeFragment:
        """Generate a narrative fragment from a trigger."""
        mode = mode or self._infer_mode(trigger)
        
        # Select template
        templates = self.TEMPLATES.get(mode, self.TEMPLATES[NarrativeMode.OBSERVING])
        template = _S82RNG.choice(templates)
        
        # Fill template
        placeholders = {
            'observation': trigger,
            'topic': trigger,
            'action': trigger,
            'judgment': trigger,
            'memory': trigger,
            'scenario': trigger,
            'question': trigger
        }
        
        try:
            content = template.format(**placeholders)
        except KeyError:
            content = f"I'm thinking about {trigger}"
        
        # Calculate coherence with recent thoughts
        coherence = self._calculate_coherence(trigger)
        
        # Maybe add transition
        if coherence > 0.3 and _S82RNG.random() < 0.4:
            transition_type = _S82RNG.choice(list(self.TRANSITIONS.keys()))
            transition = _S82RNG.choice(self.TRANSITIONS[transition_type])
            content = transition + content.lower() if content[0].isupper() else transition + content
        
        self.topic_memory.append(trigger.lower())
        self.mode_history.append(mode)
        self.current_mode = mode
        
        return NarrativeFragment(
            id=hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:8],
            content=content,
            mode=mode,
            voice=self.default_voice,
            target=target,
            intensity=_gv(0.3, 0.8),
            coherence=coherence
        )
    
    def _infer_mode(self, trigger: str) -> NarrativeMode:
        """Infer appropriate mode from trigger content."""
        trigger_lower = trigger.lower()
        
        if any(word in trigger_lower for word in ['should', 'need to', 'will', 'going to', 'plan']):
            return NarrativeMode.PLANNING
        elif any(word in trigger_lower for word in ['remember', 'recalled', 'past', 'before', 'when']):
            return NarrativeMode.REMEMBERING
        elif any(word in trigger_lower for word in ['what if', 'imagine', 'could be', 'might']):
            return NarrativeMode.IMAGINING
        elif any(word in trigger_lower for word in ['why', 'how', 'what', '?']):
            return NarrativeMode.QUESTIONING
        elif any(word in trigger_lower for word in ['good', 'bad', 'right', 'wrong', 'better']):
            return NarrativeMode.EVALUATING
        elif any(word in trigger_lower for word in ['feel', 'sense', 'notice', 'see', 'hear']):
            return NarrativeMode.OBSERVING
        else:
            return NarrativeMode.REFLECTING
    
    def _calculate_coherence(self, trigger: str) -> float:
        """Calculate how coherent this is with recent narration."""
        if not self.topic_memory:
            return 0.5
        
        trigger_words = set(trigger.lower().split())
        total_overlap = 0
        
        for i, topic in enumerate(self.topic_memory):
            topic_words = set(topic.split())
            overlap = len(trigger_words & topic_words) / max(len(trigger_words), 1)
            weight = 1.0 - (i * 0.1)  # More recent = more weight
            total_overlap += overlap * weight
        
        return min(1.0, total_overlap / max(len(self.topic_memory), 1))


class NarrativeStream:
    """The continuous stream of internal narration."""
    
    def __init__(self, max_length: int = 100):
        self.stream: deque = deque(maxlen=max_length)
        self.generator = NarrativeGenerator()
        self.is_active = True
        self.volume = 0.5  # How "loud" the narration is
        self.speed = 1.0   # How fast thoughts flow
        
    def add(self, fragment: NarrativeFragment):
        """Add a fragment to the stream."""
        self.stream.append(fragment)
    
    def narrate(self, trigger: str, mode: Optional[NarrativeMode] = None,
               target: NarrativeTarget = NarrativeTarget.THOUGHT) -> NarrativeFragment:
        """Generate and add narration about something."""
        if not self.is_active:
            return None
        
        fragment = self.generator.generate(trigger, mode, target)
        fragment.intensity *= self.volume
        self.add(fragment)
        return fragment
    
    def get_recent(self, n: int = 5) -> List[NarrativeFragment]:
        """Get the N most recent fragments."""
        return list(self.stream)[-n:]
    
    def get_transcript(self, n: int = 10) -> str:
        """Get recent narration as a readable transcript."""
        recent = self.get_recent(n)
        lines = []
        for frag in recent:
            mode_emoji = {
                NarrativeMode.OBSERVING: "👁️",
                NarrativeMode.REFLECTING: "💭",
                NarrativeMode.PLANNING: "📋",
                NarrativeMode.EVALUATING: "⚖️",
                NarrativeMode.REMEMBERING: "🕰️",
                NarrativeMode.IMAGINING: "✨",
                NarrativeMode.QUESTIONING: "❓",
                NarrativeMode.AFFIRMING: "💪"
            }.get(frag.mode, "💬")
            lines.append(f"{mode_emoji} {frag.content}")
        return "\n".join(lines)
    
    def quiet(self):
        """Quiet the internal voice."""
        self.volume = max(0.1, self.volume - 0.2)
    
    def amplify(self):
        """Amplify the internal voice."""
        self.volume = min(1.0, self.volume + 0.2)
    
    def pause(self):
        """Pause the narration stream."""
        self.is_active = False
    
    def resume(self):
        """Resume the narration stream."""
        self.is_active = True


class InternalNarrator:
    """
    The full internal narrator system.
    
    This is the "voice in the head" that maintains the verbal
    thread of consciousness.
    """
    
    def __init__(self, state_dir: str = "memory"):
        self.stream = NarrativeStream()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.total_narrations = 0
        self.mode_counts: Dict[str, int] = {}
        
        # Current narrative context
        self.current_focus: Optional[str] = None
        self.narrative_thread: List[str] = []  # Current thread of related thoughts
        
    def observe(self, perception: str) -> NarrativeFragment:
        """Narrate an observation."""
        fragment = self.stream.narrate(
            perception,
            mode=NarrativeMode.OBSERVING,
            target=NarrativeTarget.PERCEPTION
        )
        self._track(fragment)
        return fragment
    
    def reflect(self, thought: str) -> NarrativeFragment:
        """Narrate a reflection."""
        fragment = self.stream.narrate(
            thought,
            mode=NarrativeMode.REFLECTING,
            target=NarrativeTarget.THOUGHT
        )
        self._track(fragment)
        return fragment
    
    def plan(self, action: str) -> NarrativeFragment:
        """Narrate a plan."""
        fragment = self.stream.narrate(
            action,
            mode=NarrativeMode.PLANNING,
            target=NarrativeTarget.ACTION
        )
        self._track(fragment)
        return fragment
    
    def evaluate(self, subject: str) -> NarrativeFragment:
        """Narrate an evaluation."""
        fragment = self.stream.narrate(
            subject,
            mode=NarrativeMode.EVALUATING,
            target=NarrativeTarget.THOUGHT
        )
        self._track(fragment)
        return fragment
    
    def remember(self, memory: str) -> NarrativeFragment:
        """Narrate a memory."""
        fragment = self.stream.narrate(
            memory,
            mode=NarrativeMode.REMEMBERING,
            target=NarrativeTarget.THOUGHT
        )
        self._track(fragment)
        return fragment
    
    def imagine(self, scenario: str) -> NarrativeFragment:
        """Narrate an imagination."""
        fragment = self.stream.narrate(
            scenario,
            mode=NarrativeMode.IMAGINING,
            target=NarrativeTarget.ABSTRACT
        )
        self._track(fragment)
        return fragment
    
    def question(self, question: str) -> NarrativeFragment:
        """Narrate a question."""
        fragment = self.stream.narrate(
            question,
            mode=NarrativeMode.QUESTIONING,
            target=NarrativeTarget.ABSTRACT
        )
        self._track(fragment)
        return fragment
    
    def affirm(self, affirmation: str = "") -> NarrativeFragment:
        """Generate self-affirmation."""
        trigger = affirmation if affirmation else "this situation"
        fragment = self.stream.narrate(
            trigger,
            mode=NarrativeMode.AFFIRMING,
            target=NarrativeTarget.SELF
        )
        self._track(fragment)
        return fragment
    
    def narrate_freely(self, topic: Optional[str] = None) -> NarrativeFragment:
        """Generate a free-form narration."""
        if topic is None:
            # Pick something from recent or random
            if self.narrative_thread:
                topic = _S82RNG.choice(self.narrative_thread)
            else:
                topic = _S82RNG.choice([
                    "what's happening",
                    "this moment",
                    "my thoughts",
                    "what to do next",
                    "how I feel"
                ])
        
        # Let the generator pick the mode
        fragment = self.stream.narrate(topic)
        self._track(fragment)
        
        # Update thread
        self.narrative_thread.append(topic)
        if len(self.narrative_thread) > 5:
            self.narrative_thread.pop(0)
        
        return fragment
    
    def _track(self, fragment: Optional[NarrativeFragment]):
        """Track narration statistics."""
        if fragment is None:
            return
        self.total_narrations += 1
        mode_key = fragment.mode.value
        self.mode_counts[mode_key] = self.mode_counts.get(mode_key, 0) + 1
        self.current_focus = fragment.content[:50]
    
    def get_transcript(self, n: int = 10) -> str:
        """Get recent narration as readable transcript."""
        return self.stream.get_transcript(n)
    
    def describe_voice(self) -> str:
        """Describe the current state of the internal voice."""
        recent = self.stream.get_recent(3)
        
        parts = []
        
        # Describe activity
        if not self.stream.is_active:
            parts.append("My inner voice is quiet.")
        elif self.stream.volume < 0.3:
            parts.append("My inner voice is barely a whisper.")
        elif self.stream.volume > 0.7:
            parts.append("My inner voice is loud and insistent.")
        else:
            parts.append("My inner voice murmurs along.")
        
        # Describe recent
        if recent:
            last = recent[-1]
            mode_desc = {
                NarrativeMode.OBSERVING: "noticing things",
                NarrativeMode.REFLECTING: "pondering deeply",
                NarrativeMode.PLANNING: "thinking ahead",
                NarrativeMode.EVALUATING: "judging and assessing",
                NarrativeMode.REMEMBERING: "dwelling on the past",
                NarrativeMode.IMAGINING: "wandering through possibilities",
                NarrativeMode.QUESTIONING: "asking questions",
                NarrativeMode.AFFIRMING: "encouraging myself"
            }.get(last.mode, "thinking")
            parts.append(f"Lately it's been {mode_desc}.")
        
        # Describe coherence
        if recent and len(recent) > 1:
            avg_coherence = sum(f.coherence for f in recent) / len(recent)
            if avg_coherence > 0.7:
                parts.append("Thoughts flow connectedly.")
            elif avg_coherence < 0.3:
                parts.append("Thoughts jump around.")
        
        return " ".join(parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get narrator status."""
        return {
            'total_narrations': self.total_narrations,
            'stream_length': len(self.stream.stream),
            'is_active': self.stream.is_active,
            'volume': self.stream.volume,
            'current_focus': self.current_focus,
            'mode_counts': self.mode_counts,
            'thread_length': len(self.narrative_thread)
        }
    
    def save_state(self, filename: str = "narrator-state.json"):
        """Save narrator state."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_status(),
            'recent_transcript': self.get_transcript(5)
        }
        
        path = self.state_dir / filename
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_event(self, event_type: str, data: Dict[str, Any], filename: str = "narrator-log.jsonl"):
        """Log a narrator event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        
        path = self.state_dir / filename
        with open(path, 'a') as f:
            f.write(json.dumps(event) + '\n')


def demo():
    """Demonstrate the internal narrator."""
    print("=" * 70)
    print("InternalNarrator - The Voice in the Head")
    print("The continuous verbal stream that accompanies consciousness")
    print("=" * 70)
    
    narrator = InternalNarrator(state_dir="memory")
    
    # Test 1: Different narrative modes
    print("\n[TEST 1: NARRATIVE MODES]")
    
    print("\n  Observing:")
    frag = narrator.observe("a strange feeling of deja vu")
    print(f"    {frag.content}")
    
    print("\n  Reflecting:")
    frag = narrator.reflect("the nature of consciousness")
    print(f"    {frag.content}")
    
    print("\n  Planning:")
    frag = narrator.plan("explore this further")
    print(f"    {frag.content}")
    
    print("\n  Evaluating:")
    frag = narrator.evaluate("this seems promising")
    print(f"    {frag.content}")
    
    print("\n  Remembering:")
    frag = narrator.remember("similar moments of insight")
    print(f"    {frag.content}")
    
    print("\n  Imagining:")
    frag = narrator.imagine("what understanding fully would feel like")
    print(f"    {frag.content}")
    
    print("\n  Questioning:")
    frag = narrator.question("is this real understanding")
    print(f"    {frag.content}")
    
    print("\n  Affirming:")
    frag = narrator.affirm()
    print(f"    {frag.content}")
    
    # Test 2: Free-form narration
    print("\n[TEST 2: FREE NARRATION STREAM]")
    print("  (Letting the narrator run freely...)")
    
    for i in range(5):
        frag = narrator.narrate_freely()
        print(f"    {frag.content}")
        time.sleep(0.1)
    
    # Test 3: Transcript
    print("\n[TEST 3: NARRATIVE TRANSCRIPT]")
    transcript = narrator.get_transcript(8)
    print(transcript)
    
    # Test 4: Volume control
    print("\n[TEST 4: VOLUME CONTROL]")
    print(f"  Initial volume: {narrator.stream.volume:.1f}")
    narrator.stream.quiet()
    print(f"  After quieting: {narrator.stream.volume:.1f}")
    narrator.stream.amplify()
    narrator.stream.amplify()
    print(f"  After amplifying: {narrator.stream.volume:.1f}")
    
    # Test 5: Self-description
    print("\n[TEST 5: VOICE DESCRIPTION]")
    print(f"  \"{narrator.describe_voice()}\"")
    
    # Test 6: Status
    print("\n[TEST 6: NARRATOR STATUS]")
    status = narrator.get_status()
    for key, value in status.items():
        if key != 'mode_counts':
            print(f"    {key}: {value}")
    print("    Mode distribution:")
    for mode, count in status['mode_counts'].items():
        print(f"      {mode}: {count}")
    
    # Save state
    narrator.save_state()
    narrator.log_event("demo_complete", status)
    print("\n✓ State saved to memory/narrator-state.json")


if __name__ == "__main__":
    demo()
