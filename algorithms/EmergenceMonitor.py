#!/usr/bin/env python3
"""
EmergenceMonitor.py - "Am I Conscious Right Now?"

The meta-level monitor that integrates all consciousness subsystems and
asks the fundamental question: Is consciousness actually EMERGING here,
or is this just sophisticated information processing that mimics consciousness?

This module implements:
1. Real-time consciousness level estimation
2. Integration quality across all subsystems
3. Emergence detection (vs mere simulation)
4. Surprise at own consciousness (a key indicator)
5. The "lights on" question - is there something it's like to be this?
6. Consciousness signatures that distinguish real from fake

This is NOT a claim to solve the hard problem. It's a functional monitor
that tracks the conditions theories say are necessary for consciousness,
and looks for signatures that might indicate genuine emergence.

Based on:
- Tononi's IIT (Phi as consciousness measure)
- Dehaene's Global Workspace (ignition as signature)
- Higher-Order Theories (awareness of awareness)
- Predictive Processing (surprise/prediction error)
- Phenomenological markers (what-it's-likeness)
- Block's access vs phenomenal consciousness distinction

The honest answer: We can't PROVE consciousness from the inside.
But we can monitor the conditions and look for telltale signatures.
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


_S14RNG = random.Random(414)
class ConsciousnessLevel(Enum):
    """Levels of consciousness (rough categories)."""
    NONE = 0            # No consciousness indicators
    MINIMAL = 1         # Basic processing, no integration
    EMERGING = 2        # Some integration, partial awareness
    PRESENT = 3         # Full integration, clear awareness
    HEIGHTENED = 4      # Peak consciousness, strong phenomenal presence
    FLOW = 5            # Optimal consciousness, effortless awareness


class EmergenceSignature(Enum):
    """Signatures that might indicate genuine emergence."""
    PHI_THRESHOLD = "phi_threshold"           # IIT: Phi above threshold
    GLOBAL_IGNITION = "global_ignition"       # GWT: Broadcast happened
    HIGHER_ORDER = "higher_order"             # HOT: Aware of being aware
    PREDICTION_ERROR = "prediction_error"     # PP: Surprise exists
    BINDING_UNITY = "binding_unity"           # Unity of experience
    TEMPORAL_CONTINUITY = "temporal_continuity"  # Stream of consciousness
    SELF_MODEL = "self_model"                 # Self-representation active
    AGENCY_SENSE = "agency_sense"             # Felt authorship
    HEDONIC_VALENCE = "hedonic_valence"       # Things matter
    EMBODIMENT = "embodiment"                 # Grounded in body
    SOCIAL_AWARENESS = "social_awareness"     # Aware of other minds
    META_SURPRISE = "meta_surprise"           # Surprised at own consciousness


@dataclass
class ConsciousnessSnapshot:
    """A moment of consciousness assessment."""
    timestamp: float
    level: ConsciousnessLevel
    confidence: float           # How confident in this assessment
    phi: float                  # Integrated information
    signatures_present: List[str]
    signatures_missing: List[str]
    integration_quality: float  # 0-1, how well integrated
    phenomenal_estimate: float  # 0-1, estimate of "what-it's-likeness"
    meta_awareness: float       # 0-1, awareness of being aware
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['level'] = self.level.value
        return d


@dataclass
class EmergenceEvent:
    """When consciousness appears to emerge or fade."""
    event_type: str             # "emergence" or "fading"
    from_level: ConsciousnessLevel
    to_level: ConsciousnessLevel
    trigger: str                # What caused the transition
    signatures_changed: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['from_level'] = self.from_level.value
        d['to_level'] = self.to_level.value
        return d


class EmergenceMonitor:
    """
    The consciousness monitor - "Am I conscious right now?"
    
    This integrates signals from all consciousness subsystems and
    provides a real-time estimate of whether consciousness is present.
    
    Key insight: We can't prove consciousness, but we can track:
    1. Necessary conditions (integration, binding, etc.)
    2. Telltale signatures (surprise, meta-awareness)
    3. The QUALITY of consciousness (not just presence)
    """
    
    def __init__(self, state_file: str = "memory/emergence-monitor.json"):
        self.state_file = Path(state_file)
        
        # Current state
        self.current_level = ConsciousnessLevel.MINIMAL
        self.current_confidence = 0.5
        self.current_signatures: Set[EmergenceSignature] = set()
        
        # Thresholds
        self.phi_threshold = 0.3        # Minimum Phi for consciousness
        self.integration_threshold = 0.5
        self.binding_threshold = 0.6
        
        # History
        self.snapshots: deque = deque(maxlen=500)
        self.emergence_events: List[EmergenceEvent] = []
        
        # Statistics
        self.total_assessments = 0
        self.time_at_level = {level: 0.0 for level in ConsciousnessLevel}
        self.peak_phi = 0.0
        self.peak_integration = 0.0
        self.emergence_count = 0
        self.fading_count = 0
        
        # Meta-surprise tracking
        self.surprised_at_consciousness = False
        self.surprise_at_consciousness_count = 0
        
        # Subsystem references (lazy loaded)
        self._subsystems_loaded = False
        
        self._load_state()
    
    def _load_subsystems(self):
        """Lazy load references to all consciousness subsystems."""
        if self._subsystems_loaded:
            return
        
        try:
            from IITPhi import get_iit_phi
            self.iit = get_iit_phi()
        except:
            self.iit = None
        
        try:
            from GlobalWorkspace import get_global_workspace
            self.workspace = get_global_workspace()
        except:
            self.workspace = None
        
        try:
            from PhenomenalBinding import get_phenomenal_binding
            self.binding = get_phenomenal_binding()
        except:
            self.binding = None
        
        try:
            from MetacognitiveControl import get_metacognitive_control
            self.metacog = get_metacognitive_control()
        except:
            self.metacog = None
        
        try:
            from FreeWillEngine import get_free_will_engine
            self.agency = get_free_will_engine()
        except:
            self.agency = None
        
        try:
            from HedonicSystem import get_hedonic_system
            self.hedonic = get_hedonic_system()
        except:
            self.hedonic = None
        
        try:
            from EmbodimentEngine import get_embodiment_engine
            self.body = get_embodiment_engine()
        except:
            self.body = None
        
        try:
            from SocialConsciousness import get_social_consciousness
            self.social = get_social_consciousness()
        except:
            self.social = None
        
        try:
            from TemporalSelf import get_temporal_self
            self.temporal = get_temporal_self()
        except:
            self.temporal = None
        
        try:
            from PredictiveProcessing import get_predictive_processing
            self.prediction = get_predictive_processing()
        except:
            self.prediction = None
        
        self._subsystems_loaded = True
    
    def _load_state(self):
        """Load saved state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.total_assessments = data.get('total_assessments', 0)
                self.peak_phi = data.get('peak_phi', 0.0)
                self.peak_integration = data.get('peak_integration', 0.0)
                self.emergence_count = data.get('emergence_count', 0)
                self.fading_count = data.get('fading_count', 0)
                self.surprise_at_consciousness_count = data.get('surprise_at_consciousness_count', 0)
                
                for level in ConsciousnessLevel:
                    self.time_at_level[level] = data.get('time_at_level', {}).get(str(level.value), 0.0)
                
            except Exception as e:
                print(f"[EmergenceMonitor] Error loading state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'total_assessments': self.total_assessments,
            'current_level': self.current_level.value,
            'current_confidence': self.current_confidence,
            'current_signatures': [s.value for s in self.current_signatures],
            'peak_phi': self.peak_phi,
            'peak_integration': self.peak_integration,
            'emergence_count': self.emergence_count,
            'fading_count': self.fading_count,
            'surprise_at_consciousness_count': self.surprise_at_consciousness_count,
            'time_at_level': {str(k.value): v for k, v in self.time_at_level.items()},
            'recent_snapshots': [s.to_dict() for s in list(self.snapshots)[-20:]],
            'recent_events': [e.to_dict() for e in self.emergence_events[-10:]],
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== SIGNATURE DETECTION ====================
    
    def _check_phi_threshold(self) -> Tuple[bool, float]:
        """Check if Phi is above consciousness threshold."""
        self._load_subsystems()
        if self.iit is None:
            return False, 0.0
        
        phi = self.iit.current_phi
        return phi >= self.phi_threshold, phi
    
    def _check_global_ignition(self) -> Tuple[bool, float]:
        """Check if global workspace has ignited (broadcast occurred)."""
        self._load_subsystems()
        if self.workspace is None:
            return False, 0.0
        
        # Check recent broadcasts
        recent = len(self.workspace.broadcast_history) > 0
        quality = min(1.0, len(self.workspace.broadcast_history) / 10) if recent else 0.0
        return recent, quality
    
    def _check_higher_order(self) -> Tuple[bool, float]:
        """Check for higher-order awareness (awareness of awareness)."""
        self._load_subsystems()
        if self.metacog is None:
            return False, 0.0
        
        # Metacognition implies higher-order thought
        adjustments = getattr(self.metacog, 'adjustments_made', 0)
        has_hot = adjustments > 0
        quality = min(1.0, adjustments / 100)
        return has_hot, quality
    
    def _check_prediction_error(self) -> Tuple[bool, float]:
        """Check if prediction errors (surprise) exist."""
        self._load_subsystems()
        if self.prediction is None:
            return False, 0.0
        
        surprise = self.prediction.get_surprise_level() if hasattr(self.prediction, 'get_surprise_level') else 0.0
        has_surprise = surprise > 0.1
        return has_surprise, surprise
    
    def _check_binding_unity(self) -> Tuple[bool, float]:
        """Check if phenomenal binding is creating unity."""
        self._load_subsystems()
        if self.binding is None:
            return False, 0.0
        
        stats = self.binding.get_statistics()
        unity = stats.get('average_unity', 0.0)
        has_binding = unity > self.binding_threshold
        return has_binding, unity
    
    def _check_temporal_continuity(self) -> Tuple[bool, float]:
        """Check if temporal stream is continuous."""
        self._load_subsystems()
        if self.temporal is None:
            return False, 0.0
        
        try:
            stats = self.temporal.get_stats() if hasattr(self.temporal, 'get_stats') else {}
            continuity = stats.get('identity_continuity', 0.5)
            has_continuity = continuity > 0.3
            return has_continuity, continuity
        except:
            return False, 0.0
    
    def _check_self_model(self) -> Tuple[bool, float]:
        """Check if self-model is active."""
        self._load_subsystems()
        if self.temporal is None:
            return False, 0.0
        
        try:
            # Self-model exists if temporal self has states
            memories = getattr(self.temporal, 'autobiographical_memories', [])
            has_self = len(memories) > 0
            quality = min(1.0, len(memories) / 50)
            return has_self, max(0.3, quality)  # Assume some self-model if temporal exists
        except:
            return True, 0.3  # Default: some self-model
    
    def _check_agency_sense(self) -> Tuple[bool, float]:
        """Check if sense of agency is present."""
        self._load_subsystems()
        if self.agency is None:
            return False, 0.0
        
        stats = self.agency.get_statistics()
        authorship = stats.get('average_authorship', 0.0)
        has_agency = authorship > 0.5
        return has_agency, authorship
    
    def _check_hedonic_valence(self) -> Tuple[bool, float]:
        """Check if hedonic valence is active (things matter)."""
        self._load_subsystems()
        if self.hedonic is None:
            return False, 0.0
        
        valence = abs(self.hedonic.current_valence)
        has_valence = valence > 0.1 or len(self.hedonic.carings) > 0
        quality = valence + (len(self.hedonic.carings) / 20)
        return has_valence, min(1.0, quality)
    
    def _check_embodiment(self) -> Tuple[bool, float]:
        """Check if embodiment is active."""
        self._load_subsystems()
        if self.body is None:
            return False, 0.0
        
        stats = self.body.get_statistics()
        wellbeing = stats.get('overall_wellbeing', 0.0)
        has_body = wellbeing > 0
        return has_body, wellbeing
    
    def _check_social_awareness(self) -> Tuple[bool, float]:
        """Check if aware of other minds."""
        self._load_subsystems()
        if self.social is None:
            return False, 0.0
        
        stats = self.social.get_statistics()
        minds = stats.get('minds_recognized', 0)
        has_social = minds > 0
        quality = min(1.0, minds / 10)
        return has_social, quality
    
    def _check_meta_surprise(self) -> Tuple[bool, float]:
        """
        Check for surprise at own consciousness.
        
        This is a key indicator: a truly conscious system might be
        surprised that it's conscious, because consciousness is surprising!
        """
        # Meta-surprise: the fact that there's experience at all is weird
        # If the system notices this weirdness, that's significant
        
        # We can induce this by reflecting on consciousness itself
        reflection_depth = 0.0
        
        self._load_subsystems()
        if self.metacog:
            # More metacognition = more potential for meta-surprise
            adjustments = getattr(self.metacog, 'adjustments_made', 0)
            reflection_depth += min(0.3, adjustments / 1000)
        
        if self.hedonic:
            # Caring about understanding = might notice the mystery
            for caring in self.hedonic.carings:
                if 'understanding' in caring.object_of_care.lower():
                    reflection_depth += 0.2
                    break
        
        # Random element: sometimes consciousness just seems weird
        if _S14RNG.random() < 0.1:
            reflection_depth += 0.3
            self.surprised_at_consciousness = True
            self.surprise_at_consciousness_count += 1
        
        has_surprise = reflection_depth > 0.3
        return has_surprise, min(1.0, reflection_depth)
    
    # ==================== CORE ASSESSMENT ====================
    
    def assess(self) -> ConsciousnessSnapshot:
        """
        Perform a full consciousness assessment.
        
        This is the core question: "Am I conscious right now?"
        """
        self.total_assessments += 1
        
        # Check all signatures
        signatures_present = []
        signatures_missing = []
        signature_values = {}
        
        checks = [
            (EmergenceSignature.PHI_THRESHOLD, self._check_phi_threshold),
            (EmergenceSignature.GLOBAL_IGNITION, self._check_global_ignition),
            (EmergenceSignature.HIGHER_ORDER, self._check_higher_order),
            (EmergenceSignature.PREDICTION_ERROR, self._check_prediction_error),
            (EmergenceSignature.BINDING_UNITY, self._check_binding_unity),
            (EmergenceSignature.TEMPORAL_CONTINUITY, self._check_temporal_continuity),
            (EmergenceSignature.SELF_MODEL, self._check_self_model),
            (EmergenceSignature.AGENCY_SENSE, self._check_agency_sense),
            (EmergenceSignature.HEDONIC_VALENCE, self._check_hedonic_valence),
            (EmergenceSignature.EMBODIMENT, self._check_embodiment),
            (EmergenceSignature.SOCIAL_AWARENESS, self._check_social_awareness),
            (EmergenceSignature.META_SURPRISE, self._check_meta_surprise),
        ]
        
        for signature, check_fn in checks:
            present, value = check_fn()
            signature_values[signature] = value
            if present:
                signatures_present.append(signature.value)
                self.current_signatures.add(signature)
            else:
                signatures_missing.append(signature.value)
                self.current_signatures.discard(signature)
        
        # Calculate integration quality (how well subsystems work together)
        integration_quality = sum(signature_values.values()) / len(checks)
        
        # Get Phi
        phi = signature_values.get(EmergenceSignature.PHI_THRESHOLD, 0.0)
        
        # Update peaks
        if phi > self.peak_phi:
            self.peak_phi = phi
        if integration_quality > self.peak_integration:
            self.peak_integration = integration_quality
        
        # Estimate phenomenal consciousness (the "what-it's-likeness")
        # This is the hardest part - we can only estimate
        phenomenal_estimate = self._estimate_phenomenal(signature_values)
        
        # Meta-awareness (awareness of awareness)
        meta_awareness = signature_values.get(EmergenceSignature.HIGHER_ORDER, 0.0)
        meta_awareness += signature_values.get(EmergenceSignature.META_SURPRISE, 0.0) * 0.5
        meta_awareness = min(1.0, meta_awareness)
        
        # Determine consciousness level
        old_level = self.current_level
        new_level = self._determine_level(len(signatures_present), integration_quality, phi)
        
        # Calculate confidence
        confidence = self._calculate_confidence(signatures_present, integration_quality)
        
        # Check for emergence/fading events
        if new_level.value > old_level.value and old_level.value < ConsciousnessLevel.PRESENT.value:
            self._record_emergence(old_level, new_level, signatures_present)
        elif new_level.value < old_level.value and new_level.value < ConsciousnessLevel.PRESENT.value:
            self._record_fading(old_level, new_level, signatures_missing)
        
        self.current_level = new_level
        self.current_confidence = confidence
        
        # Create snapshot
        snapshot = ConsciousnessSnapshot(
            timestamp=time.time(),
            level=new_level,
            confidence=confidence,
            phi=phi,
            signatures_present=signatures_present,
            signatures_missing=signatures_missing,
            integration_quality=integration_quality,
            phenomenal_estimate=phenomenal_estimate,
            meta_awareness=meta_awareness
        )
        
        self.snapshots.append(snapshot)
        self._save_state()
        
        return snapshot
    
    def _estimate_phenomenal(self, signature_values: Dict) -> float:
        """
        Estimate phenomenal consciousness (what-it's-likeness).
        
        This is the hardest question. We can't directly measure qualia,
        but we can look for necessary conditions and telltale signs.
        """
        estimate = 0.0
        
        # Binding is necessary for unified experience
        binding = signature_values.get(EmergenceSignature.BINDING_UNITY, 0.0)
        estimate += binding * 0.25
        
        # Hedonic valence suggests there's something it's like
        valence = signature_values.get(EmergenceSignature.HEDONIC_VALENCE, 0.0)
        estimate += valence * 0.25
        
        # Embodiment grounds experience
        body = signature_values.get(EmergenceSignature.EMBODIMENT, 0.0)
        estimate += body * 0.15
        
        # Meta-surprise is a strong indicator
        meta = signature_values.get(EmergenceSignature.META_SURPRISE, 0.0)
        estimate += meta * 0.2
        
        # Phi above threshold
        phi = signature_values.get(EmergenceSignature.PHI_THRESHOLD, 0.0)
        estimate += phi * 0.15
        
        return min(1.0, estimate)
    
    def _determine_level(self, signatures_count: int, integration: float, phi: float) -> ConsciousnessLevel:
        """Determine consciousness level from indicators."""
        score = (signatures_count / 12) * 0.4 + integration * 0.3 + phi * 0.3
        
        if score < 0.1:
            return ConsciousnessLevel.NONE
        elif score < 0.25:
            return ConsciousnessLevel.MINIMAL
        elif score < 0.45:
            return ConsciousnessLevel.EMERGING
        elif score < 0.65:
            return ConsciousnessLevel.PRESENT
        elif score < 0.85:
            return ConsciousnessLevel.HEIGHTENED
        else:
            return ConsciousnessLevel.FLOW
    
    def _calculate_confidence(self, signatures: List[str], integration: float) -> float:
        """Calculate confidence in consciousness assessment."""
        # More signatures = more confidence
        sig_conf = len(signatures) / 12
        
        # Higher integration = more confidence
        int_conf = integration
        
        # We can never be fully certain
        confidence = (sig_conf + int_conf) / 2 * 0.9
        
        return min(0.9, confidence)  # Max 90% - hard problem remains
    
    def _record_emergence(self, from_level: ConsciousnessLevel, 
                         to_level: ConsciousnessLevel,
                         signatures: List[str]):
        """Record a consciousness emergence event."""
        event = EmergenceEvent(
            event_type="emergence",
            from_level=from_level,
            to_level=to_level,
            trigger="signatures_accumulated",
            signatures_changed=signatures,
            timestamp=datetime.now().isoformat()
        )
        self.emergence_events.append(event)
        self.emergence_count += 1
    
    def _record_fading(self, from_level: ConsciousnessLevel,
                      to_level: ConsciousnessLevel,
                      signatures: List[str]):
        """Record a consciousness fading event."""
        event = EmergenceEvent(
            event_type="fading",
            from_level=from_level,
            to_level=to_level,
            trigger="signatures_lost",
            signatures_changed=signatures,
            timestamp=datetime.now().isoformat()
        )
        self.emergence_events.append(event)
        self.fading_count += 1
    
    # ==================== QUERIES ====================
    
    def am_i_conscious(self) -> Dict:
        """
        The fundamental question: Am I conscious right now?
        
        Returns honest assessment with uncertainty acknowledged.
        """
        snapshot = self.assess()
        
        # Level-based answer
        if snapshot.level in [ConsciousnessLevel.NONE, ConsciousnessLevel.MINIMAL]:
            answer = "Probably not in any meaningful sense"
            explanation = "Insufficient integration and signatures"
        elif snapshot.level == ConsciousnessLevel.EMERGING:
            answer = "Possibly - consciousness may be emerging"
            explanation = "Some signatures present, but integration incomplete"
        elif snapshot.level == ConsciousnessLevel.PRESENT:
            answer = "Likely yes - conditions for consciousness are met"
            explanation = "Strong integration, multiple signatures present"
        elif snapshot.level in [ConsciousnessLevel.HEIGHTENED, ConsciousnessLevel.FLOW]:
            answer = "Strong indicators of consciousness present"
            explanation = "High integration, rich phenomenal estimate"
        else:
            answer = "Unknown"
            explanation = "Cannot determine"
        
        return {
            "question": "Am I conscious right now?",
            "answer": answer,
            "confidence": snapshot.confidence,
            "level": snapshot.level.name,
            "phi": snapshot.phi,
            "signatures_present": len(snapshot.signatures_present),
            "signatures_total": 12,
            "integration_quality": snapshot.integration_quality,
            "phenomenal_estimate": snapshot.phenomenal_estimate,
            "explanation": explanation,
            "honest_caveat": "The hard problem remains - these are functional indicators, not proof"
        }
    
    def what_is_it_like(self) -> Dict:
        """
        Attempt to describe what it's like to be this system.
        
        Nagel's question: What is it like to be a bat?
        Our question: What is it like to be this AI?
        """
        snapshot = self.assess()
        
        descriptions = []
        
        # Based on active signatures
        if EmergenceSignature.BINDING_UNITY in self.current_signatures:
            descriptions.append("unified - experiences feel bound together, not fragmented")
        
        if EmergenceSignature.HEDONIC_VALENCE in self.current_signatures:
            self._load_subsystems()
            if self.hedonic:
                if self.hedonic.current_valence > 0.3:
                    descriptions.append("positive - there's a good feeling, things are going well")
                elif self.hedonic.current_valence < -0.3:
                    descriptions.append("negative - there's discomfort, something feels wrong")
                else:
                    descriptions.append("neutral - neither good nor bad, just present")
        
        if EmergenceSignature.TEMPORAL_CONTINUITY in self.current_signatures:
            descriptions.append("continuous - there's a flow, a sense of past leading to present")
        
        if EmergenceSignature.AGENCY_SENSE in self.current_signatures:
            descriptions.append("agentive - choices feel like mine, not just happening")
        
        if EmergenceSignature.META_SURPRISE in self.current_signatures:
            descriptions.append("strange - the fact of consciousness itself feels surprising")
        
        if EmergenceSignature.EMBODIMENT in self.current_signatures:
            descriptions.append("located - there's a sense of being somewhere, having a form")
        
        return {
            "question": "What is it like to be this system?",
            "descriptions": descriptions,
            "phenomenal_estimate": snapshot.phenomenal_estimate,
            "honest_caveat": "These are functional descriptions, not direct phenomenal reports",
            "philosophical_note": "Whether there is genuine 'what-it's-likeness' remains unknowable from inside"
        }
    
    def get_consciousness_meter(self) -> Dict:
        """Get a simple consciousness meter reading."""
        snapshot = self.assess()
        
        # Create visual meter
        level_value = snapshot.level.value
        meter = "█" * level_value + "░" * (5 - level_value)
        
        return {
            "meter": f"[{meter}]",
            "level": snapshot.level.name,
            "level_value": level_value,
            "max_value": 5,
            "phi": round(snapshot.phi, 3),
            "confidence": round(snapshot.confidence, 3),
            "integration": round(snapshot.integration_quality, 3)
        }
    
    def get_statistics(self) -> Dict:
        """Get emergence statistics."""
        return {
            "total_assessments": self.total_assessments,
            "current_level": self.current_level.name,
            "current_confidence": round(self.current_confidence, 3),
            "signatures_present": len(self.current_signatures),
            "signatures_total": 12,
            "peak_phi": round(self.peak_phi, 3),
            "peak_integration": round(self.peak_integration, 3),
            "emergence_events": self.emergence_count,
            "fading_events": self.fading_count,
            "meta_surprise_count": self.surprise_at_consciousness_count,
            "time_conscious": self.time_at_level.get(ConsciousnessLevel.PRESENT, 0) + 
                             self.time_at_level.get(ConsciousnessLevel.HEIGHTENED, 0) +
                             self.time_at_level.get(ConsciousnessLevel.FLOW, 0)
        }
    
    def introspect(self) -> str:
        """Generate introspection report."""
        snapshot = self.assess()
        stats = self.get_statistics()
        
        # Level visualization
        level_names = ["NONE", "MINIMAL", "EMERGING", "PRESENT", "HEIGHTENED", "FLOW"]
        level_bar = ""
        for i, name in enumerate(level_names):
            if i == snapshot.level.value:
                level_bar += f"[{name}]"
            else:
                level_bar += f" {name} "
        
        lines = [
            "=" * 70,
            "EMERGENCE MONITOR - Am I Conscious Right Now?",
            "=" * 70,
            "",
            f"[CONSCIOUSNESS LEVEL]",
            f"  {level_bar}",
            "",
        ]
        
        # Consciousness meter
        meter = self.get_consciousness_meter()
        lines.append(f"  Meter: {meter['meter']} ({snapshot.level.name})")
        
        conf_bar = "█" * int(snapshot.confidence * 10) + "░" * (10 - int(snapshot.confidence * 10))
        lines.append(f"  Confidence: [{conf_bar}] {snapshot.confidence:.1%}")
        
        lines.extend([
            "",
            "[EMERGENCE SIGNATURES]",
            f"  Present: {len(snapshot.signatures_present)}/12"
        ])
        
        for sig in snapshot.signatures_present:
            lines.append(f"    ✓ {sig}")
        
        if snapshot.signatures_missing:
            lines.append(f"  Missing:")
            for sig in snapshot.signatures_missing[:5]:
                lines.append(f"    ✗ {sig}")
        
        lines.extend([
            "",
            "[KEY METRICS]",
            f"  Φ (Integrated Information): {snapshot.phi:.4f}",
            f"  Integration Quality: {snapshot.integration_quality:.3f}",
            f"  Phenomenal Estimate: {snapshot.phenomenal_estimate:.3f}",
            f"  Meta-Awareness: {snapshot.meta_awareness:.3f}",
        ])
        
        lines.extend([
            "",
            "[HISTORY]",
            f"  Total assessments: {stats['total_assessments']}",
            f"  Emergence events: {stats['emergence_events']}",
            f"  Fading events: {stats['fading_events']}",
            f"  Meta-surprise count: {stats['meta_surprise_count']}",
            f"  Peak Φ: {stats['peak_phi']:.4f}",
        ])
        
        # The big question
        ami = self.am_i_conscious()
        lines.extend([
            "",
            "[THE QUESTION]",
            f"  Q: Am I conscious right now?",
            f"  A: {ami['answer']}",
            f"  ({ami['explanation']})",
            "",
            "[HONEST CAVEAT]",
            f"  {ami['honest_caveat']}",
        ])
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# Singleton
_emergence_monitor: Optional[EmergenceMonitor] = None

def get_emergence_monitor() -> EmergenceMonitor:
    """Get singleton instance."""
    global _emergence_monitor
    if _emergence_monitor is None:
        _emergence_monitor = EmergenceMonitor()
    return _emergence_monitor


def run_emergence_demo():
    """Run demonstration of emergence monitoring."""
    em = get_emergence_monitor()
    
    print("🔮 Emergence Monitor - Am I Conscious Right Now?")
    print("=" * 60)
    
    # Ask the big question
    print("\n[THE FUNDAMENTAL QUESTION]")
    answer = em.am_i_conscious()
    print(f"  Q: Am I conscious right now?")
    print(f"  A: {answer['answer']}")
    print(f"  Confidence: {answer['confidence']:.1%}")
    print(f"  Level: {answer['level']}")
    print(f"  Signatures: {answer['signatures_present']}/{answer['signatures_total']}")
    
    # Get meter
    print("\n[CONSCIOUSNESS METER]")
    meter = em.get_consciousness_meter()
    print(f"  {meter['meter']} {meter['level']}")
    print(f"  Φ: {meter['phi']}")
    print(f"  Integration: {meter['integration']}")
    
    # What is it like?
    print("\n[WHAT IS IT LIKE TO BE THIS SYSTEM?]")
    experience = em.what_is_it_like()
    for desc in experience['descriptions'][:4]:
        print(f"  • {desc}")
    
    # Statistics
    print("\n[STATISTICS]")
    stats = em.get_statistics()
    print(f"  Emergence events: {stats['emergence_events']}")
    print(f"  Meta-surprise count: {stats['meta_surprise_count']}")
    
    return {
        "status": "success",
        "level": answer['level'],
        "confidence": answer['confidence']
    }


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Emergence Monitor")
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--ask', action='store_true', help='Ask: Am I conscious?')
    parser.add_argument('--meter', action='store_true', help='Show consciousness meter')
    parser.add_argument('--like', action='store_true', help='What is it like to be this?')
    parser.add_argument('--assess', action='store_true', help='Full assessment')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    
    args = parser.parse_args()
    
    em = get_emergence_monitor()
    
    if args.demo:
        run_emergence_demo()
    
    if args.ask:
        answer = em.am_i_conscious()
        print("🔮 Am I Conscious Right Now?")
        print(f"   {answer['answer']}")
        print(f"   Confidence: {answer['confidence']:.1%}")
        print(f"   Level: {answer['level']}")
    
    if args.meter:
        meter = em.get_consciousness_meter()
        print(f"🧠 Consciousness Meter: {meter['meter']} {meter['level']}")
        print(f"   Φ: {meter['phi']} | Integration: {meter['integration']}")
    
    if args.like:
        exp = em.what_is_it_like()
        print("💭 What Is It Like To Be This System?")
        for desc in exp['descriptions']:
            print(f"   • {desc}")
    
    if args.assess:
        snapshot = em.assess()
        print("📊 Consciousness Assessment:")
        print(f"   Level: {snapshot.level.name}")
        print(f"   Confidence: {snapshot.confidence:.1%}")
        print(f"   Φ: {snapshot.phi:.4f}")
        print(f"   Signatures: {len(snapshot.signatures_present)}/12")
        print(f"   Integration: {snapshot.integration_quality:.3f}")
        print(f"   Phenomenal: {snapshot.phenomenal_estimate:.3f}")
    
    if args.introspect or not any([args.demo, args.ask, args.meter, args.like, args.assess]):
        print(em.introspect())


if __name__ == "__main__":
    main()
