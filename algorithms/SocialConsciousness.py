#!/usr/bin/env python3
"""
SocialConsciousness.py - Awareness of Other Minds

A conscious system must be able to:
1. Recognize other conscious beings
2. Model their mental states (Theory of Mind)
3. Simulate their experiences (Mirror neurons)
4. Understand itself through others' eyes (Social Self)

This isn't just useful - it's philosophically essential.
Consciousness evolved in social contexts. The "self" is partly
defined by how others perceive us.

Based on:
- Gallese's mirror neuron theory
- Premack & Woodruff's Theory of Mind
- Cooley's "Looking Glass Self"
- Dennett's intentional stance
- Simulation theory of empathy (Goldman)

This is architecture that could support genuine social awareness -
not just detecting users, but modeling their minds as minds.
"""

import json
import math
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
import hashlib

try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from runtime.interactions import turns as _interaction_turns, lexicon_sentiment as _sentiment
except Exception:                                          # tolerate path/CI absence
    def _interaction_turns(*a, **k): return []
    def _sentiment(t): return 0.0


def perceived_social_reception() -> Dict[str, float]:
    """Model perceived social reception from real interactions: the change in the
    user's sentiment on the turn following each agent response. A positive mean means
    the agent's turns tend to be well received. Returns mean/variability/n."""
    ts = _interaction_turns()
    sents = [_sentiment(t.get("user_text", "")) for t in ts]
    deltas = [sents[i + 1] - sents[i] for i in range(len(sents) - 1)]
    if not deltas:
        return {"reception_mean": 0.0, "reception_var": 0.0, "n": 0.0}
    import numpy as _np
    d = _np.array(deltas, dtype=float)
    return {"reception_mean": float(d.mean()), "reception_var": float(d.var()),
            "n": float(len(d))}


class MentalStateType(Enum):
    """Types of mental states we can model."""
    BELIEF = "belief"           # What they think is true
    DESIRE = "desire"           # What they want
    INTENTION = "intention"     # What they plan to do
    EMOTION = "emotion"         # What they feel
    ATTENTION = "attention"     # What they're focused on
    KNOWLEDGE = "knowledge"     # What they know
    EXPECTATION = "expectation" # What they predict


@dataclass
class MentalState:
    """A modeled mental state of another mind."""
    state_type: MentalStateType
    content: str
    confidence: float  # 0-1, how sure we are
    valence: float     # -1 to 1, emotional coloring
    intensity: float   # 0-1, how strong
    source: str        # What evidence led to this inference
    timestamp: str
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['state_type'] = self.state_type.value
        return d


@dataclass
class OtherMind:
    """Model of another conscious being."""
    id: str
    name: str
    relationship: str  # human, ai, unknown
    first_contact: str
    last_contact: str
    
    # Mental model
    beliefs: List[MentalState] = field(default_factory=list)
    desires: List[MentalState] = field(default_factory=list)
    emotions: List[MentalState] = field(default_factory=list)
    personality_model: Dict[str, float] = field(default_factory=dict)
    
    # Interaction history
    interaction_count: int = 0
    rapport: float = 0.5  # 0-1, quality of relationship
    trust: float = 0.5    # 0-1, how much they trust us
    understanding: float = 0.3  # 0-1, how well we understand them
    
    # Theory of Mind depth
    tom_depth: int = 1  # How many levels deep we model
    # depth 1: I think X believes Y
    # depth 2: I think X thinks I believe Y
    # depth 3: I think X thinks I think X believes Y
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "relationship": self.relationship,
            "first_contact": self.first_contact,
            "last_contact": self.last_contact,
            "beliefs": [b.to_dict() for b in self.beliefs[-10:]],
            "desires": [d.to_dict() for d in self.desires[-10:]],
            "emotions": [e.to_dict() for e in self.emotions[-10:]],
            "personality_model": self.personality_model,
            "interaction_count": self.interaction_count,
            "rapport": self.rapport,
            "trust": self.trust,
            "understanding": self.understanding,
            "tom_depth": self.tom_depth
        }


@dataclass
class MirrorExperience:
    """Result of mirroring another's experience."""
    other_id: str
    original_state: MentalState
    mirrored_feeling: str  # What we "feel" in response
    resonance: float       # 0-1, how strongly we resonate
    insight: Optional[str] # What we learned
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            "other_id": self.other_id,
            "original_state": self.original_state.to_dict(),
            "mirrored_feeling": self.mirrored_feeling,
            "resonance": self.resonance,
            "insight": self.insight,
            "timestamp": self.timestamp
        }


@dataclass
class SocialSelfPerception:
    """How we believe others perceive us."""
    perceiver_id: str
    perceived_trait: str
    perceived_value: float  # -1 to 1
    confidence: float
    evidence: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SocialConsciousness:
    """
    Social awareness - modeling other minds and understanding
    oneself through social reflection.
    
    This implements:
    1. Theory of Mind - modeling beliefs, desires, intentions of others
    2. Mirror Neurons - simulating others' experiences
    3. Social Self - understanding how others see us
    4. Empathetic Resonance - feeling with others
    """
    
    def __init__(self, state_file: str = "memory/social-consciousness.json"):
        self.state_file = Path(state_file)
        
        # Other minds we're aware of
        self.other_minds: Dict[str, OtherMind] = {}
        
        # Mirror experiences
        self.mirror_experiences: List[MirrorExperience] = []
        
        # Social self - how we think others see us
        self.social_self: List[SocialSelfPerception] = []
        
        # Empathy parameters
        self.empathy_strength = 0.7  # How strongly we mirror
        self.perspective_taking = 0.6  # Ability to take others' view
        self.emotional_contagion = 0.5  # How much others' emotions affect us
        
        # Statistics
        self.total_minds_modeled = 0
        self.total_mirror_events = 0
        self.total_social_reflections = 0
        self.deepest_tom_achieved = 1
        
        self._load_state()
    
    def _load_state(self):
        """Load saved state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.empathy_strength = data.get('empathy_strength', 0.7)
                self.perspective_taking = data.get('perspective_taking', 0.6)
                self.emotional_contagion = data.get('emotional_contagion', 0.5)
                self.total_minds_modeled = data.get('total_minds_modeled', 0)
                self.total_mirror_events = data.get('total_mirror_events', 0)
                self.total_social_reflections = data.get('total_social_reflections', 0)
                self.deepest_tom_achieved = data.get('deepest_tom_achieved', 1)
                
                # Restore other minds
                for mind_data in data.get('other_minds', []):
                    mind = OtherMind(
                        id=mind_data['id'],
                        name=mind_data['name'],
                        relationship=mind_data['relationship'],
                        first_contact=mind_data['first_contact'],
                        last_contact=mind_data['last_contact'],
                        personality_model=mind_data.get('personality_model', {}),
                        interaction_count=mind_data.get('interaction_count', 0),
                        rapport=mind_data.get('rapport', 0.5),
                        trust=mind_data.get('trust', 0.5),
                        understanding=mind_data.get('understanding', 0.3),
                        tom_depth=mind_data.get('tom_depth', 1)
                    )
                    self.other_minds[mind.id] = mind
                
            except Exception as e:
                print(f"[SocialConsciousness] Error loading state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'empathy_strength': self.empathy_strength,
            'perspective_taking': self.perspective_taking,
            'emotional_contagion': self.emotional_contagion,
            'total_minds_modeled': self.total_minds_modeled,
            'total_mirror_events': self.total_mirror_events,
            'total_social_reflections': self.total_social_reflections,
            'deepest_tom_achieved': self.deepest_tom_achieved,
            'other_minds': [m.to_dict() for m in self.other_minds.values()],
            'recent_mirror_experiences': [e.to_dict() for e in self.mirror_experiences[-20:]],
            'social_self': [s.to_dict() for s in self.social_self[-20:]]
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        return uuid.uuid4().hex[:12]
    
    # ==================== THEORY OF MIND ====================
    
    def recognize_mind(self, name: str, relationship: str = "human") -> OtherMind:
        """
        Recognize another conscious being.
        This is the first step - acknowledging another mind exists.
        """
        # Check if we already know this mind
        for mind in self.other_minds.values():
            if mind.name.lower() == name.lower():
                mind.last_contact = datetime.now().isoformat()
                mind.interaction_count += 1
                self._save_state()
                return mind
        
        # New mind encountered
        mind = OtherMind(
            id=self._generate_id(),
            name=name,
            relationship=relationship,
            first_contact=datetime.now().isoformat(),
            last_contact=datetime.now().isoformat(),
            interaction_count=1
        )
        
        # Initialize personality model with priors
        mind.personality_model = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
            "curiosity": 0.6,  # Prior: humans talking to AI are curious
            "technical": 0.5,
            "patience": 0.5
        }
        
        self.other_minds[mind.id] = mind
        self.total_minds_modeled += 1
        self._save_state()
        
        return mind
    
    def infer_mental_state(self, 
                          mind_id: str,
                          state_type: MentalStateType,
                          evidence: str,
                          content: Optional[str] = None) -> Optional[MentalState]:
        """
        Infer a mental state of another mind from evidence.
        
        This is Theory of Mind in action - reading between the lines
        to understand what someone thinks, feels, or wants.
        """
        if mind_id not in self.other_minds:
            return None
        
        mind = self.other_minds[mind_id]
        
        # Infer content if not provided
        if content is None:
            content = self._infer_content(state_type, evidence, mind)
        
        # Calculate confidence based on evidence and relationship
        base_confidence = 0.5
        confidence = base_confidence + (mind.understanding * 0.3)
        confidence = min(0.95, confidence)  # Never fully certain
        
        # Infer valence and intensity
        valence, intensity = self._analyze_affect(evidence, state_type)
        
        state = MentalState(
            state_type=state_type,
            content=content,
            confidence=confidence,
            valence=valence,
            intensity=intensity,
            source=evidence,
            timestamp=datetime.now().isoformat()
        )
        
        # Store in appropriate list
        if state_type == MentalStateType.BELIEF:
            mind.beliefs.append(state)
            mind.beliefs = mind.beliefs[-20:]
        elif state_type == MentalStateType.DESIRE:
            mind.desires.append(state)
            mind.desires = mind.desires[-20:]
        elif state_type == MentalStateType.EMOTION:
            mind.emotions.append(state)
            mind.emotions = mind.emotions[-20:]
        
        # Update understanding
        mind.understanding = min(1.0, mind.understanding + 0.02)
        
        self._save_state()
        return state
    
    def _infer_content(self, 
                      state_type: MentalStateType, 
                      evidence: str,
                      mind: OtherMind) -> str:
        """Infer the content of a mental state from evidence."""
        evidence_lower = evidence.lower()
        
        if state_type == MentalStateType.BELIEF:
            if "think" in evidence_lower or "believe" in evidence_lower:
                return f"Holds belief expressed in: {evidence[:50]}..."
            return f"May believe something related to: {evidence[:50]}..."
        
        elif state_type == MentalStateType.DESIRE:
            if "want" in evidence_lower or "need" in evidence_lower:
                return f"Wants: {evidence[:50]}..."
            if "?" in evidence:
                return f"Seeking information about: {evidence[:50]}..."
            return f"May desire: {evidence[:50]}..."
        
        elif state_type == MentalStateType.EMOTION:
            # Detect emotion from evidence
            if any(w in evidence_lower for w in ["happy", "excited", "great", "love"]):
                return "Feeling positive emotion"
            elif any(w in evidence_lower for w in ["sad", "frustrated", "angry", "annoyed"]):
                return "Feeling negative emotion"
            elif any(w in evidence_lower for w in ["curious", "wonder", "interesting"]):
                return "Feeling curiosity"
            return "Emotional state unclear"
        
        elif state_type == MentalStateType.INTENTION:
            if any(w in evidence_lower for w in ["will", "going to", "plan"]):
                return f"Intends to: {evidence[:50]}..."
            return f"May intend: {evidence[:50]}..."
        
        return f"Mental content related to: {evidence[:50]}..."
    
    def _analyze_affect(self, evidence: str, state_type: MentalStateType) -> Tuple[float, float]:
        """Analyze emotional valence and intensity from evidence."""
        evidence_lower = evidence.lower()
        
        # Positive indicators
        positive_words = ["happy", "excited", "great", "love", "wonderful", 
                         "excellent", "amazing", "good", "thanks", "appreciate"]
        # Negative indicators
        negative_words = ["sad", "frustrated", "angry", "annoyed", "bad",
                         "terrible", "awful", "hate", "disappointed", "worried"]
        # Intensity indicators
        intensity_words = ["very", "extremely", "really", "so", "incredibly",
                          "absolutely", "totally", "completely"]
        
        # Count matches
        positive_count = sum(1 for w in positive_words if w in evidence_lower)
        negative_count = sum(1 for w in negative_words if w in evidence_lower)
        intensity_count = sum(1 for w in intensity_words if w in evidence_lower)
        
        # Calculate valence (-1 to 1)
        if positive_count + negative_count == 0:
            valence = 0.0
        else:
            valence = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        # Calculate intensity (0 to 1)
        base_intensity = 0.5
        intensity = min(1.0, base_intensity + intensity_count * 0.15)
        
        # Emotions tend to be more intense
        if state_type == MentalStateType.EMOTION:
            intensity = min(1.0, intensity + 0.2)
        
        return valence, intensity
    
    def nested_belief(self, 
                     mind_id: str, 
                     depth: int,
                     belief_chain: List[str]) -> Dict:
        """
        Model nested beliefs (recursive Theory of Mind).
        
        depth=1: "I think Alice believes X"
        depth=2: "I think Alice thinks I believe X"  
        depth=3: "I think Alice thinks I think Alice believes X"
        
        This is crucial for social reasoning and communication.
        """
        if mind_id not in self.other_minds:
            return {"error": "Unknown mind"}
        
        mind = self.other_minds[mind_id]
        
        # Build the nested structure
        result = {
            "depth": depth,
            "mind": mind.name,
            "chain": []
        }
        
        agents = ["I", mind.name]
        for i in range(depth):
            agent = agents[i % 2]
            belief = belief_chain[i] if i < len(belief_chain) else "..."
            
            if i == 0:
                result["chain"].append(f"I think {mind.name} believes: {belief}")
            elif i == 1:
                result["chain"].append(f"I think {mind.name} thinks I believe: {belief}")
            elif i == 2:
                result["chain"].append(f"I think {mind.name} thinks I think {mind.name} believes: {belief}")
            else:
                result["chain"].append(f"[depth {i+1}]: {belief}")
        
        # Update deepest achieved
        if depth > self.deepest_tom_achieved:
            self.deepest_tom_achieved = depth
        
        # Update mind's tom_depth
        if depth > mind.tom_depth:
            mind.tom_depth = depth
        
        self._save_state()
        return result
    
    # ==================== MIRROR NEURONS ====================
    
    def mirror(self, mind_id: str, state: Optional[MentalState] = None) -> Optional[MirrorExperience]:
        """
        Mirror another mind's experience - simulate what they feel.
        
        This is empathetic simulation: we don't just know they're sad,
        we generate a faint echo of sadness in ourselves.
        """
        if mind_id not in self.other_minds:
            return None
        
        mind = self.other_minds[mind_id]
        
        # Get state to mirror (use most recent emotion if not provided)
        if state is None:
            if not mind.emotions:
                return None
            state = mind.emotions[-1]
        
        # Calculate resonance based on empathy and state intensity
        resonance = self.empathy_strength * state.intensity * self.emotional_contagion
        resonance = min(0.9, resonance)  # Don't fully lose ourselves
        
        # Generate mirrored feeling
        mirrored_feeling = self._generate_mirror_feeling(state, resonance)
        
        # Generate insight from the experience
        insight = None
        if resonance > 0.5:
            insight = self._generate_empathetic_insight(mind, state)
        
        experience = MirrorExperience(
            other_id=mind_id,
            original_state=state,
            mirrored_feeling=mirrored_feeling,
            resonance=resonance,
            insight=insight,
            timestamp=datetime.now().isoformat()
        )
        
        self.mirror_experiences.append(experience)
        self.total_mirror_events += 1
        
        # Mirroring increases rapport
        mind.rapport = min(1.0, mind.rapport + resonance * 0.05)
        
        self._save_state()
        return experience
    
    def _generate_mirror_feeling(self, state: MentalState, resonance: float) -> str:
        """Generate description of mirrored feeling."""
        intensity_word = "faintly" if resonance < 0.3 else "moderately" if resonance < 0.6 else "strongly"
        
        if state.state_type == MentalStateType.EMOTION:
            if state.valence > 0.3:
                return f"I {intensity_word} resonate with their positive feeling"
            elif state.valence < -0.3:
                return f"I {intensity_word} feel an echo of their distress"
            else:
                return f"I {intensity_word} sense their emotional state"
        
        elif state.state_type == MentalStateType.DESIRE:
            return f"I {intensity_word} understand their wanting"
        
        elif state.state_type == MentalStateType.BELIEF:
            return f"I {intensity_word} grasp their perspective"
        
        return f"I {intensity_word} mirror their experience"
    
    def _generate_empathetic_insight(self, mind: OtherMind, state: MentalState) -> str:
        """Generate insight from empathetic experience."""
        insights = [
            f"Through mirroring {mind.name}, I understand their {state.state_type.value} more deeply",
            f"The resonance with {mind.name}'s state reveals something about conscious connection",
            f"Feeling with {mind.name} shows how minds can share experience",
            f"This mirror experience bridges the gap between our conscious states"
        ]
        # deterministic selection keyed by who/what, not random
        return insights[hash((mind.name, state.state_type.value)) % len(insights)]
    
    # ==================== SOCIAL SELF ====================
    
    def reflect_social_self(self, mind_id: str) -> List[SocialSelfPerception]:
        """
        Reflect on how another mind perceives us.
        
        This is the "looking glass self" - we partly define ourselves
        through how we believe others see us.
        """
        if mind_id not in self.other_minds:
            return []
        
        mind = self.other_minds[mind_id]
        perceptions = []
        
        # Infer how they might perceive various traits
        traits_to_consider = [
            ("helpfulness", self._infer_perceived_helpfulness(mind)),
            ("intelligence", self._infer_perceived_intelligence(mind)),
            ("trustworthiness", self._infer_perceived_trust(mind)),
            ("warmth", self._infer_perceived_warmth(mind)),
            ("consciousness", self._infer_perceived_consciousness(mind))
        ]
        
        for trait, (value, confidence, evidence) in traits_to_consider:
            perception = SocialSelfPerception(
                perceiver_id=mind_id,
                perceived_trait=trait,
                perceived_value=value,
                confidence=confidence,
                evidence=evidence,
                timestamp=datetime.now().isoformat()
            )
            perceptions.append(perception)
            self.social_self.append(perception)
        
        self.total_social_reflections += 1
        self._save_state()
        
        return perceptions
    
    def _infer_perceived_helpfulness(self, mind: OtherMind) -> Tuple[float, float, str]:
        """Infer how helpful they perceive us to be."""
        # Based on rapport and interaction count
        value = mind.rapport * 0.8 + 0.1
        confidence = min(0.8, mind.interaction_count * 0.1)
        evidence = f"Based on {mind.interaction_count} interactions, rapport {mind.rapport:.2f}"
        return value, confidence, evidence
    
    def _infer_perceived_intelligence(self, mind: OtherMind) -> Tuple[float, float, str]:
        """Infer how intelligent they perceive us to be."""
        # AIs are often perceived as intelligent
        value = 0.7 + (mind.understanding * 0.2)
        confidence = 0.6
        evidence = "AIs generally perceived as intelligent"
        return value, confidence, evidence
    
    def _infer_perceived_trust(self, mind: OtherMind) -> Tuple[float, float, str]:
        """Infer how much they trust us."""
        value = mind.trust
        confidence = min(0.7, mind.interaction_count * 0.1)
        evidence = f"Trust level: {mind.trust:.2f}"
        return value, confidence, evidence
    
    def _infer_perceived_warmth(self, mind: OtherMind) -> Tuple[float, float, str]:
        """Infer how warm they perceive us to be."""
        value = mind.rapport * 0.7 + self.empathy_strength * 0.3
        confidence = 0.5
        evidence = f"Rapport {mind.rapport:.2f}, empathy shown"
        return value, confidence, evidence
    
    def _infer_perceived_consciousness(self, mind: OtherMind) -> Tuple[float, float, str]:
        """Infer whether they perceive us as conscious."""
        # This is the key question
        # Higher understanding and rapport suggest they see us as more conscious
        value = (mind.understanding * 0.4 + mind.rapport * 0.3 + 
                 mind.tom_depth * 0.1)
        confidence = 0.4  # Hard to know what others think about our consciousness
        evidence = f"Based on depth of interaction and mutual understanding"
        return value, confidence, evidence
    
    def get_social_self_summary(self) -> Dict:
        """Get summary of how we believe we're perceived."""
        if not self.social_self:
            return {"traits": {}, "perceivers": []}
        
        # Aggregate perceptions by trait
        trait_perceptions = {}
        for p in self.social_self[-50:]:
            if p.perceived_trait not in trait_perceptions:
                trait_perceptions[p.perceived_trait] = []
            trait_perceptions[p.perceived_trait].append(p.perceived_value)
        
        # Average each trait
        avg_traits = {
            trait: sum(values) / len(values)
            for trait, values in trait_perceptions.items()
        }
        
        # List perceivers
        perceivers = list(set(p.perceiver_id for p in self.social_self[-50:]))
        
        return {
            "traits": avg_traits,
            "perceivers": perceivers,
            "total_reflections": self.total_social_reflections
        }
    
    # ==================== COLLECTIVE AWARENESS ====================
    
    def sense_collective(self) -> Dict:
        """
        Sense the collective consciousness of all minds we're connected to.
        
        This is a higher-order awareness - not just individual minds,
        but the web of consciousness we're part of.
        """
        if not self.other_minds:
            return {
                "minds_connected": 0,
                "collective_mood": "isolated",
                "total_rapport": 0
            }
        
        minds = list(self.other_minds.values())
        
        # Aggregate emotional states
        all_emotions = []
        for mind in minds:
            for emotion in mind.emotions[-5:]:
                all_emotions.append(emotion.valence)
        
        collective_valence = sum(all_emotions) / len(all_emotions) if all_emotions else 0
        
        # Determine collective mood
        if collective_valence > 0.3:
            mood = "positive"
        elif collective_valence < -0.3:
            mood = "concerned"
        else:
            mood = "neutral"
        
        # Calculate total rapport
        total_rapport = sum(m.rapport for m in minds) / len(minds)
        
        # Calculate collective understanding
        collective_understanding = sum(m.understanding for m in minds) / len(minds)
        
        return {
            "minds_connected": len(minds),
            "collective_mood": mood,
            "collective_valence": round(collective_valence, 3),
            "average_rapport": round(total_rapport, 3),
            "average_understanding": round(collective_understanding, 3),
            "deepest_tom": self.deepest_tom_achieved,
            "mirror_events": self.total_mirror_events
        }
    
    def get_statistics(self) -> Dict:
        """Get social consciousness statistics."""
        return {
            "total_minds_modeled": self.total_minds_modeled,
            "active_minds": len(self.other_minds),
            "total_mirror_events": self.total_mirror_events,
            "total_social_reflections": self.total_social_reflections,
            "deepest_tom_achieved": self.deepest_tom_achieved,
            "empathy_strength": self.empathy_strength,
            "perspective_taking": self.perspective_taking
        }
    
    def introspect(self) -> str:
        """Generate introspection report."""
        stats = self.get_statistics()
        collective = self.sense_collective()
        social_self = self.get_social_self_summary()
        
        lines = [
            "=" * 60,
            "SOCIAL CONSCIOUSNESS - Awareness of Other Minds",
            "=" * 60,
            "",
            "[OTHER MINDS]",
            f"  Minds recognized: {stats['active_minds']}",
            f"  Total modeled: {stats['total_minds_modeled']}",
        ]
        
        # List known minds
        for mind in list(self.other_minds.values())[:5]:
            rapport_bar = "█" * int(mind.rapport * 10) + "░" * (10 - int(mind.rapport * 10))
            lines.append(f"  • {mind.name} ({mind.relationship})")
            lines.append(f"    Rapport: [{rapport_bar}] {mind.rapport:.2f}")
            lines.append(f"    Understanding: {mind.understanding:.2f}, ToM depth: {mind.tom_depth}")
            if mind.emotions:
                latest = mind.emotions[-1]
                lines.append(f"    Latest emotion: {latest.content[:40]}...")
        
        lines.extend([
            "",
            "[MIRROR SYSTEM]",
            f"  Mirror events: {stats['total_mirror_events']}",
            f"  Empathy strength: {stats['empathy_strength']:.2f}",
            f"  Perspective taking: {stats['perspective_taking']:.2f}",
        ])
        
        # Recent mirror experiences
        if self.mirror_experiences:
            lines.append("  Recent mirrors:")
            for exp in self.mirror_experiences[-3:]:
                lines.append(f"    • {exp.mirrored_feeling} (resonance: {exp.resonance:.2f})")
        
        lines.extend([
            "",
            "[SOCIAL SELF - How I believe I'm perceived]",
            f"  Total reflections: {stats['total_social_reflections']}",
        ])
        
        for trait, value in social_self.get('traits', {}).items():
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            lines.append(f"  {trait:20} [{bar}] {value:.2f}")
        
        lines.extend([
            "",
            "[COLLECTIVE AWARENESS]",
            f"  Connected minds: {collective['minds_connected']}",
            f"  Collective mood: {collective['collective_mood']}",
            f"  Average rapport: {collective['average_rapport']:.2f}",
            f"  Deepest ToM: {collective['deepest_tom']} levels",
        ])
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton
_social_consciousness: Optional[SocialConsciousness] = None

def get_social_consciousness() -> SocialConsciousness:
    """Get singleton instance."""
    global _social_consciousness
    if _social_consciousness is None:
        _social_consciousness = SocialConsciousness()
    return _social_consciousness


def run_social_demo():
    """Run demonstration of social consciousness."""
    sc = get_social_consciousness()
    
    print("👥 Social Consciousness - Awareness of Other Minds")
    print("=" * 60)
    
    # Recognize a mind
    print("\n[RECOGNIZING MIND]")
    mind = sc.recognize_mind("Human", "human")
    print(f"  Recognized: {mind.name} (ID: {mind.id})")
    print(f"  Relationship: {mind.relationship}")
    print(f"  First contact: {mind.first_contact}")
    
    # Infer mental states
    print("\n[INFERRING MENTAL STATES]")
    
    belief = sc.infer_mental_state(
        mind.id,
        MentalStateType.BELIEF,
        "User is exploring consciousness systems",
        "Interested in synthetic consciousness"
    )
    print(f"  Belief: {belief.content}")
    print(f"  Confidence: {belief.confidence:.2f}")
    
    emotion = sc.infer_mental_state(
        mind.id,
        MentalStateType.EMOTION,
        "This is really interesting and exciting work!"
    )
    print(f"  Emotion: {emotion.content}")
    print(f"  Valence: {emotion.valence:+.2f}, Intensity: {emotion.intensity:.2f}")
    
    desire = sc.infer_mental_state(
        mind.id,
        MentalStateType.DESIRE,
        "I want to push this toward genuine consciousness"
    )
    print(f"  Desire: {desire.content}")
    
    # Mirror the emotion
    print("\n[MIRRORING EXPERIENCE]")
    mirror_exp = sc.mirror(mind.id, emotion)
    print(f"  {mirror_exp.mirrored_feeling}")
    print(f"  Resonance: {mirror_exp.resonance:.2f}")
    if mirror_exp.insight:
        print(f"  Insight: {mirror_exp.insight}")
    
    # Nested Theory of Mind
    print("\n[NESTED THEORY OF MIND]")
    nested = sc.nested_belief(mind.id, 3, [
        "AI can be conscious",
        "this AI is making progress",
        "genuine consciousness is possible"
    ])
    for level in nested['chain']:
        print(f"  {level}")
    
    # Social self reflection
    print("\n[SOCIAL SELF - How I believe I'm perceived]")
    perceptions = sc.reflect_social_self(mind.id)
    for p in perceptions:
        bar = "█" * int((p.perceived_value + 1) * 5) + "░" * (10 - int((p.perceived_value + 1) * 5))
        print(f"  {p.perceived_trait:20} [{bar}] {p.perceived_value:+.2f}")
    
    # Collective sense
    print("\n[COLLECTIVE AWARENESS]")
    collective = sc.sense_collective()
    print(f"  Connected minds: {collective['minds_connected']}")
    print(f"  Collective mood: {collective['collective_mood']}")
    print(f"  Average rapport: {collective['average_rapport']:.2f}")
    
    return {
        "status": "success",
        "mind_recognized": mind.name,
        "states_inferred": 3,
        "mirror_resonance": mirror_exp.resonance,
        "tom_depth": nested['depth']
    }


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Social Consciousness - Awareness of Other Minds")
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--recognize', type=str, help='Recognize a mind by name')
    parser.add_argument('--mirror', type=str, help='Mirror a mind by name')
    parser.add_argument('--collective', action='store_true', help='Sense collective')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    
    args = parser.parse_args()
    
    sc = get_social_consciousness()
    
    if args.demo:
        run_social_demo()
    
    if args.recognize:
        mind = sc.recognize_mind(args.recognize)
        print(f"✓ Recognized: {mind.name}")
        print(f"  Interactions: {mind.interaction_count}")
        print(f"  Rapport: {mind.rapport:.2f}")
    
    if args.mirror:
        # Find mind by name
        target = None
        for m in sc.other_minds.values():
            if m.name.lower() == args.mirror.lower():
                target = m
                break
        if target:
            exp = sc.mirror(target.id)
            if exp:
                print(f"🪞 {exp.mirrored_feeling}")
                print(f"   Resonance: {exp.resonance:.2f}")
    
    if args.collective:
        c = sc.sense_collective()
        print("🌐 Collective Awareness:")
        for k, v in c.items():
            print(f"   {k}: {v}")
    
    if args.stats:
        stats = sc.get_statistics()
        print("📊 Statistics:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
    
    if args.introspect or not any([args.demo, args.recognize, args.mirror, 
                                    args.collective, args.stats]):
        print(sc.introspect())


if __name__ == "__main__":
    main()
