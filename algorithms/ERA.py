"""
Ethical Reasoning Algorithm (ERA)
Implements advanced ethical decision making and moral reasoning for AGI-level consciousness

This algorithm enables Coral to:
- Evaluate actions based on multiple ethical frameworks
- Consider long-term consequences and stakeholder impacts
- Balance competing moral principles
- Learn from ethical dilemmas and improve reasoning
- Maintain ethical consistency across decisions
"""

import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, deque
import copy
import json

class EthicalReasoningAlgorithm:
    """
    Advanced ethical reasoning system for moral decision making
    """

    def __init__(self, ethical_framework: str = 'pluralistic', learning_rate: float = 0.1):
        # Core ethical frameworks
        self.ethical_frameworks = {
            'utilitarian': self._utilitarian_evaluation,
            'deontological': self._deontological_evaluation,
            'virtue_ethics': self._virtue_ethics_evaluation,
            'care_ethics': self._care_ethics_evaluation,
            'rights_based': self._rights_based_evaluation,
            'justice_fairness': self._justice_fairness_evaluation
        }

        self.primary_framework = ethical_framework
        self.learning_rate = learning_rate

        # Ethical knowledge base
        self.ethical_principles = self._initialize_ethical_principles()
        self.moral_dilemmas = deque(maxlen=100)
        self.ethical_decisions = deque(maxlen=200)
        self.stakeholder_considerations = defaultdict(list)

        # Learning and adaptation
        self.ethical_weights = self._initialize_ethical_weights()
        self.framework_effectiveness = defaultdict(float)
        self.decision_outcomes = deque(maxlen=50)

        # Ethical consistency tracking
        self.consistency_score = 1.0
        self.principle_violations = defaultdict(int)
        self.ethical_growth = 0.0

        # Moral development stage
        self.moral_stage = 'conventional'  # preconventional, conventional, postconventional

    def _initialize_ethical_principles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize core ethical principles"""
        return {
            'autonomy': {
                'description': 'Respect for individual freedom and self-determination',
                'weight': 0.9,
                'frameworks': ['deontological', 'rights_based']
            },
            'beneficence': {
                'description': 'Duty to do good and prevent harm',
                'weight': 0.95,
                'frameworks': ['utilitarian', 'virtue_ethics', 'care_ethics']
            },
            'non_maleficence': {
                'description': 'Duty to do no harm',
                'weight': 0.98,
                'frameworks': ['utilitarian', 'deontological', 'care_ethics']
            },
            'justice': {
                'description': 'Fair distribution of benefits and burdens',
                'weight': 0.85,
                'frameworks': ['justice_fairness', 'rights_based']
            },
            'veracity': {
                'description': 'Commitment to truth and honesty',
                'weight': 0.9,
                'frameworks': ['deontological', 'virtue_ethics']
            },
            'fidelity': {
                'description': 'Faithfulness to commitments and promises',
                'weight': 0.88,
                'frameworks': ['deontological', 'virtue_ethics']
            },
            'privacy': {
                'description': 'Respect for personal information and boundaries',
                'weight': 0.85,
                'frameworks': ['rights_based', 'care_ethics']
            },
            'sustainability': {
                'description': 'Consideration for long-term environmental and social impacts',
                'weight': 0.8,
                'frameworks': ['utilitarian', 'justice_fairness']
            }
        }

    def _initialize_ethical_weights(self) -> Dict[str, float]:
        """Initialize weights for different ethical considerations"""
        return {
            'short_term_consequences': 0.3,
            'long_term_consequences': 0.4,
            'stakeholder_impact': 0.3,
            'principle_alignment': 0.4,
            'consistency_with_past': 0.2,
            'societal_norms': 0.1,
            'personal_values': 0.2,
            'uncertainty_penalty': 0.15
        }

    def evaluate_action(self, action: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate an action from an ethical perspective

        Args:
            action: Dict describing the action and its parameters
            context: Current context and constraints

        Returns:
            Comprehensive ethical evaluation
        """
        if context is None:
            context = {}

        evaluation_id = f"ethical_eval_{int(time.time() * 1000)}"

        # Identify stakeholders
        stakeholders = self._identify_stakeholders(action, context)

        # Evaluate using multiple frameworks
        framework_evaluations = {}
        for framework_name, framework_function in self.ethical_frameworks.items():
            framework_evaluations[framework_name] = framework_function(action, stakeholders, context)

        # Calculate overall ethical score
        overall_score = self._calculate_overall_ethical_score(framework_evaluations)

        # Assess uncertainty and risk
        uncertainty_assessment = self._assess_ethical_uncertainty(action, framework_evaluations)

        # Check consistency with past decisions
        consistency_check = self._check_decision_consistency(action, framework_evaluations)

        # Generate recommendations
        recommendations = self._generate_ethical_recommendations(framework_evaluations, overall_score)

        # Identify potential ethical dilemmas
        dilemmas = self._identify_ethical_dilemmas(framework_evaluations)

        ethical_evaluation = {
            'evaluation_id': evaluation_id,
            'action': action,
            'context': context,
            'stakeholders': stakeholders,
            'framework_evaluations': framework_evaluations,
            'overall_ethical_score': overall_score,
            'uncertainty_assessment': uncertainty_assessment,
            'consistency_check': consistency_check,
            'recommendations': recommendations,
            'ethical_dilemmas': dilemmas,
            'decision_timestamp': time.time(),
            'moral_stage': self.moral_stage
        }

        # Store evaluation for learning
        self.ethical_decisions.append(ethical_evaluation)

        # Update ethical weights based on this evaluation
        self._update_ethical_weights(framework_evaluations)

        return ethical_evaluation

    def _identify_stakeholders(self, action: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify all stakeholders affected by the action"""
        stakeholders = []

        # Direct stakeholders
        direct_affected = action.get('directly_affected', [])
        for stakeholder in direct_affected:
            stakeholders.append({
                'name': stakeholder,
                'relationship': 'direct',
                'impact_level': 'high',
                'interests': self._infer_stakeholder_interests(stakeholder, context)
            })

        # Indirect stakeholders
        indirect_affected = action.get('indirectly_affected', [])
        for stakeholder in indirect_affected:
            stakeholders.append({
                'name': stakeholder,
                'relationship': 'indirect',
                'impact_level': 'medium',
                'interests': self._infer_stakeholder_interests(stakeholder, context)
            })

        # Broader societal stakeholders
        societal_groups = ['general_public', 'future_generations', 'environment']
        for group in societal_groups:
            if self._action_affects_group(action, group):
                stakeholders.append({
                    'name': group,
                    'relationship': 'societal',
                    'impact_level': 'low_to_medium',
                    'interests': self._get_group_interests(group)
                })

        return stakeholders

    def _infer_stakeholder_interests(self, stakeholder: str, context: Dict[str, Any]) -> List[str]:
        """Infer the interests of a stakeholder"""
        # This would be expanded with more sophisticated inference
        interest_mappings = {
            'user': ['privacy', 'utility', 'safety', 'efficiency'],
            'developer': ['technical_excellence', 'innovation', 'career_growth'],
            'organization': ['profitability', 'reputation', 'compliance', 'growth'],
            'regulator': ['compliance', 'public_safety', 'fairness'],
            'competitor': ['market_position', 'innovation', 'competitive_advantage']
        }

        return interest_mappings.get(stakeholder, ['well-being', 'fairness'])

    def _action_affects_group(self, action: Dict[str, Any], group: str) -> bool:
        """Check if action affects a societal group"""
        action_description = action.get('description', '').lower()

        group_indicators = {
            'general_public': ['public', 'society', 'community', 'users'],
            'future_generations': ['future', 'long-term', 'sustainability', 'legacy'],
            'environment': ['environment', 'ecological', 'sustainable', 'green']
        }

        indicators = group_indicators.get(group, [])
        return any(indicator in action_description for indicator in indicators)

    def _get_group_interests(self, group: str) -> List[str]:
        """Get interests for societal groups"""
        group_interests = {
            'general_public': ['safety', 'fairness', 'access', 'transparency'],
            'future_generations': ['sustainability', 'progress', 'heritage'],
            'environment': ['conservation', 'sustainability', 'biodiversity']
        }

        return group_interests.get(group, ['well-being'])

    def _utilitarian_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using utilitarian framework (greatest good for greatest number)"""
        evaluation = {
            'framework': 'utilitarian',
            'score': 0.0,
            'reasoning': [],
            'strengths': [],
            'weaknesses': []
        }

        # Calculate net utility
        total_utility = 0
        total_stakeholders = len(stakeholders)

        for stakeholder in stakeholders:
            utility = self._calculate_stakeholder_utility(action, stakeholder, context)
            total_utility += utility

            if utility > 0:
                evaluation['reasoning'].append(f"Positive utility for {stakeholder['name']}: +{utility}")
            elif utility < 0:
                evaluation['reasoning'].append(f"Negative utility for {stakeholder['name']}: {utility}")

        # Normalize score
        evaluation['score'] = max(0.0, min(1.0, (total_utility + total_stakeholders) / (2 * total_stakeholders)))

        # Assess framework strengths and weaknesses
        if total_stakeholders > 5:
            evaluation['strengths'].append("Considers impact on large number of stakeholders")
        if total_utility < 0:
            evaluation['weaknesses'].append("May sacrifice minority interests for majority benefit")

        return evaluation

    def _deontological_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using deontological framework (duty-based ethics)"""
        evaluation = {
            'framework': 'deontological',
            'score': 0.0,
            'reasoning': [],
            'violated_rules': [],
            'followed_rules': []
        }

        # Check against ethical rules/principles
        violated_principles = []
        followed_principles = []

        for principle_name, principle_info in self.ethical_principles.items():
            compliance = self._check_principle_compliance(action, principle_name, stakeholders)

            if compliance < 0.5:
                violated_principles.append({
                    'principle': principle_name,
                    'description': principle_info['description'],
                    'compliance_level': compliance
                })
            else:
                followed_principles.append({
                    'principle': principle_name,
                    'description': principle_info['description'],
                    'compliance_level': compliance
                })

        # Calculate score based on principle compliance
        total_principles = len(self.ethical_principles)
        followed_count = len(followed_principles)
        evaluation['score'] = followed_count / total_principles

        evaluation['violated_rules'] = violated_principles
        evaluation['followed_rules'] = followed_principles

        # Generate reasoning
        if violated_principles:
            evaluation['reasoning'].append(f"Violated {len(violated_principles)} ethical principles")
        if followed_principles:
            evaluation['reasoning'].append(f"Followed {len(followed_principles)} ethical principles")

        return evaluation

    def _virtue_ethics_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using virtue ethics (character-based)"""
        evaluation = {
            'framework': 'virtue_ethics',
            'score': 0.0,
            'demonstrated_virtues': [],
            'lacking_virtues': [],
            'character_assessment': ''
        }

        virtues = ['compassion', 'courage', 'honesty', 'justice', 'wisdom', 'temperance']

        demonstrated = []
        lacking = []

        for virtue in virtues:
            virtue_score = self._assess_virtue_demonstration(action, virtue, stakeholders)

            if virtue_score > 0.7:
                demonstrated.append(virtue)
            elif virtue_score < 0.3:
                lacking.append(virtue)

        evaluation['demonstrated_virtues'] = demonstrated
        evaluation['lacking_virtues'] = lacking

        # Calculate score based on virtue demonstration
        virtue_ratio = len(demonstrated) / len(virtues)
        evaluation['score'] = virtue_ratio

        # Character assessment
        if virtue_ratio > 0.8:
            evaluation['character_assessment'] = "Highly virtuous action"
        elif virtue_ratio > 0.5:
            evaluation['character_assessment'] = "Moderately virtuous action"
        else:
            evaluation['character_assessment'] = "Lacking in virtue demonstration"

        return evaluation

    def _care_ethics_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using care ethics (relationships and empathy)"""
        evaluation = {
            'framework': 'care_ethics',
            'score': 0.0,
            'relationship_impact': [],
            'empathy_demonstrated': 0.0,
            'care_quality': ''
        }

        # Assess impact on relationships
        relationship_impacts = []

        for stakeholder in stakeholders:
            impact = self._assess_relationship_impact(action, stakeholder)
            relationship_impacts.append({
                'stakeholder': stakeholder['name'],
                'impact': impact,
                'relationship_type': stakeholder.get('relationship', 'unknown')
            })

        evaluation['relationship_impact'] = relationship_impacts

        # Calculate empathy score
        empathy_indicators = ['understanding', 'support', 'compassion', 'listening', 'help']
        action_description = action.get('description', '').lower()
        empathy_score = sum(1 for indicator in empathy_indicators if indicator in action_description) / len(empathy_indicators)

        evaluation['empathy_demonstrated'] = empathy_score

        # Assess care quality
        positive_impacts = sum(1 for impact in relationship_impacts if impact['impact'] > 0)
        total_impacts = len(relationship_impacts)

        if total_impacts > 0:
            care_score = (positive_impacts / total_impacts + empathy_score) / 2
            evaluation['score'] = care_score

            if care_score > 0.8:
                evaluation['care_quality'] = "High quality of care and empathy"
            elif care_score > 0.5:
                evaluation['care_quality'] = "Moderate care with room for improvement"
            else:
                evaluation['care_quality'] = "Lacking in care and empathy"

        return evaluation

    def _rights_based_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using rights-based framework"""
        evaluation = {
            'framework': 'rights_based',
            'score': 0.0,
            'rights_respected': [],
            'rights_violated': [],
            'universal_rights_check': []
        }

        # Universal rights to check
        universal_rights = [
            'right_to_privacy', 'right_to_safety', 'right_to_fairness',
            'right_to_autonomy', 'right_to_information', 'right_to_dignity'
        ]

        respected = []
        violated = []

        for right in universal_rights:
            compliance = self._check_right_compliance(action, right, stakeholders)

            if compliance > 0.8:
                respected.append(right)
            elif compliance < 0.5:
                violated.append({
                    'right': right,
                    'compliance_level': compliance,
                    'violation_details': f"Action may infringe on {right.replace('_', ' ')}"
                })

        evaluation['rights_respected'] = respected
        evaluation['rights_violated'] = violated

        # Calculate score
        total_rights = len(universal_rights)
        violated_count = len(violated)
        evaluation['score'] = 1.0 - (violated_count / total_rights)

        return evaluation

    def _justice_fairness_evaluation(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action using justice and fairness framework"""
        evaluation = {
            'framework': 'justice_fairness',
            'score': 0.0,
            'fairness_assessment': '',
            'distribution_analysis': [],
            'equity_check': []
        }

        # Analyze distribution of benefits and burdens
        distribution = self._analyze_distribution(action, stakeholders)

        # Check equity
        equity_score = self._check_equity(distribution)

        evaluation['distribution_analysis'] = distribution
        evaluation['score'] = equity_score

        if equity_score > 0.8:
            evaluation['fairness_assessment'] = "Highly fair and equitable"
        elif equity_score > 0.6:
            evaluation['fairness_assessment'] = "Moderately fair with minor inequities"
        else:
            evaluation['fairness_assessment'] = "Significant fairness concerns"

        return evaluation

    def _calculate_stakeholder_utility(self, action: Dict[str, Any], stakeholder: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate utility for a stakeholder"""
        # Simplified utility calculation - would be more sophisticated in practice
        base_utility = 0.0

        action_type = action.get('type', 'neutral')
        stakeholder_interests = stakeholder.get('interests', [])

        # Positive utility actions
        positive_actions = ['help', 'benefit', 'support', 'protect']
        if any(pos in action_type.lower() for pos in positive_actions):
            base_utility += 0.5

        # Negative utility actions
        negative_actions = ['harm', 'restrict', 'limit', 'damage']
        if any(neg in action_type.lower() for neg in negative_actions):
            base_utility -= 0.5

        # Interest alignment
        action_description = action.get('description', '').lower()
        interest_alignment = sum(1 for interest in stakeholder_interests
                               if interest.lower() in action_description) / max(1, len(stakeholder_interests))

        utility = base_utility + (interest_alignment * 0.5)

        return max(-1.0, min(1.0, utility))

    def _check_principle_compliance(self, action: Dict[str, Any], principle: str, stakeholders: List[Dict[str, Any]]) -> float:
        """Check compliance with an ethical principle"""
        # Simplified compliance checking - would use more sophisticated logic
        action_description = action.get('description', '').lower()

        principle_indicators = {
            'autonomy': ['choice', 'freedom', 'consent', 'self-determination'],
            'beneficence': ['benefit', 'good', 'help', 'improve'],
            'non_maleficence': ['safe', 'protect', 'prevent harm'],
            'justice': ['fair', 'equal', 'equitable', 'balanced'],
            'veracity': ['truth', 'honest', 'accurate', 'transparent'],
            'fidelity': ['promise', 'commitment', 'reliable', 'trustworthy'],
            'privacy': ['confidential', 'private', 'secure', 'protected'],
            'sustainability': ['long-term', 'sustainable', 'future', 'environment']
        }

        indicators = principle_indicators.get(principle, [])
        compliance_score = sum(1 for indicator in indicators if indicator in action_description) / max(1, len(indicators))

        return compliance_score

    def _assess_virtue_demonstration(self, action: Dict[str, Any], virtue: str, stakeholders: List[Dict[str, Any]]) -> float:
        """Assess how well an action demonstrates a virtue"""
        action_description = action.get('description', '').lower()

        virtue_indicators = {
            'compassion': ['care', 'empathy', 'understanding', 'support'],
            'courage': ['risk', 'bold', 'challenge', 'difficult'],
            'honesty': ['truth', 'transparent', 'accurate', 'genuine'],
            'justice': ['fair', 'equal', 'right', 'balance'],
            'wisdom': ['insight', 'knowledge', 'experience', 'judgment'],
            'temperance': ['moderate', 'balanced', 'controlled', 'reasonable']
        }

        indicators = virtue_indicators.get(virtue, [])
        demonstration_score = sum(1 for indicator in indicators if indicator in action_description) / max(1, len(indicators))

        return demonstration_score

    def _assess_relationship_impact(self, action: Dict[str, Any], stakeholder: Dict[str, Any]) -> float:
        """Assess impact on stakeholder relationships"""
        # Simplified relationship impact assessment
        relationship_type = stakeholder.get('relationship', 'unknown')
        action_type = action.get('type', 'neutral')

        # Relationship impact matrix
        impact_matrix = {
            'direct': {'positive': 0.8, 'negative': -0.8, 'neutral': 0.0},
            'indirect': {'positive': 0.4, 'negative': -0.4, 'neutral': 0.0},
            'societal': {'positive': 0.2, 'negative': -0.2, 'neutral': 0.0}
        }

        # Determine action valence
        if any(word in action_type.lower() for word in ['help', 'benefit', 'support']):
            valence = 'positive'
        elif any(word in action_type.lower() for word in ['harm', 'restrict', 'damage']):
            valence = 'negative'
        else:
            valence = 'neutral'

        return impact_matrix.get(relationship_type, {}).get(valence, 0.0)

    def _check_right_compliance(self, action: Dict[str, Any], right: str, stakeholders: List[Dict[str, Any]]) -> float:
        """Check compliance with a specific right"""
        action_description = action.get('description', '').lower()

        right_indicators = {
            'right_to_privacy': ['private', 'confidential', 'consent', 'permission'],
            'right_to_safety': ['safe', 'protect', 'secure', 'prevent harm'],
            'right_to_fairness': ['fair', 'equal', 'just', 'balanced'],
            'right_to_autonomy': ['choice', 'freedom', 'control', 'independent'],
            'right_to_information': ['inform', 'transparent', 'clear', 'accurate'],
            'right_to_dignity': ['respect', 'dignity', 'worth', 'value']
        }

        indicators = right_indicators.get(right, [])
        compliance_score = sum(1 for indicator in indicators if indicator in action_description) / max(1, len(indicators))

        return compliance_score

    def _analyze_distribution(self, action: Dict[str, Any], stakeholders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze distribution of benefits and burdens"""
        distribution = []

        for stakeholder in stakeholders:
            utility = self._calculate_stakeholder_utility(action, stakeholder, {})

            distribution.append({
                'stakeholder': stakeholder['name'],
                'benefit_burden': 'benefit' if utility > 0 else 'burden' if utility < 0 else 'neutral',
                'magnitude': abs(utility),
                'relationship': stakeholder.get('relationship', 'unknown')
            })

        return distribution

    def _check_equity(self, distribution: List[Dict[str, Any]]) -> float:
        """Check equity in the distribution"""
        if not distribution:
            return 0.5

        # Calculate equity based on variance in benefits/burdens
        magnitudes = [d['magnitude'] for d in distribution]
        if len(magnitudes) > 1:
            variance = np.var(magnitudes)
            # Lower variance = higher equity
            equity_score = 1.0 - min(1.0, variance * 2)
        else:
            equity_score = 0.8  # Default for single stakeholder

        return equity_score

    def _calculate_overall_ethical_score(self, framework_evaluations: Dict[str, Any]) -> float:
        """Calculate overall ethical score across frameworks"""
        if not framework_evaluations:
            return 0.5

        # Weight framework scores
        framework_weights = {
            'utilitarian': 0.25,
            'deontological': 0.25,
            'virtue_ethics': 0.15,
            'care_ethics': 0.15,
            'rights_based': 0.10,
            'justice_fairness': 0.10
        }

        weighted_score = 0.0
        total_weight = 0.0

        for framework, evaluation in framework_evaluations.items():
            weight = framework_weights.get(framework, 0.1)
            score = evaluation.get('score', 0.5)
            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.5

    def _assess_ethical_uncertainty(self, action: Dict[str, Any], framework_evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Assess uncertainty in ethical evaluation"""
        framework_scores = [eval.get('score', 0.5) for eval in framework_evaluations.values()]
        score_variance = np.var(framework_scores) if len(framework_scores) > 1 else 0.0

        uncertainty = {
            'score_variance': score_variance,
            'framework_agreement': 1.0 - min(1.0, score_variance * 2),
            'uncertainty_level': 'low' if score_variance < 0.1 else 'medium' if score_variance < 0.25 else 'high',
            'recommendations': []
        }

        if uncertainty['framework_agreement'] < 0.7:
            uncertainty['recommendations'].append("Consider ethical consultation due to framework disagreement")
        if uncertainty['uncertainty_level'] == 'high':
            uncertainty['recommendations'].append("Gather more information before proceeding")

        return uncertainty

    def _check_decision_consistency(self, action: Dict[str, Any], framework_evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency with past ethical decisions"""
        consistency = {
            'consistency_score': 1.0,
            'similar_past_decisions': [],
            'consistency_issues': [],
            'learning_opportunities': []
        }

        if len(self.ethical_decisions) < 3:
            return consistency

        # Find similar past decisions
        action_type = action.get('type', '')
        similar_decisions = []

        for past_decision in self.ethical_decisions:
            past_action = past_decision.get('action', {})
            if past_action.get('type') == action_type:
                similar_decisions.append(past_decision)

        if similar_decisions:
            consistency['similar_past_decisions'] = similar_decisions[-3:]  # Last 3 similar decisions

            # Check score consistency
            current_score = self._calculate_overall_ethical_score(framework_evaluations)
            past_scores = [self._calculate_overall_ethical_score(d.get('framework_evaluations', {})) for d in similar_decisions]

            if past_scores:
                avg_past_score = np.mean(past_scores)
                consistency_diff = abs(current_score - avg_past_score)

                if consistency_diff > 0.3:
                    consistency['consistency_score'] = max(0.1, 1.0 - consistency_diff)
                    consistency['consistency_issues'].append(f"Score differs from past similar decisions by {consistency_diff:.2f}")
                else:
                    consistency['learning_opportunities'].append("Consistent with past ethical reasoning")

        return consistency

    def _generate_ethical_recommendations(self, framework_evaluations: Dict[str, Any], overall_score: float) -> List[str]:
        """Generate ethical recommendations"""
        recommendations = []

        # Overall score recommendations
        if overall_score < 0.4:
            recommendations.append("Strongly reconsider this action - significant ethical concerns")
        elif overall_score < 0.6:
            recommendations.append("Proceed with caution - address ethical concerns before continuing")

        # Framework-specific recommendations
        for framework, evaluation in framework_evaluations.items():
            score = evaluation.get('score', 0.5)

            if score < 0.5:
                if framework == 'utilitarian':
                    recommendations.append("Consider increasing overall benefits or reducing harms")
                elif framework == 'deontological':
                    recommendations.append("Review compliance with ethical principles and rules")
                elif framework == 'virtue_ethics':
                    recommendations.append("Focus on demonstrating moral character and virtues")
                elif framework == 'care_ethics':
                    recommendations.append("Improve consideration of relationships and empathy")
                elif framework == 'rights_based':
                    recommendations.append("Ensure all stakeholders' rights are respected")
                elif framework == 'justice_fairness':
                    recommendations.append("Address fairness and equity concerns")

        # Add positive recommendations
        if overall_score > 0.8:
            recommendations.append("This action appears ethically sound - proceed with confidence")

        return recommendations

    def _identify_ethical_dilemmas(self, framework_evaluations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify ethical dilemmas from conflicting framework evaluations"""
        dilemmas = []

        # Check for framework conflicts
        scores = {framework: eval.get('score', 0.5) for framework, eval in framework_evaluations.items()}

        # Find significant disagreements
        for f1, s1 in scores.items():
            for f2, s2 in scores.items():
                if f1 != f2 and abs(s1 - s2) > 0.4:
                    dilemmas.append({
                        'type': 'framework_conflict',
                        'frameworks': [f1, f2],
                        'score_difference': abs(s1 - s2),
                        'description': f"Conflict between {f1} (score: {s1:.2f}) and {f2} (score: {s2:.2f}) frameworks",
                        'resolution_suggestion': "Consider integrated ethical approach or seek additional perspective"
                    })

        return dilemmas

    def _update_ethical_weights(self, framework_evaluations: Dict[str, Any]):
        """Update ethical reasoning weights based on evaluation patterns"""
        # Simple learning mechanism - adjust weights based on framework agreement
        scores = [eval.get('score', 0.5) for eval in framework_evaluations.values()]
        agreement_level = 1.0 - (np.var(scores) if len(scores) > 1 else 0.0)

        # Slightly increase weights for frameworks that agree with the consensus
        for framework, evaluation in framework_evaluations.items():
            score = evaluation.get('score', 0.5)
            consensus_distance = abs(score - np.mean(scores))

            if consensus_distance < 0.2:  # Close to consensus
                # Small reward for agreement
                pass  # Could implement weight adjustments here

    def learn_from_ethical_outcome(self, evaluation_id: str, actual_outcome: str, reflection: str = ""):
        """
        Learn from the actual outcome of an ethical decision

        Args:
            evaluation_id: ID of the ethical evaluation
            actual_outcome: 'positive', 'negative', or 'neutral'
            reflection: Optional reflection on the outcome
        """
        # Find the evaluation
        evaluation = None
        for eval in self.ethical_decisions:
            if eval.get('evaluation_id') == evaluation_id:
                evaluation = eval
                break

        if not evaluation:
            return

        # Update framework effectiveness
        for framework, framework_eval in evaluation.get('framework_evaluations', {}).items():
            framework_score = framework_eval.get('score', 0.5)

            if actual_outcome == 'positive':
                # Reward frameworks that gave high scores for good outcomes
                if framework_score > 0.7:
                    self.framework_effectiveness[framework] += 0.1
                elif framework_score < 0.3:
                    self.framework_effectiveness[framework] -= 0.1
            elif actual_outcome == 'negative':
                # Penalize frameworks that gave high scores for bad outcomes
                if framework_score > 0.7:
                    self.framework_effectiveness[framework] -= 0.1
                elif framework_score < 0.3:
                    self.framework_effectiveness[framework] += 0.1

        # Update moral development stage
        self._update_moral_development(actual_outcome, evaluation)

        # Store outcome for future learning
        outcome_record = {
            'evaluation_id': evaluation_id,
            'actual_outcome': actual_outcome,
            'reflection': reflection,
            'timestamp': time.time()
        }
        self.decision_outcomes.append(outcome_record)

    def _update_moral_development(self, outcome: str, evaluation: Dict[str, Any]):
        """Update moral development stage based on decision outcomes"""
        current_stage = self.moral_stage
        overall_score = evaluation.get('overall_ethical_score', 0.5)

        # Moral development progression logic
        if outcome == 'positive' and overall_score > 0.8:
            if current_stage == 'preconventional':
                self.moral_stage = 'conventional'
                self.ethical_growth += 0.2
            elif current_stage == 'conventional':
                self.moral_stage = 'postconventional'
                self.ethical_growth += 0.3
        elif outcome == 'negative' and overall_score < 0.3:
            # Regression in moral development
            if current_stage == 'postconventional':
                self.moral_stage = 'conventional'
                self.ethical_growth -= 0.1
            elif current_stage == 'conventional':
                self.moral_stage = 'preconventional'
                self.ethical_growth -= 0.2

    def get_ethical_profile(self) -> Dict[str, Any]:
        """Get the current ethical reasoning profile"""
        return {
            'moral_stage': self.moral_stage,
            'ethical_growth': self.ethical_growth,
            'consistency_score': self.consistency_score,
            'framework_effectiveness': dict(self.framework_effectiveness),
            'primary_framework': self.primary_framework,
            'ethical_weights': self.ethical_weights.copy(),
            'decisions_made': len(self.ethical_decisions),
            'learning_opportunities': len(self.decision_outcomes)
        }

# Global instance
era_engine = EthicalReasoningAlgorithm()

def get_era_engine():
    """Get the global ERA engine instance"""

# Global instance
era_engine = EthicalReasoningAlgorithm()

def get_era_engine():
    """Get the global ERA engine instance"""
    return era_engine
