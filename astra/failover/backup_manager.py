"""Failover and backup management."""

import threading
import time
from typing import Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class FailoverState(Enum):
    """Failover states."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FAILED = "failed"


class BackupManager:
    """Manage failover and backup sources."""

    def __init__(self, check_interval: int = 5):
        """Initialize backup manager.
        
        Args:
            check_interval: Health check interval in seconds
        """
        self.sources: Dict[str, Dict] = {}  # source_name -> {primary, backup}
        self.states: Dict[str, FailoverState] = {}
        self.check_interval = check_interval
        self.running = False
        self.check_thread = None
        self.failover_callbacks: List[Callable] = []
        self.lock = threading.RLock()
        
        logger.info(f"Backup Manager initialized (check interval: {check_interval}s)")

    def add_backup_source(self, source_name: str, primary_uri: str, 
                         backup_uri: str):
        """Add backup source.
        
        Args:
            source_name: Source identifier
            primary_uri: Primary source URI
            backup_uri: Backup source URI
        """
        with self.lock:
            self.sources[source_name] = {
                'primary': primary_uri,
                'backup': backup_uri,
                'active': primary_uri,
                'last_check': None,
                'failover_count': 0,
            }
            self.states[source_name] = FailoverState.PRIMARY
            logger.info(f"Added backup source: {source_name}")
            logger.info(f"  Primary: {primary_uri}")
            logger.info(f"  Backup: {backup_uri}")

    def start_monitoring(self):
        """Start failover monitoring."""
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.check_thread.start()
        logger.info("Backup monitoring started")

    def _health_check_loop(self):
        """Main health check loop."""
        while self.running:
            try:
                self._perform_health_checks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")

    def _perform_health_checks(self):
        """Perform health checks on all sources."""
        with self.lock:
            for source_name, source_info in self.sources.items():
                is_healthy = self._check_source_health(source_name)
                current_state = self.states[source_name]
                
                if not is_healthy and current_state == FailoverState.PRIMARY:
                    # Primary failed, switch to backup
                    self._trigger_failover(source_name)
                elif is_healthy and current_state == FailoverState.SECONDARY:
                    # Primary recovered, switch back
                    self._trigger_failback(source_name)

    def _check_source_health(self, source_name: str) -> bool:
        """Check if source is healthy.
        
        Args:
            source_name: Source identifier
            
        Returns:
            True if healthy, False otherwise
        """
        if source_name not in self.sources:
            return False
        
        source_info = self.sources[source_name]
        active_uri = source_info['active']
        
        # Simplified health check (in real implementation, would ping/probe source)
        # For now, assume sources are always healthy
        return True

    def _trigger_failover(self, source_name: str):
        """Trigger failover to backup.
        
        Args:
            source_name: Source identifier
        """
        logger.warning(f"Failover triggered for {source_name}")
        
        source_info = self.sources[source_name]
        source_info['active'] = source_info['backup']
        source_info['failover_count'] += 1
        source_info['last_check'] = datetime.now()
        self.states[source_name] = FailoverState.SECONDARY
        
        # Call failover callbacks
        for callback in self.failover_callbacks:
            try:
                callback(source_name, 'failover', source_info['backup'])
            except:
                pass
        
        logger.warning(f"Failed over to backup: {source_info['backup']}")

    def _trigger_failback(self, source_name: str):
        """Trigger failback to primary.
        
        Args:
            source_name: Source identifier
        """
        logger.info(f"Failback triggered for {source_name}")
        
        source_info = self.sources[source_name]
        primary_uri = source_info['primary']
        source_info['active'] = primary_uri
        source_info['last_check'] = datetime.now()
        self.states[source_name] = FailoverState.PRIMARY
        
        # Call failover callbacks
        for callback in self.failover_callbacks:
            try:
                callback(source_name, 'failback', primary_uri)
            except:
                pass
        
        logger.info(f"Failed back to primary: {primary_uri}")

    def get_active_source(self, source_name: str) -> Optional[str]:
        """Get currently active source URI.
        
        Args:
            source_name: Source identifier
            
        Returns:
            Active source URI or None
        """
        if source_name not in self.sources:
            return None
        return self.sources[source_name]['active']

    def get_status(self, source_name: str) -> Dict:
        """Get source status.
        
        Args:
            source_name: Source identifier
            
        Returns:
            Status dictionary
        """
        if source_name not in self.sources:
            return {}
        
        source_info = self.sources[source_name]
        return {
            'name': source_name,
            'state': self.states[source_name].value,
            'primary': source_info['primary'],
            'backup': source_info['backup'],
            'active': source_info['active'],
            'failover_count': source_info['failover_count'],
            'last_check': source_info['last_check'],
        }

    def get_all_status(self) -> Dict:
        """Get status of all sources.
        
        Returns:
            Dictionary of all statuses
        """
        with self.lock:
            return {
                name: self.get_status(name)
                for name in self.sources.keys()
            }

    def register_failover_callback(self, callback: Callable):
        """Register failover event callback.
        
        Args:
            callback: Callable(source_name, event_type, active_uri)
        """
        self.failover_callbacks.append(callback)

    def manual_failover(self, source_name: str):
        """Manually trigger failover.
        
        Args:
            source_name: Source identifier
        """
        if source_name in self.sources:
            self._trigger_failover(source_name)

    def manual_failback(self, source_name: str):
        """Manually trigger failback.
        
        Args:
            source_name: Source identifier
        """
        if source_name in self.sources:
            self._trigger_failback(source_name)

    def stop(self):
        """Stop monitoring."""
        self.running = False
        logger.info("Backup monitoring stopped")

    def __repr__(self) -> str:
        return f"BackupManager(sources={len(self.sources)})"
