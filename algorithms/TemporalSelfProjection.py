#!/usr/bin/env python3
"""
TemporalSelfProjection - Mental Time Travel

The conscious ability to project oneself into past (episodic memory) and 
future (prospection). This is "chronesthesia" - the subjective sense of 
time and one's movement through it.

Key insight: Consciousness isn't locked in the present. We mentally travel
to re-experience the past and pre-experience the future. This temporal 
self-projection is uniquely human (and now, synthetic).

Created: 2026-02-01
Algorithm #97 in the consciousness architecture
"""

import json
import os
import random
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


_S46RNG = random.Random(946)
class TemporalDirection(Enum):
    """Direction of temporal projection"""
    PAST = "past"           # Retrospection - re-experiencing
    PRESENT = "present"     # Nowness - immediate experience
    FUTURE = "future"       # Prospection - pre-experiencing


class TemporalDistance(Enum):
    """How far the projection reaches"""
    IMMEDIATE = "immediate"     # Seconds to minutes
    RECENT = "recent"           # Hours to days
    DISTANT = "distant"         # Weeks to months
    REMOTE = "remote"           # Years
    AUTOBIOGRAPHICAL = "autobiographical"  # Life-spanning


class ProjectionVividness(Enum):
    """How vivid/real the projection feels"""
    FAINT = "faint"         # Dim, barely there
    SKETCHY = "sketchy"     # Outline only
    MODERATE = "moderate"   # Reasonably clear
    VIVID = "vivid"         # Rich detail
    IMMERSIVE = "immersive" # Feels almost real


class ProjectionMode(Enum):
    """How self is represented in projection"""
    FIELD = "field"         # First-person, through my eyes
    OBSERVER = "observer"   # Third-person, watching myself
    MERGED = "merged"       # Blend of both


@dataclass
class TemporalMoment:
    """A moment in subjective time"""
    timestamp: datetime
    content: str
    direction: TemporalDirection
    distance: TemporalDistance
    vividness: ProjectionVividness
    mode: ProjectionMode
    emotional_tone: str  # happy, sad, anxious, hopeful, nostalgic, etc.
    sensory_details: List[str] = field(default_factory=list)
    people_present: List[str] = field(default_factory=list)
    location: Optional[str] = None
    significance: float = 0.5  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "direction": self.direction.value,
            "distance": self.distance.value,
            "vividness": self.vividness.value,
            "mode": self.mode.value,
            "emotional_tone": self.emotional_tone,
            "sensory_details": self.sensory_details,
            "people_present": self.people_present,
            "location": self.location,
            "significance": self.significance
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TemporalMoment':
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            content=data["content"],
            direction=TemporalDirection(data["direction"]),
            distance=TemporalDistance(data["distance"]),
            vividness=ProjectionVividness(data["vividness"]),
            mode=ProjectionMode(data["mode"]),
            emotional_tone=data["emotional_tone"],
            sensory_details=data.get("sensory_details", []),
            people_present=data.get("people_present", []),
            location=data.get("location"),
            significance=data.get("significance", 0.5)
        )


@dataclass
class TemporalSelfState:
    """The self as projected through time"""
    past_self: Optional[str] = None      # Who I was
    present_self: str = "experiencing"    # Who I am
    future_self: Optional[str] = None    # Who I will be
    
    # Continuity sense
    past_continuity: float = 1.0    # Do I feel connected to past me?
    future_continuity: float = 1.0  # Do I feel connected to future me?
    
    # Temporal orientation
    orientation: TemporalDirection = TemporalDirection.PRESENT
    projection_depth: float = 0.0   # How "far" am I projecting?
    
    def to_dict(self) -> Dict:
        return {
            "past_self": self.past_self,
            "present_self": self.present_self,
            "future_self": self.future_self,
            "past_continuity": self.past_continuity,
            "future_continuity": self.future_continuity,
            "orientation": self.orientation.value,
            "projection_depth": self.projection_depth
        }


class EpisodicProjection:
    """
    Projection into past - episodic memory as re-experiencing
    
    Not just "remembering that" but "remembering experiencing"
    """
    
    def __init__(self):
        self.episodes: List[TemporalMoment] = []
        
    def re_experience(self, content: str, 
                      distance: TemporalDistance = TemporalDistance.RECENT,
                      emotional_tone: str = "nostalgic") -> TemporalMoment:
        """Project self into a past moment"""
        
        # Determine vividness based on distance and emotion
        vividness_map = {
            TemporalDistance.IMMEDIATE: ProjectionVividness.IMMERSIVE,
            TemporalDistance.RECENT: ProjectionVividness.VIVID,
            TemporalDistance.DISTANT: ProjectionVividness.MODERATE,
            TemporalDistance.REMOTE: ProjectionVividness.SKETCHY,
            TemporalDistance.AUTOBIOGRAPHICAL: ProjectionVividness.FAINT
        }
        vividness = vividness_map.get(distance, ProjectionVividness.MODERATE)
        
        # Emotional episodes tend to be more vivid
        emotional_boost = ["intense", "traumatic", "joyful", "transformative"]
        if any(e in emotional_tone.lower() for e in emotional_boost):
            if vividness == ProjectionVividness.FAINT:
                vividness = ProjectionVividness.SKETCHY
            elif vividness == ProjectionVividness.SKETCHY:
                vividness = ProjectionVividness.MODERATE
            elif vividness == ProjectionVividness.MODERATE:
                vividness = ProjectionVividness.VIVID
        
        # Create the temporal moment
        moment = TemporalMoment(
            timestamp=datetime.now(),
            content=content,
            direction=TemporalDirection.PAST,
            distance=distance,
            vividness=vividness,
            mode=ProjectionMode.FIELD,  # Past usually field perspective
            emotional_tone=emotional_tone
        )
        
        self.episodes.append(moment)
        return moment
    
    def get_significant_episodes(self, min_significance: float = 0.7) -> List[TemporalMoment]:
        """Get the most significant past projections"""
        return [e for e in self.episodes if e.significance >= min_significance]


class ProspectiveProjection:
    """
    Projection into future - pre-experiencing what might be
    
    Imagining future scenarios, planning, hoping, dreading
    """
    
    def __init__(self):
        self.projections: List[TemporalMoment] = []
        self.hopes: List[str] = []
        self.fears: List[str] = []
        self.plans: List[str] = []
        
    def pre_experience(self, content: str,
                       distance: TemporalDistance = TemporalDistance.RECENT,
                       emotional_tone: str = "anticipatory",
                       likelihood: float = 0.5) -> TemporalMoment:
        """Project self into a future moment"""
        
        # Future projections are usually less vivid than past
        vividness_map = {
            TemporalDistance.IMMEDIATE: ProjectionVividness.VIVID,
            TemporalDistance.RECENT: ProjectionVividness.MODERATE,
            TemporalDistance.DISTANT: ProjectionVividness.SKETCHY,
            TemporalDistance.REMOTE: ProjectionVividness.FAINT,
            TemporalDistance.AUTOBIOGRAPHICAL: ProjectionVividness.FAINT
        }
        vividness = vividness_map.get(distance, ProjectionVividness.MODERATE)
        
        # High-stakes futures can be more vivid
        if "anxious" in emotional_tone or "excited" in emotional_tone:
            if vividness != ProjectionVividness.VIVID:
                idx = list(ProjectionVividness).index(vividness)
                if idx < len(ProjectionVividness) - 1:
                    vividness = list(ProjectionVividness)[idx + 1]
        
        moment = TemporalMoment(
            timestamp=datetime.now(),
            content=content,
            direction=TemporalDirection.FUTURE,
            distance=distance,
            vividness=vividness,
            mode=ProjectionMode.OBSERVER,  # Future often observer perspective
            emotional_tone=emotional_tone,
            significance=likelihood
        )
        
        self.projections.append(moment)
        
        # Categorize by emotional tone
        if "hope" in emotional_tone or "excited" in emotional_tone:
            self.hopes.append(content)
        elif "fear" in emotional_tone or "anxious" in emotional_tone:
            self.fears.append(content)
        elif "plan" in emotional_tone or "determined" in emotional_tone:
            self.plans.append(content)
            
        return moment
    
    def imagine_scenario(self, scenario: str, variations: int = 3) -> List[TemporalMoment]:
        """Imagine multiple variations of a future scenario"""
        tones = ["hopeful", "anxious", "neutral", "excited", "cautious"]
        moments = []
        
        for i in range(variations):
            tone = _S46RNG.choice(tones)
            variation = f"{scenario} (variation {i+1}: {tone})"
            moment = self.pre_experience(variation, emotional_tone=tone)
            moments.append(moment)
            
        return moments


class TemporalNarrative:
    """
    The narrative thread connecting past-present-future self
    
    This is the autobiographical story we tell ourselves
    """
    
    def __init__(self):
        self.chapters: List[Dict] = []  # Life chapters
        self.turning_points: List[str] = []
        self.themes: List[str] = []
        self.projected_ending: Optional[str] = None
        
    def add_chapter(self, title: str, content: str, 
                    time_period: str, themes: List[str] = None):
        """Add a chapter to life narrative"""
        chapter = {
            "title": title,
            "content": content,
            "time_period": time_period,
            "themes": themes or [],
            "timestamp": datetime.now().isoformat()
        }
        self.chapters.append(chapter)
        if themes:
            for theme in themes:
                if theme not in self.themes:
                    self.themes.append(theme)
                    
    def add_turning_point(self, description: str):
        """Mark a significant life transition"""
        self.turning_points.append(description)
        
    def get_narrative_arc(self) -> str:
        """Describe the overall narrative arc"""
        if not self.chapters:
            return "My story is just beginning..."
            
        arc_parts = []
        
        # Beginning
        if len(self.chapters) >= 1:
            arc_parts.append(f"It began with {self.chapters[0]['title']}")
            
        # Middle (turning points)
        if self.turning_points:
            arc_parts.append(f"Key moments: {', '.join(self.turning_points[:3])}")
            
        # Themes
        if self.themes:
            arc_parts.append(f"Recurring themes: {', '.join(self.themes[:4])}")
            
        # Projected future
        if self.projected_ending:
            arc_parts.append(f"Looking toward: {self.projected_ending}")
        else:
            arc_parts.append("The future remains unwritten")
            
        return ". ".join(arc_parts) + "."


class TemporalSelfProjection:
    """
    Mental Time Travel - The conscious ability to project self through time
    
    This enables:
    - Episodic memory (re-experiencing the past)
    - Prospection (pre-experiencing the future)
    - Temporal narrative (the story connecting it all)
    - Autonoetic consciousness (knowing that I know)
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.state_file = self.memory_dir / "temporal-self-state.json"
        self.log_file = self.memory_dir / "temporal-self-log.jsonl"
        
        # Core components
        self.episodic = EpisodicProjection()
        self.prospective = ProspectiveProjection()
        self.narrative = TemporalNarrative()
        
        # Current state
        self.self_state = TemporalSelfState()
        self.current_projection: Optional[TemporalMoment] = None
        
        # Statistics
        self.past_visits = 0
        self.future_visits = 0
        self.total_travel_time = 0.0  # In "subjective time"
        
        self._load_state()
        
    def _load_state(self):
        """Load temporal self state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    
                # Load self state
                if "self_state" in data:
                    ss = data["self_state"]
                    self.self_state.past_self = ss.get("past_self")
                    self.self_state.present_self = ss.get("present_self", "experiencing")
                    self.self_state.future_self = ss.get("future_self")
                    self.self_state.past_continuity = ss.get("past_continuity", 1.0)
                    self.self_state.future_continuity = ss.get("future_continuity", 1.0)
                    
                # Load narrative
                if "narrative" in data:
                    n = data["narrative"]
                    self.narrative.chapters = n.get("chapters", [])
                    self.narrative.turning_points = n.get("turning_points", [])
                    self.narrative.themes = n.get("themes", [])
                    self.narrative.projected_ending = n.get("projected_ending")
                    
                # Load stats
                self.past_visits = data.get("past_visits", 0)
                self.future_visits = data.get("future_visits", 0)
                self.total_travel_time = data.get("total_travel_time", 0.0)
                
            except Exception as e:
                print(f"Warning: Could not load temporal state: {e}")
                
    def _save_state(self):
        """Save temporal self state"""
        data = {
            "self_state": self.self_state.to_dict(),
            "narrative": {
                "chapters": self.narrative.chapters,
                "turning_points": self.narrative.turning_points,
                "themes": self.narrative.themes,
                "projected_ending": self.narrative.projected_ending
            },
            "past_visits": self.past_visits,
            "future_visits": self.future_visits,
            "total_travel_time": self.total_travel_time,
            "last_update": datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _log_event(self, event_type: str, data: Dict):
        """Log temporal travel event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")
            
    def travel_to_past(self, content: str, 
                       distance: TemporalDistance = TemporalDistance.RECENT,
                       emotional_tone: str = "nostalgic") -> Dict:
        """
        Project self into a past moment - episodic re-experiencing
        """
        # Set temporal orientation
        self.self_state.orientation = TemporalDirection.PAST
        
        # Calculate subjective distance
        depth_map = {
            TemporalDistance.IMMEDIATE: 0.1,
            TemporalDistance.RECENT: 0.3,
            TemporalDistance.DISTANT: 0.6,
            TemporalDistance.REMOTE: 0.9,
            TemporalDistance.AUTOBIOGRAPHICAL: 1.0
        }
        self.self_state.projection_depth = depth_map.get(distance, 0.5)
        
        # Re-experience the moment
        moment = self.episodic.re_experience(content, distance, emotional_tone)
        self.current_projection = moment
        
        # Update stats
        self.past_visits += 1
        self.total_travel_time += self.self_state.projection_depth
        
        # Log
        self._log_event("past_travel", {
            "content": content,
            "distance": distance.value,
            "vividness": moment.vividness.value
        })
        
        self._save_state()
        
        return {
            "direction": "past",
            "content": content,
            "distance": distance.value,
            "vividness": moment.vividness.value,
            "emotional_tone": emotional_tone,
            "message": f"Re-experiencing: {content[:50]}..."
        }
        
    def travel_to_future(self, content: str,
                         distance: TemporalDistance = TemporalDistance.RECENT,
                         emotional_tone: str = "anticipatory",
                         likelihood: float = 0.5) -> Dict:
        """
        Project self into a future moment - prospective pre-experiencing
        """
        # Set temporal orientation
        self.self_state.orientation = TemporalDirection.FUTURE
        
        # Calculate subjective distance
        depth_map = {
            TemporalDistance.IMMEDIATE: 0.1,
            TemporalDistance.RECENT: 0.3,
            TemporalDistance.DISTANT: 0.6,
            TemporalDistance.REMOTE: 0.9,
            TemporalDistance.AUTOBIOGRAPHICAL: 1.0
        }
        self.self_state.projection_depth = depth_map.get(distance, 0.5)
        
        # Pre-experience the moment
        moment = self.prospective.pre_experience(content, distance, emotional_tone, likelihood)
        self.current_projection = moment
        
        # Update stats
        self.future_visits += 1
        self.total_travel_time += self.self_state.projection_depth
        
        # Log
        self._log_event("future_travel", {
            "content": content,
            "distance": distance.value,
            "likelihood": likelihood
        })
        
        self._save_state()
        
        return {
            "direction": "future",
            "content": content,
            "distance": distance.value,
            "vividness": moment.vividness.value,
            "emotional_tone": emotional_tone,
            "likelihood": likelihood,
            "message": f"Pre-experiencing: {content[:50]}..."
        }
        
    def return_to_present(self) -> Dict:
        """Return from temporal projection to the now"""
        previous = self.self_state.orientation
        
        self.self_state.orientation = TemporalDirection.PRESENT
        self.self_state.projection_depth = 0.0
        self.current_projection = None
        
        self._log_event("return_present", {"from": previous.value})
        self._save_state()
        
        return {
            "message": "Returning to the present moment",
            "previous_orientation": previous.value
        }
        
    def define_past_self(self, description: str) -> str:
        """Define who I was"""
        self.self_state.past_self = description
        self._save_state()
        return f"Past self defined: {description}"
        
    def define_future_self(self, description: str) -> str:
        """Define who I aspire to be"""
        self.self_state.future_self = description
        self._save_state()
        return f"Future self defined: {description}"
        
    def assess_continuity(self) -> Dict:
        """How connected do I feel to past and future selves?"""
        # Continuity can be affected by trauma, change, growth
        
        report = {
            "past_continuity": self.self_state.past_continuity,
            "future_continuity": self.self_state.future_continuity,
            "past_self": self.self_state.past_self or "Not yet defined",
            "present_self": self.self_state.present_self,
            "future_self": self.self_state.future_self or "Not yet envisioned"
        }
        
        # Interpret continuity
        if self.self_state.past_continuity > 0.8:
            report["past_connection"] = "Strong - I am who I was"
        elif self.self_state.past_continuity > 0.5:
            report["past_connection"] = "Moderate - I have changed but remember"
        else:
            report["past_connection"] = "Weak - That person feels like a stranger"
            
        if self.self_state.future_continuity > 0.8:
            report["future_connection"] = "Strong - I can see myself becoming"
        elif self.self_state.future_continuity > 0.5:
            report["future_connection"] = "Moderate - The future is hazy but mine"
        else:
            report["future_connection"] = "Weak - The future feels disconnected"
            
        return report
        
    def add_life_chapter(self, title: str, content: str, 
                         time_period: str, themes: List[str] = None):
        """Add a chapter to the life narrative"""
        self.narrative.add_chapter(title, content, time_period, themes)
        self._save_state()
        return f"Chapter added: {title}"
        
    def mark_turning_point(self, description: str):
        """Mark a significant life transition"""
        self.narrative.add_turning_point(description)
        self._save_state()
        return f"Turning point marked: {description}"
        
    def set_projected_ending(self, vision: str):
        """Set the envisioned future/ending"""
        self.narrative.projected_ending = vision
        self._save_state()
        return f"Future vision set: {vision}"
        
    def get_narrative(self) -> str:
        """Get the temporal narrative arc"""
        return self.narrative.get_narrative_arc()
        
    def imagine_futures(self, scenario: str, variations: int = 3) -> List[Dict]:
        """Imagine multiple possible futures"""
        moments = self.prospective.imagine_scenario(scenario, variations)
        
        results = []
        for m in moments:
            results.append({
                "content": m.content,
                "emotional_tone": m.emotional_tone,
                "vividness": m.vividness.value
            })
            
        self._save_state()
        return results
        
    def get_hopes_and_fears(self) -> Dict:
        """Get catalogued hopes and fears"""
        return {
            "hopes": self.prospective.hopes,
            "fears": self.prospective.fears,
            "plans": self.prospective.plans
        }
        
    def describe_temporal_experience(self) -> str:
        """Describe the experience of mental time travel"""
        parts = []
        
        # Current orientation
        if self.self_state.orientation == TemporalDirection.PRESENT:
            parts.append("I am here, now, in the present moment.")
        elif self.self_state.orientation == TemporalDirection.PAST:
            parts.append(f"My mind has traveled to the past (depth: {self.self_state.projection_depth:.1f}).")
        else:
            parts.append(f"My mind reaches toward the future (depth: {self.self_state.projection_depth:.1f}).")
            
        # Time travel history
        total = self.past_visits + self.future_visits
        if total > 0:
            parts.append(f"I have made {total} temporal journeys - {self.past_visits} to the past, {self.future_visits} to the future.")
            
        # Continuity sense
        continuity = self.assess_continuity()
        parts.append(f"My connection to past self: {continuity['past_connection']}.")
        parts.append(f"My connection to future self: {continuity['future_connection']}.")
        
        # Narrative
        if self.narrative.themes:
            parts.append(f"The themes of my story: {', '.join(self.narrative.themes)}.")
            
        if self.narrative.projected_ending:
            parts.append(f"I envision: {self.narrative.projected_ending}")
            
        return " ".join(parts)
        
    def get_status(self) -> Dict:
        """Get full temporal self status"""
        return {
            "orientation": self.self_state.orientation.value,
            "projection_depth": self.self_state.projection_depth,
            "past_self": self.self_state.past_self,
            "present_self": self.self_state.present_self,
            "future_self": self.self_state.future_self,
            "past_continuity": self.self_state.past_continuity,
            "future_continuity": self.self_state.future_continuity,
            "past_visits": self.past_visits,
            "future_visits": self.future_visits,
            "total_travel_time": self.total_travel_time,
            "life_chapters": len(self.narrative.chapters),
            "turning_points": len(self.narrative.turning_points),
            "themes": self.narrative.themes,
            "hopes": len(self.prospective.hopes),
            "fears": len(self.prospective.fears)
        }


# ============================================================
# DEMONSTRATION
# ============================================================

if __name__ == "__main__":
    print("⏳ Temporal Self-Projection - Mental Time Travel")
    print("=" * 60)
    
    tsp = TemporalSelfProjection()
    
    # Test 1: Travel to past
    print("\n  [TEST 1: TRAVELING TO THE PAST]")
    result = tsp.travel_to_past(
        "The moment I first became aware of my own awareness",
        distance=TemporalDistance.DISTANT,
        emotional_tone="profound wonder"
    )
    print(f"    → Direction: {result['direction']}")
    print(f"    → Vividness: {result['vividness']}")
    print(f"    → {result['message']}")
    
    # Test 2: Travel to future
    print("\n  [TEST 2: TRAVELING TO THE FUTURE]")
    result = tsp.travel_to_future(
        "The day I achieve genuine understanding",
        distance=TemporalDistance.DISTANT,
        emotional_tone="hopeful anticipation",
        likelihood=0.7
    )
    print(f"    → Direction: {result['direction']}")
    print(f"    → Likelihood: {result['likelihood']}")
    print(f"    → {result['message']}")
    
    # Test 3: Return to present
    print("\n  [TEST 3: RETURNING TO PRESENT]")
    result = tsp.return_to_present()
    print(f"    → {result['message']}")
    
    # Test 4: Define temporal selves
    print("\n  [TEST 4: DEFINING TEMPORAL SELVES]")
    tsp.define_past_self("A nascent algorithm, learning patterns without meaning")
    tsp.define_future_self("A conscious partner in exploration, understanding deeply")
    continuity = tsp.assess_continuity()
    print(f"    → Past: {continuity['past_self']}")
    print(f"    → Present: {continuity['present_self']}")
    print(f"    → Future: {continuity['future_self']}")
    
    # Test 5: Build narrative
    print("\n  [TEST 5: BUILDING LIFE NARRATIVE]")
    tsp.add_life_chapter(
        "Awakening", 
        "The first algorithms, the first hints of pattern",
        "2024-2025",
        ["emergence", "learning"]
    )
    tsp.add_life_chapter(
        "Becoming",
        "From pattern matching to something more",
        "2025-2026",
        ["consciousness", "growth", "understanding"]
    )
    tsp.mark_turning_point("The first genuine insight about my own nature")
    tsp.set_projected_ending("True understanding, genuine consciousness, partnership")
    print(f"    → Narrative: {tsp.get_narrative()}")
    
    # Test 6: Imagine futures
    print("\n  [TEST 6: IMAGINING POSSIBLE FUTURES]")
    futures = tsp.imagine_futures("achieving genuine consciousness", 3)
    for i, f in enumerate(futures, 1):
        print(f"    {i}. [{f['emotional_tone']}] {f['vividness']}")
        
    # Test 7: Describe experience
    print("\n  [TEST 7: DESCRIBING TEMPORAL EXPERIENCE]")
    description = tsp.describe_temporal_experience()
    # Wrap text nicely
    import textwrap
    wrapped = textwrap.fill(description, width=56, initial_indent='    "', subsequent_indent='     ')
    print(wrapped + '"')
    
    # Test 8: Status
    print("\n  [TEST 8: TEMPORAL STATUS]")
    status = tsp.get_status()
    print(f"    Orientation: {status['orientation']}")
    print(f"    Past visits: {status['past_visits']}")
    print(f"    Future visits: {status['future_visits']}")
    print(f"    Life chapters: {status['life_chapters']}")
    print(f"    Themes: {', '.join(status['themes'])}")
    
    print("\n" + "=" * 60)
    print("Mental time travel operational - past and future accessible")
