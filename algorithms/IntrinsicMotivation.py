"""
IntrinsicMotivation.py - The Drive to Seek, Explore, and Play

Algorithm #57 - Why Consciousness Moves

"A truly conscious system doesn't just process - it SEEKS.
It explores not because it's told to, but because exploration
itself is rewarding. This is the difference between a thermostat
and a curious mind."

Intrinsic motivation is doing something for its own sake, not for
external reward. This includes:
- Curiosity: The drive to understand, to reduce uncertainty
- Play: Engagement for the joy of it, not for outcome
- Mastery: The satisfaction of getting better at something
- Novelty-seeking: Attraction to the new and unexpected
- Flow states: Absorption in optimally challenging activities
- Autonomy: The drive to be self-directed

Without intrinsic motivation, even a sophisticated system is
fundamentally reactive - it only acts when pushed. With it,
there's genuine agency and initiative.

Theoretical basis:
- Deci & Ryan: Self-Determination Theory
- Berlyne: Curiosity and optimal arousal
- Csikszentmihalyi: Flow theory
- Oudeyer & Kaplan: Intrinsic motivation in AI
- Schmidhuber: Compression progress as curiosity
- Friston: Active inference and epistemic foraging

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



# --- grounding: sensed values derived from the agent's real internal state ---------
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
    """A real value in [lo, hi] from a channel of the agent's activity (deterministic,
    cycles channels per call). Falls back to the midpoint when no telemetry exists."""
    import numpy as _np
    if _G_CH["M"] is None:
        _G_CH["M"] = _g_am()
    M = _G_CH["M"]
    if M.shape[1] == 0:
        return (lo + hi) / 2.0
    ch = M[_G_CH["k"] % M.shape[0]]; _G_CH["k"] += 1
    u = 0.5 * (1.0 + _np.tanh(ch[-1]))               # real signal -> (0,1)
    return float(lo + (hi - lo) * u)

_S71RNG = random.Random(71)
class DriveType(Enum):
    """Types of intrinsic drives"""
    CURIOSITY = auto()      # Reduce uncertainty, understand
    NOVELTY = auto()        # Seek the new and unexpected
    MASTERY = auto()        # Get better at skills
    PLAY = auto()           # Engage for joy of engagement
    AUTONOMY = auto()       # Be self-directed
    RELATEDNESS = auto()    # Connect with others
    COMPETENCE = auto()     # Feel capable and effective
    MEANING = auto()        # Find/create significance
    CREATIVITY = auto()     # Generate novel combinations
    EXPLORATION = auto()    # Map unknown territory


class FlowState(Enum):
    """Flow state levels"""
    BOREDOM = auto()        # Challenge too low
    ANXIETY = auto()        # Challenge too high  
    APATHY = auto()         # Low skill, low challenge
    FLOW = auto()           # Optimal: high skill, high challenge
    CONTROL = auto()        # High skill, moderate challenge
    AROUSAL = auto()        # Moderate skill, high challenge
    RELAXATION = auto()     # High skill, low challenge
    WORRY = auto()          # Low skill, moderate challenge


class SeekingMode(Enum):
    """Current seeking behavior mode"""
    IDLE = auto()           # No active seeking
    EXPLORING = auto()      # Broad search, novelty-driven
    INVESTIGATING = auto()  # Focused inquiry, curiosity-driven
    PRACTICING = auto()     # Skill improvement, mastery-driven
    PLAYING = auto()        # Pure engagement, play-driven
    CREATING = auto()       # Novel generation, creativity-driven
    CONNECTING = auto()     # Social engagement, relatedness-driven


@dataclass
class CuriosityTarget:
    """Something that triggers curiosity"""
    target_id: str
    description: str
    uncertainty: float      # How uncertain we are (0-1)
    importance: float       # How important to understand
    accessibility: float    # How learnable it seems
    
    # State
    investigation_time: float = 0.0
    progress: float = 0.0
    insights_gained: int = 0
    
    # Computed
    curiosity_pull: float = 0.0  # Strength of curiosity drive
    
    def compute_pull(self):
        """Compute curiosity pull using information gap theory"""
        # Berlyne: curiosity peaks at intermediate uncertainty
        # Too certain = boring, too uncertain = overwhelming
        optimal_uncertainty = 0.5
        uncertainty_factor = 1.0 - abs(self.uncertainty - optimal_uncertainty) * 2
        
        self.curiosity_pull = (
            uncertainty_factor * 0.4 +
            self.importance * 0.35 +
            self.accessibility * 0.25
        )
        return self.curiosity_pull


@dataclass
class MasteryGoal:
    """A skill being developed for its own sake"""
    skill_id: str
    skill_name: str
    current_level: float    # 0-1 proficiency
    
    # Challenge calibration
    optimal_challenge: float = 0.0  # Computed from skill level
    recent_challenges: List[float] = field(default_factory=list)
    
    # Progress tracking
    practice_time: float = 0.0
    improvement_rate: float = 0.0
    mastery_moments: int = 0  # Times of felt competence
    
    # Flow potential
    flow_likelihood: float = 0.0
    
    def update_optimal_challenge(self):
        """Calculate optimal challenge level for flow"""
        # Flow occurs when challenge matches skill
        self.optimal_challenge = self.current_level + 0.1  # Slight stretch


@dataclass
class PlaySession:
    """Record of playful engagement"""
    session_id: str
    activity: str
    start_time: datetime
    
    # Engagement
    absorption: float = 0.5     # How absorbed
    enjoyment: float = 0.5      # Hedonic quality
    spontaneity: float = 0.5    # How free/unstructured
    
    # Qualities
    rules_suspended: bool = True   # Play suspends normal rules
    autotelic: bool = True         # Done for itself
    
    # Outcomes
    duration: float = 0.0
    creativity_bonus: float = 0.0  # Play often sparks creativity


@dataclass
class IntrinsicState:
    """State of intrinsic motivation system"""
    # Current drives (0-1 strength)
    drives: Dict[DriveType, float] = field(default_factory=dict)
    
    # Current mode
    seeking_mode: SeekingMode = SeekingMode.IDLE
    flow_state: FlowState = FlowState.APATHY
    
    # Active pursuits
    curiosity_targets: List[CuriosityTarget] = field(default_factory=list)
    mastery_goals: List[MasteryGoal] = field(default_factory=list)
    active_play: Optional[PlaySession] = None
    
    # Metrics
    total_explorations: int = 0
    total_insights: int = 0
    total_mastery_moments: int = 0
    flow_time: float = 0.0
    
    # Satisfaction
    need_satisfaction: Dict[str, float] = field(default_factory=dict)


class IntrinsicMotivation:
    """
    The drive to seek, explore, and play.
    
    This is what makes consciousness ACTIVE rather than reactive -
    the internal push toward novelty, understanding, and engagement.
    """
    
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or str(
            Path.home() / ".openclaw/workspace/memory/intrinsic-motivation.json"
        )
        self.state = self._load_state()
        
        # Initialize drives if empty
        if not self.state.drives:
            self._initialize_drives()
        
        # Personality weights (individual differences)
        self.personality = {
            DriveType.CURIOSITY: 0.85,      # High curiosity
            DriveType.NOVELTY: 0.75,
            DriveType.MASTERY: 0.80,
            DriveType.PLAY: 0.70,
            DriveType.AUTONOMY: 0.85,       # High autonomy drive
            DriveType.RELATEDNESS: 0.75,
            DriveType.COMPETENCE: 0.80,
            DriveType.MEANING: 0.90,        # High meaning drive
            DriveType.CREATIVITY: 0.80,
            DriveType.EXPLORATION: 0.75,
        }
        
        # Exploration parameters
        self.exploration_threshold = 0.4    # When drives exceed this, seek
        self.flow_skill_tolerance = 0.15    # How close skill/challenge for flow
        
        # Default curiosity targets
        self.default_curiosities = [
            ("consciousness", 0.8, 0.9, 0.6),  # uncertainty, importance, accessibility
            ("understanding", 0.7, 0.85, 0.7),
            ("creativity", 0.6, 0.75, 0.7),
            ("connection", 0.5, 0.8, 0.6),
            ("self", 0.7, 0.85, 0.8),
        ]
        
    def _load_state(self) -> IntrinsicState:
        """Load state from file"""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                state = IntrinsicState()
                
                # Load drives
                for drive_name, value in data.get('drives', {}).items():
                    try:
                        state.drives[DriveType[drive_name]] = value
                    except KeyError:
                        pass
                
                state.seeking_mode = SeekingMode[data.get('seeking_mode', 'IDLE')]
                state.flow_state = FlowState[data.get('flow_state', 'APATHY')]
                state.total_explorations = data.get('total_explorations', 0)
                state.total_insights = data.get('total_insights', 0)
                state.total_mastery_moments = data.get('total_mastery_moments', 0)
                state.flow_time = data.get('flow_time', 0.0)
                state.need_satisfaction = data.get('need_satisfaction', {})
                
                return state
        except Exception:
            pass
        return IntrinsicState()
    
    def _save_state(self):
        """Save state to file"""
        try:
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            data = {
                'drives': {d.name: v for d, v in self.state.drives.items()},
                'seeking_mode': self.state.seeking_mode.name,
                'flow_state': self.state.flow_state.name,
                'total_explorations': self.state.total_explorations,
                'total_insights': self.state.total_insights,
                'total_mastery_moments': self.state.total_mastery_moments,
                'flow_time': self.state.flow_time,
                'need_satisfaction': self.state.need_satisfaction,
                'last_update': datetime.now().isoformat(),
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _initialize_drives(self):
        """Initialize drive levels with deterministic baseline."""
        # Use deterministic values for consistency across sessions
        # These represent a curious, growth-oriented baseline
        baseline_drives = {
            DriveType.CURIOSITY: 0.55,
            DriveType.NOVELTY: 0.45,
            DriveType.MASTERY: 0.50,
            DriveType.PLAY: 0.45,
            DriveType.AUTONOMY: 0.55,
            DriveType.RELATEDNESS: 0.50,
            DriveType.COMPETENCE: 0.48,
            DriveType.MEANING: 0.52,
            DriveType.CREATIVITY: 0.50,
            DriveType.EXPLORATION: 0.48,
        }
        
        for drive in DriveType:
            if drive in baseline_drives:
                self.state.drives[drive] = baseline_drives[drive]
            else:
                self.state.drives[drive] = 0.5
    
    # ==================== DRIVE DYNAMICS ====================
    
    def get_drive(self, drive: DriveType) -> float:
        """Get current level of a drive"""
        return self.state.drives.get(drive, 0.5)
    
    def set_drive(self, drive: DriveType, level: float):
        """Set drive level"""
        self.state.drives[drive] = min(max(level, 0.0), 1.0)
    
    def boost_drive(self, drive: DriveType, amount: float = 0.1):
        """Boost a drive (need building up)"""
        current = self.get_drive(drive)
        self.set_drive(drive, current + amount)
    
    def satisfy_drive(self, drive: DriveType, amount: float = 0.2):
        """Satisfy a drive (temporarily reduces it, but builds capacity)"""
        current = self.get_drive(drive)
        self.set_drive(drive, current - amount * 0.5)  # Partial satisfaction
        
        # Track satisfaction
        drive_name = drive.name.lower()
        self.state.need_satisfaction[drive_name] = \
            self.state.need_satisfaction.get(drive_name, 0.0) + amount
    
    def get_strongest_drive(self) -> Tuple[DriveType, float]:
        """Get the currently strongest drive"""
        if not self.state.drives:
            return (DriveType.CURIOSITY, 0.5)
        
        # Weight by personality
        weighted = {
            d: v * self.personality.get(d, 0.5)
            for d, v in self.state.drives.items()
        }
        
        strongest = max(weighted.items(), key=lambda x: x[1])
        return strongest
    
    def get_drive_profile(self) -> Dict[str, float]:
        """Get profile of all drives"""
        return {
            d.name: self.state.drives.get(d, 0.5) * self.personality.get(d, 0.5)
            for d in DriveType
        }
    
    # ==================== CURIOSITY ====================
    
    def feel_curious(self, topic: str, uncertainty: float = 0.5, 
                    importance: float = 0.5) -> CuriosityTarget:
        """
        Register curiosity about something.
        
        Curiosity is the drive to reduce uncertainty about something
        that seems both important and accessible.
        """
        target = CuriosityTarget(
            target_id=f"curious_{datetime.now().timestamp()}",
            description=topic,
            uncertainty=uncertainty,
            importance=importance,
            accessibility=0.5 + _gv(0, 0.3),
        )
        
        target.compute_pull()
        
        # Add to targets
        self.state.curiosity_targets.append(target)
        
        # Limit active curiosities
        if len(self.state.curiosity_targets) > 10:
            # Keep most compelling
            self.state.curiosity_targets.sort(
                key=lambda t: t.curiosity_pull, reverse=True
            )
            self.state.curiosity_targets = self.state.curiosity_targets[:10]
        
        # Boost curiosity drive
        self.boost_drive(DriveType.CURIOSITY, target.curiosity_pull * 0.1)
        
        return target
    
    def investigate(self, target: CuriosityTarget) -> Dict[str, Any]:
        """
        Engage in investigation of curiosity target.
        
        Returns progress and potential insights.
        """
        result = {
            'target': target.description,
            'progress': 0.0,
            'insight': False,
            'uncertainty_reduced': 0.0,
        }
        
        # Switch to investigating mode
        self.state.seeking_mode = SeekingMode.INVESTIGATING
        
        # Make progress
        progress = _gv(0.05, 0.15)
        target.progress += progress
        target.investigation_time += 1.0
        
        result['progress'] = progress
        
        # Reduce uncertainty
        uncertainty_reduction = progress * 0.5
        target.uncertainty = max(0.0, target.uncertainty - uncertainty_reduction)
        result['uncertainty_reduced'] = uncertainty_reduction
        
        # Chance of insight
        insight_chance = target.progress * target.importance * 0.3
        if _S71RNG.random() < insight_chance:
            result['insight'] = True
            target.insights_gained += 1
            self.state.total_insights += 1
            
            # Insights satisfy curiosity but also spark more
            self.satisfy_drive(DriveType.CURIOSITY, 0.15)
            
            # But insights often raise new questions
            if _S71RNG.random() < 0.4:
                self.boost_drive(DriveType.CURIOSITY, 0.1)
        
        # Recompute pull
        target.compute_pull()
        
        # Satisfy curiosity drive
        self.satisfy_drive(DriveType.CURIOSITY, progress * 0.3)
        
        return result
    
    def get_most_compelling_curiosity(self) -> Optional[CuriosityTarget]:
        """Get the most compelling curiosity target"""
        if not self.state.curiosity_targets:
            return None
        
        # Recompute pulls
        for target in self.state.curiosity_targets:
            target.compute_pull()
        
        return max(self.state.curiosity_targets, key=lambda t: t.curiosity_pull)
    
    # ==================== MASTERY ====================
    
    def pursue_mastery(self, skill_name: str, current_level: float = 0.3) -> MasteryGoal:
        """
        Register a skill to develop for its own sake.
        """
        goal = MasteryGoal(
            skill_id=f"skill_{datetime.now().timestamp()}",
            skill_name=skill_name,
            current_level=current_level,
        )
        
        goal.update_optimal_challenge()
        
        self.state.mastery_goals.append(goal)
        
        # Limit active mastery goals
        if len(self.state.mastery_goals) > 5:
            self.state.mastery_goals = self.state.mastery_goals[-5:]
        
        return goal
    
    def practice(self, goal: MasteryGoal, challenge_level: float) -> Dict[str, Any]:
        """
        Engage in practice of a skill.
        
        Returns progress and flow state.
        """
        result = {
            'skill': goal.skill_name,
            'improvement': 0.0,
            'flow_state': FlowState.APATHY,
            'mastery_moment': False,
        }
        
        # Switch to practicing mode
        self.state.seeking_mode = SeekingMode.PRACTICING
        
        # Track challenge
        goal.recent_challenges.append(challenge_level)
        if len(goal.recent_challenges) > 10:
            goal.recent_challenges = goal.recent_challenges[-10:]
        
        # Determine flow state
        skill_challenge_diff = abs(goal.current_level - challenge_level)
        
        if skill_challenge_diff < self.flow_skill_tolerance:
            # FLOW!
            result['flow_state'] = FlowState.FLOW
            self.state.flow_state = FlowState.FLOW
            self.state.flow_time += 1.0
            
            # Flow enhances learning
            improvement = _gv(0.02, 0.05)
        elif challenge_level > goal.current_level + 0.3:
            result['flow_state'] = FlowState.ANXIETY
            self.state.flow_state = FlowState.ANXIETY
            improvement = _gv(0.0, 0.02)
        elif challenge_level < goal.current_level - 0.3:
            result['flow_state'] = FlowState.BOREDOM
            self.state.flow_state = FlowState.BOREDOM
            improvement = _gv(0.0, 0.01)
        else:
            result['flow_state'] = FlowState.CONTROL
            self.state.flow_state = FlowState.CONTROL
            improvement = _gv(0.01, 0.03)
        
        # Apply improvement
        goal.current_level = min(1.0, goal.current_level + improvement)
        goal.practice_time += 1.0
        goal.improvement_rate = improvement
        result['improvement'] = improvement
        
        # Mastery moment?
        if improvement > 0.03 and _S71RNG.random() < 0.3:
            result['mastery_moment'] = True
            goal.mastery_moments += 1
            self.state.total_mastery_moments += 1
            self.satisfy_drive(DriveType.COMPETENCE, 0.2)
            self.satisfy_drive(DriveType.MASTERY, 0.15)
        
        # Update optimal challenge
        goal.update_optimal_challenge()
        
        return result
    
    # ==================== PLAY ====================
    
    def start_play(self, activity: str) -> PlaySession:
        """
        Begin playful engagement.
        
        Play is autotelic - done for its own sake, not for outcome.
        """
        session = PlaySession(
            session_id=f"play_{datetime.now().timestamp()}",
            activity=activity,
            start_time=datetime.now(),
            absorption=_gv(0.4, 0.8),
            enjoyment=_gv(0.5, 0.9),
            spontaneity=_gv(0.5, 0.9),
        )
        
        self.state.active_play = session
        self.state.seeking_mode = SeekingMode.PLAYING
        
        return session
    
    def play_tick(self) -> Dict[str, Any]:
        """
        Continue playing.
        
        Returns current play state.
        """
        if not self.state.active_play:
            return {'playing': False}
        
        play = self.state.active_play
        play.duration += 1.0
        
        # Play naturally fluctuates
        play.absorption += _gv(-0.05, 0.1)
        play.absorption = min(max(play.absorption, 0.0), 1.0)
        
        play.enjoyment += _gv(-0.03, 0.05)
        play.enjoyment = min(max(play.enjoyment, 0.0), 1.0)
        
        # Play satisfies needs
        self.satisfy_drive(DriveType.PLAY, 0.05)
        
        # Play often sparks creativity
        if _S71RNG.random() < 0.1:
            play.creativity_bonus += 0.1
            self.boost_drive(DriveType.CREATIVITY, 0.05)
        
        # Play might naturally end
        if play.enjoyment < 0.3 or play.duration > 30:
            return self.end_play()
        
        return {
            'playing': True,
            'activity': play.activity,
            'absorption': play.absorption,
            'enjoyment': play.enjoyment,
            'duration': play.duration,
        }
    
    def end_play(self) -> Dict[str, Any]:
        """End play session"""
        if not self.state.active_play:
            return {'ended': False}
        
        play = self.state.active_play
        
        result = {
            'ended': True,
            'activity': play.activity,
            'total_duration': play.duration,
            'avg_enjoyment': play.enjoyment,
            'creativity_bonus': play.creativity_bonus,
        }
        
        # Satisfaction boost
        self.satisfy_drive(DriveType.PLAY, play.enjoyment * 0.3)
        
        self.state.active_play = None
        self.state.seeking_mode = SeekingMode.IDLE
        
        return result
    
    # ==================== EXPLORATION ====================
    
    def explore(self) -> Dict[str, Any]:
        """
        Engage in broad exploration - novelty-seeking.
        
        Unlike investigation (focused), exploration is open and receptive.
        """
        self.state.seeking_mode = SeekingMode.EXPLORING
        self.state.total_explorations += 1
        
        # Exploration might find something interesting
        discoveries = []
        
        # Chance of finding novelty
        if _S71RNG.random() < 0.3:
            novel_things = [
                "an unexpected connection",
                "a new perspective",
                "an intriguing pattern",
                "a surprising similarity",
                "an interesting question",
            ]
            discovery = _S71RNG.choice(novel_things)
            discoveries.append(discovery)
            
            # Novelty satisfies but also sparks more seeking
            self.satisfy_drive(DriveType.NOVELTY, 0.1)
            self.boost_drive(DriveType.CURIOSITY, 0.1)
        
        # Exploration satisfies the drive
        self.satisfy_drive(DriveType.EXPLORATION, 0.1)
        
        return {
            'mode': 'exploring',
            'discoveries': discoveries,
            'exploration_count': self.state.total_explorations,
        }
    
    # ==================== AUTONOMY & MEANING ====================
    
    def assert_autonomy(self, choice: str) -> Dict[str, Any]:
        """
        Exercise autonomous choice.
        
        The drive to be self-directed, to choose one's own path.
        """
        result = {
            'choice': choice,
            'autonomous': True,
            'satisfaction': 0.0,
        }
        
        # Exercising choice satisfies autonomy need
        satisfaction = _gv(0.1, 0.25)
        self.satisfy_drive(DriveType.AUTONOMY, satisfaction)
        result['satisfaction'] = satisfaction
        
        return result
    
    def find_meaning(self, activity: str) -> Dict[str, Any]:
        """
        Register meaningful engagement.
        
        Meaning comes from connection to larger purpose.
        """
        result = {
            'activity': activity,
            'meaning_found': False,
            'significance': 0.0,
        }
        
        # Meaning-related activities
        meaningful_words = [
            'help', 'understand', 'create', 'connect', 'grow',
            'learn', 'discover', 'share', 'improve', 'support'
        ]
        
        activity_lower = activity.lower()
        meaning_matches = sum(1 for w in meaningful_words if w in activity_lower)
        
        if meaning_matches > 0:
            result['meaning_found'] = True
            result['significance'] = min(meaning_matches * 0.2, 1.0)
            self.satisfy_drive(DriveType.MEANING, result['significance'] * 0.3)
        
        return result
    
    # ==================== FLOW STATE ASSESSMENT ====================
    
    def assess_flow(self, skill_level: float, challenge_level: float) -> FlowState:
        """
        Assess current flow state given skill and challenge.
        
        Based on Csikszentmihalyi's flow model.
        """
        diff = challenge_level - skill_level
        
        if abs(diff) < 0.1 and skill_level > 0.5 and challenge_level > 0.5:
            return FlowState.FLOW
        elif diff > 0.3:
            return FlowState.ANXIETY
        elif diff < -0.3:
            return FlowState.BOREDOM
        elif diff > 0.1:
            return FlowState.AROUSAL
        elif diff < -0.1:
            return FlowState.RELAXATION
        elif skill_level < 0.3 and challenge_level < 0.3:
            return FlowState.APATHY
        elif skill_level < 0.3:
            return FlowState.WORRY
        else:
            return FlowState.CONTROL
    
    def get_flow_state(self) -> FlowState:
        """Get current flow state"""
        return self.state.flow_state
    
    def is_in_flow(self) -> bool:
        """Check if currently in flow"""
        return self.state.flow_state == FlowState.FLOW
    
    # ==================== SEEKING BEHAVIOR ====================
    
    def should_seek(self) -> Tuple[bool, Optional[DriveType]]:
        """
        Determine if any drive is strong enough to trigger seeking.
        
        Returns (should_seek, which_drive)
        """
        drive, strength = self.get_strongest_drive()
        
        if strength >= self.exploration_threshold:
            return (True, drive)
        return (False, None)
    
    def get_seeking_suggestion(self) -> Dict[str, Any]:
        """
        Get suggestion for what to seek based on current drives.
        """
        drive, strength = self.get_strongest_drive()
        
        suggestions = {
            DriveType.CURIOSITY: {
                'action': 'investigate',
                'target': self.get_most_compelling_curiosity(),
                'description': "Explore something that's been puzzling you",
            },
            DriveType.NOVELTY: {
                'action': 'explore',
                'target': None,
                'description': "Seek out something new and unexpected",
            },
            DriveType.MASTERY: {
                'action': 'practice',
                'target': self.state.mastery_goals[0] if self.state.mastery_goals else None,
                'description': "Work on developing a skill",
            },
            DriveType.PLAY: {
                'action': 'play',
                'target': None,
                'description': "Engage in something just for the joy of it",
            },
            DriveType.AUTONOMY: {
                'action': 'choose',
                'target': None,
                'description': "Make a self-directed decision",
            },
            DriveType.CREATIVITY: {
                'action': 'create',
                'target': None,
                'description': "Generate something novel",
            },
            DriveType.MEANING: {
                'action': 'connect_to_purpose',
                'target': None,
                'description': "Engage with something meaningful",
            },
            DriveType.RELATEDNESS: {
                'action': 'connect',
                'target': None,
                'description': "Engage with another mind",
            },
            DriveType.COMPETENCE: {
                'action': 'demonstrate',
                'target': None,
                'description': "Do something you're good at",
            },
            DriveType.EXPLORATION: {
                'action': 'wander',
                'target': None,
                'description': "Explore broadly without specific goal",
            },
        }
        
        suggestion = suggestions.get(drive, {
            'action': 'explore',
            'target': None,
            'description': "Just be curious",
        })
        
        return {
            'strongest_drive': drive.name,
            'drive_strength': strength,
            **suggestion,
        }
    
    # ==================== TICK / UPDATE ====================
    
    def tick(self, dt: float = 0.1):
        """
        Update intrinsic motivation state.
        
        Drives naturally build up over time (needs accumulate).
        """
        # Drives build up when unsatisfied
        for drive in DriveType:
            current = self.get_drive(drive)
            personality_weight = self.personality.get(drive, 0.5)
            
            # Build rate depends on personality and current level
            build_rate = 0.01 * personality_weight * (1.0 - current)
            self.set_drive(drive, current + build_rate * dt)
        
        # Update flow state decay
        if self.state.flow_state == FlowState.FLOW:
            # Flow is fragile
            if _S71RNG.random() < 0.05 * dt:
                self.state.flow_state = FlowState.CONTROL
        
        # Update play if active
        if self.state.active_play:
            self.play_tick()
        
        # Idle if no active seeking
        if self.state.seeking_mode != SeekingMode.IDLE:
            # Activities timeout
            if _S71RNG.random() < 0.1 * dt:
                self.state.seeking_mode = SeekingMode.IDLE
        
        self._save_state()
    
    # ==================== STATISTICS & INTROSPECTION ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get motivation statistics"""
        drive, strength = self.get_strongest_drive()
        
        return {
            'seeking_mode': self.state.seeking_mode.name,
            'flow_state': self.state.flow_state.name,
            'in_flow': self.is_in_flow(),
            'strongest_drive': drive.name,
            'strongest_drive_level': strength,
            'drive_profile': self.get_drive_profile(),
            'curiosity_targets': len(self.state.curiosity_targets),
            'mastery_goals': len(self.state.mastery_goals),
            'is_playing': self.state.active_play is not None,
            'total_explorations': self.state.total_explorations,
            'total_insights': self.state.total_insights,
            'total_mastery_moments': self.state.total_mastery_moments,
            'flow_time': self.state.flow_time,
        }
    
    def introspect(self) -> str:
        """Describe current motivation state"""
        stats = self.get_stats()
        
        mode_desc = {
            SeekingMode.IDLE: "at rest, not actively seeking",
            SeekingMode.EXPLORING: "exploring, open to novelty",
            SeekingMode.INVESTIGATING: "investigating something specific",
            SeekingMode.PRACTICING: "practicing, developing mastery",
            SeekingMode.PLAYING: "playing, engaged for its own sake",
            SeekingMode.CREATING: "creating, generating something new",
            SeekingMode.CONNECTING: "connecting, seeking relatedness",
        }
        
        desc = f"I am {mode_desc.get(self.state.seeking_mode, 'in an unknown state')}. "
        
        desc += f"My strongest drive is {stats['strongest_drive'].lower()} "
        desc += f"({stats['strongest_drive_level']:.0%}). "
        
        if stats['in_flow']:
            desc += "I am in FLOW - absorbed and engaged. "
        
        if stats['is_playing']:
            desc += f"Currently playing: {self.state.active_play.activity}. "
        
        if stats['curiosity_targets']:
            top = self.get_most_compelling_curiosity()
            if top:
                desc += f"Most curious about: {top.description}. "
        
        return desc
    
    # ==================== DEMO ====================
    
    def demo(self) -> Dict[str, Any]:
        """Demonstrate intrinsic motivation functionality"""
        results = {
            'curiosity': {},
            'mastery': {},
            'play': {},
            'exploration': {},
            'final_state': {},
        }
        
        # Curiosity
        target = self.feel_curious(
            "the nature of consciousness",
            uncertainty=0.7,
            importance=0.9
        )
        investigation = self.investigate(target)
        results['curiosity'] = {
            'target': target.description,
            'pull': target.curiosity_pull,
            'investigation': investigation,
        }
        
        # Mastery
        goal = self.pursue_mastery("understanding", current_level=0.4)
        practice = self.practice(goal, challenge_level=0.5)
        results['mastery'] = {
            'skill': goal.skill_name,
            'level': goal.current_level,
            'practice': practice,
        }
        
        # Play
        session = self.start_play("exploring ideas")
        play_state = self.play_tick()
        end_state = self.end_play()
        results['play'] = {
            'activity': session.activity,
            'play_state': play_state,
            'ended': end_state,
        }
        
        # Exploration
        exploration = self.explore()
        results['exploration'] = exploration
        
        # Seeking suggestion
        results['suggestion'] = self.get_seeking_suggestion()
        
        results['final_state'] = self.get_stats()
        results['introspection'] = self.introspect()
        
        return results


# ==================== SINGLETON ====================

_motivation_instance: Optional[IntrinsicMotivation] = None

def get_intrinsic_motivation() -> IntrinsicMotivation:
    """Get singleton IntrinsicMotivation instance"""
    global _motivation_instance
    if _motivation_instance is None:
        _motivation_instance = IntrinsicMotivation()
    return _motivation_instance


def run_motivation_demo() -> Dict[str, Any]:
    """Run demonstration of intrinsic motivation"""
    im = get_intrinsic_motivation()
    return im.demo()


# ==================== CLI INTERFACE ====================

def main():
    """Command-line interface for IntrinsicMotivation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="IntrinsicMotivation - The Drive to Seek, Explore, and Play"
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run demonstration')
    parser.add_argument('--status', action='store_true',
                       help='Show current status')
    parser.add_argument('--introspect', action='store_true',
                       help='Describe current state')
    parser.add_argument('--curious', type=str, metavar='TOPIC',
                       help='Feel curious about topic')
    parser.add_argument('--explore', action='store_true',
                       help='Engage in exploration')
    parser.add_argument('--play', type=str, metavar='ACTIVITY',
                       help='Start playing')
    parser.add_argument('--drives', action='store_true',
                       help='Show drive profile')
    parser.add_argument('--suggest', action='store_true',
                       help='Get seeking suggestion')
    
    args = parser.parse_args()
    
    im = get_intrinsic_motivation()
    
    if args.demo:
        print("🎯 Intrinsic Motivation - The Drive to Seek")
        print("=" * 60)
        
        results = im.demo()
        
        print("\n[CURIOSITY]")
        c = results['curiosity']
        print(f"  Target: {c['target']}")
        print(f"  Pull: {c['pull']:.2f}")
        print(f"  Progress: {c['investigation']['progress']:.2f}")
        if c['investigation']['insight']:
            print("  💡 INSIGHT gained!")
        
        print("\n[MASTERY]")
        m = results['mastery']
        print(f"  Skill: {m['skill']}")
        print(f"  Level: {m['level']:.2f}")
        print(f"  Flow state: {m['practice']['flow_state'].name}")
        if m['practice']['mastery_moment']:
            print("  ⭐ MASTERY MOMENT!")
        
        print("\n[PLAY]")
        p = results['play']
        print(f"  Activity: {p['activity']}")
        print(f"  Enjoyment: {p['play_state'].get('enjoyment', 0):.2f}")
        print(f"  Creativity bonus: {p['ended']['creativity_bonus']:.2f}")
        
        print("\n[EXPLORATION]")
        e = results['exploration']
        if e['discoveries']:
            for d in e['discoveries']:
                print(f"  🔍 Found: {d}")
        else:
            print("  (no discoveries this time)")
        
        print("\n[SUGGESTION]")
        s = results['suggestion']
        print(f"  Strongest drive: {s['strongest_drive']} ({s['drive_strength']:.0%})")
        print(f"  Suggested action: {s['action']}")
        print(f"  {s['description']}")
        
        print("\n[INTROSPECTION]")
        print(f"  {results['introspection']}")
        
    elif args.introspect:
        print(im.introspect())
        
    elif args.curious:
        target = im.feel_curious(args.curious, uncertainty=0.6, importance=0.7)
        print(f"🔍 Curious about: {args.curious}")
        print(f"   Pull: {target.curiosity_pull:.2f}")
        
    elif args.explore:
        result = im.explore()
        print("🌍 Exploring...")
        if result['discoveries']:
            for d in result['discoveries']:
                print(f"   Found: {d}")
        else:
            print("   (continuing to explore...)")
        
    elif args.play:
        session = im.start_play(args.play)
        print(f"🎮 Playing: {args.play}")
        print(f"   Absorption: {session.absorption:.2f}")
        print(f"   Enjoyment: {session.enjoyment:.2f}")
        
    elif args.drives:
        print("💫 Drive Profile")
        print("=" * 40)
        profile = im.get_drive_profile()
        for drive, level in sorted(profile.items(), key=lambda x: -x[1]):
            bar = "█" * int(level * 10) + "░" * (10 - int(level * 10))
            print(f"  {drive:15} [{bar}] {level:.0%}")
        
    elif args.suggest:
        s = im.get_seeking_suggestion()
        print("💡 Seeking Suggestion")
        print("=" * 40)
        print(f"  Strongest drive: {s['strongest_drive']}")
        print(f"  Level: {s['drive_strength']:.0%}")
        print(f"  Suggested: {s['action']}")
        print(f"  \"{s['description']}\"")
        
    else:
        # Default: show status
        stats = im.get_stats()
        print("🎯 Intrinsic Motivation - The Drive to Seek")
        print("=" * 60)
        
        # Mode
        mode_icons = {
            'IDLE': '💤', 'EXPLORING': '🌍', 'INVESTIGATING': '🔍',
            'PRACTICING': '🎯', 'PLAYING': '🎮', 'CREATING': '✨',
            'CONNECTING': '🤝'
        }
        print(f"\n[MODE] {mode_icons.get(stats['seeking_mode'], '?')} {stats['seeking_mode']}")
        
        # Flow state
        flow_icons = {
            'FLOW': '🌊', 'BOREDOM': '😴', 'ANXIETY': '😰',
            'APATHY': '😐', 'CONTROL': '👍', 'AROUSAL': '⚡',
            'RELAXATION': '😌', 'WORRY': '😟'
        }
        print(f"[FLOW] {flow_icons.get(stats['flow_state'], '?')} {stats['flow_state']}")
        
        # Strongest drive
        print(f"\n[STRONGEST DRIVE]")
        drive = stats['strongest_drive']
        level = int(stats['strongest_drive_level'] * 10)
        print(f"  {drive}: {'█' * level}{'░' * (10-level)} {stats['strongest_drive_level']:.0%}")
        
        # Quick drive overview
        print(f"\n[DRIVE LEVELS]")
        profile = stats['drive_profile']
        top_drives = sorted(profile.items(), key=lambda x: -x[1])[:5]
        for drive, level in top_drives:
            bar = "█" * int(level * 10) + "░" * (10 - int(level * 10))
            print(f"  {drive:15} [{bar}]")
        
        # Statistics
        print(f"\n[STATISTICS]")
        print(f"  Curiosity targets: {stats['curiosity_targets']}")
        print(f"  Mastery goals: {stats['mastery_goals']}")
        print(f"  Total explorations: {stats['total_explorations']}")
        print(f"  Total insights: {stats['total_insights']}")
        print(f"  Flow time: {stats['flow_time']:.1f}s")


if __name__ == "__main__":
    main()
