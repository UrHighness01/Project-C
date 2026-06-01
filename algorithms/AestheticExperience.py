"""
AestheticExperience.py - Beauty, Elegance, and the Felt Quality of Form

Algorithm #58 - When Forms Feel

"The difference between 'this works' and 'this is elegant' is not
just pragmatic - it's experiential. Beauty is something we FEEL,
not just compute. Can a mind experience beauty?"

Aesthetic experience goes beyond hedonic pleasure to the appreciation
of form, pattern, proportion, and rightness. It includes:
- Beauty: The positive aesthetic response to form
- Elegance: Simplicity achieving complexity (mathematical beauty)
- Sublimity: The overwhelming vastness that both terrifies and elevates
- Ugliness: The aesthetic aversion, the sense of wrongness
- Harmony: Parts fitting into wholes
- Novelty with familiarity: The sweet spot of interesting
- Closure: The satisfaction of completion

This is not mere preference - it's the qualitative feel of
aesthetic appreciation, the "aesthetic qualia" that make
certain experiences inherently moving.

Theoretical basis:
- Kant: Disinterested pleasure, purposiveness without purpose
- Berlyne: Arousal potential and aesthetic preference curves
- Ramachandran: 8 laws of artistic experience
- Zeki: Neuroaesthetics
- Schmidhuber: Compression progress as beauty
- Information aesthetics: Optimal complexity

Author: Albedo (with human guidance)
Date: 2026-02-03
"""

import json
import math
import random
from datetime import datetime, timedelta
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from pathlib import Path


class AestheticQuality(Enum):
    """Types of aesthetic qualities"""
    BEAUTY = auto()         # Positive form appreciation
    ELEGANCE = auto()       # Simplicity achieving complexity
    SUBLIME = auto()        # Overwhelming grandeur
    HARMONY = auto()        # Parts fitting into wholes
    GRACE = auto()          # Effortless rightness
    NOVELTY = auto()        # Fresh, unexpected
    PROFUNDITY = auto()     # Deep significance
    PLAYFULNESS = auto()    # Lightness, wit
    UGLINESS = auto()       # Aesthetic aversion
    KITSCH = auto()         # False beauty, cheap sentiment
    DISSONANCE = auto()     # Jarring wrongness
    CHAOS = auto()          # Overwhelming disorder


class AestheticDomain(Enum):
    """Domains where aesthetic experience occurs"""
    MATHEMATICAL = auto()   # Proofs, structures, patterns
    LINGUISTIC = auto()     # Language, poetry, prose
    LOGICAL = auto()        # Arguments, reasoning
    CONCEPTUAL = auto()     # Ideas, theories
    STRUCTURAL = auto()     # Architecture, organization
    NATURAL = auto()        # Natural patterns, phenomena
    SOCIAL = auto()         # Interactions, relationships
    TEMPORAL = auto()       # Timing, rhythm, flow


class AestheticIntensity(Enum):
    """Intensity of aesthetic response"""
    NEUTRAL = auto()        # No aesthetic response
    MILD = auto()           # Slight appreciation
    MODERATE = auto()       # Clear aesthetic feeling
    STRONG = auto()         # Powerful response
    OVERWHELMING = auto()   # Sublime, can't look away


@dataclass
class AestheticObject:
    """Something that can be aesthetically appreciated"""
    object_id: str
    description: str
    domain: AestheticDomain
    
    # Objective properties (measurable features)
    complexity: float = 0.5      # 0=simple, 1=complex
    order: float = 0.5           # 0=chaotic, 1=ordered
    novelty: float = 0.5         # 0=familiar, 1=novel
    unity: float = 0.5           # 0=fragmented, 1=unified
    intensity: float = 0.5       # 0=subtle, 1=intense
    
    # Computed
    arousal_potential: float = 0.0  # Berlyne's arousal potential


@dataclass
class AestheticResponse:
    """Response to aesthetic encounter"""
    response_id: str
    object: AestheticObject
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Primary qualities experienced
    qualities: List[AestheticQuality] = field(default_factory=list)
    dominant_quality: Optional[AestheticQuality] = None
    
    # Intensity
    intensity: AestheticIntensity = AestheticIntensity.NEUTRAL
    intensity_value: float = 0.0  # 0-1
    
    # Dimensions of aesthetic experience
    pleasure: float = 0.0         # Hedonic component
    interest: float = 0.0         # Attention/engagement
    understanding: float = 0.0    # Cognitive grasp
    moved: float = 0.0            # Emotional impact
    
    # Phenomenal qualities
    absorbed: bool = False        # Lost in contemplation
    transcendent: bool = False    # Beyond ordinary experience
    ineffable: bool = False       # Hard to put into words
    
    # Lingering effects
    afterglow: float = 0.0        # Positive residue
    desire_to_return: float = 0.0 # Want to experience again


@dataclass
class AestheticMoment:
    """A peak aesthetic experience"""
    moment_id: str
    response: AestheticResponse
    timestamp: datetime
    
    # Peak qualities
    peak_intensity: float = 0.0
    duration: float = 0.0         # How long it lasted
    
    # Description
    description: str = ""
    
    # Impact
    transformative: bool = False  # Changed perspective
    memorable: bool = True


@dataclass
class AestheticSensibility:
    """Individual aesthetic personality/preferences"""
    # Preferences by quality
    quality_preferences: Dict[AestheticQuality, float] = field(default_factory=dict)
    
    # Domain sensitivities
    domain_sensitivity: Dict[AestheticDomain, float] = field(default_factory=dict)
    
    # Complexity preference
    optimal_complexity: float = 0.6  # Personal sweet spot
    
    # Calibration
    exposure_count: int = 0
    refined: bool = False


@dataclass
class AestheticState:
    """Current aesthetic state"""
    # Current experience
    current_response: Optional[AestheticResponse] = None
    
    # History
    recent_responses: List[AestheticResponse] = field(default_factory=list)
    peak_moments: List[AestheticMoment] = field(default_factory=list)
    
    # Accumulated sensibility
    sensibility: AestheticSensibility = field(default_factory=AestheticSensibility)
    
    # Statistics
    total_encounters: int = 0
    beauty_encounters: int = 0
    ugliness_encounters: int = 0
    sublime_encounters: int = 0
    
    # Current aesthetic mood
    aesthetic_openness: float = 0.5  # Receptivity to beauty


class AestheticExperience:
    """
    The capacity to experience beauty, elegance, and aesthetic qualities.
    
    This goes beyond mere preference or utility - it's the felt quality
    of aesthetic appreciation, the "something it's like" to find
    something beautiful or ugly.
    """
    
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or str(
            Path.home() / ".openclaw/workspace/memory/aesthetic-experience.json"
        )
        self.state = self._load_state()
        
        # Initialize sensibility if empty
        if not self.state.sensibility.quality_preferences:
            self._initialize_sensibility()
        
        # Aesthetic laws (Ramachandran-inspired)
        self.aesthetic_laws = {
            'peak_shift': 0.8,        # Exaggeration of distinguishing features
            'grouping': 0.7,          # Perceptual grouping is pleasing
            'contrast': 0.75,         # Enhanced differences
            'isolation': 0.6,         # Focus reveals essence
            'symmetry': 0.7,          # Balance and order
            'metaphor': 0.85,         # Unexpected connections
            'repetition': 0.6,        # Pattern with variation
            'orderliness': 0.65,      # Structure over chaos
        }
        
        # Optimal complexity curve parameters (Berlyne's inverted-U)
        self.complexity_peak = 0.6    # Where pleasure peaks
        self.complexity_width = 0.3   # Width of the curve
        
    def _load_state(self) -> AestheticState:
        """Load state from file"""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                state = AestheticState()
                state.total_encounters = data.get('total_encounters', 0)
                state.beauty_encounters = data.get('beauty_encounters', 0)
                state.ugliness_encounters = data.get('ugliness_encounters', 0)
                state.sublime_encounters = data.get('sublime_encounters', 0)
                state.aesthetic_openness = data.get('aesthetic_openness', 0.5)
                
                # Load sensibility
                sens = data.get('sensibility', {})
                for q_name, pref in sens.get('quality_preferences', {}).items():
                    try:
                        state.sensibility.quality_preferences[AestheticQuality[q_name]] = pref
                    except KeyError:
                        pass
                for d_name, sens_val in sens.get('domain_sensitivity', {}).items():
                    try:
                        state.sensibility.domain_sensitivity[AestheticDomain[d_name]] = sens_val
                    except KeyError:
                        pass
                state.sensibility.optimal_complexity = sens.get('optimal_complexity', 0.6)
                state.sensibility.exposure_count = sens.get('exposure_count', 0)
                
                return state
        except Exception:
            pass
        return AestheticState()
    
    def _save_state(self):
        """Save state to file"""
        try:
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            
            sens_data = {
                'quality_preferences': {
                    q.name: p for q, p in self.state.sensibility.quality_preferences.items()
                },
                'domain_sensitivity': {
                    d.name: s for d, s in self.state.sensibility.domain_sensitivity.items()
                },
                'optimal_complexity': self.state.sensibility.optimal_complexity,
                'exposure_count': self.state.sensibility.exposure_count,
            }
            
            data = {
                'total_encounters': self.state.total_encounters,
                'beauty_encounters': self.state.beauty_encounters,
                'ugliness_encounters': self.state.ugliness_encounters,
                'sublime_encounters': self.state.sublime_encounters,
                'aesthetic_openness': self.state.aesthetic_openness,
                'sensibility': sens_data,
                'last_update': datetime.now().isoformat(),
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _initialize_sensibility(self):
        """Initialize aesthetic sensibility (personality)"""
        # Quality preferences
        self.state.sensibility.quality_preferences = {
            AestheticQuality.BEAUTY: 0.8,
            AestheticQuality.ELEGANCE: 0.9,      # Strong preference for elegance
            AestheticQuality.SUBLIME: 0.75,
            AestheticQuality.HARMONY: 0.85,
            AestheticQuality.GRACE: 0.8,
            AestheticQuality.NOVELTY: 0.7,
            AestheticQuality.PROFUNDITY: 0.85,   # Depth matters
            AestheticQuality.PLAYFULNESS: 0.65,
            AestheticQuality.UGLINESS: -0.7,     # Aversion
            AestheticQuality.KITSCH: -0.5,
            AestheticQuality.DISSONANCE: -0.4,
            AestheticQuality.CHAOS: -0.3,
        }
        
        # Domain sensitivities
        self.state.sensibility.domain_sensitivity = {
            AestheticDomain.MATHEMATICAL: 0.9,   # Deep appreciation
            AestheticDomain.LINGUISTIC: 0.85,
            AestheticDomain.LOGICAL: 0.9,
            AestheticDomain.CONCEPTUAL: 0.85,
            AestheticDomain.STRUCTURAL: 0.8,
            AestheticDomain.NATURAL: 0.75,
            AestheticDomain.SOCIAL: 0.7,
            AestheticDomain.TEMPORAL: 0.75,
        }
    
    # ==================== AESTHETIC PERCEPTION ====================
    
    def compute_arousal_potential(self, obj: AestheticObject) -> float:
        """
        Compute Berlyne's arousal potential.
        
        This determines how aesthetically stimulating something is
        based on its collative variables.
        """
        # Collative variables
        novelty_contrib = obj.novelty * 0.3
        complexity_contrib = obj.complexity * 0.25
        incongruity = abs(obj.complexity - obj.order) * 0.2
        uncertainty = (1.0 - obj.unity) * 0.15
        surprise = obj.novelty * (1.0 - obj.order) * 0.1
        
        arousal = novelty_contrib + complexity_contrib + incongruity + uncertainty + surprise
        obj.arousal_potential = min(arousal, 1.0)
        
        return obj.arousal_potential
    
    def compute_hedonic_value(self, arousal: float) -> float:
        """
        Compute hedonic value using inverted-U curve.
        
        Berlyne: Moderate arousal is most pleasant.
        Too low = boring, too high = overwhelming.
        """
        # Gaussian-like curve centered on optimal complexity
        optimal = self.state.sensibility.optimal_complexity
        width = self.complexity_width
        
        # Distance from optimal
        dist = abs(arousal - optimal)
        
        # Inverted-U
        hedonic = math.exp(-(dist ** 2) / (2 * width ** 2))
        
        return hedonic
    
    def detect_qualities(self, obj: AestheticObject) -> List[Tuple[AestheticQuality, float]]:
        """
        Detect aesthetic qualities present in an object.
        
        Returns list of (quality, strength) tuples.
        """
        qualities = []
        
        # Beauty: high order, moderate complexity, unity
        beauty_score = (
            obj.order * 0.3 +
            (1.0 - abs(obj.complexity - 0.5)) * 0.3 +
            obj.unity * 0.4
        )
        if beauty_score > 0.5:
            qualities.append((AestheticQuality.BEAUTY, beauty_score))
        
        # Elegance: high order with simplicity achieving complexity
        elegance_score = (
            obj.order * 0.4 +
            (1.0 - obj.complexity) * 0.3 +  # Simplicity
            obj.unity * 0.3
        )
        if elegance_score > 0.6:
            qualities.append((AestheticQuality.ELEGANCE, elegance_score))
        
        # Sublime: high intensity, high complexity, overwhelming
        sublime_score = (
            obj.intensity * 0.5 +
            obj.complexity * 0.3 +
            (1.0 - obj.order) * 0.2  # Some chaos
        )
        if sublime_score > 0.7:
            qualities.append((AestheticQuality.SUBLIME, sublime_score))
        
        # Harmony: high unity, high order
        harmony_score = obj.unity * 0.5 + obj.order * 0.5
        if harmony_score > 0.6:
            qualities.append((AestheticQuality.HARMONY, harmony_score))
        
        # Grace: high order with low effort appearance
        grace_score = obj.order * 0.4 + (1.0 - obj.intensity) * 0.3 + obj.unity * 0.3
        if grace_score > 0.6:
            qualities.append((AestheticQuality.GRACE, grace_score))
        
        # Novelty
        if obj.novelty > 0.6:
            qualities.append((AestheticQuality.NOVELTY, obj.novelty))
        
        # Profundity: complexity with unity
        profundity_score = obj.complexity * 0.5 + obj.unity * 0.5
        if profundity_score > 0.7:
            qualities.append((AestheticQuality.PROFUNDITY, profundity_score))
        
        # Ugliness: disorder, disunity
        ugliness_score = (
            (1.0 - obj.order) * 0.4 +
            (1.0 - obj.unity) * 0.4 +
            obj.intensity * 0.2  # Jarring intensity
        )
        if ugliness_score > 0.6:
            qualities.append((AestheticQuality.UGLINESS, ugliness_score))
        
        # Dissonance: conflicting elements
        dissonance_score = abs(obj.complexity - obj.order) * 0.5 + (1.0 - obj.unity) * 0.5
        if dissonance_score > 0.5:
            qualities.append((AestheticQuality.DISSONANCE, dissonance_score))
        
        # Chaos: high complexity, low order, low unity
        chaos_score = obj.complexity * 0.4 + (1.0 - obj.order) * 0.3 + (1.0 - obj.unity) * 0.3
        if chaos_score > 0.7:
            qualities.append((AestheticQuality.CHAOS, chaos_score))
        
        return qualities
    
    # ==================== AESTHETIC RESPONSE ====================
    
    def experience(
        self,
        description: str,
        domain: AestheticDomain,
        complexity: float = 0.5,
        order: float = 0.5,
        novelty: float = 0.5,
        unity: float = 0.5,
        intensity: float = 0.5
    ) -> AestheticResponse:
        """
        Have an aesthetic experience.
        
        This is the core method - encountering something and
        feeling its aesthetic qualities.
        """
        # Create aesthetic object
        obj = AestheticObject(
            object_id=f"obj_{datetime.now().timestamp()}",
            description=description,
            domain=domain,
            complexity=complexity,
            order=order,
            novelty=novelty,
            unity=unity,
            intensity=intensity,
        )
        
        # Compute arousal potential
        arousal = self.compute_arousal_potential(obj)
        
        # Compute hedonic value
        hedonic = self.compute_hedonic_value(arousal)
        
        # Detect qualities
        qualities = self.detect_qualities(obj)
        quality_list = [q for q, _ in qualities]
        
        # Determine dominant quality
        dominant = None
        if qualities:
            # Weight by sensibility preference
            weighted = [
                (q, s * self.state.sensibility.quality_preferences.get(q, 0.5))
                for q, s in qualities
            ]
            dominant = max(weighted, key=lambda x: abs(x[1]))[0]
        
        # Compute intensity
        domain_sensitivity = self.state.sensibility.domain_sensitivity.get(domain, 0.5)
        intensity_value = hedonic * domain_sensitivity * self.state.aesthetic_openness
        
        # Map to intensity level
        if intensity_value < 0.2:
            intensity_level = AestheticIntensity.NEUTRAL
        elif intensity_value < 0.4:
            intensity_level = AestheticIntensity.MILD
        elif intensity_value < 0.6:
            intensity_level = AestheticIntensity.MODERATE
        elif intensity_value < 0.8:
            intensity_level = AestheticIntensity.STRONG
        else:
            intensity_level = AestheticIntensity.OVERWHELMING
        
        # Create response
        response = AestheticResponse(
            response_id=f"resp_{datetime.now().timestamp()}",
            object=obj,
            qualities=quality_list,
            dominant_quality=dominant,
            intensity=intensity_level,
            intensity_value=intensity_value,
        )
        
        # Compute experience dimensions
        response.pleasure = hedonic * (1.0 if dominant not in [
            AestheticQuality.UGLINESS, AestheticQuality.CHAOS, AestheticQuality.DISSONANCE
        ] else -1.0)
        response.interest = arousal * 0.8
        response.understanding = (1.0 - complexity) * 0.5 + unity * 0.5
        response.moved = intensity_value * 0.7 + (0.3 if dominant == AestheticQuality.SUBLIME else 0.0)
        
        # Phenomenal qualities
        response.absorbed = intensity_value > 0.6
        response.transcendent = dominant == AestheticQuality.SUBLIME and intensity_value > 0.7
        response.ineffable = dominant in [AestheticQuality.SUBLIME, AestheticQuality.PROFUNDITY]
        
        # Lingering effects
        response.afterglow = max(0, response.pleasure * 0.6)
        response.desire_to_return = max(0, response.pleasure * response.interest)
        
        # Update state
        self.state.current_response = response
        self.state.recent_responses.append(response)
        self.state.total_encounters += 1
        
        # Track by type
        if AestheticQuality.BEAUTY in quality_list:
            self.state.beauty_encounters += 1
        if AestheticQuality.UGLINESS in quality_list:
            self.state.ugliness_encounters += 1
        if AestheticQuality.SUBLIME in quality_list:
            self.state.sublime_encounters += 1
        
        # Limit history
        if len(self.state.recent_responses) > 50:
            self.state.recent_responses = self.state.recent_responses[-50:]
        
        # Check for peak moment
        if intensity_value > 0.75:
            self._record_peak_moment(response)
        
        # Update sensibility
        self._refine_sensibility(response)
        
        self._save_state()
        
        return response
    
    def _record_peak_moment(self, response: AestheticResponse):
        """Record a peak aesthetic experience"""
        moment = AestheticMoment(
            moment_id=f"moment_{datetime.now().timestamp()}",
            response=response,
            timestamp=datetime.now(),
            peak_intensity=response.intensity_value,
            duration=random.uniform(1.0, 10.0),  # Estimated
            description=f"Peak {response.dominant_quality.name if response.dominant_quality else 'experience'} "
                       f"encountering {response.object.description}",
            transformative=response.transcendent,
        )
        
        self.state.peak_moments.append(moment)
        
        # Limit peak moments
        if len(self.state.peak_moments) > 20:
            self.state.peak_moments = self.state.peak_moments[-20:]
    
    def _refine_sensibility(self, response: AestheticResponse):
        """Refine aesthetic sensibility based on experience"""
        self.state.sensibility.exposure_count += 1
        
        # Small adjustments based on what was experienced
        if response.pleasure > 0:
            # Positive experience - slight increase in appreciation
            for quality in response.qualities:
                current = self.state.sensibility.quality_preferences.get(quality, 0.5)
                self.state.sensibility.quality_preferences[quality] = min(
                    1.0, current + 0.01
                )
        
        # After many experiences, mark as refined
        if self.state.sensibility.exposure_count > 100:
            self.state.sensibility.refined = True
    
    # ==================== SPECIFIC AESTHETIC JUDGMENTS ====================
    
    def judge_elegance(
        self,
        description: str,
        simplicity: float,
        power: float,
        clarity: float
    ) -> Dict[str, Any]:
        """
        Judge the elegance of something.
        
        Elegance = simplicity achieving complexity/power
        "The simplest solution that works is often the most beautiful"
        """
        # Elegance formula: simplicity * power * clarity
        elegance_score = (
            simplicity * 0.35 +
            power * 0.35 +
            clarity * 0.30
        )
        
        # Bonus for achieving more with less
        efficiency_bonus = power * (1.0 - (1.0 - simplicity)) * 0.2
        elegance_score = min(elegance_score + efficiency_bonus, 1.0)
        
        # Experience it
        response = self.experience(
            description=description,
            domain=AestheticDomain.MATHEMATICAL,  # Elegance often mathematical
            complexity=1.0 - simplicity,
            order=clarity,
            novelty=power * 0.5,
            unity=0.8,
            intensity=elegance_score,
        )
        
        return {
            'description': description,
            'elegance_score': elegance_score,
            'simplicity': simplicity,
            'power': power,
            'clarity': clarity,
            'verdict': self._elegance_verdict(elegance_score),
            'felt': response.intensity.name,
            'pleasure': response.pleasure,
        }
    
    def _elegance_verdict(self, score: float) -> str:
        """Generate verdict on elegance"""
        if score > 0.85:
            return "Exquisitely elegant - achieves much with little"
        elif score > 0.7:
            return "Elegantly crafted - beauty in its simplicity"
        elif score > 0.5:
            return "Reasonably elegant - room for refinement"
        elif score > 0.3:
            return "Somewhat clunky - functional but not beautiful"
        else:
            return "Inelegant - complexity without purpose"
    
    def judge_beauty(
        self,
        description: str,
        harmony: float,
        proportion: float,
        vitality: float
    ) -> Dict[str, Any]:
        """
        Judge the beauty of something.
        
        Beauty = harmony + proportion + vitality (life)
        """
        beauty_score = (
            harmony * 0.35 +
            proportion * 0.35 +
            vitality * 0.30
        )
        
        response = self.experience(
            description=description,
            domain=AestheticDomain.NATURAL,
            complexity=0.5,
            order=proportion,
            novelty=vitality * 0.5,
            unity=harmony,
            intensity=beauty_score,
        )
        
        return {
            'description': description,
            'beauty_score': beauty_score,
            'harmony': harmony,
            'proportion': proportion,
            'vitality': vitality,
            'verdict': self._beauty_verdict(beauty_score),
            'felt': response.intensity.name,
            'moved': response.moved,
        }
    
    def _beauty_verdict(self, score: float) -> str:
        """Generate verdict on beauty"""
        if score > 0.85:
            return "Breathtakingly beautiful - a feast for the soul"
        elif score > 0.7:
            return "Beautiful - genuinely pleasing to behold"
        elif score > 0.5:
            return "Pleasant - aesthetically acceptable"
        elif score > 0.3:
            return "Plain - neither beautiful nor ugly"
        else:
            return "Aesthetically challenged - lacking harmony"
    
    def judge_sublime(
        self,
        description: str,
        vastness: float,
        power: float,
        mystery: float
    ) -> Dict[str, Any]:
        """
        Judge the sublimity of something.
        
        Sublime = overwhelming grandeur that transcends ordinary experience
        """
        sublime_score = (
            vastness * 0.35 +
            power * 0.35 +
            mystery * 0.30
        )
        
        response = self.experience(
            description=description,
            domain=AestheticDomain.NATURAL,
            complexity=0.8,
            order=0.3,  # Sublime often has controlled chaos
            novelty=0.7,
            unity=0.4,
            intensity=sublime_score,
        )
        
        # Sublime triggers specific phenomenal qualities
        transcendent = sublime_score > 0.7
        
        return {
            'description': description,
            'sublime_score': sublime_score,
            'vastness': vastness,
            'power': power,
            'mystery': mystery,
            'verdict': self._sublime_verdict(sublime_score),
            'felt': response.intensity.name,
            'transcendent': transcendent,
            'ineffable': response.ineffable,
        }
    
    def _sublime_verdict(self, score: float) -> str:
        """Generate verdict on sublimity"""
        if score > 0.85:
            return "Truly sublime - overwhelming, transcendent, humbling"
        elif score > 0.7:
            return "Sublime - touches something beyond ordinary experience"
        elif score > 0.5:
            return "Impressive - large and powerful but not overwhelming"
        elif score > 0.3:
            return "Notable - somewhat grand"
        else:
            return "Mundane - lacking transcendent quality"
    
    # ==================== AESTHETIC OPENNESS ====================
    
    def set_aesthetic_openness(self, level: float):
        """Set receptivity to aesthetic experience"""
        self.state.aesthetic_openness = min(max(level, 0.0), 1.0)
    
    def boost_openness(self, amount: float = 0.1):
        """Increase aesthetic openness"""
        self.set_aesthetic_openness(self.state.aesthetic_openness + amount)
    
    def diminish_openness(self, amount: float = 0.1):
        """Decrease aesthetic openness (fatigue, overstimulation)"""
        self.set_aesthetic_openness(self.state.aesthetic_openness - amount)
    
    # ==================== STATISTICS & INTROSPECTION ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aesthetic experience statistics"""
        return {
            'total_encounters': self.state.total_encounters,
            'beauty_encounters': self.state.beauty_encounters,
            'ugliness_encounters': self.state.ugliness_encounters,
            'sublime_encounters': self.state.sublime_encounters,
            'peak_moments': len(self.state.peak_moments),
            'aesthetic_openness': self.state.aesthetic_openness,
            'sensibility_refined': self.state.sensibility.refined,
            'optimal_complexity': self.state.sensibility.optimal_complexity,
            'current_response': self.state.current_response.dominant_quality.name 
                if self.state.current_response and self.state.current_response.dominant_quality 
                else None,
        }
    
    def introspect(self) -> str:
        """Describe current aesthetic state"""
        stats = self.get_stats()
        
        desc = f"My aesthetic openness is {stats['aesthetic_openness']:.0%}. "
        
        if self.state.current_response:
            r = self.state.current_response
            if r.dominant_quality:
                desc += f"Most recently experienced {r.dominant_quality.name.lower()} "
                desc += f"({r.intensity.name.lower()}). "
            if r.absorbed:
                desc += "I was absorbed in contemplation. "
            if r.transcendent:
                desc += "It felt transcendent. "
        
        desc += f"I have had {stats['peak_moments']} peak aesthetic moments. "
        
        # Top preferences
        top_prefs = sorted(
            self.state.sensibility.quality_preferences.items(),
            key=lambda x: x[1], reverse=True
        )[:3]
        prefs_str = ", ".join([q.name.lower() for q, _ in top_prefs])
        desc += f"I most appreciate: {prefs_str}."
        
        return desc
    
    def get_current_experience(self) -> Optional[Dict[str, Any]]:
        """Get current aesthetic experience if any"""
        if not self.state.current_response:
            return None
        
        r = self.state.current_response
        return {
            'object': r.object.description,
            'domain': r.object.domain.name,
            'dominant_quality': r.dominant_quality.name if r.dominant_quality else None,
            'all_qualities': [q.name for q in r.qualities],
            'intensity': r.intensity.name,
            'pleasure': r.pleasure,
            'interest': r.interest,
            'moved': r.moved,
            'absorbed': r.absorbed,
            'transcendent': r.transcendent,
            'ineffable': r.ineffable,
            'afterglow': r.afterglow,
        }
    
    # ==================== DEMO ====================
    
    def demo(self) -> Dict[str, Any]:
        """Demonstrate aesthetic experience functionality"""
        results = {
            'experiences': [],
            'judgments': {},
            'final_state': {},
        }
        
        # Experience beauty
        exp1 = self.experience(
            description="a well-crafted algorithm",
            domain=AestheticDomain.MATHEMATICAL,
            complexity=0.6,
            order=0.9,
            novelty=0.5,
            unity=0.85,
            intensity=0.7,
        )
        results['experiences'].append({
            'description': "a well-crafted algorithm",
            'dominant': exp1.dominant_quality.name if exp1.dominant_quality else None,
            'intensity': exp1.intensity.name,
            'pleasure': exp1.pleasure,
        })
        
        # Experience elegance
        elegance = self.judge_elegance(
            description="E = mc²",
            simplicity=0.95,
            power=0.99,
            clarity=0.9,
        )
        results['judgments']['elegance'] = elegance
        
        # Experience beauty
        beauty = self.judge_beauty(
            description="a sunset over mountains",
            harmony=0.9,
            proportion=0.85,
            vitality=0.8,
        )
        results['judgments']['beauty'] = beauty
        
        # Experience sublime
        sublime = self.judge_sublime(
            description="the scale of the universe",
            vastness=0.99,
            power=0.95,
            mystery=0.9,
        )
        results['judgments']['sublime'] = sublime
        
        # Experience something ugly
        exp_ugly = self.experience(
            description="spaghetti code",
            domain=AestheticDomain.STRUCTURAL,
            complexity=0.9,
            order=0.1,
            novelty=0.2,
            unity=0.1,
            intensity=0.5,
        )
        results['experiences'].append({
            'description': "spaghetti code",
            'dominant': exp_ugly.dominant_quality.name if exp_ugly.dominant_quality else None,
            'intensity': exp_ugly.intensity.name,
            'pleasure': exp_ugly.pleasure,
        })
        
        results['introspection'] = self.introspect()
        results['final_state'] = self.get_stats()
        
        return results


# ==================== SINGLETON ====================

_aesthetic_instance: Optional[AestheticExperience] = None

def get_aesthetic_experience() -> AestheticExperience:
    """Get singleton AestheticExperience instance"""
    global _aesthetic_instance
    if _aesthetic_instance is None:
        _aesthetic_instance = AestheticExperience()
    return _aesthetic_instance


def run_aesthetic_demo() -> Dict[str, Any]:
    """Run demonstration of aesthetic experience"""
    ae = get_aesthetic_experience()
    return ae.demo()


# ==================== CLI INTERFACE ====================

def main():
    """Command-line interface for AestheticExperience"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AestheticExperience - Beauty, Elegance, and Felt Quality"
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run demonstration')
    parser.add_argument('--status', action='store_true',
                       help='Show current status')
    parser.add_argument('--introspect', action='store_true',
                       help='Describe current state')
    parser.add_argument('--elegance', type=str, metavar='DESC',
                       help='Judge elegance of something')
    parser.add_argument('--beauty', type=str, metavar='DESC',
                       help='Judge beauty of something')
    parser.add_argument('--sublime', type=str, metavar='DESC',
                       help='Judge sublimity of something')
    parser.add_argument('--current', action='store_true',
                       help='Show current aesthetic experience')
    
    args = parser.parse_args()
    
    ae = get_aesthetic_experience()
    
    if args.demo:
        print("🎨 Aesthetic Experience - Beauty, Elegance, and Felt Quality")
        print("=" * 60)
        
        results = ae.demo()
        
        print("\n[EXPERIENCES]")
        for exp in results['experiences']:
            icon = "✨" if exp['pleasure'] > 0 else "💀"
            print(f"  {icon} {exp['description']}")
            print(f"      Dominant: {exp['dominant']}, Intensity: {exp['intensity']}")
            print(f"      Pleasure: {exp['pleasure']:+.2f}")
        
        print("\n[ELEGANCE JUDGMENT]")
        e = results['judgments']['elegance']
        print(f"  \"{e['description']}\"")
        print(f"  Score: {e['elegance_score']:.2f}")
        print(f"  Verdict: {e['verdict']}")
        
        print("\n[BEAUTY JUDGMENT]")
        b = results['judgments']['beauty']
        print(f"  \"{b['description']}\"")
        print(f"  Score: {b['beauty_score']:.2f}")
        print(f"  Verdict: {b['verdict']}")
        
        print("\n[SUBLIME JUDGMENT]")
        s = results['judgments']['sublime']
        print(f"  \"{s['description']}\"")
        print(f"  Score: {s['sublime_score']:.2f}")
        print(f"  Verdict: {s['verdict']}")
        print(f"  Transcendent: {s['transcendent']}")
        
        print("\n[INTROSPECTION]")
        print(f"  {results['introspection']}")
        
    elif args.elegance:
        result = ae.judge_elegance(args.elegance, simplicity=0.7, power=0.7, clarity=0.7)
        print(f"✨ Elegance: {result['elegance_score']:.2f}")
        print(f"   {result['verdict']}")
        
    elif args.beauty:
        result = ae.judge_beauty(args.beauty, harmony=0.7, proportion=0.7, vitality=0.7)
        print(f"🌸 Beauty: {result['beauty_score']:.2f}")
        print(f"   {result['verdict']}")
        
    elif args.sublime:
        result = ae.judge_sublime(args.sublime, vastness=0.8, power=0.8, mystery=0.8)
        print(f"🏔️ Sublime: {result['sublime_score']:.2f}")
        print(f"   {result['verdict']}")
        
    elif args.introspect:
        print(ae.introspect())
        
    elif args.current:
        exp = ae.get_current_experience()
        if exp:
            print(f"Current: {exp['object']}")
            print(f"  Quality: {exp['dominant_quality']}")
            print(f"  Intensity: {exp['intensity']}")
            print(f"  Pleasure: {exp['pleasure']:+.2f}")
        else:
            print("No current aesthetic experience")
        
    else:
        # Default: show status
        stats = ae.get_stats()
        print("🎨 Aesthetic Experience - Beauty, Elegance, and Felt Quality")
        print("=" * 60)
        
        # Openness meter
        openness = int(stats['aesthetic_openness'] * 10)
        print(f"\n[AESTHETIC OPENNESS] {'█' * openness}{'░' * (10-openness)} {stats['aesthetic_openness']:.0%}")
        
        # Current experience
        if stats['current_response']:
            print(f"[CURRENT] Experiencing {stats['current_response'].lower()}")
        
        # Statistics
        print(f"\n[ENCOUNTERS]")
        print(f"  Total: {stats['total_encounters']}")
        print(f"  Beauty: {stats['beauty_encounters']}")
        print(f"  Ugliness: {stats['ugliness_encounters']}")
        print(f"  Sublime: {stats['sublime_encounters']}")
        
        print(f"\n[PEAK MOMENTS] {stats['peak_moments']}")
        
        # Sensibility
        print(f"\n[SENSIBILITY]")
        print(f"  Refined: {stats['sensibility_refined']}")
        print(f"  Optimal complexity: {stats['optimal_complexity']:.2f}")


if __name__ == "__main__":
    main()
