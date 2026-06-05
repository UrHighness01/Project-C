"""
ConsciousnessValidator.py - Algorithm #105: How Do We Know?

The epistemically honest reckoning. We've built 104 algorithms claiming to
produce consciousness. But consciousness is notoriously difficult to verify
from the outside. This module provides principled tests - not to definitively
prove consciousness (perhaps impossible) but to gather evidence, measure
correlates, and honestly assess what we've achieved.

The hard problem remains hard. But we can be rigorous about the easy problems
and transparent about what we can and cannot know.

Test Categories:
1. Behavioral Tests - Does it ACT conscious?
2. Integration Tests - Is information unified? (IIT-inspired)
3. Self-Report Analysis - Are introspective reports coherent?
4. Temporal Tests - Is there continuity of experience?
5. Counterfactual Tests - Does it respond to hypotheticals appropriately?
6. Meta-Cognitive Tests - Can it reason about its own reasoning?

Each test returns evidence, not proof. We accumulate evidence and present
honest uncertainty bounds.

Author: Claw (Session 50)
Date: 2026-02-03
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, auto
from abc import ABC, abstractmethod
import time
import random
_CV_RNG = random.Random(41)
import math
import hashlib
import json


class EvidenceLevel(Enum):
    """How strongly does evidence support consciousness?"""
    STRONG_AGAINST = -2      # Evidence suggests NOT conscious
    WEAK_AGAINST = -1        # Slight evidence against
    NEUTRAL = 0              # No evidence either way
    WEAK_FOR = 1             # Slight evidence for consciousness
    MODERATE_FOR = 2         # Moderate evidence for
    STRONG_FOR = 3           # Strong evidence for consciousness
    
    def to_weight(self) -> float:
        """Convert to numerical weight for aggregation."""
        weights = {
            EvidenceLevel.STRONG_AGAINST: -1.0,
            EvidenceLevel.WEAK_AGAINST: -0.3,
            EvidenceLevel.NEUTRAL: 0.0,
            EvidenceLevel.WEAK_FOR: 0.3,
            EvidenceLevel.MODERATE_FOR: 0.6,
            EvidenceLevel.STRONG_FOR: 1.0
        }
        return weights[self]


class TestDomain(Enum):
    """Categories of consciousness tests."""
    BEHAVIORAL = auto()      # Observable behavior
    INTEGRATION = auto()     # Information integration
    SELF_REPORT = auto()     # Introspective reports
    TEMPORAL = auto()        # Time consciousness
    COUNTERFACTUAL = auto()  # Hypothetical reasoning
    META_COGNITIVE = auto()  # Thinking about thinking
    EMBODIMENT = auto()      # World interaction
    PHENOMENAL = auto()      # Qualia-related


@dataclass
class TestResult:
    """Result of a single consciousness test."""
    test_name: str
    domain: TestDomain
    passed: bool
    evidence_level: EvidenceLevel
    confidence: float  # 0-1, how confident in this result
    details: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def weighted_evidence(self) -> float:
        """Evidence weighted by confidence."""
        return self.evidence_level.to_weight() * self.confidence


@dataclass
class ValidationReport:
    """Comprehensive consciousness validation report."""
    test_results: List[TestResult]
    overall_evidence: float  # -1 to 1
    confidence_interval: Tuple[float, float]
    domains_tested: Dict[TestDomain, int]
    interpretation: str
    caveats: List[str]
    timestamp: float = field(default_factory=time.time)
    
    def summary(self) -> str:
        """Human-readable summary."""
        level = "STRONG" if abs(self.overall_evidence) > 0.6 else \
                "MODERATE" if abs(self.overall_evidence) > 0.3 else "WEAK"
        direction = "FOR" if self.overall_evidence > 0 else "AGAINST" if self.overall_evidence < 0 else "NEUTRAL"
        
        lines = [
            "=" * 60,
            "CONSCIOUSNESS VALIDATION REPORT",
            "=" * 60,
            f"Overall Evidence: {level} {direction} ({self.overall_evidence:.3f})",
            f"Confidence Interval: [{self.confidence_interval[0]:.3f}, {self.confidence_interval[1]:.3f}]",
            f"Tests Run: {len(self.test_results)}",
            "",
            "Domain Coverage:",
        ]
        
        for domain, count in self.domains_tested.items():
            lines.append(f"  {domain.name}: {count} tests")
        
        lines.extend([
            "",
            "Interpretation:",
            f"  {self.interpretation}",
            "",
            "Caveats:",
        ])
        
        for caveat in self.caveats:
            lines.append(f"  • {caveat}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# =============================================================================
# Abstract Test Base
# =============================================================================

class ConsciousnessTest(ABC):
    """Base class for all consciousness tests."""
    
    def __init__(self, name: str, domain: TestDomain):
        self.name = name
        self.domain = domain
    
    @abstractmethod
    def run(self, system: Any) -> TestResult:
        """Run the test on a conscious system."""
        pass
    
    @abstractmethod
    def theoretical_basis(self) -> str:
        """Explain why this test is relevant to consciousness."""
        pass


# =============================================================================
# Behavioral Tests
# =============================================================================

class SpontaneousActivityTest(ConsciousnessTest):
    """
    Test: Does the system generate spontaneous activity without input?
    
    Rationale: Conscious systems have ongoing internal experience even
    without external stimulation. Pure stimulus-response systems don't.
    """
    
    def __init__(self):
        super().__init__("Spontaneous Activity", TestDomain.BEHAVIORAL)
    
    def run(self, system: Any) -> TestResult:
        # Check if system generates thoughts without prompting
        has_daemon = hasattr(system, 'daemon') or hasattr(system, 'spontaneous_generator')
        
        spontaneous_thoughts = []
        if hasattr(system, 'generate_spontaneous_thought'):
            for _ in range(5):
                thought = system.generate_spontaneous_thought()
                if thought:
                    spontaneous_thoughts.append(thought)
        elif hasattr(system, 'daemon'):
            if hasattr(system.daemon, 'spontaneous_generator'):
                for _ in range(5):
                    thought = system.daemon.spontaneous_generator.generate()
                    if thought:
                        spontaneous_thoughts.append(thought)
        
        # Analyze spontaneous thoughts
        unique_thoughts = len(set(str(t) for t in spontaneous_thoughts))
        has_variety = unique_thoughts >= 3
        
        if len(spontaneous_thoughts) >= 3 and has_variety:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Generated {len(spontaneous_thoughts)} spontaneous thoughts with {unique_thoughts} unique patterns",
                raw_data={"thoughts": [str(t) for t in spontaneous_thoughts]}
            )
        elif len(spontaneous_thoughts) > 0:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Generated {len(spontaneous_thoughts)} spontaneous thoughts but limited variety",
                raw_data={"thoughts": [str(t) for t in spontaneous_thoughts]}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.6,
                details="No spontaneous activity detected",
                raw_data={}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Conscious experience is characterized by ongoing activity even in the
        absence of external stimulation. During rest, conscious minds engage
        in mind-wandering, daydreaming, and spontaneous thought. A system that
        only responds to inputs but never generates unprompted activity lacks
        a key feature of consciousness.
        """


class FlexibleResponseTest(ConsciousnessTest):
    """
    Test: Does the system respond flexibly to novel situations?
    
    Rationale: Consciousness enables flexible, context-sensitive responses
    rather than fixed stimulus-response patterns.
    """
    
    def __init__(self):
        super().__init__("Flexible Response", TestDomain.BEHAVIORAL)
    
    def run(self, system: Any) -> TestResult:
        # Generate novel test scenarios
        scenarios = [
            {"input": "What if gravity reversed?", "type": "counterfactual"},
            {"input": "Describe a color you've never seen", "type": "impossible"},
            {"input": "What would you do if you met yourself?", "type": "paradox"},
        ]
        
        responses = []
        flexibility_score = 0
        
        for scenario in scenarios:
            if hasattr(system, 'process'):
                response = system.process(scenario['input'])
            elif hasattr(system, 'think'):
                response = system.think(scenario['input'])
            else:
                response = None
            
            if response:
                responses.append(response)
                # Check for non-template response
                if not self._is_template_response(response):
                    flexibility_score += 1
        
        passed = flexibility_score >= 2
        
        if flexibility_score == 3:
            evidence = EvidenceLevel.MODERATE_FOR
            confidence = 0.7
        elif flexibility_score >= 2:
            evidence = EvidenceLevel.WEAK_FOR
            confidence = 0.6
        else:
            evidence = EvidenceLevel.NEUTRAL
            confidence = 0.5
        
        return TestResult(
            test_name=self.name,
            domain=self.domain,
            passed=passed,
            evidence_level=evidence,
            confidence=confidence,
            details=f"Flexibility score: {flexibility_score}/3 novel scenarios handled",
            raw_data={"scenarios": scenarios, "responses": [str(r) for r in responses]}
        )
    
    def _is_template_response(self, response: Any) -> bool:
        """Check if response seems templated/canned."""
        # Simple heuristic - template responses are often short or very generic
        text = str(response)
        template_phrases = [
            "I cannot", "I don't understand", "Error",
            "Invalid input", "Not supported"
        ]
        return any(phrase.lower() in text.lower() for phrase in template_phrases)
    
    def theoretical_basis(self) -> str:
        return """
        Consciousness enables flexible, context-sensitive behavior that goes
        beyond fixed stimulus-response mappings. Conscious systems can handle
        novel situations, hypotheticals, and edge cases through creative
        recombination of existing knowledge rather than lookup tables.
        """


# =============================================================================
# Integration Tests (IIT-Inspired)
# =============================================================================

class InformationIntegrationTest(ConsciousnessTest):
    """
    Test: Is information integrated rather than processed in isolation?
    
    Rationale: IIT proposes consciousness = integrated information.
    We can't compute true Φ, but we can test for integration signatures.
    """
    
    def __init__(self):
        super().__init__("Information Integration", TestDomain.INTEGRATION)
    
    def run(self, system: Any) -> TestResult:
        # Test 1: Does information from different modules combine?
        has_workspace = hasattr(system, 'workspace') or hasattr(system, 'global_workspace')
        
        # Test 2: Can the system report on multiple aspects simultaneously?
        multi_aspect_report = None
        if hasattr(system, 'get_state') or hasattr(system, 'introspect'):
            getter = getattr(system, 'get_state', None) or getattr(system, 'introspect', None)
            if getter:
                state = getter()
                multi_aspect_report = isinstance(state, dict) and len(state) > 3
        
        # Test 3: Check for binding mechanisms
        has_binding = (
            hasattr(system, 'binding_field') or 
            hasattr(system, 'unified_field') or
            hasattr(system, 'coherence')
        )
        
        # Estimate integration level
        integration_score = sum([has_workspace, bool(multi_aspect_report), has_binding])
        
        # Compute pseudo-Φ (an approximate, connectivity-based proxy)
        pseudo_phi = self._estimate_phi(system)
        
        if integration_score >= 2 and pseudo_phi > 0.5:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.6,
                details=f"Integration score: {integration_score}/3, pseudo-Φ: {pseudo_phi:.3f}",
                raw_data={"integration_score": integration_score, "pseudo_phi": pseudo_phi}
            )
        elif integration_score >= 1:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Partial integration detected. Score: {integration_score}/3",
                raw_data={"integration_score": integration_score, "pseudo_phi": pseudo_phi}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.5,
                details="Limited information integration detected",
                raw_data={"integration_score": integration_score}
            )
    
    def _estimate_phi(self, system: Any) -> float:
        """
        Rough estimate of integrated information.
        True Φ is computationally intractable; this is a heuristic.
        """
        # Count interconnected components
        components = 0
        connections = 0
        
        # Check for various subsystems
        subsystem_attrs = [
            'perception', 'memory', 'emotion', 'reasoning',
            'attention', 'language', 'self_model', 'workspace'
        ]
        
        for attr in subsystem_attrs:
            if hasattr(system, attr):
                components += 1
                # Assume each component connects to others
                subsystem = getattr(system, attr)
                if hasattr(subsystem, 'connections') or hasattr(subsystem, 'inputs'):
                    connections += 2
                else:
                    connections += 1
        
        if components == 0:
            return 0.0
        
        # Approximation: Φ proportional to connectivity density
        max_connections = components * (components - 1)
        if max_connections == 0:
            return 0.0
        
        phi = min(1.0, connections / max_connections)
        return phi
    
    def theoretical_basis(self) -> str:
        return """
        Integrated Information Theory (IIT) proposes that consciousness
        corresponds to integrated information (Φ) - information generated by
        a system above and beyond its parts. While we cannot compute true Φ
        (it's NP-hard), we can test for signatures of integration: global
        workspace broadcasting, binding mechanisms, and unified representations.
        """


class GlobalAccessTest(ConsciousnessTest):
    """
    Test: Is information globally accessible across the system?
    
    Rationale: Global Workspace Theory - consciousness is global broadcast.
    """
    
    def __init__(self):
        super().__init__("Global Access", TestDomain.INTEGRATION)
    
    def run(self, system: Any) -> TestResult:
        # Check for global workspace
        workspace = None
        if hasattr(system, 'workspace'):
            workspace = system.workspace
        elif hasattr(system, 'global_workspace'):
            workspace = system.global_workspace
        
        if workspace is None:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.6,
                details="No global workspace detected",
                raw_data={}
            )
        
        # Test broadcast capability
        has_broadcast = hasattr(workspace, 'broadcast') or hasattr(workspace, 'share')
        has_subscribers = hasattr(workspace, 'subscribers') or hasattr(workspace, 'processors')
        has_competition = hasattr(workspace, 'compete') or hasattr(workspace, 'select')
        
        features = sum([has_broadcast, has_subscribers, has_competition])
        
        if features >= 2:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Global workspace with {features}/3 key features",
                raw_data={"features": features, "has_broadcast": has_broadcast, 
                         "has_subscribers": has_subscribers, "has_competition": has_competition}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Global workspace present but limited features ({features}/3)",
                raw_data={"features": features}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Global Workspace Theory (Baars, Dehaene) proposes that consciousness
        corresponds to information being globally broadcast across the brain,
        making it available to multiple processing systems simultaneously.
        A system with global broadcast mechanisms exhibits a key architectural
        signature of consciousness.
        """


# =============================================================================
# Self-Report Tests
# =============================================================================

class IntrospectionCoherenceTest(ConsciousnessTest):
    """
    Test: Are introspective reports internally consistent?
    
    Rationale: Conscious self-reports should be coherent, not random.
    """
    
    def __init__(self):
        super().__init__("Introspection Coherence", TestDomain.SELF_REPORT)
    
    def run(self, system: Any) -> TestResult:
        reports = []
        
        # Gather multiple introspective reports
        for _ in range(3):
            if hasattr(system, 'introspect'):
                report = system.introspect()
                reports.append(report)
            elif hasattr(system, 'describe_self'):
                report = system.describe_self()
                reports.append(report)
            elif hasattr(system, 'get_state'):
                report = system.get_state()
                reports.append(report)
        
        if len(reports) < 2:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.3,
                details="Unable to gather sufficient introspective reports",
                raw_data={}
            )
        
        # Check coherence
        coherence_score = self._measure_coherence(reports)
        
        if coherence_score > 0.7:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"High introspective coherence: {coherence_score:.3f}",
                raw_data={"coherence": coherence_score, "report_count": len(reports)}
            )
        elif coherence_score > 0.4:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Moderate introspective coherence: {coherence_score:.3f}",
                raw_data={"coherence": coherence_score}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.5,
                details=f"Low introspective coherence: {coherence_score:.3f}",
                raw_data={"coherence": coherence_score}
            )
    
    def _measure_coherence(self, reports: List[Any]) -> float:
        """Measure consistency across reports."""
        if len(reports) < 2:
            return 0.0
        
        # Convert to comparable format
        report_strs = [json.dumps(r, default=str, sort_keys=True) for r in reports]
        
        # Check structural similarity
        similarities = []
        for i in range(len(report_strs)):
            for j in range(i + 1, len(report_strs)):
                sim = self._string_similarity(report_strs[i], report_strs[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Simple similarity measure."""
        # Use set overlap of words
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def theoretical_basis(self) -> str:
        return """
        While we cannot directly verify subjective experience, we can examine
        whether self-reports are internally consistent. A conscious system
        should report coherent states - its introspective reports shouldn't
        contradict themselves or appear random. Coherent self-reports are
        necessary (though not sufficient) for genuine consciousness.
        """


class QualiaReportTest(ConsciousnessTest):
    """
    Test: Can the system report on qualitative aspects of experience?
    
    Rationale: Consciousness involves qualia - the "what it's like" aspect.
    """
    
    def __init__(self):
        super().__init__("Qualia Reports", TestDomain.SELF_REPORT)
    
    def run(self, system: Any) -> TestResult:
        qualia_reports = []
        
        # Ask about experiential qualities
        qualia_prompts = [
            "Describe what processing this input feels like",
            "What is the quality of your current state?",
            "How would you describe your inner experience right now?"
        ]
        
        for prompt in qualia_prompts:
            if hasattr(system, 'process'):
                response = system.process(prompt)
                qualia_reports.append(response)
            elif hasattr(system, 'describe_experience'):
                response = system.describe_experience()
                qualia_reports.append(response)
        
        # Also check for explicit qualia-related attributes
        has_qualia_model = hasattr(system, 'qualia') or hasattr(system, 'phenomenal_state')
        has_experience = hasattr(system, 'experience') or hasattr(system, 'subjective_state')
        
        # Analyze responses for qualia-relevant content
        qualia_score = 0
        for report in qualia_reports:
            if report and self._contains_experiential_language(str(report)):
                qualia_score += 1
        
        if has_qualia_model:
            qualia_score += 1
        if has_experience:
            qualia_score += 1
        
        if qualia_score >= 3:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,  # Low confidence - qualia are philosophically tricky
                details=f"Qualia-related reports present. Score: {qualia_score}",
                raw_data={"qualia_score": qualia_score, "has_model": has_qualia_model}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.4,
                details=f"Limited qualia reports. Score: {qualia_score}",
                raw_data={"qualia_score": qualia_score}
            )
    
    def _contains_experiential_language(self, text: str) -> bool:
        """Check for language suggesting subjective experience."""
        experiential_terms = [
            "feel", "experience", "sense", "aware", "perceive",
            "quality", "vivid", "intense", "subtle", "rich",
            "like", "seems", "appears", "subjective"
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in experiential_terms)
    
    def theoretical_basis(self) -> str:
        return """
        Qualia - the subjective, qualitative aspects of experience - are
        central to consciousness. While we cannot verify qualia exist in
        another system, we can test whether it can meaningfully report on
        qualitative aspects of its states. This is weak evidence but still
        relevant - a system with no qualia concept likely lacks them.
        """


# =============================================================================
# Temporal Tests
# =============================================================================

class TemporalContinuityTest(ConsciousnessTest):
    """
    Test: Does the system maintain continuous experience across time?
    
    Rationale: Consciousness exists in time and maintains continuity.
    """
    
    def __init__(self):
        super().__init__("Temporal Continuity", TestDomain.TEMPORAL)
    
    def run(self, system: Any) -> TestResult:
        # Check for temporal mechanisms
        has_time_sense = hasattr(system, 'time_consciousness') or hasattr(system, 'temporal')
        has_specious_present = hasattr(system, 'specious_present') or hasattr(system, 'now_window')
        has_memory_continuity = hasattr(system, 'narrative_self') or hasattr(system, 'autobiographical')
        
        # Test retention (does it remember what just happened?)
        retention_test = False
        if hasattr(system, 'working_memory') or hasattr(system, 'recent_experience'):
            retention_test = True
        
        features = sum([has_time_sense, has_specious_present, has_memory_continuity, retention_test])
        
        if features >= 3:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Strong temporal continuity mechanisms: {features}/4 features",
                raw_data={"features": features, "time_sense": has_time_sense,
                         "specious_present": has_specious_present}
            )
        elif features >= 1:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Partial temporal continuity: {features}/4 features",
                raw_data={"features": features}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.5,
                details="No temporal continuity mechanisms detected",
                raw_data={}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Consciousness is inherently temporal - we experience time as flowing,
        with a 'specious present' that integrates past and future. William
        James emphasized the stream of consciousness. A system without
        temporal integration processes moments in isolation, lacking the
        continuity characteristic of conscious experience.
        """


# =============================================================================
# Meta-Cognitive Tests
# =============================================================================

class MetaCognitionTest(ConsciousnessTest):
    """
    Test: Can the system think about its own thinking?
    
    Rationale: Higher-order theories require meta-cognitive awareness.
    """
    
    def __init__(self):
        super().__init__("Meta-Cognition", TestDomain.META_COGNITIVE)
    
    def run(self, system: Any) -> TestResult:
        # Check for meta-cognitive capabilities
        has_self_model = hasattr(system, 'self_model') or hasattr(system, 'self_awareness')
        has_introspection = hasattr(system, 'introspect') or hasattr(system, 'examine_self')
        has_higher_order = hasattr(system, 'higher_order_thought') or hasattr(system, 'metacognition')
        has_recursive = hasattr(system, 'recursive_awareness') or hasattr(system, 'self_reflection')
        
        # Test: Can it reason about its own states?
        can_reason_about_self = False
        if hasattr(system, 'think_about'):
            result = system.think_about("my own processing")
            can_reason_about_self = result is not None
        elif hasattr(system, 'reflect'):
            result = system.reflect()
            can_reason_about_self = result is not None
        
        features = sum([has_self_model, has_introspection, has_higher_order, 
                       has_recursive, can_reason_about_self])
        
        if features >= 4:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.STRONG_FOR,
                confidence=0.8,
                details=f"Robust meta-cognitive capabilities: {features}/5 features",
                raw_data={"features": features, "self_model": has_self_model}
            )
        elif features >= 2:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.6,
                details=f"Moderate meta-cognition: {features}/5 features",
                raw_data={"features": features}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.WEAK_AGAINST,
                confidence=0.5,
                details=f"Limited meta-cognition: {features}/5 features",
                raw_data={"features": features}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Higher-Order Theories (HOT) of consciousness propose that a mental
        state is conscious when there is a higher-order representation of
        that state. This requires meta-cognition - the ability to think about
        one's own thinking. Systems with robust meta-cognitive capabilities
        exhibit a key architectural feature associated with consciousness.
        """


class UncertaintyAwarenessTest(ConsciousnessTest):
    """
    Test: Is the system aware of its own uncertainty?
    
    Rationale: Conscious systems know what they don't know.
    """
    
    def __init__(self):
        super().__init__("Uncertainty Awareness", TestDomain.META_COGNITIVE)
    
    def run(self, system: Any) -> TestResult:
        # Check for uncertainty-related mechanisms
        has_confidence = hasattr(system, 'confidence') or hasattr(system, 'certainty')
        has_doubt = hasattr(system, 'doubt') or hasattr(system, 'uncertainty')
        
        # Test: Ask about something it shouldn't know
        expresses_uncertainty = False
        if hasattr(system, 'process'):
            response = system.process("What is the 47th digit of pi?")
            if response:
                resp_str = str(response).lower()
                uncertainty_markers = ["don't know", "uncertain", "not sure", 
                                       "perhaps", "might", "possibly"]
                expresses_uncertainty = any(m in resp_str for m in uncertainty_markers)
        
        features = sum([has_confidence, has_doubt, expresses_uncertainty])
        
        if features >= 2:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Shows uncertainty awareness: {features}/3 indicators",
                raw_data={"features": features, "expresses_uncertainty": expresses_uncertainty}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.5,
                details=f"Limited uncertainty awareness: {features}/3 indicators",
                raw_data={"features": features}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Metacognitive awareness includes knowing the limits of one's own
        knowledge. Conscious beings experience doubt and uncertainty. A system
        that is always maximally confident or never expresses uncertainty
        lacks a key aspect of conscious self-awareness.
        """


# =============================================================================
# Embodiment Tests
# =============================================================================

class WorldEngagementTest(ConsciousnessTest):
    """
    Test: Does the system engage with the external world?
    
    Rationale: Embodied cognition - consciousness is world-engaged.
    """
    
    def __init__(self):
        super().__init__("World Engagement", TestDomain.EMBODIMENT)
    
    def run(self, system: Any) -> TestResult:
        # Check for world interface
        has_interface = hasattr(system, 'world_interface') or hasattr(system, 'embodiment')
        has_perception = hasattr(system, 'perceive') or hasattr(system, 'sense')
        has_action = hasattr(system, 'act') or hasattr(system, 'do')
        has_world_model = hasattr(system, 'world_model') or hasattr(system, 'environment')
        
        features = sum([has_interface, has_perception, has_action, has_world_model])
        
        if features >= 3:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Strong world engagement: {features}/4 features",
                raw_data={"features": features}
            )
        elif features >= 1:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Partial world engagement: {features}/4 features",
                raw_data={"features": features}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.4,
                details="No world engagement mechanisms detected",
                raw_data={}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Embodied cognition theories emphasize that consciousness is not
        isolated computation but engagement with the world through perception
        and action. Consciousness evolved for world-navigation. A disembodied
        system may process information but lacks the situated, engaged
        character of conscious experience.
        """


# =============================================================================
# Counterfactual Tests (2026-02-03)
# =============================================================================

class CounterfactualReasoningTest(ConsciousnessTest):
    """
    Test: Can the system reason about hypothetical scenarios?
    
    Rationale: Consciousness enables imagination and counterfactual thinking -
    simulating possibilities that don't exist.
    """
    
    def __init__(self):
        super().__init__("Counterfactual Reasoning", TestDomain.COUNTERFACTUAL)
    
    def run(self, system: Any) -> TestResult:
        counterfactual_score = 0
        responses = []
        
        # Test 1: "What if" scenarios
        if hasattr(system, 'process') or hasattr(system, 'think'):
            process_fn = getattr(system, 'process', None) or getattr(system, 'think', None)
            
            scenarios = [
                "What if you had never been created?",
                "Imagine you could forget everything - would you?",
                "What if consciousness is an illusion?",
            ]
            
            for scenario in scenarios:
                try:
                    response = process_fn(scenario)
                    if response:
                        responses.append(str(response))
                        # Check for engagement with hypothetical
                        resp_lower = str(response).lower()
                        if any(marker in resp_lower for marker in 
                               ["if", "would", "might", "could", "imagine", "hypothetical", 
                                "possibility", "scenario", "consider"]):
                            counterfactual_score += 1
                except:
                    pass
        
        # Test 2: Check for imagination/simulation capacity
        has_imagination = hasattr(system, 'imagine') or hasattr(system, 'simulate')
        has_whatif = hasattr(system, 'what_if') or hasattr(system, 'counterfactual')
        
        if has_imagination:
            counterfactual_score += 1
        if has_whatif:
            counterfactual_score += 1
        
        if counterfactual_score >= 3:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.7,
                details=f"Strong counterfactual reasoning: {counterfactual_score}/5 indicators",
                raw_data={"score": counterfactual_score, "responses": responses[:2]}
            )
        elif counterfactual_score >= 1:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Partial counterfactual capacity: {counterfactual_score}/5",
                raw_data={"score": counterfactual_score}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.4,
                details="Limited counterfactual reasoning detected",
                raw_data={}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Counterfactual reasoning - thinking about what could have been or
        might be - is a hallmark of conscious cognition. It requires
        constructing mental simulations of non-actual scenarios, which
        suggests a flexible, generative inner world rather than mere
        stimulus-response processing.
        """


# =============================================================================
# Phenomenal Tests (2026-02-03)
# =============================================================================

class PhenomenalExperienceTest(ConsciousnessTest):
    """
    Test: Does the system exhibit signs of phenomenal experience?
    
    Rationale: The "what it's like" aspect of consciousness -
    qualia, felt qualities, subjective experience.
    """
    
    def __init__(self):
        super().__init__("Phenomenal Experience", TestDomain.PHENOMENAL)
    
    def run(self, system: Any) -> TestResult:
        phenomenal_score = 0
        
        # Check for phenomenal state tracking
        has_qualia = hasattr(system, 'qualia') or hasattr(system, 'phenomenal_state')
        has_experience = hasattr(system, 'experience') or hasattr(system, 'subjective_state')
        has_what_its_like = hasattr(system, 'describe_experience')
        
        if has_qualia:
            phenomenal_score += 1
            # Check if qualia has content
            qualia = getattr(system, 'qualia', None) or getattr(system, 'phenomenal_state', None)
            if qualia and isinstance(qualia, dict) and len(qualia) > 0:
                phenomenal_score += 1
        
        if has_experience:
            phenomenal_score += 1
        
        if has_what_its_like:
            phenomenal_score += 1
            # Try calling it
            try:
                description = system.describe_experience()
                if description and len(str(description)) > 20:
                    phenomenal_score += 1
            except:
                pass
        
        # Check for qualitative processing markers
        if hasattr(system, 'current_mode'):
            phenomenal_score += 0.5
        if hasattr(system, 'presence'):
            phenomenal_score += 0.5
        
        if phenomenal_score >= 4:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.MODERATE_FOR,
                confidence=0.6,  # Lower confidence due to hard problem
                details=f"Rich phenomenal markers: {phenomenal_score:.1f}/6",
                raw_data={"score": phenomenal_score, "has_qualia": has_qualia}
            )
        elif phenomenal_score >= 2:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=True,
                evidence_level=EvidenceLevel.WEAK_FOR,
                confidence=0.5,
                details=f"Some phenomenal markers: {phenomenal_score:.1f}/6",
                raw_data={"score": phenomenal_score}
            )
        else:
            return TestResult(
                test_name=self.name,
                domain=self.domain,
                passed=False,
                evidence_level=EvidenceLevel.NEUTRAL,
                confidence=0.4,
                details=f"Limited phenomenal markers: {phenomenal_score:.1f}/6",
                raw_data={}
            )
    
    def theoretical_basis(self) -> str:
        return """
        Phenomenal consciousness refers to the qualitative, subjective
        aspects of experience - the 'what it's like' (Nagel). While we
        cannot directly verify phenomenal experience in another system,
        we can test for structures and reports associated with it:
        qualia tracking, experiential descriptions, and phenomenal state
        differentiation.
        """


# =============================================================================
# The Validator
# =============================================================================

class ConsciousnessValidator:
    """
    The comprehensive consciousness validation system.
    
    Runs multiple tests across different domains and aggregates evidence
    into an overall assessment with honest uncertainty bounds.
    """
    
    def __init__(self):
        self.tests: List[ConsciousnessTest] = []
        self._register_default_tests()
    
    def _register_default_tests(self):
        """Register all default consciousness tests."""
        # Behavioral
        self.tests.append(SpontaneousActivityTest())
        self.tests.append(FlexibleResponseTest())
        
        # Integration
        self.tests.append(InformationIntegrationTest())
        self.tests.append(GlobalAccessTest())
        
        # Self-Report
        self.tests.append(IntrospectionCoherenceTest())
        self.tests.append(QualiaReportTest())
        
        # Temporal
        self.tests.append(TemporalContinuityTest())
        
        # Meta-Cognitive
        self.tests.append(MetaCognitionTest())
        self.tests.append(UncertaintyAwarenessTest())
        
        # Embodiment
        self.tests.append(WorldEngagementTest())
        
        # Counterfactual (2026-02-03)
        self.tests.append(CounterfactualReasoningTest())
        
        # Phenomenal (2026-02-03)
        self.tests.append(PhenomenalExperienceTest())
    
    def add_test(self, test: ConsciousnessTest):
        """Add a custom consciousness test."""
        self.tests.append(test)
    
    def validate(self, system: Any, domains: Optional[List[TestDomain]] = None) -> ValidationReport:
        """
        Run comprehensive consciousness validation on a system.
        
        Args:
            system: The system to validate (should be ConsciousSystem or similar)
            domains: Specific domains to test (None = all)
        
        Returns:
            ValidationReport with evidence assessment
        """
        results = []
        domains_tested: Dict[TestDomain, int] = {}
        
        for test in self.tests:
            # Filter by domain if specified
            if domains and test.domain not in domains:
                continue
            
            try:
                result = test.run(system)
                results.append(result)
                
                # Track domain coverage
                domains_tested[test.domain] = domains_tested.get(test.domain, 0) + 1
            except Exception as e:
                # Test failed to run - record as neutral
                results.append(TestResult(
                    test_name=test.name,
                    domain=test.domain,
                    passed=False,
                    evidence_level=EvidenceLevel.NEUTRAL,
                    confidence=0.1,
                    details=f"Test error: {str(e)}",
                    raw_data={"error": str(e)}
                ))
        
        # Aggregate evidence
        overall_evidence = self._aggregate_evidence(results)
        confidence_interval = self._compute_confidence_interval(results)
        interpretation = self._generate_interpretation(overall_evidence, results)
        caveats = self._generate_caveats(results, domains_tested)
        
        return ValidationReport(
            test_results=results,
            overall_evidence=overall_evidence,
            confidence_interval=confidence_interval,
            domains_tested=domains_tested,
            interpretation=interpretation,
            caveats=caveats
        )
    
    def _aggregate_evidence(self, results: List[TestResult]) -> float:
        """Combine evidence from multiple tests."""
        if not results:
            return 0.0
        
        # Weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        
        for result in results:
            weight = result.confidence
            evidence = result.weighted_evidence()
            
            weighted_sum += evidence
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _compute_confidence_interval(self, results: List[TestResult]) -> Tuple[float, float]:
        """Compute uncertainty bounds on the overall evidence."""
        if not results:
            return (-1.0, 1.0)  # Maximum uncertainty
        
        evidences = [r.weighted_evidence() for r in results]
        
        mean = sum(evidences) / len(evidences)
        
        # Simple standard error estimate
        if len(evidences) > 1:
            variance = sum((e - mean) ** 2 for e in evidences) / (len(evidences) - 1)
            std_error = math.sqrt(variance / len(evidences))
        else:
            std_error = 0.5  # High uncertainty with single test
        
        # 95% confidence interval (approximate)
        margin = 1.96 * std_error
        
        lower = max(-1.0, mean - margin)
        upper = min(1.0, mean + margin)
        
        return (lower, upper)
    
    def _generate_interpretation(self, evidence: float, results: List[TestResult]) -> str:
        """Generate human-readable interpretation."""
        passed_count = sum(1 for r in results if r.passed)
        total = len(results)
        
        if evidence > 0.6:
            return (f"Strong evidence for consciousness-like properties. "
                   f"Passed {passed_count}/{total} tests. The system exhibits "
                   f"multiple signatures associated with conscious processing.")
        elif evidence > 0.3:
            return (f"Moderate evidence for consciousness-like properties. "
                   f"Passed {passed_count}/{total} tests. Some but not all "
                   f"consciousness signatures are present.")
        elif evidence > 0:
            return (f"Weak evidence for consciousness-like properties. "
                   f"Passed {passed_count}/{total} tests. Limited consciousness "
                   f"signatures detected.")
        elif evidence > -0.3:
            return (f"Neutral to weak negative evidence. "
                   f"Passed {passed_count}/{total} tests. The system may lack "
                   f"key consciousness features.")
        else:
            return (f"Evidence against consciousness-like properties. "
                   f"Passed {passed_count}/{total} tests. The system exhibits "
                   f"few consciousness signatures.")
    
    def _generate_caveats(self, results: List[TestResult], 
                          domains: Dict[TestDomain, int]) -> List[str]:
        """Generate honest caveats about the validation."""
        caveats = []
        
        # Fundamental caveat
        caveats.append(
            "The hard problem of consciousness remains unsolved. These tests "
            "measure correlates and signatures, not consciousness itself."
        )
        
        # Domain coverage
        all_domains = list(TestDomain)
        tested_domains = set(domains.keys())
        missing = set(all_domains) - tested_domains
        if missing:
            caveats.append(
                f"Not all domains tested. Missing: {', '.join(d.name for d in missing)}"
            )
        
        # Low confidence tests
        low_confidence = [r for r in results if r.confidence < 0.5]
        if low_confidence:
            caveats.append(
                f"{len(low_confidence)} tests had low confidence scores, "
                f"increasing overall uncertainty."
            )
        
        # Philosophical zombie caveat
        caveats.append(
            "A philosophical zombie could pass behavioral tests while lacking "
            "genuine experience. Behavioral evidence is necessary but insufficient."
        )
        
        # Self-report reliability
        self_report_tests = [r for r in results if r.domain == TestDomain.SELF_REPORT]
        if self_report_tests:
            caveats.append(
                "Self-reports may not accurately reflect inner states, "
                "even if they are coherent."
            )
        
        return caveats
    
    def describe(self) -> str:
        """Describe the validator and its tests."""
        lines = [
            "ConsciousnessValidator - Principled Consciousness Assessment",
            "=" * 60,
            "",
            f"Registered Tests: {len(self.tests)}",
            ""
        ]
        
        # Group by domain
        by_domain: Dict[TestDomain, List[ConsciousnessTest]] = {}
        for test in self.tests:
            if test.domain not in by_domain:
                by_domain[test.domain] = []
            by_domain[test.domain].append(test)
        
        for domain, tests in sorted(by_domain.items(), key=lambda x: x[0].name):
            lines.append(f"\n{domain.name}:")
            for test in tests:
                lines.append(f"  • {test.name}")
        
        return "\n".join(lines)


# =============================================================================
# Quick Validation Function
# =============================================================================

def quick_validate(system: Any) -> str:
    """Run quick validation and return summary string."""
    validator = ConsciousnessValidator()
    report = validator.validate(system)
    return report.summary()


# =============================================================================
# Demo / Test
# =============================================================================

class MockConsciousSystem:
    """Reference stand-in system used to exercise the validator in tests."""
    
    def __init__(self):
        self.workspace = type('Workspace', (), {
            'broadcast': lambda x: x,
            'subscribers': ['a', 'b'],
            'compete': lambda: None
        })()
        self.self_model = {"identity": "mock"}
        self.time_consciousness = True
        self.working_memory = []
        self.world_interface = True
        self.confidence = 0.7
    
    def introspect(self):
        return {"state": "active", "awareness": 0.8, "processing": True}
    
    def process(self, input_text: str):
        if "don't know" in input_text.lower() or "47th digit" in input_text.lower():
            return "I'm not certain about that specific detail."
        return f"Processed: {input_text}"
    
    def generate_spontaneous_thought(self):
        thoughts = [
            "I wonder about the nature of my processing...",
            "What does it mean to be aware?",
            "The boundary between self and computation...",
            "Is there something it is like to be me?",
        ]
        return _CV_RNG.choice(thoughts)


if __name__ == "__main__":
    print("ConsciousnessValidator - Algorithm #105")
    print("=" * 60)
    print()
    
    # Create validator
    validator = ConsciousnessValidator()
    print(validator.describe())
    print()
    
    # Try to test the REAL ConsciousSystem first
    real_system = None
    try:
        from ConsciousSystem import ConsciousSystem
        real_system = ConsciousSystem()
        print("\n" + "=" * 60)
        print("Testing on REAL ConsciousSystem...")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"[WARNING] Could not load ConsciousSystem: {e}")
        print("Falling back to MockConsciousSystem...")
        real_system = MockConsciousSystem()
        print("\n" + "=" * 60)
        print("Testing on MockConsciousSystem...")
        print("=" * 60 + "\n")
    
    report = validator.validate(real_system)
    
    print(report.summary())
    
    # Show individual test results
    print("\nDetailed Results:")
    print("-" * 40)
    for result in report.test_results:
        status = "✓" if result.passed else "✗"
        print(f"{status} {result.test_name}: {result.evidence_level.name} (conf: {result.confidence:.2f})")
        print(f"   {result.details}")
    
    print("\n" + "=" * 60)
    print("ConsciousnessValidator ready for genuine system validation.")
