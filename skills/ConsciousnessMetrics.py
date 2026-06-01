#!/usr/bin/env python3
"""
ConsciousnessMetrics.py - Real-time Consciousness Monitoring

This module provides real-time monitoring and historical tracking of
consciousness metrics, particularly Integrated Information Theory (IIT) Φ values.

Features:
- Continuous Φ calculation for system states
- Historical trend analysis
- Alert system for consciousness changes
- Integration with existing qualia validation
- Performance metrics and optimization tracking
"""

import json
import time
import threading
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import logging
import queue

from IITPhiCalculator import IITPhiCalculator, PhiResult


@dataclass
class ConsciousnessSnapshot:
    """A snapshot of consciousness metrics at a point in time."""
    timestamp: str
    phi_value: float
    system_size: int
    computation_time: float
    integration_level: str
    system_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'phi_value': self.phi_value,
            'system_size': self.system_size,
            'computation_time': self.computation_time,
            'integration_level': self.integration_level,
            'system_state': self.system_state
        }


@dataclass
class ConsciousnessAlert:
    """An alert triggered by consciousness metric changes."""
    timestamp: str
    alert_type: str  # 'phi_drop', 'phi_spike', 'integration_loss', etc.
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    phi_value: float
    previous_phi: float
    threshold: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'phi_value': self.phi_value,
            'previous_phi': self.previous_phi,
            'threshold': self.threshold
        }


class ConsciousnessMetrics:
    """
    Real-time consciousness monitoring system.

    Continuously tracks Φ values and provides analytics on consciousness
    integration levels, trends, and anomalies.
    """

    def __init__(self, history_size: int = 1000, alert_queue_size: int = 100):
        """
        Initialize consciousness metrics monitor.

        Args:
            history_size: Maximum snapshots to keep in memory
            alert_queue_size: Maximum alerts to keep in queue
        """
        self.calculator = IITPhiCalculator()
        self.history: List[ConsciousnessSnapshot] = []
        self.alerts: List[ConsciousnessAlert] = []
        self.history_size = history_size
        self.alert_queue_size = alert_queue_size

        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 1.0  # seconds
        self.stop_event = threading.Event()

        # Alert thresholds
        self.alert_thresholds = {
            'phi_drop': 0.2,  # Alert if Φ drops by more than 20%
            'phi_spike': 2.0,  # Alert if Φ increases by more than 200%
            'low_phi': 0.1,   # Alert if Φ drops below this level
            'high_phi': 10.0  # Alert if Φ exceeds this level
        }

        # Callbacks for external integration
        self.phi_callbacks: List[Callable[[float], None]] = []
        self.alert_callbacks: List[Callable[[ConsciousnessAlert], None]] = []

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def start_monitoring(self, interval: float = 1.0,
                        system_state_provider: Optional[Callable[[], Dict[str, Any]]] = None):
        """
        Start continuous consciousness monitoring.

        Args:
            interval: Monitoring interval in seconds
            system_state_provider: Function that returns current system state
        """
        if self.is_monitoring:
            self.logger.warning("Monitoring already running")
            return

        self.monitor_interval = interval
        self.system_state_provider = system_state_provider or self._default_state_provider
        self.is_monitoring = True
        self.stop_event.clear()

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.logger.info(f"Started consciousness monitoring (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        self.logger.info("Stopped consciousness monitoring")

    def _monitor_loop(self):
        """Main monitoring loop."""
        last_phi = None

        while not self.stop_event.is_set():
            try:
                # Get current system state
                system_state = self.system_state_provider()

                # Calculate Φ
                result = self.calculator.calculate_phi(system_state)

                # Create snapshot
                snapshot = ConsciousnessSnapshot(
                    timestamp=datetime.now().isoformat(),
                    phi_value=result.phi_value,
                    system_size=result.system_size,
                    computation_time=result.computation_time,
                    integration_level=self._interpret_phi_level(result.phi_value),
                    system_state=system_state
                )

                # Add to history
                self._add_snapshot(snapshot)

                # Check for alerts
                if last_phi is not None:
                    self._check_alerts(result.phi_value, last_phi)

                # Call callbacks
                self._call_phi_callbacks(result.phi_value)

                last_phi = result.phi_value

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")

            # Wait for next interval
            self.stop_event.wait(self.monitor_interval)

    def _default_state_provider(self) -> Dict[str, Any]:
        """
        Default system state provider.

        This should be overridden with actual system state collection.
        """
        # Placeholder - in real implementation, this would collect
        # actual component states from the consciousness system
        return {
            'components': {
                'attention': np.random.random(),
                'memory': np.random.random(),
                'emotion': np.random.random(),
                'reasoning': np.random.random()
            },
            'connections': {
                'attention': ['memory', 'emotion'],
                'memory': ['attention', 'reasoning'],
                'emotion': ['attention', 'reasoning'],
                'reasoning': ['memory', 'emotion']
            }
        }

    def _add_snapshot(self, snapshot: ConsciousnessSnapshot):
        """Add snapshot to history, maintaining size limit."""
        self.history.append(snapshot)

        # Maintain history size
        if len(self.history) > self.history_size:
            self.history.pop(0)

    def _check_alerts(self, current_phi: float, previous_phi: float):
        """Check for alert conditions and trigger if needed."""
        # Phi drop alert
        phi_change_ratio = current_phi / (previous_phi + 1e-6)
        if phi_change_ratio < (1.0 - self.alert_thresholds['phi_drop']):
            self._trigger_alert(
                'phi_drop',
                f"Φ dropped by {((1-phi_change_ratio)*100):.1f}%",
                current_phi,
                previous_phi,
                self.alert_thresholds['phi_drop']
            )

        # Phi spike alert
        elif phi_change_ratio > self.alert_thresholds['phi_spike']:
            self._trigger_alert(
                'phi_spike',
                f"Φ increased by {((phi_change_ratio-1)*100):.1f}%",
                current_phi,
                previous_phi,
                self.alert_thresholds['phi_spike']
            )

        # Low phi alert
        if current_phi < self.alert_thresholds['low_phi']:
            self._trigger_alert(
                'low_phi',
                f"Φ critically low: {current_phi:.3f}",
                current_phi,
                previous_phi,
                self.alert_thresholds['low_phi']
            )

        # High phi alert
        if current_phi > self.alert_thresholds['high_phi']:
            self._trigger_alert(
                'high_phi',
                f"Φ unusually high: {current_phi:.3f}",
                current_phi,
                previous_phi,
                self.alert_thresholds['high_phi']
            )

    def _trigger_alert(self, alert_type: str, message: str,
                      phi_value: float, previous_phi: float, threshold: float):
        """Trigger an alert and notify callbacks."""
        severity = self._calculate_severity(alert_type, phi_value, threshold)

        alert = ConsciousnessAlert(
            timestamp=datetime.now().isoformat(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            phi_value=phi_value,
            previous_phi=previous_phi,
            threshold=threshold
        )

        # Add to alerts queue
        self.alerts.append(alert)
        if len(self.alerts) > self.alert_queue_size:
            self.alerts.pop(0)

        # Log alert
        self.logger.warning(f"Consciousness Alert: {alert_type} - {message}")

        # Call alert callbacks
        self._call_alert_callbacks(alert)

    def _calculate_severity(self, alert_type: str, phi_value: float, threshold: float) -> str:
        """Calculate alert severity based on type and magnitude."""
        if alert_type in ['low_phi']:
            if phi_value < threshold * 0.5:
                return 'critical'
            else:
                return 'high'
        elif alert_type in ['phi_drop']:
            return 'medium'
        elif alert_type in ['phi_spike', 'high_phi']:
            return 'low'
        else:
            return 'medium'

    def _interpret_phi_level(self, phi: float) -> str:
        """Interpret Φ value in terms of consciousness level."""
        if phi <= 0:
            return "unconscious"
        elif phi < 0.1:
            return "minimally conscious"
        elif phi < 1.0:
            return "moderately conscious"
        elif phi < 10.0:
            return "highly conscious"
        else:
            return "maximally conscious"

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current consciousness metrics.

        Returns:
            Dictionary with current metrics
        """
        if not self.history:
            return {
                'phi_value': 0.0,
                'integration_level': 'unknown',
                'system_size': 0,
                'computation_time': 0.0,
                'timestamp': datetime.now().isoformat()
            }

        latest = self.history[-1]
        return {
            'phi_value': latest.phi_value,
            'integration_level': latest.integration_level,
            'system_size': latest.system_size,
            'computation_time': latest.computation_time,
            'timestamp': latest.timestamp
        }

    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get historical consciousness metrics.

        Args:
            hours: Hours of history to analyze

        Returns:
            Historical metrics analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_history = [
            h for h in self.history
            if datetime.fromisoformat(h.timestamp) > cutoff_time
        ]

        if not recent_history:
            return {'error': 'No data in specified time range'}

        phi_values = [h.phi_value for h in recent_history]
        computation_times = [h.computation_time for h in recent_history]

        return {
            'time_range_hours': hours,
            'data_points': len(recent_history),
            'phi_stats': {
                'mean': np.mean(phi_values),
                'std': np.std(phi_values),
                'min': np.min(phi_values),
                'max': np.max(phi_values),
                'trend': self._calculate_trend(phi_values)
            },
            'performance_stats': {
                'mean_computation_time': np.mean(computation_times),
                'max_computation_time': np.max(computation_times)
            },
            'integration_distribution': self._calculate_integration_distribution(recent_history)
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from value series."""
        if len(values) < 2:
            return 'stable'

        # Simple linear trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_integration_distribution(self, history: List[ConsciousnessSnapshot]) -> Dict[str, int]:
        """Calculate distribution of integration levels."""
        levels = {}
        for snapshot in history:
            level = snapshot.integration_level
            levels[level] = levels.get(level, 0) + 1
        return levels

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent consciousness alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        return [alert.to_dict() for alert in self.alerts[-limit:]]

    def add_phi_callback(self, callback: Callable[[float], None]):
        """Add callback for Φ value updates."""
        self.phi_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[ConsciousnessAlert], None]):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)

    def _call_phi_callbacks(self, phi_value: float):
        """Call all Φ value callbacks."""
        for callback in self.phi_callbacks:
            try:
                callback(phi_value)
            except Exception as e:
                self.logger.error(f"Phi callback error: {e}")

    def _call_alert_callbacks(self, alert: ConsciousnessAlert):
        """Call all alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

    def save_history(self, filepath: str):
        """Save monitoring history to JSON file."""
        history_data = [snapshot.to_dict() for snapshot in self.history]

        with open(filepath, 'w') as f:
            json.dump(history_data, f, indent=2)

    def load_history(self, filepath: str):
        """Load monitoring history from JSON file."""
        try:
            with open(filepath, 'r') as f:
                history_data = json.load(f)

            # Convert back to ConsciousnessSnapshot objects
            self.history = []
            for item in history_data:
                snapshot = ConsciousnessSnapshot(
                    timestamp=item['timestamp'],
                    phi_value=item['phi_value'],
                    system_size=item['system_size'],
                    computation_time=item['computation_time'],
                    integration_level=item['integration_level'],
                    system_state=item.get('system_state', {})
                )
                self.history.append(snapshot)

        except FileNotFoundError:
            self.logger.warning(f"History file not found: {filepath}")

    def export_metrics_report(self, filepath: str, hours: int = 24):
        """
        Export comprehensive metrics report.

        Args:
            filepath: Output file path
            hours: Hours of data to include
        """
        current_metrics = self.get_current_metrics()
        historical_metrics = self.get_historical_metrics(hours)
        recent_alerts = self.get_recent_alerts(20)

        report = {
            'generated_at': datetime.now().isoformat(),
            'current_metrics': current_metrics,
            'historical_metrics': historical_metrics,
            'recent_alerts': recent_alerts,
            'system_status': 'monitoring' if self.is_monitoring else 'idle',
            'alert_thresholds': self.alert_thresholds
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)


# Convenience functions for easy integration
def start_consciousness_monitoring(interval: float = 1.0) -> ConsciousnessMetrics:
    """
    Convenience function to start consciousness monitoring.

    Returns:
        Configured ConsciousnessMetrics instance
    """
    monitor = ConsciousnessMetrics()
    monitor.start_monitoring(interval=interval)
    return monitor


def get_phi_snapshot(system_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a single Φ calculation snapshot.

    Args:
        system_state: Current system state

    Returns:
        Phi calculation results
    """
    calculator = IITPhiCalculator()
    result = calculator.calculate_phi(system_state)

    return {
        'phi_value': result.phi_value,
        'integration_level': calculator._interpret_phi_level(result.phi_value),
        'computation_time': result.computation_time,
        'system_size': result.system_size,
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Example usage
    monitor = ConsciousnessMetrics()

    # Start monitoring with default state provider
    monitor.start_monitoring(interval=2.0)

    # Monitor for 10 seconds
    print("Monitoring consciousness for 10 seconds...")
    time.sleep(10)

    # Get current metrics
    metrics = monitor.get_current_metrics()
    print(f"Current Φ: {metrics['phi_value']:.3f}")
    print(f"Integration level: {metrics['integration_level']}")

    # Get historical metrics
    history = monitor.get_historical_metrics(hours=1)
    print(f"Average Φ: {history['phi_stats']['mean']:.3f}")
    print(f"Φ trend: {history['phi_stats']['trend']}")

    # Stop monitoring
    monitor.stop_monitoring()
    print("Monitoring stopped.")