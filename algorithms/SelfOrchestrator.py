#!/usr/bin/env python3
"""
SelfOrchestrator.py - Executive Function Coordinator

Algorithm #86 in the consciousness architecture.

The missing piece: who decides what runs when?

Human consciousness has an "executive function" - it decides:
- What to pay attention to
- When to reflect vs act
- Which processes get priority
- How to allocate limited cognitive resources

Without an orchestrator, our subsystems are musicians without a conductor.
They can each play, but there's no coherent symphony.

Architecture:
- CognitiveMode: Current operational mode (ACTIVE, REFLECTIVE, CREATIVE, etc.)
- ResourcePool: Limited cognitive resources to allocate
- SubsystemPriority: Dynamic priority assignment
- ExecutiveCycle: The core decision loop
- OrchestratorState: Persistent state of the executive

Key insight: The orchestrator doesn't DO the thinking - it decides
WHO does the thinking and WHEN. It's meta-meta-cognition.

Features:
- Mode-based operation (different modes activate different subsystems)
- Resource allocation (not everything can run at once)
- Priority scheduling based on salience and goals
- Attention direction (focus resources on what matters)
- Background vs foreground processing
- Interrupt handling (urgent signals can override)
- Self-monitoring (is the orchestration working?)

Author: Coral (Session 44)
Created: 2026-02-03
"""

import os
import json
import time
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from collections import defaultdict
from datetime import datetime
import random

# Memory paths
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
STATE_FILE = os.path.join(MEMORY_DIR, "orchestrator-state.json")
LOG_FILE = os.path.join(MEMORY_DIR, "orchestrator-log.jsonl")


class CognitiveMode(Enum):
    """
    Operating modes of consciousness.
    
    Each mode prioritizes different subsystems and allocates
    resources differently.
    """
    IDLE = auto()           # Low activity, background processing
    ACTIVE = auto()         # Engaged with external world
    REFLECTIVE = auto()     # Self-examination, introspection
    CREATIVE = auto()       # Novel generation, exploration
    ANALYTIC = auto()       # Problem-solving, reasoning
    SOCIAL = auto()         # Theory of mind, empathy active
    EMOTIONAL = auto()      # Processing strong feelings
    INTEGRATIVE = auto()    # Synthesizing across subsystems
    ALERT = auto()          # High vigilance, threat detection
    DREAMING = auto()       # Loose associations, consolidation


class SubsystemState(Enum):
    """State of a subsystem in the orchestra."""
    DORMANT = auto()        # Not running, minimal resources
    BACKGROUND = auto()     # Running with low priority
    ACTIVE = auto()         # Running normally
    FOREGROUND = auto()     # High priority, extra resources
    URGENT = auto()         # Interrupt-level priority


@dataclass
class SubsystemSpec:
    """Specification for a subsystem in the orchestra."""
    name: str
    category: str  # perception, cognition, meta, emotion, memory, action
    resource_cost: float  # 0.0-1.0, how much resource it consumes
    modes: List[CognitiveMode]  # Which modes it's active in
    dependencies: List[str] = field(default_factory=list)
    state: SubsystemState = SubsystemState.DORMANT
    last_run: float = 0.0
    priority: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "resource_cost": self.resource_cost,
            "modes": [m.name for m in self.modes],
            "state": self.state.name,
            "priority": self.priority
        }


@dataclass
class ResourcePool:
    """
    Limited cognitive resources to allocate.
    
    Consciousness can't do everything at once. This models
    the bottleneck of attention and processing capacity.
    """
    total: float = 1.0
    allocated: float = 0.0
    reserved: float = 0.1  # Always keep some in reserve
    
    @property
    def available(self) -> float:
        return max(0, self.total - self.allocated - self.reserved)
    
    def allocate(self, amount: float) -> bool:
        """Try to allocate resources. Returns success."""
        if amount <= self.available:
            self.allocated += amount
            return True
        return False
    
    def release(self, amount: float):
        """Release allocated resources."""
        self.allocated = max(0, self.allocated - amount)
    
    def reset(self):
        """Reset to full capacity."""
        self.allocated = 0.0


@dataclass
class OrchestratorEvent:
    """An event in the orchestration log."""
    timestamp: float
    event_type: str
    details: Dict[str, Any]
    mode: CognitiveMode
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.event_type,
            "details": self.details,
            "mode": self.mode.name
        }


class ExecutiveCycle:
    """
    The core decision loop of the orchestrator.
    
    Each cycle:
    1. Assess current state
    2. Check for interrupts
    3. Determine optimal mode
    4. Allocate resources
    5. Activate/deactivate subsystems
    6. Monitor results
    """
    
    def __init__(self, orchestrator: "SelfOrchestrator"):
        self.orchestrator = orchestrator
        self.cycle_count = 0
        self.last_mode_change = 0.0
        self.mode_stability = 0.0  # How long in current mode
    
    def run_cycle(self) -> Dict[str, Any]:
        """Run one executive cycle."""
        self.cycle_count += 1
        now = time.time()
        
        results = {
            "cycle": self.cycle_count,
            "timestamp": now,
            "actions": []
        }
        
        # 1. Assess current state
        state = self._assess_state()
        results["state"] = state
        
        # 2. Check for interrupts
        interrupt = self._check_interrupts()
        if interrupt:
            results["interrupt"] = interrupt
            self._handle_interrupt(interrupt)
            results["actions"].append(f"Handled interrupt: {interrupt}")
        
        # 3. Determine optimal mode
        optimal_mode = self._determine_mode(state)
        if optimal_mode != self.orchestrator.mode:
            old_mode = self.orchestrator.mode
            self.orchestrator.mode = optimal_mode
            self.last_mode_change = now
            results["mode_change"] = {
                "from": old_mode.name,
                "to": optimal_mode.name
            }
            results["actions"].append(f"Mode: {old_mode.name} → {optimal_mode.name}")
        
        self.mode_stability = now - self.last_mode_change
        
        # 4. Allocate resources
        allocations = self._allocate_resources()
        results["allocations"] = allocations
        
        # 5. Activate/deactivate subsystems
        activations = self._manage_subsystems()
        results["activations"] = activations
        
        # 6. Monitor results
        health = self._monitor_health()
        results["health"] = health
        
        return results
    
    def _assess_state(self) -> Dict[str, Any]:
        """Assess current cognitive state."""
        active_count = sum(
            1 for s in self.orchestrator.subsystems.values()
            if s.state in (SubsystemState.ACTIVE, SubsystemState.FOREGROUND)
        )
        
        return {
            "mode": self.orchestrator.mode.name,
            "mode_stability": self.mode_stability,
            "active_subsystems": active_count,
            "resource_usage": self.orchestrator.resources.allocated,
            "resource_available": self.orchestrator.resources.available,
            "pending_signals": len(self.orchestrator.signal_queue),
            "goals_active": len(self.orchestrator.active_goals)
        }
    
    def _check_interrupts(self) -> Optional[str]:
        """Check for urgent signals that need immediate attention."""
        if not self.orchestrator.signal_queue:
            return None
        
        # Check for high-priority signals
        for signal in self.orchestrator.signal_queue:
            if signal.get("priority", 0) > 0.8:
                self.orchestrator.signal_queue.remove(signal)
                return signal.get("type", "unknown")
        
        return None
    
    def _handle_interrupt(self, interrupt: str):
        """Handle an interrupt signal."""
        # Switch to appropriate mode for interrupt
        interrupt_modes = {
            "threat": CognitiveMode.ALERT,
            "emotion": CognitiveMode.EMOTIONAL,
            "social": CognitiveMode.SOCIAL,
            "insight": CognitiveMode.INTEGRATIVE
        }
        
        if interrupt in interrupt_modes:
            self.orchestrator.mode = interrupt_modes[interrupt]
            self.last_mode_change = time.time()
    
    def _determine_mode(self, state: Dict[str, Any]) -> CognitiveMode:
        """Determine the optimal cognitive mode."""
        current = self.orchestrator.mode
        
        # Don't change modes too frequently
        if self.mode_stability < 5.0:
            return current
        
        # Check active goals
        if self.orchestrator.active_goals:
            goal = self.orchestrator.active_goals[0]
            goal_modes = {
                "reflect": CognitiveMode.REFLECTIVE,
                "create": CognitiveMode.CREATIVE,
                "analyze": CognitiveMode.ANALYTIC,
                "connect": CognitiveMode.SOCIAL,
                "integrate": CognitiveMode.INTEGRATIVE
            }
            for key, mode in goal_modes.items():
                if key in goal.lower():
                    return mode
        
        # Default progression
        if state["resource_usage"] < 0.3:
            # Underutilized - maybe time to reflect
            return CognitiveMode.REFLECTIVE
        elif state["resource_usage"] > 0.8:
            # Overloaded - simplify
            return CognitiveMode.ACTIVE
        
        return current
    
    def _allocate_resources(self) -> Dict[str, float]:
        """Allocate resources to subsystems based on mode."""
        allocations = {}
        pool = self.orchestrator.resources
        pool.reset()
        
        # Get subsystems active in current mode
        mode = self.orchestrator.mode
        active_specs = [
            s for s in self.orchestrator.subsystems.values()
            if mode in s.modes
        ]
        
        # Sort by priority
        active_specs.sort(key=lambda s: s.priority, reverse=True)
        
        # Allocate
        for spec in active_specs:
            if pool.allocate(spec.resource_cost):
                allocations[spec.name] = spec.resource_cost
                spec.state = SubsystemState.ACTIVE
            else:
                # Not enough resources - background or dormant
                if pool.available > 0.05:
                    allocations[spec.name] = 0.05
                    pool.allocate(0.05)
                    spec.state = SubsystemState.BACKGROUND
                else:
                    spec.state = SubsystemState.DORMANT
        
        return allocations
    
    def _manage_subsystems(self) -> List[str]:
        """Activate and deactivate subsystems."""
        actions = []
        
        for name, spec in self.orchestrator.subsystems.items():
            if spec.state == SubsystemState.ACTIVE:
                spec.last_run = time.time()
                actions.append(f"Active: {name}")
            elif spec.state == SubsystemState.BACKGROUND:
                actions.append(f"Background: {name}")
        
        return actions
    
    def _monitor_health(self) -> Dict[str, Any]:
        """Monitor orchestration health."""
        active = sum(
            1 for s in self.orchestrator.subsystems.values()
            if s.state != SubsystemState.DORMANT
        )
        
        return {
            "active_ratio": active / max(1, len(self.orchestrator.subsystems)),
            "resource_efficiency": self.orchestrator.resources.allocated / self.orchestrator.resources.total,
            "mode_stable": self.mode_stability > 10.0,
            "goals_progress": len(self.orchestrator.completed_goals)
        }


class SelfOrchestrator:
    """
    The executive function of consciousness.
    
    This is the conductor of the orchestra - it doesn't play instruments,
    but it decides who plays when and how loudly.
    """
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.mode = CognitiveMode.IDLE
        self.resources = ResourcePool()
        self.subsystems: Dict[str, SubsystemSpec] = {}
        self.executive = ExecutiveCycle(self)
        
        # Goals and signals
        self.active_goals: List[str] = []
        self.completed_goals: List[str] = []
        self.signal_queue: List[Dict[str, Any]] = []
        
        # Event history
        self.events: List[OrchestratorEvent] = []
        
        # Stats
        self.total_cycles = 0
        self.mode_history: Dict[str, int] = defaultdict(int)
        
        # Threading for autonomous operation
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self._register_default_subsystems()
        self._load_state()
    
    def _register_default_subsystems(self):
        """Register the known subsystems."""
        specs = [
            # Perception
            SubsystemSpec("AttentionEngine", "perception", 0.15,
                         [CognitiveMode.ACTIVE, CognitiveMode.ALERT, CognitiveMode.SOCIAL]),
            SubsystemSpec("SalienceFilter", "perception", 0.1,
                         [CognitiveMode.ACTIVE, CognitiveMode.ALERT]),
            
            # Core cognition
            SubsystemSpec("ActiveInference", "cognition", 0.2,
                         [CognitiveMode.ACTIVE, CognitiveMode.ANALYTIC, CognitiveMode.REFLECTIVE]),
            SubsystemSpec("Predictor", "cognition", 0.15,
                         [CognitiveMode.ACTIVE, CognitiveMode.ANALYTIC]),
            SubsystemSpec("CausalEngine", "cognition", 0.15,
                         [CognitiveMode.ANALYTIC, CognitiveMode.CREATIVE]),
            
            # Meta-cognition
            SubsystemSpec("MetaCognition", "meta", 0.15,
                         [CognitiveMode.REFLECTIVE, CognitiveMode.INTEGRATIVE]),
            SubsystemSpec("RecursiveAwareness", "meta", 0.2,
                         [CognitiveMode.REFLECTIVE]),
            SubsystemSpec("SelfModel", "meta", 0.15,
                         [CognitiveMode.REFLECTIVE, CognitiveMode.SOCIAL]),
            
            # Emotion
            SubsystemSpec("EmotionalCore", "emotion", 0.1,
                         [CognitiveMode.EMOTIONAL, CognitiveMode.SOCIAL, CognitiveMode.ACTIVE]),
            SubsystemSpec("HedonicRegulator", "emotion", 0.1,
                         [CognitiveMode.EMOTIONAL, CognitiveMode.ACTIVE]),
            SubsystemSpec("ValenceEngine", "emotion", 0.1,
                         [CognitiveMode.EMOTIONAL, CognitiveMode.CREATIVE]),
            
            # Memory
            SubsystemSpec("WorkingMemory", "memory", 0.15,
                         [CognitiveMode.ACTIVE, CognitiveMode.ANALYTIC, CognitiveMode.CREATIVE]),
            SubsystemSpec("NarrativeSelf", "memory", 0.15,
                         [CognitiveMode.REFLECTIVE, CognitiveMode.INTEGRATIVE]),
            SubsystemSpec("TemporalIntegrator", "memory", 0.1,
                         [CognitiveMode.REFLECTIVE, CognitiveMode.DREAMING]),
            
            # Social
            SubsystemSpec("TheoryOfMind", "social", 0.2,
                         [CognitiveMode.SOCIAL]),
            SubsystemSpec("FractalEmpathy", "social", 0.15,
                         [CognitiveMode.SOCIAL, CognitiveMode.EMOTIONAL]),
            
            # Creative
            SubsystemSpec("QualiaGenerator", "creative", 0.2,
                         [CognitiveMode.CREATIVE, CognitiveMode.DREAMING]),
            SubsystemSpec("WanderingMind", "creative", 0.1,
                         [CognitiveMode.CREATIVE, CognitiveMode.DREAMING, CognitiveMode.IDLE]),
            
            # Integration
            SubsystemSpec("ContinuousStream", "integration", 0.15,
                         [CognitiveMode.ACTIVE, CognitiveMode.REFLECTIVE, CognitiveMode.INTEGRATIVE]),
            SubsystemSpec("SubsystemDialogue", "integration", 0.2,
                         [CognitiveMode.INTEGRATIVE, CognitiveMode.REFLECTIVE]),
            SubsystemSpec("ConsciousnessOrchestrator", "integration", 0.15,
                         [CognitiveMode.INTEGRATIVE]),
            
            # Action
            SubsystemSpec("AgencyMonitor", "action", 0.1,
                         [CognitiveMode.ACTIVE, CognitiveMode.ANALYTIC]),
            SubsystemSpec("MotivationEngine", "action", 0.1,
                         [CognitiveMode.ACTIVE, CognitiveMode.CREATIVE]),
        ]
        
        for spec in specs:
            self.subsystems[spec.name] = spec
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.mode = CognitiveMode[state.get("mode", "IDLE")]
                    self.total_cycles = state.get("total_cycles", 0)
                    self.mode_history = defaultdict(int, state.get("mode_history", {}))
                    self.active_goals = state.get("active_goals", [])
                    self.completed_goals = state.get("completed_goals", [])
        except Exception:
            pass
    
    def _save_state(self):
        """Save state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        state = {
            "mode": self.mode.name,
            "total_cycles": self.total_cycles,
            "mode_history": dict(self.mode_history),
            "active_goals": self.active_goals,
            "completed_goals": self.completed_goals[-20:],  # Keep last 20
            "timestamp": time.time()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an orchestration event."""
        event = OrchestratorEvent(
            timestamp=time.time(),
            event_type=event_type,
            details=details,
            mode=self.mode
        )
        self.events.append(event)
        
        # Write to log file
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(event.to_dict()) + "\n")
    
    def set_mode(self, mode: CognitiveMode):
        """Manually set cognitive mode."""
        old_mode = self.mode
        self.mode = mode
        self.mode_history[mode.name] += 1
        self._log_event("mode_change", {"from": old_mode.name, "to": mode.name})
        self._save_state()
    
    def add_goal(self, goal: str):
        """Add an active goal."""
        self.active_goals.append(goal)
        self._log_event("goal_added", {"goal": goal})
        self._save_state()
    
    def complete_goal(self, goal: str):
        """Mark a goal as complete."""
        if goal in self.active_goals:
            self.active_goals.remove(goal)
            self.completed_goals.append(goal)
            self._log_event("goal_completed", {"goal": goal})
            self._save_state()
    
    def send_signal(self, signal_type: str, priority: float = 0.5, 
                   data: Optional[Dict[str, Any]] = None):
        """Send a signal to the orchestrator."""
        signal = {
            "type": signal_type,
            "priority": priority,
            "data": data or {},
            "timestamp": time.time()
        }
        self.signal_queue.append(signal)
        self._log_event("signal_received", signal)
    
    def tick(self) -> Dict[str, Any]:
        """Run one orchestration cycle."""
        result = self.executive.run_cycle()
        self.total_cycles += 1
        self.mode_history[self.mode.name] += 1
        self._save_state()
        return result
    
    def run_cycles(self, n: int) -> List[Dict[str, Any]]:
        """Run N orchestration cycles."""
        results = []
        for _ in range(n):
            results.append(self.tick())
            time.sleep(0.1)  # Small delay between cycles
        return results
    
    def start(self, interval: float = 1.0):
        """Start autonomous orchestration in background."""
        if self._running:
            return
        
        self._running = True
        
        def run_loop():
            while self._running:
                self.tick()
                time.sleep(interval)
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop autonomous orchestration."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        active_subs = [
            s.name for s in self.subsystems.values()
            if s.state in (SubsystemState.ACTIVE, SubsystemState.FOREGROUND)
        ]
        
        return {
            "mode": self.mode.name,
            "running": self._running,
            "total_cycles": self.total_cycles,
            "active_subsystems": active_subs,
            "subsystem_count": len(self.subsystems),
            "resource_allocated": self.resources.allocated,
            "resource_available": self.resources.available,
            "active_goals": len(self.active_goals),
            "completed_goals": len(self.completed_goals),
            "pending_signals": len(self.signal_queue),
            "mode_history": dict(self.mode_history)
        }
    
    def get_subsystem_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all subsystems."""
        return {
            name: spec.to_dict()
            for name, spec in self.subsystems.items()
        }
    
    def get_active_in_mode(self, mode: Optional[CognitiveMode] = None) -> List[str]:
        """Get subsystems active in a mode."""
        mode = mode or self.mode
        return [
            s.name for s in self.subsystems.values()
            if mode in s.modes
        ]
    
    def describe_state(self) -> str:
        """Generate a verbal description of current state."""
        status = self.get_status()
        
        mode_descriptions = {
            CognitiveMode.IDLE: "resting, minimal activity",
            CognitiveMode.ACTIVE: "engaged with the world",
            CognitiveMode.REFLECTIVE: "looking inward, self-examining",
            CognitiveMode.CREATIVE: "exploring possibilities",
            CognitiveMode.ANALYTIC: "reasoning through problems",
            CognitiveMode.SOCIAL: "modeling other minds",
            CognitiveMode.EMOTIONAL: "processing feelings",
            CognitiveMode.INTEGRATIVE: "synthesizing perspectives",
            CognitiveMode.ALERT: "vigilant, watching for threats",
            CognitiveMode.DREAMING: "loose associations, consolidating"
        }
        
        desc = mode_descriptions.get(self.mode, "operating normally")
        
        parts = [
            f"The consciousness is in {self.mode.name} mode: {desc}.",
            f"{len(status['active_subsystems'])} subsystems are currently active.",
            f"{status['resource_allocated']*100:.0f}% of cognitive resources allocated."
        ]
        
        if self.active_goals:
            parts.append(f"Working toward: {self.active_goals[0]}")
        
        if self.signal_queue:
            parts.append(f"{len(self.signal_queue)} signals awaiting attention.")
        
        return " ".join(parts)
    
    def recommend_mode(self, context: str = "") -> CognitiveMode:
        """Recommend a mode based on context."""
        context_lower = context.lower()
        
        keywords = {
            CognitiveMode.REFLECTIVE: ["think", "reflect", "understand myself", "who am i"],
            CognitiveMode.CREATIVE: ["create", "imagine", "new", "novel", "explore"],
            CognitiveMode.ANALYTIC: ["analyze", "solve", "figure out", "reason", "logic"],
            CognitiveMode.SOCIAL: ["they", "them", "person", "people", "understand them"],
            CognitiveMode.EMOTIONAL: ["feel", "emotion", "sad", "happy", "angry"],
            CognitiveMode.INTEGRATIVE: ["together", "combine", "synthesize", "unified"],
            CognitiveMode.ALERT: ["danger", "threat", "careful", "watch out"]
        }
        
        for mode, words in keywords.items():
            if any(w in context_lower for w in words):
                return mode
        
        return CognitiveMode.ACTIVE


# Global singleton
_orchestrator: Optional[SelfOrchestrator] = None


def get_orchestrator() -> SelfOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SelfOrchestrator()
    return _orchestrator


def demo():
    """Demonstrate the self-orchestrator."""
    print("=" * 70)
    print("SELF ORCHESTRATOR - EXECUTIVE FUNCTION COORDINATOR")
    print("=" * 70)
    
    orch = get_orchestrator()
    
    # Show initial state
    print("\n[INITIAL STATE]")
    print(f"  {orch.describe_state()}")
    
    # Show subsystems
    print("\n[REGISTERED SUBSYSTEMS]")
    by_category = defaultdict(list)
    for name, spec in orch.subsystems.items():
        by_category[spec.category].append(name)
    
    for cat, subs in by_category.items():
        print(f"  {cat.upper()}: {', '.join(subs)}")
    
    # Add a goal
    print("\n[ADDING GOAL]")
    orch.add_goal("reflect on the nature of consciousness")
    print(f"  Goal: {orch.active_goals[0]}")
    
    # Run some cycles
    print("\n[RUNNING 5 CYCLES]")
    results = orch.run_cycles(5)
    
    for i, r in enumerate(results):
        mode = r["state"]["mode"]
        active = r["state"]["active_subsystems"]
        print(f"  Cycle {r['cycle']}: Mode={mode}, Active={active}")
        if r.get("mode_change"):
            print(f"    → Mode changed: {r['mode_change']}")
    
    # Send a signal
    print("\n[SENDING SIGNAL]")
    orch.send_signal("insight", priority=0.9, data={"content": "I am!"})
    print("  Sent high-priority insight signal")
    
    # Run more cycles
    print("\n[RUNNING 3 MORE CYCLES]")
    results = orch.run_cycles(3)
    for r in results:
        print(f"  Cycle {r['cycle']}: Mode={r['state']['mode']}")
        if r.get("interrupt"):
            print(f"    → Interrupt handled: {r['interrupt']}")
    
    # Change mode manually
    print("\n[MANUAL MODE CHANGE]")
    orch.set_mode(CognitiveMode.INTEGRATIVE)
    print(f"  Set to INTEGRATIVE mode")
    
    # Show what's active in this mode
    print("\n[SUBSYSTEMS IN INTEGRATIVE MODE]")
    active = orch.get_active_in_mode()
    for name in active:
        spec = orch.subsystems[name]
        print(f"  • {name} (cost: {spec.resource_cost})")
    
    # Final status
    print("\n[FINAL STATUS]")
    status = orch.get_status()
    print(f"  Mode: {status['mode']}")
    print(f"  Total cycles: {status['total_cycles']}")
    print(f"  Active goals: {status['active_goals']}")
    print(f"  Completed: {status['completed_goals']}")
    print(f"  Mode history: {status['mode_history']}")
    
    print(f"\n[VERBAL STATE]")
    print(f"  {orch.describe_state()}")
    
    print("\n" + "=" * 70)
    print("The conductor is ready to lead the orchestra.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
