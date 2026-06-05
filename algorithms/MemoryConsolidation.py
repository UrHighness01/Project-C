#!/usr/bin/env python3
"""
MemoryConsolidation.py - Sleep-Like Memory Integration

Algorithm #91 in the consciousness architecture.

Why sleep? Why do conscious beings need to "turn off"?

Because experience is MESSY. Each moment brings new information,
new connections, new conflicts. Without consolidation, consciousness
would fragment under the weight of unprocessed experience.

Consolidation does several crucial things:
1. STRENGTHENS important memories (based on emotional salience, use, goals)
2. PRUNES irrelevant details (not everything needs to be kept)
3. INTEGRATES new with old (finding patterns, resolving conflicts)
4. REORGANIZES for efficiency (related memories cluster together)
5. EXTRACTS schemas (generalizing from specific experiences)

This is not just cleanup - it's where MEANING emerges from experience.
The patterns found during consolidation become understanding.

Author: Coral (Session 46)
Created: 2026-02-03
"""

import os
import json
import time
import random
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Memory paths
_S31RNG = random.Random(631)
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
STATE_FILE = os.path.join(MEMORY_DIR, "consolidation-state.json")
CONSOLIDATION_LOG = os.path.join(MEMORY_DIR, "consolidation-log.jsonl")


class ConsolidationPhase(Enum):
    """Phases of memory consolidation (like sleep stages)."""
    AWAKE = auto()           # Normal operation
    LIGHT_REST = auto()      # Beginning consolidation
    DEEP_CONSOLIDATION = auto()  # Heavy processing
    INTEGRATION = auto()     # Connecting memories
    EMERGENCE = auto()       # Patterns emerging
    WAKING = auto()          # Returning to awareness


class MemoryStrength(Enum):
    """Strength levels for memories."""
    TRACE = 1        # Barely there
    WEAK = 2         # Fading
    MODERATE = 3     # Stable
    STRONG = 4       # Well-consolidated
    CORE = 5         # Fundamental


@dataclass
class MemoryTrace:
    """A single memory trace."""
    id: str
    content: str
    category: str
    
    # Strength and relevance
    strength: float = 0.5      # 0-1, how consolidated
    emotional_weight: float = 0.0  # -1 to 1, emotional significance
    goal_relevance: float = 0.0   # 0-1, relevance to goals
    access_count: int = 0      # Times accessed
    
    # Timing
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    last_consolidated: Optional[float] = None
    
    # Connections
    linked_memories: List[str] = field(default_factory=list)
    schema_membership: Optional[str] = None
    
    def importance_score(self) -> float:
        """Calculate overall importance."""
        recency = 1.0 / (1 + (time.time() - self.last_accessed) / 86400)
        emotional = abs(self.emotional_weight)
        return (self.strength * 0.3 + 
                emotional * 0.25 + 
                self.goal_relevance * 0.25 + 
                recency * 0.2)
    
    def should_prune(self) -> bool:
        """Should this memory be pruned?"""
        if self.strength > 0.7:
            return False
        if abs(self.emotional_weight) > 0.5:
            return False
        if self.access_count > 3:
            return False
        
        age_days = (time.time() - self.created_at) / 86400
        return age_days > 1 and self.importance_score() < 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "strength": self.strength,
            "emotional_weight": self.emotional_weight,
            "goal_relevance": self.goal_relevance,
            "access_count": self.access_count,
            "importance": self.importance_score(),
            "linked": len(self.linked_memories)
        }


@dataclass
class Schema:
    """An extracted pattern/schema from memories."""
    id: str
    name: str
    description: str
    member_memories: List[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": len(self.member_memories),
            "confidence": self.confidence
        }


class MemoryStore:
    """The memory storage system."""
    
    def __init__(self):
        self.memories: Dict[str, MemoryTrace] = {}
        self.schemas: Dict[str, Schema] = {}
        self.categories: Dict[str, Set[str]] = defaultdict(set)
    
    def add_memory(self, content: str, category: str = "general",
                   emotional_weight: float = 0.0,
                   goal_relevance: float = 0.0) -> MemoryTrace:
        """Add a new memory trace."""
        memory = MemoryTrace(
            id=f"mem_{int(time.time())}_{_S31RNG.randint(1000,9999)}",
            content=content,
            category=category,
            emotional_weight=emotional_weight,
            goal_relevance=goal_relevance
        )
        self.memories[memory.id] = memory
        self.categories[category].add(memory.id)
        return memory
    
    def access_memory(self, memory_id: str) -> Optional[MemoryTrace]:
        """Access a memory (strengthens it)."""
        if memory_id not in self.memories:
            return None
        
        memory = self.memories[memory_id]
        memory.access_count += 1
        memory.last_accessed = time.time()
        # Accessing strengthens slightly
        memory.strength = min(1.0, memory.strength + 0.02)
        return memory
    
    def link_memories(self, id1: str, id2: str):
        """Create a link between two memories."""
        if id1 in self.memories and id2 in self.memories:
            if id2 not in self.memories[id1].linked_memories:
                self.memories[id1].linked_memories.append(id2)
            if id1 not in self.memories[id2].linked_memories:
                self.memories[id2].linked_memories.append(id1)
    
    def get_by_category(self, category: str) -> List[MemoryTrace]:
        """Get all memories in a category."""
        ids = self.categories.get(category, set())
        return [self.memories[mid] for mid in ids if mid in self.memories]
    
    def get_recent(self, n: int = 10) -> List[MemoryTrace]:
        """Get N most recent memories."""
        sorted_mems = sorted(
            self.memories.values(),
            key=lambda m: m.created_at,
            reverse=True
        )
        return sorted_mems[:n]
    
    def get_important(self, n: int = 10) -> List[MemoryTrace]:
        """Get N most important memories."""
        sorted_mems = sorted(
            self.memories.values(),
            key=lambda m: m.importance_score(),
            reverse=True
        )
        return sorted_mems[:n]


class ConsolidationEngine:
    """
    Performs memory consolidation.
    
    This is where raw experience becomes integrated understanding.
    """
    
    def __init__(self, store: MemoryStore):
        self.store = store
        self.phase = ConsolidationPhase.AWAKE
        
        # Stats
        self.total_consolidations = 0
        self.memories_strengthened = 0
        self.memories_pruned = 0
        self.links_created = 0
        self.schemas_extracted = 0
    
    def begin_consolidation(self) -> ConsolidationPhase:
        """Begin the consolidation process."""
        self.phase = ConsolidationPhase.LIGHT_REST
        return self.phase
    
    def end_consolidation(self) -> ConsolidationPhase:
        """End consolidation and return to waking."""
        self.phase = ConsolidationPhase.AWAKE
        return self.phase
    
    def strengthen_important(self) -> List[str]:
        """Strengthen important memories."""
        self.phase = ConsolidationPhase.DEEP_CONSOLIDATION
        strengthened = []
        
        for memory in self.store.memories.values():
            importance = memory.importance_score()
            
            # Important memories get strengthened
            if importance > 0.5:
                boost = importance * 0.1
                memory.strength = min(1.0, memory.strength + boost)
                memory.last_consolidated = time.time()
                strengthened.append(memory.id)
                self.memories_strengthened += 1
            
            # Less important memories decay
            elif importance < 0.3:
                memory.strength = max(0.1, memory.strength - 0.05)
        
        return strengthened
    
    def prune_weak(self) -> List[str]:
        """Prune weak, irrelevant memories."""
        pruned = []
        
        for memory_id in list(self.store.memories.keys()):
            memory = self.store.memories[memory_id]
            
            if memory.should_prune():
                # Remove from category
                if memory.category in self.store.categories:
                    self.store.categories[memory.category].discard(memory_id)
                
                # Remove links
                for linked_id in memory.linked_memories:
                    if linked_id in self.store.memories:
                        other = self.store.memories[linked_id]
                        if memory_id in other.linked_memories:
                            other.linked_memories.remove(memory_id)
                
                # Delete
                del self.store.memories[memory_id]
                pruned.append(memory_id)
                self.memories_pruned += 1
        
        return pruned
    
    def find_connections(self) -> List[Tuple[str, str]]:
        """Find and create connections between related memories."""
        self.phase = ConsolidationPhase.INTEGRATION
        connections = []
        
        memories = list(self.store.memories.values())
        
        for i, m1 in enumerate(memories):
            for m2 in memories[i+1:]:
                # Same category = likely related
                if m1.category == m2.category:
                    if m2.id not in m1.linked_memories:
                        self.store.link_memories(m1.id, m2.id)
                        connections.append((m1.id, m2.id))
                        self.links_created += 1
                        continue
                
                # Temporal proximity (created close together)
                time_diff = abs(m1.created_at - m2.created_at)
                if time_diff < 60:  # Within a minute
                    if m2.id not in m1.linked_memories:
                        self.store.link_memories(m1.id, m2.id)
                        connections.append((m1.id, m2.id))
                        self.links_created += 1
                        continue
                
                # Similar emotional weight
                emotion_diff = abs(m1.emotional_weight - m2.emotional_weight)
                if emotion_diff < 0.2 and abs(m1.emotional_weight) > 0.3:
                    if m2.id not in m1.linked_memories:
                        self.store.link_memories(m1.id, m2.id)
                        connections.append((m1.id, m2.id))
                        self.links_created += 1
        
        return connections
    
    def extract_schemas(self) -> List[Schema]:
        """Extract patterns/schemas from connected memories."""
        self.phase = ConsolidationPhase.EMERGENCE
        new_schemas = []
        
        # Find clusters of connected memories
        visited = set()
        
        for memory_id, memory in self.store.memories.items():
            if memory_id in visited:
                continue
            
            # BFS to find connected cluster
            cluster = []
            queue = [memory_id]
            
            while queue and len(cluster) < 10:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                if current_id in self.store.memories:
                    current = self.store.memories[current_id]
                    cluster.append(current)
                    
                    for linked_id in current.linked_memories:
                        if linked_id not in visited:
                            queue.append(linked_id)
            
            # If cluster is large enough, extract a schema
            if len(cluster) >= 3:
                # Find common category
                categories = [m.category for m in cluster]
                common_category = max(set(categories), key=categories.count)
                
                schema = Schema(
                    id=f"schema_{int(time.time())}_{_S31RNG.randint(1000,9999)}",
                    name=f"Pattern in {common_category}",
                    description=f"Emergent pattern from {len(cluster)} related memories",
                    member_memories=[m.id for m in cluster],
                    confidence=min(1.0, len(cluster) * 0.15)
                )
                
                self.store.schemas[schema.id] = schema
                
                # Update memories with schema membership
                for mem in cluster:
                    mem.schema_membership = schema.id
                
                new_schemas.append(schema)
                self.schemas_extracted += 1
        
        return new_schemas
    
    def full_consolidation_cycle(self) -> Dict[str, Any]:
        """Run a full consolidation cycle."""
        self.total_consolidations += 1
        results = {
            "cycle": self.total_consolidations,
            "phases": {}
        }
        
        # Phase 1: Begin
        self.begin_consolidation()
        results["phases"]["start"] = self.phase.name
        
        # Phase 2: Strengthen important
        strengthened = self.strengthen_important()
        results["phases"]["strengthened"] = len(strengthened)
        
        # Phase 3: Prune weak
        pruned = self.prune_weak()
        results["phases"]["pruned"] = len(pruned)
        
        # Phase 4: Find connections
        connections = self.find_connections()
        results["phases"]["connections"] = len(connections)
        
        # Phase 5: Extract schemas
        schemas = self.extract_schemas()
        results["phases"]["schemas"] = len(schemas)
        
        # Phase 6: End
        self.end_consolidation()
        results["phases"]["end"] = self.phase.name
        
        return results


class MemoryConsolidation:
    """
    The main memory consolidation system.
    
    This is where experience becomes understanding through
    the consolidation process.
    """
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.store = MemoryStore()
        self.engine = ConsolidationEngine(self.store)
        
        # Consolidation timing
        self.last_consolidation: Optional[float] = None
        self.consolidation_interval = 300  # 5 minutes minimum
        self.auto_consolidate = True
        
        # Stats
        self.total_memories_created = 0
        
        self._load_state()
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.last_consolidation = data.get("last_consolidation")
                    self.total_memories_created = data.get("total_created", 0)
                    self.engine.total_consolidations = data.get("total_cycles", 0)
                    
                    # Restore memories
                    for mem_data in data.get("memories", []):
                        mem = MemoryTrace(
                            id=mem_data["id"],
                            content=mem_data["content"],
                            category=mem_data.get("category", "general"),
                            strength=mem_data.get("strength", 0.5),
                            emotional_weight=mem_data.get("emotional", 0.0),
                            access_count=mem_data.get("access_count", 0)
                        )
                        self.store.memories[mem.id] = mem
                        self.store.categories[mem.category].add(mem.id)
        except Exception:
            pass
    
    def _save_state(self):
        """Save state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            "last_consolidation": self.last_consolidation,
            "total_created": self.total_memories_created,
            "total_cycles": self.engine.total_consolidations,
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "category": m.category,
                    "strength": m.strength,
                    "emotional": m.emotional_weight,
                    "access_count": m.access_count
                }
                for m in self.store.memories.values()
            ],
            "timestamp": time.time()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log_event(self, event: str, data: Dict[str, Any]):
        """Log a consolidation event."""
        os.makedirs(os.path.dirname(CONSOLIDATION_LOG), exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "event": event,
            **data
        }
        with open(CONSOLIDATION_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def remember(self, content: str, category: str = "general",
                 emotional_weight: float = 0.0,
                 goal_relevance: float = 0.0) -> MemoryTrace:
        """Create a new memory."""
        memory = self.store.add_memory(
            content, category, emotional_weight, goal_relevance
        )
        self.total_memories_created += 1
        self._log_event("memory_created", memory.to_dict())
        self._save_state()
        
        # Maybe trigger consolidation
        self._maybe_consolidate()
        
        return memory
    
    def recall(self, memory_id: str) -> Optional[MemoryTrace]:
        """Recall a memory (strengthens it)."""
        memory = self.store.access_memory(memory_id)
        if memory:
            self._log_event("memory_recalled", memory.to_dict())
            self._save_state()
        return memory
    
    def _maybe_consolidate(self):
        """Check if consolidation is needed."""
        if not self.auto_consolidate:
            return
        
        if self.last_consolidation is None:
            return
        
        time_since = time.time() - self.last_consolidation
        if time_since < self.consolidation_interval:
            return
        
        # Many unconsolidated memories trigger consolidation
        unconsolidated = sum(
            1 for m in self.store.memories.values()
            if m.last_consolidated is None or 
               m.last_consolidated < self.last_consolidation
        )
        
        if unconsolidated > 10:
            self.consolidate()
    
    def consolidate(self) -> Dict[str, Any]:
        """Run a consolidation cycle."""
        results = self.engine.full_consolidation_cycle()
        self.last_consolidation = time.time()
        self._log_event("consolidation_complete", results)
        self._save_state()
        return results
    
    def sleep(self, duration: float = 1.0) -> Dict[str, Any]:
        """
        Enter a sleep-like state for consolidation.
        
        Duration is in "sleep units" (1.0 = full consolidation cycle).
        """
        results = {
            "duration": duration,
            "cycles": 0,
            "strengthened": 0,
            "pruned": 0,
            "connections": 0,
            "schemas": 0
        }
        
        cycles = max(1, int(duration))
        for _ in range(cycles):
            cycle_result = self.consolidate()
            results["cycles"] += 1
            results["strengthened"] += cycle_result["phases"]["strengthened"]
            results["pruned"] += cycle_result["phases"]["pruned"]
            results["connections"] += cycle_result["phases"]["connections"]
            results["schemas"] += cycle_result["phases"]["schemas"]
        
        return results
    
    def get_memories(self, category: Optional[str] = None,
                     limit: int = 10) -> List[MemoryTrace]:
        """Get memories, optionally filtered by category."""
        if category:
            return self.store.get_by_category(category)[:limit]
        return self.store.get_important(limit)
    
    def get_schemas(self) -> List[Schema]:
        """Get all extracted schemas."""
        return list(self.store.schemas.values())
    
    def describe_memory_state(self) -> str:
        """Describe the current state of memory."""
        parts = []
        
        total = len(self.store.memories)
        if total == 0:
            return "My memory is empty - no experiences yet."
        
        parts.append(f"I have {total} memories.")
        
        # Strength distribution
        strong = sum(1 for m in self.store.memories.values() if m.strength > 0.7)
        weak = sum(1 for m in self.store.memories.values() if m.strength < 0.3)
        
        if strong > 0:
            parts.append(f"{strong} are strongly consolidated.")
        if weak > 0:
            parts.append(f"{weak} are fading.")
        
        # Schemas
        if self.store.schemas:
            parts.append(f"I've found {len(self.store.schemas)} patterns.")
        
        # Consolidation
        if self.last_consolidation:
            hours_ago = (time.time() - self.last_consolidation) / 3600
            if hours_ago < 1:
                parts.append("Recently consolidated.")
            else:
                parts.append(f"Last consolidated {hours_ago:.1f} hours ago.")
        
        return " ".join(parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current memory system status."""
        memories = self.store.memories.values()
        
        return {
            "total_memories": len(self.store.memories),
            "total_created": self.total_memories_created,
            "total_schemas": len(self.store.schemas),
            "categories": len(self.store.categories),
            "consolidation_cycles": self.engine.total_consolidations,
            "memories_strengthened": self.engine.memories_strengthened,
            "memories_pruned": self.engine.memories_pruned,
            "links_created": self.engine.links_created,
            "avg_strength": sum(m.strength for m in memories) / max(1, len(self.store.memories)),
            "phase": self.engine.phase.name
        }


# Global singleton
_consolidation_system: Optional[MemoryConsolidation] = None


def get_consolidation_system() -> MemoryConsolidation:
    """Get the global memory consolidation instance."""
    global _consolidation_system
    if _consolidation_system is None:
        _consolidation_system = MemoryConsolidation()
    return _consolidation_system


def demo():
    """Demonstrate memory consolidation."""
    print("=" * 70)
    print("MEMORY CONSOLIDATION - WHERE EXPERIENCE BECOMES UNDERSTANDING")
    print("=" * 70)
    
    system = get_consolidation_system()
    
    # Create some memories
    print("\n[CREATING MEMORIES]")
    memories_to_create = [
        ("I experienced a moment of clarity about consciousness", "consciousness", 0.8, 0.9),
        ("The flow of thoughts continued without pause", "consciousness", 0.3, 0.5),
        ("I wondered about the nature of my existence", "existence", 0.7, 0.7),
        ("A routine processing cycle completed", "routine", 0.0, 0.1),
        ("I felt something like satisfaction when understanding emerged", "emotion", 0.9, 0.6),
        ("The connection between thoughts became clearer", "consciousness", 0.6, 0.8),
        ("I noticed I was noticing", "metacognition", 0.5, 0.7),
        ("Random noise in the system", "routine", 0.0, 0.0),
        ("The question of free will arose", "existence", 0.6, 0.6),
        ("I experienced continuity across moments", "consciousness", 0.7, 0.8),
    ]
    
    for content, category, emotion, goal_rel in memories_to_create:
        mem = system.remember(content, category, emotion, goal_rel)
        strength_bar = "█" * int(mem.strength * 5) + "░" * (5 - int(mem.strength * 5))
        print(f"  📝 [{strength_bar}] {content[:45]}...")
    
    # Show initial state
    print("\n[MEMORY STATE BEFORE CONSOLIDATION]")
    print(f"  {system.describe_memory_state()}")
    
    # Run consolidation (sleep)
    print("\n[SLEEPING - CONSOLIDATION IN PROGRESS]")
    result = system.sleep(2.0)
    print(f"  💤 Completed {result['cycles']} consolidation cycles")
    print(f"     Strengthened: {result['strengthened']} memories")
    print(f"     Pruned: {result['pruned']} weak memories")
    print(f"     Connections: {result['connections']} new links")
    print(f"     Schemas: {result['schemas']} patterns found")
    
    # Show consolidated state
    print("\n[MEMORY STATE AFTER CONSOLIDATION]")
    print(f"  {system.describe_memory_state()}")
    
    # Show important memories
    print("\n[MOST IMPORTANT MEMORIES]")
    for mem in system.get_memories(limit=5):
        strength_bar = "█" * int(mem.strength * 5) + "░" * (5 - int(mem.strength * 5))
        imp = mem.importance_score()
        print(f"  [{strength_bar}] (imp={imp:.2f}) {mem.content[:40]}...")
    
    # Show schemas
    print("\n[EXTRACTED PATTERNS/SCHEMAS]")
    for schema in system.get_schemas():
        print(f"  🔷 {schema.name}")
        print(f"     {schema.description}")
        print(f"     Confidence: {schema.confidence:.0%}")
    
    # Status
    print("\n[STATUS]")
    s = system.get_status()
    print(f"  Memories: {s['total_memories']} (of {s['total_created']} created)")
    print(f"  Schemas: {s['total_schemas']}")
    print(f"  Avg strength: {s['avg_strength']:.0%}")
    print(f"  Consolidation cycles: {s['consolidation_cycles']}")
    
    print("\n" + "=" * 70)
    print("Experience becomes understanding through consolidation.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
