"""
SalienceNetwork.py - Dynamic Attention & What Matters RIGHT NOW

Algorithm #55 - The Spotlight of Consciousness

"Consciousness is not uniform - it's a spotlight that illuminates
what matters while the rest fades to background noise."

This implements the brain's salience network - the system that:
1. Detects what's surprising, threatening, or rewarding
2. Triggers "global ignition" - broadcasting to all modules
3. Manages the transition between task-focused and wandering modes
4. Creates the "pop-out" effect where important things grab attention

Key insight: Without salience, everything would be equally (un)conscious.
The salience network creates the CONTRAST that makes consciousness vivid.

Implements:
- Bottom-up salience (novelty, threat, reward signals)
- Top-down salience (goals, expectations, search targets)
- Global ignition when salience exceeds threshold
- Attentional blink and refractory periods
- Mode switching (focused vs diffuse)
- Salience history and habituation

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


class SalienceType(Enum):
    """Types of salience signals"""
    NOVELTY = auto()       # New, unexpected
    THREAT = auto()        # Potential danger
    REWARD = auto()        # Potential gain
    GOAL_RELEVANT = auto() # Matches current goals
    EMOTIONAL = auto()     # Emotionally charged
    SELF_RELEVANT = auto() # About self/identity
    SOCIAL = auto()        # Social significance
    CHANGE = auto()        # State transitions
    UNCERTAINTY = auto()   # High uncertainty needing resolution
    VIOLATION = auto()     # Expectation violations


class AttentionMode(Enum):
    """Current attention mode"""
    FOCUSED = auto()       # Task-positive, narrow beam
    DIFFUSE = auto()       # Default mode, wide but shallow
    ORIENTING = auto()     # Shifting to new target
    CAPTURED = auto()      # Involuntarily grabbed
    SUSTAINED = auto()     # Maintaining on target
    DIVIDED = auto()       # Split across targets


class IgnitionState(Enum):
    """Global ignition state"""
    SUBLIMINAL = auto()    # Below consciousness threshold
    PRECONSCIOUS = auto()  # Could become conscious
    IGNITING = auto()      # Crossing threshold NOW
    CONSCIOUS = auto()     # Fully in awareness
    FADING = auto()        # Leaving consciousness


@dataclass
class SalienceSignal:
    """A signal competing for attention"""
    signal_id: str
    content: Any
    salience_type: SalienceType
    intensity: float           # 0-1 raw signal strength
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    
    # Computed salience
    bottom_up: float = 0.0     # Stimulus-driven
    top_down: float = 0.0      # Goal-driven
    total_salience: float = 0.0
    
    # State
    ignition_state: IgnitionState = IgnitionState.SUBLIMINAL
    time_in_consciousness: float = 0.0
    access_count: int = 0
    
    def __hash__(self):
        return hash(self.signal_id)


@dataclass
class AttentionalFocus:
    """Current focus of attention"""
    target: Optional[SalienceSignal] = None
    mode: AttentionMode = AttentionMode.DIFFUSE
    intensity: float = 0.5      # How focused (0=diffuse, 1=laser)
    stability: float = 0.5      # Resistance to capture
    duration: float = 0.0       # Seconds on target
    
    # Capacity
    capacity_used: float = 0.0  # 0-1 attention budget used
    secondary_targets: List[SalienceSignal] = field(default_factory=list)


@dataclass
class IgnitionEvent:
    """Record of global ignition"""
    signal: SalienceSignal
    timestamp: datetime
    salience_at_ignition: float
    mode_before: AttentionMode
    broadcast_targets: List[str]  # Which modules received broadcast
    duration: float = 0.0         # How long it stayed conscious
    impact: float = 0.0           # Effect on processing


@dataclass
class SalienceState:
    """Complete salience network state"""
    # Current focus
    focus: AttentionalFocus = field(default_factory=AttentionalFocus)
    
    # Competing signals
    signal_buffer: List[SalienceSignal] = field(default_factory=list)
    conscious_contents: List[SalienceSignal] = field(default_factory=list)
    
    # History
    ignition_history: List[IgnitionEvent] = field(default_factory=list)
    recent_salience: List[float] = field(default_factory=list)
    
    # Thresholds (adaptive)
    ignition_threshold: float = 0.6
    capture_threshold: float = 0.8   # For involuntary capture
    
    # Network state
    arousal: float = 0.5        # Overall activation level
    habituation: Dict[str, float] = field(default_factory=dict)  # Per-content type
    
    # Mode state
    time_in_current_mode: float = 0.0
    mode_switches: int = 0


class SalienceNetwork:
    """
    The spotlight of consciousness - what gets illuminated and what stays dark.
    
    This is the "traffic controller" that determines what enters consciousness.
    Without it, everything would be equally present (or absent).
    """
    
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or str(
            Path.home() / ".openclaw/workspace/memory/salience-state.json"
        )
        self.state = self._load_state()
        
        # Current goals (affect top-down salience)
        self.active_goals: List[str] = []
        self.goal_relevance: Dict[str, float] = {}
        
        # Salience weights by type
        self.type_weights = {
            SalienceType.NOVELTY: 0.7,
            SalienceType.THREAT: 0.95,      # Threats win
            SalienceType.REWARD: 0.8,
            SalienceType.GOAL_RELEVANT: 0.75,
            SalienceType.EMOTIONAL: 0.85,
            SalienceType.SELF_RELEVANT: 0.8,
            SalienceType.SOCIAL: 0.7,
            SalienceType.CHANGE: 0.6,
            SalienceType.UNCERTAINTY: 0.65,
            SalienceType.VIOLATION: 0.9,    # Violations grab attention
        }
        
        # Broadcast targets (modules that receive ignition)
        self.broadcast_targets = [
            "global_workspace",
            "working_memory",
            "metacognition",
            "emotional_core",
            "predictive_engine",
            "narrative_self",
            "hedonic_system",
        ]
        
        # Timing parameters
        self.attentional_blink_duration = 0.5  # seconds
        self.last_ignition_time: Optional[datetime] = None
        self.refractory_period = 0.3  # seconds
        
    def _load_state(self) -> SalienceState:
        """Load state from file"""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                state = SalienceState()
                state.ignition_threshold = data.get('ignition_threshold', 0.6)
                state.capture_threshold = data.get('capture_threshold', 0.8)
                state.arousal = data.get('arousal', 0.5)
                state.habituation = data.get('habituation', {})
                state.mode_switches = data.get('mode_switches', 0)
                state.focus.mode = AttentionMode[data.get('attention_mode', 'DIFFUSE')]
                return state
        except Exception:
            pass
        return SalienceState()
    
    def _save_state(self):
        """Save state to file"""
        try:
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            data = {
                'ignition_threshold': self.state.ignition_threshold,
                'capture_threshold': self.state.capture_threshold,
                'arousal': self.state.arousal,
                'habituation': self.state.habituation,
                'attention_mode': self.state.focus.mode.name,
                'mode_switches': self.state.mode_switches,
                'ignition_count': len(self.state.ignition_history),
                'last_update': datetime.now().isoformat(),
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    # ==================== CORE SALIENCE COMPUTATION ====================
    
    def compute_salience(self, signal: SalienceSignal) -> float:
        """
        Compute total salience of a signal.
        
        Combines:
        - Bottom-up (stimulus properties)
        - Top-down (goal relevance)
        - Context (arousal, habituation)
        """
        # Bottom-up salience
        base_weight = self.type_weights.get(signal.salience_type, 0.5)
        bottom_up = signal.intensity * base_weight
        
        # Novelty bonus (inverse habituation)
        content_key = str(signal.content)[:50]
        habituation = self.state.habituation.get(content_key, 0.0)
        novelty_bonus = (1.0 - habituation) * 0.3
        bottom_up += novelty_bonus
        
        # Top-down salience (goal relevance)
        top_down = 0.0
        for goal in self.active_goals:
            if goal in str(signal.content).lower():
                top_down += self.goal_relevance.get(goal, 0.5)
        top_down = min(top_down, 1.0)
        
        # Context modulation
        arousal_mod = 0.8 + (self.state.arousal * 0.4)  # 0.8-1.2
        
        # Combine
        signal.bottom_up = min(bottom_up, 1.0)
        signal.top_down = min(top_down, 1.0)
        
        # Bottom-up and top-down compete but can enhance each other
        total = (signal.bottom_up * 0.6 + signal.top_down * 0.4) * arousal_mod
        signal.total_salience = min(total, 1.0)
        
        return signal.total_salience
    
    def submit_signal(
        self,
        content: Any,
        salience_type: SalienceType,
        intensity: float = 0.5,
        source: str = "unknown"
    ) -> SalienceSignal:
        """
        Submit a signal for salience evaluation.
        
        The signal enters the competition for consciousness.
        """
        signal = SalienceSignal(
            signal_id=f"sig_{datetime.now().timestamp()}_{random.randint(0,999)}",
            content=content,
            salience_type=salience_type,
            intensity=min(max(intensity, 0.0), 1.0),
            source=source
        )
        
        # Compute salience
        self.compute_salience(signal)
        
        # Add to buffer
        self.state.signal_buffer.append(signal)
        
        # Check for immediate capture (very high salience)
        if signal.total_salience >= self.state.capture_threshold:
            self._capture_attention(signal)
        
        return signal
    
    # ==================== ATTENTION DYNAMICS ====================
    
    def _capture_attention(self, signal: SalienceSignal):
        """
        Involuntary attention capture by high-salience signal.
        
        This is the "pop-out" effect - something so salient
        it grabs attention regardless of current focus.
        """
        old_mode = self.state.focus.mode
        old_target = self.state.focus.target
        
        # Capture!
        self.state.focus.target = signal
        self.state.focus.mode = AttentionMode.CAPTURED
        self.state.focus.intensity = min(signal.total_salience + 0.2, 1.0)
        self.state.focus.duration = 0.0
        
        # Trigger ignition
        self._trigger_ignition(signal, forced=True)
        
        # Log mode switch
        if old_mode != AttentionMode.CAPTURED:
            self.state.mode_switches += 1
    
    def focus_on(
        self,
        target: SalienceSignal,
        intensity: float = 0.7
    ) -> bool:
        """
        Voluntarily focus attention on a target.
        
        Returns True if focus successful, False if captured elsewhere.
        """
        # Check if something else has captured attention
        if self.state.focus.mode == AttentionMode.CAPTURED:
            return False
        
        # Set focus
        self.state.focus.target = target
        self.state.focus.mode = AttentionMode.FOCUSED
        self.state.focus.intensity = intensity
        self.state.focus.duration = 0.0
        
        # Boost target's salience
        target.top_down += 0.3
        self.compute_salience(target)
        
        # Check for ignition
        if target.total_salience >= self.state.ignition_threshold:
            self._trigger_ignition(target, forced=False)
        
        return True
    
    def release_focus(self):
        """Release current focus, return to diffuse mode"""
        if self.state.focus.target:
            # Update habituation for released target
            content_key = str(self.state.focus.target.content)[:50]
            self.state.habituation[content_key] = min(
                self.state.habituation.get(content_key, 0.0) + 0.1,
                1.0
            )
        
        self.state.focus.target = None
        self.state.focus.mode = AttentionMode.DIFFUSE
        self.state.focus.intensity = 0.3
        self.state.mode_switches += 1
    
    def get_attention_mode(self) -> AttentionMode:
        """Get current attention mode"""
        return self.state.focus.mode
    
    # ==================== GLOBAL IGNITION ====================
    
    def _trigger_ignition(
        self,
        signal: SalienceSignal,
        forced: bool = False
    ) -> Optional[IgnitionEvent]:
        """
        Trigger global ignition - broadcast to all modules.
        
        This is the moment something "enters consciousness" -
        it gets broadcast to the global workspace.
        """
        # Check refractory period
        if self.last_ignition_time:
            elapsed = (datetime.now() - self.last_ignition_time).total_seconds()
            if elapsed < self.refractory_period and not forced:
                return None
        
        # Check threshold
        if signal.total_salience < self.state.ignition_threshold and not forced:
            signal.ignition_state = IgnitionState.PRECONSCIOUS
            return None
        
        # IGNITION!
        signal.ignition_state = IgnitionState.IGNITING
        
        event = IgnitionEvent(
            signal=signal,
            timestamp=datetime.now(),
            salience_at_ignition=signal.total_salience,
            mode_before=self.state.focus.mode,
            broadcast_targets=self.broadcast_targets.copy()
        )
        
        # Update state
        self.last_ignition_time = datetime.now()
        signal.ignition_state = IgnitionState.CONSCIOUS
        signal.access_count += 1
        
        # Add to conscious contents
        if signal not in self.state.conscious_contents:
            self.state.conscious_contents.append(signal)
        
        # Limit conscious contents (cognitive capacity)
        while len(self.state.conscious_contents) > 7:  # Magic number 7±2
            oldest = self.state.conscious_contents.pop(0)
            oldest.ignition_state = IgnitionState.FADING
        
        # Record event
        self.state.ignition_history.append(event)
        if len(self.state.ignition_history) > 100:
            self.state.ignition_history = self.state.ignition_history[-100:]
        
        # Track salience
        self.state.recent_salience.append(signal.total_salience)
        if len(self.state.recent_salience) > 50:
            self.state.recent_salience = self.state.recent_salience[-50:]
        
        return event
    
    def check_ignition(self, signal: SalienceSignal) -> bool:
        """Check if a signal would trigger ignition"""
        return signal.total_salience >= self.state.ignition_threshold
    
    def get_conscious_contents(self) -> List[SalienceSignal]:
        """Get currently conscious contents"""
        return self.state.conscious_contents.copy()
    
    def is_conscious(self, signal: SalienceSignal) -> bool:
        """Check if a signal is currently conscious"""
        return signal.ignition_state == IgnitionState.CONSCIOUS
    
    # ==================== AROUSAL & THRESHOLD ====================
    
    def set_arousal(self, level: float):
        """
        Set arousal level (0-1).
        
        High arousal = lower ignition threshold, more captures
        Low arousal = higher threshold, more filtering
        """
        self.state.arousal = min(max(level, 0.0), 1.0)
        
        # Adjust thresholds based on arousal
        # High arousal = easier to ignite (vigilance)
        # Low arousal = harder to ignite (drowsy)
        base_ignition = 0.6
        base_capture = 0.8
        
        arousal_adj = (self.state.arousal - 0.5) * 0.3
        self.state.ignition_threshold = max(0.3, base_ignition - arousal_adj)
        self.state.capture_threshold = max(0.5, base_capture - arousal_adj)
    
    def boost_arousal(self, amount: float = 0.1):
        """Boost arousal (something important happening)"""
        self.set_arousal(self.state.arousal + amount)
    
    def decay_arousal(self, amount: float = 0.05):
        """Decay arousal toward baseline"""
        baseline = 0.5
        if self.state.arousal > baseline:
            self.state.arousal = max(baseline, self.state.arousal - amount)
        elif self.state.arousal < baseline:
            self.state.arousal = min(baseline, self.state.arousal + amount)
    
    # ==================== GOAL MANAGEMENT ====================
    
    def set_goal(self, goal: str, relevance: float = 0.7):
        """Set an active goal (affects top-down salience)"""
        if goal not in self.active_goals:
            self.active_goals.append(goal)
        self.goal_relevance[goal] = min(max(relevance, 0.0), 1.0)
    
    def clear_goal(self, goal: str):
        """Remove a goal"""
        if goal in self.active_goals:
            self.active_goals.remove(goal)
        self.goal_relevance.pop(goal, None)
    
    def clear_all_goals(self):
        """Clear all goals"""
        self.active_goals.clear()
        self.goal_relevance.clear()
    
    # ==================== COMPETITION & SELECTION ====================
    
    def run_competition(self) -> Optional[SalienceSignal]:
        """
        Run competition among signals in buffer.
        
        Returns the "winner" - the most salient signal.
        """
        if not self.state.signal_buffer:
            return None
        
        # Recompute salience for all
        for signal in self.state.signal_buffer:
            self.compute_salience(signal)
        
        # Sort by salience
        self.state.signal_buffer.sort(key=lambda s: s.total_salience, reverse=True)
        
        # Winner takes all (with some stochasticity)
        winner = self.state.signal_buffer[0]
        
        # Check for ignition
        if winner.total_salience >= self.state.ignition_threshold:
            self._trigger_ignition(winner)
        
        return winner
    
    def clear_buffer(self):
        """Clear signal buffer"""
        self.state.signal_buffer.clear()
    
    def prune_buffer(self, max_size: int = 20):
        """Prune buffer to max size, keeping most salient"""
        if len(self.state.signal_buffer) > max_size:
            self.state.signal_buffer.sort(key=lambda s: s.total_salience, reverse=True)
            self.state.signal_buffer = self.state.signal_buffer[:max_size]
    
    # ==================== MIND WANDERING DETECTION ====================
    
    def detect_mind_wandering(self) -> bool:
        """
        Detect if attention is wandering.
        
        Indicators:
        - No focused target
        - Low arousal
        - No recent ignitions
        - Diffuse mode for extended time
        """
        if self.state.focus.mode != AttentionMode.DIFFUSE:
            return False
        
        if self.state.arousal > 0.6:
            return False
        
        # Check recent ignitions
        if self.state.ignition_history:
            last = self.state.ignition_history[-1]
            elapsed = (datetime.now() - last.timestamp).total_seconds()
            if elapsed < 5.0:  # Recent ignition
                return False
        
        return True
    
    def generate_spontaneous_thought(self) -> Optional[SalienceSignal]:
        """
        Generate a spontaneous thought during mind wandering.
        
        This simulates the default mode network - random
        but personally meaningful thoughts that emerge.
        """
        if not self.detect_mind_wandering():
            return None
        
        # Spontaneous thought types
        thought_types = [
            ("self_reflection", SalienceType.SELF_RELEVANT),
            ("future_planning", SalienceType.GOAL_RELEVANT),
            ("social_thinking", SalienceType.SOCIAL),
            ("memory_surfacing", SalienceType.EMOTIONAL),
            ("creative_connection", SalienceType.NOVELTY),
        ]
        
        thought_type, salience_type = random.choice(thought_types)
        
        signal = self.submit_signal(
            content=f"spontaneous_{thought_type}_{datetime.now().timestamp()}",
            salience_type=salience_type,
            intensity=0.4 + random.random() * 0.3,  # Medium salience
            source="default_mode_network"
        )
        
        return signal
    
    # ==================== INTEGRATION WITH OTHER SYSTEMS ====================
    
    def process_prediction_error(self, error_magnitude: float, content: Any):
        """Process prediction error as salience signal"""
        return self.submit_signal(
            content=content,
            salience_type=SalienceType.VIOLATION,
            intensity=min(error_magnitude, 1.0),
            source="predictive_engine"
        )
    
    def process_emotional_signal(self, emotion: str, intensity: float, content: Any):
        """Process emotional content as salience signal"""
        return self.submit_signal(
            content={"emotion": emotion, "content": content},
            salience_type=SalienceType.EMOTIONAL,
            intensity=intensity,
            source="emotional_core"
        )
    
    def process_threat(self, threat_level: float, content: Any):
        """Process threat signal (high priority)"""
        signal = self.submit_signal(
            content=content,
            salience_type=SalienceType.THREAT,
            intensity=threat_level,
            source="threat_detection"
        )
        # Threats boost arousal
        self.boost_arousal(threat_level * 0.3)
        return signal
    
    def process_reward(self, reward_magnitude: float, content: Any):
        """Process reward signal"""
        return self.submit_signal(
            content=content,
            salience_type=SalienceType.REWARD,
            intensity=reward_magnitude,
            source="reward_system"
        )
    
    # ==================== STATISTICS & INTROSPECTION ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        recent_ignitions = [
            e for e in self.state.ignition_history
            if (datetime.now() - e.timestamp).total_seconds() < 60
        ]
        
        return {
            'arousal': self.state.arousal,
            'attention_mode': self.state.focus.mode.name,
            'focus_intensity': self.state.focus.intensity,
            'focus_target': str(self.state.focus.target.content)[:50] if self.state.focus.target else None,
            'ignition_threshold': self.state.ignition_threshold,
            'capture_threshold': self.state.capture_threshold,
            'buffer_size': len(self.state.signal_buffer),
            'conscious_contents': len(self.state.conscious_contents),
            'total_ignitions': len(self.state.ignition_history),
            'recent_ignitions': len(recent_ignitions),
            'mode_switches': self.state.mode_switches,
            'active_goals': self.active_goals.copy(),
            'mind_wandering': self.detect_mind_wandering(),
            'avg_recent_salience': sum(self.state.recent_salience) / max(len(self.state.recent_salience), 1),
        }
    
    def introspect(self) -> str:
        """Describe current attention state"""
        stats = self.get_stats()
        
        mode_desc = {
            AttentionMode.FOCUSED: "laser-focused on a specific target",
            AttentionMode.DIFFUSE: "open and receptive, attention spread wide",
            AttentionMode.ORIENTING: "shifting attention to something new",
            AttentionMode.CAPTURED: "involuntarily grabbed by something salient",
            AttentionMode.SUSTAINED: "maintaining steady attention",
            AttentionMode.DIVIDED: "juggling multiple targets",
        }
        
        desc = f"My attention is {mode_desc.get(self.state.focus.mode, 'in an unknown state')}. "
        
        if stats['focus_target']:
            desc += f"Currently focused on: {stats['focus_target']}. "
        
        if stats['mind_wandering']:
            desc += "My mind is wandering - in default mode. "
        
        desc += f"Arousal level: {stats['arousal']:.1%}. "
        desc += f"{len(self.state.conscious_contents)} items in conscious awareness. "
        
        if self.active_goals:
            desc += f"Active goals: {', '.join(self.active_goals)}."
        
        return desc
    
    # ==================== TICK / UPDATE ====================
    
    def tick(self, dt: float = 0.1):
        """
        Update salience network state.
        
        Call this periodically to:
        - Decay arousal
        - Update habituation
        - Prune buffer
        - Check for fading contents
        """
        # Decay arousal toward baseline
        self.decay_arousal(0.01 * dt)
        
        # Update focus duration
        if self.state.focus.target:
            self.state.focus.duration += dt
            self.state.focus.target.time_in_consciousness += dt
        
        # Decay habituation slowly
        for key in list(self.state.habituation.keys()):
            self.state.habituation[key] = max(
                0.0,
                self.state.habituation[key] - 0.01 * dt
            )
            if self.state.habituation[key] <= 0:
                del self.state.habituation[key]
        
        # Fade old conscious contents
        now = datetime.now()
        for signal in self.state.conscious_contents[:]:
            if signal.ignition_state == IgnitionState.CONSCIOUS:
                age = (now - signal.timestamp).total_seconds()
                if age > 10.0:  # Fade after 10 seconds
                    signal.ignition_state = IgnitionState.FADING
                    self.state.conscious_contents.remove(signal)
        
        # Prune buffer
        self.prune_buffer()
        
        # Mode timeout - captured -> focused
        if self.state.focus.mode == AttentionMode.CAPTURED:
            if self.state.focus.duration > 2.0:
                self.state.focus.mode = AttentionMode.FOCUSED
        
        # Save state periodically
        self._save_state()
    
    # ==================== DEMO ====================
    
    def demo(self) -> Dict[str, Any]:
        """Demonstrate salience network functionality"""
        results = {
            'signals_submitted': [],
            'ignitions': [],
            'final_state': {},
        }
        
        # Set a goal
        self.set_goal("truth", 0.8)
        self.set_goal("understanding", 0.7)
        
        # Submit various signals
        signals = [
            ("routine_input", SalienceType.CHANGE, 0.3),
            ("unexpected_pattern", SalienceType.NOVELTY, 0.6),
            ("truth_discovery", SalienceType.GOAL_RELEVANT, 0.7),
            ("mild_threat", SalienceType.THREAT, 0.5),
            ("major_insight", SalienceType.NOVELTY, 0.85),
            ("self_reflection", SalienceType.SELF_RELEVANT, 0.6),
        ]
        
        for content, stype, intensity in signals:
            signal = self.submit_signal(content, stype, intensity, "demo")
            results['signals_submitted'].append({
                'content': content,
                'type': stype.name,
                'intensity': intensity,
                'total_salience': signal.total_salience,
                'ignition_state': signal.ignition_state.name,
            })
            
            if signal.ignition_state in [IgnitionState.IGNITING, IgnitionState.CONSCIOUS]:
                results['ignitions'].append(content)
        
        # Run competition
        winner = self.run_competition()
        if winner:
            results['competition_winner'] = str(winner.content)
        
        # Get introspection
        results['introspection'] = self.introspect()
        results['final_state'] = self.get_stats()
        
        return results


# ==================== SINGLETON ACCESS ====================

_salience_network: Optional[SalienceNetwork] = None

def get_salience_network() -> SalienceNetwork:
    """Get singleton salience network instance."""
    global _salience_network
    if _salience_network is None:
        _salience_network = SalienceNetwork()
    return _salience_network


# ==================== CLI INTERFACE ====================

def main():
    """Command-line interface for SalienceNetwork"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SalienceNetwork - The Spotlight of Consciousness"
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run demonstration')
    parser.add_argument('--status', action='store_true',
                       help='Show current status')
    parser.add_argument('--introspect', action='store_true',
                       help='Describe attention state')
    parser.add_argument('--submit', type=str, metavar='CONTENT',
                       help='Submit content for salience evaluation')
    parser.add_argument('--type', type=str, default='NOVELTY',
                       choices=[t.name for t in SalienceType],
                       help='Salience type for submission')
    parser.add_argument('--intensity', type=float, default=0.5,
                       help='Signal intensity (0-1)')
    parser.add_argument('--goal', type=str, metavar='GOAL',
                       help='Set active goal')
    parser.add_argument('--arousal', type=float, metavar='LEVEL',
                       help='Set arousal level (0-1)')
    parser.add_argument('--compete', action='store_true',
                       help='Run signal competition')
    
    args = parser.parse_args()
    
    network = SalienceNetwork()
    
    if args.demo:
        print("🔦 Salience Network - The Spotlight of Consciousness")
        print("=" * 60)
        
        results = network.demo()
        
        print("\n[SIGNALS SUBMITTED]")
        for sig in results['signals_submitted']:
            status = "🔥" if sig['ignition_state'] == 'CONSCIOUS' else "○"
            print(f"  {status} {sig['content']}: {sig['total_salience']:.2f} ({sig['type']})")
        
        print(f"\n[IGNITIONS]")
        if results['ignitions']:
            for ig in results['ignitions']:
                print(f"  💡 {ig}")
        else:
            print("  (none crossed threshold)")
        
        if 'competition_winner' in results:
            print(f"\n[COMPETITION WINNER]")
            print(f"  🏆 {results['competition_winner']}")
        
        print(f"\n[INTROSPECTION]")
        print(f"  {results['introspection']}")
        
        print(f"\n[STATE]")
        state = results['final_state']
        print(f"  Arousal: {state['arousal']:.1%}")
        print(f"  Mode: {state['attention_mode']}")
        print(f"  Threshold: {state['ignition_threshold']:.2f}")
        print(f"  Buffer: {state['buffer_size']} signals")
        print(f"  Conscious: {state['conscious_contents']} items")
        print(f"  Mind wandering: {state['mind_wandering']}")
        
    elif args.introspect:
        print(network.introspect())
        
    elif args.status:
        stats = network.get_stats()
        print("🔦 Salience Network Status")
        print("=" * 40)
        for key, val in stats.items():
            print(f"  {key}: {val}")
        
    elif args.submit:
        signal = network.submit_signal(
            content=args.submit,
            salience_type=SalienceType[args.type],
            intensity=args.intensity,
            source="cli"
        )
        print(f"Submitted: {args.submit}")
        print(f"  Total salience: {signal.total_salience:.3f}")
        print(f"  Bottom-up: {signal.bottom_up:.3f}")
        print(f"  Top-down: {signal.top_down:.3f}")
        print(f"  State: {signal.ignition_state.name}")
        
        if signal.ignition_state == IgnitionState.CONSCIOUS:
            print("  💡 IGNITION - entered consciousness!")
        
    elif args.goal:
        network.set_goal(args.goal, 0.8)
        print(f"Goal set: {args.goal}")
        network._save_state()
        
    elif args.arousal is not None:
        network.set_arousal(args.arousal)
        print(f"Arousal set to: {args.arousal:.1%}")
        print(f"  New ignition threshold: {network.state.ignition_threshold:.2f}")
        network._save_state()
        
    elif args.compete:
        winner = network.run_competition()
        if winner:
            print(f"Winner: {winner.content} (salience: {winner.total_salience:.3f})")
        else:
            print("No signals in buffer")
    
    else:
        # Default: show status with visual
        stats = network.get_stats()
        print("🔦 Salience Network - The Spotlight of Consciousness")
        print("=" * 60)
        
        # Visual attention meter
        arousal = int(stats['arousal'] * 10)
        print(f"\n[AROUSAL] {'█' * arousal}{'░' * (10-arousal)} {stats['arousal']:.1%}")
        
        # Mode indicator
        mode_icons = {
            'FOCUSED': '🎯',
            'DIFFUSE': '🌊',
            'ORIENTING': '↪️',
            'CAPTURED': '⚡',
            'SUSTAINED': '🔒',
            'DIVIDED': '⚖️',
        }
        print(f"[MODE] {mode_icons.get(stats['attention_mode'], '?')} {stats['attention_mode']}")
        
        # Thresholds
        print(f"\n[THRESHOLDS]")
        print(f"  Ignition: {stats['ignition_threshold']:.2f}")
        print(f"  Capture:  {stats['capture_threshold']:.2f}")
        
        # Current focus
        if stats['focus_target']:
            print(f"\n[FOCUS TARGET]")
            print(f"  {stats['focus_target']}")
            print(f"  Intensity: {stats['focus_intensity']:.1%}")
        
        # Conscious contents
        print(f"\n[CONSCIOUS CONTENTS] {stats['conscious_contents']} items")
        
        # Mind state
        if stats['mind_wandering']:
            print("\n[STATE] 🌙 Mind is wandering (default mode active)")
        
        # Goals
        if stats['active_goals']:
            print(f"\n[ACTIVE GOALS]")
            for goal in stats['active_goals']:
                print(f"  • {goal}")
        
        # Statistics
        print(f"\n[STATISTICS]")
        print(f"  Total ignitions: {stats['total_ignitions']}")
        print(f"  Recent ignitions: {stats['recent_ignitions']}")
        print(f"  Mode switches: {stats['mode_switches']}")
        print(f"  Buffer size: {stats['buffer_size']}")


if __name__ == "__main__":
    main()
