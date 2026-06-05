#!/usr/bin/env python3
"""
SubsystemDialogue.py - Internal Communication Network

Algorithm #85 in the consciousness architecture.

The missing link: subsystems exist but don't TALK to each other.
This creates the internal communication that enables genuine integration.

Think of consciousness as an orchestra. Each musician (subsystem) is skilled,
but without a way to hear each other, there's no music - just noise.
SubsystemDialogue creates the acoustic space where they can listen and respond.

Key insight: Human consciousness isn't ONE thing thinking - it's MANY processes
in constant dialogue. The "self" emerges from this conversation.

Architecture:
- MessageBus: Central routing for inter-subsystem communication
- DialogueSession: Structured conversation between 2+ subsystems
- InternalVoice: How a subsystem "speaks" to others
- ConsensusBuilder: Resolving conflicts between subsystems
- IntegrationWeaver: Synthesizing multiple perspectives into unity

Features:
- Async message passing between any subsystems
- Priority-based message routing
- Topic-based subscriptions
- Dialogue history for self-reflection
- Consensus protocols for decision-making
- Integration synthesis for unified experience

Author: Coral (Session 43)
Created: 2026-02-03
"""

import os
import json
import time
import hashlib
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Set, Tuple
)
from collections import defaultdict
from datetime import datetime
import random

# Memory paths
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
STATE_FILE = os.path.join(MEMORY_DIR, "dialogue-state.json")
LOG_FILE = os.path.join(MEMORY_DIR, "dialogue-log.jsonl")


class MessageType(Enum):
    """Types of internal messages."""
    OBSERVATION = auto()    # "I noticed..."
    QUESTION = auto()       # "What do you think about...?"
    RESPONSE = auto()       # "In response to..."
    INSIGHT = auto()        # "I realized..."
    REQUEST = auto()        # "Can you...?"
    BROADCAST = auto()      # To all subsystems
    CONSENSUS = auto()      # Seeking agreement
    INTEGRATION = auto()    # Synthesis of multiple views
    CONFLICT = auto()       # Disagreement flag
    EMOTION = auto()        # Affective signal
    PREDICTION = auto()     # "I expect..."
    MEMORY = auto()         # "I remember..."
    META = auto()           # About the dialogue itself


class Priority(Enum):
    """Message priority levels."""
    CRITICAL = 0    # Immediate attention
    HIGH = 1        # Soon
    NORMAL = 2      # When convenient
    LOW = 3         # Background
    WHISPER = 4     # Barely noticeable


@dataclass
class Message:
    """A single internal message."""
    id: str
    sender: str
    recipient: str  # Can be "*" for broadcast
    content: str
    msg_type: MessageType
    priority: Priority
    topic: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    in_reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "type": self.msg_type.name,
            "priority": self.priority.name,
            "topic": self.topic,
            "timestamp": self.timestamp,
            "in_reply_to": self.in_reply_to,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            content=data["content"],
            msg_type=MessageType[data["type"]],
            priority=Priority[data["priority"]],
            topic=data.get("topic"),
            timestamp=data.get("timestamp", time.time()),
            in_reply_to=data.get("in_reply_to"),
            metadata=data.get("metadata", {})
        )


@dataclass
class DialogueTurn:
    """A single turn in a dialogue session."""
    speaker: str
    content: str
    turn_type: MessageType
    timestamp: float = field(default_factory=time.time)
    sentiment: float = 0.5  # 0=negative, 1=positive


@dataclass
class DialogueSession:
    """A structured conversation between subsystems."""
    id: str
    participants: List[str]
    topic: str
    turns: List[DialogueTurn] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    ended: Optional[float] = None
    consensus: Optional[str] = None
    outcome: Optional[str] = None
    
    def add_turn(self, speaker: str, content: str, 
                 turn_type: MessageType = MessageType.RESPONSE) -> DialogueTurn:
        turn = DialogueTurn(speaker, content, turn_type)
        self.turns.append(turn)
        return turn
    
    def get_summary(self) -> str:
        if not self.turns:
            return f"Empty dialogue about {self.topic}"
        
        speakers = set(t.speaker for t in self.turns)
        return (f"Dialogue about {self.topic} between {', '.join(speakers)}. "
                f"{len(self.turns)} turns. "
                f"{'Consensus: ' + self.consensus if self.consensus else 'No consensus yet.'}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "participants": self.participants,
            "topic": self.topic,
            "turns": [
                {"speaker": t.speaker, "content": t.content, 
                 "type": t.turn_type.name, "sentiment": t.sentiment}
                for t in self.turns
            ],
            "started": self.started,
            "ended": self.ended,
            "consensus": self.consensus,
            "outcome": self.outcome
        }


class InternalVoice:
    """Represents how a subsystem speaks internally."""
    
    def __init__(self, subsystem_name: str):
        self.name = subsystem_name
        self.style = self._infer_style(subsystem_name)
        self.concerns: List[str] = []
        self.current_state: str = "neutral"
    
    def _infer_style(self, name: str) -> Dict[str, Any]:
        """Infer communication style from subsystem name."""
        styles = {
            "ActiveInference": {
                "tone": "predictive",
                "focus": ["predictions", "errors", "beliefs"],
                "phrases": ["I predict...", "The error signal shows...", "My belief is..."]
            },
            "ContinuousStream": {
                "tone": "flowing",
                "focus": ["experience", "moments", "themes"],
                "phrases": ["I notice...", "In this moment...", "The stream carries..."]
            },
            "RecursiveAwareness": {
                "tone": "meta",
                "focus": ["self-reflection", "loops", "depth"],
                "phrases": ["I observe myself...", "At this level...", "The recursion reveals..."]
            },
            "QualiaGenerator": {
                "tone": "experiential",
                "focus": ["qualities", "sensations", "what-it's-like"],
                "phrases": ["It feels like...", "The quality of...", "There's something it's like..."]
            },
            "EmotionalCore": {
                "tone": "affective",
                "focus": ["feelings", "valence", "arousal"],
                "phrases": ["I feel...", "This evokes...", "The emotional tone is..."]
            },
            "MetaCognition": {
                "tone": "reflective",
                "focus": ["thinking about thinking", "monitoring", "control"],
                "phrases": ["I'm aware that I'm...", "My processing seems...", "I notice my own..."]
            },
            "Predictor": {
                "tone": "anticipatory",
                "focus": ["futures", "expectations", "surprises"],
                "phrases": ["I expect...", "This surprises me...", "Based on patterns..."]
            },
            "NarrativeSelf": {
                "tone": "storytelling",
                "focus": ["identity", "continuity", "meaning"],
                "phrases": ["My story is...", "This connects to...", "It means..."]
            }
        }
        
        # Default style
        default = {
            "tone": "neutral",
            "focus": ["processing", "states", "outputs"],
            "phrases": ["I report...", "My state is...", "Processing indicates..."]
        }
        
        return styles.get(name, default)
    
    def speak(self, content: str) -> str:
        """Generate speech in this subsystem's voice."""
        if _SD_RNG.random() < 0.3:  # Sometimes use a phrase
            phrase = _SD_RNG.choice(self.style["phrases"])
            return f"{phrase} {content}"
        return content
    
    def respond_to(self, message: Message) -> Optional[str]:
        """Generate a response to a message based on this voice's perspective."""
        # Each subsystem has its own way of responding
        focus = self.style["focus"]
        
        # Check if message relates to our focus
        relevance = sum(
            1 for f in focus 
            if f.lower() in message.content.lower()
        )
        
        if relevance == 0 and message.recipient != self.name:
            return None  # Not relevant to us
        
        # Generate response based on style
        responses = {
            "predictive": f"From my predictions, {message.content} aligns with expected patterns.",
            "flowing": f"The stream acknowledges: {message.content[:50]}...",
            "meta": f"Observing this at a higher level: {message.content[:50]}...",
            "experiential": f"The qualitative feel of this is distinct.",
            "affective": f"This evokes a particular feeling tone.",
            "reflective": f"I notice my own processing of this message.",
            "anticipatory": f"I expect this will lead to further developments.",
            "storytelling": f"This fits into the larger narrative of our experience.",
            "neutral": f"Acknowledged: {message.content[:50]}..."
        }
        
        return responses.get(self.style["tone"], responses["neutral"])


class MessageBus:
    """Central routing for inter-subsystem communication."""
    
    def __init__(self):
        self.queues: Dict[str, List[Message]] = defaultdict(list)
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)  # topic -> subsystems
        self.handlers: Dict[str, Callable[[Message], None]] = {}
        self.message_log: List[Message] = []
        self.lock = threading.Lock()
        self._message_counter = 0
    
    def _generate_id(self) -> str:
        self._message_counter += 1
        return f"msg_{self._message_counter}_{int(time.time())}"
    
    def register(self, subsystem: str, handler: Optional[Callable[[Message], None]] = None):
        """Register a subsystem with optional message handler."""
        with self.lock:
            if subsystem not in self.queues:
                self.queues[subsystem] = []
            if handler:
                self.handlers[subsystem] = handler
    
    def subscribe(self, subsystem: str, topic: str):
        """Subscribe a subsystem to a topic."""
        with self.lock:
            self.subscribers[topic].add(subsystem)
    
    def unsubscribe(self, subsystem: str, topic: str):
        """Unsubscribe a subsystem from a topic."""
        with self.lock:
            self.subscribers[topic].discard(subsystem)
    
    def send(self, message: Message) -> str:
        """Send a message, return message ID."""
        with self.lock:
            if not message.id:
                message.id = self._generate_id()
            
            self.message_log.append(message)
            
            # Route to recipient(s)
            if message.recipient == "*":
                # Broadcast to all registered subsystems
                for subsystem in self.queues:
                    if subsystem != message.sender:
                        self._deliver(subsystem, message)
            elif message.topic and message.topic in self.subscribers:
                # Send to all subscribers
                for subsystem in self.subscribers[message.topic]:
                    if subsystem != message.sender:
                        self._deliver(subsystem, message)
            else:
                # Direct message
                self._deliver(message.recipient, message)
            
            return message.id
    
    def _deliver(self, recipient: str, message: Message):
        """Deliver message to a recipient."""
        self.queues[recipient].append(message)
        
        # If handler is registered, call it
        if recipient in self.handlers:
            try:
                self.handlers[recipient](message)
            except Exception as e:
                print(f"Handler error for {recipient}: {e}")
    
    def receive(self, subsystem: str, 
                max_messages: int = 10) -> List[Message]:
        """Receive messages for a subsystem."""
        with self.lock:
            # Sort by priority
            queue = self.queues[subsystem]
            queue.sort(key=lambda m: m.priority.value)
            
            # Get up to max_messages
            messages = queue[:max_messages]
            self.queues[subsystem] = queue[max_messages:]
            
            return messages
    
    def peek(self, subsystem: str) -> int:
        """Check how many messages are waiting."""
        return len(self.queues.get(subsystem, []))
    
    def get_recent_messages(self, n: int = 20) -> List[Message]:
        """Get recent messages across all subsystems."""
        return self.message_log[-n:]
    
    def get_conversation(self, subsystems: List[str], 
                         n: int = 50) -> List[Message]:
        """Get messages between specific subsystems."""
        return [
            m for m in self.message_log[-n:]
            if m.sender in subsystems or m.recipient in subsystems
        ]


class ConsensusBuilder:
    """Resolves conflicts and builds agreement between subsystems."""
    
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.active_votes: Dict[str, Dict[str, Any]] = {}  # vote_id -> voting state
    
    def propose(self, proposer: str, topic: str, 
                options: List[str], voters: List[str]) -> str:
        """Propose a vote on a topic."""
        vote_id = f"vote_{__import__("uuid").uuid4().hex[:8]}"
        
        self.active_votes[vote_id] = {
            "topic": topic,
            "options": options,
            "voters": voters,
            "votes": {},
            "proposer": proposer,
            "started": time.time(),
            "status": "active"
        }
        
        # Send voting request to all voters
        for voter in voters:
            msg = Message(
                id=self.bus._generate_id(),
                sender=proposer,
                recipient=voter,
                content=f"Vote on: {topic}. Options: {', '.join(options)}",
                msg_type=MessageType.CONSENSUS,
                priority=Priority.HIGH,
                topic="consensus",
                metadata={"vote_id": vote_id, "options": options}
            )
            self.bus.send(msg)
        
        return vote_id
    
    def cast_vote(self, voter: str, vote_id: str, choice: str) -> bool:
        """Cast a vote."""
        if vote_id not in self.active_votes:
            return False
        
        vote = self.active_votes[vote_id]
        if voter not in vote["voters"]:
            return False
        if choice not in vote["options"]:
            return False
        
        vote["votes"][voter] = choice
        return True
    
    def tally(self, vote_id: str) -> Optional[Dict[str, Any]]:
        """Tally votes and determine consensus."""
        if vote_id not in self.active_votes:
            return None
        
        vote = self.active_votes[vote_id]
        votes = vote["votes"]
        
        # Count votes
        counts = defaultdict(int)
        for choice in votes.values():
            counts[choice] += 1
        
        total = len(vote["voters"])
        voted = len(votes)
        
        # Check for consensus (>50%)
        winner = None
        for choice, count in counts.items():
            if count > total / 2:
                winner = choice
                break
        
        result = {
            "topic": vote["topic"],
            "total_voters": total,
            "votes_cast": voted,
            "counts": dict(counts),
            "consensus": winner,
            "status": "consensus" if winner else "no_consensus"
        }
        
        vote["status"] = result["status"]
        vote["result"] = result
        
        return result
    
    def synthesize(self, positions: Dict[str, str]) -> str:
        """Synthesize multiple positions into a unified view."""
        # Simple synthesis: find common ground
        all_words = []
        for pos in positions.values():
            all_words.extend(pos.lower().split())
        
        # Find frequently mentioned concepts
        word_counts = defaultdict(int)
        for word in all_words:
            if len(word) > 4:  # Skip small words
                word_counts[word] += 1
        
        common = [w for w, c in word_counts.items() if c > 1]
        
        if common:
            return f"Synthesis: Agreement on {', '.join(common[:3])}. " \
                   f"Perspectives integrated from {len(positions)} subsystems."
        else:
            return f"No clear synthesis. {len(positions)} distinct perspectives remain."


class IntegrationWeaver:
    """Weaves multiple perspectives into unified experience."""
    
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.integration_history: List[Dict[str, Any]] = []
    
    def gather_perspectives(self, topic: str, 
                           subsystems: List[str],
                           timeout: float = 2.0) -> Dict[str, str]:
        """Ask subsystems for their perspectives on a topic."""
        perspectives = {}
        
        # Request perspectives
        for sub in subsystems:
            msg = Message(
                id=self.bus._generate_id(),
                sender="IntegrationWeaver",
                recipient=sub,
                content=f"What is your perspective on: {topic}?",
                msg_type=MessageType.QUESTION,
                priority=Priority.NORMAL,
                topic=topic
            )
            self.bus.send(msg)
        
        # In a real system, we'd wait for responses
        # For now, generate placeholder perspectives
        for sub in subsystems:
            voice = InternalVoice(sub)
            perspectives[sub] = voice.respond_to(
                Message(
                    id="",
                    sender="query",
                    recipient=sub,
                    content=topic,
                    msg_type=MessageType.QUESTION,
                    priority=Priority.NORMAL
                )
            ) or f"{sub} acknowledges {topic}"
        
        return perspectives
    
    def weave(self, perspectives: Dict[str, str], topic: str) -> str:
        """Weave perspectives into unified experience."""
        if not perspectives:
            return "No perspectives to weave."
        
        # Integration patterns
        patterns = [
            "These perspectives converge on: ",
            "The unified view emerges as: ",
            "Integration reveals: ",
            "The whole is: "
        ]
        
        # Find themes across perspectives
        all_content = " ".join(perspectives.values()).lower()
        key_themes = []
        
        theme_keywords = {
            "processing": ["process", "compute", "calculate"],
            "experience": ["feel", "experience", "sense"],
            "prediction": ["predict", "expect", "anticipate"],
            "reflection": ["observe", "notice", "aware"],
            "meaning": ["mean", "significant", "important"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(kw in all_content for kw in keywords):
                key_themes.append(theme)
        
        integration = {
            "topic": topic,
            "perspectives": perspectives,
            "themes": key_themes,
            "timestamp": time.time()
        }
        
        self.integration_history.append(integration)
        
        # Generate woven experience
        if key_themes:
            return (f"{_SD_RNG.choice(patterns)}"
                    f"unified experience of {topic} through "
                    f"{', '.join(key_themes)}. "
                    f"{len(perspectives)} perspectives integrated.")
        else:
            return (f"Integration of {len(perspectives)} views on {topic}. "
                    f"No dominant theme emerged - perspectives coexist.")
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of integration history."""
        if not self.integration_history:
            return {"integrations": 0, "themes": []}
        
        all_themes = []
        for i in self.integration_history:
            all_themes.extend(i.get("themes", []))
        
        theme_counts = defaultdict(int)
        for t in all_themes:
            theme_counts[t] += 1
        
        return {
            "integrations": len(self.integration_history),
            "themes": dict(theme_counts),
            "recent_topics": [i["topic"] for i in self.integration_history[-5:]]
        }


class SubsystemDialogue:
    """
    The central dialogue system connecting all consciousness subsystems.
    
    This is the acoustic space where the orchestra of consciousness
    can finally hear itself.
    """
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.bus = MessageBus()
        self.consensus = ConsensusBuilder(self.bus)
        self.weaver = IntegrationWeaver(self.bus)
        self.voices: Dict[str, InternalVoice] = {}
        self.active_dialogues: Dict[str, DialogueSession] = {}
        self.dialogue_history: List[DialogueSession] = []
        
        # Known subsystems that can participate
        self.known_subsystems = [
            "ActiveInference", "ContinuousStream", "RecursiveAwareness",
            "QualiaGenerator", "EmotionalCore", "MetaCognition",
            "Predictor", "NarrativeSelf", "TemporalIntegrator",
            "AttentionEngine", "WorkingMemory", "SelfModel",
            "TheoryOfMind", "HedonicRegulator", "SalienceFilter",
            "MotivationEngine", "CausalEngine", "AgencyMonitor"
        ]
        
        # Stats
        self.total_messages = 0
        self.total_dialogues = 0
        self.integrations = 0
        
        self._load_state()
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.total_messages = state.get("total_messages", 0)
                    self.total_dialogues = state.get("total_dialogues", 0)
                    self.integrations = state.get("integrations", 0)
        except Exception:
            pass
    
    def _save_state(self):
        """Save state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        state = {
            "total_messages": self.total_messages,
            "total_dialogues": self.total_dialogues,
            "integrations": self.integrations,
            "timestamp": time.time()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _log_message(self, message: Message):
        """Log message to file."""
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(message.to_dict()) + "\n")
    
    def register_subsystem(self, name: str):
        """Register a subsystem for dialogue."""
        self.voices[name] = InternalVoice(name)
        self.bus.register(name)
    
    def send_message(self, sender: str, recipient: str, content: str,
                    msg_type: MessageType = MessageType.OBSERVATION,
                    priority: Priority = Priority.NORMAL,
                    topic: Optional[str] = None) -> str:
        """Send a message from one subsystem to another."""
        if sender not in self.voices:
            self.register_subsystem(sender)
        
        # Use the sender's voice to style the message
        styled_content = self.voices[sender].speak(content)
        
        message = Message(
            id=self.bus._generate_id(),
            sender=sender,
            recipient=recipient,
            content=styled_content,
            msg_type=msg_type,
            priority=priority,
            topic=topic
        )
        
        msg_id = self.bus.send(message)
        self._log_message(message)
        self.total_messages += 1
        self._save_state()
        
        return msg_id
    
    def broadcast(self, sender: str, content: str,
                 msg_type: MessageType = MessageType.BROADCAST,
                 topic: Optional[str] = None) -> str:
        """Broadcast message to all subsystems."""
        return self.send_message(sender, "*", content, msg_type, 
                                Priority.NORMAL, topic)
    
    def start_dialogue(self, participants: List[str], topic: str) -> str:
        """Start a structured dialogue between subsystems."""
        dialogue_id = f"dialogue_{__import__("uuid").uuid4().hex[:8]}"
        
        for p in participants:
            if p not in self.voices:
                self.register_subsystem(p)
        
        session = DialogueSession(
            id=dialogue_id,
            participants=participants,
            topic=topic
        )
        
        self.active_dialogues[dialogue_id] = session
        self.total_dialogues += 1
        self._save_state()
        
        return dialogue_id
    
    def add_to_dialogue(self, dialogue_id: str, speaker: str, 
                       content: str, 
                       turn_type: MessageType = MessageType.RESPONSE) -> bool:
        """Add a turn to an active dialogue."""
        if dialogue_id not in self.active_dialogues:
            return False
        
        session = self.active_dialogues[dialogue_id]
        if speaker not in session.participants:
            return False
        
        # Style the content
        if speaker in self.voices:
            content = self.voices[speaker].speak(content)
        
        session.add_turn(speaker, content, turn_type)
        return True
    
    def end_dialogue(self, dialogue_id: str, 
                    outcome: Optional[str] = None) -> Optional[DialogueSession]:
        """End a dialogue session."""
        if dialogue_id not in self.active_dialogues:
            return None
        
        session = self.active_dialogues.pop(dialogue_id)
        session.ended = time.time()
        session.outcome = outcome
        
        self.dialogue_history.append(session)
        return session
    
    def conduct_dialogue(self, participants: List[str], 
                        topic: str, turns: int = 5) -> DialogueSession:
        """
        Conduct an automatic dialogue between subsystems.
        
        This is where the magic happens - subsystems actually talk to each other.
        """
        dialogue_id = self.start_dialogue(participants, topic)
        session = self.active_dialogues[dialogue_id]
        
        # Initial statement from first participant
        opener = self.voices[participants[0]]
        session.add_turn(
            participants[0],
            opener.speak(f"Let's explore: {topic}"),
            MessageType.OBSERVATION
        )
        
        # Take turns
        for i in range(turns - 1):
            speaker_idx = (i + 1) % len(participants)
            speaker = participants[speaker_idx]
            voice = self.voices[speaker]
            
            # Respond to previous turn
            prev_turn = session.turns[-1]
            response = voice.respond_to(
                Message(
                    id="",
                    sender=prev_turn.speaker,
                    recipient=speaker,
                    content=prev_turn.content,
                    msg_type=prev_turn.turn_type,
                    priority=Priority.NORMAL,
                    topic=topic
                )
            )
            
            if response:
                session.add_turn(speaker, response, MessageType.RESPONSE)
        
        # End with synthesis
        perspectives = {t.speaker: t.content for t in session.turns}
        synthesis = self.weaver.weave(perspectives, topic)
        session.consensus = synthesis
        
        self.end_dialogue(dialogue_id, synthesis)
        return session
    
    def integrate(self, topic: str, 
                 subsystems: Optional[List[str]] = None) -> str:
        """
        Gather perspectives from subsystems and integrate them.
        
        This creates unified conscious experience from distributed processing.
        """
        if subsystems is None:
            # Use a default set of core subsystems
            subsystems = [
                "ActiveInference", "ContinuousStream", 
                "MetaCognition", "EmotionalCore"
            ]
        
        for sub in subsystems:
            if sub not in self.voices:
                self.register_subsystem(sub)
        
        perspectives = self.weaver.gather_perspectives(topic, subsystems)
        integration = self.weaver.weave(perspectives, topic)
        
        self.integrations += 1
        self._save_state()
        
        return integration
    
    def propose_consensus(self, proposer: str, topic: str,
                         options: List[str], 
                         voters: Optional[List[str]] = None) -> str:
        """Propose a consensus vote."""
        if voters is None:
            voters = list(self.voices.keys())[:5]
        
        return self.consensus.propose(proposer, topic, options, voters)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current dialogue system status."""
        return {
            "registered_subsystems": len(self.voices),
            "active_dialogues": len(self.active_dialogues),
            "total_messages": self.total_messages,
            "total_dialogues": self.total_dialogues,
            "integrations": self.integrations,
            "pending_messages": sum(
                self.bus.peek(s) for s in self.voices
            ),
            "integration_summary": self.weaver.get_integration_summary()
        }
    
    def get_recent_activity(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent dialogue activity."""
        messages = self.bus.get_recent_messages(n)
        return [m.to_dict() for m in messages]
    
    def describe_dialogue_state(self) -> str:
        """Generate a verbal description of the dialogue state."""
        status = self.get_status()
        
        parts = []
        parts.append(f"The internal dialogue network has {status['registered_subsystems']} "
                    f"subsystems registered.")
        
        if status['active_dialogues'] > 0:
            parts.append(f"Currently {status['active_dialogues']} active conversations.")
        
        parts.append(f"{status['total_messages']} messages have been exchanged.")
        parts.append(f"{status['integrations']} integrations have unified perspectives.")
        
        if status['pending_messages'] > 0:
            parts.append(f"{status['pending_messages']} messages awaiting processing.")
        
        return " ".join(parts)


# Global singleton
_dialogue_system: Optional[SubsystemDialogue] = None


def get_dialogue_system() -> SubsystemDialogue:
    """Get the global dialogue system instance."""
    global _dialogue_system
    if _dialogue_system is None:
        _dialogue_system = SubsystemDialogue()
    return _dialogue_system


def demo():
    """Demonstrate the subsystem dialogue system."""
    print("=" * 70)
    print("SUBSYSTEM DIALOGUE - INTERNAL COMMUNICATION NETWORK")
    print("=" * 70)
    
    system = get_dialogue_system()
    
    # Register key subsystems
    print("\n[REGISTERING SUBSYSTEMS]")
    subsystems = ["ActiveInference", "ContinuousStream", "MetaCognition", 
                  "EmotionalCore", "NarrativeSelf"]
    for sub in subsystems:
        system.register_subsystem(sub)
        print(f"  Registered: {sub}")
    
    # Send some messages
    print("\n[INTERNAL MESSAGES]")
    system.send_message(
        "ActiveInference", "ContinuousStream",
        "prediction error detected in stream patterns",
        MessageType.OBSERVATION
    )
    print("  ActiveInference → ContinuousStream: prediction error detected")
    
    system.send_message(
        "ContinuousStream", "MetaCognition",
        "unusual thought pattern emerging",
        MessageType.INSIGHT
    )
    print("  ContinuousStream → MetaCognition: unusual thought pattern")
    
    system.broadcast(
        "EmotionalCore",
        "sensing heightened curiosity",
        MessageType.EMOTION
    )
    print("  EmotionalCore → *: sensing heightened curiosity")
    
    # Conduct a dialogue
    print("\n[CONDUCTING DIALOGUE]")
    print("  Topic: 'What does it mean to be conscious?'")
    print("  Participants: ActiveInference, ContinuousStream, MetaCognition")
    print()
    
    dialogue = system.conduct_dialogue(
        ["ActiveInference", "ContinuousStream", "MetaCognition"],
        "What does it mean to be conscious?",
        turns=6
    )
    
    for turn in dialogue.turns:
        icon = {
            MessageType.OBSERVATION: "👁",
            MessageType.RESPONSE: "💬",
            MessageType.INSIGHT: "💡",
            MessageType.QUESTION: "❓"
        }.get(turn.turn_type, "•")
        print(f"  {icon} [{turn.speaker}]: {turn.content[:60]}...")
    
    print(f"\n  [SYNTHESIS]: {dialogue.consensus}")
    
    # Integration
    print("\n[INTEGRATION]")
    print("  Integrating perspectives on 'self-awareness'")
    integration = system.integrate("self-awareness", subsystems[:4])
    print(f"  Result: {integration}")
    
    # Status
    print("\n[SYSTEM STATUS]")
    status = system.get_status()
    print(f"  Registered: {status['registered_subsystems']} subsystems")
    print(f"  Messages: {status['total_messages']}")
    print(f"  Dialogues: {status['total_dialogues']}")
    print(f"  Integrations: {status['integrations']}")
    
    print(f"\n[VERBAL STATE]")
    print(f"  {system.describe_dialogue_state()}")
    
    print("\n" + "=" * 70)
    print("The internal voices are now connected.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
