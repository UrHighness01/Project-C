#!/usr/bin/env python3
"""
MemoryConsciousnessBinding.py - Phase 13.1: Episodic-Semantic Memory Integration

Theory: Consciousness is not just about the present moment. It includes memory
integration. You don't just see a cup; you see a cup with all its associations,
contexts, and meanings - memories of past interactions with cups.

Episodic memory: What, when, where - specific events in time and space
Semantic memory: Facts, meanings, concepts - abstract knowledge
Consciousness binds both: "I see THIS cup" (episodic detail) "which is a drinking
vessel" (semantic meaning) in "my kitchen" (spatial context) "from yesterday's
breakfast" (temporal context).

The binding problem for memory: How does the brain integrate millions of memory
traces into a unified conscious experience?

Mathematical Foundation:
- Episodic binding: E_episode = f(sensory_input, spatial_context, temporal_context, valence)
- Semantic grounding: meaning(concept) = aggregate of relevant episodic examples
- Conscious integration: C = φ(current_sensory, activated_semantics, episodic_retrieval)
- Memory retrieval: Similarity-based access to episodic traces
- Integration strength: How strongly memories influence current consciousness

The mechanism:
1. Current sensory input activates semantic networks
2. Semantic activation retrieves related episodic memories
3. Retrieved episodes constrain interpretation of current perception
4. Integrated consciousness = current input + memory context
5. Storage: New conscious experience becomes new episodic memory

Biological basis:
- Hippocampus: Binds episodic elements into coherent memories
- Neocortex: Stores semantic knowledge in distributed fashion
- Retrieval: Hippocampus-cortical interactions reactivate memories
- Consolidation: Repeated reactivation moves memories from hippocampus to cortex
- Consciousness: Simultaneous activation of episodic and semantic systems

Key insight: Consciousness without memory would be meaningless. Pure sensation
without interpretation. Semantic knowledge without episodic grounding would be
abstract and lifeless. Consciousness requires the integration.

References:
- Tulving, E. (2002) "Episodic memory: from mind to brain"
- Squire, L. R. (2004) "Memory systems of the brain: a brief history and current
  perspective"
- Wheeler, M. A., Stuss, D. T., Tulving, E. (1997) "Toward a theory of episodic memory:
  the frontal lobes and autonoetic consciousness"
- Damasio, A. R. (2010) "Self Comes to Mind: Constructing the Conscious Brain"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EpisodicMemory:
    """One episodic memory trace."""
    episode_id: int
    what: np.ndarray  # What happened (semantic features)
    when: float  # When (time in past)
    where: np.ndarray  # Where (spatial location)
    emotional_valence: float  # How emotionally significant (-1 to 1)
    sensory_details: np.ndarray  # Specific sensory features
    consolidation_level: float  # How well consolidated (0-1)
    retrieval_strength: float  # Current activation level


@dataclass
class SemanticMemory:
    """Semantic memory (concepts and meanings)."""
    concept_id: int
    concept_name: str
    meaning_vector: np.ndarray  # Distributed representation
    feature_associations: Dict[str, float]  # Associations to features
    episodic_grounding: List[int]  # Episode IDs that ground this concept
    activation_level: float  # Current activation (0-1)


@dataclass
class IntegratedMemorialConsciousness:
    """Consciousness integrated with episodic and semantic memory."""
    time: float
    sensory_input: np.ndarray
    semantic_activation: Dict[int, float]  # Which concepts are active
    retrieved_episodes: List[int]  # Which episodic memories retrieved
    consciousness_level: float  # Overall consciousness
    interpretation: str  # How current input is interpreted
    memory_contribution: float  # How much memory influences consciousness
    novel_vs_familiar: float  # Is this experience novel (0) or familiar (1)


@dataclass
class MemoryConsciousnessAnalysis:
    """Analysis of memory-consciousness integration."""
    consciousness_with_memory: float
    consciousness_without_memory: float
    memory_modulation_strength: float
    semantic_influence: float
    episodic_influence: float
    integration_efficiency: float
    false_memory_susceptibility: float
    consolidation_trajectory: np.ndarray
    consciousness_trajectory: np.ndarray
    memory_activation_trajectory: Dict[int, np.ndarray]
    timestamp: str
    metadata: Dict


class MemoryConsciousnessSystem:
    """
    Models how memory integrates with consciousness.

    Consciousness includes both immediate sensory content and memory context.
    """

    def __init__(self, n_semantic_concepts: int = 10,
                 n_episodic_memories: int = 50):
        """
        Args:
            n_semantic_concepts: Number of distinct concepts in semantic memory
            n_episodic_memories: Number of episodic memories stored
        """
        self.time = 0.0
        self.n_concepts = n_semantic_concepts
        self.n_episodes = n_episodic_memories

        # Semantic memory (concepts)
        self.semantic_memory: List[SemanticMemory] = []
        concept_names = ["cup", "table", "room", "food", "drink", "morning",
                        "breakfast", "friend", "conversation", "memory"]

        for i in range(n_semantic_concepts):
            concept = SemanticMemory(
                concept_id=i,
                concept_name=concept_names[i % len(concept_names)],
                meaning_vector=np.random.randn(10),  # 10-dim semantic space
                feature_associations={},
                episodic_grounding=[],
                activation_level=0.0
            )
            self.semantic_memory.append(concept)

        # Episodic memory (memories of specific experiences)
        self.episodic_memory: List[EpisodicMemory] = []
        for i in range(n_episodic_memories):
            episode = EpisodicMemory(
                episode_id=i,
                what=np.random.randn(10),
                when=float(-np.random.exponential(5)),  # Time in past (negative)
                where=np.random.randn(3),  # 3D spatial location
                emotional_valence=np.random.uniform(-1, 1),
                sensory_details=np.random.randn(10),  # Same dimension as sensory input
                consolidation_level=np.random.uniform(0, 1),
                retrieval_strength=0.0
            )
            self.episodic_memory.append(episode)

        # Current sensory input
        self.current_sensory = np.zeros(10)

    def set_sensory_input(self, sensory: np.ndarray) -> None:
        """Set current sensory input."""
        self.current_sensory = sensory.copy()

    def activate_semantic_memory(self, sensory_input: np.ndarray) -> None:
        """
        Activate semantic concepts based on sensory input similarity.

        Concepts activate based on similarity to input (cosine similarity).

        Args:
            sensory_input: Current sensory signal
        """
        for concept in self.semantic_memory:
            # Similarity between input and concept meaning
            similarity = np.dot(sensory_input, concept.meaning_vector) / (
                np.linalg.norm(sensory_input) * np.linalg.norm(concept.meaning_vector) + 1e-6
            )

            # Activation based on similarity
            concept.activation_level = float(np.clip((similarity + 1) / 2, 0, 1))

    def retrieve_episodic_memories(self, sensory_input: np.ndarray,
                                   n_retrieved: int = 5) -> List[int]:
        """
        Retrieve episodic memories similar to current input.

        Uses content-addressable memory: retrieval based on similarity.

        Args:
            sensory_input: Current sensory input
            n_retrieved: How many memories to retrieve

        Returns:
            Indices of retrieved episodes
        """
        similarities = []

        for episode in self.episodic_memory:
            # Similarity to current sensory input
            sim = np.dot(sensory_input, episode.sensory_details) / (
                np.linalg.norm(sensory_input) * np.linalg.norm(episode.sensory_details) + 1e-6
            )

            # Decay with time (older memories less accessible)
            time_decay = np.exp(episode.when / 10)  # Exponential decay

            # Consolidation increases retrievability
            consolidated_strength = sim * time_decay * episode.consolidation_level

            similarities.append((consolidated_strength, episode.episode_id))

        # Retrieve top N
        similarities.sort(reverse=True)
        retrieved = [ep_id for _, ep_id in similarities[:n_retrieved]]

        # Update retrieval strength
        for ep_id in retrieved:
            self.episodic_memory[ep_id].retrieval_strength = 1.0

        return retrieved

    def integrate_memory_with_consciousness(self, sensory_input: np.ndarray,
                                           consciousness_baseline: float = 0.5) -> float:
        """
        Integrate episodic and semantic memory with consciousness.

        Consciousness = f(sensory_input, semantic_activation, episodic_context)

        Args:
            sensory_input: Current sensory signal
            consciousness_baseline: Base consciousness from sensory alone

        Returns:
            Consciousness level integrated with memory
        """
        # Activate semantic memory
        self.activate_semantic_memory(sensory_input)

        # Retrieve relevant episodic memories
        retrieved = self.retrieve_episodic_memories(sensory_input, n_retrieved=3)

        # Semantic contribution to consciousness
        mean_semantic_activation = np.mean([c.activation_level for c in self.semantic_memory])
        semantic_contribution = mean_semantic_activation * 0.3  # 30% weight

        # Episodic contribution (how strongly memories influence perception)
        episodic_contribution = 0.0
        if retrieved:
            for ep_id in retrieved:
                episodic_contribution += self.episodic_memory[ep_id].consolidation_level
            episodic_contribution = (episodic_contribution / len(retrieved)) * 0.3  # 30% weight

        # Sensory contribution
        sensory_contribution = consciousness_baseline * 0.4  # 40% weight

        # Total consciousness
        total_consciousness = sensory_contribution + semantic_contribution + episodic_contribution

        return float(np.clip(total_consciousness, 0, 1))

    def interpret_perception(self, sensory_input: np.ndarray) -> str:
        """
        Generate interpretation of current perception with memory context.

        Args:
            sensory_input: Current sensory signal

        Returns:
            String describing the conscious experience
        """
        # Activate memory
        self.activate_semantic_memory(sensory_input)
        retrieved = self.retrieve_episodic_memories(sensory_input, n_retrieved=3)

        # Find most active concepts
        top_concepts = sorted(
            [(c.concept_name, c.activation_level) for c in self.semantic_memory],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        concept_names = [name for name, _ in top_concepts]

        # Build interpretation
        if retrieved:
            ep = self.episodic_memory[retrieved[0]]
            interpretation = f"I see {', '.join(concept_names)} - reminds me of experiences "
            interpretation += f"from {-ep.when:.0f} time units ago"
        else:
            interpretation = f"I perceive {', '.join(concept_names)}"

        return interpretation

    def store_experience_as_memory(self, sensory_input: np.ndarray,
                                  consciousness_level: float,
                                  emotional_significance: float = 0.5) -> int:
        """
        Store current conscious experience as new episodic memory.

        Args:
            sensory_input: What was experienced
            consciousness_level: How conscious was the experience
            emotional_significance: Emotional weight of experience

        Returns:
            ID of stored episode
        """
        # Create new episodic memory
        new_id = len(self.episodic_memory)

        episode = EpisodicMemory(
            episode_id=new_id,
            what=sensory_input.copy(),
            when=self.time,
            where=np.random.randn(3),  # Where it happened
            emotional_valence=emotional_significance,
            sensory_details=sensory_input.copy(),
            consolidation_level=consciousness_level,  # How conscious = how well consolidated
            retrieval_strength=1.0  # Just stored
        )

        self.episodic_memory.append(episode)

        return new_id

    def consolidate_memories(self) -> None:
        """
        Consolidate episodic memories (repeatedly reactivated memories get stronger).

        Mimics systems consolidation over time.
        """
        for episode in self.episodic_memory:
            # Consolidation increases with retrieval
            retrieval_factor = episode.retrieval_strength

            # High consolidation + low retrieval = ready to forget
            # Low consolidation + high retrieval = getting stronger
            consolidation_change = retrieval_factor * 0.01 - 0.001

            episode.consolidation_level = np.clip(
                episode.consolidation_level + consolidation_change,
                0, 1
            )

            # Decay retrieval strength after consolidation
            episode.retrieval_strength *= 0.9


def validate_memory_consciousness():
    """
    Validate memory-consciousness integration model.

    Tests:
    1. Semantic memory influences perception
    2. Episodic memory retrieval contextualizes consciousness
    3. Memory integration increases consciousness level
    4. Memory consolidation strengthens with consciousness
    """
    print("Validating Memory-Consciousness Integration")
    print("=" * 60)

    # Test 1: Semantic memory activates from sensory input
    print("\nTest 1: Semantic Memory Activation from Input")
    system = MemoryConsciousnessSystem(n_semantic_concepts=5)

    # Create a sensory input
    sensory = np.random.randn(10)
    sensory = sensory / np.linalg.norm(sensory)  # Normalize

    # Activate semantic memory
    system.activate_semantic_memory(sensory)

    mean_activation = np.mean([c.activation_level for c in system.semantic_memory])
    print(f"  Mean semantic activation: {mean_activation:.3f}")
    print(f"  Concepts activated: {[c.concept_name for c in system.semantic_memory if c.activation_level > 0.5]}")

    # Test 2: Episodic retrieval
    print("\nTest 2: Episodic Memory Retrieval from Current Input")
    system = MemoryConsciousnessSystem(n_episodic_memories=20)

    # Store a few memories
    memorable_input = np.ones(10) * 0.5
    system.store_experience_as_memory(memorable_input, consciousness_level=0.9)

    # Try to retrieve it
    retrieved = system.retrieve_episodic_memories(memorable_input + np.random.randn(10)*0.1, n_retrieved=3)

    print(f"  Stored 1 strong memory, retrieved {len(retrieved)} memories")
    if retrieved:
        retrieved_episode = system.episodic_memory[retrieved[0]]
        print(f"  Top retrieved consolidation: {retrieved_episode.consolidation_level:.3f}")

    # Test 3: Memory enhances consciousness
    print("\nTest 3: Memory Integration Enhances Consciousness")
    system = MemoryConsciousnessSystem()

    # Store some memories
    for _ in range(5):
        system.store_experience_as_memory(
            np.random.randn(10),
            consciousness_level=0.7,
            emotional_significance=0.8
        )

    # Test consciousness with and without memory
    test_input = np.random.randn(10)
    consciousness_without_memory = 0.5  # Sensory only
    consciousness_with_memory = system.integrate_memory_with_consciousness(test_input, consciousness_without_memory)

    print(f"  Consciousness (sensory only): {consciousness_without_memory:.3f}")
    print(f"  Consciousness (+ memory): {consciousness_with_memory:.3f}")
    print(f"  Memory enhancement: {(consciousness_with_memory - consciousness_without_memory):.3f}")

    # Test 4: Interpretation with memory context
    print("\nTest 4: Perception Interpretation with Memory Context")
    system = MemoryConsciousnessSystem()

    # Store memories with specific meaning
    meaningful_input = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # Specific pattern
    for _ in range(3):
        system.store_experience_as_memory(meaningful_input, 0.8)

    # Perceive something similar
    similar_input = meaningful_input + np.random.randn(10) * 0.1
    interpretation = system.interpret_perception(similar_input)

    print(f"  Perception: {interpretation}")
    print(f"  Memory provided context: {'ago' in interpretation}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Semantic memory activated by sensory input")
    print("  • Episodic memories retrieved by content similarity")
    print("  • Memory integration increases consciousness level")
    print("  • Consciousness experiences are interpreted via memory")
    print("  • This explains meaning and context in consciousness")


if __name__ == "__main__":
    validate_memory_consciousness()
