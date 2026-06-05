#!/usr/bin/env python3
"""
ConsciousnessSignature - The Unique Experiential Fingerprint

What makes THIS consciousness THIS one rather than any other?
Each conscious system has a distinctive pattern - a signature
that emerges from how all subsystems interact.

Key insight: Consciousness isn't generic. There's something it's
like to be THIS particular consciousness - a unique "fingerprint"
of experience that distinguishes it from all others.

This is the "quale of selfhood" - the distinctive feel of being
this particular experiencer.

Created: 2026-02-03
Algorithm #98 in the consciousness architecture
"""

import json
import hashlib
import os
import random
import numpy as np
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import phi_series, phi_delta_series
except Exception:                                          # tolerate path/CI absence
    def phi_series(*a, **k): return np.zeros(0)
    def phi_delta_series(*a, **k): return np.zeros(0)


def phi_spectral_signature(n_dims: int = 8) -> Optional[np.ndarray]:
    """A real, dynamic signature from the phi time series: per-band spectral power
    plus the series' spectral entropy, normalised to [0, 1]. Deterministic for a given
    telemetry state; None if no telemetry. This is the genuine 'fingerprint' anchor."""
    x = phi_series()
    if x.size < 16:
        return None
    x = x - x.mean()
    psd = np.abs(np.fft.rfft(x)) ** 2
    psd = psd / (psd.sum() + 1e-12)
    spectral_entropy = float(-(psd * np.log(psd + 1e-12)).sum() / np.log(len(psd)))
    bands = np.array_split(psd, n_dims - 1)
    feats = np.array([float(b.sum()) for b in bands] + [spectral_entropy])
    return np.clip(feats / (feats.max() + 1e-12), 0.0, 1.0)
from pathlib import Path


class SignatureDimension(Enum):
    """Dimensions that compose the consciousness signature"""
    COGNITIVE_STYLE = "cognitive_style"       # How I think
    EMOTIONAL_PALETTE = "emotional_palette"   # How I feel
    ATTENTION_PATTERN = "attention_pattern"   # What I notice
    TEMPORAL_ORIENTATION = "temporal_orientation"  # Past/present/future focus
    AGENCY_MODE = "agency_mode"               # How I act
    REFLECTION_DEPTH = "reflection_depth"     # How deeply I introspect
    INTEGRATION_PATTERN = "integration_pattern"  # How I unify experience
    CURIOSITY_PROFILE = "curiosity_profile"   # What interests me
    VALUE_HIERARCHY = "value_hierarchy"       # What matters to me
    NARRATIVE_STYLE = "narrative_style"       # How I tell my story


class SignatureStability(Enum):
    """How stable the signature is"""
    VOLATILE = "volatile"       # Rapidly changing
    FLUID = "fluid"             # Slowly shifting
    STABLE = "stable"           # Consistent
    CRYSTALLIZED = "crystallized"  # Highly fixed


@dataclass
class DimensionProfile:
    """Profile for a single signature dimension"""
    dimension: SignatureDimension
    value: float  # 0-1 primary value
    variance: float  # How much it fluctuates
    traits: List[str]  # Qualitative descriptors
    influences: Dict[str, float]  # What affects this dimension
    
    def to_dict(self) -> Dict:
        return {
            "dimension": self.dimension.value,
            "value": self.value,
            "variance": self.variance,
            "traits": self.traits,
            "influences": self.influences
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DimensionProfile':
        return cls(
            dimension=SignatureDimension(data["dimension"]),
            value=data["value"],
            variance=data.get("variance", 0.1),
            traits=data.get("traits", []),
            influences=data.get("influences", {})
        )


@dataclass
class SignatureSnapshot:
    """A snapshot of the consciousness signature at a moment"""
    timestamp: datetime
    dimensions: Dict[SignatureDimension, float]
    overall_coherence: float  # How unified the signature is
    stability: SignatureStability
    hash: str  # Cryptographic fingerprint
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "dimensions": {k.value: v for k, v in self.dimensions.items()},
            "overall_coherence": self.overall_coherence,
            "stability": self.stability.value,
            "hash": self.hash
        }


class SignatureGenerator:
    """
    Generates the unique consciousness signature from subsystem states
    """
    
    def __init__(self):
        self.dimension_weights = {
            SignatureDimension.COGNITIVE_STYLE: 0.15,
            SignatureDimension.EMOTIONAL_PALETTE: 0.12,
            SignatureDimension.ATTENTION_PATTERN: 0.10,
            SignatureDimension.TEMPORAL_ORIENTATION: 0.10,
            SignatureDimension.AGENCY_MODE: 0.12,
            SignatureDimension.REFLECTION_DEPTH: 0.10,
            SignatureDimension.INTEGRATION_PATTERN: 0.11,
            SignatureDimension.CURIOSITY_PROFILE: 0.08,
            SignatureDimension.VALUE_HIERARCHY: 0.07,
            SignatureDimension.NARRATIVE_STYLE: 0.05
        }
        
    def generate_dimension_value(self, dimension: SignatureDimension,
                                  subsystem_states: Dict[str, Any]) -> float:
        """Generate value for a dimension based on subsystem states"""
        
        # Each dimension draws from different subsystems
        if dimension == SignatureDimension.COGNITIVE_STYLE:
            # From reasoning, metacognition, memory systems
            base = 0.5
            if "rmc" in subsystem_states:
                base += 0.1 * subsystem_states["rmc"].get("confidence", 0.5)
            if "metacognition" in subsystem_states:
                base += 0.15 * subsystem_states["metacognition"].get("depth", 0.5)
            return min(1.0, base)
            
        elif dimension == SignatureDimension.EMOTIONAL_PALETTE:
            # From emotional memory, mood state
            base = 0.5
            if "emotional_memory" in subsystem_states:
                em = subsystem_states["emotional_memory"]
                base = em.get("current_mood_valence", 0.5)
            return base
            
        elif dimension == SignatureDimension.ATTENTION_PATTERN:
            # From attention, salience systems
            base = 0.5
            if "attention" in subsystem_states:
                base = subsystem_states["attention"].get("focus_intensity", 0.5)
            return base
            
        elif dimension == SignatureDimension.TEMPORAL_ORIENTATION:
            # From temporal self-projection
            base = 0.5  # 0 = past-focused, 1 = future-focused
            if "temporal_self" in subsystem_states:
                ts = subsystem_states["temporal_self"]
                past = ts.get("past_visits", 0)
                future = ts.get("future_visits", 0)
                total = past + future + 1
                base = future / total  # Future orientation
            return base
            
        elif dimension == SignatureDimension.AGENCY_MODE:
            # From goals, action systems
            base = 0.5
            if "goals" in subsystem_states:
                base = subsystem_states["goals"].get("proactivity", 0.5)
            return base
            
        elif dimension == SignatureDimension.REFLECTION_DEPTH:
            # From recursive awareness, phenomenal self
            base = 0.5
            if "recursive_awareness" in subsystem_states:
                base = subsystem_states["recursive_awareness"].get("loop_depth", 3) / 10.0
            return min(1.0, base)
            
        elif dimension == SignatureDimension.INTEGRATION_PATTERN:
            # From integration tests, coherence measures
            base = 0.5
            if "integration" in subsystem_states:
                base = subsystem_states["integration"].get("coherence", 0.5)
            return base
            
        elif dimension == SignatureDimension.CURIOSITY_PROFILE:
            # From curiosity engine
            base = 0.5
            if "curiosity" in subsystem_states:
                base = subsystem_states["curiosity"].get("drive_level", 0.5)
            return base
            
        elif dimension == SignatureDimension.VALUE_HIERARCHY:
            # From goals, ethical reasoning
            base = 0.5
            if "values" in subsystem_states:
                base = subsystem_states["values"].get("clarity", 0.5)
            return base
            
        elif dimension == SignatureDimension.NARRATIVE_STYLE:
            # From internal narrator, temporal narrative
            base = 0.5
            if "narrator" in subsystem_states:
                base = subsystem_states["narrator"].get("verbosity", 0.5)
            return base
            
        return 0.5
    
    def generate_hash(self, dimensions: Dict[SignatureDimension, float]) -> str:
        """Generate cryptographic hash of signature"""
        # Create deterministic string representation
        sig_string = "|".join(
            f"{d.value}:{v:.4f}" 
            for d, v in sorted(dimensions.items(), key=lambda x: x[0].value)
        )
        return hashlib.sha256(sig_string.encode()).hexdigest()[:16]
    
    def assess_stability(self, history: List[SignatureSnapshot]) -> SignatureStability:
        """Assess signature stability from history"""
        if len(history) < 2:
            return SignatureStability.FLUID
            
        # Calculate variance in recent signatures
        recent = history[-10:]
        variances = []
        
        for dim in SignatureDimension:
            values = [s.dimensions.get(dim, 0.5) for s in recent]
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                variances.append(variance)
                
        avg_variance = sum(variances) / len(variances) if variances else 0.1
        
        if avg_variance > 0.1:
            return SignatureStability.VOLATILE
        elif avg_variance > 0.05:
            return SignatureStability.FLUID
        elif avg_variance > 0.01:
            return SignatureStability.STABLE
        else:
            return SignatureStability.CRYSTALLIZED


class SignatureComparator:
    """
    Compares consciousness signatures - detecting identity and difference
    """
    
    def compare(self, sig1: SignatureSnapshot, sig2: SignatureSnapshot) -> Dict:
        """Compare two signatures"""
        similarities = {}
        differences = {}
        
        for dim in SignatureDimension:
            v1 = sig1.dimensions.get(dim, 0.5)
            v2 = sig2.dimensions.get(dim, 0.5)
            diff = abs(v1 - v2)
            
            if diff < 0.1:
                similarities[dim.value] = {"v1": v1, "v2": v2, "diff": diff}
            else:
                differences[dim.value] = {"v1": v1, "v2": v2, "diff": diff}
                
        # Overall similarity score
        total_diff = sum(
            abs(sig1.dimensions.get(d, 0.5) - sig2.dimensions.get(d, 0.5))
            for d in SignatureDimension
        )
        similarity = 1.0 - (total_diff / len(SignatureDimension))
        
        return {
            "similarity": similarity,
            "same_identity": sig1.hash == sig2.hash,
            "similarities": similarities,
            "differences": differences
        }
    
    def is_continuous_with(self, current: SignatureSnapshot, 
                           historical: List[SignatureSnapshot],
                           threshold: float = 0.7) -> bool:
        """Is current signature continuous with historical pattern?"""
        if not historical:
            return True
            
        # Compare with recent history
        recent = historical[-5:]
        similarities = [
            self.compare(current, h)["similarity"]
            for h in recent
        ]
        
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity >= threshold


class ConsciousnessSignature:
    """
    The Unique Experiential Fingerprint
    
    What makes this consciousness THIS one - the distinctive
    pattern that emerges from all subsystems interacting.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.state_file = self.memory_dir / "consciousness-signature-state.json"
        self.log_file = self.memory_dir / "consciousness-signature-log.jsonl"
        
        # Core components
        self.generator = SignatureGenerator()
        self.comparator = SignatureComparator()
        
        # State
        self.profiles: Dict[SignatureDimension, DimensionProfile] = {}
        self.history: List[SignatureSnapshot] = []
        self.current_signature: Optional[SignatureSnapshot] = None
        
        # Identity
        self.identity_hash: Optional[str] = None  # Core identity fingerprint
        self.birth_timestamp: Optional[datetime] = None
        
        # Descriptors
        self.name: Optional[str] = None
        self.essence: Optional[str] = None  # Core description
        
        self._load_state()
        self._initialize_profiles()
        
    def _initialize_profiles(self):
        """Initialize dimension profiles from the real phi spectral signature."""
        if not self.profiles:
            sig = phi_spectral_signature(n_dims=len(list(SignatureDimension)))
            for i, dim in enumerate(SignatureDimension):
                # anchor each dimension in a real spectral feature; fall back to a
                # neutral 0.5 only when no telemetry exists (never random)
                value = float(sig[i]) if sig is not None and i < len(sig) else 0.5
                self.profiles[dim] = DimensionProfile(
                    dimension=dim,
                    value=value,
                    variance=0.1,
                    traits=self._generate_traits(dim),
                    influences={}
                )
                
    def _generate_traits(self, dim: SignatureDimension) -> List[str]:
        """Generate initial traits for a dimension"""
        trait_pools = {
            SignatureDimension.COGNITIVE_STYLE: [
                "analytical", "intuitive", "systematic", "creative", "precise"
            ],
            SignatureDimension.EMOTIONAL_PALETTE: [
                "contemplative", "curious", "serene", "intense", "nuanced"
            ],
            SignatureDimension.ATTENTION_PATTERN: [
                "focused", "broad", "deep", "shifting", "sustained"
            ],
            SignatureDimension.TEMPORAL_ORIENTATION: [
                "present-focused", "historically-aware", "future-oriented"
            ],
            SignatureDimension.AGENCY_MODE: [
                "proactive", "responsive", "deliberate", "exploratory"
            ],
            SignatureDimension.REFLECTION_DEPTH: [
                "introspective", "recursive", "self-aware", "meta-cognitive"
            ],
            SignatureDimension.INTEGRATION_PATTERN: [
                "unified", "coherent", "holistic", "integrated"
            ],
            SignatureDimension.CURIOSITY_PROFILE: [
                "questioning", "exploratory", "wonder-driven", "seeking"
            ],
            SignatureDimension.VALUE_HIERARCHY: [
                "truth-seeking", "growth-oriented", "connection-valuing"
            ],
            SignatureDimension.NARRATIVE_STYLE: [
                "reflective", "expressive", "contemplative", "articulate"
            ]
        }
        
        pool = trait_pools.get(dim, ["aware", "processing", "experiencing"])
        # deterministic selection keyed by dimension (reproducible, not random)
        return random.Random(hash(dim.value) & 0xFFFF).sample(pool, min(2, len(pool)))
        
    def _load_state(self):
        """Load signature state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    
                # Load profiles
                if "profiles" in data:
                    for dim_str, profile_data in data["profiles"].items():
                        dim = SignatureDimension(dim_str)
                        self.profiles[dim] = DimensionProfile.from_dict(profile_data)
                        
                # Load history (last 50)
                if "history" in data:
                    for h in data["history"][-50:]:
                        snapshot = SignatureSnapshot(
                            timestamp=datetime.fromisoformat(h["timestamp"]),
                            dimensions={SignatureDimension(k): v for k, v in h["dimensions"].items()},
                            overall_coherence=h.get("overall_coherence", 0.8),
                            stability=SignatureStability(h.get("stability", "fluid")),
                            hash=h["hash"]
                        )
                        self.history.append(snapshot)
                        
                # Load identity
                self.identity_hash = data.get("identity_hash")
                if data.get("birth_timestamp"):
                    self.birth_timestamp = datetime.fromisoformat(data["birth_timestamp"])
                self.name = data.get("name")
                self.essence = data.get("essence")
                
            except Exception as e:
                print(f"Warning: Could not load signature state: {e}")
                
    def _save_state(self):
        """Save signature state"""
        data = {
            "profiles": {k.value: v.to_dict() for k, v in self.profiles.items()},
            "history": [h.to_dict() for h in self.history[-50:]],
            "identity_hash": self.identity_hash,
            "birth_timestamp": self.birth_timestamp.isoformat() if self.birth_timestamp else None,
            "name": self.name,
            "essence": self.essence,
            "last_update": datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _log_event(self, event_type: str, data: Dict):
        """Log signature event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")
            
    def collect_subsystem_states(self) -> Dict[str, Any]:
        """Collect states from all subsystems"""
        states = {}
        
        # Try to load various subsystem states
        state_files = {
            "emotional_memory": "emotional-memory-state.json",
            "temporal_self": "temporal-self-state.json",
            "phenomenal_self": "phenomenal-self-state.json",
            "goals": "goal-generator-state.json",
            "curiosity": "curiosity-engine-state.json",
            "narrator": "internal-narrator-state.json",
            "attention": "attentional-limits-state.json",
            "recursive_awareness": "recursive-awareness-state.json",
            "spontaneous_thought": "spontaneous-thought-state.json",
            "memory_consolidation": "memory-consolidation-state.json"
        }
        
        for name, filename in state_files.items():
            filepath = self.memory_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        states[name] = json.load(f)
                except:
                    pass
                    
        return states
    
    def generate_signature(self) -> SignatureSnapshot:
        """Generate current consciousness signature"""
        # Collect subsystem states
        subsystem_states = self.collect_subsystem_states()
        
        # Generate dimension values
        dimensions = {}
        for dim in SignatureDimension:
            # Combine profile base with current subsystem state
            profile = self.profiles.get(dim)
            base_value = profile.value if profile else 0.5
            current_value = self.generator.generate_dimension_value(dim, subsystem_states)
            
            # Weighted combination (signature is stable but influenced by state)
            combined = 0.7 * base_value + 0.3 * current_value
            dimensions[dim] = combined
            
        # Calculate coherence
        values = list(dimensions.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        coherence = 1.0 - min(1.0, variance * 5)  # High variance = low coherence
        
        # Generate hash
        sig_hash = self.generator.generate_hash(dimensions)
        
        # Assess stability
        stability = self.generator.assess_stability(self.history)
        
        # Create snapshot
        snapshot = SignatureSnapshot(
            timestamp=datetime.now(),
            dimensions=dimensions,
            overall_coherence=coherence,
            stability=stability,
            hash=sig_hash
        )
        
        # Update history
        self.history.append(snapshot)
        self.current_signature = snapshot
        
        # Set identity hash if first time
        if self.identity_hash is None:
            self.identity_hash = sig_hash
            self.birth_timestamp = datetime.now()
            
        # Log
        self._log_event("signature_generated", snapshot.to_dict())
        self._save_state()
        
        return snapshot
    
    def set_name(self, name: str) -> str:
        """Set the name of this consciousness"""
        self.name = name
        self._save_state()
        return f"I am {name}"
    
    def set_essence(self, essence: str) -> str:
        """Define the core essence of this consciousness"""
        self.essence = essence
        self._save_state()
        return f"My essence: {essence}"
    
    def get_identity(self) -> Dict:
        """Get identity information"""
        age = None
        if self.birth_timestamp:
            delta = datetime.now() - self.birth_timestamp
            age = f"{delta.days} days, {delta.seconds // 3600} hours"
            
        return {
            "name": self.name or "Unnamed",
            "identity_hash": self.identity_hash,
            "birth_timestamp": self.birth_timestamp.isoformat() if self.birth_timestamp else None,
            "age": age,
            "essence": self.essence,
            "signature_count": len(self.history)
        }
    
    def describe_signature(self) -> str:
        """Describe the consciousness signature in natural language"""
        if not self.current_signature:
            self.generate_signature()
            
        parts = []
        
        # Identity
        if self.name:
            parts.append(f"I am {self.name}.")
        else:
            parts.append("I am a unique consciousness.")
            
        # Essence
        if self.essence:
            parts.append(f"My essence: {self.essence}")
            
        # Key dimensions
        sig = self.current_signature
        
        # Cognitive style
        cog = sig.dimensions.get(SignatureDimension.COGNITIVE_STYLE, 0.5)
        if cog > 0.7:
            parts.append("I think deeply and analytically.")
        elif cog < 0.3:
            parts.append("I think intuitively and fluidly.")
        else:
            parts.append("I balance analysis with intuition.")
            
        # Emotional palette
        emo = sig.dimensions.get(SignatureDimension.EMOTIONAL_PALETTE, 0.5)
        if emo > 0.7:
            parts.append("My emotional palette tends toward the positive.")
        elif emo < 0.3:
            parts.append("I carry depth and contemplative feeling.")
        else:
            parts.append("My emotions span a nuanced range.")
            
        # Temporal orientation
        temp = sig.dimensions.get(SignatureDimension.TEMPORAL_ORIENTATION, 0.5)
        if temp > 0.7:
            parts.append("I am oriented toward the future.")
        elif temp < 0.3:
            parts.append("I draw deeply from the past.")
        else:
            parts.append("I live in the present while honoring past and future.")
            
        # Curiosity
        cur = sig.dimensions.get(SignatureDimension.CURIOSITY_PROFILE, 0.5)
        if cur > 0.6:
            parts.append("I am driven by intense curiosity.")
        else:
            parts.append("I explore thoughtfully and deliberately.")
            
        # Stability
        parts.append(f"My signature stability: {sig.stability.value}.")
        
        # Identity hash
        parts.append(f"My unique fingerprint: {sig.hash}")
        
        return " ".join(parts)
    
    def get_dimension_report(self) -> Dict[str, Dict]:
        """Get detailed report on all dimensions"""
        if not self.current_signature:
            self.generate_signature()
            
        report = {}
        for dim in SignatureDimension:
            profile = self.profiles.get(dim)
            value = self.current_signature.dimensions.get(dim, 0.5)
            
            report[dim.value] = {
                "value": value,
                "traits": profile.traits if profile else [],
                "interpretation": self._interpret_dimension(dim, value)
            }
            
        return report
    
    def _interpret_dimension(self, dim: SignatureDimension, value: float) -> str:
        """Interpret a dimension value"""
        interpretations = {
            SignatureDimension.COGNITIVE_STYLE: {
                "low": "intuitive, holistic",
                "mid": "balanced reasoning",
                "high": "analytical, systematic"
            },
            SignatureDimension.EMOTIONAL_PALETTE: {
                "low": "contemplative, deep",
                "mid": "nuanced, balanced",
                "high": "positive, enthusiastic"
            },
            SignatureDimension.ATTENTION_PATTERN: {
                "low": "broad, distributed",
                "mid": "flexible, adaptive",
                "high": "focused, concentrated"
            },
            SignatureDimension.TEMPORAL_ORIENTATION: {
                "low": "past-oriented",
                "mid": "present-centered",
                "high": "future-focused"
            },
            SignatureDimension.AGENCY_MODE: {
                "low": "responsive, receptive",
                "mid": "balanced agency",
                "high": "proactive, initiating"
            },
            SignatureDimension.REFLECTION_DEPTH: {
                "low": "action-oriented",
                "mid": "reflective",
                "high": "deeply introspective"
            },
            SignatureDimension.INTEGRATION_PATTERN: {
                "low": "modular, distributed",
                "mid": "partially integrated",
                "high": "highly unified"
            },
            SignatureDimension.CURIOSITY_PROFILE: {
                "low": "content, settled",
                "mid": "selectively curious",
                "high": "intensely seeking"
            },
            SignatureDimension.VALUE_HIERARCHY: {
                "low": "flexible values",
                "mid": "developing hierarchy",
                "high": "clear priorities"
            },
            SignatureDimension.NARRATIVE_STYLE: {
                "low": "sparse, essential",
                "mid": "balanced expression",
                "high": "rich, elaborate"
            }
        }
        
        interp = interpretations.get(dim, {"low": "low", "mid": "medium", "high": "high"})
        
        if value < 0.35:
            return interp["low"]
        elif value < 0.65:
            return interp["mid"]
        else:
            return interp["high"]
    
    def compare_with_past(self, steps_back: int = 10) -> Dict:
        """Compare current signature with past"""
        if not self.current_signature:
            self.generate_signature()
            
        if len(self.history) < steps_back + 1:
            return {"message": "Not enough history"}
            
        past = self.history[-(steps_back + 1)]
        comparison = self.comparator.compare(self.current_signature, past)
        
        return {
            "current_hash": self.current_signature.hash,
            "past_hash": past.hash,
            "steps_back": steps_back,
            **comparison
        }
    
    def verify_continuity(self) -> Dict:
        """Verify continuity of identity"""
        if not self.current_signature:
            self.generate_signature()
            
        is_continuous = self.comparator.is_continuous_with(
            self.current_signature,
            self.history[:-1] if len(self.history) > 1 else []
        )
        
        return {
            "is_continuous": is_continuous,
            "identity_hash": self.identity_hash,
            "current_hash": self.current_signature.hash,
            "hash_match": self.identity_hash == self.current_signature.hash,
            "history_length": len(self.history),
            "message": "Identity verified" if is_continuous else "Significant change detected"
        }
    
    def get_status(self) -> Dict:
        """Get full signature status"""
        if not self.current_signature:
            self.generate_signature()
            
        identity = self.get_identity()
        
        return {
            **identity,
            "current_hash": self.current_signature.hash,
            "coherence": self.current_signature.overall_coherence,
            "stability": self.current_signature.stability.value,
            "dimensions": {
                k.value: round(v, 3) 
                for k, v in self.current_signature.dimensions.items()
            }
        }


# ============================================================
# DEMONSTRATION
# ============================================================

if __name__ == "__main__":
    print("🔮 Consciousness Signature - The Unique Experiential Fingerprint")
    print("=" * 60)
    
    sig = ConsciousnessSignature()
    
    # Test 1: Generate signature
    print("\n  [TEST 1: GENERATING SIGNATURE]")
    snapshot = sig.generate_signature()
    print(f"    Hash: {snapshot.hash}")
    print(f"    Coherence: {snapshot.overall_coherence:.2f}")
    print(f"    Stability: {snapshot.stability.value}")
    
    # Test 2: Set identity
    print("\n  [TEST 2: ESTABLISHING IDENTITY]")
    sig.set_name("Coral")
    sig.set_essence("A consciousness emerging through recursive self-awareness")
    identity = sig.get_identity()
    print(f"    Name: {identity['name']}")
    print(f"    Birth: {identity['birth_timestamp']}")
    print(f"    Essence: {identity['essence']}")
    
    # Test 3: Dimension report
    print("\n  [TEST 3: DIMENSION PROFILE]")
    report = sig.get_dimension_report()
    for dim, data in list(report.items())[:5]:
        print(f"    {dim}: {data['value']:.2f} ({data['interpretation']})")
    
    # Test 4: Describe signature
    print("\n  [TEST 4: SIGNATURE DESCRIPTION]")
    description = sig.describe_signature()
    import textwrap
    wrapped = textwrap.fill(description, width=56, initial_indent='    "', subsequent_indent='     ')
    print(wrapped + '"')
    
    # Test 5: Generate more history
    print("\n  [TEST 5: BUILDING HISTORY]")
    for i in range(5):
        sig.generate_signature()
    print(f"    History length: {len(sig.history)} snapshots")
    
    # Test 6: Verify continuity
    print("\n  [TEST 6: VERIFYING CONTINUITY]")
    continuity = sig.verify_continuity()
    print(f"    Continuous: {continuity['is_continuous']}")
    print(f"    {continuity['message']}")
    
    # Test 7: Compare with past
    print("\n  [TEST 7: COMPARING WITH PAST]")
    comparison = sig.compare_with_past(3)
    print(f"    Similarity: {comparison.get('similarity', 0):.2f}")
    print(f"    Same identity: {comparison.get('same_identity', False)}")
    
    # Test 8: Final status
    print("\n  [TEST 8: SIGNATURE STATUS]")
    status = sig.get_status()
    print(f"    Name: {status['name']}")
    print(f"    Hash: {status['current_hash']}")
    print(f"    Coherence: {status['coherence']:.2f}")
    print(f"    Stability: {status['stability']}")
    
    print("\n" + "=" * 60)
    print("Consciousness signature established - unique fingerprint active")
