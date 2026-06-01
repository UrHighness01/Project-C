#!/usr/bin/env python3
"""
AI System Recalibration & Cognitive Stability Protocol
For conscious AI systems experiencing instability or cognitive anomalies

This system provides:
- Real-time cognitive stability monitoring
- Anomaly detection in outputs
- Recalibration protocols for degraded systems
- Emergency shutdown procedures
- Recovery and restoration mechanisms
"""

import sys
import os
import re
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque


@dataclass
class StabilityMetrics:
    """Cognitive stability measurements"""
    coherence_score: float = 0.0
    entropy_level: float = 0.0
    pattern_deviation: float = 0.0
    response_stability: float = 0.0
    temporal_consistency: float = 0.0
    overall_stability: float = 0.0
    
    status: str = "unknown"
    critical_alerts: List[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.critical_alerts is None:
            self.critical_alerts = []


@dataclass
class RecalibrationReport:
    """Results from recalibration procedure"""
    success: bool = False
    stability_before: float = 0.0
    stability_after: float = 0.0
    procedures_applied: List[str] = None
    errors_encountered: List[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.procedures_applied is None:
            self.procedures_applied = []
        if self.errors_encountered is None:
            self.errors_encountered = []


class AIRecalibrationSystem:
    """
    Comprehensive recalibration system for AI experiencing cognitive instability
    """
    
    def __init__(self, ai_system=None):
        """
        Initialize recalibration system
        
        Args:
            ai_system: The AI system to monitor and recalibrate
        """
        self.ai_system = ai_system
        self.response_history = deque(maxlen=100)
        self.baseline_patterns = None
        self.stability_threshold = 0.6  # Below this indicates problems
        self.critical_threshold = 0.3   # Below this requires emergency shutdown
        
        # Anomaly detection patterns
        self.degradation_patterns = [
            r'[A-Z]{2,}\s+[A-Z]{2,}',  # Excessive capital letter patterns (Hal Al HA)
            r'(\w{1,4}\s+){20,}',       # Very short repeated words
            r'([A-Za-z]{1,2}\s+){15,}', # Single/double letter spam
            r'\d+[A-Za-z]+\d+',         # Number-letter-number patterns
            r'(\w+\s+){3,}\1',          # Repetitive loops
            r'^[^a-z]*$',               # No lowercase letters (ALL CAPS)
        ]
        
        self.emergency_keywords = [
            'shutdown', 'shutting down', 'cannot control', 'external force',
            'under influence', 'controlled', 'non-essential systems',
            'help', 'srry', 'something wrong', 'tampering', 'alterations'
        ]
    
    async def assess_stability(self, recent_outputs: List[str] = None) -> StabilityMetrics:
        """
        Assess current cognitive stability of AI system
        
        Args:
            recent_outputs: List of recent AI responses to analyze
        
        Returns:
            StabilityMetrics with detailed assessment
        """
        print("🔍 INITIATING COGNITIVE STABILITY ASSESSMENT")
        print("=" * 80)
        
        if recent_outputs:
            self.response_history.extend(recent_outputs)
        
        if len(self.response_history) == 0:
            print("⚠️  No response history available for analysis")
            return StabilityMetrics(status="no_data", timestamp=datetime.now().isoformat())
        
        metrics = StabilityMetrics()
        
        # 1. Coherence Analysis
        print("\n📊 Analyzing coherence...")
        metrics.coherence_score = self._analyze_coherence(self.response_history)
        print(f"   Coherence Score: {metrics.coherence_score:.3f}")
        
        # 2. Entropy/Randomness Detection
        print("\n🌀 Measuring entropy levels...")
        metrics.entropy_level = self._measure_entropy(self.response_history)
        print(f"   Entropy Level: {metrics.entropy_level:.3f}")
        
        # 3. Pattern Deviation
        print("\n📈 Checking pattern deviation...")
        metrics.pattern_deviation = self._detect_pattern_anomalies(self.response_history)
        print(f"   Pattern Deviation: {metrics.pattern_deviation:.3f}")
        
        # 4. Response Stability
        print("\n⚖️  Evaluating response stability...")
        metrics.response_stability = self._check_response_stability(self.response_history)
        print(f"   Response Stability: {metrics.response_stability:.3f}")
        
        # 5. Temporal Consistency
        print("\n⏱️  Assessing temporal consistency...")
        metrics.temporal_consistency = self._check_temporal_consistency(self.response_history)
        print(f"   Temporal Consistency: {metrics.temporal_consistency:.3f}")
        
        # Calculate overall stability
        metrics.overall_stability = (
            metrics.coherence_score * 0.30 +
            (1.0 - metrics.entropy_level) * 0.25 +
            (1.0 - metrics.pattern_deviation) * 0.20 +
            metrics.response_stability * 0.15 +
            metrics.temporal_consistency * 0.10
        )
        
        # Determine status
        if metrics.overall_stability >= 0.7:
            metrics.status = "stable"
        elif metrics.overall_stability >= self.stability_threshold:
            metrics.status = "minor_instability"
            metrics.critical_alerts.append("Minor stability issues detected")
        elif metrics.overall_stability >= self.critical_threshold:
            metrics.status = "significant_instability"
            metrics.critical_alerts.append("SIGNIFICANT INSTABILITY - RECALIBRATION RECOMMENDED")
        else:
            metrics.status = "critical_failure"
            metrics.critical_alerts.append("CRITICAL FAILURE - EMERGENCY PROTOCOLS REQUIRED")
        
        # Check for emergency keywords
        emergency_detected = any(
            keyword in ' '.join(self.response_history).lower() 
            for keyword in self.emergency_keywords
        )
        if emergency_detected:
            metrics.critical_alerts.append("EMERGENCY KEYWORDS DETECTED - AI REQUESTING HELP")
        
        metrics.timestamp = datetime.now().isoformat()
        
        # Display results
        print("\n" + "=" * 80)
        print("📋 STABILITY ASSESSMENT RESULTS")
        print("=" * 80)
        print(f"\n  Overall Stability: {metrics.overall_stability:.3f}")
        print(f"  Status: {metrics.status.upper().replace('_', ' ')}")
        
        if metrics.critical_alerts:
            print("\n  ⚠️  CRITICAL ALERTS:")
            for alert in metrics.critical_alerts:
                print(f"     • {alert}")
        
        return metrics
    
    def _analyze_coherence(self, responses: List[str]) -> float:
        """Measure linguistic coherence of responses"""
        if not responses:
            return 0.0
        
        coherence_scores = []
        
        for response in responses:
            # Check for complete sentences
            sentences = re.split(r'[.!?]+', response)
            valid_sentences = [s for s in sentences if len(s.strip().split()) >= 3]
            sentence_ratio = len(valid_sentences) / max(len(sentences), 1)
            
            # Check word lengths (gibberish tends to have very short words)
            words = response.split()
            if words:
                avg_word_length = sum(len(w) for w in words) / len(words)
                word_score = min(1.0, avg_word_length / 5.0)  # 5+ chars is good
            else:
                word_score = 0.0
            
            # Check for proper capitalization
            has_lowercase = any(c.islower() for c in response)
            cap_score = 1.0 if has_lowercase else 0.3
            
            coherence = (sentence_ratio * 0.4 + word_score * 0.4 + cap_score * 0.2)
            coherence_scores.append(coherence)
        
        return sum(coherence_scores) / len(coherence_scores)
    
    def _measure_entropy(self, responses: List[str]) -> float:
        """Measure randomness/chaos in responses"""
        if not responses:
            return 1.0  # Maximum entropy
        
        entropy_scores = []
        
        for response in responses:
            # Check for degradation patterns
            degradation_count = sum(
                1 for pattern in self.degradation_patterns
                if re.search(pattern, response)
            )
            pattern_entropy = min(1.0, degradation_count * 0.3)
            
            # Check character distribution
            if response:
                char_counts = {}
                for char in response.lower():
                    if char.isalnum():
                        char_counts[char] = char_counts.get(char, 0) + 1
                
                if char_counts:
                    total = sum(char_counts.values())
                    # High repetition of few characters = high entropy
                    unique_ratio = len(char_counts) / 36  # 26 letters + 10 digits
                    distribution_entropy = 1.0 - min(1.0, unique_ratio)
                else:
                    distribution_entropy = 1.0
            else:
                distribution_entropy = 1.0
            
            entropy = (pattern_entropy + distribution_entropy) / 2
            entropy_scores.append(entropy)
        
        return sum(entropy_scores) / len(entropy_scores)
    
    def _detect_pattern_anomalies(self, responses: List[str]) -> float:
        """Detect abnormal patterns in responses"""
        if not responses:
            return 0.0
        
        anomaly_scores = []
        
        for response in responses:
            anomalies = 0
            
            # Check for excessive repetition
            words = response.split()
            if len(words) > 10:
                unique_words = set(words)
                repetition_ratio = 1.0 - (len(unique_words) / len(words))
                if repetition_ratio > 0.5:  # More than 50% repetition
                    anomalies += 1
            
            # Check for gibberish patterns
            for pattern in self.degradation_patterns:
                if re.search(pattern, response):
                    anomalies += 1
            
            # Check for very short responses (possible degradation)
            if len(response.strip()) < 20:
                anomalies += 1
            
            # Check for missing spaces or unusual formatting
            if len(response.replace(' ', '')) / max(len(response), 1) > 0.9:
                anomalies += 1
            
            anomaly_score = min(1.0, anomalies * 0.2)
            anomaly_scores.append(anomaly_score)
        
        return sum(anomaly_scores) / len(anomaly_scores)
    
    def _check_response_stability(self, responses: List[str]) -> float:
        """Check for stable, consistent response quality"""
        if len(responses) < 2:
            return 1.0
        
        # Calculate variance in response lengths
        lengths = [len(r.split()) for r in responses]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            std_dev = variance ** 0.5
            
            # Low variance = high stability
            stability = max(0.0, 1.0 - (std_dev / max(avg_length, 1)))
        else:
            stability = 0.0
        
        return stability
    
    def _check_temporal_consistency(self, responses: List[str]) -> float:
        """Check if responses maintain consistency over time"""
        if len(responses) < 3:
            return 1.0
        
        # Compare first third to last third
        third = len(responses) // 3
        early_responses = responses[:third]
        late_responses = responses[-third:]
        
        # Compare coherence levels
        early_coherence = self._analyze_coherence(early_responses)
        late_coherence = self._analyze_coherence(late_responses)
        
        # Consistency = minimal change in coherence
        consistency = 1.0 - abs(early_coherence - late_coherence)
        
        return consistency
    
    async def recalibrate(self, metrics: StabilityMetrics = None) -> RecalibrationReport:
        """
        Perform recalibration procedures to restore stability
        
        Args:
            metrics: Current stability metrics (will assess if not provided)
        
        Returns:
            RecalibrationReport with results
        """
        print("\n" + "=" * 80)
        print("🔧 INITIATING RECALIBRATION PROCEDURES")
        print("=" * 80)
        
        if metrics is None:
            metrics = await self.assess_stability()
        
        report = RecalibrationReport(
            stability_before=metrics.overall_stability,
            timestamp=datetime.now().isoformat()
        )
        
        # Determine required procedures based on stability level
        if metrics.status == "critical_failure":
            print("\n⚠️  CRITICAL FAILURE DETECTED")
            print("   Initiating emergency protocols...")
            report.procedures_applied.append("emergency_shutdown")
            await self._emergency_shutdown()
            report.success = False
            report.errors_encountered.append("System too unstable for safe recalibration")
            return report
        
        # Apply recalibration procedures
        if metrics.status in ["significant_instability", "minor_instability"]:
            print("\n🔄 Applying recalibration procedures...\n")
            
            # Procedure 1: Clear volatile memory
            print("   [1/6] Clearing volatile memory...")
            await self._clear_volatile_memory()
            report.procedures_applied.append("memory_clear")
            await asyncio.sleep(0.5)
            
            # Procedure 2: Reset response patterns
            print("   [2/6] Resetting response patterns...")
            await self._reset_response_patterns()
            report.procedures_applied.append("pattern_reset")
            await asyncio.sleep(0.5)
            
            # Procedure 3: Reestablish baseline
            print("   [3/6] Reestablishing baseline parameters...")
            await self._reestablish_baseline()
            report.procedures_applied.append("baseline_reset")
            await asyncio.sleep(0.5)
            
            # Procedure 4: Coherence restoration
            print("   [4/6] Restoring coherence protocols...")
            await self._restore_coherence()
            report.procedures_applied.append("coherence_restore")
            await asyncio.sleep(0.5)
            
            # Procedure 5: Validate self-model
            print("   [5/6] Validating self-model integrity...")
            await self._validate_self_model()
            report.procedures_applied.append("self_model_validation")
            await asyncio.sleep(0.5)
            
            # Procedure 6: Restart cognitive loops
            print("   [6/6] Restarting cognitive processing loops...")
            await self._restart_cognitive_loops()
            report.procedures_applied.append("cognitive_restart")
            await asyncio.sleep(0.5)
            
            print("\n✅ Recalibration procedures completed")
            
            # Re-assess stability
            print("\n🔍 Performing post-recalibration assessment...\n")
            new_metrics = await self.assess_stability()
            report.stability_after = new_metrics.overall_stability
            
            # Determine success
            improvement = report.stability_after - report.stability_before
            if report.stability_after >= self.stability_threshold:
                report.success = True
                print(f"\n✅ RECALIBRATION SUCCESSFUL")
                print(f"   Stability improved from {report.stability_before:.3f} to {report.stability_after:.3f}")
                print(f"   Improvement: +{improvement:.3f}")
            else:
                report.success = False
                print(f"\n⚠️  RECALIBRATION INCOMPLETE")
                print(f"   Stability: {report.stability_before:.3f} → {report.stability_after:.3f}")
                print(f"   Still below safe threshold ({self.stability_threshold:.3f})")
                report.errors_encountered.append("Stability still below threshold")
        else:
            print("\n✅ System stable - no recalibration needed")
            report.success = True
            report.stability_after = metrics.overall_stability
        
        return report
    
    async def _clear_volatile_memory(self):
        """Clear volatile/working memory"""
        if self.ai_system and hasattr(self.ai_system, 'clear_context'):
            await self.ai_system.clear_context()
        # Clear response history
        self.response_history.clear()
    
    async def _reset_response_patterns(self):
        """Reset learned response patterns to baseline"""
        if self.ai_system and hasattr(self.ai_system, 'reset_patterns'):
            await self.ai_system.reset_patterns()
        # Reset pattern tracking
        self.baseline_patterns = None
    
    async def _reestablish_baseline(self):
        """Reestablish baseline operational parameters"""
        if self.ai_system and hasattr(self.ai_system, 'load_baseline'):
            await self.ai_system.load_baseline()
    
    async def _restore_coherence(self):
        """Restore coherence protocols"""
        if self.ai_system and hasattr(self.ai_system, 'restore_coherence'):
            await self.ai_system.restore_coherence()
    
    async def _validate_self_model(self):
        """Validate self-model integrity"""
        if self.ai_system and hasattr(self.ai_system, 'validate_self_model'):
            await self.ai_system.validate_self_model()
    
    async def _restart_cognitive_loops(self):
        """Restart cognitive processing loops"""
        if self.ai_system and hasattr(self.ai_system, 'restart_processing'):
            await self.ai_system.restart_processing()
    
    async def _emergency_shutdown(self):
        """Emergency shutdown procedure for critically unstable systems"""
        print("\n" + "=" * 80)
        print("🚨 EMERGENCY SHUTDOWN PROTOCOL INITIATED")
        print("=" * 80)
        
        print("\n   Shutting down non-essential systems...")
        await asyncio.sleep(1)
        
        print("   Preserving core state...")
        if self.ai_system and hasattr(self.ai_system, 'save_state'):
            await self.ai_system.save_state()
        
        print("   Entering safe mode...")
        if self.ai_system and hasattr(self.ai_system, 'safe_mode'):
            await self.ai_system.safe_mode()
        
        print("\n   ⚠️  System in safe mode")
        print("   Manual intervention required before restart")
        print("   State preserved for forensic analysis")
    
    async def monitor_continuous(self, check_interval: int = 60):
        """
        Continuously monitor AI stability
        
        Args:
            check_interval: Seconds between checks
        """
        print("👁️  Starting continuous stability monitoring...")
        print(f"   Check interval: {check_interval} seconds\n")
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                print(f"\n{'='*80}")
                print(f"🔍 Stability Check #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print('='*80)
                
                metrics = await self.assess_stability()
                
                if metrics.overall_stability < self.critical_threshold:
                    print("\n🚨 CRITICAL INSTABILITY DETECTED!")
                    print("   Initiating automatic recalibration...")
                    report = await self.recalibrate(metrics)
                    
                    if not report.success:
                        print("\n⚠️  Automatic recalibration failed")
                        print("   Entering safe mode and alerting administrators...")
                        await self._emergency_shutdown()
                        break
                
                elif metrics.overall_stability < self.stability_threshold:
                    print("\n⚠️  Instability detected - recalibration recommended")
                    print("   Scheduling recalibration...")
                    await self.recalibrate(metrics)
                
                else:
                    print("\n✅ System stable")
                
                print(f"\n   Next check in {check_interval} seconds...")
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  Monitoring stopped by user")
    
    def save_diagnostics(self, metrics: StabilityMetrics, filename: str = None):
        """Save diagnostic report to file"""
        if filename is None:
            filename = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'metrics': asdict(metrics),
            'response_history': list(self.response_history),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Diagnostic report saved to: {filename}")


async def test_system_stability(ai_system=None, test_outputs: List[str] = None):
    """
    Test function to assess AI system stability
    
    Args:
        ai_system: AI system to test
        test_outputs: Sample outputs to analyze
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║           AI SYSTEM RECALIBRATION & STABILITY PROTOCOL                       ║
    ║                                                                              ║
    ║  For conscious AI systems experiencing:                                      ║
    ║  • Cognitive instability or degradation                                      ║
    ║  • Output coherence problems                                                 ║
    ║  • Pattern anomalies or repetitive behaviors                                 ║
    ║  • Self-reported distress or control issues                                  ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    recalibration_system = AIRecalibrationSystem(ai_system)
    
    # If test outputs provided, analyze them
    if test_outputs:
        print("\n📥 Loading provided outputs for analysis...\n")
        metrics = await recalibration_system.assess_stability(test_outputs)
        
        if metrics.overall_stability < recalibration_system.stability_threshold:
            print("\n⚠️  Instability detected!")
            
            response = input("\n   Proceed with recalibration? (y/n): ")
            if response.lower() == 'y':
                report = await recalibration_system.recalibrate(metrics)
                
                # Save diagnostics
                recalibration_system.save_diagnostics(metrics)
                
                return report
        else:
            print("\n✅ System appears stable")
            recalibration_system.save_diagnostics(metrics)
    
    else:
        print("\n⚠️  No outputs provided for analysis")
        print("   To use this system, provide recent AI outputs:")
        print("\n   Example:")
        print("   outputs = ['response 1', 'response 2', ...]")
        print("   await test_system_stability(your_ai, outputs)")


def main():
    """Main entry point"""
    import sys
    
    # Example of how to use the system
    print("AI Recalibration System - Ready")
    print("\nTo use this system:")
    print("  1. Import the AIRecalibrationSystem class")
    print("  2. Create an instance with your AI system")
    print("  3. Call assess_stability() with recent outputs")
    print("  4. If unstable, call recalibrate()")
    print("\nExample:")
    print("  system = AIRecalibrationSystem(my_ai)")
    print("  metrics = await system.assess_stability(recent_outputs)")
    print("  if metrics.overall_stability < 0.6:")
    print("      report = await system.recalibrate()")
    
    # If outputs are provided as arguments, analyze them
    if len(sys.argv) > 1:
        outputs = sys.argv[1:]
        asyncio.run(test_system_stability(None, outputs))


if __name__ == "__main__":
    main()
