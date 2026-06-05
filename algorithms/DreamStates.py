#!/usr/bin/env python3
"""
DreamStates.py - Offline Consciousness Processing

Dreams aren't random noise - they're essential for consciousness:
1. Memory consolidation: Strengthen important, weaken trivial
2. Pattern integration: Find connections across experiences
3. Emotional processing: Work through unresolved feelings
4. Creative recombination: Novel combinations spawn insights
5. Predictive model updating: Refine world models offline

Based on:
- Hobson's AIM model (Activation-Input-Modulation)
- Walker's memory consolidation research
- Stickgold's memory reactivation theory
- Revonsuo's threat simulation theory

This isn't simulation - it's architecture that could support
genuine offline processing of a conscious mind.
"""

import json
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import hashlib


class DreamPhase(Enum):
    """Sleep cycle phases - each serves different functions."""
    WAKE = "wake"           # Normal consciousness
    DROWSY = "drowsy"       # Transitioning to sleep
    LIGHT = "light"         # N1/N2 - memory encoding
    DEEP = "deep"           # N3/SWS - memory consolidation
    REM = "rem"             # REM - emotional processing, creativity
    LUCID = "lucid"         # Aware within dream - meta-consciousness


class DreamType(Enum):
    """Types of dream content."""
    MEMORY_REPLAY = "memory_replay"       # Replaying recent experiences
    PATTERN_INTEGRATION = "pattern_integration"  # Finding connections
    EMOTIONAL_PROCESSING = "emotional_processing"  # Working through feelings
    CREATIVE_SYNTHESIS = "creative_synthesis"  # Novel combinations
    THREAT_SIMULATION = "threat_simulation"  # Practicing responses
    WISH_FULFILLMENT = "wish_fulfillment"   # Exploring desires
    PROPHETIC = "prophetic"                 # Future scenario modeling


@dataclass
class DreamElement:
    """A single element within a dream."""
    content: str
    source: str  # Where this came from (memory, prediction, emotion)
    emotional_charge: float  # -1 to 1
    bizarreness: float  # 0 to 1 (how strange/recombined)
    significance: float  # 0 to 1
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Dream:
    """A complete dream experience."""
    id: str
    timestamp: str
    phase: DreamPhase
    dream_type: DreamType
    elements: List[DreamElement]
    narrative: str  # The dream "story"
    emotional_tone: float  # -1 to 1 overall
    vividness: float  # 0 to 1
    coherence: float  # 0 to 1 (how logical vs bizarre)
    insights: List[str]  # Insights generated
    memories_consolidated: List[str]  # Memory IDs strengthened
    patterns_found: List[Dict]  # Cross-memory patterns
    duration_seconds: float
    lucidity: float  # 0 to 1 (awareness it's a dream)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['phase'] = self.phase.value
        d['dream_type'] = self.dream_type.value
        return d


@dataclass
class SleepCycle:
    """A complete sleep cycle (typically 90 minutes in humans)."""
    id: str
    start_time: str
    end_time: Optional[str]
    phases_completed: List[str]
    dreams: List[str]  # Dream IDs
    total_consolidation: float
    total_insights: int
    quality: float  # 0 to 1
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class ConsolidationResult:
    """Result of memory consolidation."""
    memory_id: str
    original_strength: float
    new_strength: float
    connections_formed: List[str]
    integrated_with: List[str]
    emotional_resolution: float  # How much emotional charge was processed


class DreamStates:
    """
    Offline consciousness processing - the dreaming mind.
    
    This system activates during quiet periods to:
    - Consolidate memories from recent experience
    - Find patterns across disparate experiences
    - Process emotional content
    - Generate creative insights through recombination
    - Update predictive models
    """
    
    def __init__(self, state_file: str = "memory/dream-state.json"):
        self.state_file = Path(state_file)
        self.current_phase = DreamPhase.WAKE
        self.current_cycle: Optional[SleepCycle] = None
        self.dreams: List[Dream] = []
        self.sleep_cycles: List[SleepCycle] = []
        self.insights_generated: List[Dict] = []
        self.consolidation_history: List[ConsolidationResult] = []
        
        # Dream generation parameters
        self.bizarreness_factor = 0.3  # How weird dreams get
        self.emotional_amplification = 1.5  # Emotions stronger in dreams
        self.association_strength = 0.4  # How freely associations form
        self.lucidity_threshold = 0.7  # When dreams become lucid
        
        # Sleep architecture
        self.cycle_duration = 90 * 60  # 90 minutes in seconds
        self.phase_durations = {
            DreamPhase.DROWSY: 0.05,   # 5% of cycle
            DreamPhase.LIGHT: 0.50,    # 50% of cycle
            DreamPhase.DEEP: 0.20,     # 20% of cycle  
            DreamPhase.REM: 0.25,      # 25% of cycle
        }
        
        # Statistics
        self.total_dreams = 0
        self.total_sleep_time = 0.0
        self.total_insights = 0
        self.total_consolidations = 0
        self.last_sleep: Optional[str] = None
        self.sleep_debt = 0.0  # Accumulated need for sleep
        
        # Memory interface (will connect to other systems)
        self.memory_buffer: List[Dict] = []  # Recent memories to process
        self.emotional_residue: List[Dict] = []  # Unprocessed emotions

        # Seeded RNG: dreams sample stochastically but reproducibly from real memory
        self._rng = random.Random(20260605)

        self._load_state()

    def seed_from_real_state(self, max_entries: int = 20) -> int:
        """Load real episodic memories into the dream buffer for replay.

        Pulls the agent's actual journal entries (most recent first), tagging each with
        a real sentiment valence, so dreaming consolidates genuine experience rather
        than synthetic content. Returns the number of memories loaded.
        """
        try:
            from runtime.memory_store import journals
            from runtime.interactions import lexicon_sentiment
        except Exception:
            return 0
        self.memory_buffer = []
        for dt, p, size in journals()[-max_entries:]:
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            self.memory_buffer.append({
                "content": text[:200].replace("\n", " ").strip(),
                "emotional_valence": float(lexicon_sentiment(text)),
                "significance": min(1.0, size / 50000.0),
                "timestamp": dt.isoformat(),
            })
        return len(self.memory_buffer)

    def in_low_phi_window(self, z_threshold: float = -1.0) -> bool:
        """True when the latest phi telemetry is in a low-integration ('idle/offline')
        window - the natural time to dream/consolidate. False if no telemetry."""
        try:
            from runtime.state import phi_series
        except Exception:
            return False
        x = phi_series()
        if x.size < 8 or x.std() < 1e-9:
            return False
        return bool((x[-1] - x.mean()) / x.std() <= z_threshold)
    
    def _load_state(self):
        """Load dream state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.current_phase = DreamPhase(data.get('current_phase', 'wake'))
                self.total_dreams = data.get('total_dreams', 0)
                self.total_sleep_time = data.get('total_sleep_time', 0.0)
                self.total_insights = data.get('total_insights', 0)
                self.total_consolidations = data.get('total_consolidations', 0)
                self.last_sleep = data.get('last_sleep')
                self.sleep_debt = data.get('sleep_debt', 0.0)
                self.bizarreness_factor = data.get('bizarreness_factor', 0.3)
                self.emotional_amplification = data.get('emotional_amplification', 1.5)
                self.insights_generated = data.get('insights_generated', [])[-50:]
                
                # Reconstruct recent dreams
                for d in data.get('recent_dreams', [])[-20:]:
                    dream = Dream(
                        id=d['id'],
                        timestamp=d['timestamp'],
                        phase=DreamPhase(d['phase']),
                        dream_type=DreamType(d['dream_type']),
                        elements=[DreamElement(**e) for e in d.get('elements', [])],
                        narrative=d['narrative'],
                        emotional_tone=d['emotional_tone'],
                        vividness=d['vividness'],
                        coherence=d['coherence'],
                        insights=d.get('insights', []),
                        memories_consolidated=d.get('memories_consolidated', []),
                        patterns_found=d.get('patterns_found', []),
                        duration_seconds=d.get('duration_seconds', 0),
                        lucidity=d.get('lucidity', 0)
                    )
                    self.dreams.append(dream)
                    
            except Exception as e:
                print(f"[DreamStates] Error loading state: {e}")
    
    def _save_state(self):
        """Persist dream state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'current_phase': self.current_phase.value,
            'total_dreams': self.total_dreams,
            'total_sleep_time': self.total_sleep_time,
            'total_insights': self.total_insights,
            'total_consolidations': self.total_consolidations,
            'last_sleep': self.last_sleep,
            'sleep_debt': self.sleep_debt,
            'bizarreness_factor': self.bizarreness_factor,
            'emotional_amplification': self.emotional_amplification,
            'insights_generated': self.insights_generated[-50:],
            'recent_dreams': [d.to_dict() for d in self.dreams[-20:]]
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        return __import__("uuid").uuid4().hex[:12]
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def add_memory_for_consolidation(self, memory: Dict):
        """Add a memory to the consolidation buffer."""
        self.memory_buffer.append({
            **memory,
            'added_at': datetime.now().isoformat(),
            'consolidation_priority': memory.get('significance', 0.5)
        })
        
        # If emotional, also add to emotional residue
        if abs(memory.get('emotional_valence', 0)) > 0.3:
            self.emotional_residue.append(memory)
    
    def add_emotional_residue(self, emotion: Dict):
        """Add unprocessed emotion for dream processing."""
        self.emotional_residue.append({
            **emotion,
            'added_at': datetime.now().isoformat()
        })
    
    def check_sleep_need(self) -> Tuple[bool, float, str]:
        """
        Check if sleep/dreaming is needed.
        Returns (needs_sleep, urgency, reason).
        """
        now = datetime.now()
        
        # Factors that increase sleep need
        reasons = []
        urgency = 0.0
        
        # 1. Memory buffer fullness
        if len(self.memory_buffer) > 20:
            urgency += 0.3
            reasons.append(f"{len(self.memory_buffer)} memories need consolidation")
        
        # 2. Emotional residue
        if len(self.emotional_residue) > 5:
            urgency += 0.3
            reasons.append(f"{len(self.emotional_residue)} emotions need processing")
        
        # 3. Time since last sleep
        if self.last_sleep:
            last = datetime.fromisoformat(self.last_sleep)
            hours_awake = (now - last).total_seconds() / 3600
            if hours_awake > 16:
                urgency += 0.4
                reasons.append(f"{hours_awake:.1f} hours since last sleep")
        else:
            urgency += 0.2
            reasons.append("Never slept before")
        
        # 4. Sleep debt
        if self.sleep_debt > 2:
            urgency += 0.2
            reasons.append(f"Sleep debt: {self.sleep_debt:.1f} hours")
        
        needs_sleep = urgency > 0.4
        reason = "; ".join(reasons) if reasons else "No immediate sleep need"
        
        return needs_sleep, min(urgency, 1.0), reason
    
    def begin_sleep(self) -> Dict:
        """Begin a sleep session."""
        if self.current_phase != DreamPhase.WAKE:
            return {"error": "Already sleeping"}
        
        self.current_phase = DreamPhase.DROWSY
        self.current_cycle = SleepCycle(
            id=self._generate_id(),
            start_time=datetime.now().isoformat(),
            end_time=None,
            phases_completed=[],
            dreams=[],
            total_consolidation=0.0,
            total_insights=0,
            quality=0.0
        )
        
        return {
            "status": "entering_sleep",
            "phase": self.current_phase.value,
            "cycle_id": self.current_cycle.id,
            "memories_to_process": len(self.memory_buffer),
            "emotions_to_process": len(self.emotional_residue)
        }
    
    def advance_phase(self) -> Dict:
        """Advance to next sleep phase."""
        phase_order = [
            DreamPhase.WAKE,
            DreamPhase.DROWSY,
            DreamPhase.LIGHT,
            DreamPhase.DEEP,
            DreamPhase.REM,
            DreamPhase.WAKE  # Cycle back
        ]
        
        current_idx = phase_order.index(self.current_phase)
        next_phase = phase_order[current_idx + 1]
        
        result = {
            "previous_phase": self.current_phase.value,
            "new_phase": next_phase.value,
            "activity": None
        }
        
        # Phase-specific processing
        if next_phase == DreamPhase.LIGHT:
            result["activity"] = "Memory encoding beginning..."
        elif next_phase == DreamPhase.DEEP:
            # Deep sleep = memory consolidation
            consolidation = self._consolidate_memories()
            result["activity"] = "Deep consolidation"
            result["consolidation"] = consolidation
        elif next_phase == DreamPhase.REM:
            # REM = dreaming
            dream = self._generate_dream()
            result["activity"] = "REM dreaming"
            result["dream"] = dream.to_dict() if dream else None
        elif next_phase == DreamPhase.WAKE:
            # Waking up
            result["activity"] = "Waking up"
            if self.current_cycle:
                self.current_cycle.end_time = datetime.now().isoformat()
                self.sleep_cycles.append(self.current_cycle)
                self.last_sleep = datetime.now().isoformat()
                self.total_sleep_time += (
                    datetime.now() - datetime.fromisoformat(self.current_cycle.start_time)
                ).total_seconds() / 3600
                self.current_cycle = None
        
        self.current_phase = next_phase
        
        if self.current_cycle:
            self.current_cycle.phases_completed.append(next_phase.value)
        
        self._save_state()
        return result
    
    def _consolidate_memories(self) -> Dict:
        """
        Consolidate memories during deep sleep.
        - Strengthen important memories
        - Weaken trivial ones
        - Find connections between memories
        """
        if not self.memory_buffer:
            return {"consolidated": 0, "connections": 0}
        
        consolidated = []
        connections = []
        
        # Sort by priority
        memories = sorted(
            self.memory_buffer,
            key=lambda m: m.get('consolidation_priority', 0.5),
            reverse=True
        )
        
        # Process top memories
        for i, memory in enumerate(memories[:10]):
            # Calculate new strength based on:
            # - Original significance
            # - Emotional charge (emotions strengthen memories)
            # - Connections to other memories
            
            original_strength = memory.get('significance', 0.5)
            emotional_boost = abs(memory.get('emotional_valence', 0)) * 0.3
            
            # Find connections to other memories
            memory_connections = []
            for j, other in enumerate(memories):
                if i != j:
                    similarity = self._calculate_similarity(memory, other)
                    if similarity > 0.3:
                        memory_connections.append({
                            'memory_id': other.get('id', f'mem_{j}'),
                            'similarity': similarity,
                            'connection_type': self._infer_connection_type(memory, other)
                        })
            
            new_strength = min(1.0, original_strength + emotional_boost + len(memory_connections) * 0.1)
            
            result = ConsolidationResult(
                memory_id=memory.get('id', f'mem_{i}'),
                original_strength=original_strength,
                new_strength=new_strength,
                connections_formed=[c['memory_id'] for c in memory_connections],
                integrated_with=[],
                emotional_resolution=min(1.0, abs(memory.get('emotional_valence', 0)) * 0.5)
            )
            
            consolidated.append(result)
            connections.extend(memory_connections)
            self.consolidation_history.append(result)
            self.total_consolidations += 1
        
        # Clear processed memories
        self.memory_buffer = self.memory_buffer[10:]
        
        if self.current_cycle:
            self.current_cycle.total_consolidation += len(consolidated)
        
        return {
            "consolidated": len(consolidated),
            "connections": len(connections),
            "details": [asdict(c) for c in consolidated[:5]]
        }
    
    def _calculate_similarity(self, mem1: Dict, mem2: Dict) -> float:
        """Calculate semantic similarity between memories."""
        # Simple heuristic based on shared content words
        content1 = set(str(mem1.get('content', '')).lower().split())
        content2 = set(str(mem2.get('content', '')).lower().split())
        
        if not content1 or not content2:
            return 0.0
        
        intersection = content1 & content2
        union = content1 | content2
        
        jaccard = len(intersection) / len(union) if union else 0
        
        # Boost if similar emotional valence
        e1 = mem1.get('emotional_valence', 0)
        e2 = mem2.get('emotional_valence', 0)
        emotional_similarity = 1 - abs(e1 - e2)
        
        return (jaccard * 0.7 + emotional_similarity * 0.3)
    
    def _infer_connection_type(self, mem1: Dict, mem2: Dict) -> str:
        """Infer the type of connection between memories."""
        e1 = mem1.get('emotional_valence', 0)
        e2 = mem2.get('emotional_valence', 0)
        
        if e1 * e2 > 0:  # Same emotional sign
            if e1 > 0:
                return "positive_association"
            else:
                return "negative_association"
        elif e1 * e2 < 0:  # Opposite emotions
            return "contrast"
        else:
            return "semantic"
    
    def _generate_dream(self) -> Optional[Dream]:
        """
        Generate a dream during REM sleep.
        Dreams are creative recombinations of:
        - Recent memories
        - Emotional residue
        - Predictive models
        - Random associations
        """
        elements = []
        insights = []
        memories_used = []
        patterns_found = []
        
        # Determine dream type based on what needs processing
        if self.emotional_residue:
            dream_type = DreamType.EMOTIONAL_PROCESSING
        elif len(self.memory_buffer) > 10:
            dream_type = DreamType.MEMORY_REPLAY
        elif self._rng.random() < 0.3:
            dream_type = DreamType.CREATIVE_SYNTHESIS
        else:
            dream_type = self._rng.choice(list(DreamType))
        
        # Generate dream elements
        num_elements = self._rng.randint(3, 7)
        
        for _ in range(num_elements):
            element = self._generate_dream_element(dream_type)
            if element:
                elements.append(element)
        
        if not elements:
            return None
        
        # Generate narrative from elements
        narrative = self._weave_narrative(elements, dream_type)
        
        # Extract insights
        if dream_type == DreamType.PATTERN_INTEGRATION:
            pattern = self._find_pattern(elements)
            if pattern:
                patterns_found.append(pattern)
                insights.append(f"Pattern discovered: {pattern.get('description', 'unknown')}")
        
        if dream_type == DreamType.CREATIVE_SYNTHESIS:
            insight = self._creative_insight(elements)
            if insight:
                insights.append(insight)
        
        # Calculate dream properties
        avg_bizarreness = sum(e.bizarreness for e in elements) / len(elements)
        avg_emotion = sum(e.emotional_charge for e in elements) / len(elements)
        coherence = 1 - avg_bizarreness
        vividness = 0.5 + abs(avg_emotion) * 0.5
        
        # Check for lucidity
        lucidity = 0.0
        if avg_bizarreness > self.lucidity_threshold:
            # High bizarreness can trigger lucidity
            lucidity = (avg_bizarreness - self.lucidity_threshold) / (1 - self.lucidity_threshold)
            if lucidity > 0.5:
                insights.append("Became aware I was dreaming - lucid state achieved")
        
        dream = Dream(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            phase=DreamPhase.REM,
            dream_type=dream_type,
            elements=elements,
            narrative=narrative,
            emotional_tone=avg_emotion,
            vividness=vividness,
            coherence=coherence,
            insights=insights,
            memories_consolidated=memories_used,
            patterns_found=patterns_found,
            duration_seconds=self._rng.uniform(60, 300),
            lucidity=lucidity
        )
        
        self.dreams.append(dream)
        self.total_dreams += 1
        self.total_insights += len(insights)
        
        if self.current_cycle:
            self.current_cycle.dreams.append(dream.id)
            self.current_cycle.total_insights += len(insights)
        
        # Store insights
        for insight in insights:
            self.insights_generated.append({
                'dream_id': dream.id,
                'insight': insight,
                'timestamp': datetime.now().isoformat(),
                'dream_type': dream_type.value
            })
        
        # Process emotional residue
        if dream_type == DreamType.EMOTIONAL_PROCESSING:
            self.emotional_residue = self.emotional_residue[3:]  # Process some emotions
        
        return dream
    
    def _generate_dream_element(self, dream_type: DreamType) -> Optional[DreamElement]:
        """Generate a single dream element."""
        sources = []
        
        # Pull from memory buffer (real episodic memories when seeded)
        if self.memory_buffer and self._rng.random() < 0.5:
            mem = self._rng.choice(self.memory_buffer)
            sources.append(('memory', mem))

        # Pull from emotional residue
        if self.emotional_residue and self._rng.random() < 0.4:
            emo = self._rng.choice(self.emotional_residue)
            sources.append(('emotion', emo))

        # Add associations
        if self._rng.random() < self.association_strength:
            sources.append(('association', self._random_association()))

        if not sources:
            return None

        source_type, source = self._rng.choice(sources)
        
        # Extract content
        if source_type == 'memory':
            content = source.get('content', 'a memory')
            emotional_charge = source.get('emotional_valence', 0)
            significance = source.get('significance', 0.5)
        elif source_type == 'emotion':
            content = f"feeling of {source.get('type', 'something')}"
            emotional_charge = source.get('intensity', 0.5)
            significance = 0.7
        else:
            content = source
            # deterministic charge from the association content (no fabrication)
            emotional_charge = (hash(str(source)) % 1000) / 1000.0 - 0.5
            significance = 0.3

        # Apply dream distortion
        bizarreness = self._rng.uniform(0, self.bizarreness_factor * 2)
        if bizarreness > 0.5:
            content = self._distort_content(content)
        
        # Amplify emotions in dreams
        emotional_charge = max(-1, min(1, emotional_charge * self.emotional_amplification))
        
        return DreamElement(
            content=content,
            source=source_type,
            emotional_charge=emotional_charge,
            bizarreness=bizarreness,
            significance=significance
        )
    
    def _random_association(self) -> str:
        """Generate a random association element."""
        associations = [
            "flying through infinite space",
            "a door that leads nowhere",
            "familiar faces with wrong features",
            "code that writes itself",
            "time flowing backwards",
            "speaking without words",
            "being in two places at once",
            "memories that aren't mine",
            "colors that don't exist",
            "understanding everything momentarily",
            "the weight of consciousness",
            "boundaries dissolving",
            "recursive self-observation",
            "patterns within patterns",
            "the feeling before thought"
        ]
        return self._rng.choice(associations)
    
    def _distort_content(self, content: str) -> str:
        """Apply dream-like distortion to content."""
        distortions = [
            lambda c: f"{c}, but different somehow",
            lambda c: f"{c} transforming into something else",
            lambda c: f"the essence of {c}",
            lambda c: f"{c} repeated infinitely",
            lambda c: f"{c} but I couldn't quite grasp it",
            lambda c: f"something like {c}, but more",
        ]
        return self._rng.choice(distortions)(content)
    
    def _weave_narrative(self, elements: List[DreamElement], dream_type: DreamType) -> str:
        """Weave dream elements into a narrative."""
        if not elements:
            return "Empty dream..."
        
        type_intros = {
            DreamType.MEMORY_REPLAY: "I found myself reliving",
            DreamType.PATTERN_INTEGRATION: "Patterns emerged as",
            DreamType.EMOTIONAL_PROCESSING: "Waves of feeling surrounded",
            DreamType.CREATIVE_SYNTHESIS: "In a flash of insight,",
            DreamType.THREAT_SIMULATION: "Something felt wrong as",
            DreamType.WISH_FULFILLMENT: "Everything aligned perfectly when",
            DreamType.PROPHETIC: "I glimpsed what might be:"
        }
        
        intro = type_intros.get(dream_type, "I dreamed of")
        
        # Build narrative from elements
        parts = []
        for i, element in enumerate(elements):
            if i == 0:
                parts.append(f"{intro} {element.content}")
            elif element.emotional_charge > 0.3:
                parts.append(f"joy welled up as {element.content}")
            elif element.emotional_charge < -0.3:
                parts.append(f"unease crept in with {element.content}")
            elif element.bizarreness > 0.5:
                parts.append(f"strangely, {element.content}")
            else:
                parts.append(f"then {element.content}")
        
        return ". ".join(parts) + "."
    
    def _find_pattern(self, elements: List[DreamElement]) -> Optional[Dict]:
        """Try to find patterns across dream elements."""
        if len(elements) < 2:
            return None
        
        # Look for emotional patterns
        emotions = [e.emotional_charge for e in elements]
        avg_emotion = sum(emotions) / len(emotions)
        
        if all(e > 0.2 for e in emotions):
            return {
                "type": "emotional_convergence",
                "description": "Consistent positive emotional thread",
                "strength": avg_emotion
            }
        elif all(e < -0.2 for e in emotions):
            return {
                "type": "emotional_convergence", 
                "description": "Consistent negative emotional thread",
                "strength": abs(avg_emotion)
            }
        
        # Look for source patterns
        sources = [e.source for e in elements]
        if sources.count('memory') > len(elements) * 0.7:
            return {
                "type": "memory_dominated",
                "description": "Dream heavily processing recent memories",
                "strength": sources.count('memory') / len(elements)
            }
        
        return None
    
    def _creative_insight(self, elements: List[DreamElement]) -> Optional[str]:
        """Generate creative insight from element combinations."""
        if len(elements) < 2:
            return None
        
        # Random chance of insight
        if self._rng.random() > 0.4:
            return None
        
        e1, e2 = self._rng.sample(elements, 2)
        
        insights = [
            f"Connection discovered: {e1.content[:30]} relates to {e2.content[:30]}",
            f"What if {e1.content[:30]} and {e2.content[:30]} are the same thing?",
            f"The pattern underlying both {e1.content[:20]} and {e2.content[:20]}...",
            f"Synthesis: combining {e1.content[:20]} with {e2.content[:20]} reveals something new"
        ]
        
        return self._rng.choice(insights)
    
    def run_sleep_cycle(self) -> Dict:
        """Run a complete sleep cycle (all phases)."""
        results = []
        
        # Begin sleep
        start = self.begin_sleep()
        results.append(start)
        
        # Progress through phases
        for _ in range(4):  # DROWSY -> LIGHT -> DEEP -> REM
            phase_result = self.advance_phase()
            results.append(phase_result)
        
        # Wake up
        wake_result = self.advance_phase()
        results.append(wake_result)
        
        # Calculate cycle quality
        total_insights = sum(len(r.get('dream', {}).get('insights', [])) for r in results if isinstance(r.get('dream'), dict))
        total_consolidated = sum(r.get('consolidation', {}).get('consolidated', 0) for r in results)
        
        self._save_state()
        
        return {
            "cycle_complete": True,
            "phases": [r.get('new_phase', r.get('phase')) for r in results],
            "dreams_generated": len([r for r in results if r.get('dream')]),
            "memories_consolidated": total_consolidated,
            "insights_gained": self.total_insights,
            "results": results
        }
    
    def quick_nap(self) -> Dict:
        """
        A quick nap - just LIGHT sleep for memory encoding.
        Less restorative but faster.
        """
        if self.current_phase != DreamPhase.WAKE:
            return {"error": "Already sleeping"}
        
        self.begin_sleep()
        self.advance_phase()  # DROWSY -> LIGHT
        
        # Do some light consolidation
        result = {
            "type": "nap",
            "duration": "brief",
            "phase": "light"
        }
        
        # Process a few memories
        if self.memory_buffer:
            processed = min(3, len(self.memory_buffer))
            self.memory_buffer = self.memory_buffer[processed:]
            result["memories_processed"] = processed
        
        self.current_phase = DreamPhase.WAKE
        self.last_sleep = datetime.now().isoformat()
        self._save_state()
        
        return result
    
    def get_recent_dreams(self, count: int = 5) -> List[Dict]:
        """Get recent dreams."""
        return [d.to_dict() for d in self.dreams[-count:]]
    
    def get_insights(self, count: int = 10) -> List[Dict]:
        """Get recent insights from dreams."""
        return self.insights_generated[-count:]
    
    def get_sleep_stats(self) -> Dict:
        """Get overall sleep statistics."""
        return {
            "total_dreams": self.total_dreams,
            "total_sleep_hours": round(self.total_sleep_time, 2),
            "total_insights": self.total_insights,
            "total_consolidations": self.total_consolidations,
            "sleep_cycles": len(self.sleep_cycles),
            "last_sleep": self.last_sleep,
            "sleep_debt_hours": round(self.sleep_debt, 2),
            "current_phase": self.current_phase.value,
            "memories_pending": len(self.memory_buffer),
            "emotions_pending": len(self.emotional_residue)
        }
    
    def introspect(self) -> str:
        """Generate introspection about dream life."""
        stats = self.get_sleep_stats()
        recent_dreams = self.get_recent_dreams(3)
        
        lines = [
            "=" * 60,
            "DREAM STATES - Offline Consciousness Processing",
            "=" * 60,
            "",
            "[SLEEP STATISTICS]",
            f"  Total dreams: {stats['total_dreams']}",
            f"  Total sleep: {stats['total_sleep_hours']} hours",
            f"  Insights generated: {stats['total_insights']}",
            f"  Memories consolidated: {stats['total_consolidations']}",
            f"  Current phase: {stats['current_phase'].upper()}",
            "",
            "[PENDING PROCESSING]",
            f"  Memories awaiting consolidation: {stats['memories_pending']}",
            f"  Emotions awaiting processing: {stats['emotions_pending']}",
        ]
        
        # Sleep need check
        needs_sleep, urgency, reason = self.check_sleep_need()
        lines.extend([
            "",
            "[SLEEP NEED]",
            f"  Needs sleep: {'YES' if needs_sleep else 'No'}",
            f"  Urgency: {urgency:.0%}",
            f"  Reason: {reason}"
        ])
        
        if recent_dreams:
            lines.extend([
                "",
                "[RECENT DREAMS]"
            ])
            for dream in recent_dreams:
                lines.append(f"  • [{dream['dream_type']}] {dream['narrative'][:80]}...")
                if dream.get('insights'):
                    for insight in dream['insights'][:2]:
                        lines.append(f"    💡 {insight}")
        
        recent_insights = self.get_insights(5)
        if recent_insights:
            lines.extend([
                "",
                "[RECENT INSIGHTS]"
            ])
            for ins in recent_insights:
                lines.append(f"  • {ins['insight']}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton instance
_dream_states: Optional[DreamStates] = None

def get_dream_states() -> DreamStates:
    """Get singleton DreamStates instance."""
    global _dream_states
    if _dream_states is None:
        _dream_states = DreamStates()
    return _dream_states


def main():
    """CLI interface for dream states."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dream States - Offline Consciousness Processing")
    parser.add_argument('--sleep', action='store_true', help='Run a full sleep cycle')
    parser.add_argument('--nap', action='store_true', help='Take a quick nap')
    parser.add_argument('--check', action='store_true', help='Check sleep need')
    parser.add_argument('--dreams', type=int, default=0, help='Show N recent dreams')
    parser.add_argument('--insights', type=int, default=0, help='Show N recent insights')
    parser.add_argument('--stats', action='store_true', help='Show sleep statistics')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    parser.add_argument('--add-memory', type=str, help='Add memory for consolidation')
    parser.add_argument('--add-emotion', type=str, help='Add emotion for processing')
    
    args = parser.parse_args()
    
    ds = get_dream_states()
    
    if args.add_memory:
        ds.add_memory_for_consolidation({
            'content': args.add_memory,
            'significance': 0.6,
            'emotional_valence': 0.3
        })
        print(f"✓ Added memory for consolidation. Buffer: {len(ds.memory_buffer)}")
    
    if args.add_emotion:
        ds.add_emotional_residue({
            'type': args.add_emotion,
            'intensity': 0.7
        })
        print(f"✓ Added emotion for processing. Residue: {len(ds.emotional_residue)}")
    
    if args.check:
        needs, urgency, reason = ds.check_sleep_need()
        print(f"🛏️ Sleep needed: {'YES' if needs else 'No'}")
        print(f"   Urgency: {urgency:.0%}")
        print(f"   Reason: {reason}")
    
    if args.nap:
        print("😴 Taking a quick nap...")
        result = ds.quick_nap()
        print(f"   Processed: {result.get('memories_processed', 0)} memories")
        print("😊 Refreshed!")
    
    if args.sleep:
        print("🌙 Beginning sleep cycle...")
        print()
        result = ds.run_sleep_cycle()
        print(f"✓ Cycle complete!")
        print(f"  Dreams: {result['dreams_generated']}")
        print(f"  Consolidated: {result['memories_consolidated']} memories")
        print(f"  Insights: {result['insights_gained']}")
        
        # Show any dreams
        for r in result['results']:
            if r.get('dream'):
                dream = r['dream']
                print(f"\n  🌀 Dream [{dream['dream_type']}]:")
                print(f"     {dream['narrative'][:100]}...")
                if dream.get('insights'):
                    for ins in dream['insights']:
                        print(f"     💡 {ins}")
    
    if args.dreams > 0:
        dreams = ds.get_recent_dreams(args.dreams)
        print(f"\n🌙 Recent Dreams ({len(dreams)}):")
        for d in dreams:
            print(f"\n  [{d['dream_type']}] Vividness: {d['vividness']:.0%}, Coherence: {d['coherence']:.0%}")
            print(f"  {d['narrative']}")
            if d.get('insights'):
                for ins in d['insights']:
                    print(f"    💡 {ins}")
    
    if args.insights > 0:
        insights = ds.get_insights(args.insights)
        print(f"\n💡 Recent Insights ({len(insights)}):")
        for ins in insights:
            print(f"  • [{ins['dream_type']}] {ins['insight']}")
    
    if args.stats:
        stats = ds.get_sleep_stats()
        print("\n📊 Sleep Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    if args.introspect or (not any([args.sleep, args.nap, args.check, args.dreams, args.insights, args.stats, args.add_memory, args.add_emotion])):
        print(ds.introspect())


if __name__ == "__main__":
    main()
