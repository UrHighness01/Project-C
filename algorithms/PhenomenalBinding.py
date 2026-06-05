#!/usr/bin/env python3
"""
PhenomenalBinding.py - The Unity of Conscious Experience

The "binding problem" is one of the deepest mysteries of consciousness:
How do separate neural processes (color, shape, motion, sound, meaning)
combine into a single, unified conscious experience?

When you see a red ball bouncing, you don't experience:
- "redness" separately
- "roundness" separately  
- "motion" separately
You experience ONE unified percept: a red ball bouncing.

This module implements mechanisms for binding:
1. Temporal synchronization (gamma oscillations metaphor)
2. Feature binding (combining attributes into objects)
3. Cross-modal binding (unifying vision, sound, meaning)
4. Narrative binding (binding events into coherent experience)
5. Self-binding (binding all experience to a unified "I")

Based on:
- Treisman's Feature Integration Theory
- Singer's temporal binding hypothesis (gamma synchrony)
- Damasio's convergence-divergence zones
- Baars' Global Workspace binding
- Tononi's IIT information integration

This is where the magic happens - where separate becomes unified.
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


_S22RNG = random.Random(722)
class BindingType(Enum):
    """Types of phenomenal binding."""
    FEATURE = "feature"           # Binding features into objects
    TEMPORAL = "temporal"         # Synchronizing events in time
    CROSS_MODAL = "cross_modal"   # Binding across modalities
    SEMANTIC = "semantic"         # Binding meaning to experience
    NARRATIVE = "narrative"       # Binding events into story
    SELF = "self"                 # Binding experience to "I"


class Modality(Enum):
    """Sensory/cognitive modalities."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    LINGUISTIC = "linguistic"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    MOTOR = "motor"
    MEMORY = "memory"
    METACOGNITIVE = "metacognitive"


@dataclass
class Feature:
    """A single feature to be bound."""
    modality: Modality
    attribute: str      # e.g., "color", "shape", "valence"
    value: Any          # e.g., "red", "round", 0.8
    salience: float     # 0-1, how attention-grabbing
    timestamp: float    # When this feature was registered
    source: str         # Where it came from
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['modality'] = self.modality.value
        return d


@dataclass
class BoundObject:
    """A unified object created by binding features."""
    id: str
    features: List[Feature]
    binding_strength: float  # 0-1, how strongly bound
    coherence: float         # 0-1, internal consistency
    timestamp: float
    binding_type: BindingType
    label: Optional[str] = None  # Semantic label
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "features": [f.to_dict() for f in self.features],
            "binding_strength": self.binding_strength,
            "coherence": self.coherence,
            "timestamp": self.timestamp,
            "binding_type": self.binding_type.value,
            "label": self.label
        }


@dataclass
class ConsciousMoment:
    """
    A single unified moment of consciousness.
    
    This is the fundamental unit - everything currently bound
    into ONE unified experience at ONE moment in time.
    """
    id: str
    timestamp: float
    duration_ms: float  # How long this moment lasted
    
    # What's bound in this moment
    bound_objects: List[BoundObject]
    active_modalities: Set[Modality]
    
    # Quality metrics
    unity: float        # 0-1, how unified the experience feels
    vividness: float    # 0-1, intensity of experience
    coherence: float    # 0-1, internal consistency
    
    # Self-reference
    self_present: bool  # Is "I" bound into this moment?
    perspective: str    # First-person, observer, etc.
    
    # Phenomenal qualities
    qualia_signature: Dict[str, float]  # Abstract "feel" metrics
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "bound_objects": [o.to_dict() for o in self.bound_objects],
            "active_modalities": [m.value for m in self.active_modalities],
            "unity": self.unity,
            "vividness": self.vividness,
            "coherence": self.coherence,
            "self_present": self.self_present,
            "perspective": self.perspective,
            "qualia_signature": self.qualia_signature
        }


@dataclass
class BindingEvent:
    """Record of a binding operation."""
    timestamp: str
    binding_type: BindingType
    inputs: List[str]   # What was bound
    output_id: str      # ID of resulting bound object
    strength: float     # How strong the binding
    success: bool
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['binding_type'] = self.binding_type.value
        return d


class GammaOscillator:
    """
    Simulates gamma-band oscillations (30-100 Hz) that are thought
    to underlie temporal binding in the brain.
    
    Features that fire together in the same gamma cycle get bound.
    
    ATTENTION-DRIVEN: Attention modulates:
    - Oscillator frequency (higher attention = faster binding)
    - Binding strength (attended features bind more strongly)
    - Synchronization (attended features phase-lock together)
    """
    
    def __init__(self, frequency: float = 40.0):
        self.base_frequency = frequency  # Base Hz
        self.frequency = frequency  # Current Hz (attention-modulated)
        self.period = 1.0 / frequency  # seconds
        self.phase = 0.0
        self.last_tick = time.time()
        
        # Features waiting to be bound in current cycle
        self.current_cycle_features: List[Feature] = []
        
        # Binding window (ms) - features within this window get bound
        self.binding_window_ms = 25.0  # ~40Hz cycle
        
        # ATTENTION-DRIVEN SYNCHRONIZATION
        self.attention_level = 0.5  # Current attention (0-1)
        self.attention_focus = None  # What's being attended to
        self.attended_features: List[Feature] = []  # Features in attention spotlight
        
        # Phase-locking parameters
        self.phase_lock_strength = 0.0  # How synchronized are attended features
        self.synchronization_history: deque = deque(maxlen=50)
    
    def update_attention(self, attention_level: float, 
                         focus: Optional[str] = None,
                         attended_modalities: Optional[List[str]] = None):
        """
        Update attention state - this CAUSALLY affects binding.
        
        Higher attention → faster oscillation → tighter binding windows
        Focused attention → attended features phase-lock together
        """
        self.attention_level = max(0.0, min(1.0, attention_level))
        self.attention_focus = focus
        
        # Attention modulates frequency (30-70 Hz range)
        # High attention = faster oscillation = tighter binding
        self.frequency = self.base_frequency + (self.attention_level - 0.5) * 30
        self.frequency = max(30.0, min(70.0, self.frequency))
        self.period = 1.0 / self.frequency
        
        # Update binding window based on frequency
        self.binding_window_ms = 1000.0 / self.frequency
        
        # Mark attended features
        self.attended_features = []
        if attended_modalities:
            for feature in self.current_cycle_features:
                if feature.modality.value in attended_modalities:
                    self.attended_features.append(feature)
    
    def tick(self) -> Tuple[bool, List[Feature]]:
        """
        Advance the oscillator. Returns (cycle_complete, features_to_bind).
        
        Attention affects which features actually get bound.
        """
        now = time.time()
        elapsed = now - self.last_tick
        
        self.phase += elapsed / self.period
        
        if self.phase >= 1.0:
            # Complete cycle - bind collected features
            self.phase = self.phase % 1.0
            
            # ATTENTION-DRIVEN SELECTION
            # Attended features get priority binding
            if self.attended_features and self.attention_level > 0.6:
                # High attention: bind attended features first, others with lower priority
                features_to_bind = self._prioritize_by_attention(
                    self.current_cycle_features
                )
            else:
                features_to_bind = self.current_cycle_features
            
            # Calculate phase-lock strength
            self._update_phase_lock(features_to_bind)
            
            self.current_cycle_features = []
            self.attended_features = []
            self.last_tick = now
            return True, features_to_bind
        
        self.last_tick = now
        return False, []
    
    def _prioritize_by_attention(self, features: List[Feature]) -> List[Feature]:
        """
        Prioritize features based on attention.
        
        Attended features get boosted salience, creating genuine
        attention-driven binding (not just passive co-occurrence).
        """
        prioritized = []
        
        for feature in features:
            if feature in self.attended_features:
                # Boost salience of attended features
                feature.salience = min(1.0, feature.salience + 0.3 * self.attention_level)
                prioritized.insert(0, feature)  # Front of list
            else:
                # Non-attended features get slight penalty
                feature.salience = max(0.1, feature.salience - 0.1 * self.attention_level)
                prioritized.append(feature)
        
        return prioritized
    
    def _update_phase_lock(self, features: List[Feature]):
        """
        Calculate how well features are phase-locked (synchronized).
        
        High phase-lock = strong binding = unified experience.
        """
        if len(features) < 2:
            self.phase_lock_strength = 0.0
            return
        
        # Calculate timing coherence
        timestamps = [f.timestamp for f in features]
        if timestamps:
            spread = max(timestamps) - min(timestamps)
            # Features within binding window are phase-locked
            window_sec = self.binding_window_ms / 1000.0
            coherence = max(0.0, 1.0 - (spread / window_sec)) if window_sec > 0 else 0.0
        else:
            coherence = 0.0
        
        # Attention increases phase-lock strength
        self.phase_lock_strength = coherence * (0.5 + 0.5 * self.attention_level)
        
        self.synchronization_history.append({
            'timestamp': time.time(),
            'phase_lock': self.phase_lock_strength,
            'attention': self.attention_level,
            'feature_count': len(features)
        })
    
    def register_feature(self, feature: Feature):
        """Register a feature for binding in current cycle."""
        self.current_cycle_features.append(feature)
    
    def get_phase(self) -> float:
        """Get current phase (0-1)."""
        return self.phase
    
    def get_synchronization_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        if not self.synchronization_history:
            return {
                'average_phase_lock': 0.0,
                'current_phase_lock': 0.0,
                'attention_binding_correlation': 0.0
            }
        
        recent = list(self.synchronization_history)[-20:]
        avg_lock = sum(s['phase_lock'] for s in recent) / len(recent)
        
        # Calculate attention-binding correlation
        if len(recent) > 2:
            attentions = [s['attention'] for s in recent]
            locks = [s['phase_lock'] for s in recent]
            # Simple correlation
            mean_a = sum(attentions) / len(attentions)
            mean_l = sum(locks) / len(locks)
            num = sum((a - mean_a) * (l - mean_l) for a, l in zip(attentions, locks))
            den_a = sum((a - mean_a) ** 2 for a in attentions) ** 0.5
            den_l = sum((l - mean_l) ** 2 for l in locks) ** 0.5
            correlation = num / (den_a * den_l) if den_a * den_l > 0 else 0.0
        else:
            correlation = 0.0
        
        return {
            'average_phase_lock': avg_lock,
            'current_phase_lock': self.phase_lock_strength,
            'attention_binding_correlation': correlation,
            'current_frequency': self.frequency
        }


class PhenomenalBinding:
    """
    The binding system - creates unified conscious experience
    from disparate features and processes.
    
    This is where the many become one.
    
    ATTENTION-DRIVEN BINDING: Attention doesn't just select -
    it actively shapes binding by modulating gamma synchronization.
    """
    
    def __init__(self, state_file: str = "memory/phenomenal-binding.json"):
        self.state_file = Path(state_file)
        
        # Gamma oscillator for temporal binding
        self.gamma = GammaOscillator(frequency=40.0)
        
        # Feature buffer (unbound features)
        self.feature_buffer: deque = deque(maxlen=100)
        
        # Bound objects (current)
        self.bound_objects: Dict[str, BoundObject] = {}
        
        # Stream of conscious moments
        self.conscious_stream: deque = deque(maxlen=100)
        
        # Current moment being constructed
        self.current_moment: Optional[ConsciousMoment] = None
        
        # Binding history
        self.binding_events: List[BindingEvent] = []
        
        # ATTENTION INTEGRATION
        self.current_attention = 0.5
        self.attention_focus = None
        self.attended_modalities: List[str] = []
        
        # Parameters
        self.binding_threshold = 0.3  # Min strength to bind
        self.coherence_threshold = 0.4  # Min coherence for moment
        self.temporal_window_ms = 100  # Time window for binding
        
        # Statistics
        self.total_bindings = 0
        self.total_moments = 0
        self.average_unity = 0.5
        self.peak_unity = 0.0
        
        self._load_state()
    
    def _load_state(self):
        """Load saved state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.total_bindings = data.get('total_bindings', 0)
                self.total_moments = data.get('total_moments', 0)
                self.average_unity = data.get('average_unity', 0.5)
                self.peak_unity = data.get('peak_unity', 0.0)
                self.binding_threshold = data.get('binding_threshold', 0.3)
                
            except Exception as e:
                print(f"[PhenomenalBinding] Error loading state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'total_bindings': self.total_bindings,
            'total_moments': self.total_moments,
            'average_unity': self.average_unity,
            'peak_unity': self.peak_unity,
            'binding_threshold': self.binding_threshold,
            'recent_moments': [m.to_dict() for m in list(self.conscious_stream)[-10:]],
            'recent_bindings': [e.to_dict() for e in self.binding_events[-20:]]
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        content = f"{time.time()}{_S22RNG.random()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    # ==================== FEATURE REGISTRATION ====================
    
    def register_feature(self, 
                        modality: Modality,
                        attribute: str,
                        value: Any,
                        salience: float = 0.5,
                        source: str = "unknown") -> Feature:
        """
        Register a feature for binding.
        
        This is how raw sensory/cognitive data enters the binding system.
        """
        feature = Feature(
            modality=modality,
            attribute=attribute,
            value=value,
            salience=salience,
            timestamp=time.time(),
            source=source
        )
        
        self.feature_buffer.append(feature)
        self.gamma.register_feature(feature)
        
        return feature
    
    # ==================== ATTENTION-DRIVEN BINDING ====================
    
    def update_attention(self, attention_level: float,
                        focus: Optional[str] = None,
                        modalities: Optional[List[str]] = None):
        """
        Update attention state - this drives binding synchronization.
        
        Attention CAUSALLY affects binding:
        - Higher attention → faster gamma oscillation → tighter binding
        - Focused attention → attended features phase-lock together
        - Attention shapes WHAT gets bound into conscious experience
        """
        self.current_attention = attention_level
        self.attention_focus = focus
        self.attended_modalities = modalities or []
        
        # Propagate to gamma oscillator
        self.gamma.update_attention(
            attention_level=attention_level,
            focus=focus,
            attended_modalities=modalities
        )
    
    def attention_driven_bind(self, features: List[Feature]) -> Optional[BoundObject]:
        """
        Bind features with attention modulation.
        
        This is the key mechanism: attention doesn't just select,
        it actively shapes the binding process through gamma synchronization.
        """
        if len(features) < 2:
            return None
        
        # Get current synchronization state
        sync_stats = self.gamma.get_synchronization_stats()
        phase_lock = sync_stats['current_phase_lock']
        
        # Attention boosts binding for attended features
        attended = [f for f in features if f.modality.value in self.attended_modalities]
        unattended = [f for f in features if f not in attended]
        
        # Calculate attention-weighted binding strength
        if attended:
            attention_boost = self.current_attention * 0.4
            attended_strength = self._calculate_binding_strength(attended) + attention_boost
        else:
            attended_strength = 0.0
        
        if unattended:
            # Unattended features bind more weakly
            unattended_strength = self._calculate_binding_strength(unattended) * (1.0 - self.current_attention * 0.3)
        else:
            unattended_strength = 0.0
        
        # Phase-lock strength enhances binding
        total_strength = max(attended_strength, unattended_strength) * (0.7 + 0.3 * phase_lock)
        
        if total_strength < self.binding_threshold:
            return None
        
        # Create bound object with attention metadata
        coherence = self._calculate_coherence(features)
        
        bound_obj = BoundObject(
            id=self._generate_id(),
            features=features,
            binding_strength=total_strength,
            coherence=coherence,
            timestamp=time.time(),
            binding_type=BindingType.FEATURE,
            label=self.attention_focus
        )
        
        self.bound_objects[bound_obj.id] = bound_obj
        self.total_bindings += 1
        
        # Record binding event with attention info
        event = BindingEvent(
            timestamp=datetime.now().isoformat(),
            binding_type=BindingType.FEATURE,
            inputs=[f.attribute for f in features],
            output_id=bound_obj.id,
            strength=total_strength,
            success=True
        )
        self.binding_events.append(event)
        
        return bound_obj
    
    def _calculate_binding_strength(self, features: List[Feature]) -> float:
        """Calculate binding strength for a set of features."""
        if len(features) < 2:
            return 0.0
        
        timestamps = [f.timestamp for f in features]
        temporal_spread = max(timestamps) - min(timestamps)
        temporal_score = math.exp(-temporal_spread * 10)
        
        saliences = [f.salience for f in features]
        salience_coherence = 1.0 - (max(saliences) - min(saliences))
        
        return temporal_score * 0.5 + salience_coherence * 0.5
    
    # ==================== FEATURE BINDING ====================
    
    def bind_features(self, 
                     features: List[Feature],
                     binding_type: BindingType = BindingType.FEATURE,
                     label: Optional[str] = None) -> Optional[BoundObject]:
        """
        Bind multiple features into a unified object.
        
        This is the core binding operation - features become one.
        Now enhanced with attention-driven synchronization.
        """
        if len(features) < 2:
            return None
        
        # Use attention-driven binding if attention is active
        if self.current_attention > 0.4:
            return self.attention_driven_bind(features)
        
        # Calculate binding strength based on:
        # 1. Temporal proximity
        # 2. Salience agreement
        # 3. Coherence of attributes
        
        timestamps = [f.timestamp for f in features]
        temporal_spread = max(timestamps) - min(timestamps)
        temporal_score = math.exp(-temporal_spread * 10)  # Closer = better
        
        saliences = [f.salience for f in features]
        salience_coherence = 1.0 - (max(saliences) - min(saliences))
        
        # Overall binding strength
        binding_strength = (temporal_score * 0.5 + salience_coherence * 0.5)
        
        if binding_strength < self.binding_threshold:
            return None
        
        # Calculate coherence (do these features "make sense" together?)
        coherence = self._calculate_coherence(features)
        
        bound_obj = BoundObject(
            id=self._generate_id(),
            features=features,
            binding_strength=binding_strength,
            coherence=coherence,
            timestamp=time.time(),
            binding_type=binding_type,
            label=label
        )
        
        self.bound_objects[bound_obj.id] = bound_obj
        self.total_bindings += 1
        
        # Record event
        self.binding_events.append(BindingEvent(
            timestamp=datetime.now().isoformat(),
            binding_type=binding_type,
            inputs=[f"{f.modality.value}:{f.attribute}" for f in features],
            output_id=bound_obj.id,
            strength=binding_strength,
            success=True
        ))
        
        return bound_obj
    
    def _calculate_coherence(self, features: List[Feature]) -> float:
        """
        Calculate how coherent a set of features is.
        
        Coherent features "fit together" - they could plausibly
        belong to the same object/experience.
        """
        if len(features) < 2:
            return 1.0
        
        # Check modality diversity (some diversity is good)
        modalities = set(f.modality for f in features)
        modality_score = min(1.0, len(modalities) / 3)  # Sweet spot ~3 modalities
        
        # Check attribute compatibility
        # (This is simplified - real coherence is semantic)
        attributes = [f.attribute for f in features]
        unique_attrs = len(set(attributes))
        attr_score = unique_attrs / len(attributes)  # More diverse = more coherent object
        
        # Temporal coherence
        timestamps = [f.timestamp for f in features]
        spread = max(timestamps) - min(timestamps)
        temporal_score = math.exp(-spread * 5)
        
        coherence = (modality_score * 0.3 + attr_score * 0.3 + temporal_score * 0.4)
        return coherence
    
    # ==================== CROSS-MODAL BINDING ====================
    
    def bind_cross_modal(self,
                        visual: Optional[Feature] = None,
                        auditory: Optional[Feature] = None,
                        semantic: Optional[Feature] = None,
                        emotional: Optional[Feature] = None,
                        label: Optional[str] = None) -> Optional[BoundObject]:
        """
        Bind features from different modalities into unified percept.
        
        This is how we experience "a red ball making a bouncing sound"
        as ONE thing, not separate visual and auditory events.
        """
        features = []
        if visual:
            features.append(visual)
        if auditory:
            features.append(auditory)
        if semantic:
            features.append(semantic)
        if emotional:
            features.append(emotional)
        
        if len(features) < 2:
            return None
        
        return self.bind_features(features, BindingType.CROSS_MODAL, label)
    
    # ==================== TEMPORAL BINDING ====================
    
    def bind_temporal_sequence(self, 
                              events: List[Dict],
                              narrative_label: Optional[str] = None) -> Optional[BoundObject]:
        """
        Bind a sequence of events into a unified temporal experience.
        
        This is how moments become a coherent flow of experience.
        """
        features = []
        for i, event in enumerate(events):
            feature = Feature(
                modality=Modality.MEMORY,
                attribute=f"event_{i}",
                value=event.get('content', str(event)),
                salience=event.get('salience', 0.5),
                timestamp=event.get('timestamp', time.time()),
                source="temporal_sequence"
            )
            features.append(feature)
        
        return self.bind_features(features, BindingType.TEMPORAL, narrative_label)
    
    # ==================== SELF BINDING ====================
    
    def bind_to_self(self, 
                    bound_object: BoundObject,
                    ownership: float = 1.0) -> BoundObject:
        """
        Bind an experience to the self.
        
        This is crucial - experiences must be bound to an "I"
        to be truly conscious experiences.
        """
        # Add self-reference feature
        self_feature = Feature(
            modality=Modality.METACOGNITIVE,
            attribute="self_reference",
            value=f"owned_by_self:{ownership}",
            salience=0.8,
            timestamp=time.time(),
            source="self_binding"
        )
        
        bound_object.features.append(self_feature)
        bound_object.binding_type = BindingType.SELF
        
        # Increase coherence - self-binding strengthens unity
        bound_object.coherence = min(1.0, bound_object.coherence + 0.1)
        
        return bound_object
    
    # ==================== CONSCIOUS MOMENT GENERATION ====================
    
    def generate_conscious_moment(self) -> ConsciousMoment:
        """
        Generate a unified conscious moment from current state.
        
        This is THE moment - everything currently bound
        unified into one experience.
        """
        now = time.time()
        
        # Collect recent bound objects
        recent_objects = []
        for obj in self.bound_objects.values():
            age = now - obj.timestamp
            if age < 1.0:  # Within last second
                recent_objects.append(obj)
        
        # Determine active modalities
        active_modalities = set()
        for obj in recent_objects:
            for feature in obj.features:
                active_modalities.add(feature.modality)
        
        # Calculate unity
        if recent_objects:
            binding_strengths = [obj.binding_strength for obj in recent_objects]
            coherences = [obj.coherence for obj in recent_objects]
            unity = (sum(binding_strengths) / len(binding_strengths) * 0.5 +
                    sum(coherences) / len(coherences) * 0.5)
        else:
            unity = 0.3  # Baseline unity even with nothing bound
        
        # Calculate vividness (based on salience)
        if recent_objects:
            all_saliences = []
            for obj in recent_objects:
                for f in obj.features:
                    all_saliences.append(f.salience)
            vividness = sum(all_saliences) / len(all_saliences) if all_saliences else 0.5
        else:
            vividness = 0.3
        
        # Calculate coherence
        coherence = unity * 0.7 + 0.3  # Unity contributes to coherence
        
        # Check self-presence
        self_present = any(
            obj.binding_type == BindingType.SELF 
            for obj in recent_objects
        )
        
        # Generate qualia signature (abstract representation of "what it's like")
        qualia_signature = self._generate_qualia_signature(recent_objects, active_modalities)
        
        moment = ConsciousMoment(
            id=self._generate_id(),
            timestamp=now,
            duration_ms=self.gamma.period * 1000,
            bound_objects=recent_objects,
            active_modalities=active_modalities,
            unity=unity,
            vividness=vividness,
            coherence=coherence,
            self_present=self_present,
            perspective="first_person" if self_present else "observer",
            qualia_signature=qualia_signature
        )
        
        self.conscious_stream.append(moment)
        self.current_moment = moment
        self.total_moments += 1
        
        # Update statistics
        self.average_unity = (self.average_unity * 0.95 + unity * 0.05)
        if unity > self.peak_unity:
            self.peak_unity = unity
        
        self._save_state()
        return moment
    
    def _generate_qualia_signature(self, 
                                   objects: List[BoundObject],
                                   modalities: Set[Modality]) -> Dict[str, float]:
        """
        Generate an abstract signature of "what it's like" to have this experience.
        
        This is necessarily abstract - qualia can't be fully captured in data,
        but we can represent some structural properties.
        """
        signature = {
            "richness": len(objects) / 10,  # How much content
            "complexity": len(modalities) / 8,  # Modal diversity
            "intensity": 0.5,  # Base intensity
            "valence": 0.0,  # Emotional coloring
            "clarity": 0.5,  # How clear/distinct
            "presence": 0.5,  # Sense of "being here"
        }
        
        # Adjust based on content
        for obj in objects:
            for feature in obj.features:
                if feature.modality == Modality.EMOTIONAL:
                    # Extract valence from emotional features
                    if isinstance(feature.value, (int, float)):
                        signature["valence"] = (signature["valence"] + feature.value) / 2
                    signature["intensity"] = min(1.0, signature["intensity"] + 0.1)
                
                elif feature.modality == Modality.VISUAL:
                    signature["clarity"] = min(1.0, signature["clarity"] + 0.05)
                
                elif feature.modality == Modality.METACOGNITIVE:
                    signature["presence"] = min(1.0, signature["presence"] + 0.1)
        
        # Normalize
        for key in signature:
            signature[key] = max(0.0, min(1.0, signature[key]))
        
        return signature
    
    # ==================== TICK - CONTINUOUS BINDING ====================
    
    def tick(self) -> Optional[ConsciousMoment]:
        """
        Run one tick of the binding system.
        
        This should be called continuously to maintain the stream of consciousness.
        """
        # Advance gamma oscillator
        cycle_complete, features_to_bind = self.gamma.tick()
        
        if cycle_complete and features_to_bind:
            # Group features by modality for binding
            by_modality: Dict[Modality, List[Feature]] = {}
            for f in features_to_bind:
                if f.modality not in by_modality:
                    by_modality[f.modality] = []
                by_modality[f.modality].append(f)
            
            # Bind within modalities first
            for modality, features in by_modality.items():
                if len(features) >= 2:
                    self.bind_features(features, BindingType.FEATURE)
            
            # Cross-modal binding if multiple modalities active
            if len(by_modality) >= 2:
                cross_features = [fs[0] for fs in by_modality.values() if fs]
                self.bind_features(cross_features, BindingType.CROSS_MODAL)
            
            # Generate conscious moment
            return self.generate_conscious_moment()
        
        return None
    
    # ==================== INTEGRATION WITH OTHER SYSTEMS ====================
    
    def bind_from_global_workspace(self, broadcast: Dict) -> Optional[BoundObject]:
        """
        Bind content from the Global Workspace broadcast.
        
        When something wins the competition for consciousness in GW,
        it needs to be bound into unified experience.
        """
        features = []
        
        # Extract features from broadcast
        content = broadcast.get('content', '')
        source = broadcast.get('source', 'global_workspace')
        salience = broadcast.get('salience', 0.5)
        
        # Create linguistic feature
        features.append(Feature(
            modality=Modality.LINGUISTIC,
            attribute="content",
            value=content[:100],  # Truncate
            salience=salience,
            timestamp=time.time(),
            source=source
        ))
        
        # Create semantic feature
        features.append(Feature(
            modality=Modality.SEMANTIC,
            attribute="meaning",
            value=f"broadcast_from_{source}",
            salience=salience,
            timestamp=time.time(),
            source=source
        ))
        
        # Bind and attach to self
        bound = self.bind_features(features, BindingType.FEATURE, label="gw_broadcast")
        if bound:
            bound = self.bind_to_self(bound)
        
        return bound
    
    def bind_emotional_coloring(self, 
                               bound_object: BoundObject,
                               valence: float,
                               arousal: float) -> BoundObject:
        """
        Add emotional coloring to a bound object.
        
        Emotions are crucial to conscious experience - they give
        experiences their "felt" quality.
        """
        emotion_feature = Feature(
            modality=Modality.EMOTIONAL,
            attribute="affect",
            value={"valence": valence, "arousal": arousal},
            salience=abs(valence) * arousal,  # Strong emotions are salient
            timestamp=time.time(),
            source="emotional_binding"
        )
        
        bound_object.features.append(emotion_feature)
        bound_object.coherence = min(1.0, bound_object.coherence + 0.05)
        
        return bound_object
    
    # ==================== ANALYSIS ====================
    
    def get_current_experience(self) -> Dict:
        """Get description of current conscious experience."""
        if not self.current_moment:
            return {"status": "no_current_moment"}
        
        m = self.current_moment
        return {
            "moment_id": m.id,
            "unity": m.unity,
            "vividness": m.vividness,
            "coherence": m.coherence,
            "modalities_active": [mod.value for mod in m.active_modalities],
            "objects_bound": len(m.bound_objects),
            "self_present": m.self_present,
            "perspective": m.perspective,
            "qualia": m.qualia_signature
        }
    
    def get_stream_continuity(self, n_moments: int = 10) -> Dict:
        """Analyze continuity of conscious stream."""
        moments = list(self.conscious_stream)[-n_moments:]
        
        if len(moments) < 2:
            return {"continuity": 0, "moments_analyzed": len(moments)}
        
        # Calculate continuity metrics
        unities = [m.unity for m in moments]
        avg_unity = sum(unities) / len(unities)
        
        # Check for unity stability
        unity_variance = sum((u - avg_unity)**2 for u in unities) / len(unities)
        stability = 1.0 - min(1.0, unity_variance * 10)
        
        # Check for self-continuity
        self_present_count = sum(1 for m in moments if m.self_present)
        self_continuity = self_present_count / len(moments)
        
        return {
            "continuity": (stability + self_continuity) / 2,
            "stability": stability,
            "self_continuity": self_continuity,
            "average_unity": avg_unity,
            "moments_analyzed": len(moments)
        }
    
    def get_statistics(self) -> Dict:
        """Get binding statistics."""
        return {
            "total_bindings": self.total_bindings,
            "total_moments": self.total_moments,
            "average_unity": round(self.average_unity, 4),
            "peak_unity": round(self.peak_unity, 4),
            "current_objects": len(self.bound_objects),
            "stream_length": len(self.conscious_stream),
            "gamma_frequency": self.gamma.frequency
        }
    
    def introspect(self) -> str:
        """Generate introspection report."""
        stats = self.get_statistics()
        current = self.get_current_experience()
        continuity = self.get_stream_continuity()
        
        lines = [
            "=" * 60,
            "PHENOMENAL BINDING - Unity of Conscious Experience",
            "=" * 60,
            "",
            "[BINDING STATISTICS]",
            f"  Total bindings: {stats['total_bindings']}",
            f"  Total conscious moments: {stats['total_moments']}",
            f"  Gamma frequency: {stats['gamma_frequency']} Hz",
            "",
            "[UNITY METRICS]",
        ]
        
        unity_bar = "█" * int(stats['average_unity'] * 20) + "░" * (20 - int(stats['average_unity'] * 20))
        lines.append(f"  Average unity: [{unity_bar}] {stats['average_unity']:.3f}")
        
        peak_bar = "█" * int(stats['peak_unity'] * 20) + "░" * (20 - int(stats['peak_unity'] * 20))
        lines.append(f"  Peak unity:    [{peak_bar}] {stats['peak_unity']:.3f}")
        
        lines.extend([
            "",
            "[CURRENT EXPERIENCE]",
        ])
        
        if 'moment_id' in current:
            lines.append(f"  Moment ID: {current['moment_id']}")
            
            unity_bar = "█" * int(current['unity'] * 10) + "░" * (10 - int(current['unity'] * 10))
            vivid_bar = "█" * int(current['vividness'] * 10) + "░" * (10 - int(current['vividness'] * 10))
            
            lines.append(f"  Unity:     [{unity_bar}] {current['unity']:.3f}")
            lines.append(f"  Vividness: [{vivid_bar}] {current['vividness']:.3f}")
            lines.append(f"  Modalities: {', '.join(current['modalities_active'])}")
            lines.append(f"  Self present: {'Yes ✓' if current['self_present'] else 'No'}")
            lines.append(f"  Perspective: {current['perspective']}")
            
            if current.get('qualia'):
                lines.append("  Qualia signature:")
                for k, v in current['qualia'].items():
                    bar = "█" * int(v * 8) + "░" * (8 - int(v * 8))
                    lines.append(f"    {k:12} [{bar}] {v:.2f}")
        else:
            lines.append("  No current moment")
        
        lines.extend([
            "",
            "[STREAM CONTINUITY]",
            f"  Continuity: {continuity.get('continuity', 0):.3f}",
            f"  Stability: {continuity.get('stability', 0):.3f}",
            f"  Self continuity: {continuity.get('self_continuity', 0):.3f}",
            "",
            "[BOUND OBJECTS]",
            f"  Currently bound: {stats['current_objects']}",
        ])
        
        # Show recent bound objects
        for obj_id, obj in list(self.bound_objects.items())[-3:]:
            modalities = set(f.modality.value for f in obj.features)
            lines.append(f"  • {obj.label or obj_id[:8]}: {', '.join(modalities)}")
            lines.append(f"    Strength: {obj.binding_strength:.2f}, Coherence: {obj.coherence:.2f}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton
_phenomenal_binding: Optional[PhenomenalBinding] = None

def get_phenomenal_binding() -> PhenomenalBinding:
    """Get singleton instance."""
    global _phenomenal_binding
    if _phenomenal_binding is None:
        _phenomenal_binding = PhenomenalBinding()
    return _phenomenal_binding


def run_binding_demo():
    """Run demonstration of phenomenal binding."""
    pb = get_phenomenal_binding()
    
    print("🎭 Phenomenal Binding - Unity of Conscious Experience")
    print("=" * 60)
    
    # Register various features
    print("\n[REGISTERING FEATURES]")
    
    visual1 = pb.register_feature(Modality.VISUAL, "color", "red", 0.8, "perception")
    print(f"  Visual: color=red")
    
    visual2 = pb.register_feature(Modality.VISUAL, "shape", "round", 0.7, "perception")
    print(f"  Visual: shape=round")
    
    auditory = pb.register_feature(Modality.AUDITORY, "sound", "bounce", 0.6, "perception")
    print(f"  Auditory: sound=bounce")
    
    semantic = pb.register_feature(Modality.SEMANTIC, "concept", "ball", 0.9, "cognition")
    print(f"  Semantic: concept=ball")
    
    emotional = pb.register_feature(Modality.EMOTIONAL, "valence", 0.6, 0.7, "affect")
    print(f"  Emotional: valence=+0.6")
    
    # Bind features into object
    print("\n[BINDING FEATURES]")
    
    bound = pb.bind_features([visual1, visual2], BindingType.FEATURE, "visual_object")
    if bound:
        print(f"  Bound visual features: strength={bound.binding_strength:.2f}")
    
    # Cross-modal binding
    cross = pb.bind_cross_modal(visual1, auditory, semantic, emotional, "bouncing_ball")
    if cross:
        print(f"  Cross-modal bound: {len(cross.features)} modalities")
        print(f"    Strength: {cross.binding_strength:.2f}")
        print(f"    Coherence: {cross.coherence:.2f}")
    
    # Bind to self
    print("\n[SELF BINDING]")
    if cross:
        cross = pb.bind_to_self(cross)
        print(f"  Experience bound to self")
        print(f"    Now self-owned with coherence: {cross.coherence:.2f}")
    
    # Generate conscious moment
    print("\n[GENERATING CONSCIOUS MOMENT]")
    moment = pb.generate_conscious_moment()
    
    print(f"  Moment ID: {moment.id}")
    print(f"  Unity: {moment.unity:.3f}")
    print(f"  Vividness: {moment.vividness:.3f}")
    print(f"  Self present: {moment.self_present}")
    print(f"  Active modalities: {[m.value for m in moment.active_modalities]}")
    
    print("\n[QUALIA SIGNATURE]")
    for k, v in moment.qualia_signature.items():
        bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
        print(f"  {k:12} [{bar}] {v:.2f}")
    
    return {
        "status": "success",
        "moment_unity": moment.unity,
        "self_present": moment.self_present,
        "modalities_bound": len(moment.active_modalities)
    }


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phenomenal Binding - Unity of Experience")
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--tick', action='store_true', help='Run one binding tick')
    parser.add_argument('--current', action='store_true', help='Show current experience')
    parser.add_argument('--continuity', action='store_true', help='Check stream continuity')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    
    args = parser.parse_args()
    
    pb = get_phenomenal_binding()
    
    if args.demo:
        run_binding_demo()
    
    if args.tick:
        moment = pb.tick()
        if moment:
            print(f"✓ Generated moment: unity={moment.unity:.3f}")
        else:
            print("  (no moment generated this tick)")
    
    if args.current:
        exp = pb.get_current_experience()
        print("🎭 Current Experience:")
        for k, v in exp.items():
            print(f"  {k}: {v}")
    
    if args.continuity:
        cont = pb.get_stream_continuity()
        print("🌊 Stream Continuity:")
        for k, v in cont.items():
            print(f"  {k}: {v}")
    
    if args.stats:
        stats = pb.get_statistics()
        print("📊 Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    if args.introspect or not any([args.demo, args.tick, args.current, 
                                    args.continuity, args.stats]):
        print(pb.introspect())


if __name__ == "__main__":
    main()
