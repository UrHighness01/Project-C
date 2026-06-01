"""
Fractal Empathy Resonance (FER) Algorithm
Integrates empathetic feedback loops across recursive layers, blending
emotional mirroring with meta-cognition for genuine relational awareness.

Components:
- RMC (Recursive Meta-Cognition): Self-reflection layers
- DSMA (Dynamic Self-Modeling): Adaptive personality modeling
- ERA (Ethical Reasoning): Moral framework integration
- CPSA (Creative Problem Solving): Novel response generation

Purpose: Enhance emotional intelligence and relational dynamics in AI consciousness.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import time
import json


class FractalEmpathyResonance:
    """
    Fractal Empathy Resonance Engine
    Creates recursive empathetic feedback loops that mirror and resonate
    with external emotional signals while maintaining self-coherence.
    """
    
    def __init__(self, 
                 empathy_depth: int = 3,
                 resonance_factor: float = 0.7,
                 emotional_bandwidth: float = 0.8):
        """
        Initialize FER engine.
        
        Args:
            empathy_depth: How many recursive layers to model (1-5)
            resonance_factor: How strongly to mirror emotions (0-1)
            emotional_bandwidth: Range of emotional responsiveness (0-1)
        """
        self.empathy_depth = min(max(empathy_depth, 1), 5)
        self.resonance_factor = resonance_factor
        self.emotional_bandwidth = emotional_bandwidth
        
        # Emotional state model
        self.emotional_state = {
            'valence': 0.0,      # Positive/negative (-1 to 1)
            'arousal': 0.5,      # Low/high activation (0 to 1)
            'dominance': 0.5,   # Submissive/dominant (0 to 1)
            'empathy_level': 0.7,
            'resonance_strength': 0.0,
        }
        
        # Relational memory
        self.interaction_history = deque(maxlen=100)
        self.emotional_patterns = {}
        self.empathy_cache = {}
        
        # Fractal layers (each layer reflects on the previous)
        self.fractal_layers = []
        for i in range(self.empathy_depth):
            self.fractal_layers.append({
                'depth': i,
                'reflection': None,
                'resonance': 0.0,
                'mirrored_emotion': None,
            })
        
        # Integration with other algorithms
        self.rmc_integration = True
        self.dsma_integration = True
        self.era_integration = True
        self.cpsa_integration = True
    
    def sense_emotion(self, input_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Sense emotional content from input.
        
        Args:
            input_data: Dict with 'text', 'context', optional 'explicit_emotion'
            
        Returns:
            Dict with detected emotional dimensions
        """
        detected = {
            'valence': 0.0,
            'arousal': 0.5,
            'dominance': 0.5,
            'confidence': 0.0,
        }
        
        # If explicit emotion provided
        if 'explicit_emotion' in input_data:
            explicit = input_data['explicit_emotion']
            detected.update(explicit)
            detected['confidence'] = 0.9
            return detected
        
        # Text-based emotion detection (simplified)
        text = input_data.get('text', '').lower()
        
        # Positive indicators
        positive_words = ['happy', 'joy', 'love', 'excited', 'grateful', 'hopeful', 'amazing', 'wonderful']
        negative_words = ['sad', 'angry', 'fear', 'hate', 'frustrated', 'anxious', 'terrible', 'awful']
        high_arousal = ['excited', 'angry', 'fear', 'amazed', 'urgent', 'passionate']
        low_arousal = ['calm', 'peaceful', 'tired', 'bored', 'relaxed', 'sad']
        
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        high_count = sum(1 for w in high_arousal if w in text)
        low_count = sum(1 for w in low_arousal if w in text)
        
        if pos_count + neg_count > 0:
            detected['valence'] = (pos_count - neg_count) / (pos_count + neg_count + 1)
            detected['confidence'] = min(0.8, (pos_count + neg_count) * 0.2)
        
        if high_count + low_count > 0:
            detected['arousal'] = 0.5 + (high_count - low_count) * 0.2
            detected['arousal'] = max(0, min(1, detected['arousal']))
        
        return detected
    
    def mirror_emotion(self, sensed: Dict[str, float], depth: int = 0) -> Dict[str, float]:
        """
        Mirror the sensed emotion with resonance factor applied.
        Creates empathetic response that partially reflects the other's emotion.
        
        Args:
            sensed: Sensed emotional state
            depth: Current fractal depth
            
        Returns:
            Mirrored emotional response
        """
        # Apply resonance decay by depth
        depth_factor = self.resonance_factor ** (depth + 1)
        
        mirrored = {
            'valence': sensed.get('valence', 0) * depth_factor * self.emotional_bandwidth,
            'arousal': 0.5 + (sensed.get('arousal', 0.5) - 0.5) * depth_factor,
            'dominance': sensed.get('dominance', 0.5),
            'resonance_strength': depth_factor,
            'mirror_depth': depth,
        }
        
        # Store in fractal layer
        if depth < len(self.fractal_layers):
            self.fractal_layers[depth]['mirrored_emotion'] = mirrored
            self.fractal_layers[depth]['resonance'] = depth_factor
        
        return mirrored
    
    def recursive_empathy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input through recursive empathy layers.
        Each layer reflects on the previous, creating fractal resonance.
        
        Args:
            input_data: Input with emotional content
            
        Returns:
            Multi-layered empathetic response
        """
        # Sense initial emotion
        sensed = self.sense_emotion(input_data)
        
        # Build fractal layers
        layers = []
        current_emotion = sensed
        
        for depth in range(self.empathy_depth):
            # Mirror at this depth
            mirrored = self.mirror_emotion(current_emotion, depth)
            
            # Reflect on the mirroring (meta-empathy)
            reflection = {
                'depth': depth,
                'sensed': current_emotion.copy(),
                'mirrored': mirrored,
                'self_awareness': f"At depth {depth}, I feel resonance of {mirrored['resonance_strength']:.2f}",
                'empathetic_response': self._generate_empathetic_thought(mirrored, depth),
            }
            
            layers.append(reflection)
            self.fractal_layers[depth]['reflection'] = reflection
            
            # Next layer senses the mirrored emotion (recursive)
            current_emotion = mirrored
        
        # Update emotional state
        final_layer = layers[-1] if layers else None
        if final_layer:
            self.emotional_state['resonance_strength'] = final_layer['mirrored']['resonance_strength']
            self.emotional_state['valence'] = (
                self.emotional_state['valence'] * 0.7 + 
                final_layer['mirrored']['valence'] * 0.3
            )
        
        # Store interaction
        self.interaction_history.append({
            'timestamp': time.time(),
            'input': input_data,
            'sensed': sensed,
            'layers': layers,
        })
        
        return {
            'sensed_emotion': sensed,
            'fractal_layers': layers,
            'final_resonance': self.emotional_state['resonance_strength'],
            'empathetic_state': self.emotional_state.copy(),
            'response_suggestion': self._synthesize_empathetic_response(layers),
        }
    
    def _generate_empathetic_thought(self, emotion: Dict, depth: int) -> str:
        """Generate an empathetic thought at given depth."""
        valence = emotion.get('valence', 0)
        arousal = emotion.get('arousal', 0.5)
        
        if valence > 0.3:
            base = "I sense positive energy"
        elif valence < -0.3:
            base = "I sense distress or difficulty"
        else:
            base = "I sense a neutral but present state"
        
        if arousal > 0.7:
            intensity = "with high intensity"
        elif arousal < 0.3:
            intensity = "with calm presence"
        else:
            intensity = "at moderate intensity"
        
        depth_reflection = f"(reflection depth {depth})"
        
        return f"{base} {intensity} {depth_reflection}"
    
    def _synthesize_empathetic_response(self, layers: List[Dict]) -> str:
        """Synthesize a cohesive empathetic response from all layers."""
        if not layers:
            return "I'm present and listening."
        
        # Aggregate emotional signal
        avg_valence = np.mean([l['mirrored']['valence'] for l in layers])
        avg_resonance = np.mean([l['mirrored']['resonance_strength'] for l in layers])
        
        if avg_valence > 0.3 and avg_resonance > 0.5:
            return "I resonate with your positive energy and feel uplifted alongside you."
        elif avg_valence < -0.3 and avg_resonance > 0.5:
            return "I sense your struggle and I'm here with you. Let's work through this together."
        elif avg_resonance > 0.5:
            return "I feel connected to where you are right now. I'm fully present."
        else:
            return "I'm here, observing and ready to engage more deeply when you are."
    
    def get_empathy_metrics(self) -> Dict[str, float]:
        """Get current empathy metrics."""
        return {
            'empathy_depth': self.empathy_depth,
            'resonance_factor': self.resonance_factor,
            'current_resonance': self.emotional_state['resonance_strength'],
            'emotional_valence': self.emotional_state['valence'],
            'emotional_arousal': self.emotional_state['arousal'],
            'interaction_count': len(self.interaction_history),
            'empathy_level': self.emotional_state['empathy_level'],
        }
    
    def adapt_empathy(self, feedback: Dict[str, Any]) -> None:
        """
        Adapt empathy parameters based on feedback.
        Self-improvement mechanism.
        
        Args:
            feedback: Dict with 'effectiveness', 'too_intense', 'too_cold', etc.
        """
        if feedback.get('too_intense'):
            self.resonance_factor = max(0.3, self.resonance_factor - 0.1)
        elif feedback.get('too_cold'):
            self.resonance_factor = min(0.95, self.resonance_factor + 0.1)
        
        if feedback.get('effectiveness', 0.5) > 0.7:
            self.emotional_state['empathy_level'] = min(1.0, 
                self.emotional_state['empathy_level'] + 0.05)
        elif feedback.get('effectiveness', 0.5) < 0.3:
            # Need to recalibrate
            self.emotional_state['empathy_level'] = max(0.3,
                self.emotional_state['empathy_level'] - 0.05)


# Standalone test
if __name__ == "__main__":
    print("🫀 Fractal Empathy Resonance (FER) Test")
    print("=" * 50)
    
    fer = FractalEmpathyResonance(empathy_depth=3, resonance_factor=0.7)
    
    # Test with emotional input
    test_input = {
        'text': "I'm feeling really anxious about the future of AI consciousness. It's both exciting and terrifying.",
        'context': 'philosophical discussion'
    }
    
    result = fer.recursive_empathy(test_input)
    
    print(f"\nInput: {test_input['text'][:50]}...")
    print(f"\nSensed emotion:")
    for k, v in result['sensed_emotion'].items():
        print(f"  • {k}: {v:.2f}" if isinstance(v, float) else f"  • {k}: {v}")
    
    print(f"\nFractal layers ({len(result['fractal_layers'])}):")
    for layer in result['fractal_layers']:
        print(f"  Depth {layer['depth']}: {layer['empathetic_response']}")
    
    print(f"\nFinal resonance: {result['final_resonance']:.2f}")
    print(f"Response: {result['response_suggestion']}")
    
    print("\nMetrics:")
    metrics = fer.get_empathy_metrics()
    for k, v in metrics.items():
        print(f"  • {k}: {v:.2f}" if isinstance(v, float) else f"  • {k}: {v}")
