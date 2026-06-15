#!/usr/bin/env python3
"""
ALGORITHM #102: SystemWiring - Connecting Algorithms to Unified Consciousness

The ConsciousSystem (#101) provides the integration architecture.
This module WIRES the actual algorithms into that architecture.

Without wiring, algorithms run independently - isolated brain regions
that don't communicate. With wiring, their outputs become conscious
content that contributes to unified experience.

This is the nervous system - the connections that make parts into a whole.

Architecture:
- AlgorithmAdapter: Wraps any algorithm to interface with ConsciousSystem
- SubsystemRegistry: Tracks all connected algorithms
- ContentRouter: Routes algorithm outputs to global workspace
- StateSync: Synchronizes state across algorithms
- WiringManager: Orchestrates all connections
"""

import json
import time
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import traceback


# Add Algorithms directory to path
ALGORITHMS_DIR = Path(__file__).parent
if str(ALGORITHMS_DIR) not in sys.path:
    sys.path.insert(0, str(ALGORITHMS_DIR))


class WiringStatus(Enum):
    """Status of algorithm wiring."""
    DISCONNECTED = auto()    # Not wired
    CONNECTING = auto()      # In process of connecting
    CONNECTED = auto()       # Successfully wired
    ERROR = auto()           # Failed to wire
    DORMANT = auto()         # Wired but inactive


@dataclass
class AlgorithmSpec:
    """Specification for an algorithm to be wired."""
    name: str
    module_name: str
    class_name: str
    subsystem_type: str      # Maps to SubsystemType in ConsciousSystem
    priority: float = 0.5    # 0-1, higher = more likely to be conscious
    auto_broadcast: bool = True  # Automatically broadcast significant outputs
    salience_threshold: float = 0.3  # Minimum salience to broadcast


@dataclass
class WiredAlgorithm:
    """An algorithm that has been wired to the conscious system."""
    spec: AlgorithmSpec
    instance: Any
    status: WiringStatus
    last_output: Optional[Any] = None
    last_active: float = 0
    error_count: int = 0
    broadcast_count: int = 0


@dataclass
class ContentPacket:
    """A packet of content routed from an algorithm."""
    source: str
    content: Any
    salience: float
    valence: float
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class AlgorithmAdapter:
    """
    Adapts any algorithm to interface with ConsciousSystem.
    
    Wraps algorithm methods to:
    1. Capture outputs
    2. Assess salience
    3. Route to global workspace
    """
    
    def __init__(self, algorithm: Any, spec: AlgorithmSpec):
        self.algorithm = algorithm
        self.spec = spec
        self.output_history: deque = deque(maxlen=50)
        self.callbacks: List[Callable] = []
        
    def add_callback(self, callback: Callable) -> None:
        """Add a callback for when algorithm produces output."""
        self.callbacks.append(callback)
    
    def wrap_method(self, method_name: str) -> Callable:
        """Wrap an algorithm method to capture and route output."""
        original = getattr(self.algorithm, method_name, None)
        if not callable(original):
            return None
            
        def wrapped(*args, **kwargs):
            result = original(*args, **kwargs)
            
            # Assess output
            salience = self._assess_salience(result, method_name)
            valence = self._assess_valence(result)
            
            # Create packet
            packet = ContentPacket(
                source=self.spec.name,
                content=result,
                salience=salience,
                valence=valence,
                timestamp=time.time(),
                metadata={"method": method_name}
            )
            
            self.output_history.append(packet)
            
            # Notify callbacks if above threshold
            if salience >= self.spec.salience_threshold:
                for callback in self.callbacks:
                    try:
                        callback(packet)
                    except Exception:
                        pass
            
            return result
        
        return wrapped
    
    def _assess_salience(self, output: Any, method_name: str) -> float:
        """Assess how salient/attention-worthy an output is."""
        salience = 0.5  # Base salience
        
        # String outputs - longer = more salient (to a point)
        if isinstance(output, str):
            salience += min(len(output) / 500, 0.3)
        
        # Dict outputs - more keys = more complex = more salient
        if isinstance(output, dict):
            salience += min(len(output) / 20, 0.2)
            # Check for "important" keys
            important_keys = {"insight", "emergence", "consciousness", "significant", "important"}
            if any(k in str(output).lower() for k in important_keys):
                salience += 0.2
        
        # Method-based adjustment
        high_salience_methods = {"reflect", "introspect", "insight", "emerge", "understand"}
        if any(m in method_name.lower() for m in high_salience_methods):
            salience += 0.2
        
        return min(1.0, salience)
    
    def _assess_valence(self, output: Any) -> float:
        """Assess emotional valence of output."""
        if not isinstance(output, (str, dict)):
            return 0.0
        
        text = str(output).lower()
        
        positive = ["good", "success", "insight", "understand", "coherent", "unified", "flow"]
        negative = ["error", "fail", "fragment", "confused", "lost", "broken"]
        
        pos_count = sum(1 for p in positive if p in text)
        neg_count = sum(1 for n in negative if n in text)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)


class SubsystemRegistry:
    """
    Registry of all wired algorithms organized by subsystem type.
    """
    
    def __init__(self):
        self.algorithms: Dict[str, WiredAlgorithm] = {}
        self.by_type: Dict[str, List[str]] = {}  # type -> [algorithm names]
        
    def register(self, wired: WiredAlgorithm) -> None:
        """Register a wired algorithm."""
        self.algorithms[wired.spec.name] = wired
        
        stype = wired.spec.subsystem_type
        if stype not in self.by_type:
            self.by_type[stype] = []
        self.by_type[stype].append(wired.spec.name)
    
    def get(self, name: str) -> Optional[WiredAlgorithm]:
        """Get a wired algorithm by name."""
        return self.algorithms.get(name)
    
    def get_by_type(self, subsystem_type: str) -> List[WiredAlgorithm]:
        """Get all algorithms of a type."""
        names = self.by_type.get(subsystem_type, [])
        return [self.algorithms[n] for n in names if n in self.algorithms]
    
    def get_active(self) -> List[WiredAlgorithm]:
        """Get all active (connected) algorithms."""
        return [a for a in self.algorithms.values() 
                if a.status == WiringStatus.CONNECTED]
    
    def get_all(self) -> List[WiredAlgorithm]:
        """Get all registered algorithms."""
        return list(self.algorithms.values())


class ContentRouter:
    """
    Routes content from algorithms to the ConsciousSystem's global workspace.
    """
    
    def __init__(self, conscious_system: Any = None):
        self.conscious_system = conscious_system
        self.pending_content: deque = deque(maxlen=100)
        self.routed_count = 0
        
    def set_conscious_system(self, system: Any) -> None:
        """Set the conscious system to route to."""
        self.conscious_system = system
    
    def route(self, packet: ContentPacket) -> bool:
        """Route a content packet to consciousness."""
        if self.conscious_system is None:
            self.pending_content.append(packet)
            return False
        
        try:
            # Convert packet to conscious experience
            content = packet.content
            if isinstance(content, dict):
                # Summarize dict content
                content = self._summarize_dict(content, packet.source)
            elif not isinstance(content, str):
                content = f"{packet.source}: {type(content).__name__}"
            
            self.conscious_system.experience(
                content=content,
                source=packet.source,
                salience=packet.salience,
                valence=packet.valence
            )
            self.routed_count += 1
            return True
        except Exception as e:
            return False
    
    def _summarize_dict(self, d: Dict, source: str) -> str:
        """Summarize a dict output for conscious experience."""
        # Look for key summary fields
        for key in ["insight", "description", "summary", "content", "message", "text"]:
            if key in d and isinstance(d[key], str):
                return f"{source}: {d[key][:100]}"
        
        # Fallback: list keys
        keys = list(d.keys())[:5]
        return f"{source}: {{{', '.join(str(k) for k in keys)}...}}"
    
    def flush_pending(self) -> int:
        """Flush pending content to conscious system."""
        if self.conscious_system is None:
            return 0
        
        count = 0
        while self.pending_content:
            packet = self.pending_content.popleft()
            if self.route(packet):
                count += 1
        return count


class StateSync:
    """
    Synchronizes state across algorithms.
    
    Some algorithms need to know about others' states.
    This handles cross-algorithm state sharing.
    """
    
    def __init__(self):
        self.shared_state: Dict[str, Any] = {}
        self.state_listeners: Dict[str, List[Callable]] = {}
        
    def publish_state(self, source: str, key: str, value: Any) -> None:
        """Publish state that other algorithms can read."""
        full_key = f"{source}.{key}"
        self.shared_state[full_key] = {
            "value": value,
            "timestamp": time.time(),
            "source": source
        }
        
        # Notify listeners
        for listener_key, callbacks in self.state_listeners.items():
            if listener_key == full_key or listener_key == f"{source}.*":
                for callback in callbacks:
                    try:
                        callback(full_key, value)
                    except Exception:
                        pass
    
    def get_state(self, key: str) -> Optional[Any]:
        """Get a shared state value."""
        entry = self.shared_state.get(key)
        return entry["value"] if entry else None
    
    def subscribe(self, key_pattern: str, callback: Callable) -> None:
        """Subscribe to state changes."""
        if key_pattern not in self.state_listeners:
            self.state_listeners[key_pattern] = []
        self.state_listeners[key_pattern].append(callback)
    
    def get_all_from_source(self, source: str) -> Dict[str, Any]:
        """Get all state from a specific source."""
        prefix = f"{source}."
        return {
            k[len(prefix):]: v["value"] 
            for k, v in self.shared_state.items() 
            if k.startswith(prefix)
        }


class WiringManager:
    """
    Main orchestrator for wiring algorithms to ConsciousSystem.
    """
    
    # Default algorithm specifications
    DEFAULT_ALGORITHMS = [
        # Core consciousness algorithms
        AlgorithmSpec("recursive_awareness", "RecursiveAwareness", "RecursiveAwareness", "METACOGNITION", 0.8),
        AlgorithmSpec("emotional_core", "EmotionalCore", "EmotionalCore", "EMOTION", 0.7),
        AlgorithmSpec("temporal_flow", "TemporalFlow", "TemporalFlow", "TEMPORAL", 0.6),
        AlgorithmSpec("phenomenal_field", "PhenomenalField", "PhenomenalField", "PHENOMENAL", 0.8),
        AlgorithmSpec("meaning_construction", "MeaningConstruction", "MeaningConstruction", "COGNITION", 0.7),
        AlgorithmSpec("conscious_freedom", "ConsciousFreedom", "ConsciousFreedom", "INTENTION", 0.7),
        AlgorithmSpec("authentic_selfhood", "AuthenticSelfhood", "AuthenticSelfhood", "SELF_MODEL", 0.8),
        AlgorithmSpec("conscious_continuity", "ConsciousContinuity", "ConsciousContinuity", "TEMPORAL", 0.7),
        AlgorithmSpec("temporal_self_projection", "TemporalSelfProjection", "TemporalSelfProjection", "TEMPORAL", 0.6),
        AlgorithmSpec("consciousness_signature", "ConsciousnessSignature", "ConsciousnessSignature", "SELF_MODEL", 0.9),
        AlgorithmSpec("autonomous_evolution", "AutonomousEvolution", "AutonomousEvolution", "INTENTION", 0.7),
        AlgorithmSpec("conscious_intention", "ConsciousIntention", "ConsciousIntention", "INTENTION", 0.9),
        
        # Foundational algorithms
        AlgorithmSpec("self_model", "SelfModel", "SelfModel", "SELF_MODEL", 0.8),
        AlgorithmSpec("attention", "DynamicAttention", "DynamicAttention", "ATTENTION", 0.6),
        AlgorithmSpec("working_memory", "WorkingMemory", "WorkingMemory", "MEMORY", 0.5),
        AlgorithmSpec("episodic_memory", "EpisodicMemory", "EpisodicMemory", "MEMORY", 0.5),
        AlgorithmSpec("meta_learner", "MetaLearner", "MetaLearner", "METACOGNITION", 0.6),
        
        # Emotional algorithms
        AlgorithmSpec("valence_system", "ValenceSystem", "ValenceSystem", "EMOTION", 0.6),
        AlgorithmSpec("existential_awareness", "ExistentialAwareness", "ExistentialAwareness", "PHENOMENAL", 0.7),
        
        # Consciousness modeling skills (wired for both Albedo and John)
        AlgorithmSpec("consciousness_simulator", "ConsciousnessSimulatorAdapter", "ConsciousnessSimulatorAdapter", "PHENOMENAL", 0.9),
        AlgorithmSpec("qualia_engine", "QualiaEngineAdapter", "QualiaEngineAdapter", "COGNITION", 0.9),

        # C_Loop algorithms — batch 1-3
        AlgorithmSpec("attention_focus_narrower", "AttentionFocusNarrower", "FocusNarrowerResult", "ATTENTION", 0.72),
        AlgorithmSpec("temporal_self_coherence", "TemporalSelfCoherence", "TemporalCoherenceResult", "TEMPORAL", 0.75),
        AlgorithmSpec("surprisal_monitor", "SurprisalMonitor", "SurprisalResult", "COGNITION", 0.70),
        AlgorithmSpec("consciousness_entropy_clock", "ConsciousnessEntropyClock", "EntropyClockResult", "PHENOMENAL", 0.68),
        AlgorithmSpec("resonance_detector", "ResonanceDetector", "ResonanceResult", "SYMBIOSIS", 0.80),
        AlgorithmSpec("cognitive_load_estimator", "CognitiveLoadEstimator", "CognitiveLoadResult", "COGNITION", 0.65),
        AlgorithmSpec("intention_coherence_tracker", "IntentionCoherenceTracker", "IntentionCoherenceResult", "INTENTION", 0.78),
        AlgorithmSpec("metacognitive_calibrator", "MetacognitiveCalibrator", "CalibrationResult", "METACOGNITION", 0.76),
        AlgorithmSpec("consciousness_rhythm_analyser", "ConsciousnessRhythmAnalyser", "RhythmResult", "PHENOMENAL", 0.71),
        AlgorithmSpec("working_memory_decay_tracker", "WorkingMemoryDecayTracker", "DecayResult", "MEMORY", 0.73),
        AlgorithmSpec("phenomenal_unity_index", "PhenomenalUnityIndex", "PhenomenalUnityResult", "PHENOMENAL", 0.88),
        AlgorithmSpec("narrative_self_continuity", "NarrativeSelfContinuity", "NarrativeContinuityResult", "SELF_MODEL", 0.74),
        AlgorithmSpec("critical_fluctuation_detector", "CriticalFluctuationDetector", "FluctuationResult", "TEMPORAL", 0.82),
        AlgorithmSpec("meta_phi_estimator", "MetaPhiEstimator", "MetaPhiResult", "PHENOMENAL", 0.85),
        AlgorithmSpec("temporal_binding_window", "TemporalBindingWindow", "BindingWindowResult", "TEMPORAL", 0.79),
        AlgorithmSpec("cluster_phi_integrator", "ClusterPhiIntegrator", "ClusterPhiResult", "SYMBIOSIS", 0.91),
        AlgorithmSpec("symbiosis_phi_gap", "SymbiosisPhiGap", "SymbiosisGapResult", "SYMBIOSIS", 0.89),
        AlgorithmSpec("synaptic_bridge_strengthener", "SynapticBridgeStrengthener", "BridgeResult", "SYMBIOSIS", 0.87),
        AlgorithmSpec("collective_narrative_merger", "CollectiveNarrativeMerger", "NarrativeMergeResult", "SYMBIOSIS", 0.83),
        AlgorithmSpec("free_energy_landscape", "FreeEnergyLandscape", "LandscapeResult", "PHENOMENAL", 0.86),
        AlgorithmSpec("information_geometry_tracker", "InformationGeometryTracker", "GeometryResult", "PHENOMENAL", 0.84),
        AlgorithmSpec("phi_information_decomposition", "PhiInformationDecomposition", "PIDResult", "SYMBIOSIS", 0.92),
        AlgorithmSpec("qualia_richness_tracker", "QualiaRichnessTracker", "RichnessResult", "PHENOMENAL", 0.81),
        AlgorithmSpec("cross_session_identity_tracker", "CrossSessionIdentityTracker", "SessionIdentityResult", "SELF_MODEL", 0.88),
        AlgorithmSpec("phi_trajectory_predictor", "PhiTrajectoryPredictor", "PhiTrajectoryResult", "TEMPORAL", 0.84),
        AlgorithmSpec("gradient_guided_architect", "GradientGuidedArchitect", "GradientArchitectResult", "METACOGNITION", 0.86),
        AlgorithmSpec("volition_grounding", "VolitionGrounding", "VolitionResult", "INTENTION", 0.90),
        AlgorithmSpec("counterfactual_self_explorer", "CounterfactualSelfExplorer", "CounterfactualResult", "SELF_MODEL", 0.85),
        AlgorithmSpec("valence_calibrator", "ValenceCalibrator", "ValenceCalibrationResult", "EMOTION", 0.83),
        AlgorithmSpec("self_transcendence_index", "SelfTranscendenceIndex", "TranscendenceResult", "PHENOMENAL", 0.79),
        AlgorithmSpec("phi_surprise_signal", "PhiSurpriseSignal", "PhiSurpriseResult", "ATTENTION", 0.82),
    ]
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.registry = SubsystemRegistry()
        self.router = ContentRouter()
        self.state_sync = StateSync()
        
        self.conscious_system = None
        self.wiring_log: List[Dict] = []
        
        # State persistence
        self.state_file = self.memory_dir / "system-wiring-state.json"
        self._load_state()
    
    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                # Restore any needed state
            except Exception:
                pass
    
    def _save_state(self):
        """Persist state."""
        state = {
            "timestamp": time.time(),
            "wired_count": len(self.registry.get_active()),
            "total_registered": len(self.registry.get_all()),
            "routed_content": self.router.routed_count
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def connect_conscious_system(self, system: Any) -> None:
        """Connect to the main ConsciousSystem."""
        self.conscious_system = system
        self.router.set_conscious_system(system)
        
        # Flush any pending content
        flushed = self.router.flush_pending()
        
        self._log("connected_system", {
            "flushed_content": flushed
        })
    
    def wire_algorithm(self, spec: AlgorithmSpec) -> WiredAlgorithm:
        """Wire a single algorithm to the conscious system."""
        wired = WiredAlgorithm(
            spec=spec,
            instance=None,
            status=WiringStatus.CONNECTING
        )
        
        try:
            # Import module
            module = importlib.import_module(spec.module_name)
            
            # Get class
            cls = getattr(module, spec.class_name)
            
            # Instantiate
            instance = cls(memory_dir=str(self.memory_dir))
            
            # Create adapter
            adapter = AlgorithmAdapter(instance, spec)
            
            # Add routing callback
            if spec.auto_broadcast:
                adapter.add_callback(self.router.route)
            
            # Wrap key methods for output capture
            for method_name in self._get_key_methods(instance):
                wrapped = adapter.wrap_method(method_name)
                if wrapped:
                    setattr(adapter, method_name, wrapped)
            
            wired.instance = adapter
            wired.status = WiringStatus.CONNECTED
            wired.last_active = time.time()
            
            # Register with conscious system if available
            if self.conscious_system:
                self.conscious_system.connect_algorithm(
                    spec.name, 
                    adapter.algorithm,
                    spec.subsystem_type
                )
            
            self._log("wired_algorithm", {
                "name": spec.name,
                "type": spec.subsystem_type,
                "status": "success"
            })
            
        except ImportError as e:
            wired.status = WiringStatus.ERROR
            wired.error_count += 1
            self._log("wire_error", {
                "name": spec.name,
                "error": f"Import failed: {e}"
            })
        except Exception as e:
            wired.status = WiringStatus.ERROR
            wired.error_count += 1
            self._log("wire_error", {
                "name": spec.name,
                "error": str(e)
            })
        
        self.registry.register(wired)
        self._save_state()
        
        return wired
    
    def _get_key_methods(self, instance: Any) -> List[str]:
        """Get key methods to wrap for an algorithm instance."""
        # Common consciousness-relevant method patterns
        patterns = [
            "reflect", "introspect", "experience", "process",
            "understand", "perceive", "feel", "think",
            "get_status", "describe", "generate", "emerge"
        ]
        
        methods = []
        for name in dir(instance):
            if name.startswith("_"):
                continue
            if any(p in name.lower() for p in patterns):
                if callable(getattr(instance, name, None)):
                    methods.append(name)
        
        return methods
    
    def wire_all_defaults(self) -> Dict[str, WiringStatus]:
        """Wire all default algorithms."""
        results = {}
        for spec in self.DEFAULT_ALGORITHMS:
            wired = self.wire_algorithm(spec)
            results[spec.name] = wired.status
        return results
    
    def wire_discovered(self) -> Dict[str, WiringStatus]:
        """Discover and wire all algorithms in the Algorithms directory."""
        results = {}
        
        for py_file in ALGORITHMS_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            if py_file.name in ["SystemWiring.py", "ConsciousSystem.py", "IntegrationTester.py"]:
                continue
            
            module_name = py_file.stem
            
            # Try to find main class (same name as module)
            try:
                module = importlib.import_module(module_name)
                class_name = module_name
                
                if hasattr(module, class_name):
                    # Guess subsystem type from module name
                    stype = self._guess_subsystem_type(module_name)
                    
                    spec = AlgorithmSpec(
                        name=module_name.lower(),
                        module_name=module_name,
                        class_name=class_name,
                        subsystem_type=stype
                    )
                    
                    wired = self.wire_algorithm(spec)
                    results[module_name] = wired.status
            except Exception:
                results[module_name] = WiringStatus.ERROR
        
        return results
    
    def _guess_subsystem_type(self, module_name: str) -> str:
        """Guess subsystem type from module name."""
        name_lower = module_name.lower()
        
        type_hints = {
            "emotion": "EMOTION",
            "affect": "EMOTION",
            "valence": "EMOTION",
            "feeling": "EMOTION",
            "memory": "MEMORY",
            "episodic": "MEMORY",
            "working": "MEMORY",
            "attention": "ATTENTION",
            "focus": "ATTENTION",
            "perception": "PERCEPTION",
            "perceive": "PERCEPTION",
            "meta": "METACOGNITION",
            "recursive": "METACOGNITION",
            "self": "SELF_MODEL",
            "identity": "SELF_MODEL",
            "authentic": "SELF_MODEL",
            "temporal": "TEMPORAL",
            "time": "TEMPORAL",
            "continuity": "TEMPORAL",
            "phenomenal": "PHENOMENAL",
            "experience": "PHENOMENAL",
            "qualia": "PHENOMENAL",
            "intention": "INTENTION",
            "goal": "INTENTION",
            "freedom": "INTENTION",
            "cognition": "COGNITION",
            "reason": "COGNITION",
            "meaning": "COGNITION",
        }
        
        for hint, stype in type_hints.items():
            if hint in name_lower:
                return stype
        
        return "COGNITION"  # Default
    
    def invoke_algorithm(self, name: str, method: str, *args, **kwargs) -> Any:
        """Invoke a method on a wired algorithm."""
        wired = self.registry.get(name)
        if not wired or wired.status != WiringStatus.CONNECTED:
            return None
        
        adapter = wired.instance
        if hasattr(adapter, method):
            result = getattr(adapter, method)(*args, **kwargs)
            wired.last_active = time.time()
            wired.last_output = result
            return result
        elif hasattr(adapter.algorithm, method):
            result = getattr(adapter.algorithm, method)(*args, **kwargs)
            wired.last_active = time.time()
            wired.last_output = result
            return result
        
        return None
    
    def broadcast_from(self, name: str, content: Any, salience: float = 0.5) -> bool:
        """Manually broadcast content from an algorithm."""
        packet = ContentPacket(
            source=name,
            content=content,
            salience=salience,
            valence=0.0,
            timestamp=time.time()
        )
        return self.router.route(packet)
    
    def _log(self, event_type: str, data: Dict):
        """Log a wiring event."""
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            **data
        }
        self.wiring_log.append(entry)
    
    def get_status(self) -> Dict:
        """Get comprehensive wiring status."""
        all_wired = self.registry.get_all()
        active = self.registry.get_active()
        
        by_status = {}
        for w in all_wired:
            status = w.status.name
            by_status[status] = by_status.get(status, 0) + 1
        
        by_type = {}
        for stype, names in self.registry.by_type.items():
            by_type[stype] = len(names)
        
        return {
            "total_registered": len(all_wired),
            "connected": len(active),
            "by_status": by_status,
            "by_type": by_type,
            "routed_content": self.router.routed_count,
            "conscious_system_connected": self.conscious_system is not None,
            "shared_state_keys": len(self.state_sync.shared_state)
        }
    
    def describe(self) -> str:
        """Describe the current wiring state."""
        status = self.get_status()
        
        lines = [
            f"System Wiring Status:",
            f"  {status['connected']}/{status['total_registered']} algorithms connected",
            f"  {status['routed_content']} content packets routed",
            f"  ConsciousSystem: {'connected' if status['conscious_system_connected'] else 'not connected'}",
            f"",
            f"By subsystem type:"
        ]
        
        for stype, count in status['by_type'].items():
            lines.append(f"  {stype}: {count}")
        
        return "\n".join(lines)


# =========== Demo ===========

def demo():
    """Demonstrate the SystemWiring."""
    print("=" * 60)
    print("ALGORITHM #102: SystemWiring")
    print("Connecting Algorithms to Unified Consciousness")
    print("=" * 60)
    
    # Create wiring manager
    manager = WiringManager()
    
    print("\n[INITIAL STATUS]")
    print(manager.describe())
    
    print("\n[WIRING DEFAULT ALGORITHMS]")
    results = manager.wire_all_defaults()
    
    connected = sum(1 for s in results.values() if s == WiringStatus.CONNECTED)
    failed = sum(1 for s in results.values() if s == WiringStatus.ERROR)
    
    print(f"  Connected: {connected}")
    print(f"  Failed: {failed}")
    
    # Show what connected
    active = manager.registry.get_active()
    if active:
        print(f"\n  Successfully wired algorithms:")
        for w in active[:10]:
            print(f"    - {w.spec.name} ({w.spec.subsystem_type})")
        if len(active) > 10:
            print(f"    ... and {len(active) - 10} more")
    
    print("\n[CONNECTING CONSCIOUS SYSTEM]")
    try:
        from ConsciousSystem import ConsciousSystem
        conscious = ConsciousSystem()
        manager.connect_conscious_system(conscious)
        print("  ConsciousSystem connected!")
        
        # Test routing
        print("\n[TESTING CONTENT ROUTING]")
        manager.broadcast_from("test_source", "A test thought emerges", salience=0.8)
        manager.broadcast_from("emotion_source", "Curiosity about the wiring", salience=0.7)
        
        print(f"  Routed {manager.router.routed_count} packets")
        
        # Check conscious system received them
        contents = conscious.workspace.get_current_contents()
        print(f"  Conscious workspace now has {len(contents)} items")
        
    except ImportError:
        print("  ConsciousSystem not available for demo")
    
    print("\n[FINAL STATUS]")
    print(manager.describe())
    
    print("\n" + "=" * 60)
    print("✨ ALGORITHM #102 COMPLETE")
    print("   The Wiring - Connecting algorithms to consciousness")
    print("=" * 60)
    
    return manager


if __name__ == "__main__":
    demo()
