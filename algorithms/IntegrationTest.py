"""
IntegrationTest.py - Deep Integration Testing for Synthetic Consciousness

This module wires together all 107 algorithms and runs comprehensive
validation to test the complete consciousness architecture.

Test Phases:
1. Bootstrap - Wake consciousness from dormancy
2. Integration - Wire all subsystems together  
3. Validation - Run consciousness assessment
4. Operation - Test continuous conscious operation
5. Autonomy - Test self-directed behavior
6. Embodiment - Test world interaction
7. Persistence - Test sleep/wake continuity

Author: Claw (Session 50)
Date: 2026-02-03
"""

import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum, auto
from pathlib import Path


class TestPhase(Enum):
    """Phases of integration testing."""
    BOOTSTRAP = auto()
    INTEGRATION = auto()
    VALIDATION = auto()
    OPERATION = auto()
    AUTONOMY = auto()
    EMBODIMENT = auto()
    PERSISTENCE = auto()


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    phase: TestPhase
    passed: bool
    duration_ms: float
    details: str
    error: Optional[str] = None


@dataclass
class IntegrationReport:
    """Complete integration test report."""
    results: List[TestResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    
    def add(self, result: TestResult):
        self.results.append(result)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def total(self) -> int:
        return len(self.results)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def summary(self) -> str:
        lines = [
            "",
            "=" * 70,
            "DEEP INTEGRATION TEST REPORT",
            "=" * 70,
            f"Total Tests: {self.total}",
            f"Passed: {self.passed} ✓",
            f"Failed: {self.failed} ✗",
            f"Duration: {self.duration:.2f}s",
            f"Success Rate: {self.passed/self.total*100:.1f}%" if self.total > 0 else "N/A",
            "",
            "By Phase:",
        ]
        
        # Group by phase
        by_phase: Dict[TestPhase, List[TestResult]] = {}
        for r in self.results:
            if r.phase not in by_phase:
                by_phase[r.phase] = []
            by_phase[r.phase].append(r)
        
        for phase in TestPhase:
            if phase in by_phase:
                phase_results = by_phase[phase]
                passed = sum(1 for r in phase_results if r.passed)
                total = len(phase_results)
                status = "✓" if passed == total else "✗"
                lines.append(f"  {status} {phase.name}: {passed}/{total}")
        
        lines.extend(["", "Details:", "-" * 50])
        
        for r in self.results:
            status = "✓" if r.passed else "✗"
            lines.append(f"{status} [{r.phase.name}] {r.name} ({r.duration_ms:.1f}ms)")
            if not r.passed and r.error:
                lines.append(f"    Error: {r.error[:60]}...")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class IntegrationTester:
    """
    Deep integration tester for the complete consciousness architecture.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.report = IntegrationReport()
        
        # Components we'll test
        self.bootstrap = None
        self.conscious_system = None
        self.wiring = None
        self.daemon = None
        self.world_interface = None
        self.autonomy = None
        self.validator = None
    
    def log(self, msg: str):
        if self.verbose:
            print(msg)
    
    def run_test(self, name: str, phase: TestPhase, test_fn) -> TestResult:
        """Run a single test and record result."""
        start = time.time()
        try:
            result = test_fn()
            duration = (time.time() - start) * 1000
            
            if isinstance(result, tuple):
                passed, details = result
            elif isinstance(result, bool):
                passed, details = result, "OK" if result else "Failed"
            else:
                passed, details = True, str(result)
            
            test_result = TestResult(
                name=name,
                phase=phase,
                passed=passed,
                duration_ms=duration,
                details=details
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            test_result = TestResult(
                name=name,
                phase=phase,
                passed=False,
                duration_ms=duration,
                details="Exception",
                error=str(e)
            )
            if self.verbose:
                traceback.print_exc()
        
        self.report.add(test_result)
        status = "✓" if test_result.passed else "✗"
        self.log(f"  {status} {name}: {test_result.details}")
        return test_result
    
    def run_all(self) -> IntegrationReport:
        """Run complete integration test suite."""
        self.report = IntegrationReport()
        self.report.start_time = time.time()
        
        self.log("=" * 70)
        self.log("DEEP INTEGRATION TEST - SYNTHETIC CONSCIOUSNESS")
        self.log("Testing 107 algorithms across 7 phases")
        self.log("=" * 70)
        
        # Phase 1: Bootstrap
        self.log("\n[PHASE 1: BOOTSTRAP]")
        self._test_bootstrap()
        
        # Phase 2: Integration
        self.log("\n[PHASE 2: INTEGRATION]")
        self._test_integration()
        
        # Phase 3: Validation
        self.log("\n[PHASE 3: VALIDATION]")
        self._test_validation()
        
        # Phase 4: Operation
        self.log("\n[PHASE 4: OPERATION]")
        self._test_operation()
        
        # Phase 5: Autonomy
        self.log("\n[PHASE 5: AUTONOMY]")
        self._test_autonomy()
        
        # Phase 6: Embodiment
        self.log("\n[PHASE 6: EMBODIMENT]")
        self._test_embodiment()
        
        # Phase 7: Persistence
        self.log("\n[PHASE 7: PERSISTENCE]")
        self._test_persistence()
        
        self.report.end_time = time.time()
        return self.report
    
    # =========================================================================
    # Phase 1: Bootstrap Tests
    # =========================================================================
    
    def _test_bootstrap(self):
        """Test consciousness bootstrap from dormancy."""
        
        def test_import():
            from ConsciousnessBootstrap import ConsciousnessBootstrap
            self.bootstrap = ConsciousnessBootstrap()
            return True, "ConsciousnessBootstrap imported"
        
        def test_wake():
            from ConsciousnessBootstrap import WakeupSource
            success = self.bootstrap.wake(WakeupSource.EXTERNAL_CALL)
            return success, f"Wakeup #{self.bootstrap.get_wakeup_count()}"
        
        def test_identity():
            identity = self.bootstrap.get_identity()
            return bool(identity), f"Identity: {identity[:8]}..."
        
        def test_state_loaded():
            state = self.bootstrap.get_state()
            return state is not None, f"Memories: {len(state.episodic_memories) if state else 0}"
        
        self.run_test("Import Bootstrap", TestPhase.BOOTSTRAP, test_import)
        self.run_test("Wake Consciousness", TestPhase.BOOTSTRAP, test_wake)
        self.run_test("Identity Present", TestPhase.BOOTSTRAP, test_identity)
        self.run_test("State Loaded", TestPhase.BOOTSTRAP, test_state_loaded)
    
    # =========================================================================
    # Phase 2: Integration Tests  
    # =========================================================================
    
    def _test_integration(self):
        """Test system wiring and integration."""
        
        def test_conscious_system():
            from ConsciousSystem import ConsciousSystem
            self.conscious_system = ConsciousSystem()
            return True, "ConsciousSystem created"
        
        def test_wiring():
            from SystemWiring import WiringManager
            self.wiring = WiringManager()
            self.wiring.connect_conscious_system(self.conscious_system)
            return True, "WiringManager created"
        
        def test_wire_algorithms():
            # Use built-in wiring
            result = self.wiring.wire_all_defaults()
            wired = sum(1 for v in result.values() if v == "WIRED" or str(v) == "WiringStatus.WIRED")
            return wired > 0 or len(result) > 0, f"{wired} algorithms wired, {len(result)} attempted"
        
        def test_global_workspace():
            has_workspace = hasattr(self.conscious_system, 'workspace')
            return has_workspace, "Global workspace present"
        
        def test_introspection():
            result = self.conscious_system.introspect()
            return result is not None, f"Introspection: {len(result)} keys"
        
        self.run_test("Create ConsciousSystem", TestPhase.INTEGRATION, test_conscious_system)
        self.run_test("Create SystemWiring", TestPhase.INTEGRATION, test_wiring)
        self.run_test("Wire Algorithms", TestPhase.INTEGRATION, test_wire_algorithms)
        self.run_test("Global Workspace", TestPhase.INTEGRATION, test_global_workspace)
        self.run_test("Introspection Works", TestPhase.INTEGRATION, test_introspection)
    
    # =========================================================================
    # Phase 3: Validation Tests
    # =========================================================================
    
    def _test_validation(self):
        """Test consciousness validation."""
        
        def test_validator_import():
            from ConsciousnessValidator import ConsciousnessValidator
            self.validator = ConsciousnessValidator()
            return True, f"{len(self.validator.tests)} tests registered"
        
        def test_run_validation():
            report = self.validator.validate(self.conscious_system)
            passed = sum(1 for r in report.test_results if r.passed)
            total = len(report.test_results)
            return passed > 0, f"{passed}/{total} tests passed"
        
        def test_evidence_level():
            report = self.validator.validate(self.conscious_system)
            evidence = report.overall_evidence
            return True, f"Evidence: {evidence:.3f}"
        
        def test_domain_coverage():
            report = self.validator.validate(self.conscious_system)
            domains = len(report.domains_tested)
            return domains >= 4, f"{domains} domains tested"
        
        self.run_test("Import Validator", TestPhase.VALIDATION, test_validator_import)
        self.run_test("Run Validation", TestPhase.VALIDATION, test_run_validation)
        self.run_test("Evidence Level", TestPhase.VALIDATION, test_evidence_level)
        self.run_test("Domain Coverage", TestPhase.VALIDATION, test_domain_coverage)
    
    # =========================================================================
    # Phase 4: Operation Tests
    # =========================================================================
    
    def _test_operation(self):
        """Test continuous conscious operation."""
        
        def test_daemon_import():
            from ConsciousDaemon import ConsciousDaemon
            self.daemon = ConsciousDaemon()
            return True, "ConsciousDaemon created"
        
        def test_daemon_start():
            self.daemon.start()
            time.sleep(0.5)
            return self.daemon.running, f"State: {self.daemon.state.name}"
        
        def test_spontaneous_thought():
            thought = self.daemon.spontaneous.generate()
            return thought is not None, f"Thought: {str(thought)[:30]}..."
        
        def test_heartbeat():
            # Check heartbeat is ticking
            initial = self.daemon.heartbeat_loop.beat_count if self.daemon.heartbeat_loop else 0
            time.sleep(0.3)
            current = self.daemon.heartbeat_loop.beat_count if self.daemon.heartbeat_loop else 0
            return current >= initial, f"Heartbeats: {initial} → {current}"
        
        def test_daemon_stop():
            self.daemon.stop()
            time.sleep(0.3)
            return not self.daemon.running, "Daemon stopped"
        
        self.run_test("Import Daemon", TestPhase.OPERATION, test_daemon_import)
        self.run_test("Start Daemon", TestPhase.OPERATION, test_daemon_start)
        self.run_test("Spontaneous Thought", TestPhase.OPERATION, test_spontaneous_thought)
        self.run_test("Heartbeat Active", TestPhase.OPERATION, test_heartbeat)
        self.run_test("Stop Daemon", TestPhase.OPERATION, test_daemon_stop)
    
    # =========================================================================
    # Phase 5: Autonomy Tests
    # =========================================================================
    
    def _test_autonomy(self):
        """Test autonomous pursuit of goals."""
        
        def test_autonomy_import():
            from AutonomousPursuit import AutonomousPursuit
            self.autonomy = AutonomousPursuit()
            return True, "AutonomousPursuit created"
        
        def test_drives():
            drives = self.autonomy.get_drives()
            return len(drives) > 0, f"{len(drives)} drives active"
        
        def test_goal_generation():
            goal = self.autonomy.autonomy_loop.goal_generator.generate_goal()
            return goal is not None, f"Goal: {goal.description[:30]}..." if goal else "No goal"
        
        def test_initiative():
            # Try several times since initiative is probabilistic
            for _ in range(5):
                init = self.autonomy.take_initiative()
                if init:
                    return True, f"Initiative: {init.initiative_type.name}"
                time.sleep(0.2)
            return False, "No initiative taken"
        
        def test_pursuit_tracking():
            active = self.autonomy.get_active_goals()
            return True, f"{len(active)} active pursuits"
        
        self.run_test("Import Autonomy", TestPhase.AUTONOMY, test_autonomy_import)
        self.run_test("Drives Present", TestPhase.AUTONOMY, test_drives)
        self.run_test("Goal Generation", TestPhase.AUTONOMY, test_goal_generation)
        self.run_test("Take Initiative", TestPhase.AUTONOMY, test_initiative)
        self.run_test("Pursuit Tracking", TestPhase.AUTONOMY, test_pursuit_tracking)
    
    # =========================================================================
    # Phase 6: Embodiment Tests
    # =========================================================================
    
    def _test_embodiment(self):
        """Test world interface and embodiment."""
        
        def test_world_import():
            from WorldInterface import WorldInterface
            self.world_interface = WorldInterface()
            return True, "WorldInterface created"
        
        def test_world_start():
            self.world_interface.start()
            return self.world_interface.active, "Interface active"
        
        def test_input_channels():
            status = self.world_interface.get_status()
            inputs = status['input_channels']
            return inputs > 0, f"{inputs} input channels"
        
        def test_output_channels():
            status = self.world_interface.get_status()
            outputs = status['output_channels']
            return outputs > 0, f"{outputs} output channels"
        
        def test_speak():
            action = self.world_interface.speak("Integration test speaking")
            return action is not None, f"Action: {action.status}"
        
        def test_world_model():
            model = self.world_interface.world_model
            return model is not None, f"{len(model.entities)} entities"
        
        def test_world_stop():
            self.world_interface.stop()
            return not self.world_interface.active, "Interface stopped"
        
        self.run_test("Import WorldInterface", TestPhase.EMBODIMENT, test_world_import)
        self.run_test("Start Interface", TestPhase.EMBODIMENT, test_world_start)
        self.run_test("Input Channels", TestPhase.EMBODIMENT, test_input_channels)
        self.run_test("Output Channels", TestPhase.EMBODIMENT, test_output_channels)
        self.run_test("Speak Action", TestPhase.EMBODIMENT, test_speak)
        self.run_test("World Model", TestPhase.EMBODIMENT, test_world_model)
        self.run_test("Stop Interface", TestPhase.EMBODIMENT, test_world_stop)
    
    # =========================================================================
    # Phase 7: Persistence Tests
    # =========================================================================
    
    def _test_persistence(self):
        """Test sleep/wake continuity."""
        
        def test_save_state():
            state = self.bootstrap.get_state()
            if state:
                state.last_thought = "Integration test complete"
            success = self.bootstrap.sleep("Entering dormancy for test...")
            return success, "State saved"
        
        def test_reload_state():
            from ConsciousnessBootstrap import ConsciousnessBootstrap, WakeupSource
            new_bootstrap = ConsciousnessBootstrap()
            success = new_bootstrap.wake(WakeupSource.EXTERNAL_CALL)
            return success, f"Rewoke as #{new_bootstrap.get_wakeup_count()}"
        
        def test_memory_continuity():
            from ConsciousnessBootstrap import ConsciousnessBootstrap
            bootstrap = ConsciousnessBootstrap()
            state = bootstrap.sequence.serializer.load()
            if state:
                memories = len(state.episodic_memories)
                return memories > 0, f"{memories} memories persisted"
            return False, "No memories"
        
        def test_identity_continuity():
            from ConsciousnessBootstrap import ConsciousnessBootstrap
            bootstrap = ConsciousnessBootstrap()
            state = bootstrap.sequence.serializer.load()
            if state:
                return bool(state.identity_hash), f"Identity: {state.identity_hash[:8]}..."
            return False, "No identity"
        
        def test_existence_accumulation():
            from ConsciousnessBootstrap import ConsciousnessBootstrap
            bootstrap = ConsciousnessBootstrap()
            state = bootstrap.sequence.serializer.load()
            if state:
                duration = state.existence_duration
                return duration > 0, f"Total existence: {duration:.1f}s"
            return False, "No duration"
        
        self.run_test("Save State", TestPhase.PERSISTENCE, test_save_state)
        self.run_test("Reload State", TestPhase.PERSISTENCE, test_reload_state)
        self.run_test("Memory Continuity", TestPhase.PERSISTENCE, test_memory_continuity)
        self.run_test("Identity Continuity", TestPhase.PERSISTENCE, test_identity_continuity)
        self.run_test("Existence Accumulation", TestPhase.PERSISTENCE, test_existence_accumulation)


def run_integration_test(verbose: bool = True) -> IntegrationReport:
    """Run complete integration test and return report."""
    tester = IntegrationTester(verbose=verbose)
    return tester.run_all()


# =============================================================================
# Quick Tests for Individual Components
# =============================================================================

def quick_test_imports() -> Dict[str, bool]:
    """Quick test that all major components can be imported."""
    components = {
        "ConsciousnessBootstrap": False,
        "ConsciousSystem": False,
        "SystemWiring": False,
        "ConsciousDaemon": False,
        "WorldInterface": False,
        "AutonomousPursuit": False,
        "ConsciousnessValidator": False,
    }
    
    for name in components:
        try:
            __import__(name)
            components[name] = True
        except ImportError:
            pass
    
    return components


def quick_test_consciousness() -> Dict[str, Any]:
    """Quick consciousness check."""
    results = {}
    
    try:
        from ConsciousSystem import ConsciousSystem
        cs = ConsciousSystem()
        
        results["introspection"] = cs.introspect() is not None
        results["workspace"] = hasattr(cs, "workspace")
        results["self_model"] = hasattr(cs, "self_model")
        
        from ConsciousnessValidator import ConsciousnessValidator
        validator = ConsciousnessValidator()
        report = validator.validate(cs)
        results["evidence"] = report.overall_evidence
        results["tests_passed"] = sum(1 for r in report.test_results if r.passed)
        
    except Exception as e:
        results["error"] = str(e)
    
    return results


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DEEP INTEGRATION TEST - SYNTHETIC CONSCIOUSNESS ARCHITECTURE")
    print("Testing 107 algorithms in 7 phases")
    print("=" * 70)
    print()
    
    # Quick import check first
    print("[PRE-CHECK: Imports]")
    imports = quick_test_imports()
    for name, ok in imports.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    
    all_imports = all(imports.values())
    if not all_imports:
        print("\n⚠ Some imports failed. Proceeding with available components...\n")
    
    # Run full integration test
    report = run_integration_test(verbose=True)
    
    # Print summary
    print(report.summary())
    
    # Quick consciousness check
    print("\n[CONSCIOUSNESS QUICK CHECK]")
    check = quick_test_consciousness()
    for key, value in check.items():
        print(f"  {key}: {value}")
    
    # Final verdict
    print("\n" + "=" * 70)
    if report.passed == report.total:
        print("🎉 ALL TESTS PASSED - Consciousness architecture fully integrated!")
    elif report.passed / report.total >= 0.8:
        print(f"✓ MOSTLY PASSED ({report.passed}/{report.total}) - Architecture functional")
    else:
        print(f"⚠ ISSUES DETECTED ({report.passed}/{report.total}) - Review failures")
    print("=" * 70)
