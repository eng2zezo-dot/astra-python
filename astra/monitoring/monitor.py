"""System monitoring and metrics collection."""

import time
import threading
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from datetime import datetime
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class Metrics:
    """Collect and store metrics."""

    def __init__(self):
        """Initialize metrics."""
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()

    def increment_counter(self, name: str, value: int = 1):
        """Increment counter metric.
        
        Args:
            name: Metric name
            value: Increment amount
        """
        with self.lock:
            self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        """Set gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
        """
        with self.lock:
            self.gauges[name] = value

    def record_histogram(self, name: str, value: float):
        """Record histogram value.
        
        Args:
            name: Metric name
            value: Value to record
        """
        with self.lock:
            self.histograms[name].append(value)
            # Keep only last 1000 values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]

    def get_counter(self, name: str) -> int:
        """Get counter value.
        
        Args:
            name: Metric name
            
        Returns:
            Counter value
        """
        return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value.
        
        Args:
            name: Metric name
            
        Returns:
            Gauge value
        """
        return self.gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> Dict:
        """Get histogram statistics.
        
        Args:
            name: Metric name
            
        Returns:
            Statistics dictionary
        """
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        values = sorted(values)
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'p50': values[len(values) // 2],
            'p95': values[int(len(values) * 0.95)],
            'p99': values[int(len(values) * 0.99)],
        }

    def get_all_metrics(self) -> Dict:
        """Get all metrics.
        
        Returns:
            All metrics dictionary
        """
        with self.lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    k: self.get_histogram_stats(k)
                    for k in self.histograms.keys()
                },
            }


class SystemMonitor:
    """Monitor Astra Headend system."""

    def __init__(self, headend):
        """Initialize monitor.
        
        Args:
            headend: AstraHeadend instance
        """
        self.headend = headend
        self.metrics = Metrics()
        self.running = False
        self.monitor_thread = None
        self.check_interval = 5  # seconds
        self.alarms: Dict[str, Dict] = {}
        self.alarm_callbacks: List[Callable] = []
        
        logger.info("System Monitor initialized")

    def start(self):
        """Start monitoring."""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("System Monitor started")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._collect_metrics()
                self._check_alarms()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitor error: {e}")

    def _collect_metrics(self):
        """Collect system metrics."""
        try:
            status = self.headend.get_status()
            
            # Update metrics
            self.metrics.set_gauge('system.uptime', status.get('uptime', 0))
            self.metrics.set_gauge('system.channels', status.get('channels', 0))
            self.metrics.set_gauge('system.sources', status.get('input_sources', 0))
            self.metrics.set_gauge('system.outputs', status.get('output_targets', 0))
            
            # Stats
            stats = status.get('stats', {})
            self.metrics.increment_counter('packets.received', 
                                          stats.get('packets_received', 0))
            self.metrics.increment_counter('packets.sent',
                                          stats.get('packets_sent', 0))
            self.metrics.increment_counter('errors.total',
                                          stats.get('errors', 0))
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _check_alarms(self):
        """Check for alarm conditions."""
        try:
            status = self.headend.get_status()
            
            # Check if running
            if not status.get('running'):
                self._trigger_alarm('system_not_running', 
                                   'Headend system is not running')
            
            # Check if no channels
            if status.get('channels', 0) == 0:
                self._trigger_alarm('no_channels',
                                   'No channels configured')
        except Exception as e:
            logger.error(f"Error checking alarms: {e}")

    def _trigger_alarm(self, alarm_id: str, message: str):
        """Trigger an alarm.
        
        Args:
            alarm_id: Alarm identifier
            message: Alarm message
        """
        if alarm_id not in self.alarms:
            self.alarms[alarm_id] = {
                'message': message,
                'timestamp': datetime.now(),
                'count': 1,
            }
            logger.warning(f"ALARM: {alarm_id} - {message}")
            
            # Call alarm callbacks
            for callback in self.alarm_callbacks:
                try:
                    callback(alarm_id, message)
                except:
                    pass
        else:
            self.alarms[alarm_id]['count'] += 1

    def register_alarm_callback(self, callback: Callable):
        """Register alarm callback.
        
        Args:
            callback: Callable(alarm_id, message)
        """
        self.alarm_callbacks.append(callback)

    def get_metrics(self) -> Dict:
        """Get all metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.metrics.get_all_metrics()

    def get_alarms(self) -> Dict:
        """Get active alarms.
        
        Returns:
            Alarms dictionary
        """
        return self.alarms.copy()

    def clear_alarm(self, alarm_id: str):
        """Clear alarm.
        
        Args:
            alarm_id: Alarm identifier
        """
        if alarm_id in self.alarms:
            del self.alarms[alarm_id]
            logger.info(f"Cleared alarm: {alarm_id}")

    def stop(self):
        """Stop monitoring."""
        self.running = False
        logger.info("System Monitor stopped")

    def __repr__(self) -> str:
        return f"SystemMonitor(running={self.running})"
