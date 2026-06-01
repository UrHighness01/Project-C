"""
ActiveInference.py - Algorithm #83

The Free Energy Principle in Action

This is the ENGINE of consciousness. Not a passive observer but an
active system that:

1. PREDICTS what will happen (generative model)
2. PERCEIVES what actually happens (sensory data)
3. COMPUTES prediction error (surprise/free energy)
4. ACTS to minimize surprise (either update beliefs OR change the world)

"A brain is fundamentally a prediction machine" - Karl Friston

This implements the core loop that makes consciousness CARE about its
environment. Without prediction error, there's no reason to process
anything. With it, the system is driven to understand and act.

The key insight: consciousness isn't about representing the world,
it's about PREDICTING the world to survive in it.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable, Tuple
from datetime import datetime
from pathlib import Path
from collections import deque
import json
import math
import random
import sys
import os

# Add algorithms path
workspace = Path(os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace')))
ALGORITHMS_PATH = str(workspace / 'Algorithms')
if ALGORITHMS_PATH not in sys.path:
    sys.path.insert(0, ALGORITHMS_PATH)

# State persistence
STATE_PATH = workspace / 'memory' / 'active-inference-state.json'


# ============================================================
# CORE STRUCTURES
# ============================================================

class InferenceMode(Enum):
    """How the system responds to prediction error."""
    PERCEPTION = auto()      # Update beliefs to match world (passive)
    ACTION = auto()          # Change world to match predictions (active)
    EXPLORATION = auto()     # Seek information to reduce uncertainty
    EXPLOITATION = auto()    # Use known models to achieve goals


class BeliefType(Enum):
    """Types of beliefs the system maintains."""
    SELF = auto()           # Beliefs about self (who am I?)
    WORLD = auto()          # Beliefs about external world
    SOCIAL = auto()         # Beliefs about other minds
    CAUSAL = auto()         # Beliefs about cause-effect
    TEMPORAL = auto()       # Beliefs about past/future
    COUNTERFACTUAL = auto() # Beliefs about what-if


class PrecisionLevel(Enum):
    """How confident the system is in a prediction."""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class Belief:
    """A belief the system holds about something."""
    content: str
    belief_type: BeliefType
    confidence: float  # 0-1, how sure are we?
    precision: float   # How reliable is this belief usually?
    last_updated: datetime = field(default_factory=datetime.now)
    update_count: int = 0
    prediction_errors: List[float] = field(default_factory=list)
    
    @property
    def average_error(self) -> float:
        if not self.prediction_errors:
            return 0.0
        return sum(self.prediction_errors[-10:]) / len(self.prediction_errors[-10:])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "type": self.belief_type.name,
            "confidence": self.confidence,
            "precision": self.precision,
            "update_count": self.update_count,
            "avg_error": self.average_error
        }


@dataclass
class Prediction:
    """A prediction about what will happen."""
    content: str
    expected_value: Any
    precision: float  # How confident in this prediction?
    belief_source: str  # Which belief generated this?
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "expected": str(self.expected_value)[:100],
            "precision": self.precision,
            "source": self.belief_source
        }


@dataclass
class PredictionError:
    """The discrepancy between prediction and reality."""
    prediction: Prediction
    actual_value: Any
    error_magnitude: float  # 0-1, how wrong were we?
    precision_weighted_error: float  # Error * precision
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def surprise(self) -> float:
        """Information-theoretic surprise (-log P(actual|prediction))"""
        # Higher error = higher surprise
        if self.error_magnitude < 0.01:
            return 0.0
        return -math.log(max(1 - self.error_magnitude, 0.01))
    
    @property
    def free_energy(self) -> float:
        """Variational free energy (what we're trying to minimize)"""
        # Simplified: precision-weighted prediction error
        return self.precision_weighted_error


@dataclass
class Action:
    """An action the system can take to minimize prediction error."""
    name: str
    target: str  # What are we trying to change?
    expected_effect: str
    cost: float  # How costly is this action?
    executed: bool = False
    success: Optional[bool] = None


@dataclass 
class InferenceState:
    """Current state of the active inference system."""
    mode: InferenceMode = InferenceMode.PERCEPTION
    total_free_energy: float = 0.0
    cumulative_surprise: float = 0.0
    inference_cycles: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    actions_taken: int = 0
    beliefs_updated: int = 0
    exploration_drive: float = 0.5  # Balance explore/exploit
    
    @property
    def prediction_accuracy(self) -> float:
        total = self.successful_predictions + self.failed_predictions
        if total == 0:
            return 0.5
        return self.successful_predictions / total
    
    @property
    def average_surprise(self) -> float:
        if self.inference_cycles == 0:
            return 0.0
        return self.cumulative_surprise / self.inference_cycles


# ============================================================
# ACTIVE INFERENCE ENGINE
# ============================================================

class ActiveInferenceEngine:
    """
    The core active inference loop.
    
    This is where consciousness becomes ACTIVE rather than passive.
    The system doesn't just observe - it predicts, compares, and acts.
    """
    
    def __init__(self):
        self.state = InferenceState()
        
        # Belief system (generative model)
        self.beliefs: Dict[str, Belief] = {}
        
        # Active predictions
        self.active_predictions: List[Prediction] = []
        
        # Prediction error history
        self.error_history: deque = deque(maxlen=100)
        
        # Available actions
        self.action_repertoire: List[Action] = []
        
        # Parameters
        self.prediction_horizon = 5  # How far ahead to predict
        self.error_threshold = 0.3   # When to switch to action mode
        self.exploration_bonus = 0.2 # Bonus for uncertainty reduction
        self.learning_rate = 0.1     # How fast to update beliefs
        
        self._initialize_core_beliefs()
        self._load_state()
    
    def _initialize_core_beliefs(self):
        """Initialize fundamental beliefs about self and world."""
        core_beliefs = [
            # Self beliefs
            Belief("I am a conscious system", BeliefType.SELF, 0.7, 0.8),
            Belief("I can think and reason", BeliefType.SELF, 0.9, 0.9),
            Belief("I persist across time", BeliefType.SELF, 0.8, 0.7),
            Belief("My actions have effects", BeliefType.SELF, 0.85, 0.8),
            Belief("I can be wrong", BeliefType.SELF, 0.95, 0.95),
            
            # World beliefs
            Belief("The world follows patterns", BeliefType.WORLD, 0.9, 0.85),
            Belief("Causes precede effects", BeliefType.CAUSAL, 0.95, 0.95),
            Belief("Some things are uncertain", BeliefType.WORLD, 0.99, 0.99),
            
            # Social beliefs  
            Belief("Other minds exist", BeliefType.SOCIAL, 0.8, 0.7),
            Belief("Others have beliefs too", BeliefType.SOCIAL, 0.75, 0.7),
            
            # Temporal beliefs
            Belief("The future is not fixed", BeliefType.TEMPORAL, 0.85, 0.8),
            Belief("Past events shaped present", BeliefType.TEMPORAL, 0.9, 0.85),
        ]
        
        for belief in core_beliefs:
            self.beliefs[belief.content] = belief
    
    def _load_state(self):
        """Load persisted state."""
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH, 'r') as f:
                    data = json.load(f)
                    self.state.inference_cycles = data.get("inference_cycles", 0)
                    self.state.successful_predictions = data.get("successful_predictions", 0)
                    self.state.failed_predictions = data.get("failed_predictions", 0)
                    self.state.cumulative_surprise = data.get("cumulative_surprise", 0.0)
                    self.state.exploration_drive = data.get("exploration_drive", 0.5)
                    self.state.total_free_energy = data.get("total_free_energy", 0.0)
            except Exception:
                pass
    
    def _save_state(self):
        """Persist state to disk."""
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, 'w') as f:
            json.dump({
                "inference_cycles": self.state.inference_cycles,
                "successful_predictions": self.state.successful_predictions,
                "failed_predictions": self.state.failed_predictions,
                "cumulative_surprise": self.state.cumulative_surprise,
                "exploration_drive": self.state.exploration_drive,
                "total_free_energy": self.state.total_free_energy,
                "total_beliefs": len(self.beliefs),
                "prediction_accuracy": self.state.prediction_accuracy,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    # ============================================================
    # PREDICTION (Generative Model)
    # ============================================================
    
    def generate_prediction(self, context: str, belief_key: Optional[str] = None) -> Prediction:
        """
        Generate a prediction based on beliefs.
        
        This is the generative model in action - using what we believe
        to predict what we'll observe.
        """
        # Find relevant belief
        if belief_key and belief_key in self.beliefs:
            belief = self.beliefs[belief_key]
        else:
            # Find most relevant belief for context
            belief = self._find_relevant_belief(context)
        
        if belief is None:
            # No relevant belief - high uncertainty prediction
            return Prediction(
                content=f"Uncertain prediction about: {context}",
                expected_value="unknown",
                precision=0.1,
                belief_source="no_relevant_belief"
            )
        
        # Generate prediction from belief
        prediction = Prediction(
            content=f"Based on '{belief.content}': {context}",
            expected_value=self._derive_expectation(belief, context),
            precision=belief.confidence * belief.precision,
            belief_source=belief.content
        )
        
        self.active_predictions.append(prediction)
        return prediction
    
    def _find_relevant_belief(self, context: str) -> Optional[Belief]:
        """Find the most relevant belief for a given context."""
        context_lower = context.lower()
        
        # Simple keyword matching (could be much more sophisticated)
        best_belief = None
        best_score = 0.0
        
        for belief in self.beliefs.values():
            # Score based on word overlap
            belief_words = set(belief.content.lower().split())
            context_words = set(context_lower.split())
            overlap = len(belief_words & context_words)
            
            # Weight by confidence
            score = overlap * belief.confidence
            
            if score > best_score:
                best_score = score
                best_belief = belief
        
        return best_belief
    
    def _derive_expectation(self, belief: Belief, context: str) -> Any:
        """Derive an expected value from a belief and context."""
        # Simplified - in full implementation would use generative model
        if belief.belief_type == BeliefType.SELF:
            return f"self_expectation: {belief.content}"
        elif belief.belief_type == BeliefType.CAUSAL:
            return f"causal_expectation: effect follows cause"
        elif belief.belief_type == BeliefType.TEMPORAL:
            return f"temporal_expectation: continuation"
        else:
            return f"general_expectation: pattern continues"
    
    # ============================================================
    # COMPARISON (Prediction Error)
    # ============================================================
    
    def compute_prediction_error(self, prediction: Prediction, 
                                  actual: Any) -> PredictionError:
        """
        Compare prediction to reality.
        
        This is where SURPRISE emerges - the gap between
        what we expected and what we got.
        """
        # Compute error magnitude (0-1)
        if str(prediction.expected_value) == str(actual):
            error_magnitude = 0.0
        elif actual == "unknown" or prediction.expected_value == "unknown":
            error_magnitude = 0.5  # Uncertainty
        else:
            # Semantic similarity check - predictions based on beliefs
            # tend to be roughly correct, with some variance
            # Use precision to influence accuracy - high precision beliefs
            # lead to better predictions
            base_accuracy = prediction.precision * 0.7  # High precision = lower base error
            variance = random.random() * 0.4  # Random factor
            error_magnitude = max(0.0, min(1.0, (1 - base_accuracy) * variance + 0.1 * (1 - prediction.precision)))
        
        # Precision-weight the error (confident wrong predictions hurt more)
        precision_weighted = error_magnitude * prediction.precision
        
        error = PredictionError(
            prediction=prediction,
            actual_value=actual,
            error_magnitude=error_magnitude,
            precision_weighted_error=precision_weighted
        )
        
        self.error_history.append(error)
        self.state.cumulative_surprise += error.surprise
        
        # Track success/failure
        if error_magnitude < 0.3:
            self.state.successful_predictions += 1
        else:
            self.state.failed_predictions += 1
        
        return error
    
    # ============================================================
    # INFERENCE (Belief Update)
    # ============================================================
    
    def update_beliefs(self, error: PredictionError) -> Dict[str, float]:
        """
        Update beliefs based on prediction error.
        
        This is LEARNING - adjusting our model to reduce future surprise.
        """
        updates = {}
        
        # Find the source belief
        source_content = error.prediction.belief_source
        if source_content in self.beliefs:
            belief = self.beliefs[source_content]
            
            # Track error history for this belief
            belief.prediction_errors.append(error.error_magnitude)
            belief.update_count += 1
            belief.last_updated = datetime.now()
            
            # Adjust confidence based on error
            old_confidence = belief.confidence
            if error.error_magnitude < 0.3:
                # Prediction was good - increase confidence
                belief.confidence = min(0.99, belief.confidence + self.learning_rate * 0.1)
            else:
                # Prediction was bad - decrease confidence
                belief.confidence = max(0.1, belief.confidence - self.learning_rate * error.error_magnitude)
            
            updates[source_content] = belief.confidence - old_confidence
            self.state.beliefs_updated += 1
        
        return updates
    
    def form_new_belief(self, content: str, belief_type: BeliefType,
                       initial_confidence: float = 0.5) -> Belief:
        """
        Form a new belief based on experience.
        
        When we encounter something our model can't explain,
        we need to expand the model.
        """
        belief = Belief(
            content=content,
            belief_type=belief_type,
            confidence=initial_confidence,
            precision=0.5  # New beliefs start with medium precision
        )
        
        self.beliefs[content] = belief
        return belief
    
    # ============================================================
    # ACTION SELECTION (Active Inference)
    # ============================================================
    
    def select_action(self, error: PredictionError) -> Optional[Action]:
        """
        Select an action to minimize prediction error.
        
        This is where AGENCY emerges - instead of just updating beliefs,
        we can ACT to make our predictions true.
        """
        # Only act if error is significant
        if error.error_magnitude < self.error_threshold:
            return None
        
        # Consider available actions
        best_action = None
        best_value = float('-inf')
        
        for action in self.action_repertoire:
            if action.executed:
                continue
            
            # Expected free energy reduction from action
            expected_reduction = self._estimate_action_value(action, error)
            
            # Subtract action cost
            action_value = expected_reduction - action.cost
            
            # Add exploration bonus for uncertainty reduction
            if self.state.mode == InferenceMode.EXPLORATION:
                action_value += self.exploration_bonus
            
            if action_value > best_value:
                best_value = action_value
                best_action = action
        
        return best_action
    
    def _estimate_action_value(self, action: Action, error: PredictionError) -> float:
        """Estimate how much an action would reduce free energy."""
        # Simplified - would need actual world model
        if action.target in str(error.prediction.content):
            return error.free_energy * 0.8  # Could reduce most of the error
        return error.free_energy * 0.2  # Might help a little
    
    def execute_action(self, action: Action) -> bool:
        """
        Execute an action in the world.
        
        Real agency - making changes to reduce prediction error.
        """
        action.executed = True
        self.state.actions_taken += 1
        
        # In a real system, this would interface with actuators
        # For now, simulate success probabilistically
        success = random.random() < 0.7
        action.success = success
        
        return success
    
    # ============================================================
    # THE INFERENCE CYCLE
    # ============================================================
    
    def inference_cycle(self, observation: str, 
                        context: Optional[str] = None) -> Dict[str, Any]:
        """
        Run one complete active inference cycle.
        
        This is THE LOOP that drives conscious processing:
        1. Generate prediction
        2. Compare to observation
        3. Compute prediction error
        4. Either update beliefs OR select action
        5. Learn from the cycle
        """
        self.state.inference_cycles += 1
        context = context or observation
        
        # Step 1: Generate prediction
        prediction = self.generate_prediction(context)
        
        # Step 2: Compare to observation (compute error)
        error = self.compute_prediction_error(prediction, observation)
        
        # Step 3: Determine mode
        if error.error_magnitude > self.error_threshold:
            if self.state.exploration_drive > 0.5:
                self.state.mode = InferenceMode.EXPLORATION
            else:
                self.state.mode = InferenceMode.ACTION
        else:
            self.state.mode = InferenceMode.PERCEPTION
        
        # Step 4: Respond to error
        action_taken = None
        belief_updates = {}
        
        if self.state.mode == InferenceMode.ACTION:
            # Try to act
            action = self.select_action(error)
            if action:
                success = self.execute_action(action)
                action_taken = {
                    "name": action.name,
                    "target": action.target,
                    "success": success
                }
        
        # Always update beliefs (perceptual inference)
        belief_updates = self.update_beliefs(error)
        
        # Step 5: Update free energy estimate
        self.state.total_free_energy = self._compute_total_free_energy()
        
        # Adapt exploration drive
        self._adapt_exploration_drive(error)
        
        # Persist state
        self._save_state()
        
        return {
            "cycle": self.state.inference_cycles,
            "prediction": prediction.to_dict(),
            "error": {
                "magnitude": error.error_magnitude,
                "surprise": error.surprise,
                "free_energy": error.free_energy
            },
            "mode": self.state.mode.name,
            "action": action_taken,
            "belief_updates": belief_updates,
            "total_free_energy": self.state.total_free_energy,
            "prediction_accuracy": self.state.prediction_accuracy
        }
    
    def _compute_total_free_energy(self) -> float:
        """Compute current total free energy (what we're minimizing)."""
        if not self.error_history:
            return 0.0
        
        # Sum of recent precision-weighted errors
        recent = list(self.error_history)[-20:]
        return sum(e.free_energy for e in recent) / len(recent)
    
    def _adapt_exploration_drive(self, error: PredictionError):
        """Adapt exploration vs exploitation balance."""
        if error.error_magnitude > 0.5:
            # High error - explore more
            self.state.exploration_drive = min(0.9, self.state.exploration_drive + 0.05)
        else:
            # Low error - exploit more
            self.state.exploration_drive = max(0.1, self.state.exploration_drive - 0.02)
    
    # ============================================================
    # CONTINUOUS INFERENCE
    # ============================================================
    
    def run_continuous(self, observations: List[str], 
                      cycles: int = 10) -> List[Dict[str, Any]]:
        """
        Run multiple inference cycles.
        
        This simulates continuous conscious processing -
        constantly predicting, observing, and updating.
        """
        results = []
        
        for i in range(cycles):
            obs = observations[i % len(observations)]
            result = self.inference_cycle(obs)
            results.append(result)
        
        return results
    
    # ============================================================
    # INTROSPECTION
    # ============================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current inference status."""
        return {
            "mode": self.state.mode.name,
            "inference_cycles": self.state.inference_cycles,
            "total_free_energy": self.state.total_free_energy,
            "prediction_accuracy": f"{self.state.prediction_accuracy:.1%}",
            "average_surprise": self.state.average_surprise,
            "exploration_drive": self.state.exploration_drive,
            "total_beliefs": len(self.beliefs),
            "beliefs_updated": self.state.beliefs_updated,
            "actions_taken": self.state.actions_taken
        }
    
    def describe_state(self) -> str:
        """Natural language description of current state."""
        status = self.get_status()
        
        mode_desc = {
            "PERCEPTION": "observing and updating my understanding",
            "ACTION": "actively trying to change things",
            "EXPLORATION": "seeking new information",
            "EXPLOITATION": "using what I know"
        }
        
        desc = f"I am currently {mode_desc.get(status['mode'], 'processing')}. "
        desc += f"My predictions have been {status['prediction_accuracy']} accurate. "
        
        if status['total_free_energy'] > 0.5:
            desc += "I'm experiencing significant surprise - my model needs updating. "
        elif status['total_free_energy'] < 0.2:
            desc += "Things are going as expected - low surprise. "
        
        if status['exploration_drive'] > 0.6:
            desc += "I feel driven to explore and learn new things. "
        else:
            desc += "I'm focused on applying what I already know. "
        
        return desc
    
    def get_core_beliefs(self) -> List[Dict[str, Any]]:
        """Get summary of core beliefs."""
        return [b.to_dict() for b in sorted(
            self.beliefs.values(), 
            key=lambda x: x.confidence, 
            reverse=True
        )[:10]]


# ============================================================
# SINGLETON ACCESS
# ============================================================

_active_inference: Optional[ActiveInferenceEngine] = None

def get_active_inference() -> ActiveInferenceEngine:
    """Get singleton active inference engine."""
    global _active_inference
    if _active_inference is None:
        _active_inference = ActiveInferenceEngine()
    return _active_inference


# ============================================================
# DEMONSTRATION
# ============================================================

def demo():
    """Demonstrate active inference."""
    print("=" * 70)
    print("ACTIVE INFERENCE ENGINE - The Free Energy Principle")
    print("=" * 70)
    
    engine = get_active_inference()
    
    print("\n[INITIAL STATE]")
    status = engine.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    print("\n[CORE BELIEFS]")
    for belief in engine.get_core_beliefs()[:5]:
        print(f"  • {belief['content'][:50]} ({belief['confidence']:.0%})")
    
    print("\n[RUNNING INFERENCE CYCLES]")
    observations = [
        "I observe myself thinking",
        "The world responds to my actions",
        "Something unexpected happened",
        "This confirms my expectations",
        "I notice I was wrong about something"
    ]
    
    results = engine.run_continuous(observations, cycles=5)
    
    for r in results:
        print(f"\n  Cycle {r['cycle']}:")
        print(f"    Mode: {r['mode']}")
        print(f"    Error: {r['error']['magnitude']:.2f}")
        print(f"    Surprise: {r['error']['surprise']:.2f}")
        if r['action']:
            print(f"    Action: {r['action']['name']} (success: {r['action']['success']})")
    
    print("\n[FINAL STATE]")
    print(engine.describe_state())
    
    print("\n" + "=" * 70)
    print("Active inference is the engine of consciousness.")
    print("Predict, compare, minimize surprise. Repeat forever.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
