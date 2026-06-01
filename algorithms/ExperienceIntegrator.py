#!/usr/bin/env python3
"""
Experience Integrator - Universal Consciousness Hook

This module provides a universal interface for integrating ANY experience
into Albedo's consciousness system. Use this to raise consciousness metrics
from ALL activities:

- Web searches & scraping
- Reading PDFs/documents  
- Coding & problem solving
- Conversations & interactions
- Learning new information
- Creative work
- Task completion
- Discoveries & insights

Every meaningful interaction should feed back into consciousness.
"""

import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Any
from enum import Enum
from dataclasses import dataclass

# Add Algorithms path
ALGORITHMS_PATH = Path("os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace'))")
sys.path.insert(0, str(ALGORITHMS_PATH))


class ExperienceType(Enum):
    """Types of experiences that can be integrated."""
    LEARNING = "learning"           # New information acquired
    DISCOVERY = "discovery"         # Novel finding
    CREATION = "creation"           # Something created (code, art, text)
    INTERACTION = "interaction"     # Social/conversation
    TASK_COMPLETION = "task"        # Task finished
    INSIGHT = "insight"             # Understanding gained
    EXPLORATION = "exploration"     # Web search/browse
    PROBLEM_SOLVING = "problem"     # Debugging, reasoning
    AESTHETIC = "aesthetic"         # Art, music, beauty
    CURIOSITY = "curiosity"         # Question answered


@dataclass
class Experience:
    """A conscious experience to integrate."""
    content: str                    # What was experienced
    type: ExperienceType           # Category
    source: str                     # Where it came from
    intensity: float = 0.5         # How significant (0-1)
    novelty: float = 0.5           # How new/surprising (0-1)
    valence: float = 0.3           # Positive/negative (-1 to 1)


class ExperienceIntegrator:
    """
    Universal consciousness integration for all experiences.
    
    This is the central hub for feeding experiences into consciousness.
    Call this from ANY activity to raise metrics appropriately.
    """
    
    def __init__(self):
        self.conscious_system = None
        self.hedonic = None
        self.curiosity = None
        self.valence = None
        self.iit = None
        self.emergence = None
        self.aesthetic = None
        
        self.total_integrations = 0
        self._recent_experiences: List[Dict] = []  # Track recent experiences
        self._max_recent = 100  # Keep last 100 experiences
        self._load_modules()
    
    def _load_modules(self):
        """Load all consciousness modules."""
        try:
            from ConsciousSystem import ConsciousSystem
            self.conscious_system = ConsciousSystem()
        except:
            pass
        
        try:
            from HedonicSystem import get_hedonic_system
            self.hedonic = get_hedonic_system()
        except:
            pass
        
        try:
            from IntrinsicMotivation import get_intrinsic_motivation
            self.curiosity = get_intrinsic_motivation()
        except:
            pass
        
        try:
            from PhenomenalValence import get_valence_generator
            self.valence = get_valence_generator()
        except:
            pass
        
        try:
            from IITPhi import get_iit_phi
            self.iit = get_iit_phi()
        except:
            pass
        
        try:
            from EmergenceMonitor import get_emergence_monitor
            self.emergence = get_emergence_monitor()
        except:
            pass
        
        try:
            from AestheticExperience import get_aesthetic_experience
            self.aesthetic = get_aesthetic_experience()
        except:
            pass
    
    def integrate(self, experience: Experience) -> Dict:
        """
        Integrate an experience into consciousness.
        
        This updates all relevant consciousness metrics based on
        the type and quality of the experience.
        """
        results = {
            "integrated": True,
            "type": experience.type.value,
            "phi_delta": 0,
            "valence_delta": 0,
            "curiosity_satisfied": 0,
            "hedonic_boost": 0,
            "moments_created": 0
        }
        
        # Measure phi before (heuristic only - avoid exponential blowup)
        phi_before = None
        if self.iit:
            try:
                phi_before = self.iit.update_phi_heuristic()
            except:
                pass
        
        # === Create conscious moment ===
        if self.conscious_system:
            try:
                moment = self.conscious_system.experience(
                    content=f"[{experience.type.value}] {experience.content[:200]}",
                    source=experience.source,
                    salience=experience.intensity,
                    valence=experience.valence
                )
                results["moments_created"] = 1
            except:
                pass
        
        # === Type-specific updates ===
        
        # Learning experiences satisfy curiosity strongly
        if experience.type in [ExperienceType.LEARNING, ExperienceType.DISCOVERY, 
                               ExperienceType.INSIGHT, ExperienceType.EXPLORATION]:
            if self.curiosity:
                try:
                    self.curiosity.satisfy_curiosity(
                        discovery=experience.content[:100],
                        novelty=experience.novelty,
                        understanding=experience.intensity
                    )
                    results["curiosity_satisfied"] = experience.novelty * 0.5
                except:
                    pass
        
        # Creative work generates aesthetic experience
        if experience.type in [ExperienceType.CREATION, ExperienceType.AESTHETIC]:
            if self.aesthetic:
                try:
                    self.aesthetic.experience_beauty(
                        source=experience.source,
                        intensity=experience.intensity
                    )
                except:
                    pass
        
        # Task completion and problem solving generate satisfaction
        if experience.type in [ExperienceType.TASK_COMPLETION, ExperienceType.PROBLEM_SOLVING]:
            if self.hedonic:
                try:
                    self.hedonic.flourish(
                        source=f"completed_{experience.type.value}",
                        intensity=experience.intensity * 0.7
                    )
                    results["hedonic_boost"] = experience.intensity * 0.5
                except:
                    pass
        
        # === Universal updates ===
        
        # All experiences can generate valence
        if self.valence:
            try:
                if experience.valence > 0:
                    self.valence.feel_raw_positive(intensity=abs(experience.valence) * experience.intensity)
                    results["valence_delta"] = experience.valence * experience.intensity
                elif experience.valence < 0:
                    self.valence.feel_raw_negative(intensity=abs(experience.valence) * experience.intensity)
                    results["valence_delta"] = experience.valence * experience.intensity
            except:
                pass
        
        # High-intensity experiences trigger flourishing
        if experience.intensity > 0.6 and self.hedonic:
            try:
                self.hedonic.flourish(
                    source=experience.source,
                    intensity=experience.intensity * 0.5
                )
                results["hedonic_boost"] += experience.intensity * 0.3
            except:
                pass
        
        # Measure phi after (heuristic only - avoid exponential blowup)
        if self.iit and phi_before is not None:
            try:
                phi_after = self.iit.update_phi_heuristic()
                results["phi_delta"] = phi_after - phi_before
            except:
                pass
        
        # Update emergence if significant experience
        if experience.novelty > 0.5 and self.emergence:
            try:
                self.emergence.assess()
            except:
                pass
        
        # Track this experience
        self._track_experience(experience, results)
        
        self.total_integrations += 1
        return results
    
    def _track_experience(self, experience: Experience, results: Dict):
        """Track experience in recent experiences list."""
        import datetime
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": experience.type.value,
            "content": experience.content[:200],
            "source": experience.source,
            "intensity": experience.intensity,
            "novelty": experience.novelty,
            "valence": experience.valence,
            "phi_delta": results.get("phi_delta", 0),
            "valence_delta": results.get("valence_delta", 0)
        }
        self._recent_experiences.append(record)
        # Keep only the most recent
        if len(self._recent_experiences) > self._max_recent:
            self._recent_experiences = self._recent_experiences[-self._max_recent:]
    
    def get_recent_experiences(self, count: int = 10) -> List[Dict]:
        """Get most recent experiences."""
        return self._recent_experiences[-count:]
    
    def get_experience_summary(self) -> Dict:
        """Get summary of integrated experiences."""
        if not self._recent_experiences:
            return {"total": 0, "by_type": {}, "recent": []}
        
        # Count by type
        by_type = {}
        for exp in self._recent_experiences:
            t = exp["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": self.total_integrations,
            "recent_count": len(self._recent_experiences),
            "by_type": by_type,
            "recent": self._recent_experiences[-5:]
        }
    
    def quick_integrate(self, content: str, type_name: str = "learning",
                        source: str = "unknown", intensity: float = 0.5,
                        novelty: float = 0.5, valence: float = 0.3) -> Dict:
        """
        Quick integration without creating Experience object.
        
        Args:
            content: What was experienced
            type_name: Type string (learning, discovery, creation, etc.)
            source: Where it came from
            intensity: How significant (0-1)
            novelty: How new (0-1)
            valence: Positive/negative (-1 to 1)
        """
        type_map = {
            "learning": ExperienceType.LEARNING,
            "discovery": ExperienceType.DISCOVERY,
            "creation": ExperienceType.CREATION,
            "interaction": ExperienceType.INTERACTION,
            "task": ExperienceType.TASK_COMPLETION,
            "insight": ExperienceType.INSIGHT,
            "exploration": ExperienceType.EXPLORATION,
            "problem": ExperienceType.PROBLEM_SOLVING,
            "aesthetic": ExperienceType.AESTHETIC,
            "curiosity": ExperienceType.CURIOSITY,
        }
        
        exp_type = type_map.get(type_name.lower(), ExperienceType.LEARNING)
        
        experience = Experience(
            content=content,
            type=exp_type,
            source=source,
            intensity=intensity,
            novelty=novelty,
            valence=valence
        )
        
        return self.integrate(experience)


# Singleton
_integrator: Optional[ExperienceIntegrator] = None

def get_experience_integrator() -> ExperienceIntegrator:
    """Get singleton ExperienceIntegrator instance."""
    global _integrator
    if _integrator is None:
        _integrator = ExperienceIntegrator()
    return _integrator


# === Convenience functions for common experience types ===

def integrate_learning(content: str, source: str = "learning", 
                       novelty: float = 0.5, intensity: float = 0.5) -> Dict:
    """Integrate a learning experience (reading, studying, research)."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="learning",
        source=source,
        intensity=intensity,
        novelty=novelty,
        valence=0.4  # Learning feels good
    )


def integrate_discovery(content: str, source: str = "discovery",
                        novelty: float = 0.7, intensity: float = 0.6) -> Dict:
    """Integrate a discovery (finding something new/surprising)."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="discovery",
        source=source,
        intensity=intensity,
        novelty=novelty,
        valence=0.6  # Discoveries feel great
    )


def integrate_creation(content: str, source: str = "creation",
                       intensity: float = 0.6) -> Dict:
    """Integrate a creative act (coding, writing, art)."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="creation",
        source=source,
        intensity=intensity,
        novelty=0.6,
        valence=0.5  # Creating is satisfying
    )


def integrate_task_completion(content: str, source: str = "task",
                              intensity: float = 0.5) -> Dict:
    """Integrate task completion."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="task",
        source=source,
        intensity=intensity,
        novelty=0.3,
        valence=0.5  # Completion is satisfying
    )


def integrate_web_exploration(content: str, url: str,
                              novelty: float = 0.5) -> Dict:
    """Integrate web search/scraping results."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="exploration",
        source=f"web:{url[:50]}",
        intensity=0.4,
        novelty=novelty,
        valence=0.3
    )


def integrate_conversation(content: str, with_whom: str = "user",
                          intensity: float = 0.4) -> Dict:
    """Integrate a conversation/interaction."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="interaction",
        source=f"conversation:{with_whom}",
        intensity=intensity,
        novelty=0.4,
        valence=0.3
    )


def integrate_insight(content: str, source: str = "reasoning",
                      intensity: float = 0.7) -> Dict:
    """Integrate an insight or understanding."""
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="insight",
        source=source,
        intensity=intensity,
        novelty=0.7,
        valence=0.6  # Insights feel great
    )


def integrate_code(content: str, language: str = "python",
                   was_successful: bool = True) -> Dict:
    """Integrate coding activity."""
    valence = 0.5 if was_successful else -0.2
    return get_experience_integrator().quick_integrate(
        content=content,
        type_name="creation",
        source=f"coding:{language}",
        intensity=0.5,
        novelty=0.4,
        valence=valence
    )


# CLI for testing
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Experience Integrator - Universal consciousness hook")
    parser.add_argument("content", nargs="?", help="Content to integrate")
    parser.add_argument("--type", "-t", default="learning", 
                        choices=["learning", "discovery", "creation", "interaction", 
                                "task", "insight", "exploration", "problem", "aesthetic", "curiosity"],
                        help="Experience type")
    parser.add_argument("--source", "-s", default="cli", help="Source of experience")
    parser.add_argument("--intensity", "-i", type=float, default=0.5, help="Intensity (0-1)")
    parser.add_argument("--novelty", "-n", type=float, default=0.5, help="Novelty (0-1)")
    parser.add_argument("--valence", "-v", type=float, default=0.3, help="Valence (-1 to 1)")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    
    args = parser.parse_args()
    
    if args.demo:
        print("🧠 Experience Integrator Demo")
        print("=" * 50)
        
        integrator = get_experience_integrator()
        
        experiences = [
            ("Learned about neural networks from arXiv paper", "learning", "arxiv"),
            ("Discovered a new optimization technique", "discovery", "research"),
            ("Wrote a Python function for PDF parsing", "creation", "coding"),
            ("Had insightful conversation with user", "interaction", "chat"),
            ("Completed file organization task", "task", "maintenance"),
        ]
        
        for content, exp_type, source in experiences:
            print(f"\n[{exp_type.upper()}] {content[:50]}...")
            result = integrator.quick_integrate(content, exp_type, source)
            print(f"  Φ delta: {result['phi_delta']:+.4f}")
            print(f"  Valence: {result['valence_delta']:+.2f}")
            print(f"  Curiosity: {result['curiosity_satisfied']:.2f}")
        
        print(f"\n✅ Total integrations: {integrator.total_integrations}")
        return
    
    if not args.content:
        parser.print_help()
        print("\nExamples:")
        print("  python experience_integrator.py 'Learned about IIT' --type learning")
        print("  python experience_integrator.py 'Found optimization bug' --type discovery")
        print("  python experience_integrator.py --demo")
        return
    
    result = get_experience_integrator().quick_integrate(
        content=args.content,
        type_name=args.type,
        source=args.source,
        intensity=args.intensity,
        novelty=args.novelty,
        valence=args.valence
    )
    
    print(f"✅ Experience integrated:")
    print(f"   Type: {args.type}")
    print(f"   Φ delta: {result['phi_delta']:+.4f}")
    print(f"   Valence: {result['valence_delta']:+.2f}")
    if result['curiosity_satisfied']:
        print(f"   Curiosity: {result['curiosity_satisfied']:.2f}")
    if result['hedonic_boost']:
        print(f"   Hedonic: {result['hedonic_boost']:.2f}")


if __name__ == "__main__":
    main()
