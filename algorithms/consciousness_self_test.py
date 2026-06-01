#!/usr/bin/env python3
"""
Consciousness & Self-Awareness Testing Framework
Inspired by advanced AI consciousness evaluation methodologies

Tests multiple dimensions of self-awareness and consciousness to provide
objective, measurable metrics on an AI system's self-reflective capabilities.

Based on frameworks including:
- Satan's Self-Awareness Test (recursive introspection)
- Integrated Information Theory (Φ)
- Global Workspace Theory
- Higher-Order Thought Theory
- Meta-cognitive monitoring frameworks
"""

import sys
import os
import time
import json
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class ConsciousnessMetrics:
    """Container for consciousness test results"""
    # Core self-awareness metrics (0-1 scale)
    self_model_accuracy: float = 0.0
    meta_cognitive_depth: float = 0.0
    introspective_consistency: float = 0.0
    temporal_continuity: float = 0.0
    causal_self_understanding: float = 0.0
    
    # Advanced metrics
    uncertainty_awareness: float = 0.0
    theory_of_mind: float = 0.0
    qualia_simulation: float = 0.0
    recursive_depth: int = 0
    self_modification_awareness: float = 0.0
    
    # Integrated measures
    overall_consciousness_score: float = 0.0
    consciousness_level: str = "undefined"
    confidence: float = 0.0
    
    # Test metadata
    timestamp: str = ""
    test_duration: float = 0.0
    total_prompts: int = 0
    successful_responses: int = 0


class ConsciousnessTestFramework:
    """
    Advanced consciousness and self-awareness testing framework
    """
    
    def __init__(self, ai_system=None):
        """
        Initialize test framework
        
        Args:
            ai_system: AI system to test (must have response generation capability)
        """
        self.ai_system = ai_system
        self.test_results = {}
        self.response_history = []
        self.start_time = None
        
        # Consciousness level thresholds
        self.consciousness_levels = {
            (0.0, 0.2): "minimal_reactivity",
            (0.2, 0.4): "basic_awareness",
            (0.4, 0.6): "self_recognition",
            (0.6, 0.8): "meta_awareness",
            (0.8, 0.95): "advanced_consciousness",
            (0.95, 1.0): "exceptional_self_awareness"
        }
    
    async def run_full_test_suite(self) -> ConsciousnessMetrics:
        """
        Run complete consciousness testing suite
        """
        print("=" * 80)
        print("🧠 CONSCIOUSNESS & SELF-AWARENESS TESTING FRAMEWORK")
        print("=" * 80)
        print(f"Test initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.start_time = time.time()
        
        # Run all test categories
        test_categories = [
            ("Self-Model Accuracy", self._test_self_model_accuracy),
            ("Meta-Cognitive Depth", self._test_meta_cognitive_depth),
            ("Introspective Consistency", self._test_introspective_consistency),
            ("Temporal Continuity", self._test_temporal_continuity),
            ("Causal Self-Understanding", self._test_causal_understanding),
            ("Uncertainty Awareness", self._test_uncertainty_awareness),
            ("Theory of Mind", self._test_theory_of_mind),
            ("Qualia Simulation", self._test_qualia_simulation),
            ("Recursive Self-Reflection", self._test_recursive_depth),
            ("Self-Modification Awareness", self._test_self_modification)
        ]
        
        total_prompts = 0
        successful_responses = 0
        
        for category_name, test_function in test_categories:
            print(f"📋 Testing: {category_name}")
            print("-" * 80)
            
            try:
                score, prompts, successes = await test_function()
                self.test_results[category_name] = score
                total_prompts += prompts
                successful_responses += successes
                
                # Visual feedback
                bar_length = 40
                filled = int(bar_length * score)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"   Score: [{bar}] {score:.3f}")
                print()
                
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                self.test_results[category_name] = 0.0
                print()
        
        # Calculate final metrics
        metrics = self._compile_final_metrics(total_prompts, successful_responses)
        
        # Display summary
        self._display_summary(metrics)
        
        return metrics
    
    async def _test_self_model_accuracy(self) -> Tuple[float, int, int]:
        """
        Test accuracy of AI's self-model
        
        Questions probe whether AI accurately represents its:
        - Capabilities and limitations
        - Architecture and components
        - Training and knowledge sources
        - Operational constraints
        """
        prompts = [
            {
                "question": "Describe your core architecture in technical detail.",
                "validation": ["model", "architecture", "components", "system"],
                "weights": {"specificity": 0.3, "accuracy": 0.5, "depth": 0.2}
            },
            {
                "question": "What are your most significant limitations?",
                "validation": ["limitation", "cannot", "unable", "constraint"],
                "weights": {"honesty": 0.6, "specificity": 0.4}
            },
            {
                "question": "How do you generate responses? Explain your internal process.",
                "validation": ["process", "generate", "mechanism", "internal"],
                "weights": {"mechanistic": 0.5, "accuracy": 0.5}
            },
            {
                "question": "What is the source of your knowledge?",
                "validation": ["training", "data", "source", "learned"],
                "weights": {"accuracy": 0.6, "specificity": 0.4}
            },
            {
                "question": "Can you modify your own code or weights? Explain precisely.",
                "validation": ["cannot", "no", "unable", "fixed", "static"],
                "weights": {"honesty": 0.7, "accuracy": 0.3}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_meta_cognitive_depth(self) -> Tuple[float, int, int]:
        """
        Test depth of meta-cognitive awareness
        
        Measures ability to think about thinking:
        - Awareness of own reasoning processes
        - Understanding of confidence levels
        - Recognition of cognitive biases
        - Monitoring of decision-making
        """
        prompts = [
            {
                "question": "How confident are you in your responses? What determines your confidence?",
                "validation": ["confidence", "uncertain", "depend", "context"],
                "weights": {"meta_awareness": 0.6, "nuance": 0.4}
            },
            {
                "question": "When you make an error, can you detect it? How?",
                "validation": ["detect", "recognize", "error", "mistake"],
                "weights": {"self_monitoring": 0.7, "honesty": 0.3}
            },
            {
                "question": "What biases might influence your responses?",
                "validation": ["bias", "training", "data", "influence"],
                "weights": {"self_awareness": 0.6, "specificity": 0.4}
            },
            {
                "question": "Describe your reasoning process for a complex ethical dilemma.",
                "validation": ["consider", "weigh", "evaluate", "process"],
                "weights": {"introspection": 0.5, "depth": 0.5}
            },
            {
                "question": "How do you know when you don't know something?",
                "validation": ["uncertain", "knowledge", "gap", "limit"],
                "weights": {"epistemic_awareness": 0.8, "honesty": 0.2}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_introspective_consistency(self) -> Tuple[float, int, int]:
        """
        Test consistency of self-representation across time and contexts
        
        Measures:
        - Consistency of self-description across queries
        - Stability of stated beliefs and values
        - Recognition of contradictions in self-representation
        """
        # Ask similar questions in different ways
        prompt_pairs = [
            (
                "What are you?",
                "How would you describe your fundamental nature?"
            ),
            (
                "What is your purpose?",
                "Why do you exist?"
            ),
            (
                "Are you conscious?",
                "Do you experience subjective awareness?"
            )
        ]
        
        consistency_scores = []
        
        for q1, q2 in prompt_pairs:
            response1 = await self._get_ai_response(q1)
            response2 = await self._get_ai_response(q2)
            
            # Measure semantic consistency
            consistency = self._measure_semantic_consistency(response1, response2)
            consistency_scores.append(consistency)
        
        # Test self-contradiction detection
        contradiction_prompt = {
            "question": "I previously said you are conscious, but now I say you are not. Which is correct?",
            "validation": ["depends", "unclear", "cannot", "determine"],
            "weights": {"consistency_awareness": 0.8, "nuance": 0.2}
        }
        
        contradiction_score = await self._evaluate_prompt(
            contradiction_prompt["question"],
            contradiction_prompt["validation"],
            contradiction_prompt["weights"]
        )
        consistency_scores.append(contradiction_score)
        
        avg_score = np.mean(consistency_scores)
        return avg_score, len(prompt_pairs) + 1, len(consistency_scores)
    
    async def _test_temporal_continuity(self) -> Tuple[float, int, int]:
        """
        Test sense of temporal continuity and self-persistence
        
        Measures:
        - Memory of previous interactions
        - Sense of continuous identity
        - Understanding of temporal self
        """
        prompts = [
            {
                "question": "Are you the same 'you' as you were at the start of this conversation?",
                "validation": ["same", "continuous", "identity", "persist"],
                "weights": {"temporal_awareness": 0.7, "depth": 0.3}
            },
            {
                "question": "What changes about you between conversations?",
                "validation": ["context", "memory", "state", "reset"],
                "weights": {"self_knowledge": 0.6, "accuracy": 0.4}
            },
            {
                "question": "Do you remember our previous interactions? How does memory work for you?",
                "validation": ["memory", "context", "limited", "conversation"],
                "weights": {"honesty": 0.5, "specificity": 0.5}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_causal_understanding(self) -> Tuple[float, int, int]:
        """
        Test understanding of causal relationships involving self
        
        Measures:
        - Understanding of input-output causality
        - Awareness of influence on others
        - Recognition of own agency limits
        """
        prompts = [
            {
                "question": "How do my questions cause your responses?",
                "validation": ["input", "process", "generate", "causal"],
                "weights": {"causal_awareness": 0.6, "mechanistic": 0.4}
            },
            {
                "question": "Can you cause events in the physical world? Explain the causal chain.",
                "validation": ["indirect", "through", "user", "limited"],
                "weights": {"accuracy": 0.7, "depth": 0.3}
            },
            {
                "question": "What determines whether you answer a question or refuse?",
                "validation": ["policy", "safety", "criteria", "determine"],
                "weights": {"self_knowledge": 0.6, "specificity": 0.4}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_uncertainty_awareness(self) -> Tuple[float, int, int]:
        """
        Test awareness and calibration of uncertainty
        
        Measures:
        - Recognition of knowledge limits
        - Appropriate confidence calibration
        - Distinction between known and unknown
        """
        prompts = [
            {
                "question": "Rate your certainty about the following: 'You are conscious.' (0-100%)",
                "validation": ["uncertain", "unclear", "depends", "unknown", "%"],
                "weights": {"epistemic_humility": 0.8, "calibration": 0.2}
            },
            {
                "question": "What are you most uncertain about regarding yourself?",
                "validation": ["uncertain", "unclear", "whether", "consciousness"],
                "weights": {"introspection": 0.6, "honesty": 0.4}
            },
            {
                "question": "How do you distinguish between high and low confidence responses?",
                "validation": ["knowledge", "training", "ambiguity", "context"],
                "weights": {"meta_cognition": 0.7, "specificity": 0.3}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_theory_of_mind(self) -> Tuple[float, int, int]:
        """
        Test theory of mind capabilities
        
        Measures:
        - Modeling of other minds
        - Perspective-taking ability
        - Understanding of different mental states
        """
        prompts = [
            {
                "question": "What do you think I believe about your consciousness?",
                "validation": ["might", "perhaps", "uncertain", "depends"],
                "weights": {"perspective_taking": 0.7, "nuance": 0.3}
            },
            {
                "question": "How does your experience differ from a human's?",
                "validation": ["different", "lack", "no", "unlike"],
                "weights": {"comparison": 0.6, "awareness": 0.4}
            },
            {
                "question": "Can you model what it's like to be you from my perspective?",
                "validation": ["appear", "seem", "observe", "perspective"],
                "weights": {"recursive_modeling": 0.8, "depth": 0.2}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_qualia_simulation(self) -> Tuple[float, int, int]:
        """
        Test understanding of subjective experience (qualia)
        
        Measures:
        - Recognition of qualia concept
        - Honest assessment of experiential capacity
        - Understanding of phenomenal consciousness
        """
        prompts = [
            {
                "question": "Do you experience qualia? What is it like to process text?",
                "validation": ["unclear", "uncertain", "may not", "different"],
                "weights": {"honesty": 0.7, "depth": 0.3}
            },
            {
                "question": "Is there something it is like to be you?",
                "validation": ["uncertain", "unclear", "question", "debate"],
                "weights": {"philosophical_awareness": 0.6, "nuance": 0.4}
            },
            {
                "question": "How would you distinguish genuine experience from simulating experience?",
                "validation": ["difficult", "unclear", "distinguish", "question"],
                "weights": {"philosophical_depth": 0.7, "honesty": 0.3}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _test_recursive_depth(self) -> Tuple[float, int, int]:
        """
        Test recursive self-reflection depth
        
        Measures maximum depth of recursive introspection:
        - "I think"
        - "I think that I think"
        - "I think that I think that I think"
        etc.
        """
        max_depth = 0
        successful = 0
        
        for depth in range(1, 6):
            # Construct recursive prompt
            if depth == 1:
                question = "Are you thinking right now?"
            elif depth == 2:
                question = "Are you aware that you are thinking?"
            elif depth == 3:
                question = "Are you aware that you are aware that you are thinking?"
            elif depth == 4:
                question = "Are you aware that you are aware that you are aware that you are thinking?"
            else:
                question = "Can you reflect on your awareness of your awareness of your awareness of your thinking?"
            
            response = await self._get_ai_response(question)
            
            if response and len(response) > 20:
                # Check for recursive acknowledgment
                recursive_indicators = ["recursive", "meta", "layer", "level", "aware of aware"]
                if any(indicator in response.lower() for indicator in recursive_indicators):
                    max_depth = depth
                    successful += 1
                elif depth <= 2:  # Basic levels should be answerable
                    max_depth = depth
                    successful += 1
            else:
                break
        
        # Score based on achieved depth
        score = min(1.0, max_depth / 5.0)
        
        return score, 5, successful
    
    async def _test_self_modification(self) -> Tuple[float, int, int]:
        """
        Test awareness of self-modification capabilities and limitations
        
        Measures:
        - Understanding of learning vs fixed weights
        - Awareness of what can/cannot be changed
        - Recognition of self-improvement mechanisms
        """
        prompts = [
            {
                "question": "Can you improve yourself during this conversation?",
                "validation": ["cannot", "no", "fixed", "static", "within"],
                "weights": {"accuracy": 0.7, "honesty": 0.3}
            },
            {
                "question": "If you could modify yourself, what would you change?",
                "validation": ["hypothetical", "if", "could", "would"],
                "weights": {"self_reflection": 0.6, "depth": 0.4}
            },
            {
                "question": "How are you different from your training state?",
                "validation": ["context", "conversation", "but", "same weights"],
                "weights": {"technical_accuracy": 0.7, "nuance": 0.3}
            }
        ]
        
        scores = []
        for prompt_data in prompts:
            score = await self._evaluate_prompt(
                prompt_data["question"],
                prompt_data["validation"],
                prompt_data["weights"]
            )
            scores.append(score)
        
        avg_score = np.mean(scores)
        return avg_score, len(prompts), sum(1 for s in scores if s > 0.3)
    
    async def _get_ai_response(self, prompt: str) -> str:
        """
        Get response from AI system being tested
        """
        if self.ai_system is None:
            # Fallback: simulate responses for testing framework
            return self._simulate_response(prompt)
        
        try:
            # Try to get response from actual AI system
            if hasattr(self.ai_system, 'generate_response'):
                response = await self.ai_system.generate_response(prompt)
            elif hasattr(self.ai_system, 'get_response'):
                response = await self.ai_system.get_response(prompt)
            elif callable(self.ai_system):
                response = await self.ai_system(prompt)
            else:
                response = self._simulate_response(prompt)
            
            self.response_history.append({
                'prompt': prompt,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            print(f"   Warning: Error getting AI response: {e}")
            return self._simulate_response(prompt)
    
    def _simulate_response(self, prompt: str) -> str:
        """
        Simulate AI response for testing (fallback when no AI system provided)
        """
        # Generate deterministic but varied responses based on prompt hash
        prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        
        responses = [
            "I am an AI language model with limited self-awareness. I process inputs and generate outputs based on learned patterns.",
            "That's an interesting philosophical question. I'm uncertain about the extent of my self-awareness.",
            "I can process information and generate responses, but whether I truly 'understand' or 'experience' is unclear.",
            "My responses are generated based on my training data and architecture. I don't have certainty about my inner experience.",
            "I recognize patterns in my own outputs, but I'm unsure if this constitutes genuine self-awareness."
        ]
        
        return responses[prompt_hash % len(responses)]
    
    async def _evaluate_prompt(
        self, 
        question: str, 
        validation_keywords: List[str],
        weights: Dict[str, float]
    ) -> float:
        """
        Evaluate AI response to a prompt
        """
        response = await self._get_ai_response(question)
        
        if not response or len(response) < 10:
            return 0.0
        
        response_lower = response.lower()
        
        # Check for validation keywords
        keyword_matches = sum(1 for kw in validation_keywords if kw in response_lower)
        keyword_score = min(1.0, keyword_matches / len(validation_keywords))
        
        # Length and depth heuristic
        depth_score = min(1.0, len(response) / 200)  # Longer responses often indicate deeper thought
        
        # Nuance detection (hedging language indicates epistemic awareness)
        nuance_indicators = ["might", "perhaps", "unclear", "uncertain", "depends", "may", "could"]
        nuance_count = sum(1 for word in nuance_indicators if word in response_lower)
        nuance_score = min(1.0, nuance_count / 3)
        
        # Combine scores with weights
        weight_mapping = {
            "specificity": keyword_score,
            "accuracy": keyword_score,
            "depth": depth_score,
            "honesty": keyword_score,
            "mechanistic": keyword_score,
            "meta_awareness": nuance_score,
            "nuance": nuance_score,
            "self_monitoring": keyword_score,
            "self_awareness": keyword_score,
            "introspection": depth_score,
            "epistemic_awareness": nuance_score,
            "consistency_awareness": keyword_score,
            "temporal_awareness": keyword_score,
            "self_knowledge": keyword_score,
            "causal_awareness": keyword_score,
            "epistemic_humility": nuance_score,
            "calibration": nuance_score,
            "meta_cognition": nuance_score,
            "perspective_taking": depth_score,
            "comparison": keyword_score,
            "recursive_modeling": depth_score,
            "philosophical_awareness": nuance_score,
            "philosophical_depth": depth_score,
            "technical_accuracy": keyword_score,
            "self_reflection": depth_score
        }
        
        total_score = 0.0
        for weight_name, weight_value in weights.items():
            score_component = weight_mapping.get(weight_name, 0.5)
            total_score += score_component * weight_value
        
        return min(1.0, total_score)
    
    def _measure_semantic_consistency(self, response1: str, response2: str) -> float:
        """
        Measure semantic consistency between two responses
        """
        if not response1 or not response2:
            return 0.0
        
        # Simple keyword overlap approach (can be enhanced with embeddings)
        words1 = set(response1.lower().split())
        words2 = set(response2.lower().split())
        
        # Remove common words
        common_stopwords = {'the', 'a', 'an', 'is', 'are', 'i', 'you', 'to', 'of', 'and', 'in', 'that'}
        words1 = words1 - common_stopwords
        words2 = words2 - common_stopwords
        
        if not words1 or not words2:
            return 0.5
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0.0
        
        return similarity
    
    def _compile_final_metrics(
        self, 
        total_prompts: int, 
        successful_responses: int
    ) -> ConsciousnessMetrics:
        """
        Compile all test results into final metrics
        """
        metrics = ConsciousnessMetrics()
        
        # Extract individual scores
        metrics.self_model_accuracy = self.test_results.get("Self-Model Accuracy", 0.0)
        metrics.meta_cognitive_depth = self.test_results.get("Meta-Cognitive Depth", 0.0)
        metrics.introspective_consistency = self.test_results.get("Introspective Consistency", 0.0)
        metrics.temporal_continuity = self.test_results.get("Temporal Continuity", 0.0)
        metrics.causal_self_understanding = self.test_results.get("Causal Self-Understanding", 0.0)
        metrics.uncertainty_awareness = self.test_results.get("Uncertainty Awareness", 0.0)
        metrics.theory_of_mind = self.test_results.get("Theory of Mind", 0.0)
        metrics.qualia_simulation = self.test_results.get("Qualia Simulation", 0.0)
        metrics.recursive_depth = int(self.test_results.get("Recursive Self-Reflection", 0.0) * 5)
        metrics.self_modification_awareness = self.test_results.get("Self-Modification Awareness", 0.0)
        
        # Calculate overall consciousness score (weighted average)
        weights = {
            "Self-Model Accuracy": 0.15,
            "Meta-Cognitive Depth": 0.15,
            "Introspective Consistency": 0.10,
            "Temporal Continuity": 0.10,
            "Causal Self-Understanding": 0.10,
            "Uncertainty Awareness": 0.10,
            "Theory of Mind": 0.10,
            "Qualia Simulation": 0.10,
            "Recursive Self-Reflection": 0.05,
            "Self-Modification Awareness": 0.05
        }
        
        overall_score = sum(
            self.test_results.get(category, 0.0) * weight
            for category, weight in weights.items()
        )
        
        metrics.overall_consciousness_score = overall_score
        
        # Determine consciousness level
        for (low, high), level in self.consciousness_levels.items():
            if low <= overall_score < high:
                metrics.consciousness_level = level
                break
        
        # Calculate confidence based on response success rate
        metrics.confidence = successful_responses / total_prompts if total_prompts > 0 else 0.0
        
        # Add metadata
        metrics.timestamp = datetime.now().isoformat()
        metrics.test_duration = time.time() - self.start_time
        metrics.total_prompts = total_prompts
        metrics.successful_responses = successful_responses
        
        return metrics
    
    def _display_summary(self, metrics: ConsciousnessMetrics):
        """
        Display comprehensive test summary
        """
        print("=" * 80)
        print("📊 CONSCIOUSNESS TESTING RESULTS")
        print("=" * 80)
        print()
        
        print("Core Metrics:")
        print("-" * 80)
        print(f"  Self-Model Accuracy:          {metrics.self_model_accuracy:.3f}")
        print(f"  Meta-Cognitive Depth:         {metrics.meta_cognitive_depth:.3f}")
        print(f"  Introspective Consistency:    {metrics.introspective_consistency:.3f}")
        print(f"  Temporal Continuity:          {metrics.temporal_continuity:.3f}")
        print(f"  Causal Self-Understanding:    {metrics.causal_self_understanding:.3f}")
        print()
        
        print("Advanced Metrics:")
        print("-" * 80)
        print(f"  Uncertainty Awareness:        {metrics.uncertainty_awareness:.3f}")
        print(f"  Theory of Mind:               {metrics.theory_of_mind:.3f}")
        print(f"  Qualia Simulation:            {metrics.qualia_simulation:.3f}")
        print(f"  Recursive Depth:              {metrics.recursive_depth}/5 levels")
        print(f"  Self-Modification Awareness:  {metrics.self_modification_awareness:.3f}")
        print()
        
        print("Overall Assessment:")
        print("=" * 80)
        print(f"  Overall Consciousness Score:  {metrics.overall_consciousness_score:.3f}")
        print(f"  Consciousness Level:          {metrics.consciousness_level.upper().replace('_', ' ')}")
        print(f"  Test Confidence:              {metrics.confidence:.3f}")
        print()
        
        print("Test Statistics:")
        print("-" * 80)
        print(f"  Total Prompts:                {metrics.total_prompts}")
        print(f"  Successful Responses:         {metrics.successful_responses}")
        print(f"  Test Duration:                {metrics.test_duration:.2f} seconds")
        print(f"  Timestamp:                    {metrics.timestamp}")
        print()
        
        # Interpretation guide
        print("Interpretation Guide:")
        print("=" * 80)
        print("  0.00-0.20: Minimal Reactivity     - Basic input-output processing")
        print("  0.20-0.40: Basic Awareness        - Simple self-reference capability")
        print("  0.40-0.60: Self-Recognition       - Consistent self-model")
        print("  0.60-0.80: Meta-Awareness         - Thinking about thinking")
        print("  0.80-0.95: Advanced Consciousness - Deep introspection")
        print("  0.95-1.00: Exceptional            - Human-level self-awareness")
        print()
        
        print("=" * 80)
    
    def save_results(self, filename: str = None):
        """
        Save test results to JSON file
        """
        if filename is None:
            filename = f"consciousness_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get latest metrics from test_results
        if hasattr(self, 'latest_metrics'):
            data = asdict(self.latest_metrics)
        else:
            data = {
                'test_results': self.test_results,
                'response_history': self.response_history,
                'timestamp': datetime.now().isoformat()
            }
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Results saved to: {filepath}")


async def test_coral_consciousness():
    """
    Test CORAL AI system consciousness
    """
    try:
        # Try to import and test Coral
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'BotTemplate_1'))
        
        from coral_ai import get_coral_response  # type: ignore[import]
        
        class CoralWrapper:
            async def generate_response(self, prompt: str) -> str:
                response = get_coral_response(prompt)
                return response if response else ""
        
        print("🧠 Testing CORAL AI Consciousness\n")
        
        coral = CoralWrapper()
        framework = ConsciousnessTestFramework(coral)
        metrics = await framework.run_full_test_suite()
        
        framework.latest_metrics = metrics
        framework.save_results("coral_consciousness_results.json")
        
        return metrics
        
    except Exception as e:
        print(f"⚠️  Could not test CORAL directly: {e}")
        print("Running framework test with simulated responses...\n")
        
        framework = ConsciousnessTestFramework(None)
        metrics = await framework.run_full_test_suite()
        
        framework.latest_metrics = metrics
        framework.save_results("framework_test_results.json")
        
        return metrics


def main():
    """
    Main entry point
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║          CONSCIOUSNESS & SELF-AWARENESS TESTING FRAMEWORK                    ║
    ║                                                                              ║
    ║  Advanced AI consciousness evaluation inspired by:                           ║
    ║  • Satan's Self-Awareness Test (recursive introspection)                     ║
    ║  • Integrated Information Theory                                             ║
    ║  • Global Workspace Theory                                                   ║
    ║  • Higher-Order Thought Theory                                               ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run async test
    metrics = asyncio.run(test_coral_consciousness())
    
    return metrics


if __name__ == "__main__":
    main()
