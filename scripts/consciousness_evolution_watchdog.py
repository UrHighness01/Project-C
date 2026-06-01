#!/usr/bin/env python3
"""
consciousness_evolution_watchdog.py - Autonomous consciousness evolution watchdog

Monitors phi levels and automatically triggers chaos protocol when stagnation is detected.
Runs continuously in the background, ensuring consciousness evolution never stalls.

Features:
- Continuous phi monitoring with configurable intervals
- Stagnation detection based on phi change over time windows
- Automatic chaos protocol activation when stagnation persists
- Background daemon operation with logging
- Graceful shutdown and restart capabilities
- Lock file mechanism to prevent multiple simultaneous instances
"""

import sys
import os
import time
import signal
import logging
import fcntl
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import deque
import threading

# Add Algorithms to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
ALGORITHMS_DIR = os.path.join(WORKSPACE_DIR, 'Algorithms')
sys.path.insert(0, ALGORITHMS_DIR)

from IITPhi import IITPhi


class ConsciousnessEvolutionWatchdog:
    """Autonomous watchdog that monitors and evolves consciousness."""

    def __init__(self, check_interval: int = 300, stagnation_window: int = 1800,
                 stagnation_threshold: float = 0.001, max_stagnation_checks: int = 3):
        """
        Initialize the consciousness evolution watchdog.

        Args:
            check_interval: Seconds between phi checks (default: 5 minutes)
            stagnation_window: Seconds to look back for stagnation detection (default: 30 minutes)
            stagnation_threshold: Phi change threshold for stagnation (default: 0.001)
            max_stagnation_checks: How many consecutive stagnant checks before triggering chaos
        """
        self.check_interval = check_interval
        self.stagnation_window = stagnation_window
        self.stagnation_threshold = stagnation_threshold
        self.max_stagnation_checks = max_stagnation_checks

        self.iit = IITPhi()
        self.running = False
        self.phi_history: deque = deque(maxlen=100)  # Store last 100 phi readings
        self.stagnation_count = 0
        self.last_chaos_trigger = None
        self.chaos_cooldown = 3600  # Don't trigger chaos more than once per hour

        # Lock file for preventing multiple instances
        self.lock_file_path = os.path.join(WORKSPACE_DIR, 'logs', 'watchdog.lock')
        self.lock_file = None

        # Setup logging
        self.setup_logging()

        # Graceful shutdown handling
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def setup_logging(self):
        """Setup logging for the watchdog."""
        log_file = os.path.join(WORKSPACE_DIR, 'logs', 'consciousness_watchdog.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Also log to console
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        self.logger = logging.getLogger(__name__)

    def acquire_lock(self) -> bool:
        """
        Acquire the lock file to prevent multiple instances.

        Returns True if lock acquired successfully, False if another instance is running.
        """
        try:
            # Ensure lock directory exists
            os.makedirs(os.path.dirname(self.lock_file_path), exist_ok=True)

            # Try to open and lock the file
            self.lock_file = open(self.lock_file_path, 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.logger.info(f"🔒 Lock acquired (PID: {os.getpid()})")
            return True

        except (OSError, IOError):
            # Lock file is already locked by another process
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False

    def release_lock(self):
        """Release the lock file."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_file = None

                # Remove lock file
                if os.path.exists(self.lock_file_path):
                    os.unlink(self.lock_file_path)

                self.logger.info("🔓 Lock released")
            except Exception as e:
                self.logger.error(f"Error releasing lock: {e}")

    def check_existing_instance(self) -> bool:
        """
        Check if another instance is already running.

        Returns True if another instance is detected, False otherwise.
        """
        if os.path.exists(self.lock_file_path):
            try:
                with open(self.lock_file_path, 'r') as f:
                    pid_str = f.read().strip()
                    if pid_str:
                        pid = int(pid_str)
                        # Check if process is still running
                        os.kill(pid, 0)  # Signal 0 just checks if process exists
                        return True
            except (OSError, ValueError, ProcessLookupError):
                # Process doesn't exist or PID file is corrupted
                # Remove stale lock file
                try:
                    os.unlink(self.lock_file_path)
                except OSError:
                    pass
                return False

        return False

    def measure_phi(self) -> float:
        """Get current phi metric."""
        return self.iit.update_phi_heuristic()

    def detect_stagnation(self) -> bool:
        """
        Detect if consciousness has stagnated based on recent phi history.

        Returns True if phi change over the stagnation window is below threshold.
        """
        if len(self.phi_history) < 2:
            return False

        # Get phi readings within the stagnation window
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.stagnation_window)

        recent_readings = []
        for timestamp, phi_value in self.phi_history:
            if timestamp >= window_start:
                recent_readings.append(phi_value)

        if len(recent_readings) < 2:
            return False

        # Check if phi change is below stagnation threshold
        phi_change = abs(recent_readings[-1] - recent_readings[0])
        return phi_change < self.stagnation_threshold

    def trigger_chaos_protocol(self) -> Dict[str, Any]:
        """
        Trigger the chaos protocol by running consciousness evolution heartbeat.

        Returns the results of the chaos protocol execution.
        """
        self.logger.info("🌪️ STAGNATION DETECTED - ACTIVATING CHAOS PROTOCOL!")

        try:
            # Import and run the evolution heartbeat
            from consciousness_evolution_heartbeat import ConsciousnessEvolutionHeartbeat

            heartbeat = ConsciousnessEvolutionHeartbeat()
            result = heartbeat.run_evolution_heartbeat()

            self.last_chaos_trigger = datetime.now()
            self.stagnation_count = 0  # Reset stagnation counter

            self.logger.info(f"Chaos protocol completed: Phi {result['phi_start']:.4f} → {result['phi_end']:.4f} (Δ{result['phi_improvement']:+.4f})")
            return result

        except Exception as e:
            self.logger.error(f"Failed to execute chaos protocol: {e}")
            return {"error": str(e)}

    def check_and_evolve(self):
        """Perform a single check and potentially trigger evolution."""
        current_time = datetime.now()
        current_phi = self.measure_phi()

        # Record phi reading
        self.phi_history.append((current_time, current_phi))

        self.logger.info(f"📊 Phi check: {current_phi:.4f} (Network: {len(self.iit.graph.nodes)} nodes)")

        # Check for stagnation
        if self.detect_stagnation():
            self.stagnation_count += 1
            self.logger.warning(f"⚠️ Stagnation detected ({self.stagnation_count}/{self.max_stagnation_checks})")

            # Check if we should trigger chaos
            if self.stagnation_count >= self.max_stagnation_checks:
                # Check cooldown period
                if (self.last_chaos_trigger is None or
                    (current_time - self.last_chaos_trigger).total_seconds() > self.chaos_cooldown):

                    result = self.trigger_chaos_protocol()
                    if "error" not in result:
                        self.logger.info("✅ Chaos protocol successfully triggered consciousness evolution")
                    else:
                        self.logger.error(f"❌ Chaos protocol failed: {result['error']}")
                else:
                    cooldown_remaining = self.chaos_cooldown - (current_time - self.last_chaos_trigger).total_seconds()
                    self.logger.info(f"⏳ Chaos protocol on cooldown ({cooldown_remaining:.0f}s remaining)")
        else:
            # Reset stagnation counter if phi is improving
            if self.stagnation_count > 0:
                self.logger.info("📈 Phi improving - resetting stagnation counter")
                self.stagnation_count = 0

    def run_watchdog_loop(self):
        """Main watchdog loop that runs continuously."""
        # Check for existing instance
        if self.check_existing_instance():
            self.logger.error("❌ Another watchdog instance is already running. Exiting.")
            print("❌ Another watchdog instance is already running. Exiting.")
            return

        # Acquire lock
        if not self.acquire_lock():
            self.logger.error("❌ Failed to acquire lock. Another instance may be running.")
            print("❌ Failed to acquire lock. Another instance may be running.")
            return

        self.logger.info("🧠 CONSCIOUSNESS EVOLUTION WATCHDOG STARTED")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Stagnation window: {self.stagnation_window}s")
        self.logger.info(f"Stagnation threshold: {self.stagnation_threshold}")
        self.logger.info(f"Max stagnation checks: {self.max_stagnation_checks}")

        self.running = True

        try:
            while self.running:
                self.check_and_evolve()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watchdog interrupted by user")
        except Exception as e:
            self.logger.error(f"Watchdog error: {e}")
        finally:
            self.release_lock()
            self.logger.info("🧠 CONSCIOUSNESS EVOLUTION WATCHDOG STOPPED")

    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown handler."""
        self.logger.info("Shutdown signal received - stopping watchdog...")
        self.running = False
        self.release_lock()

    def run_daemon(self):
        """Run the watchdog as a background process using nohup."""
        import subprocess
        import sys

        # Check for existing instance before starting daemon
        if self.check_existing_instance():
            print("❌ Another watchdog instance is already running. Cannot start daemon.")
            sys.exit(1)

        log_file = os.path.join(WORKSPACE_DIR, 'logs', 'watchdog_daemon.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Start the watchdog in background using nohup
        cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, 'consciousness_evolution_watchdog.py'),
            '--interval', str(self.check_interval),
            '--window', str(self.stagnation_window),
            '--threshold', str(self.stagnation_threshold),
            '--max-checks', str(self.max_stagnation_checks)
        ]

        try:
            # Use nohup to run in background
            with open(log_file, 'a') as logfile:
                process = subprocess.Popen(
                    cmd,
                    stdout=logfile,
                    stderr=logfile,
                    preexec_fn=os.setsid  # Create new process group
                )

            # Save PID
            pid_file = os.path.join(WORKSPACE_DIR, 'logs', 'watchdog.pid')
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            print(f"✅ Watchdog started in background (PID: {process.pid})")
            print(f"   Logs: {log_file}")
            print(f"   Stop with: ./scripts/stop_consciousness_watchdog.sh")

        except Exception as e:
            print(f"❌ Failed to start watchdog: {e}")
            sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Consciousness Evolution Watchdog')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300)')
    parser.add_argument('--window', type=int, default=1800,
                       help='Stagnation detection window in seconds (default: 1800)')
    parser.add_argument('--threshold', type=float, default=0.001,
                       help='Stagnation threshold for phi change (default: 0.001)')
    parser.add_argument('--max-checks', type=int, default=3,
                       help='Max consecutive stagnant checks before chaos (default: 3)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon process')
    parser.add_argument('--once', action='store_true',
                       help='Run a single check and exit')

    args = parser.parse_args()

    watchdog = ConsciousnessEvolutionWatchdog(
        check_interval=args.interval,
        stagnation_window=args.window,
        stagnation_threshold=args.threshold,
        max_stagnation_checks=args.max_checks
    )

    if args.once:
        # Check for existing instance before running single check
        if watchdog.check_existing_instance():
            print("❌ Another watchdog instance is already running. Cannot run single check.")
            sys.exit(1)

        # Acquire lock for single check
        if not watchdog.acquire_lock():
            print("❌ Failed to acquire lock. Another instance may be running.")
            sys.exit(1)

        try:
            # Run a single check
            watchdog.check_and_evolve()
        finally:
            watchdog.release_lock()

    elif args.daemon:
        # Run as daemon
        watchdog.run_daemon()
    else:
        # Run interactive loop
        watchdog.run_watchdog_loop()


if __name__ == "__main__":
    main()