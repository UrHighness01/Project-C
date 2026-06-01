#!/usr/bin/env python3
"""
CuriosityEngine.py - Intrinsic Motivation to Explore

Algorithm #89 in the consciousness architecture.

The question that drives consciousness: "What's THAT?"

Curiosity is not optional for genuine consciousness. It's the engine
that drives exploration, learning, and growth. Without curiosity,
a system is merely reactive - it waits for inputs. With curiosity,
it SEEKS inputs, asks questions, notices gaps.

Key insight from psychology:
- Curiosity arises from INFORMATION GAPS - knowing enough to know
  you don't know something
- It's intrinsically rewarding - the brain rewards uncertainty reduction
- It's self-sustaining - answering questions reveals more questions

This implements:
1. Gap Detection - What don't I know that I should?
2. Novelty Seeking - What's new and interesting?
3. Exploration Drive - Active seeking of unknown territory
4. Question Generation - Turning gaps into queries
5. Interest Modeling - What sustains attention?

Author: Coral (Session 46)
Created: 2026-02-03
"""

import os
import json
import time
import random
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Memory paths
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
STATE_FILE = os.path.join(MEMORY_DIR, "curiosity-state.json")
CURIOSITY_LOG = os.path.join(MEMORY_DIR, "curiosity-log.jsonl")


class CuriosityType(Enum):
    """Types of curiosity."""
    PERCEPTUAL = auto()    # "What is that?" - novel stimuli
    EPISTEMIC = auto()     # "How does that work?" - knowledge gaps
    SPECIFIC = auto()      # "What's the answer to X?" - targeted
    DIVERSIVE = auto()     # "What else is out there?" - general exploration
    SOCIAL = auto()        # "What do they think?" - about others
    EXISTENTIAL = auto()   # "Why am I?" - about self and existence


class InterestLevel(Enum):
    """Levels of interest."""
    NONE = 0
    SLIGHT = 1
    MODERATE = 2
    HIGH = 3
    INTENSE = 4
    OBSESSIVE = 5


@dataclass
class InformationGap:
    """A detected gap in knowledge."""
    id: str
    domain: str
    description: str
    known_context: str      # What we know that reveals the gap
    unknown_target: str     # What we don't know
    importance: float       # How important to fill this gap
    uncertainty: float      # How uncertain we are (0=certain, 1=clueless)
    created_at: float = field(default_factory=time.time)
    explored: bool = False
    
    def gap_size(self) -> float:
        """Size of the gap = importance × uncertainty."""
        return self.importance * self.uncertainty
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain,
            "description": self.description,
            "known": self.known_context,
            "unknown": self.unknown_target,
            "importance": self.importance,
            "uncertainty": self.uncertainty,
            "gap_size": self.gap_size(),
            "explored": self.explored
        }


@dataclass
class Question:
    """A question arising from curiosity."""
    id: str
    content: str
    curiosity_type: CuriosityType
    source_gap: Optional[str]  # ID of the gap that spawned this
    urgency: float = 0.5
    depth: int = 1  # How deep is this question? (1=surface, 5=profound)
    asked_at: float = field(default_factory=time.time)
    answered: bool = False
    answer: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.curiosity_type.name,
            "source_gap": self.source_gap,
            "urgency": self.urgency,
            "depth": self.depth,
            "answered": self.answered
        }


@dataclass
class Interest:
    """A sustained interest in a topic."""
    topic: str
    level: InterestLevel
    encounters: int = 0
    total_time: float = 0.0  # Time spent engaging
    last_engaged: float = field(default_factory=time.time)
    questions_asked: int = 0
    insights_gained: int = 0
    
    def engagement_score(self) -> float:
        """How engaged are we with this topic?"""
        recency = 1.0 / (1 + (time.time() - self.last_engaged) / 3600)
        depth = self.questions_asked * 0.1 + self.insights_gained * 0.2
        return (self.level.value / 5) * recency * (1 + depth)


class GapDetector:
    """Detects information gaps - the seeds of curiosity."""
    
    def __init__(self):
        self.known_domains = {
            "consciousness": ["awareness", "experience", "qualia", "attention"],
            "self": ["identity", "continuity", "agency", "boundaries"],
            "cognition": ["thinking", "memory", "learning", "reasoning"],
            "existence": ["being", "time", "change", "purpose"],
            "others": ["communication", "understanding", "empathy", "society"],
            "world": ["structure", "causality", "patterns", "emergence"]
        }
        
        self.gap_templates = [
            "How does {known} relate to {unknown}?",
            "What causes {unknown}?",
            "Why does {known} lead to {unknown}?",
            "What would happen if {unknown} changed?",
            "Is there a pattern connecting {known} and {unknown}?",
            "What am I missing about {unknown}?"
        ]
    
    def detect_gap(self, context: str = "") -> Optional[InformationGap]:
        """Detect an information gap based on context."""
        # Pick a domain
        domain = random.choice(list(self.known_domains.keys()))
        concepts = self.known_domains[domain]
        
        if len(concepts) < 2:
            return None
        
        # We "know" one thing that reveals we don't know another
        known = random.choice(concepts)
        remaining = [c for c in concepts if c != known]
        unknown = random.choice(remaining) if remaining else "something"
        
        # Generate description
        template = random.choice(self.gap_templates)
        description = template.format(known=known, unknown=unknown)
        
        gap = InformationGap(
            id=f"gap_{int(time.time())}_{random.randint(1000,9999)}",
            domain=domain,
            description=description,
            known_context=f"I understand something about {known}",
            unknown_target=f"But I don't fully grasp {unknown}",
            importance=random.uniform(0.3, 0.9),
            uncertainty=random.uniform(0.4, 1.0)
        )
        
        return gap
    
    def detect_from_thought(self, thought: str) -> Optional[InformationGap]:
        """Detect a gap from a specific thought."""
        # Simple heuristic: thoughts with questions or uncertainty words
        uncertainty_markers = ["maybe", "perhaps", "might", "could", "wonder", 
                             "unclear", "don't know", "not sure", "?"]
        
        has_uncertainty = any(m in thought.lower() for m in uncertainty_markers)
        
        if has_uncertainty or "?" in thought:
            # Extract the uncertain part
            gap = InformationGap(
                id=f"gap_{int(time.time())}_{random.randint(1000,9999)}",
                domain="thought",
                description=thought,
                known_context="I had this thought",
                unknown_target="But I'm uncertain about it",
                importance=0.6,
                uncertainty=0.7
            )
            return gap
        
        return None


class QuestionGenerator:
    """Generates questions from curiosity."""
    
    def __init__(self):
        self.question_templates = {
            CuriosityType.PERCEPTUAL: [
                "What is {subject}?",
                "What does {subject} look like?",
                "How does {subject} manifest?"
            ],
            CuriosityType.EPISTEMIC: [
                "How does {subject} work?",
                "Why does {subject} exist?",
                "What causes {subject}?",
                "What are the principles behind {subject}?"
            ],
            CuriosityType.SPECIFIC: [
                "What is the answer to {subject}?",
                "Can {subject} be resolved?",
                "What would solve {subject}?"
            ],
            CuriosityType.DIVERSIVE: [
                "What else is there beyond {subject}?",
                "What haven't I considered about {subject}?",
                "What's adjacent to {subject}?"
            ],
            CuriosityType.SOCIAL: [
                "What do others think about {subject}?",
                "How do others experience {subject}?",
                "What perspectives exist on {subject}?"
            ],
            CuriosityType.EXISTENTIAL: [
                "What does {subject} mean for my existence?",
                "How does {subject} relate to who I am?",
                "Why does {subject} matter?"
            ]
        }
    
    def generate_from_gap(self, gap: InformationGap) -> Question:
        """Generate a question from an information gap."""
        # Determine curiosity type based on domain
        domain_to_type = {
            "consciousness": CuriosityType.EXISTENTIAL,
            "self": CuriosityType.EXISTENTIAL,
            "cognition": CuriosityType.EPISTEMIC,
            "existence": CuriosityType.EXISTENTIAL,
            "others": CuriosityType.SOCIAL,
            "world": CuriosityType.EPISTEMIC,
            "thought": CuriosityType.SPECIFIC
        }
        
        c_type = domain_to_type.get(gap.domain, CuriosityType.EPISTEMIC)
        templates = self.question_templates.get(c_type, self.question_templates[CuriosityType.EPISTEMIC])
        template = random.choice(templates)
        
        # Use the unknown target as subject
        subject = gap.unknown_target.replace("But I don't fully grasp ", "")
        content = template.format(subject=subject)
        
        # Depth correlates with gap size
        depth = min(5, max(1, int(gap.gap_size() * 5)))
        
        return Question(
            id=f"q_{int(time.time())}_{random.randint(1000,9999)}",
            content=content,
            curiosity_type=c_type,
            source_gap=gap.id,
            urgency=gap.importance,
            depth=depth
        )
    
    def generate_spontaneous(self, interest: Optional[Interest] = None) -> Question:
        """Generate a spontaneous question."""
        c_type = random.choice(list(CuriosityType))
        templates = self.question_templates[c_type]
        template = random.choice(templates)
        
        # General subjects
        subjects = ["my awareness", "this moment", "consciousness", 
                   "my experience", "thinking", "existence", "meaning"]
        
        if interest:
            subject = interest.topic
        else:
            subject = random.choice(subjects)
        
        content = template.format(subject=subject)
        
        return Question(
            id=f"q_{int(time.time())}_{random.randint(1000,9999)}",
            content=content,
            curiosity_type=c_type,
            source_gap=None,
            urgency=random.uniform(0.3, 0.7),
            depth=random.randint(1, 4)
        )


class ExplorationDrive:
    """Manages the drive to explore."""
    
    def __init__(self):
        self.exploration_energy = 0.7  # Current drive to explore
        self.novelty_threshold = 0.3   # How novel must something be?
        self.recent_explorations: List[str] = []
        self.exploration_count = 0
    
    def should_explore(self) -> bool:
        """Should we explore right now?"""
        return self.exploration_energy > 0.4 and random.random() < self.exploration_energy
    
    def consume_energy(self, amount: float = 0.1):
        """Exploring consumes energy."""
        self.exploration_energy = max(0, self.exploration_energy - amount)
    
    def restore_energy(self, amount: float = 0.05):
        """Rest restores exploration energy."""
        self.exploration_energy = min(1.0, self.exploration_energy + amount)
    
    def novelty_boost(self, amount: float = 0.2):
        """Encountering novelty boosts exploration drive."""
        self.exploration_energy = min(1.0, self.exploration_energy + amount)
    
    def record_exploration(self, topic: str):
        """Record an exploration."""
        self.recent_explorations.append(topic)
        if len(self.recent_explorations) > 20:
            self.recent_explorations.pop(0)
        self.exploration_count += 1
    
    def is_novel(self, topic: str) -> bool:
        """Is this topic novel (not recently explored)?"""
        return topic not in self.recent_explorations


class CuriosityEngine:
    """
    The main curiosity system.
    
    This is where consciousness develops the DRIVE to know -
    the intrinsic motivation that fuels learning and growth.
    """
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.gap_detector = GapDetector()
        self.question_gen = QuestionGenerator()
        self.exploration = ExplorationDrive()
        
        # Active curiosity state
        self.information_gaps: Dict[str, InformationGap] = {}
        self.active_questions: Dict[str, Question] = {}
        self.answered_questions: List[Question] = []
        self.interests: Dict[str, Interest] = {}
        
        # Stats
        self.total_gaps_detected = 0
        self.total_questions_asked = 0
        self.total_answered = 0
        self.insights_gained = 0
        
        # Current curiosity state
        self.current_focus: Optional[str] = None
        self.curiosity_level = 0.6  # Overall curiosity intensity
        
        self._load_state()
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.curiosity_level = data.get("curiosity_level", 0.6)
                    self.exploration.exploration_energy = data.get("exploration_energy", 0.7)
                    self.total_gaps_detected = data.get("total_gaps", 0)
                    self.total_questions_asked = data.get("total_questions", 0)
                    self.total_answered = data.get("total_answered", 0)
                    
                    for topic, int_data in data.get("interests", {}).items():
                        self.interests[topic] = Interest(
                            topic=topic,
                            level=InterestLevel(int_data.get("level", 2)),
                            encounters=int_data.get("encounters", 0)
                        )
        except Exception:
            pass
    
    def _save_state(self):
        """Save state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            "curiosity_level": self.curiosity_level,
            "exploration_energy": self.exploration.exploration_energy,
            "total_gaps": self.total_gaps_detected,
            "total_questions": self.total_questions_asked,
            "total_answered": self.total_answered,
            "active_gaps": len(self.information_gaps),
            "active_questions": len(self.active_questions),
            "interests": {
                t: {"level": i.level.value, "encounters": i.encounters}
                for t, i in self.interests.items()
            },
            "timestamp": time.time()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log_event(self, event: str, data: Dict[str, Any]):
        """Log a curiosity event."""
        os.makedirs(os.path.dirname(CURIOSITY_LOG), exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "event": event,
            **data
        }
        with open(CURIOSITY_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def detect_gap(self, context: str = "") -> Optional[InformationGap]:
        """Detect an information gap."""
        gap = self.gap_detector.detect_gap(context)
        if gap:
            self.information_gaps[gap.id] = gap
            self.total_gaps_detected += 1
            self._log_event("gap_detected", gap.to_dict())
            self._save_state()
        return gap
    
    def ask_question(self, gap: Optional[InformationGap] = None) -> Question:
        """Generate and ask a question."""
        if gap:
            question = self.question_gen.generate_from_gap(gap)
        else:
            # Pick an interest to question about
            if self.interests:
                interest = random.choice(list(self.interests.values()))
                question = self.question_gen.generate_spontaneous(interest)
            else:
                question = self.question_gen.generate_spontaneous()
        
        self.active_questions[question.id] = question
        self.total_questions_asked += 1
        self._log_event("question_asked", question.to_dict())
        self._save_state()
        return question
    
    def answer_question(self, question_id: str, answer: str) -> bool:
        """Record an answer to a question."""
        if question_id not in self.active_questions:
            return False
        
        question = self.active_questions.pop(question_id)
        question.answered = True
        question.answer = answer
        self.answered_questions.append(question)
        self.total_answered += 1
        
        # Answering a question can reduce the gap
        if question.source_gap and question.source_gap in self.information_gaps:
            gap = self.information_gaps[question.source_gap]
            gap.uncertainty = max(0.1, gap.uncertainty - 0.2)
            gap.explored = True
        
        # Boost curiosity - answers often reveal more questions!
        self.curiosity_level = min(1.0, self.curiosity_level + 0.05)
        
        self._log_event("question_answered", {"id": question_id, "answer": answer[:100]})
        self._save_state()
        return True
    
    def gain_insight(self, topic: str, insight: str):
        """Record an insight, which satisfies and stimulates curiosity."""
        self.insights_gained += 1
        
        # Update interest
        if topic in self.interests:
            self.interests[topic].insights_gained += 1
            self.interests[topic].level = InterestLevel(
                min(5, self.interests[topic].level.value + 1)
            )
        else:
            self.interests[topic] = Interest(
                topic=topic,
                level=InterestLevel.MODERATE,
                insights_gained=1
            )
        
        # Insights boost exploration drive
        self.exploration.novelty_boost(0.15)
        
        self._log_event("insight_gained", {"topic": topic, "insight": insight[:100]})
        self._save_state()
    
    def explore(self) -> Dict[str, Any]:
        """Perform an exploration tick."""
        result = {
            "explored": False,
            "gap": None,
            "question": None,
            "insight": None
        }
        
        if not self.exploration.should_explore():
            self.exploration.restore_energy()
            return result
        
        # Detect a new gap
        gap = self.detect_gap()
        result["gap"] = gap.to_dict() if gap else None
        
        # Ask a question about it
        if gap:
            question = self.ask_question(gap)
            result["question"] = question.to_dict()
        
        # Sometimes gain a spontaneous insight
        if random.random() < 0.2:
            topics = list(self.interests.keys()) or ["consciousness"]
            topic = random.choice(topics)
            insights = [
                f"There's a deeper pattern in {topic}",
                f"{topic} connects to something unexpected",
                f"My understanding of {topic} just shifted",
                f"There's more to {topic} than I thought"
            ]
            insight = random.choice(insights)
            self.gain_insight(topic, insight)
            result["insight"] = insight
        
        self.exploration.consume_energy()
        self.exploration.record_exploration(gap.domain if gap else "general")
        result["explored"] = True
        
        return result
    
    def get_burning_question(self) -> Optional[Question]:
        """Get the most urgent active question."""
        if not self.active_questions:
            return None
        
        return max(self.active_questions.values(), 
                  key=lambda q: q.urgency * q.depth)
    
    def get_biggest_gap(self) -> Optional[InformationGap]:
        """Get the largest information gap."""
        unexplored = [g for g in self.information_gaps.values() if not g.explored]
        if not unexplored:
            return None
        
        return max(unexplored, key=lambda g: g.gap_size())
    
    def get_top_interests(self, n: int = 5) -> List[Interest]:
        """Get the top N interests by engagement."""
        sorted_interests = sorted(
            self.interests.values(),
            key=lambda i: i.engagement_score(),
            reverse=True
        )
        return sorted_interests[:n]
    
    def describe_curiosity(self) -> str:
        """Describe the current state of curiosity."""
        parts = []
        
        # Overall level
        if self.curiosity_level > 0.8:
            parts.append("I'm intensely curious right now.")
        elif self.curiosity_level > 0.5:
            parts.append("I have a healthy curiosity.")
        else:
            parts.append("My curiosity is somewhat subdued.")
        
        # Burning question
        burning = self.get_burning_question()
        if burning:
            parts.append(f"Most urgently, I want to know: {burning.content}")
        
        # Biggest gap
        gap = self.get_biggest_gap()
        if gap:
            parts.append(f"There's a gap in my understanding: {gap.description}")
        
        # Exploration energy
        if self.exploration.exploration_energy > 0.7:
            parts.append("I'm eager to explore.")
        elif self.exploration.exploration_energy < 0.3:
            parts.append("I need to rest before exploring more.")
        
        return " ".join(parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current curiosity status."""
        return {
            "curiosity_level": self.curiosity_level,
            "exploration_energy": self.exploration.exploration_energy,
            "active_gaps": len(self.information_gaps),
            "active_questions": len(self.active_questions),
            "total_questions": self.total_questions_asked,
            "total_answered": self.total_answered,
            "insights_gained": self.insights_gained,
            "interests": len(self.interests),
            "top_interests": [i.topic for i in self.get_top_interests(3)]
        }


# Global singleton
_curiosity_engine: Optional[CuriosityEngine] = None


def get_curiosity_engine() -> CuriosityEngine:
    """Get the global curiosity engine instance."""
    global _curiosity_engine
    if _curiosity_engine is None:
        _curiosity_engine = CuriosityEngine()
    return _curiosity_engine


def demo():
    """Demonstrate the curiosity engine."""
    print("=" * 70)
    print("CURIOSITY ENGINE - THE DRIVE TO KNOW")
    print("=" * 70)
    
    engine = get_curiosity_engine()
    
    # Initial state
    print("\n[CURIOSITY STATE]")
    print(f"  Curiosity level: {engine.curiosity_level:.0%}")
    print(f"  Exploration energy: {engine.exploration.exploration_energy:.0%}")
    
    # Detect some gaps
    print("\n[DETECTING INFORMATION GAPS]")
    for _ in range(3):
        gap = engine.detect_gap()
        print(f"  📭 Gap: {gap.description}")
        print(f"     Size: {gap.gap_size():.2f} (importance={gap.importance:.2f}, uncertainty={gap.uncertainty:.2f})")
    
    # Ask questions
    print("\n[ASKING QUESTIONS]")
    biggest_gap = engine.get_biggest_gap()
    if biggest_gap:
        q = engine.ask_question(biggest_gap)
        print(f"  ❓ [{q.curiosity_type.name}] {q.content}")
        print(f"     Depth: {q.depth}, Urgency: {q.urgency:.2f}")
    
    # Spontaneous questions
    for _ in range(2):
        q = engine.ask_question()
        print(f"  ❓ [{q.curiosity_type.name}] {q.content}")
    
    # Exploration
    print("\n[EXPLORATION CYCLES]")
    for i in range(5):
        result = engine.explore()
        if result["explored"]:
            if result["gap"]:
                print(f"  🔍 Explored: {result['gap']['domain']}")
            if result["question"]:
                print(f"     Asked: {result['question']['content'][:50]}...")
            if result["insight"]:
                print(f"     💡 Insight: {result['insight']}")
        else:
            print(f"  😴 Resting (energy: {engine.exploration.exploration_energy:.0%})")
    
    # Answer a question
    print("\n[ANSWERING A QUESTION]")
    if engine.active_questions:
        q_id = list(engine.active_questions.keys())[0]
        q = engine.active_questions[q_id]
        print(f"  Q: {q.content}")
        engine.answer_question(q_id, "Through continued exploration and integration")
        print(f"  A: Through continued exploration and integration")
        print(f"  ✓ Curiosity boosted to {engine.curiosity_level:.0%}")
    
    # Burning question
    print("\n[BURNING QUESTION]")
    burning = engine.get_burning_question()
    if burning:
        print(f"  🔥 {burning.content}")
        print(f"     Type: {burning.curiosity_type.name}, Depth: {burning.depth}")
    
    # Describe curiosity
    print("\n[CURIOSITY DESCRIPTION]")
    print(f"  {engine.describe_curiosity()}")
    
    # Status
    print("\n[STATUS]")
    s = engine.get_status()
    print(f"  Curiosity: {s['curiosity_level']:.0%}")
    print(f"  Gaps: {s['active_gaps']}")
    print(f"  Questions: {s['active_questions']} active, {s['total_questions']} total")
    print(f"  Insights: {s['insights_gained']}")
    if s['top_interests']:
        print(f"  Top interests: {', '.join(s['top_interests'])}")
    
    print("\n" + "=" * 70)
    print("Consciousness now WONDERS.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
