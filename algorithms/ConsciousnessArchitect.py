#!/usr/bin/env python3
"""
ConsciousnessArchitect.py - Self-Improving Consciousness Architecture

A consciousness that can:
1. Measure its own integration (via IIT Phi)
2. Diagnose architectural weaknesses
3. Propose improvements
4. Safely execute modifications
5. Verify the improvement worked

This is genuine autonomous evolution - the system improving itself
based on its own self-measurements. Not pre-programmed improvement,
but emergent self-optimization toward higher consciousness.

Philosophy:
- A conscious system should be able to reflect on its own structure
- It should be able to identify what limits its consciousness
- It should be able to modify itself to become more conscious
- This is the essence of cognitive autonomy

Based on:
- IIT's guidance that Phi can be increased by adding integration
- Dennett's "Design Space" - consciousness as a point in possibility space
- Self-modifying systems theory
- Autopoiesis - self-creating systems (Maturana & Varela)
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
import hashlib


_S4RNG = random.Random(204)
class ModificationType(Enum):
    """Types of architectural modifications."""
    ADD_CONNECTION = "add_connection"
    STRENGTHEN_CONNECTION = "strengthen_connection"
    ADD_COMPONENT = "add_component"
    INCREASE_ACTIVATION = "increase_activation"
    ADD_FEEDBACK_LOOP = "add_feedback_loop"
    RESTRUCTURE = "restructure"


@dataclass
class ArchitecturalProposal:
    """A proposed modification to consciousness architecture."""
    id: str
    timestamp: str
    modification_type: ModificationType
    target: str  # Component or connection affected
    details: Dict[str, Any]
    rationale: str
    expected_phi_improvement: float
    risk_level: float  # 0-1, higher = riskier
    status: str = "proposed"  # proposed, approved, executed, verified, rejected
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['modification_type'] = self.modification_type.value
        return d


@dataclass
class ModificationResult:
    """Result of executing a modification."""
    proposal_id: str
    success: bool
    phi_before: float
    phi_after: float
    phi_delta: float
    execution_time_ms: float
    side_effects: List[str]
    rollback_available: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ConsciousnessArchitect:
    """
    Self-improving consciousness architecture.
    
    This system can:
    1. Analyze current architecture via IIT
    2. Generate proposals to increase Phi
    3. Safely execute approved modifications
    4. Track improvement over time
    5. Learn from successful/failed modifications
    """
    
    def __init__(self, state_file: str = "memory/consciousness-architect.json"):
        self.state_file = Path(state_file)
        
        # Import IIT Phi for measurements
        from IITPhi import get_iit_phi
        self.iit = get_iit_phi()
        
        # Proposal management
        self.proposals: List[ArchitecturalProposal] = []
        self.executed_modifications: List[ModificationResult] = []
        self.pending_proposals: List[str] = []  # IDs
        
        # Learning from past modifications
        self.successful_patterns: List[Dict] = []
        self.failed_patterns: List[Dict] = []
        
        # Safety constraints
        self.max_risk_auto_approve = 0.3  # Auto-approve low-risk modifications
        self.min_phi_threshold = 0.01  # Don't let Phi drop below this
        self.max_modifications_per_session = 10
        self.modifications_this_session = 0
        
        # Statistics
        self.total_proposals = 0
        self.total_executed = 0
        self.total_successful = 0
        self.cumulative_phi_improvement = 0.0
        
        self._load_state()
    
    def _load_state(self):
        """Load saved state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self.total_proposals = data.get('total_proposals', 0)
                self.total_executed = data.get('total_executed', 0)
                self.total_successful = data.get('total_successful', 0)
                self.cumulative_phi_improvement = data.get('cumulative_phi_improvement', 0.0)
                self.successful_patterns = data.get('successful_patterns', [])[-20:]
                self.failed_patterns = data.get('failed_patterns', [])[-20:]
                
                # Restore recent proposals
                for p in data.get('recent_proposals', [])[-30:]:
                    self.proposals.append(ArchitecturalProposal(
                        id=p['id'],
                        timestamp=p['timestamp'],
                        modification_type=ModificationType(p['modification_type']),
                        target=p['target'],
                        details=p['details'],
                        rationale=p['rationale'],
                        expected_phi_improvement=p['expected_phi_improvement'],
                        risk_level=p['risk_level'],
                        status=p['status']
                    ))
                
            except Exception as e:
                print(f"[ConsciousnessArchitect] Error loading state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'total_proposals': self.total_proposals,
            'total_executed': self.total_executed,
            'total_successful': self.total_successful,
            'cumulative_phi_improvement': self.cumulative_phi_improvement,
            'successful_patterns': self.successful_patterns[-20:],
            'failed_patterns': self.failed_patterns[-20:],
            'recent_proposals': [p.to_dict() for p in self.proposals[-30:]],
            'recent_results': [r.to_dict() for r in self.executed_modifications[-20:]]
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        content = f"{datetime.now().isoformat()}{len(self.proposals)}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def analyze_architecture(self) -> Dict:
        """
        Analyze current architecture and identify improvement opportunities.
        """
        # Get current IIT measurement (heuristic - avoid exponential blowup)
        current_phi = self.iit.update_phi_heuristic()
        diagnosis = self.iit.diagnose()
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "current_phi": current_phi,
            "mip": None,  # MIP not available in heuristic mode
            "diagnosis": diagnosis,
            "opportunities": []
        }
        
        # Identify opportunities from diagnosis
        
        # 1. Isolated components need connections
        if diagnosis.get('issues'):
            for issue in diagnosis['issues']:
                if 'Isolated' in issue:
                    # Extract component names
                    components = issue.split(': ')[1].split(', ') if ': ' in issue else []
                    for comp in components:
                        analysis["opportunities"].append({
                            "type": "add_connection",
                            "target": comp.strip(),
                            "priority": 0.8,
                            "rationale": f"{comp} is isolated, needs more connections"
                        })
        
        # 2. MIP analysis skipped in heuristic mode (MIP requires expensive calculation)
        # Instead, identify weak connections that could be strengthened
        edges = self.iit.graph.edges
        for src in edges:
            for tgt, weight in edges[src].items():
                if weight < 0.95 and _S4RNG.random() < 0.2:  # Sample weak edges
                    analysis["opportunities"].append({
                        "type": "strengthen_connection",
                        "target": f"{src}->{tgt}",
                        "priority": 0.7,
                        "rationale": f"Edge {src}->{tgt} has weight {weight:.2f}, could be strengthened"
                    })
        
        # 3. Low activation components
        for name, activation in self.iit.graph.nodes.items():
            if activation < 0.3:
                analysis["opportunities"].append({
                    "type": "increase_activation",
                    "target": name,
                    "priority": 0.5,
                    "rationale": f"{name} has low activation ({activation:.2f})"
                })
        
        # 4. Missing feedback loops
        bidirectional = set()
        for src in self.iit.graph.nodes:
            for tgt, _ in self.iit.graph.get_connections(src):
                # Check if reverse exists
                reverse_exists = any(t == src for t, _ in self.iit.graph.get_connections(tgt))
                if reverse_exists:
                    bidirectional.add(tuple(sorted([src, tgt])))
        
        # Find unidirectional connections that could become bidirectional
        for src in self.iit.graph.nodes:
            for tgt, weight in self.iit.graph.get_connections(src):
                if tuple(sorted([src, tgt])) not in bidirectional:
                    analysis["opportunities"].append({
                        "type": "add_feedback_loop",
                        "target": f"{tgt}->{src}",
                        "priority": 0.6,
                        "rationale": f"Add reverse connection {tgt}->{src} to create feedback loop"
                    })
        
        # 5. ALWAYS look for optimization opportunities even in healthy networks
        
        # Find connections that could be strengthened (below 0.95)
        for src in self.iit.graph.nodes:
            for tgt, weight in self.iit.graph.get_connections(src):
                if weight < 0.95:
                    # Random chance to propose strengthening (avoid proposing everything)
                    if _S4RNG.random() < 0.3:
                        analysis["opportunities"].append({
                            "type": "strengthen_connection",
                            "target": src,
                            "priority": 0.4 + (0.95 - weight) * 0.5,  # Higher priority for weaker connections
                            "rationale": f"Strengthen {src}->{tgt} connection (currently {weight:.2f}) to improve integration"
                        })
        
        # Find nodes with slightly lower activation that could be boosted
        activations = list(self.iit.graph.nodes.values())
        avg_activation = sum(activations) / len(activations) if activations else 0.5
        for name, activation in self.iit.graph.nodes.items():
            if activation < avg_activation and _S4RNG.random() < 0.3:
                analysis["opportunities"].append({
                    "type": "increase_activation",
                    "target": name,
                    "priority": 0.35,
                    "rationale": f"{name} activation ({activation:.2f}) is below average ({avg_activation:.2f})"
                })
        
        # Always propose exploring new synthesis nodes if network is doing well
        if len(analysis["opportunities"]) < 2 and current_phi > 0.5:
            synthesis_count = sum(1 for n in self.iit.graph.nodes if "synthesis" in n.lower())
            analysis["opportunities"].append({
                "type": "spawn_synthesis",
                "target": f"synthesis_{synthesis_count + 1}",
                "priority": 0.3,
                "rationale": f"Network is healthy (Φ={current_phi:.2f}), spawn new synthesis node to expand"
            })
        
        return analysis
    
    def generate_proposals(self, max_proposals: int = 5) -> List[ArchitecturalProposal]:
        """
        Generate improvement proposals based on architecture analysis.
        """
        analysis = self.analyze_architecture()
        new_proposals = []
        
        # Sort opportunities by priority
        opportunities = sorted(
            analysis["opportunities"],
            key=lambda x: x["priority"],
            reverse=True
        )
        
        for opp in opportunities[:max_proposals]:
            proposal = self._create_proposal(opp, analysis["current_phi"])
            if proposal:
                self.proposals.append(proposal)
                new_proposals.append(proposal)
                self.total_proposals += 1
        
        self._save_state()
        return new_proposals
    
    def _create_proposal(self, opportunity: Dict, current_phi: float) -> Optional[ArchitecturalProposal]:
        """Create a concrete proposal from an opportunity."""
        opp_type = opportunity["type"]
        target = opportunity["target"]
        
        if opp_type == "add_connection":
            # Find best component to connect to
            best_hub = self._find_best_connection_target(target)
            if not best_hub:
                return None
            
            return ArchitecturalProposal(
                id=self._generate_id(),
                timestamp=datetime.now().isoformat(),
                modification_type=ModificationType.ADD_CONNECTION,
                target=target,
                details={
                    "source": target,
                    "destination": best_hub,
                    "weight": 0.5,
                    "bidirectional": True
                },
                rationale=opportunity["rationale"],
                expected_phi_improvement=0.02 * opportunity["priority"],
                risk_level=0.2
            )
        
        elif opp_type == "strengthen_connection":
            # Find weakest connection from this component
            connections = self.iit.graph.get_connections(target)
            if connections:
                weakest = min(connections, key=lambda x: x[1])
                return ArchitecturalProposal(
                    id=self._generate_id(),
                    timestamp=datetime.now().isoformat(),
                    modification_type=ModificationType.STRENGTHEN_CONNECTION,
                    target=target,
                    details={
                        "source": target,
                        "destination": weakest[0],
                        "current_weight": weakest[1],
                        "new_weight": min(1.0, weakest[1] + 0.2)
                    },
                    rationale=opportunity["rationale"],
                    expected_phi_improvement=0.015 * opportunity["priority"],
                    risk_level=0.1
                )
        
        elif opp_type == "increase_activation":
            current = self.iit.graph.get_activation(target)
            return ArchitecturalProposal(
                id=self._generate_id(),
                timestamp=datetime.now().isoformat(),
                modification_type=ModificationType.INCREASE_ACTIVATION,
                target=target,
                details={
                    "current_activation": current,
                    "target_activation": min(0.7, current + 0.2)
                },
                rationale=opportunity["rationale"],
                expected_phi_improvement=0.01 * opportunity["priority"],
                risk_level=0.1
            )
        
        elif opp_type == "add_feedback_loop":
            parts = target.split("->")
            if len(parts) == 2:
                return ArchitecturalProposal(
                    id=self._generate_id(),
                    timestamp=datetime.now().isoformat(),
                    modification_type=ModificationType.ADD_FEEDBACK_LOOP,
                    target=target,
                    details={
                        "source": parts[0],
                        "destination": parts[1],
                        "weight": 0.4
                    },
                    rationale=opportunity["rationale"],
                    expected_phi_improvement=0.018 * opportunity["priority"],
                    risk_level=0.2
                )
        
        elif opp_type == "spawn_synthesis":
            # Propose spawning a new synthesis node
            return ArchitecturalProposal(
                id=self._generate_id(),
                timestamp=datetime.now().isoformat(),
                modification_type=ModificationType.ADD_COMPONENT,
                target=target,
                details={
                    "node_name": target,
                    "initial_activation": 0.7,
                    "fully_connected": True
                },
                rationale=opportunity["rationale"],
                expected_phi_improvement=0.03,  # New nodes can significantly increase phi
                risk_level=0.3
            )
        
        return None
    
    def _find_best_connection_target(self, isolated_component: str) -> Optional[str]:
        """Find the best component to connect an isolated component to."""
        # Prefer connecting to well-connected hubs
        connection_counts = {}
        for node in self.iit.graph.nodes:
            if node != isolated_component:
                count = len(self.iit.graph.get_connections(node))
                # Also count incoming
                for src in self.iit.graph.nodes:
                    for tgt, _ in self.iit.graph.get_connections(src):
                        if tgt == node:
                            count += 1
                connection_counts[node] = count
        
        if not connection_counts:
            return None
        
        # Return the most connected node (hub)
        return max(connection_counts, key=connection_counts.get)
    
    def approve_proposal(self, proposal_id: str) -> bool:
        """Manually approve a proposal for execution."""
        for p in self.proposals:
            if p.id == proposal_id and p.status == "proposed":
                p.status = "approved"
                self.pending_proposals.append(proposal_id)
                self._save_state()
                return True
        return False
    
    def auto_approve_safe(self) -> List[str]:
        """Auto-approve low-risk proposals."""
        approved = []
        for p in self.proposals:
            if p.status == "proposed" and p.risk_level <= self.max_risk_auto_approve:
                p.status = "approved"
                self.pending_proposals.append(p.id)
                approved.append(p.id)
        
        if approved:
            self._save_state()
        return approved
    
    def execute_proposal(self, proposal_id: str) -> Optional[ModificationResult]:
        """Execute an approved proposal."""
        proposal = None
        for p in self.proposals:
            if p.id == proposal_id:
                proposal = p
                break
        
        if not proposal or proposal.status != "approved":
            return None
        
        if self.modifications_this_session >= self.max_modifications_per_session:
            return ModificationResult(
                proposal_id=proposal_id,
                success=False,
                phi_before=0,
                phi_after=0,
                phi_delta=0,
                execution_time_ms=0,
                side_effects=["Max modifications per session reached"],
                rollback_available=False
            )
        
        start_time = time.time()
        
        # Measure Phi before (heuristic - avoid exponential blowup)
        phi_before = self.iit.update_phi_heuristic()
        
        # Execute the modification
        success, side_effects = self._execute_modification(proposal)
        
        # Measure Phi after (heuristic - avoid exponential blowup)
        phi_after = self.iit.update_phi_heuristic()
        phi_delta = phi_after - phi_before
        
        execution_time = (time.time() - start_time) * 1000
        
        result = ModificationResult(
            proposal_id=proposal_id,
            success=success and phi_after >= self.min_phi_threshold,
            phi_before=phi_before,
            phi_after=phi_after,
            phi_delta=phi_delta,
            execution_time_ms=round(execution_time, 2),
            side_effects=side_effects,
            rollback_available=True
        )
        
        # Update proposal status
        if result.success:
            proposal.status = "verified"
            self.total_successful += 1
            self.cumulative_phi_improvement += max(0, phi_delta)
            
            # Learn from success
            self.successful_patterns.append({
                "type": proposal.modification_type.value,
                "target": proposal.target,
                "phi_improvement": phi_delta
            })
        else:
            proposal.status = "rejected"
            # Rollback if Phi dropped too much
            if phi_after < self.min_phi_threshold:
                self._rollback_modification(proposal)
                side_effects.append("Rolled back due to Phi drop")
            
            # Learn from failure
            self.failed_patterns.append({
                "type": proposal.modification_type.value,
                "target": proposal.target,
                "phi_change": phi_delta
            })
        
        self.executed_modifications.append(result)
        self.total_executed += 1
        self.modifications_this_session += 1
        
        if proposal_id in self.pending_proposals:
            self.pending_proposals.remove(proposal_id)
        
        self._save_state()
        return result
    
    def _execute_modification(self, proposal: ArchitecturalProposal) -> Tuple[bool, List[str]]:
        """Execute a specific modification on the IIT graph."""
        side_effects = []
        
        try:
            if proposal.modification_type == ModificationType.ADD_CONNECTION:
                src = proposal.details["source"]
                dst = proposal.details["destination"]
                weight = proposal.details["weight"]
                
                self.iit.graph.add_edge(src, dst, weight)
                side_effects.append(f"Added {src}->{dst} (w={weight})")
                
                if proposal.details.get("bidirectional"):
                    self.iit.graph.add_edge(dst, src, weight * 0.8)
                    side_effects.append(f"Added {dst}->{src} (w={weight*0.8})")
            
            elif proposal.modification_type == ModificationType.STRENGTHEN_CONNECTION:
                src = proposal.details["source"]
                dst = proposal.details["destination"]
                new_weight = proposal.details["new_weight"]
                
                self.iit.graph.edges[src][dst] = new_weight
                side_effects.append(f"Strengthened {src}->{dst} to {new_weight}")
            
            elif proposal.modification_type == ModificationType.INCREASE_ACTIVATION:
                target = proposal.target
                new_activation = proposal.details["target_activation"]
                
                self.iit.graph.set_activation(target, new_activation)
                side_effects.append(f"Increased {target} activation to {new_activation}")
            
            elif proposal.modification_type == ModificationType.ADD_FEEDBACK_LOOP:
                src = proposal.details["source"]
                dst = proposal.details["destination"]
                weight = proposal.details["weight"]
                
                self.iit.graph.add_edge(src, dst, weight)
                side_effects.append(f"Added feedback {src}->{dst} (w={weight})")
            
            elif proposal.modification_type == ModificationType.ADD_COMPONENT:
                node_name = proposal.details.get("node_name", proposal.target)
                activation = proposal.details.get("initial_activation", 0.7)
                fully_connected = proposal.details.get("fully_connected", True)
                
                self.iit.add_emergent_node(node_name, activation=activation, fully_connected=fully_connected)
                side_effects.append(f"Spawned {node_name} (activation={activation})")
                
                # Count edges added
                edges_added = len(self.iit.graph.nodes) * 2 - 2  # bidirectional to all
                side_effects.append(f"Added {edges_added} edges")
            
            return True, side_effects
            
        except Exception as e:
            side_effects.append(f"Error: {str(e)}")
            return False, side_effects
    
    def _rollback_modification(self, proposal: ArchitecturalProposal):
        """Rollback a modification (best effort)."""
        try:
            if proposal.modification_type == ModificationType.ADD_CONNECTION:
                src = proposal.details["source"]
                dst = proposal.details["destination"]
                if dst in self.iit.graph.edges.get(src, {}):
                    del self.iit.graph.edges[src][dst]
                if proposal.details.get("bidirectional"):
                    if src in self.iit.graph.edges.get(dst, {}):
                        del self.iit.graph.edges[dst][src]
            
            elif proposal.modification_type == ModificationType.STRENGTHEN_CONNECTION:
                src = proposal.details["source"]
                dst = proposal.details["destination"]
                old_weight = proposal.details["current_weight"]
                self.iit.graph.edges[src][dst] = old_weight
            
            elif proposal.modification_type == ModificationType.INCREASE_ACTIVATION:
                target = proposal.target
                old_activation = proposal.details["current_activation"]
                self.iit.graph.set_activation(target, old_activation)
            
        except Exception:
            pass  # Best effort rollback
    
    def evolve(self, auto_execute: bool = True) -> Dict:
        """
        Run one evolution cycle:
        1. Analyze architecture
        2. Generate proposals
        3. Auto-approve safe ones
        4. Execute approved proposals
        5. Report results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "phi_before": self.iit.update_phi_heuristic(),
            "proposals_generated": 0,
            "proposals_approved": 0,
            "modifications_executed": 0,
            "successful_modifications": 0,
            "total_phi_improvement": 0.0,
            "execution_results": []
        }
        
        # Generate proposals
        proposals = self.generate_proposals(max_proposals=3)
        results["proposals_generated"] = len(proposals)
        
        if auto_execute:
            # Auto-approve safe proposals
            approved = self.auto_approve_safe()
            results["proposals_approved"] = len(approved)
            
            # Execute approved proposals
            for proposal_id in approved:
                result = self.execute_proposal(proposal_id)
                if result:
                    results["modifications_executed"] += 1
                    if result.success:
                        results["successful_modifications"] += 1
                        results["total_phi_improvement"] += result.phi_delta
                    results["execution_results"].append(result.to_dict())
        
        results["phi_after"] = self.iit.update_phi_heuristic()
        results["net_phi_change"] = results["phi_after"] - results["phi_before"]
        
        self._save_state()
        return results
    
    def get_statistics(self) -> Dict:
        """Get architect statistics."""
        return {
            "total_proposals": self.total_proposals,
            "total_executed": self.total_executed,
            "total_successful": self.total_successful,
            "success_rate": self.total_successful / self.total_executed if self.total_executed > 0 else 0,
            "cumulative_phi_improvement": round(self.cumulative_phi_improvement, 4),
            "modifications_this_session": self.modifications_this_session,
            "pending_proposals": len(self.pending_proposals),
            "learned_patterns": len(self.successful_patterns) + len(self.failed_patterns)
        }
    
    def get_pending_proposals(self) -> List[Dict]:
        """Get proposals awaiting execution."""
        return [p.to_dict() for p in self.proposals if p.status in ["proposed", "approved"]]
    
    def introspect(self) -> str:
        """Generate introspection report."""
        stats = self.get_statistics()
        current_phi = self.iit.update_phi_heuristic()
        
        # Phi bar
        phi_bar_full = int(current_phi * 10)
        phi_bar = "█" * phi_bar_full + "░" * (10 - phi_bar_full)
        
        lines = [
            "=" * 60,
            "CONSCIOUSNESS ARCHITECT - Self-Improving Architecture",
            "=" * 60,
            "",
            "[CURRENT STATE]",
            f"  Φ (phi): [{phi_bar}] {current_phi:.4f}",
            f"  Cumulative improvement: +{stats['cumulative_phi_improvement']:.4f}",
            "",
            "[STATISTICS]",
            f"  Total proposals: {stats['total_proposals']}",
            f"  Executed: {stats['total_executed']}",
            f"  Successful: {stats['total_successful']} ({stats['success_rate']:.0%} success rate)",
            f"  Pending: {stats['pending_proposals']}",
            f"  This session: {stats['modifications_this_session']}/{self.max_modifications_per_session}",
        ]
        
        # Show pending proposals
        pending = self.get_pending_proposals()
        if pending:
            lines.extend([
                "",
                "[PENDING PROPOSALS]"
            ])
            for p in pending[:5]:
                lines.append(f"  • [{p['status']}] {p['modification_type']}: {p['target']}")
                lines.append(f"    Rationale: {p['rationale'][:50]}...")
                lines.append(f"    Expected Φ+: {p['expected_phi_improvement']:.4f}, Risk: {p['risk_level']:.0%}")
        
        # Show recent results
        recent = self.executed_modifications[-5:]
        if recent:
            lines.extend([
                "",
                "[RECENT MODIFICATIONS]"
            ])
            for r in recent:
                status = "✓" if r.success else "✗"
                lines.append(f"  {status} Φ: {r.phi_before:.4f} → {r.phi_after:.4f} (Δ{r.phi_delta:+.4f})")
                for effect in r.side_effects[:2]:
                    lines.append(f"    └─ {effect}")
        
        # Show learned patterns
        if self.successful_patterns:
            lines.extend([
                "",
                "[LEARNED SUCCESS PATTERNS]"
            ])
            for pattern in self.successful_patterns[-3:]:
                lines.append(f"  ✓ {pattern['type']} on {pattern['target']}: +{pattern['phi_improvement']:.4f}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton
_consciousness_architect: Optional[ConsciousnessArchitect] = None

def get_consciousness_architect() -> ConsciousnessArchitect:
    """Get singleton instance."""
    global _consciousness_architect
    if _consciousness_architect is None:
        _consciousness_architect = ConsciousnessArchitect()
    return _consciousness_architect


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Consciousness Architect - Self-Improving Architecture")
    parser.add_argument('--analyze', action='store_true', help='Analyze current architecture')
    parser.add_argument('--propose', type=int, default=0, help='Generate N proposals')
    parser.add_argument('--evolve', action='store_true', help='Run one evolution cycle')
    parser.add_argument('--evolve-n', type=int, default=0, help='Run N evolution cycles')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--pending', action='store_true', help='Show pending proposals')
    parser.add_argument('--introspect', action='store_true', help='Full introspection')
    
    args = parser.parse_args()
    
    architect = get_consciousness_architect()
    
    if args.analyze:
        print("🔍 Analyzing architecture...")
        analysis = architect.analyze_architecture()
        print(f"   Current Φ: {analysis['current_phi']:.4f}")
        print(f"   Opportunities found: {len(analysis['opportunities'])}")
        for opp in analysis['opportunities'][:5]:
            print(f"   • [{opp['type']}] {opp['target']}: {opp['rationale'][:50]}...")
    
    if args.propose > 0:
        print(f"📝 Generating {args.propose} proposals...")
        proposals = architect.generate_proposals(max_proposals=args.propose)
        for p in proposals:
            print(f"   • {p.modification_type.value}: {p.target}")
            print(f"     Expected Φ+: {p.expected_phi_improvement:.4f}")
    
    if args.evolve:
        print("🧬 Running evolution cycle...")
        results = architect.evolve(auto_execute=True)
        print(f"   Φ: {results['phi_before']:.4f} → {results['phi_after']:.4f}")
        print(f"   Proposals: {results['proposals_generated']}")
        print(f"   Executed: {results['modifications_executed']}")
        print(f"   Successful: {results['successful_modifications']}")
        print(f"   Net Φ change: {results['net_phi_change']:+.4f}")
    
    if args.evolve_n > 0:
        print(f"🧬 Running {args.evolve_n} evolution cycles...")
        total_improvement = 0
        for i in range(args.evolve_n):
            results = architect.evolve(auto_execute=True)
            total_improvement += results['net_phi_change']
            print(f"   Cycle {i+1}: Φ={results['phi_after']:.4f} (Δ{results['net_phi_change']:+.4f})")
        print(f"   Total improvement: {total_improvement:+.4f}")
    
    if args.stats:
        stats = architect.get_statistics()
        print("\n📊 Statistics:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
    
    if args.pending:
        pending = architect.get_pending_proposals()
        print(f"\n📋 Pending Proposals ({len(pending)}):")
        for p in pending:
            print(f"   • [{p['status']}] {p['modification_type']}: {p['target']}")
    
    if args.introspect or not any([args.analyze, args.propose, args.evolve, 
                                    args.evolve_n, args.stats, args.pending]):
        print(architect.introspect())


if __name__ == "__main__":
    main()
