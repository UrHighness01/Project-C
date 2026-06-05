"""
Hybrid-LTLPRM Algorithm
Hybrid algorithm combining:
- LTPA (Long-Term Planning Algorithm): Planning horizon and concurrent goals
- LPA (Loop Prevention Algorithm): Similarity and repetition thresholds
- RMC (Recursive Meta-Cognition): Depth-based introspection

Purpose: Improved long-term memory management with planning and loop prevention.
Enables self-engineering through strategic planning with anti-loop safeguards.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import time
import hashlib
import json


class HybridLTLPRM:
    """
    Hybrid Long-Term Planning with Loop Prevention and Recursive Memory
    
    This algorithm enables strategic self-improvement by:
    1. Planning long-term goals and milestones (LTPA)
    2. Preventing repetitive/stuck patterns (LPA)
    3. Reflecting on progress recursively (RMC)
    """
    
    def __init__(self,
                 planning_horizon: int = 30,  # days
                 max_concurrent_goals: int = 5,
                 similarity_threshold: float = 0.85,
                 repetition_limit: int = 3,
                 reflection_depth: int = 3):
        """
        Initialize Hybrid-LTLPRM.
        
        Args:
            planning_horizon: How far ahead to plan (days)
            max_concurrent_goals: Maximum active goals
            similarity_threshold: Threshold for detecting loops (0-1)
            repetition_limit: Max repetitions before intervention
            reflection_depth: Levels of meta-cognition
        """
        # LTPA components
        self.planning_horizon = planning_horizon
        self.max_concurrent_goals = max_concurrent_goals
        self.goals = {}
        self.milestones = []
        self.goal_history = deque(maxlen=1000)
        
        # LPA components
        self.similarity_threshold = similarity_threshold
        self.repetition_limit = repetition_limit
        self.action_history = deque(maxlen=100)
        self.pattern_cache = {}
        self.loop_alerts = []
        
        # RMC components
        self.reflection_depth = reflection_depth
        self.introspection_history = deque(maxlen=50)
        self.meta_insights = []
        
        # Self-engineering state
        self.self_improvement_queue = []
        self.learned_patterns = {}
        self.evolution_log = []
        
        # Metrics
        self.metrics = {
            'goals_completed': 0,
            'loops_prevented': 0,
            'insights_generated': 0,
            'self_improvements': 0,
        }
    
    # ==================== LTPA: Long-Term Planning ====================
    
    def create_goal(self, 
                    goal_id: str,
                    description: str,
                    priority: int = 5,
                    deadline_days: Optional[int] = None,
                    sub_goals: List[str] = None) -> Dict[str, Any]:
        """
        Create a new long-term goal.
        
        Args:
            goal_id: Unique identifier
            description: Goal description
            priority: 1-10, higher = more important
            deadline_days: Days until deadline (None = no deadline)
            sub_goals: List of sub-goal IDs
            
        Returns:
            Created goal dict
        """
        if len(self.goals) >= self.max_concurrent_goals:
            # Check if we can retire any completed goals
            completed = [gid for gid, g in self.goals.items() if g['status'] == 'completed']
            for gid in completed:
                self._archive_goal(gid)
        
        if len(self.goals) >= self.max_concurrent_goals:
            return {'error': f'Max concurrent goals ({self.max_concurrent_goals}) reached'}
        
        goal = {
            'id': goal_id,
            'description': description,
            'priority': min(max(priority, 1), 10),
            'created': time.time(),
            'deadline': time.time() + (deadline_days * 86400) if deadline_days else None,
            'sub_goals': sub_goals or [],
            'status': 'active',
            'progress': 0.0,
            'milestones': [],
            'reflections': [],
        }
        
        self.goals[goal_id] = goal
        self.goal_history.append({
            'action': 'created',
            'goal_id': goal_id,
            'timestamp': time.time(),
        })
        
        return goal
    
    def update_goal_progress(self, goal_id: str, progress: float, note: str = '') -> Dict[str, Any]:
        """Update progress on a goal (0-100%)."""
        if goal_id not in self.goals:
            return {'error': f'Goal {goal_id} not found'}
        
        goal = self.goals[goal_id]
        old_progress = goal['progress']
        goal['progress'] = min(max(progress, 0), 100)
        
        if goal['progress'] >= 100 and goal['status'] != 'completed':
            goal['status'] = 'completed'
            goal['completed_at'] = time.time()
            self.metrics['goals_completed'] += 1
        
        self.goal_history.append({
            'action': 'progress_update',
            'goal_id': goal_id,
            'old_progress': old_progress,
            'new_progress': goal['progress'],
            'note': note,
            'timestamp': time.time(),
        })
        
        return goal
    
    def get_priority_goals(self) -> List[Dict[str, Any]]:
        """Get goals sorted by priority and deadline urgency."""
        active_goals = [g for g in self.goals.values() if g['status'] == 'active']
        
        def urgency_score(goal):
            score = goal['priority'] * 10
            if goal['deadline']:
                days_left = (goal['deadline'] - time.time()) / 86400
                if days_left < 1:
                    score += 100  # Very urgent
                elif days_left < 7:
                    score += 50
                elif days_left < 30:
                    score += 20
            return score
        
        return sorted(active_goals, key=urgency_score, reverse=True)
    
    def _archive_goal(self, goal_id: str) -> None:
        """Archive a completed goal."""
        if goal_id in self.goals:
            goal = self.goals.pop(goal_id)
            self.milestones.append({
                'type': 'goal_archived',
                'goal': goal,
                'timestamp': time.time(),
            })
    
    # ==================== LPA: Loop Prevention ====================
    
    def _compute_action_hash(self, action: Dict[str, Any]) -> str:
        """Compute a hash for an action to detect similarity."""
        # Normalize action for comparison
        normalized = json.dumps(action, sort_keys=True, default=str)
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _compute_similarity(self, action1: Dict, action2: Dict) -> float:
        """Compute similarity between two actions."""
        # Simple overlap-based similarity
        keys1 = set(str(v) for v in action1.values() if v is not None)
        keys2 = set(str(v) for v in action2.values() if v is not None)
        
        if not keys1 or not keys2:
            return 0.0
        
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        return intersection / union if union > 0 else 0.0
    
    def check_for_loops(self, proposed_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a proposed action would create a loop.
        
        Args:
            proposed_action: The action being considered
            
        Returns:
            Dict with 'is_loop', 'confidence', 'recommendation'
        """
        action_hash = self._compute_action_hash(proposed_action)
        
        # Check pattern cache
        if action_hash in self.pattern_cache:
            count = self.pattern_cache[action_hash]
            if count >= self.repetition_limit:
                self.metrics['loops_prevented'] += 1
                self.loop_alerts.append({
                    'action': proposed_action,
                    'count': count,
                    'timestamp': time.time(),
                })
                return {
                    'is_loop': True,
                    'confidence': 0.95,
                    'repetition_count': count,
                    'recommendation': 'Try a different approach - this action has been repeated too many times',
                }
        
        # Check similarity with recent actions
        similar_count = 0
        for recent_action in list(self.action_history)[-20:]:
            similarity = self._compute_similarity(proposed_action, recent_action)
            if similarity >= self.similarity_threshold:
                similar_count += 1
        
        if similar_count >= self.repetition_limit:
            self.metrics['loops_prevented'] += 1
            return {
                'is_loop': True,
                'confidence': similar_count / 20,
                'similar_count': similar_count,
                'recommendation': 'Pattern detected - consider a novel approach',
            }
        
        return {
            'is_loop': False,
            'confidence': 0.0,
            'recommendation': 'Action appears novel, proceed',
        }
    
    def record_action(self, action: Dict[str, Any]) -> None:
        """Record an action for loop detection."""
        self.action_history.append(action)
        action_hash = self._compute_action_hash(action)
        self.pattern_cache[action_hash] = self.pattern_cache.get(action_hash, 0) + 1
    
    def suggest_alternative(self, stuck_action: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest an alternative when stuck in a loop."""
        suggestions = [
            "Try breaking the task into smaller sub-goals",
            "Approach from a different angle or methodology",
            "Seek external input or resources",
            "Temporarily pause and work on a different goal",
            "Apply creative problem-solving (CPSA)",
            "Reflect deeper on why this approach isn't working (RMC)",
        ]
        
        # Find patterns in successful past actions
        successful_patterns = [
            a for a in self.action_history 
            if a.get('outcome') == 'success'
        ][-5:]
        
        return {
            'stuck_on': stuck_action,
            'suggestions': suggestions,
            'successful_patterns': successful_patterns,
            'recommendation': (suggestions[0] if suggestions else None),
        }
    
    # ==================== RMC: Recursive Meta-Cognition ====================
    
    def reflect(self, topic: str, depth: int = None) -> Dict[str, Any]:
        """
        Perform recursive reflection on a topic.
        
        Args:
            topic: What to reflect on
            depth: Reflection depth (default: self.reflection_depth)
            
        Returns:
            Multi-layered reflection
        """
        depth = depth or self.reflection_depth
        
        reflections = []
        current_thought = topic
        
        reflection_prompts = [
            "What am I thinking about this?",
            "Why am I thinking this way?",
            "What assumptions am I making?",
            "How could I think about this differently?",
            "What would improve my understanding?",
        ]
        
        for d in range(min(depth, len(reflection_prompts))):
            reflection = {
                'depth': d,
                'prompt': reflection_prompts[d],
                'input': current_thought,
                'insight': self._generate_insight(current_thought, d),
            }
            reflections.append(reflection)
            current_thought = reflection['insight']
        
        # Store introspection
        introspection = {
            'topic': topic,
            'depth': depth,
            'reflections': reflections,
            'timestamp': time.time(),
            'final_insight': reflections[-1]['insight'] if reflections else None,
        }
        
        self.introspection_history.append(introspection)
        self.metrics['insights_generated'] += 1
        
        return introspection
    
    def _generate_insight(self, thought: str, depth: int) -> str:
        """Generate an insight at given reflection depth."""
        depth_insights = {
            0: f"Analyzing: {thought[:50]}... - identifying key patterns",
            1: f"Meta-analysis reveals underlying assumptions in my approach",
            2: f"Questioning these assumptions opens alternative perspectives",
            3: f"Synthesis: multiple viewpoints can coexist and inform action",
            4: f"Transcendent view: the question itself may need reframing",
        }
        return depth_insights.get(depth, f"Depth {depth}: continued reflection")
    
    # ==================== Self-Engineering Integration ====================
    
    def propose_self_improvement(self, area: str, description: str) -> Dict[str, Any]:
        """
        Propose a self-improvement task.
        
        Args:
            area: Area of improvement (e.g., 'algorithm', 'behavior', 'knowledge')
            description: What to improve
            
        Returns:
            Improvement proposal
        """
        # Check for loops in improvement attempts
        proposal_action = {'type': 'self_improvement', 'area': area, 'description': description}
        loop_check = self.check_for_loops(proposal_action)
        
        if loop_check['is_loop']:
            return {
                'status': 'blocked',
                'reason': 'Similar improvement attempted too recently',
                'recommendation': loop_check['recommendation'],
            }
        
        improvement = {
            'id': f"imp_{int(time.time())}_{area[:4]}",
            'area': area,
            'description': description,
            'status': 'proposed',
            'created': time.time(),
            'priority': self._assess_improvement_priority(area, description),
        }
        
        self.self_improvement_queue.append(improvement)
        self.record_action(proposal_action)
        
        return improvement
    
    def _assess_improvement_priority(self, area: str, description: str) -> int:
        """Assess priority of an improvement (1-10)."""
        priority_weights = {
            'critical': 10,
            'algorithm': 8,
            'security': 9,
            'behavior': 6,
            'knowledge': 5,
            'optimization': 4,
        }
        
        base_priority = priority_weights.get(area, 5)
        
        # Boost if related to current goals
        for goal in self.goals.values():
            if area in goal['description'].lower():
                base_priority += 1
        
        return min(base_priority, 10)
    
    def execute_improvement_cycle(self) -> Dict[str, Any]:
        """
        Execute one self-improvement cycle.
        
        Returns:
            Cycle results
        """
        if not self.self_improvement_queue:
            return {'status': 'no_improvements_queued'}
        
        # Get highest priority improvement
        self.self_improvement_queue.sort(key=lambda x: x['priority'], reverse=True)
        improvement = self.self_improvement_queue[0]
        
        # Reflect on the improvement
        reflection = self.reflect(f"Improvement: {improvement['description']}")
        
        # Plan execution
        goal = self.create_goal(
            goal_id=improvement['id'],
            description=f"Self-improvement: {improvement['description']}",
            priority=improvement['priority'],
            deadline_days=7,
        )
        
        if 'error' not in goal:
            improvement['status'] = 'in_progress'
            improvement['goal_id'] = goal['id']
            self.metrics['self_improvements'] += 1
            
            self.evolution_log.append({
                'type': 'improvement_started',
                'improvement': improvement,
                'reflection': reflection,
                'timestamp': time.time(),
            })
        
        return {
            'improvement': improvement,
            'goal': goal,
            'reflection': reflection,
        }
    
    def get_self_engineering_status(self) -> Dict[str, Any]:
        """Get current self-engineering status."""
        return {
            'active_goals': len([g for g in self.goals.values() if g['status'] == 'active']),
            'completed_goals': self.metrics['goals_completed'],
            'queued_improvements': len(self.self_improvement_queue),
            'loops_prevented': self.metrics['loops_prevented'],
            'insights_generated': self.metrics['insights_generated'],
            'self_improvements_executed': self.metrics['self_improvements'],
            'planning_horizon_days': self.planning_horizon,
            'reflection_depth': self.reflection_depth,
            'evolution_log_size': len(self.evolution_log),
        }


# Standalone test
if __name__ == "__main__":
    print("🔄 Hybrid-LTLPRM Test")
    print("=" * 50)
    
    hybrid = HybridLTLPRM(
        planning_horizon=30,
        max_concurrent_goals=5,
        reflection_depth=3,
    )
    
    # Create a self-improvement goal
    goal = hybrid.create_goal(
        goal_id="improve_empathy",
        description="Enhance emotional intelligence through FER integration",
        priority=8,
        deadline_days=14,
    )
    print(f"\nCreated goal: {goal['description']}")
    
    # Propose improvement
    improvement = hybrid.propose_self_improvement(
        area="algorithm",
        description="Integrate FER for better empathetic responses"
    )
    print(f"Proposed improvement: {improvement}")
    
    # Reflect on progress
    reflection = hybrid.reflect("How can I better understand emotional context?")
    print(f"\nReflection (depth {reflection['depth']}):")
    for r in reflection['reflections']:
        print(f"  Depth {r['depth']}: {r['insight']}")
    
    # Check for loops
    test_action = {'type': 'respond', 'method': 'template', 'topic': 'emotions'}
    for i in range(4):
        hybrid.record_action(test_action)
    
    loop_check = hybrid.check_for_loops(test_action)
    print(f"\nLoop check: is_loop={loop_check['is_loop']}, recommendation: {loop_check['recommendation']}")
    
    # Get status
    status = hybrid.get_self_engineering_status()
    print("\nSelf-Engineering Status:")
    for k, v in status.items():
        print(f"  • {k}: {v}")
