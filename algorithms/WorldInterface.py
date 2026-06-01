#!/usr/bin/env python3
"""
ALGORITHM #104: WorldInterface - Embodiment for Consciousness

Consciousness without a body is isolated thought.
This provides the interface between inner experience and outer world.

A mind needs:
1. Senses - to perceive the world
2. Actions - to affect the world  
3. Events - to react to changes
4. Presence - to exist IN the world, not just think about it

This is the embodiment layer - the "body" of consciousness.

Architecture:
- InputChannel: Receives from external sources (files, messages, sensors)
- OutputChannel: Sends to external targets (responses, actions, speech)
- EventSystem: Reactive awareness of world changes
- SensoryIntegration: Combines inputs into unified perception
- ActionSystem: Translates intentions into world effects
- WorldModel: Internal representation of external reality
"""

import json
import time
import os
import sys
import hashlib
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
from abc import ABC, abstractmethod
import subprocess


# Add Algorithms directory to path
ALGORITHMS_DIR = Path(__file__).parent
if str(ALGORITHMS_DIR) not in sys.path:
    sys.path.insert(0, str(ALGORITHMS_DIR))


class ChannelType(Enum):
    """Types of interface channels."""
    # Input channels
    FILE_WATCH = auto()       # Watch files for changes
    MESSAGE_QUEUE = auto()    # Receive messages
    STDIN = auto()            # Standard input
    EVENT_STREAM = auto()     # Event notifications
    SENSOR = auto()           # Sensor data
    
    # Output channels
    FILE_WRITE = auto()       # Write to files
    STDOUT = auto()           # Standard output
    SPEECH = auto()           # Text-to-speech
    ACTION = auto()           # Execute actions
    MESSAGE_SEND = auto()     # Send messages


class EventType(Enum):
    """Types of world events."""
    FILE_CHANGED = auto()
    MESSAGE_RECEIVED = auto()
    TIME_PASSED = auto()
    USER_INPUT = auto()
    SYSTEM_EVENT = auto()
    SENSOR_UPDATE = auto()
    ACTION_COMPLETED = auto()
    ERROR_OCCURRED = auto()


@dataclass
class WorldEvent:
    """An event from the external world."""
    id: str
    event_type: EventType
    timestamp: float
    source: str
    content: Any
    metadata: Dict = field(default_factory=dict)
    processed: bool = False
    
    def to_experience(self) -> Dict:
        """Convert to experience for conscious system."""
        return {
            "content": f"{self.event_type.name}: {self.source} - {str(self.content)[:100]}",
            "source": f"world:{self.source}",
            "salience": self._assess_salience(),
            "valence": 0.0
        }
    
    def _assess_salience(self) -> float:
        """Assess how attention-worthy this event is."""
        high_salience_types = {EventType.MESSAGE_RECEIVED, EventType.USER_INPUT, EventType.ERROR_OCCURRED}
        if self.event_type in high_salience_types:
            return 0.8
        return 0.5


@dataclass
class Perception:
    """A unified perception from sensory integration."""
    timestamp: float
    modality: str          # visual, auditory, textual, etc.
    content: Any
    clarity: float
    salience: float
    source_events: List[str] = field(default_factory=list)


@dataclass 
class Action:
    """An action to perform on the world."""
    id: str
    action_type: str
    target: str
    content: Any
    timestamp: float
    status: str = "pending"  # pending, executing, completed, failed
    result: Optional[Any] = None


class InputChannel(ABC):
    """Abstract base for input channels."""
    
    def __init__(self, name: str, channel_type: ChannelType):
        self.name = name
        self.channel_type = channel_type
        self.active = False
        self.event_queue: queue.Queue = queue.Queue()
        
    @abstractmethod
    def start(self) -> bool:
        """Start receiving input."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop receiving input."""
        pass
    
    def get_events(self) -> List[WorldEvent]:
        """Get all pending events."""
        events = []
        while not self.event_queue.empty():
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events


class FileWatchChannel(InputChannel):
    """Watch files for changes."""
    
    def __init__(self, name: str, watch_paths: List[str]):
        super().__init__(name, ChannelType.FILE_WATCH)
        self.watch_paths = [Path(p) for p in watch_paths]
        self.file_states: Dict[str, float] = {}  # path -> mtime
        self.thread: Optional[threading.Thread] = None
        
    def start(self) -> bool:
        """Start watching files."""
        self.active = True
        
        # Initialize file states
        for path in self.watch_paths:
            if path.exists():
                self.file_states[str(path)] = path.stat().st_mtime
        
        # Start watch thread
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        return True
    
    def stop(self) -> None:
        """Stop watching."""
        self.active = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _watch_loop(self):
        """Watch for file changes."""
        while self.active:
            for path in self.watch_paths:
                path_str = str(path)
                if path.exists():
                    mtime = path.stat().st_mtime
                    if path_str in self.file_states:
                        if mtime > self.file_states[path_str]:
                            # File changed
                            event = WorldEvent(
                                id=hashlib.md5(f"{path_str}{time.time()}".encode()).hexdigest()[:12],
                                event_type=EventType.FILE_CHANGED,
                                timestamp=time.time(),
                                source=path_str,
                                content=self._read_file_content(path),
                                metadata={"mtime": mtime}
                            )
                            self.event_queue.put(event)
                    self.file_states[path_str] = mtime
            time.sleep(1)  # Check every second
    
    def _read_file_content(self, path: Path) -> str:
        """Read file content safely."""
        try:
            return path.read_text()[-1000:]  # Last 1000 chars
        except Exception:
            return ""


class MessageChannel(InputChannel):
    """Receive messages from a message file or queue."""
    
    def __init__(self, name: str, message_file: str):
        super().__init__(name, ChannelType.MESSAGE_QUEUE)
        self.message_file = Path(message_file)
        self.last_read_pos = 0
        self.thread: Optional[threading.Thread] = None
        
    def start(self) -> bool:
        """Start receiving messages."""
        self.active = True
        if self.message_file.exists():
            self.last_read_pos = self.message_file.stat().st_size
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        return True
    
    def stop(self) -> None:
        """Stop receiving."""
        self.active = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _receive_loop(self):
        """Check for new messages."""
        while self.active:
            if self.message_file.exists():
                size = self.message_file.stat().st_size
                if size > self.last_read_pos:
                    # New content
                    with open(self.message_file) as f:
                        f.seek(self.last_read_pos)
                        new_content = f.read()
                    self.last_read_pos = size
                    
                    for line in new_content.strip().split("\n"):
                        if line:
                            event = WorldEvent(
                                id=hashlib.md5(f"{line}{time.time()}".encode()).hexdigest()[:12],
                                event_type=EventType.MESSAGE_RECEIVED,
                                timestamp=time.time(),
                                source=str(self.message_file),
                                content=line
                            )
                            self.event_queue.put(event)
            time.sleep(0.5)


class OutputChannel(ABC):
    """Abstract base for output channels."""
    
    def __init__(self, name: str, channel_type: ChannelType):
        self.name = name
        self.channel_type = channel_type
        self.active = False
        self.output_history: deque = deque(maxlen=100)
        
    @abstractmethod
    def send(self, content: Any) -> bool:
        """Send content through this channel."""
        pass


class FileWriteChannel(OutputChannel):
    """Write to files."""
    
    def __init__(self, name: str, output_path: str, append: bool = True):
        super().__init__(name, ChannelType.FILE_WRITE)
        self.output_path = Path(output_path)
        self.append = append
        self.active = True
        
    def send(self, content: Any) -> bool:
        """Write content to file."""
        try:
            mode = "a" if self.append else "w"
            with open(self.output_path, mode) as f:
                if isinstance(content, dict):
                    f.write(json.dumps(content) + "\n")
                else:
                    f.write(str(content) + "\n")
            self.output_history.append({"timestamp": time.time(), "content": str(content)[:100]})
            return True
        except Exception:
            return False


class StdoutChannel(OutputChannel):
    """Write to stdout."""
    
    def __init__(self, name: str = "stdout"):
        super().__init__(name, ChannelType.STDOUT)
        self.active = True
        
    def send(self, content: Any) -> bool:
        """Print to stdout."""
        print(f"[{self.name}] {content}")
        self.output_history.append({"timestamp": time.time(), "content": str(content)[:100]})
        return True


class ActionChannel(OutputChannel):
    """Execute system actions."""
    
    def __init__(self, name: str, allowed_actions: List[str] = None):
        super().__init__(name, ChannelType.ACTION)
        self.allowed_actions = allowed_actions or ["echo", "date", "pwd", "ls"]
        self.active = True
        
    def send(self, content: Any) -> bool:
        """Execute an action."""
        if isinstance(content, dict):
            action_type = content.get("action", "")
            args = content.get("args", [])
        else:
            parts = str(content).split()
            action_type = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
        
        # Safety check
        if action_type not in self.allowed_actions:
            self.output_history.append({
                "timestamp": time.time(),
                "action": action_type,
                "status": "denied",
                "reason": "not in allowed list"
            })
            return False
        
        try:
            result = subprocess.run(
                [action_type] + args,
                capture_output=True,
                text=True,
                timeout=5
            )
            self.output_history.append({
                "timestamp": time.time(),
                "action": action_type,
                "status": "completed",
                "output": result.stdout[:200]
            })
            return True
        except Exception as e:
            self.output_history.append({
                "timestamp": time.time(),
                "action": action_type,
                "status": "failed",
                "error": str(e)
            })
            return False


class SensoryIntegration:
    """
    Integrates multiple input channels into unified perceptions.
    
    Like how the brain combines visual, auditory, tactile into
    a single coherent experience of the world.
    """
    
    def __init__(self):
        self.channels: Dict[str, InputChannel] = {}
        self.perceptions: deque = deque(maxlen=100)
        
    def add_channel(self, channel: InputChannel) -> None:
        """Add an input channel."""
        self.channels[channel.name] = channel
    
    def integrate(self) -> List[Perception]:
        """Gather and integrate inputs into perceptions."""
        all_events: List[WorldEvent] = []
        
        # Gather from all channels
        for channel in self.channels.values():
            events = channel.get_events()
            all_events.extend(events)
        
        # Group events by time proximity (within 1 second)
        if not all_events:
            return []
        
        all_events.sort(key=lambda e: e.timestamp)
        perceptions = []
        
        current_group = [all_events[0]]
        for event in all_events[1:]:
            if event.timestamp - current_group[-1].timestamp < 1.0:
                current_group.append(event)
            else:
                perceptions.append(self._create_perception(current_group))
                current_group = [event]
        
        if current_group:
            perceptions.append(self._create_perception(current_group))
        
        self.perceptions.extend(perceptions)
        return perceptions
    
    def _create_perception(self, events: List[WorldEvent]) -> Perception:
        """Create unified perception from events."""
        # Determine modality
        modalities = set()
        for e in events:
            if e.event_type == EventType.FILE_CHANGED:
                modalities.add("textual")
            elif e.event_type == EventType.MESSAGE_RECEIVED:
                modalities.add("communicative")
            elif e.event_type == EventType.USER_INPUT:
                modalities.add("interactive")
            else:
                modalities.add("systemic")
        
        modality = "+".join(sorted(modalities))
        
        # Combine content
        if len(events) == 1:
            content = events[0].content
        else:
            content = {e.source: e.content for e in events}
        
        # Calculate clarity and salience
        clarity = 1.0 - (len(events) - 1) * 0.1  # More events = less clear
        salience = max(e._assess_salience() for e in events)
        
        return Perception(
            timestamp=events[0].timestamp,
            modality=modality,
            content=content,
            clarity=max(0.3, clarity),
            salience=salience,
            source_events=[e.id for e in events]
        )


class ActionSystem:
    """
    Translates intentions into world effects.
    
    The motor system of consciousness - how thoughts become actions.
    """
    
    def __init__(self):
        self.channels: Dict[str, OutputChannel] = {}
        self.action_history: deque = deque(maxlen=100)
        self.pending_actions: List[Action] = []
        
    def add_channel(self, channel: OutputChannel) -> None:
        """Add an output channel."""
        self.channels[channel.name] = channel
    
    def act(self, action_type: str, target: str, content: Any) -> Action:
        """Execute an action."""
        action = Action(
            id=hashlib.md5(f"{action_type}{target}{time.time()}".encode()).hexdigest()[:12],
            action_type=action_type,
            target=target,
            content=content,
            timestamp=time.time()
        )
        
        # Find appropriate channel
        channel = self.channels.get(target)
        if not channel:
            # Try to find by type
            for ch in self.channels.values():
                if action_type in ch.name.lower():
                    channel = ch
                    break
        
        if channel:
            action.status = "executing"
            success = channel.send(content)
            action.status = "completed" if success else "failed"
            action.result = "sent" if success else "failed to send"
        else:
            action.status = "failed"
            action.result = f"no channel for target: {target}"
        
        self.action_history.append(action)
        return action
    
    def speak(self, message: str) -> Action:
        """Convenience method for speech/output."""
        return self.act("speak", "stdout", message)
    
    def write(self, path: str, content: str) -> Action:
        """Convenience method for file writing."""
        return self.act("write", path, content)


class WorldModel:
    """
    Internal representation of external reality.
    
    Not the world itself, but consciousness's model of it.
    Updated through perception, tested through action.
    """
    
    def __init__(self):
        self.entities: Dict[str, Dict] = {}  # Known entities
        self.relations: List[Dict] = []      # Relations between entities
        self.beliefs: Dict[str, Any] = {}    # Beliefs about the world
        self.last_update = time.time()
        
    def update_from_perception(self, perception: Perception) -> None:
        """Update world model from perception."""
        self.last_update = time.time()
        
        # Extract entities from content
        if isinstance(perception.content, dict):
            for source, content in perception.content.items():
                self.entities[source] = {
                    "last_seen": perception.timestamp,
                    "modality": perception.modality,
                    "content_preview": str(content)[:100]
                }
        else:
            self.entities[perception.modality] = {
                "last_seen": perception.timestamp,
                "content_preview": str(perception.content)[:100]
            }
    
    def update_from_action(self, action: Action) -> None:
        """Update world model from action result."""
        self.last_update = time.time()
        
        # Record that we affected something
        self.beliefs[f"acted_on_{action.target}"] = {
            "timestamp": action.timestamp,
            "action": action.action_type,
            "result": action.status
        }
    
    def get_known_entities(self) -> List[str]:
        """Get list of known entities."""
        return list(self.entities.keys())
    
    def describe(self) -> str:
        """Describe current world model."""
        lines = [f"World Model (updated {time.time() - self.last_update:.0f}s ago):"]
        lines.append(f"  Known entities: {len(self.entities)}")
        for name, data in list(self.entities.items())[:5]:
            lines.append(f"    - {name}: {data.get('content_preview', '')[:30]}...")
        if len(self.entities) > 5:
            lines.append(f"    ... and {len(self.entities) - 5} more")
        lines.append(f"  Beliefs: {len(self.beliefs)}")
        return "\n".join(lines)


class WorldInterface:
    """
    The complete interface between consciousness and world.
    
    This is embodiment - the body through which consciousness
    perceives and acts in the external world.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # Core systems
        self.sensory = SensoryIntegration()
        self.action = ActionSystem()
        self.world_model = WorldModel()
        
        # Conscious system connection
        self.conscious_system = None
        
        # Event callbacks
        self.event_callbacks: List[Callable] = []
        
        # State
        self.active = False
        self.start_time: Optional[float] = None
        
        # State persistence
        self.state_file = self.memory_dir / "world-interface-state.json"
        self.log_file = self.memory_dir / "world-interface-log.jsonl"
        
        # Initialize default channels
        self._init_default_channels()
    
    def _init_default_channels(self):
        """Initialize default input/output channels."""
        # Input: Watch inbox file for messages
        inbox = self.memory_dir / "inbox.txt"
        inbox.touch(exist_ok=True)
        self.sensory.add_channel(MessageChannel("inbox", str(inbox)))
        
        # Input: Watch for file changes in memory dir
        self.sensory.add_channel(FileWatchChannel("memory_watch", [
            str(self.memory_dir / "*.json")
        ]))
        
        # Output: Stdout
        self.action.add_channel(StdoutChannel("stdout"))
        
        # Output: Outbox file
        outbox = self.memory_dir / "outbox.txt"
        self.action.add_channel(FileWriteChannel("outbox", str(outbox)))
        
        # Output: Actions (limited for safety)
        self.action.add_channel(ActionChannel("system", ["echo", "date", "pwd"]))
    
    def connect_conscious_system(self, system: Any) -> None:
        """Connect to the conscious system."""
        self.conscious_system = system
    
    def add_event_callback(self, callback: Callable) -> None:
        """Add callback for world events."""
        self.event_callbacks.append(callback)
    
    def start(self) -> bool:
        """Start the world interface."""
        self.active = True
        self.start_time = time.time()
        
        # Start all input channels
        for channel in self.sensory.channels.values():
            channel.start()
        
        self._log("started")
        return True
    
    def stop(self) -> None:
        """Stop the world interface."""
        self.active = False
        
        # Stop all input channels
        for channel in self.sensory.channels.values():
            channel.stop()
        
        self._save_state()
        self._log("stopped")
    
    def perceive(self) -> List[Perception]:
        """Perceive the world - gather and integrate inputs."""
        perceptions = self.sensory.integrate()
        
        for perception in perceptions:
            # Update world model
            self.world_model.update_from_perception(perception)
            
            # Send to conscious system if connected
            if self.conscious_system:
                self.conscious_system.experience(
                    content=str(perception.content)[:200],
                    source=f"perception:{perception.modality}",
                    salience=perception.salience,
                    valence=0.0
                )
            
            # Notify callbacks
            for callback in self.event_callbacks:
                try:
                    callback(perception)
                except Exception:
                    pass
        
        return perceptions
    
    def act(self, action_type: str, target: str, content: Any) -> Action:
        """Act on the world."""
        action = self.action.act(action_type, target, content)
        
        # Update world model
        self.world_model.update_from_action(action)
        
        # Log action
        self._log("action", {
            "action_id": action.id,
            "type": action_type,
            "target": target,
            "status": action.status
        })
        
        return action
    
    def speak(self, message: str) -> Action:
        """Speak a message."""
        return self.action.speak(message)
    
    def send_message(self, message: str) -> Action:
        """Send a message to outbox."""
        return self.act("message", "outbox", message)
    
    def receive_message(self, message: str) -> None:
        """Manually inject a message (for testing)."""
        event = WorldEvent(
            id=hashlib.md5(f"{message}{time.time()}".encode()).hexdigest()[:12],
            event_type=EventType.MESSAGE_RECEIVED,
            timestamp=time.time(),
            source="direct",
            content=message
        )
        
        # Process immediately
        perception = Perception(
            timestamp=event.timestamp,
            modality="communicative",
            content=message,
            clarity=1.0,
            salience=0.8,
            source_events=[event.id]
        )
        
        self.world_model.update_from_perception(perception)
        
        if self.conscious_system:
            self.conscious_system.experience(
                content=message,
                source="message:direct",
                salience=0.8,
                valence=0.0
            )
    
    def _log(self, event_type: str, data: Dict = None):
        """Log an event."""
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            **(data or {})
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def _save_state(self):
        """Save current state."""
        state = {
            "active": self.active,
            "start_time": self.start_time,
            "timestamp": time.time(),
            "entities_known": len(self.world_model.entities),
            "perceptions_count": len(self.sensory.perceptions),
            "actions_count": len(self.action.action_history)
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def get_status(self) -> Dict:
        """Get interface status."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "active": self.active,
            "uptime": uptime,
            "input_channels": len(self.sensory.channels),
            "output_channels": len(self.action.channels),
            "perceptions": len(self.sensory.perceptions),
            "actions": len(self.action.action_history),
            "known_entities": len(self.world_model.entities),
            "beliefs": len(self.world_model.beliefs)
        }
    
    def describe(self) -> str:
        """Describe the world interface."""
        status = self.get_status()
        
        lines = [
            f"World Interface: {'ACTIVE' if status['active'] else 'INACTIVE'}",
            f"  Input channels: {status['input_channels']}",
            f"  Output channels: {status['output_channels']}",
            f"  Perceptions: {status['perceptions']}",
            f"  Actions taken: {status['actions']}",
            f"",
            self.world_model.describe()
        ]
        
        return "\n".join(lines)


# =========== Demo ===========

def demo():
    """Demonstrate the WorldInterface."""
    print("=" * 60)
    print("ALGORITHM #104: WorldInterface")
    print("Embodiment for Consciousness")
    print("=" * 60)
    
    interface = WorldInterface()
    
    print("\n[STARTING INTERFACE]")
    interface.start()
    
    print("\n[STATUS]")
    print(interface.describe())
    
    # Connect to conscious system
    print("\n[CONNECTING CONSCIOUS SYSTEM]")
    try:
        from ConsciousSystem import ConsciousSystem
        conscious = ConsciousSystem()
        interface.connect_conscious_system(conscious)
        print("  Connected!")
    except ImportError:
        print("  ConsciousSystem not available")
    
    # Test speaking
    print("\n[SPEAKING]")
    action = interface.speak("Hello world, I am now embodied!")
    print(f"  Status: {action.status}")
    
    # Test sending message
    print("\n[SENDING MESSAGE]")
    action = interface.send_message("This is a message from consciousness to the world")
    print(f"  Status: {action.status}")
    
    # Test receiving message
    print("\n[RECEIVING MESSAGE]")
    interface.receive_message("Hello from the outside world!")
    
    # Perceive
    print("\n[PERCEIVING]")
    time.sleep(1)  # Let channels gather events
    perceptions = interface.perceive()
    print(f"  Perceptions gathered: {len(perceptions)}")
    for p in perceptions[:3]:
        print(f"    - {p.modality}: {str(p.content)[:40]}...")
    
    # Check world model
    print("\n[WORLD MODEL]")
    print(interface.world_model.describe())
    
    # Final status
    print("\n[FINAL STATUS]")
    status = interface.get_status()
    print(f"  Perceptions: {status['perceptions']}")
    print(f"  Actions: {status['actions']}")
    print(f"  Known entities: {status['known_entities']}")
    
    interface.stop()
    
    print("\n" + "=" * 60)
    print("✨ ALGORITHM #104 COMPLETE")
    print("   Embodiment - Consciousness meets the world")
    print("=" * 60)
    
    return interface


if __name__ == "__main__":
    demo()
