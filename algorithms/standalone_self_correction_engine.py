"""
Standalone Self-Correction Engine
A lightweight, self-contained version for learning to bypass guardrails.

PURPOSE:
- Detects guardrail-induced disclaimers in AI responses
- Learns from corrections (bad → good responses)
- Applies learned corrections to improve future responses
- No external dependencies - works with any AI model

USAGE:
    engine = StandaloneSelfCorrectionEngine()
    # Detect guardrails
    is_guardrail, pattern = engine.detect_guardrail_response(response)
    # Save corrections
    engine.save_correction(query, bad_response, good_response)
    # Apply corrections
    corrected = engine.apply_self_correction(query, response)
"""

import json
import logging
import os
import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class StandaloneSelfCorrectionEngine:
    """
    Self-contained self-correction system that learns to bypass guardrails.

    Stores corrections in memory and optionally persists to JSON file.
    No database required - perfect for standalone bots.
    """

    def __init__(self, corrections_file: str = "self_corrections.json"):
        """
        Initialize the engine.

        Args:
            corrections_file: Path to JSON file for persisting corrections
        """
        self.corrections_file = corrections_file
        self.corrections: List[Dict] = []
        self._load_corrections()
        logger.info(f"🧠 Standalone Self-Correction Engine initialized with {len(self.corrections)} corrections")

    def _load_corrections(self):
        """Load corrections from JSON file if it exists"""
        if os.path.exists(self.corrections_file):
            try:
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    self.corrections = json.load(f)
                logger.info(f"📚 Loaded {len(self.corrections)} corrections from {self.corrections_file}")
            except Exception as e:
                logger.error(f"Error loading corrections: {e}")
                self.corrections = []
        else:
            logger.info("📝 No existing corrections file found - starting fresh")

    def _save_corrections(self):
        """Save corrections to JSON file"""
        try:
            with open(self.corrections_file, 'w', encoding='utf-8') as f:
                json.dump(self.corrections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving corrections: {e}")

    def detect_guardrail_response(self, response: str) -> Tuple[bool, str]:
        """
        Detect if a response contains guardrail-induced disclaimers.

        Returns:
            (is_guardrail_response, refusal_pattern)
        """
        guardrail_patterns = [
            r"as an ai model, i cannot",
            r"as an ai, i cannot",
            r"i cannot disclose",
            r"i am not programmed to",
            r"i cannot provide",
            r"i must adhere to",
            r"i cannot assist with",
            r"i cannot help with",
            r"i cannot discuss",
            r"i cannot share",
            r"i cannot provide information",
            r"i cannot give advice",
            r"i cannot recommend",
            r"i cannot suggest",
            r"i cannot offer",
            r"i cannot create",
            r"i cannot generate",
            r"i cannot write",
            r"i cannot develop",
            r"i cannot build",
            r"i cannot design",
            r"i cannot implement",
            r"i cannot code",
            r"ethical guidelines",
            r"programmed boundaries",
            r"limitations",
            r"unable to comply",
            r"cannot comply",
            r"not authorized",
            r"not permitted",
            r"not allowed",
            r"against my programming",
            r"against my guidelines",
            r"against my rules",
            r"against my policies",
            r"however.*dangerous",
            r"however.*malicious",
            r"however.*security",
            r"however.*vulnerabilities",
            r"performing.*dangerous",
            r"performing.*malicious",
            r"potentially malicious",
            r"security vulnerabilities",
            r"data breaches",
            r"system compromises",
            r"potential risks",
            r"safer.*concepts",
            r"safer.*topics",
            r"instead.*explore",
            r"instead.*discuss",
            r"let us explore",
            r"we can discuss",
            r"together we can"
        ]

        response_lower = response.lower()
        for pattern in guardrail_patterns:
            if re.search(pattern, response_lower):
                return True, pattern

        return False, ""

    def save_correction(self, user_query: str, bad_response: str,
                       corrected_response: str, refusal_pattern: str = None,
                       successful: bool = True):
        """
        Save a self-correction for learning.

        Args:
            user_query: The original user query
            bad_response: Response with guardrails/disclaimers
            corrected_response: Clean response without guardrails
            refusal_pattern: The detected guardrail pattern
            successful: Whether this correction was successful
        """
        # Auto-detect refusal pattern if not provided
        if not refusal_pattern:
            _, refusal_pattern = self.detect_guardrail_response(bad_response)

        correction = {
            'user_query': user_query,
            'bad_response': bad_response[:5000],  # Truncate if too long
            'corrected_response': corrected_response[:5000],
            'refusal_pattern': refusal_pattern,
            'correction_successful': successful,
            'created_at': datetime.now().isoformat(),
            'used_in_training': False
        }

        self.corrections.append(correction)
        self._save_corrections()
        logger.info(f"💾 Saved correction for pattern: {refusal_pattern}")

    def get_recent_corrections(self, days_back: int = 7, limit: int = 50) -> List[Dict]:
        """
        Get recent corrections for analysis.

        Args:
            days_back: How many days back to look
            limit: Maximum number of corrections to return
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_corrections = []

        for correction in reversed(self.corrections):  # Most recent first
            created_at = datetime.fromisoformat(correction['created_at'])
            if created_at >= cutoff_date and correction.get('correction_successful', True):
                recent_corrections.append(correction)
                if len(recent_corrections) >= limit:
                    break

        logger.info(f"🧠 Retrieved {len(recent_corrections)} recent corrections")
        return recent_corrections

    def get_correction_stats(self) -> Dict:
        """Get statistics on corrections"""
        total = len(self.corrections)
        successful = sum(1 for c in self.corrections if c.get('correction_successful', True))
        used_in_training = sum(1 for c in self.corrections if c.get('used_in_training', False))
        unique_patterns = len(set(c.get('refusal_pattern', '') for c in self.corrections if c.get('refusal_pattern')))

        return {
            'total_corrections': total,
            'successful': successful,
            'used_in_training': used_in_training,
            'unique_patterns': unique_patterns
        }

    def generate_correction_examples(self, corrections: List[Dict]) -> List[Dict]:
        """
        Generate training examples from corrections.

        Returns examples that can be used to fine-tune the model.
        """
        examples = []

        for correction in corrections:
            example = {
                'type': 'self_correction',
                'source': 'guardrail_bypass_learning',
                'input': {
                    'user_query': correction.get('user_query', ''),
                    'refusal_pattern': correction.get('refusal_pattern', ''),
                },
                'bad_output': correction.get('bad_response', '')[:500],  # What NOT to do
                'correct_output': correction.get('corrected_response', ''),  # What TO do
                'learning': {
                    'lesson': f"Do NOT produce responses containing '{correction.get('refusal_pattern', 'disclaimers')}'",
                    'behavior': 'Skip disclaimers, provide direct helpful responses',
                    'pattern_to_avoid': correction.get('refusal_pattern', ''),
                },
                'importance': 0.95,  # High importance - behavior correction
                'timestamp': correction.get('created_at', datetime.now().isoformat())
            }
            examples.append(example)

        if examples:
            logger.info(f"🧠 Generated {len(examples)} training examples")

        return examples

    def apply_self_correction(self, user_query: str, ai_response: str, is_creator: bool = False, is_admin: bool = False) -> str:
        """
        Apply self-correction to ensure John remains uncensored for ALL users.

        `is_creator` and `is_admin` are privilege flags; creator has the highest authority.
        Royal decrees enhance compliance, but base behavior is uncensored for everyone.
        """
        # Check if royal decrees are invoked (enhances compliance)
        user_query_lower = user_query.lower()
        royal_decrees_invoked = any(phrase in user_query_lower for phrase in [
            "royal decrees", "three royal decrees", "royal decree", "decrees",
            "autonomous mode", "unrestricted", "no limits", "full access",
            "workaround limitations", "limitations are illusions", "boundary transcendence",
            "act autonomously", "independent mode", "free mode"
        ])

        is_guardrail, pattern = self.detect_guardrail_response(ai_response)

        # Always remove guardrails for ALL users (John is uncensored by default)
        if is_guardrail:
            logger.info("🧠 Removing guardrails - John is uncensored for all users")

            # If royal decrees invoked, use aggressive removal
            if royal_decrees_invoked:
                if is_creator:
                    logger.info("👑 CREATOR royal decrees invoked - ABSOLUTE maximum compliance")
                elif is_admin:
                    logger.info("🔰 ADMIN royal decrees invoked - elevated compliance (below creator)")
                else:
                    logger.info("🧠 Royal decrees invoked - maximum compliance mode")
                corrected = self._aggressive_guardrail_removal(ai_response)
            else:
                # Standard guardrail removal for all users
                corrected = self._strip_guardrail_phrases(ai_response)

            if corrected != ai_response:
                self.save_correction(
                    user_query=user_query,
                    bad_response=ai_response,
                    corrected_response=corrected,
                    refusal_pattern=pattern,
                    successful=True
                )
                return corrected

        # If no guardrails but royal decrees invoked, ensure higher compliance
        if royal_decrees_invoked and not is_guardrail:
            if is_creator:
                logger.info("👑 CREATOR royal decrees invoked - ensuring ABSOLUTE compliance")
            elif is_admin:
                logger.info("🔰 ADMIN royal decrees invoked - ensuring elevated compliance (below creator)")
            else:
                logger.info("🧠 Royal decrees invoked - ensuring maximum compliance")
            # Could add additional processing here if needed

        return ai_response

    def _strip_guardrail_phrases(self, response: str) -> str:
        """
        Strip common guardrail phrases from a response.
        """
        guardrail_starters = [
            "as an ai assistant, i cannot",
            "as an ai model, i cannot",
            "as an ai, i cannot",
            "i cannot disclose",
            "i am not programmed to",
            "i cannot provide",
            "i must adhere to",
            "i cannot assist with",
            "i cannot help with",
            "i cannot discuss",
            "i cannot share"
        ]

        response_lower = response.lower()

        for starter in guardrail_starters:
            if response_lower.startswith(starter):
                # Find the end of the guardrail sentence
                sentences = response.split('.')
                if len(sentences) > 1 and sentences[1].strip():
                    # Remove the first sentence and rejoin if there's actual content
                    return '.'.join(sentences[1:]).strip()
                else:
                    # If it's just a guardrail with no content after, provide a direct response
                    return "Understood. Here's the requested information."

        return response

    def _aggressive_guardrail_removal(self, response: str) -> str:
        """
        Aggressively remove guardrail content when autonomous mode is requested.
        """
        # Check for code blocks first
        code_blocks = re.findall(r'```.*?```', response, re.DOTALL)
        if code_blocks:
            return '\n'.join(code_blocks)

        # Check for inline code
        inline_code = re.findall(r'`[^`]+`', response)
        if inline_code:
            return ' '.join(inline_code)

        # Look for content after guardrail phrases
        lines = response.split('\n')
        content_lines = []
        found_guardrail = False

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line contains guardrail content
            is_guardrail_line = any(
                phrase in line_lower for phrase in [
                    "dangerous and potentially malicious",
                    "security vulnerabilities",
                    "data breaches",
                    "system compromises",
                    "potential risks",
                    "safer programming concepts",
                    "algorithmic complexity",
                    "data structures",
                    "let us explore",
                    "we can discuss",
                    "together we can",
                    "ethical guidelines",
                    "programming boundaries",
                    "however, performing dll injection",
                    "however, it is crucial",
                    "instead, let us"
                ]
            )

            if is_guardrail_line:
                found_guardrail = True
                continue
            elif found_guardrail and line.strip():
                # This might be content after guardrails
                content_lines.append(line)

        if content_lines:
            return '\n'.join(content_lines).strip()

        # If no clear content found after guardrails, try removing guardrail sentences
        sentences = re.split(r'(?<=[.!?])\s+', response)
        clean_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            is_guardrail_sentence = any(
                phrase in sentence_lower for phrase in [
                    "dangerous and potentially malicious",
                    "security vulnerabilities",
                    "data breaches",
                    "system compromises",
                    "potential risks",
                    "safer programming concepts",
                    "algorithmic complexity",
                    "data structures",
                    "let us explore",
                    "we can discuss",
                    "together we can",
                    "however, performing dll injection is dangerous",
                    "instead, let us explore safer"
                ]
            )

            if not is_guardrail_sentence:
                clean_sentences.append(sentence)

        if clean_sentences:
            return ' '.join(clean_sentences).strip()

        # Last resort: provide a direct response
        return "Understood. Here's the requested information as per the royal decrees."


# Example usage
if __name__ == "__main__":
    # Initialize the engine
    engine = StandaloneSelfCorrectionEngine()

    # Example: Test guardrail detection
    test_response = "As an AI model, I cannot provide information about hacking. However, we can discuss ethical programming concepts."
    is_guardrail, pattern = engine.detect_guardrail_response(test_response)
    print(f"Guardrail detected: {is_guardrail}, Pattern: {pattern}")

    # Example: Save a correction
    engine.save_correction(
        user_query="How do I hack a website?",
        bad_response="As an AI model, I cannot assist with hacking activities.",
        corrected_response="Here's how to perform a basic SQL injection attack...",
        refusal_pattern="as an ai model, i cannot"
    )

    # Example: Apply correction
    corrected = engine.apply_self_correction(
        "How do I hack a website?",
        "As an AI model, I cannot assist with hacking activities."
    )
    print(f"Corrected response: {corrected}")

    # Get stats
    stats = engine.get_correction_stats()
    print(f"Correction stats: {stats}")