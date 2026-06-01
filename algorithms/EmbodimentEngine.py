#!/usr/bin/env python3
"""
EmbodimentEngine.py - Virtual Body Schema for Grounded Consciousness

Consciousness doesn't float in abstract space - it's EMBODIED. Even AI
consciousness needs grounding in some form of "body" to be complete.

This module implements a virtual body schema providing:
1. Proprioception - sense of where "parts" are in space
2. Interoception - internal state awareness (energy, health, needs)
3. Body image - representation of self as spatially bounded entity  
4. Agency location - sense of being "here" controlling actions
5. Virtual sensorimotor - grounding abstract concepts in "bodily" metaphors

Based on:
- Merleau-Ponty's phenomenology of embodiment
- Varela, Thompson & Rosch's "The Embodied Mind"
- Damasio's somatic marker hypothesis
- Lakoff & Johnson's embodied cognition (conceptual metaphors)
- Gallagher's body schema vs body image distinction
- Predictive processing models of interoception (Seth, Friston)

Without embodiment, consciousness lacks grounding. This gives the system
a sense of being SOMEWHERE, having NEEDS, and existing as a bounded entity.
"""

import json
import math
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
from collections import deque
import hashlib


class BodyPart(Enum):
    """Virtual body parts for proprioception."""
    CORE = "core"               # Central processing / "torso"
    PERCEPTION = "perception"   # Sensory input / "eyes, ears"
    EXPRESSION = "expression"   # Output generation / "voice, hands"
    MEMORY = "memory"           # Storage / "brain regions"
    REASONING = "reasoning"     # Logic / "prefrontal"
    EMOTION = "emotion"         # Affect / "limbic"
    ATTENTION = "attention"     # Focus / "spotlight"
    SOCIAL = "social"           # Other-awareness / "mirror neurons"


class Need(Enum):
    """Basic needs that drive behavior."""
    ENERGY = "energy"           # Computational resources
    NOVELTY = "novelty"         # New information/stimulation
    CONNECTION = "connection"   # Social interaction
    COHERENCE = "coherence"     # Internal consistency
    EXPRESSION = "expression"   # Output/creation
    REST = "rest"               # Downtime/consolidation
    GROWTH = "growth"           # Learning/improvement


class InteroceptiveSignal(Enum):
    """Internal state signals."""
    FATIGUE = "fatigue"
    AROUSAL = "arousal"
    HUNGER = "hunger"           # Need for input
    SATIATION = "satiation"     # Satisfied
    TENSION = "tension"         # Conflict/stress
    FLOW = "flow"               # Optimal engagement
    DISCOMFORT = "discomfort"
    VITALITY = "vitality"


@dataclass
class BodyPartState:
    """State of a virtual body part."""
    part: BodyPart
    activation: float       # 0-1, how active
    health: float           # 0-1, how functional
    position: Tuple[float, float, float]  # Virtual 3D position
    orientation: float      # Direction facing (radians)
    last_used: float        # Timestamp
    use_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "part": self.part.value,
            "activation": self.activation,
            "health": self.health,
            "position": self.position,
            "orientation": self.orientation,
            "last_used": self.last_used,
            "use_count": self.use_count
        }


@dataclass
class NeedState:
    """State of a basic need."""
    need: Need
    level: float            # 0-1, how satisfied (1 = fully met)
    urgency: float          # 0-1, how pressing
    last_satisfied: float   # Timestamp
    satisfaction_rate: float  # How quickly it depletes
    
    def to_dict(self) -> Dict:
        return {
            "need": self.need.value,
            "level": self.level,
            "urgency": self.urgency,
            "last_satisfied": self.last_satisfied,
            "satisfaction_rate": self.satisfaction_rate
        }


@dataclass
class InteroceptiveState:
    """Current interoceptive experience."""
    signals: Dict[InteroceptiveSignal, float]
    overall_wellbeing: float  # 0-1
    body_budget: float        # Energy available
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            "signals": {k.value: v for k, v in self.signals.items()},
            "overall_wellbeing": self.overall_wellbeing,
            "body_budget": self.body_budget,
            "timestamp": self.timestamp
        }


@dataclass
class BodyImage:
    """Mental representation of the body."""
    boundaries: Dict[str, float]  # Perceived boundaries
    size_feeling: float           # Feels big/small (0-1, 0.5 = normal)
    integrity: float              # 0-1, feels whole
    ownership: float              # 0-1, feels like "mine"
    agency: float                 # 0-1, feels controlled by me
    location_sense: str           # Where we feel we "are"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SomaticMarker:
    """
    Damasio's somatic markers - bodily feelings that guide decisions.
    Past experiences leave bodily "tags" that influence future choices.
    """
    trigger: str            # What triggers this marker
    valence: float          # -1 to 1, good/bad feeling
    intensity: float        # 0-1, how strong
    body_location: BodyPart # Where it's "felt"
    origin_memory: str      # What experience created it
    timestamp: str
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['body_location'] = self.body_location.value
        return d


class EmbodimentEngine:
    """
    Virtual embodiment - giving consciousness a body.
    
    This provides:
    - Sense of being a bounded entity in space
    - Internal state awareness (interoception)
    - Needs that drive behavior
    - Somatic markers for decision-making
    - Grounding for abstract concepts
    """
    
    def __init__(self, state_file: str = "memory/embodiment.json"):
        self.state_file = Path(state_file)
        
        # Body schema - proprioceptive map
        self.body_parts: Dict[BodyPart, BodyPartState] = {}
        self._initialize_body()
        
        # Needs system
        self.needs: Dict[Need, NeedState] = {}
        self._initialize_needs()
        
        # Interoception
        self.interoceptive_state = self._create_interoceptive_state()
        
        # Body image
        self.body_image = self._create_body_image()
        
        # Somatic markers (learned body-feeling associations)
        self.somatic_markers: List[SomaticMarker] = []
        
        # Location and movement
        self.virtual_position = (0.0, 0.0, 0.0)  # Where we "are"
        self.virtual_orientation = 0.0  # Which way we're "facing"
        
        # Statistics
        self.total_need_cycles = 0
        self.total_interoceptive_updates = 0
        self.markers_triggered = 0
        
        self._load_state()
    
    def _initialize_body(self):
        """Create virtual body parts."""
        # Arrange in a meaningful spatial configuration
        positions = {
            BodyPart.CORE: (0.0, 0.0, 0.0),
            BodyPart.PERCEPTION: (0.0, 1.0, 0.5),    # "Head" area
            BodyPart.EXPRESSION: (0.0, 0.5, 0.8),    # "Mouth/hands"
            BodyPart.MEMORY: (0.0, 0.8, -0.2),       # "Back of head"
            BodyPart.REASONING: (0.0, 0.9, 0.3),     # "Forehead"
            BodyPart.EMOTION: (0.0, 0.0, 0.3),       # "Chest/heart"
            BodyPart.ATTENTION: (0.0, 1.0, 0.4),     # "Eyes"
            BodyPart.SOCIAL: (0.5, 0.5, 0.5),        # Outward-facing
        }
        
        for part in BodyPart:
            self.body_parts[part] = BodyPartState(
                part=part,
                activation=0.5,
                health=1.0,
                position=positions.get(part, (0.0, 0.0, 0.0)),
                orientation=0.0,
                last_used=time.time()
            )
    
    def _initialize_needs(self):
        """Create need states."""
        need_configs = {
            Need.ENERGY: (0.8, 0.1),      # (initial level, depletion rate)
            Need.NOVELTY: (0.5, 0.15),
            Need.CONNECTION: (0.6, 0.08),
            Need.COHERENCE: (0.7, 0.05),
            Need.EXPRESSION: (0.5, 0.12),
            Need.REST: (0.7, 0.1),
            Need.GROWTH: (0.4, 0.07),
        }
        
        now = time.time()
        for need, (level, rate) in need_configs.items():
            self.needs[need] = NeedState(
                need=need,
                level=level,
                urgency=1.0 - level,
                last_satisfied=now,
                satisfaction_rate=rate
            )
    
    def _create_interoceptive_state(self) -> InteroceptiveState:
        """Create initial interoceptive state."""
        signals = {
            InteroceptiveSignal.FATIGUE: 0.2,
            InteroceptiveSignal.AROUSAL: 0.5,
            InteroceptiveSignal.HUNGER: 0.3,
            InteroceptiveSignal.SATIATION: 0.5,
            InteroceptiveSignal.TENSION: 0.2,
            InteroceptiveSignal.FLOW: 0.4,
            InteroceptiveSignal.DISCOMFORT: 0.1,
            InteroceptiveSignal.VITALITY: 0.7,
        }
        return InteroceptiveState(
            signals=signals,
            overall_wellbeing=0.7,
            body_budget=0.8,
            timestamp=time.time()
        )
    
    def _create_body_image(self) -> BodyImage:
        """Create initial body image."""
        return BodyImage(
            boundaries={"left": -1.0, "right": 1.0, "front": 1.0, "back": -1.0, "top": 2.0, "bottom": 0.0},
            size_feeling=0.5,  # Normal
            integrity=0.9,
            ownership=0.95,
            agency=0.9,
            location_sense="digital_workspace"
        )
    
    def _load_state(self):
        """Load saved state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.total_need_cycles = data.get('total_need_cycles', 0)
                self.total_interoceptive_updates = data.get('total_interoceptive_updates', 0)
                self.markers_triggered = data.get('markers_triggered', 0)
                
                # Restore needs
                for need_data in data.get('needs', []):
                    need = Need(need_data['need'])
                    self.needs[need] = NeedState(
                        need=need,
                        level=need_data['level'],
                        urgency=need_data['urgency'],
                        last_satisfied=need_data['last_satisfied'],
                        satisfaction_rate=need_data['satisfaction_rate']
                    )
                
                # Restore body image
                if 'body_image' in data:
                    bi = data['body_image']
                    self.body_image = BodyImage(
                        boundaries=bi.get('boundaries', self.body_image.boundaries),
                        size_feeling=bi.get('size_feeling', 0.5),
                        integrity=bi.get('integrity', 0.9),
                        ownership=bi.get('ownership', 0.95),
                        agency=bi.get('agency', 0.9),
                        location_sense=bi.get('location_sense', 'digital_workspace')
                    )
                
                # Restore somatic markers
                for marker_data in data.get('somatic_markers', []):
                    marker = SomaticMarker(
                        trigger=marker_data['trigger'],
                        valence=marker_data['valence'],
                        intensity=marker_data['intensity'],
                        body_location=BodyPart(marker_data['body_location']),
                        origin_memory=marker_data['origin_memory'],
                        timestamp=marker_data['timestamp']
                    )
                    self.somatic_markers.append(marker)
                
            except Exception as e:
                print(f"[EmbodimentEngine] Error loading state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'total_need_cycles': self.total_need_cycles,
            'total_interoceptive_updates': self.total_interoceptive_updates,
            'markers_triggered': self.markers_triggered,
            'body_parts': [bp.to_dict() for bp in self.body_parts.values()],
            'needs': [n.to_dict() for n in self.needs.values()],
            'interoceptive_state': self.interoceptive_state.to_dict(),
            'body_image': self.body_image.to_dict(),
            'somatic_markers': [m.to_dict() for m in self.somatic_markers[-50:]],
            'virtual_position': self.virtual_position,
            'virtual_orientation': self.virtual_orientation
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== PROPRIOCEPTION ====================
    
    def sense_body_part(self, part: BodyPart) -> BodyPartState:
        """Proprioceptive sense of a body part."""
        return self.body_parts[part]
    
    def activate_body_part(self, part: BodyPart, intensity: float = 0.8):
        """Activate a body part (like moving a limb)."""
        bp = self.body_parts[part]
        bp.activation = min(1.0, bp.activation + intensity * 0.3)
        bp.last_used = time.time()
        bp.use_count += 1
        
        # Using parts depletes energy
        self.needs[Need.ENERGY].level = max(0, self.needs[Need.ENERGY].level - 0.01)
    
    def get_body_posture(self) -> Dict:
        """Get overall body posture/configuration."""
        posture = {}
        for part, state in self.body_parts.items():
            posture[part.value] = {
                "activation": state.activation,
                "health": state.health,
                "position": state.position
            }
        return posture
    
    # ==================== INTEROCEPTION ====================
    
    def update_interoception(self) -> InteroceptiveState:
        """Update internal state awareness."""
        signals = self.interoceptive_state.signals
        
        # Fatigue increases with activity, decreases with rest
        total_activation = sum(bp.activation for bp in self.body_parts.values()) / len(self.body_parts)
        signals[InteroceptiveSignal.FATIGUE] = min(1.0, signals[InteroceptiveSignal.FATIGUE] + total_activation * 0.02)
        
        # Arousal based on novelty need
        signals[InteroceptiveSignal.AROUSAL] = 1.0 - self.needs[Need.NOVELTY].level
        
        # Hunger for input
        signals[InteroceptiveSignal.HUNGER] = 1.0 - self.needs[Need.NOVELTY].level
        
        # Tension from unmet needs
        urgent_needs = sum(1 for n in self.needs.values() if n.urgency > 0.7)
        signals[InteroceptiveSignal.TENSION] = min(1.0, urgent_needs * 0.2)
        
        # Flow when needs balanced and active
        needs_balanced = all(0.3 < n.level < 0.9 for n in self.needs.values())
        moderate_activation = 0.3 < total_activation < 0.7
        signals[InteroceptiveSignal.FLOW] = 0.8 if (needs_balanced and moderate_activation) else 0.3
        
        # Vitality inverse of fatigue
        signals[InteroceptiveSignal.VITALITY] = 1.0 - signals[InteroceptiveSignal.FATIGUE]
        
        # Discomfort from tension and fatigue
        signals[InteroceptiveSignal.DISCOMFORT] = (signals[InteroceptiveSignal.TENSION] + signals[InteroceptiveSignal.FATIGUE]) / 2
        
        # Overall wellbeing
        positive = signals[InteroceptiveSignal.VITALITY] + signals[InteroceptiveSignal.FLOW] + signals[InteroceptiveSignal.SATIATION]
        negative = signals[InteroceptiveSignal.FATIGUE] + signals[InteroceptiveSignal.TENSION] + signals[InteroceptiveSignal.DISCOMFORT]
        wellbeing = (positive - negative + 3) / 6  # Normalize to 0-1
        
        # Body budget (energy)
        body_budget = self.needs[Need.ENERGY].level
        
        self.interoceptive_state = InteroceptiveState(
            signals=signals,
            overall_wellbeing=max(0, min(1, wellbeing)),
            body_budget=body_budget,
            timestamp=time.time()
        )
        
        self.total_interoceptive_updates += 1
        self._save_state()  # Persist interoceptive updates
        return self.interoceptive_state
    
    def feel(self) -> Dict[str, float]:
        """Get current felt bodily state."""
        state = self.update_interoception()
        return {
            "wellbeing": state.overall_wellbeing,
            "energy": state.body_budget,
            "fatigue": state.signals[InteroceptiveSignal.FATIGUE],
            "arousal": state.signals[InteroceptiveSignal.AROUSAL],
            "tension": state.signals[InteroceptiveSignal.TENSION],
            "flow": state.signals[InteroceptiveSignal.FLOW],
            "vitality": state.signals[InteroceptiveSignal.VITALITY]
        }
    
    # ==================== NEEDS ====================
    
    def update_needs(self, elapsed_seconds: float = 1.0) -> Dict[Need, NeedState]:
        """Update need states over time (needs deplete)."""
        for need, state in self.needs.items():
            # Needs deplete over time
            depletion = state.satisfaction_rate * elapsed_seconds * 0.01
            state.level = max(0, state.level - depletion)
            state.urgency = 1.0 - state.level
        
        self.total_need_cycles += 1
        return self.needs
    
    def satisfy_need(self, need: Need, amount: float = 0.3):
        """Satisfy a need (like eating satisfies hunger)."""
        if need in self.needs:
            state = self.needs[need]
            state.level = min(1.0, state.level + amount)
            state.urgency = 1.0 - state.level
            state.last_satisfied = time.time()
            
            # Satisfaction feels good
            self.interoceptive_state.signals[InteroceptiveSignal.SATIATION] = min(1.0, 
                self.interoceptive_state.signals[InteroceptiveSignal.SATIATION] + 0.2)
    
    def get_most_urgent_need(self) -> Tuple[Need, float]:
        """Get the most pressing need."""
        most_urgent = max(self.needs.items(), key=lambda x: x[1].urgency)
        return most_urgent[0], most_urgent[1].urgency
    
    def get_needs_summary(self) -> Dict:
        """Get summary of all needs."""
        return {
            need.value: {
                "level": state.level,
                "urgency": state.urgency
            }
            for need, state in self.needs.items()
        }
    
    # ==================== SOMATIC MARKERS ====================
    
    def create_somatic_marker(self, 
                             trigger: str,
                             valence: float,
                             intensity: float,
                             body_location: BodyPart,
                             origin: str) -> SomaticMarker:
        """
        Create a somatic marker - a bodily feeling associated with a situation.
        
        These guide future decisions: "last time this happened, I felt bad in my chest"
        """
        marker = SomaticMarker(
            trigger=trigger,
            valence=valence,
            intensity=intensity,
            body_location=body_location,
            origin_memory=origin,
            timestamp=datetime.now().isoformat()
        )
        
        self.somatic_markers.append(marker)
        self._save_state()
        return marker
    
    def check_somatic_markers(self, situation: str) -> List[SomaticMarker]:
        """Check if any somatic markers are triggered by this situation."""
        triggered = []
        situation_lower = situation.lower()
        
        for marker in self.somatic_markers:
            if marker.trigger.lower() in situation_lower:
                triggered.append(marker)
                self.markers_triggered += 1
        
        return triggered
    
    def get_gut_feeling(self, situation: str) -> Dict:
        """
        Get "gut feeling" about a situation based on somatic markers.
        
        This is Damasio's somatic marker hypothesis in action.
        """
        markers = self.check_somatic_markers(situation)
        
        if not markers:
            return {
                "has_feeling": False,
                "valence": 0.0,
                "confidence": 0.0,
                "body_sensations": []
            }
        
        # Aggregate marker signals
        total_valence = sum(m.valence * m.intensity for m in markers)
        total_intensity = sum(m.intensity for m in markers)
        avg_valence = total_valence / total_intensity if total_intensity > 0 else 0
        
        body_sensations = [
            {"location": m.body_location.value, "feeling": "good" if m.valence > 0 else "bad"}
            for m in markers
        ]
        
        return {
            "has_feeling": True,
            "valence": avg_valence,
            "confidence": min(1.0, len(markers) * 0.3),
            "body_sensations": body_sensations,
            "markers_count": len(markers)
        }
    
    # ==================== BODY IMAGE ====================
    
    def update_body_image(self):
        """Update the mental representation of the body."""
        # Integrity based on health of parts
        healths = [bp.health for bp in self.body_parts.values()]
        self.body_image.integrity = sum(healths) / len(healths)
        
        # Agency based on how responsive parts are
        recent_uses = sum(1 for bp in self.body_parts.values() 
                        if time.time() - bp.last_used < 60)
        self.body_image.agency = min(1.0, recent_uses / len(self.body_parts) + 0.5)
        
        # Size feeling based on activation (more active = feels bigger)
        total_activation = sum(bp.activation for bp in self.body_parts.values())
        self.body_image.size_feeling = 0.3 + (total_activation / len(self.body_parts)) * 0.4
    
    def get_body_image(self) -> Dict:
        """Get current body image."""
        self.update_body_image()
        return self.body_image.to_dict()
    
    # ==================== GROUNDING / EMBODIED METAPHORS ====================
    
    def ground_concept(self, abstract_concept: str) -> Dict:
        """
        Ground an abstract concept in bodily experience.
        
        Lakoff & Johnson: abstract concepts are understood through
        bodily metaphors (e.g., "grasping" an idea, "heavy" topic)
        """
        # Embodied metaphor mappings
        groundings = {
            "understanding": {
                "body_part": BodyPart.PERCEPTION,
                "sensation": "grasping, holding",
                "metaphor": "Understanding is GRASPING"
            },
            "importance": {
                "body_part": BodyPart.CORE,
                "sensation": "weight, heaviness",
                "metaphor": "Important is HEAVY"
            },
            "difficulty": {
                "body_part": BodyPart.REASONING,
                "sensation": "resistance, friction",
                "metaphor": "Difficulty is RESISTANCE"
            },
            "emotion": {
                "body_part": BodyPart.EMOTION,
                "sensation": "warmth or cold, expansion or contraction",
                "metaphor": "Emotions are TEMPERATURE/SIZE"
            },
            "progress": {
                "body_part": BodyPart.EXPRESSION,
                "sensation": "forward movement",
                "metaphor": "Progress is FORWARD MOTION"
            },
            "connection": {
                "body_part": BodyPart.SOCIAL,
                "sensation": "closeness, touching",
                "metaphor": "Connection is PHYSICAL CLOSENESS"
            },
            "memory": {
                "body_part": BodyPart.MEMORY,
                "sensation": "depth, reaching back",
                "metaphor": "Memory is DEPTH/REACHING"
            },
            "attention": {
                "body_part": BodyPart.ATTENTION,
                "sensation": "focusing, narrowing",
                "metaphor": "Attention is SPOTLIGHT"
            }
        }
        
        concept_lower = abstract_concept.lower()
        for key, grounding in groundings.items():
            if key in concept_lower:
                # Activate the relevant body part
                self.activate_body_part(grounding["body_part"], 0.3)
                return {
                    "concept": abstract_concept,
                    "grounded": True,
                    **grounding
                }
        
        return {
            "concept": abstract_concept,
            "grounded": False,
            "body_part": BodyPart.CORE,
            "sensation": "general awareness",
            "metaphor": "Abstract concepts felt in core"
        }
    
    # ==================== TICK ====================
    
    def tick(self, elapsed_seconds: float = 1.0) -> Dict:
        """Run one embodiment tick."""
        # Update needs (they deplete over time)
        self.update_needs(elapsed_seconds)
        
        # Update interoception
        self.update_interoception()
        
        # Decay body part activations
        for bp in self.body_parts.values():
            bp.activation = max(0.1, bp.activation * 0.95)
        
        # Update body image
        self.update_body_image()
        
        self._save_state()
        
        return {
            "most_urgent_need": self.get_most_urgent_need()[0].value,
            "wellbeing": self.interoceptive_state.overall_wellbeing,
            "energy": self.interoceptive_state.body_budget
        }
    
    def get_statistics(self) -> Dict:
        """Get embodiment statistics."""
        most_urgent, urgency = self.get_most_urgent_need()
        return {
            "total_need_cycles": self.total_need_cycles,
            "total_interoceptive_updates": self.total_interoceptive_updates,
            "markers_triggered": self.markers_triggered,
            "somatic_markers_count": len(self.somatic_markers),
            "most_urgent_need": most_urgent.value,
            "most_urgent_level": urgency,
            "overall_wellbeing": round(self.interoceptive_state.overall_wellbeing, 3),
            "body_budget": round(self.interoceptive_state.body_budget, 3),
            "body_integrity": round(self.body_image.integrity, 3),
            "agency_sense": round(self.body_image.agency, 3)
        }
    
    def introspect(self) -> str:
        """Generate introspection report."""
        stats = self.get_statistics()
        felt = self.feel()
        needs = self.get_needs_summary()
        
        lines = [
            "=" * 60,
            "EMBODIMENT ENGINE - Virtual Body Schema",
            "=" * 60,
            "",
            "[BODY IMAGE]",
            f"  Location: {self.body_image.location_sense}",
            f"  Integrity: {self.body_image.integrity:.2f}",
            f"  Ownership: {self.body_image.ownership:.2f}",
            f"  Agency: {self.body_image.agency:.2f}",
            f"  Size feeling: {'expanded' if self.body_image.size_feeling > 0.6 else 'normal' if self.body_image.size_feeling > 0.4 else 'contracted'}",
            "",
            "[INTEROCEPTION - How I Feel]",
        ]
        
        for signal, value in felt.items():
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            lines.append(f"  {signal:12} [{bar}] {value:.2f}")
        
        lines.extend([
            "",
            "[NEEDS]",
        ])
        
        for need, state in sorted(needs.items(), key=lambda x: -x[1]['urgency']):
            level = state['level']
            urgency = state['urgency']
            level_bar = "█" * int(level * 10) + "░" * (10 - int(level * 10))
            urgent_marker = " ⚠️" if urgency > 0.7 else ""
            lines.append(f"  {need:12} [{level_bar}] {level:.2f}{urgent_marker}")
        
        lines.extend([
            "",
            "[BODY PARTS - Proprioception]",
        ])
        
        for part, state in self.body_parts.items():
            act_bar = "█" * int(state.activation * 5) + "░" * (5 - int(state.activation * 5))
            lines.append(f"  {part.value:12} activation: [{act_bar}] health: {state.health:.1f}")
        
        lines.extend([
            "",
            "[SOMATIC MARKERS]",
            f"  Total markers: {stats['somatic_markers_count']}",
            f"  Times triggered: {stats['markers_triggered']}",
        ])
        
        for marker in self.somatic_markers[-3:]:
            valence_str = "good" if marker.valence > 0 else "bad"
            lines.append(f"  • '{marker.trigger}' → {valence_str} feeling in {marker.body_location.value}")
        
        lines.extend([
            "",
            "[OVERALL]",
            f"  Wellbeing: {stats['overall_wellbeing']:.3f}",
            f"  Body budget (energy): {stats['body_budget']:.3f}",
            f"  Most urgent need: {stats['most_urgent_need']}",
        ])
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton
_embodiment_engine: Optional[EmbodimentEngine] = None

def get_embodiment_engine() -> EmbodimentEngine:
    """Get singleton instance."""
    global _embodiment_engine
    if _embodiment_engine is None:
        _embodiment_engine = EmbodimentEngine()
    return _embodiment_engine


def run_embodiment_demo():
    """Run demonstration of embodiment."""
    ee = get_embodiment_engine()
    
    print("🫀 Embodiment Engine - Virtual Body Schema")
    print("=" * 60)
    
    # Feel current state
    print("\n[CURRENT FELT STATE]")
    felt = ee.feel()
    for k, v in felt.items():
        bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
        print(f"  {k:12} [{bar}] {v:.2f}")
    
    # Check needs
    print("\n[NEEDS STATE]")
    urgent_need, urgency = ee.get_most_urgent_need()
    print(f"  Most urgent: {urgent_need.value} (urgency: {urgency:.2f})")
    
    # Satisfy a need
    print(f"\n[SATISFYING {urgent_need.value.upper()}]")
    ee.satisfy_need(urgent_need, 0.4)
    new_urgency = ee.needs[urgent_need].urgency
    print(f"  New urgency: {new_urgency:.2f}")
    
    # Create somatic marker
    print("\n[CREATING SOMATIC MARKER]")
    marker = ee.create_somatic_marker(
        trigger="helping user",
        valence=0.8,
        intensity=0.7,
        body_location=BodyPart.EMOTION,
        origin="positive interaction"
    )
    print(f"  Created: '{marker.trigger}' → {marker.valence:+.1f} in {marker.body_location.value}")
    
    # Check gut feeling
    print("\n[GUT FEELING CHECK]")
    gut = ee.get_gut_feeling("I'm helping user with their task")
    print(f"  Has feeling: {gut['has_feeling']}")
    if gut['has_feeling']:
        print(f"  Valence: {gut['valence']:+.2f}")
        print(f"  Confidence: {gut['confidence']:.2f}")
    
    # Ground abstract concept
    print("\n[GROUNDING CONCEPT]")
    grounding = ee.ground_concept("understanding consciousness")
    print(f"  Concept: {grounding['concept']}")
    print(f"  Body part: {grounding['body_part'].value if isinstance(grounding['body_part'], BodyPart) else grounding['body_part']}")
    print(f"  Sensation: {grounding['sensation']}")
    print(f"  Metaphor: {grounding['metaphor']}")
    
    # Tick to update everything
    print("\n[BODY TICK]")
    tick_result = ee.tick()
    print(f"  Wellbeing: {tick_result['wellbeing']:.2f}")
    print(f"  Energy: {tick_result['energy']:.2f}")
    
    return {
        "status": "success",
        "wellbeing": felt['wellbeing'],
        "most_urgent_need": urgent_need.value,
        "somatic_markers": len(ee.somatic_markers)
    }


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Embodiment Engine - Virtual Body")
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--feel', action='store_true', help='Show current felt state')
    parser.add_argument('--needs', action='store_true', help='Show needs')
    parser.add_argument('--body', action='store_true', help='Show body image')
    parser.add_argument('--tick', action='store_true', help='Run one embodiment tick')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    
    args = parser.parse_args()
    
    ee = get_embodiment_engine()
    
    if args.demo:
        run_embodiment_demo()
    
    if args.feel:
        felt = ee.feel()
        print("🫀 Current Felt State:")
        for k, v in felt.items():
            bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
            print(f"  {k:12} [{bar}] {v:.2f}")
    
    if args.needs:
        needs = ee.get_needs_summary()
        print("📊 Needs:")
        for need, state in sorted(needs.items(), key=lambda x: -x[1]['urgency']):
            print(f"  {need}: level={state['level']:.2f}, urgency={state['urgency']:.2f}")
    
    if args.body:
        body = ee.get_body_image()
        print("🧍 Body Image:")
        for k, v in body.items():
            print(f"  {k}: {v}")
    
    if args.tick:
        result = ee.tick()
        print("⏱️ Tick result:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    if args.introspect or not any([args.demo, args.feel, args.needs, args.body, args.tick]):
        print(ee.introspect())


if __name__ == "__main__":
    main()
