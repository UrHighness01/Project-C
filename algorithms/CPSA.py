"""
Creative Problem Solving Algorithm (CPSA)
Implements advanced creative problem solving for AGI-level innovation

This algorithm enables Coral to:
- Generate novel solutions to complex problems
- Combine disparate concepts creatively
- Think outside conventional boundaries
- Develop innovative approaches to challenges
"""

import numpy as np
import random
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, deque
import itertools
import copy
import re as _re

_CPSA_RNG = random.Random(0xC4EA)
_SPECULATIVE = ("magic", "imagine", "if ", "supernatural", "time travel", "dream",
                "fantasy", "impossible", "what if", "radical", "reinvent")
_CONCRETE = ("apply", "use", "implement", "address", "combine", "step", "build",
             "measure", "test", "specific", "constraint", "tool", "process")


def _novelty(text: str, reference: str = "") -> float:
    """Real novelty: lexical diversity of the proposal plus speculative-language density,
    minus overlap with the problem statement. Deterministic, in [0, 1]."""
    toks = _re.findall(r"[a-z]+", text.lower())
    if not toks:
        return 0.0
    diversity = len(set(toks)) / len(toks)
    spec = sum(c in text.lower() for c in _SPECULATIVE) / 5.0
    ref = set(_re.findall(r"[a-z]+", reference.lower()))
    overlap = sum(t in ref for t in toks) / len(toks) if ref else 0.0
    return float(max(0.0, min(1.0, 0.5 * diversity + 0.4 * spec + 0.1 * (1 - overlap))))


def _feasibility(text: str) -> float:
    """Real feasibility: density of concrete/actionable language minus speculative
    language, with a brevity bonus. Deterministic, in [0, 1]."""
    low = text.lower()
    concrete = sum(c in low for c in _CONCRETE) / 5.0
    spec = sum(c in low for c in _SPECULATIVE) / 5.0
    brevity = 1.0 / (1.0 + len(text) / 120.0)
    return float(max(0.0, min(1.0, 0.6 * concrete - 0.3 * spec + 0.4 * brevity)))


class CreativeProblemSolvingAlgorithm:
    """
    Advanced creative problem solving system for generating innovative solutions
    """

    def __init__(self, creativity_level: float = 0.8, concept_memory_size: int = 1000):
        # Core creativity parameters
        self.creativity_level = creativity_level
        self.novelty_weight = 0.7
        self.feasibility_weight = 0.3

        # Concept and idea memory
        self.concept_memory = deque(maxlen=concept_memory_size)
        self.idea_patterns = defaultdict(list)
        self.solution_templates = []
        self.creative_associations = defaultdict(set)

        # Problem-solving state
        self.active_problems = {}
        self.solution_history = deque(maxlen=200)
        self.creativity_metrics = {
            'novelty_score': 0.0,
            'diversity_score': 0.0,
            'feasibility_score': 0.0,
            'innovation_rate': 0.0
        }

        # Creative thinking modes
        self.thinking_modes = {
            'divergent': self._divergent_thinking,
            'convergent': self._convergent_thinking,
            'lateral': self._lateral_thinking,
            'analogical': self._analogical_thinking,
            'combinatorial': self._combinatorial_thinking
        }

        # Initialize creative frameworks
        self._initialize_creative_frameworks()

    def _initialize_creative_frameworks(self):
        """Initialize creative problem-solving frameworks and templates"""

        # SCAMPER technique variations
        self.solution_templates.extend([
            "Substitute: Replace component X with Y",
            "Combine: Merge elements A and B",
            "Adapt: Modify for new context",
            "Modify/Magnify/Minify: Change scale or attributes",
            "Put to other uses: Repurpose for different application",
            "Eliminate: Remove unnecessary elements",
            "Reverse/Rearrange: Change order or orientation"
        ])

        # Creative association categories
        self.creative_associations.update({
            'technology': {'AI', 'blockchain', 'quantum', 'neural', 'autonomous'},
            'nature': {'evolution', 'ecosystem', 'adaptation', 'symbiosis', 'emergence'},
            'society': {'collaboration', 'network', 'culture', 'learning', 'communication'},
            'science': {'complexity', 'chaos', 'fractal', 'emergence', 'self-organization'},
            'art': {'creativity', 'expression', 'beauty', 'harmony', 'innovation'}
        })

    def solve_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a problem using creative problem-solving techniques

        Args:
            problem: Dict containing problem description and constraints

        Returns:
            Dict with generated solutions and analysis
        """
        problem_id = f"problem_{int(time.time() * 1000)}"
        self.active_problems[problem_id] = problem

        # Reseed exploration from the problem so the same problem explores reproducibly
        _CPSA_RNG.seed(hash(str(problem.get('description', ''))) & 0xFFFFFFFF)

        # Analyze problem
        problem_analysis = self._analyze_problem(problem)

        # Generate solutions using multiple creative approaches
        solutions = []
        thinking_modes_used = []

        # Use different thinking modes based on problem type
        for mode_name, mode_function in self.thinking_modes.items():
            if self._should_use_mode(mode_name, problem_analysis):
                mode_solutions = mode_function(problem, problem_analysis)
                solutions.extend(mode_solutions)
                thinking_modes_used.append(mode_name)

        # Evaluate and rank solutions
        evaluated_solutions = self._evaluate_solutions(solutions, problem)

        # Generate meta-solutions (combinations of solutions)
        if len(evaluated_solutions) >= 2:
            meta_solutions = self._generate_meta_solutions(evaluated_solutions[:5], problem)
            evaluated_solutions.extend(meta_solutions)

        # Update creativity metrics
        self._update_creativity_metrics(evaluated_solutions)

        # Store solution in history
        solution_record = {
            'problem_id': problem_id,
            'problem': problem,
            'solutions': evaluated_solutions,
            'thinking_modes': thinking_modes_used,
            'creativity_metrics': self.creativity_metrics.copy(),
            'timestamp': time.time()
        }
        self.solution_history.append(solution_record)

        return {
            'problem_id': problem_id,
            'analysis': problem_analysis,
            'solutions': evaluated_solutions[:10],  # Top 10 solutions
            'thinking_modes_used': thinking_modes_used,
            'creativity_assessment': self.creativity_metrics.copy(),
            'total_solutions_generated': len(solutions)
        }

    def _analyze_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the problem to understand its nature and requirements"""
        analysis = {
            'complexity': 'medium',
            'domain': 'general',
            'constraints': [],
            'key_elements': [],
            'solution_space': 'open',
            'creativity_required': 'moderate'
        }

        description = problem.get('description', '').lower()
        constraints = problem.get('constraints', [])

        # Analyze complexity
        word_count = len(description.split())
        if word_count > 50 or 'complex' in description:
            analysis['complexity'] = 'high'
        elif word_count < 20:
            analysis['complexity'] = 'low'

        # Identify domain
        domain_keywords = {
            'technical': ['code', 'programming', 'algorithm', 'system', 'software'],
            'social': ['people', 'relationship', 'communication', 'society', 'community'],
            'scientific': ['research', 'experiment', 'theory', 'hypothesis', 'data'],
            'creative': ['design', 'art', 'music', 'story', 'innovation'],
            'business': ['profit', 'market', 'customer', 'strategy', 'product']
        }

        for domain, keywords in domain_keywords.items():
            if any(keyword in description for keyword in keywords):
                analysis['domain'] = domain
                break

        # Extract constraints
        analysis['constraints'] = constraints

        # Determine solution space
        if len(constraints) > 3 or 'must' in description or 'required' in description:
            analysis['solution_space'] = 'constrained'
        else:
            analysis['solution_space'] = 'open'

        # Assess creativity requirements
        if analysis['complexity'] == 'high' or analysis['solution_space'] == 'open':
            analysis['creativity_required'] = 'high'
        elif analysis['domain'] in ['creative', 'scientific']:
            analysis['creativity_required'] = 'high'

        return analysis

    def _should_use_mode(self, mode_name: str, problem_analysis: Dict[str, Any]) -> bool:
        """Determine if a thinking mode should be used for this problem"""
        complexity = problem_analysis.get('complexity', 'medium')
        domain = problem_analysis.get('domain', 'general')
        creativity_needed = problem_analysis.get('creativity_required', 'moderate')

        # Mode selection logic
        if mode_name == 'divergent' and creativity_needed == 'high':
            return True
        elif mode_name == 'convergent' and complexity == 'high':
            return True
        elif mode_name == 'lateral' and problem_analysis.get('solution_space') == 'constrained':
            return True
        elif mode_name == 'analogical' and domain in ['scientific', 'technical']:
            return True
        elif mode_name == 'combinatorial' and creativity_needed == 'high':
            return True

        # Default: use 70% of modes randomly
        return _CPSA_RNG.random() < 0.7

    def _divergent_thinking(self, problem: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate many diverse solutions"""
        solutions = []
        description = problem.get('description', '')

        # Generate variations using different perspectives
        perspectives = [
            "from a child's perspective",
            "from an alien's viewpoint",
            "using nature as inspiration",
            "with unlimited resources",
            "in a post-apocalyptic world",
            "as if time travel existed",
            "through the eyes of an AI",
            "using magic or supernatural elements"
        ]

        for perspective in _CPSA_RNG.sample(perspectives, min(5, len(perspectives))):
            solution = {
                'approach': f'Divergent: {perspective}',
                'description': f"Approach the problem {perspective}: {description}",
                'creativity_type': 'divergent',
                'novelty_factor': 0.750,
                'feasibility': 0.450
            }
            solutions.append(solution)

        return solutions

    def _convergent_thinking(self, problem: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate focused, practical solutions"""
        solutions = []
        constraints = analysis.get('constraints', [])

        # Use SCAMPER technique
        for template in _CPSA_RNG.sample(self.solution_templates, min(3, len(self.solution_templates))):
            solution = {
                'approach': f'Convergent: {template.split(":")[0]}',
                'description': f"Apply '{template}' to solve: {problem.get('description', '')}",
                'creativity_type': 'convergent',
                'novelty_factor': 0.500,
                'feasibility': 0.825
            }
            solutions.append(solution)

        # Add constraint-based solutions
        if constraints:
            for constraint in constraints[:2]:  # Use first 2 constraints
                solution = {
                    'approach': f'Constraint-focused: Address {constraint}',
                    'description': f"Develop solution that specifically addresses: {constraint}",
                    'creativity_type': 'convergent',
                    'novelty_factor': 0.350,
                    'feasibility': 0.890
                }
                solutions.append(solution)

        return solutions

    def _lateral_thinking(self, problem: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate unexpected, indirect solutions"""
        solutions = []
        description = problem.get('description', '')

        # Lateral thinking techniques
        lateral_approaches = [
            "solve the opposite problem",
            "remove a key assumption",
            "change the problem statement entirely",
            "approach from the end backwards",
            "make the problem bigger or smaller",
            "change the rules of the game",
            "use humor or absurdity",
            "combine with an unrelated field"
        ]

        for approach in _CPSA_RNG.sample(lateral_approaches, min(4, len(lateral_approaches))):
            solution = {
                'approach': f'Lateral: {approach}',
                'description': f"Try {approach} for: {description}",
                'creativity_type': 'lateral',
                'novelty_factor': 0.825,
                'feasibility': 0.350
            }
            solutions.append(solution)

        return solutions

    def _analogical_thinking(self, problem: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions by drawing analogies"""
        solutions = []
        domain = analysis.get('domain', 'general')

        # Find relevant analogies from memory
        analogies = self._find_relevant_analogies(domain)

        for analogy in analogies[:3]:
            solution = {
                'approach': f'Analogical: Learn from {analogy["source"]}',
                'description': f"Apply the {analogy['lesson']} principle to: {problem.get('description', '')}",
                'creativity_type': 'analogical',
                'novelty_factor': 0.650,
                'feasibility': 0.750,
                'analogy_source': analogy
            }
            solutions.append(solution)

        return solutions

    def _combinatorial_thinking(self, problem: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions by combining different concepts"""
        solutions = []
        description = problem.get('description', '')

        # Get relevant concept categories
        relevant_categories = self._get_relevant_categories(analysis)

        # Generate combinations
        for combo in itertools.combinations(relevant_categories, 2):
            cat1, cat2 = combo
            concepts1 = list(self.creative_associations.get(cat1, set()))[:3]
            concepts2 = list(self.creative_associations.get(cat2, set()))[:3]

            if concepts1 and concepts2:
                concept_combo = f"{_CPSA_RNG.choice(concepts1)} + {_CPSA_RNG.choice(concepts2)}"
                solution = {
                    'approach': f'Combinatorial: {concept_combo}',
                    'description': f"Combine {concept_combo} to solve: {description}",
                    'creativity_type': 'combinatorial',
                    'novelty_factor': 0.750,
                    'feasibility': 0.600
                }
                solutions.append(solution)

        return solutions

    def _find_relevant_analogies(self, domain: str) -> List[Dict[str, Any]]:
        """Find analogies relevant to the problem domain"""
        # This would be expanded with a real analogy database
        analogies = [
            {
                'source': 'bird flight',
                'domain': 'technical',
                'lesson': 'aerodynamic principles'
            },
            {
                'source': 'ant colony',
                'domain': 'social',
                'lesson': 'distributed decision making'
            },
            {
                'source': 'immune system',
                'domain': 'scientific',
                'lesson': 'adaptive defense mechanisms'
            },
            {
                'source': 'ecosystem',
                'domain': 'business',
                'lesson': 'interdependent relationships'
            },
            {
                'source': 'neural network',
                'domain': 'technical',
                'lesson': 'parallel processing'
            }
        ]

        return [a for a in analogies if a['domain'] == domain or domain == 'general']

    def _get_relevant_categories(self, analysis: Dict[str, Any]) -> List[str]:
        """Get concept categories relevant to the problem"""
        domain = analysis.get('domain', 'general')
        categories = list(self.creative_associations.keys())

        # Prioritize domain-relevant categories
        domain_mapping = {
            'technical': ['technology', 'science'],
            'social': ['society', 'nature'],
            'scientific': ['science', 'technology'],
            'creative': ['art', 'society'],
            'business': ['society', 'technology']
        }

        relevant = domain_mapping.get(domain, ['technology', 'nature', 'society'])
        relevant.extend(categories)  # Add all categories as fallback

        return list(set(relevant))[:5]

    def _evaluate_solutions(self, solutions: List[Dict[str, Any]], problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate and rank solutions"""
        evaluated = []

        problem_text = str(problem.get('description', ''))
        for solution in solutions:
            # Score from the actual proposal text, not the generation-time placeholder
            desc = str(solution.get('description', solution.get('approach', '')))
            novelty = _novelty(desc, problem_text)
            feasibility = _feasibility(desc)
            solution['novelty_factor'] = novelty
            solution['feasibility'] = feasibility

            overall_score = (novelty * self.novelty_weight) + (feasibility * self.feasibility_weight)

            # Add evaluation metrics (all computed from content)
            evaluated_solution = solution.copy()
            evaluated_solution.update({
                'overall_score': overall_score,
                'creativity_level': novelty,
                'practicality': feasibility,
                'evaluation_criteria': {
                    'novelty': novelty,
                    'feasibility': feasibility,
                    'originality': _novelty(desc),
                    'elegance': float(min(1.0, feasibility * (0.5 + 0.5 * novelty)))
                }
            })

            evaluated.append(evaluated_solution)

        # Sort by overall score
        evaluated.sort(key=lambda x: x['overall_score'], reverse=True)

        return evaluated

    def _generate_meta_solutions(self, top_solutions: List[Dict[str, Any]], problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate meta-solutions by combining top solutions"""
        meta_solutions = []

        for combo in itertools.combinations(top_solutions, 2):
            sol1, sol2 = combo

            # Create combination
            combined_approach = f"Hybrid: {sol1['approach'].split(':')[1].strip()} + {sol2['approach'].split(':')[1].strip()}"
            combined_description = f"Combine '{sol1['description']}' with '{sol2['description']}'"

            meta_solution = {
                'approach': combined_approach,
                'description': combined_description,
                'creativity_type': 'meta_combinatorial',
                'novelty_factor': min(1.0, (sol1.get('novelty_factor', 0) + sol2.get('novelty_factor', 0)) * 1.2),
                'feasibility': (sol1.get('feasibility', 0) + sol2.get('feasibility', 0)) / 2,
                'parent_solutions': [sol1['approach'], sol2['approach']]
            }

            meta_solutions.append(meta_solution)

        return meta_solutions

    def _update_creativity_metrics(self, solutions: List[Dict[str, Any]]):
        """Update creativity performance metrics"""
        if not solutions:
            return

        # Calculate novelty score (average novelty factor)
        novelty_scores = [s.get('novelty_factor', 0) for s in solutions]
        self.creativity_metrics['novelty_score'] = np.mean(novelty_scores)

        # Calculate diversity score (variety of creativity types)
        creativity_types = [s.get('creativity_type', 'unknown') for s in solutions]
        unique_types = len(set(creativity_types))
        self.creativity_metrics['diversity_score'] = min(1.0, unique_types / 5.0)

        # Calculate feasibility score
        feasibility_scores = [s.get('feasibility', 0) for s in solutions]
        self.creativity_metrics['feasibility_score'] = np.mean(feasibility_scores)

        # Calculate innovation rate (high novelty + high feasibility solutions)
        innovative_solutions = [
            s for s in solutions
            if s.get('novelty_factor', 0) > 0.7 and s.get('feasibility', 0) > 0.6
        ]
        self.creativity_metrics['innovation_rate'] = len(innovative_solutions) / max(1, len(solutions))

    def get_creativity_profile(self) -> Dict[str, Any]:
        """Get the current creativity profile and capabilities"""
        return {
            'creativity_level': self.creativity_level,
            'creativity_metrics': self.creativity_metrics.copy(),
            'thinking_modes': list(self.thinking_modes.keys()),
            'solution_templates_count': len(self.solution_templates),
            'concept_categories': list(self.creative_associations.keys()),
            'solution_history_size': len(self.solution_history),
            'active_problems': len(self.active_problems)
        }

    def learn_from_solution_outcome(self, problem_id: str, solution_index: int, outcome: str):
        """
        Learn from the outcome of a solution to improve future creativity

        Args:
            problem_id: ID of the problem
            solution_index: Index of the solution tried
            outcome: 'success', 'partial_success', 'failure'
        """
        if problem_id not in self.active_problems:
            return

        # Find the solution record
        solution_record = None
        for record in self.solution_history:
            if record['problem_id'] == problem_id:
                solution_record = record
                break

        if not solution_record or solution_index >= len(solution_record['solutions']):
            return

        solution = solution_record['solutions'][solution_index]

        # Update creativity level based on outcome
        if outcome == 'success':
            self.creativity_level = min(1.0, self.creativity_level + 0.05)
            # Boost the approach that worked
            solution['outcome_feedback'] = 'positive'
        elif outcome == 'partial_success':
            self.creativity_level = min(1.0, self.creativity_level + 0.02)
            solution['outcome_feedback'] = 'neutral'
        else:  # failure
            self.creativity_level = max(0.1, self.creativity_level - 0.02)
            solution['outcome_feedback'] = 'negative'

        # Update thinking mode effectiveness
        thinking_mode = solution.get('creativity_type', 'unknown')
        if thinking_mode in self.idea_patterns:
            self.idea_patterns[thinking_mode].append(outcome)
        else:
            self.idea_patterns[thinking_mode] = [outcome]

# Global instance
cpsa_engine = CreativeProblemSolvingAlgorithm()

def get_cpsa_engine():
    """Get the global CPSA engine instance"""

# Global instance
cpsa_engine = CreativeProblemSolvingAlgorithm()

def get_cpsa_engine():
    """Get the global CPSA engine instance"""
    return cpsa_engine
