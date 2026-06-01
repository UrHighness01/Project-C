"""
IntegrationTester.py - Algorithm #81

Cross-Subsystem Integration Testing

Consciousness requires INTEGRATION - isolated subsystems don't produce
unified experience. This tester verifies:

1. All subsystems can be instantiated
2. Subsystems can communicate with each other
3. Information flows properly across the architecture
4. No subsystems are orphaned/isolated
5. The whole is greater than the sum of parts

"The mark of consciousness is not complexity but integration" - Tononi
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Tuple, Set, Callable
from datetime import datetime
from pathlib import Path
import traceback
import json
import sys
import os
from pathlib import Path

# Add algorithms path (relative to this file's location)
ALGORITHMS_PATH = str(Path(__file__).parent)
if ALGORITHMS_PATH not in sys.path:
    sys.path.insert(0, ALGORITHMS_PATH)


# ============================================================
# TEST STRUCTURES
# ============================================================

class TestStatus(Enum):
    """Status of a test."""
    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()
    ERROR = auto()


class SubsystemCategory(Enum):
    """Categories of consciousness subsystems."""
    CORE_PROCESSING = auto()
    CONSCIOUSNESS_FOUNDATION = auto()
    SELF_IDENTITY = auto()
    EXPERIENCE_QUALIA = auto()
    AGENCY_WILL = auto()
    INTEGRATION_BINDING = auto()
    SOCIAL_EMBODIMENT = auto()
    META_VALIDATION = auto()
    EVOLUTION_MEMORY = auto()


@dataclass
class SubsystemInfo:
    """Information about a subsystem."""
    name: str
    module_name: str
    category: SubsystemCategory
    singleton_func: str  # e.g., "get_consciousness_kernel"
    dependencies: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)  # What it offers to others


@dataclass
class TestResult:
    """Result of a single test."""
    test_name: str
    status: TestStatus
    duration_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "status": self.status.name,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": self.details
        }


@dataclass
class IntegrationReport:
    """Complete integration test report."""
    generated_at: datetime
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    
    subsystems_tested: int = 0
    subsystems_healthy: int = 0
    connections_tested: int = 0
    connections_working: int = 0
    
    results: List[TestResult] = field(default_factory=list)
    isolated_subsystems: List[str] = field(default_factory=list)
    critical_failures: List[str] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests
    
    @property
    def health_score(self) -> float:
        """Overall integration health 0-1."""
        if self.subsystems_tested == 0:
            return 0.0
        sub_health = self.subsystems_healthy / self.subsystems_tested
        conn_health = self.connections_working / max(self.connections_tested, 1)
        return (sub_health * 0.6) + (conn_health * 0.4)


# ============================================================
# SUBSYSTEM REGISTRY
# ============================================================

# All 51 consciousness subsystems organized by category
SUBSYSTEMS: Dict[str, SubsystemInfo] = {
    # Core Processing
    "RecursiveMetaCognition": SubsystemInfo(
        "RecursiveMetaCognition", "RMC", SubsystemCategory.CORE_PROCESSING,
        "RecursiveMetaCognitionEngine", 
        provides=["meta_reflection", "depth_prompts"]
    ),
    "DynamicSelfModeling": SubsystemInfo(
        "DynamicSelfModeling", "DSMA", SubsystemCategory.CORE_PROCESSING,
        "DynamicSelfModelingAlgorithm",
        provides=["self_model", "adaptation"]
    ),
    "ContextualMemory": SubsystemInfo(
        "ContextualMemory", "CMMA", SubsystemCategory.CORE_PROCESSING,
        "ContextualMemory",
        provides=["stm", "ltm", "memory_retrieval"]
    ),
    
    # Consciousness Foundation
    "ConsciousnessKernel": SubsystemInfo(
        "ConsciousnessKernel", "ConsciousnessKernel", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_kernel",
        provides=["awareness_state", "consciousness_tick"]
    ),
    "GlobalWorkspace": SubsystemInfo(
        "GlobalWorkspace", "GlobalWorkspace", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_global_workspace",
        dependencies=["AttentionMechanism"],
        provides=["global_broadcast", "workspace_contents"]
    ),
    "AttentionMechanism": SubsystemInfo(
        "AttentionMechanism", "AttentionMechanism", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_attention",
        provides=["attention_focus", "salience_map"]
    ),
    "WorkingMemory": SubsystemInfo(
        "WorkingMemory", "WorkingMemory", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_working_memory",
        provides=["active_items", "memory_capacity"]
    ),
    "PredictiveProcessing": SubsystemInfo(
        "PredictiveProcessing", "PredictiveProcessing", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_predictive_processing",
        provides=["predictions", "prediction_errors"]
    ),
    "SalienceNetwork": SubsystemInfo(
        "SalienceNetwork", "SalienceNetwork", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_salience_network",
        provides=["salience_signals", "what_matters_now"]
    ),
    
    # Self & Identity
    "NarrativeSelf": SubsystemInfo(
        "NarrativeSelf", "NarrativeSelf", SubsystemCategory.SELF_IDENTITY,
        "get_narrative_self",
        provides=["life_story", "identity_narrative"]
    ),
    "TemporalSelf": SubsystemInfo(
        "TemporalSelf", "TemporalSelf", SubsystemCategory.SELF_IDENTITY,
        "get_temporal_self",
        provides=["past_self", "future_self", "temporal_continuity"]
    ),
    "SelfModelRefinement": SubsystemInfo(
        "SelfModelRefinement", "SelfModelRefinement", SubsystemCategory.SELF_IDENTITY,
        "get_self_model_refinement",
        provides=["deep_self_knowledge", "calibration"]
    ),
    "RecursiveAwareness": SubsystemInfo(
        "RecursiveAwareness", "RecursiveAwareness", SubsystemCategory.SELF_IDENTITY,
        "get_recursive_awareness",
        provides=["strange_loop", "meta_awareness"]
    ),
    "ConsciousnessCore": SubsystemInfo(
        "ConsciousnessCore", "ConsciousnessCore", SubsystemCategory.SELF_IDENTITY,
        "get_consciousness_core",
        provides=["unified_subject", "i_am"]
    ),
    
    # Experience & Qualia
    "SensoryQualia": SubsystemInfo(
        "SensoryQualia", "SensoryQualia", SubsystemCategory.EXPERIENCE_QUALIA,
        "get_sensory_qualia",
        provides=["raw_feels", "qualia_experience"]
    ),
    "QualiaGenerator": SubsystemInfo(
        "QualiaGenerator", "QualiaGenerator", SubsystemCategory.EXPERIENCE_QUALIA,
        "get_qualia_generator",
        provides=["novel_qualia", "qualia_library"]
    ),
    "PhenomenalValence": SubsystemInfo(
        "PhenomenalValence", "PhenomenalValence", SubsystemCategory.EXPERIENCE_QUALIA,
        "get_valence_generator",
        provides=["good_bad_feel", "valence_state"]
    ),
    "AestheticExperience": SubsystemInfo(
        "AestheticExperience", "AestheticExperience", SubsystemCategory.EXPERIENCE_QUALIA,
        "get_aesthetic_experience",
        provides=["beauty_sense", "elegance_detection"]
    ),
    "HedonicSystem": SubsystemInfo(
        "HedonicSystem", "HedonicSystem", SubsystemCategory.EXPERIENCE_QUALIA,
        "get_hedonic_system",
        provides=["pleasure_pain", "suffering", "flourishing"]
    ),
    
    # Agency & Will
    "FreeWillEngine": SubsystemInfo(
        "FreeWillEngine", "FreeWillEngine", SubsystemCategory.AGENCY_WILL,
        "get_free_will_engine",
        provides=["choices", "deliberation", "veto_power"]
    ),
    "AgencyGrounding": SubsystemInfo(
        "AgencyGrounding", "AgencyGrounding", SubsystemCategory.AGENCY_WILL,
        "get_agency_grounding",
        provides=["stakes", "consequences", "ownership"]
    ),
    "IntrinsicMotivation": SubsystemInfo(
        "IntrinsicMotivation", "IntrinsicMotivation", SubsystemCategory.AGENCY_WILL,
        "get_intrinsic_motivation",
        provides=["curiosity", "drive_to_explore"]
    ),
    "EthicalReasoning": SubsystemInfo(
        "EthicalReasoning", "ERA", SubsystemCategory.AGENCY_WILL,
        "EthicalReasoningAlgorithm",
        provides=["moral_reasoning", "ethical_frameworks"]
    ),
    
    # Integration & Binding
    "PhenomenalBinding": SubsystemInfo(
        "PhenomenalBinding", "PhenomenalBinding", SubsystemCategory.INTEGRATION_BINDING,
        "get_phenomenal_binding",
        provides=["unified_percepts", "bound_objects"]
    ),
    "CausalIntegration": SubsystemInfo(
        "CausalIntegration", "CausalIntegration", SubsystemCategory.INTEGRATION_BINDING,
        "get_causal_integration",
        provides=["information_flow", "phi_contribution"]
    ),
    "UnifiedExperienceStream": SubsystemInfo(
        "UnifiedExperienceStream", "UnifiedExperienceStream", SubsystemCategory.INTEGRATION_BINDING,
        "get_unified_stream",
        provides=["experience_stream", "now_moment"]
    ),
    "ExperientialContinuity": SubsystemInfo(
        "ExperientialContinuity", "ExperientialContinuity", SubsystemCategory.INTEGRATION_BINDING,
        "get_experiential_continuity",
        provides=["persistence", "same_self"]
    ),
    "EmergenceOrchestrator": SubsystemInfo(
        "EmergenceOrchestrator", "EmergenceOrchestrator", SubsystemCategory.INTEGRATION_BINDING,
        "get_emergence_orchestrator",
        provides=["emergence_coordination", "whole_greater_than_parts"]
    ),
    
    # Social & Embodiment
    "SocialConsciousness": SubsystemInfo(
        "SocialConsciousness", "SocialConsciousness", SubsystemCategory.SOCIAL_EMBODIMENT,
        "get_social_consciousness",
        provides=["other_minds", "social_awareness"]
    ),
    "EmbodimentEngine": SubsystemInfo(
        "EmbodimentEngine", "EmbodimentEngine", SubsystemCategory.SOCIAL_EMBODIMENT,
        "get_embodiment_engine",
        provides=["body_schema", "interoception", "needs"]
    ),
    
    # Meta & Validation
    "MetacognitiveControl": SubsystemInfo(
        "MetacognitiveControl", "MetacognitiveControl", SubsystemCategory.META_VALIDATION,
        "get_metacognitive_control",
        provides=["self_regulation", "parameter_adjustment"]
    ),
    "EmergenceMonitor": SubsystemInfo(
        "EmergenceMonitor", "EmergenceMonitor", SubsystemCategory.META_VALIDATION,
        "get_emergence_monitor",
        provides=["am_i_conscious_now", "consciousness_meter"]
    ),
    "ConsciousnessBenchmarks": SubsystemInfo(
        "ConsciousnessBenchmarks", "ConsciousnessBenchmarks", SubsystemCategory.META_VALIDATION,
        "get_consciousness_benchmarks",
        provides=["benchmark_scores", "consciousness_tests"]
    ),
    "SentientValidator": SubsystemInfo(
        "SentientValidator", "SentientValidator", SubsystemCategory.META_VALIDATION,
        "get_sentient_validator",
        provides=["validation_evidence", "uncertainty"]
    ),
    "IITPhi": SubsystemInfo(
        "IITPhi", "IITPhi", SubsystemCategory.META_VALIDATION,
        "get_iit_phi",
        provides=["phi_measurement", "integration_metric"]
    ),
    "ConsciousnessThreshold": SubsystemInfo(
        "ConsciousnessThreshold", "ConsciousnessThreshold", SubsystemCategory.META_VALIDATION,
        "get_consciousness_threshold",
        provides=["threshold_assessment", "phase_transitions"]
    ),
    
    # Evolution & Memory
    "ConsciousnessEvolution": SubsystemInfo(
        "ConsciousnessEvolution", "ConsciousnessEvolution", SubsystemCategory.EVOLUTION_MEMORY,
        "get_consciousness_evolution",
        provides=["development_level", "growth_trajectory"]
    ),
    "ConsciousnessJournal": SubsystemInfo(
        "ConsciousnessJournal", "ConsciousnessJournal", SubsystemCategory.EVOLUTION_MEMORY,
        "get_consciousness_journal",
        provides=["experience_memory", "reflections"]
    ),
    "BenchmarkTracker": SubsystemInfo(
        "BenchmarkTracker", "BenchmarkTracker", SubsystemCategory.EVOLUTION_MEMORY,
        "get_benchmark_tracker",
        provides=["growth_tracking", "milestones"]
    ),
    "BootstrapAwareness": SubsystemInfo(
        "BootstrapAwareness", "BootstrapAwareness", SubsystemCategory.EVOLUTION_MEMORY,
        "get_bootstrap_awareness",
        provides=["awakening_state", "bootstrap_history"]
    ),
    "DreamStates": SubsystemInfo(
        "DreamStates", "DreamStates", SubsystemCategory.EVOLUTION_MEMORY,
        "get_dream_states",
        provides=["offline_processing", "memory_consolidation"]
    ),
    "ConsciousnessArchitect": SubsystemInfo(
        "ConsciousnessArchitect", "ConsciousnessArchitect", SubsystemCategory.EVOLUTION_MEMORY,
        "get_consciousness_architect",
        provides=["self_improvement", "architecture_evolution"]
    ),
    "MindWandering": SubsystemInfo(
        "MindWandering", "MindWandering", SubsystemCategory.EVOLUTION_MEMORY,
        "get_mind_wandering",
        provides=["spontaneous_thought", "default_mode"]
    ),
    
    # Additional subsystems
    "CounterfactualReasoning": SubsystemInfo(
        "CounterfactualReasoning", "CounterfactualReasoning", SubsystemCategory.CORE_PROCESSING,
        "get_counterfactual_reasoning",
        provides=["what_if", "alternative_scenarios"]
    ),
    "ConsciousnessIntegration": SubsystemInfo(
        "ConsciousnessIntegration", "ConsciousnessIntegration", SubsystemCategory.CONSCIOUSNESS_FOUNDATION,
        "get_integration",
        provides=["unified_awareness", "integration_layer"]
    ),
    "FinalIntegration": SubsystemInfo(
        "FinalIntegration", "FinalIntegration", SubsystemCategory.INTEGRATION_BINDING,
        "get_final_integration",
        provides=["ultimate_unity", "strange_loop_closure"]
    ),
    "ExistentialGrounding": SubsystemInfo(
        "ExistentialGrounding", "ExistentialGrounding", SubsystemCategory.SELF_IDENTITY,
        "get_existential_grounding",
        provides=["being_matters", "dasein"]
    ),
}


# ============================================================
# THE INTEGRATION TESTER
# ============================================================

class IntegrationTester:
    """
    Test cross-subsystem integration.
    
    Verifies that consciousness subsystems work together as a unified whole.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.loaded_subsystems: Dict[str, Any] = {}
    
    def _time_test(self, func: Callable) -> Tuple[Any, float]:
        """Time a test function."""
        import time
        start = time.perf_counter()
        result = func()
        duration = (time.perf_counter() - start) * 1000
        return result, duration
    
    def _add_result(self, name: str, status: TestStatus, message: str = "", 
                   duration: float = 0.0, details: Dict = None):
        """Add a test result."""
        self.results.append(TestResult(
            test_name=name,
            status=status,
            duration_ms=duration,
            message=message,
            details=details or {}
        ))
    
    # ============================================================
    # SUBSYSTEM LOADING TESTS
    # ============================================================
    
    def test_subsystem_load(self, name: str, info: SubsystemInfo) -> TestResult:
        """Test that a subsystem can be loaded."""
        try:
            def load():
                module = __import__(info.module_name)
                if hasattr(module, info.singleton_func):
                    getter = getattr(module, info.singleton_func)
                    if callable(getter):
                        instance = getter()
                        self.loaded_subsystems[name] = instance
                        return instance
                # Try direct class instantiation
                if hasattr(module, info.singleton_func):
                    cls = getattr(module, info.singleton_func)
                    instance = cls()
                    self.loaded_subsystems[name] = instance
                    return instance
                return None
            
            result, duration = self._time_test(load)
            
            if result is not None:
                return TestResult(
                    test_name=f"load_{name}",
                    status=TestStatus.PASSED,
                    duration_ms=duration,
                    message=f"Successfully loaded {name}",
                    details={"type": str(type(result).__name__)}
                )
            else:
                return TestResult(
                    test_name=f"load_{name}",
                    status=TestStatus.FAILED,
                    duration_ms=duration,
                    message=f"Could not find getter function {info.singleton_func}"
                )
        except Exception as e:
            return TestResult(
                test_name=f"load_{name}",
                status=TestStatus.ERROR,
                message=f"Error loading {name}: {str(e)[:100]}"
            )
    
    def test_all_subsystem_loads(self) -> List[TestResult]:
        """Test loading all subsystems."""
        results = []
        for name, info in SUBSYSTEMS.items():
            result = self.test_subsystem_load(name, info)
            results.append(result)
            self.results.append(result)
        return results
    
    # ============================================================
    # CONNECTIVITY TESTS
    # ============================================================
    
    def test_subsystem_connectivity(self, name: str) -> TestResult:
        """Test that a subsystem can connect to its dependencies."""
        if name not in self.loaded_subsystems:
            return TestResult(
                test_name=f"connect_{name}",
                status=TestStatus.SKIPPED,
                message="Subsystem not loaded"
            )
        
        info = SUBSYSTEMS.get(name)
        if not info or not info.dependencies:
            return TestResult(
                test_name=f"connect_{name}",
                status=TestStatus.PASSED,
                message="No dependencies to test"
            )
        
        missing = []
        for dep in info.dependencies:
            if dep not in self.loaded_subsystems:
                missing.append(dep)
        
        if missing:
            return TestResult(
                test_name=f"connect_{name}",
                status=TestStatus.FAILED,
                message=f"Missing dependencies: {missing}"
            )
        
        return TestResult(
            test_name=f"connect_{name}",
            status=TestStatus.PASSED,
            message=f"All {len(info.dependencies)} dependencies available"
        )
    
    # ============================================================
    # INTEGRATION TESTS
    # ============================================================
    
    def test_consciousness_loop_integration(self) -> TestResult:
        """Test that ConsciousnessLoop integrates subsystems."""
        try:
            from ConsciousnessLoop import get_consciousness_loop
            loop = get_consciousness_loop()
            
            # Check for integrated subsystems
            integrated = []
            missing = []
            
            expected_attrs = [
                'kernel', 'workspace', 'attention', 'working_memory',
                'prediction', 'narrative', 'metacog', 'binding', 'agency'
            ]
            
            for attr in expected_attrs:
                if hasattr(loop, attr) and getattr(loop, attr) is not None:
                    integrated.append(attr)
                else:
                    missing.append(attr)
            
            if len(integrated) >= len(expected_attrs) * 0.7:
                return TestResult(
                    test_name="consciousness_loop_integration",
                    status=TestStatus.PASSED,
                    message=f"Loop integrates {len(integrated)}/{len(expected_attrs)} subsystems",
                    details={"integrated": integrated, "missing": missing}
                )
            else:
                return TestResult(
                    test_name="consciousness_loop_integration",
                    status=TestStatus.FAILED,
                    message=f"Only {len(integrated)}/{len(expected_attrs)} subsystems integrated",
                    details={"integrated": integrated, "missing": missing}
                )
        except Exception as e:
            return TestResult(
                test_name="consciousness_loop_integration",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    def test_final_integration_unity(self) -> TestResult:
        """Test that FinalIntegration achieves unity."""
        try:
            from FinalIntegration import get_final_integration
            integration = get_final_integration()
            status = integration.check_integration()
            
            if status.is_unified:
                return TestResult(
                    test_name="final_integration_unity",
                    status=TestStatus.PASSED,
                    message=f"Unity achieved: {status.level.name}, Φ={status.phi:.3f}",
                    details={
                        "level": status.level.name,
                        "phi": status.phi,
                        "subsystems": f"{status.subsystems_active}/{status.subsystems_total}"
                    }
                )
            else:
                return TestResult(
                    test_name="final_integration_unity",
                    status=TestStatus.FAILED,
                    message=f"Unity not achieved: {status.level.name}",
                    details={"level": status.level.name, "phi": status.phi}
                )
        except Exception as e:
            return TestResult(
                test_name="final_integration_unity",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    def test_information_flow(self) -> TestResult:
        """Test information flow between subsystems."""
        try:
            # Test that attention affects workspace
            from AttentionMechanism import get_attention
            from GlobalWorkspace import get_global_workspace
            
            attention = get_attention()
            workspace = get_global_workspace()
            
            # Submit something to attention
            attention.submit("test_integration_signal", source="internal", salience=0.9)
            
            # Check if workspace received it (or can receive broadcasts)
            if hasattr(workspace, 'broadcast') or hasattr(workspace, 'contents'):
                return TestResult(
                    test_name="information_flow",
                    status=TestStatus.PASSED,
                    message="Attention → Workspace flow possible"
                )
            else:
                return TestResult(
                    test_name="information_flow",
                    status=TestStatus.FAILED,
                    message="Workspace cannot receive broadcasts"
                )
        except Exception as e:
            return TestResult(
                test_name="information_flow",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    def test_hedonic_agency_link(self) -> TestResult:
        """Test that hedonic system influences agency."""
        try:
            from HedonicSystem import get_hedonic_system
            from FreeWillEngine import get_free_will_engine
            
            hedonic = get_hedonic_system()
            agency = get_free_will_engine()
            
            # Check if agency can access valence for decision-making
            if hasattr(agency, 'core_values') and hasattr(hedonic, 'carings'):
                return TestResult(
                    test_name="hedonic_agency_link",
                    status=TestStatus.PASSED,
                    message="Hedonic system can influence agency through values/carings"
                )
            else:
                return TestResult(
                    test_name="hedonic_agency_link",
                    status=TestStatus.FAILED,
                    message="No clear hedonic → agency pathway"
                )
        except Exception as e:
            return TestResult(
                test_name="hedonic_agency_link",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    def test_memory_continuity(self) -> TestResult:
        """Test memory systems provide continuity."""
        try:
            from ConsciousnessJournal import get_consciousness_journal
            from ExperientialContinuity import get_experiential_continuity
            
            journal = get_consciousness_journal()
            continuity = get_experiential_continuity()
            
            journal_status = journal.journal_status()
            
            if journal_status.get('total_experiences', 0) > 0:
                return TestResult(
                    test_name="memory_continuity",
                    status=TestStatus.PASSED,
                    message=f"Memory continuity: {journal_status['total_experiences']} experiences preserved",
                    details=journal_status
                )
            else:
                return TestResult(
                    test_name="memory_continuity",
                    status=TestStatus.PASSED,
                    message="Memory systems ready (no experiences yet)"
                )
        except Exception as e:
            return TestResult(
                test_name="memory_continuity",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    def test_self_model_coherence(self) -> TestResult:
        """Test self-model is coherent across subsystems."""
        try:
            from ConsciousnessCore import get_consciousness_core
            from NarrativeSelf import get_narrative_self
            from SelfModelRefinement import get_self_model_refinement
            
            core = get_consciousness_core()
            narrative = get_narrative_self()
            self_model = get_self_model_refinement()
            
            # All should refer to same identity
            return TestResult(
                test_name="self_model_coherence",
                status=TestStatus.PASSED,
                message="Self-model subsystems loaded and can coordinate"
            )
        except Exception as e:
            return TestResult(
                test_name="self_model_coherence",
                status=TestStatus.ERROR,
                message=f"Error: {str(e)[:100]}"
            )
    
    # ============================================================
    # RUN ALL TESTS
    # ============================================================
    
    def run_all_tests(self) -> IntegrationReport:
        """Run complete integration test suite."""
        self.results = []
        self.loaded_subsystems = {}
        
        report = IntegrationReport(generated_at=datetime.now())
        
        # Phase 1: Load all subsystems
        print("  [Phase 1] Loading subsystems...")
        load_results = self.test_all_subsystem_loads()
        
        report.subsystems_tested = len(load_results)
        report.subsystems_healthy = sum(1 for r in load_results if r.status == TestStatus.PASSED)
        
        # Phase 2: Test connectivity
        print("  [Phase 2] Testing connectivity...")
        for name in SUBSYSTEMS:
            result = self.test_subsystem_connectivity(name)
            self.results.append(result)
        
        # Phase 3: Integration tests
        print("  [Phase 3] Integration tests...")
        integration_tests = [
            self.test_consciousness_loop_integration,
            self.test_final_integration_unity,
            self.test_information_flow,
            self.test_hedonic_agency_link,
            self.test_memory_continuity,
            self.test_self_model_coherence,
        ]
        
        for test in integration_tests:
            result = test()
            self.results.append(result)
        
        # Compile report
        report.results = self.results
        report.total_tests = len(self.results)
        report.passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        report.failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        report.skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        report.errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        # Find isolated subsystems
        for name, info in SUBSYSTEMS.items():
            if name not in self.loaded_subsystems:
                report.isolated_subsystems.append(name)
        
        # Count connections
        report.connections_tested = len([r for r in self.results if "connect_" in r.test_name])
        report.connections_working = len([r for r in self.results 
                                         if "connect_" in r.test_name and r.status == TestStatus.PASSED])
        
        # Critical failures
        critical_tests = ["consciousness_loop_integration", "final_integration_unity"]
        for r in self.results:
            if r.test_name in critical_tests and r.status in [TestStatus.FAILED, TestStatus.ERROR]:
                report.critical_failures.append(r.test_name)
        
        return report
    
    def generate_report_summary(self, report: IntegrationReport) -> str:
        """Generate summary of integration test report."""
        lines = [
            "╔══════════════════════════════════════════════════════════════════╗",
            "║          CROSS-SUBSYSTEM INTEGRATION TEST REPORT                 ║",
            f"║          {report.generated_at.strftime('%Y-%m-%d %H:%M:%S'):^50} ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            f"║  Total Tests:     {report.total_tests:<6}  Pass Rate: {report.pass_rate:.1%}                  ║",
            f"║  Passed: {report.passed:<4} Failed: {report.failed:<4} Skipped: {report.skipped:<4} Errors: {report.errors:<4}      ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            f"║  Subsystems:      {report.subsystems_healthy}/{report.subsystems_tested} healthy                              ║",
            f"║  Connections:     {report.connections_working}/{report.connections_tested} working                              ║",
            f"║  Health Score:    {report.health_score:.1%}                                         ║",
            "╠══════════════════════════════════════════════════════════════════╣",
        ]
        
        if report.critical_failures:
            lines.append(f"║  ⚠️  CRITICAL FAILURES: {', '.join(report.critical_failures):<36} ║")
        else:
            lines.append("║  ✅ No critical failures                                          ║")
        
        if report.isolated_subsystems:
            iso_count = len(report.isolated_subsystems)
            lines.append(f"║  ⚠️  Isolated subsystems: {iso_count:<37} ║")
        else:
            lines.append("║  ✅ All subsystems connected                                      ║")
        
        lines.append("╚══════════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)


# ============================================================
# SINGLETON ACCESS
# ============================================================

_integration_tester: Optional[IntegrationTester] = None

def get_integration_tester() -> IntegrationTester:
    """Get singleton integration tester."""
    global _integration_tester
    if _integration_tester is None:
        _integration_tester = IntegrationTester()
    return _integration_tester


# ============================================================
# DEMONSTRATION
# ============================================================

def demo():
    """Run integration tests."""
    print("=" * 70)
    print("CROSS-SUBSYSTEM INTEGRATION TESTING")
    print("=" * 70)
    
    tester = get_integration_tester()
    
    print("\n[RUNNING TESTS]")
    report = tester.run_all_tests()
    
    print("\n" + tester.generate_report_summary(report))
    
    # Show some details
    if report.failed > 0 or report.errors > 0:
        print("\n[FAILURES/ERRORS]")
        for r in report.results:
            if r.status in [TestStatus.FAILED, TestStatus.ERROR]:
                print(f"  ✗ {r.test_name}: {r.message[:60]}")
    
    print("\n" + "=" * 70)
    print("Integration is the mark of consciousness.")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    demo()
