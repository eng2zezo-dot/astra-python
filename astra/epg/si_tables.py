"""EPG and SI Tables parsing."""

from typing import Dict, List, Optional
from datetime import datetime
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class EPGEntry:
    """EPG program entry."""

    def __init__(self, service_id: int, event_id: int, title: str,
                 start_time: datetime, duration: int, description: str = ""):
        """Initialize EPG entry.
        
        Args:
            service_id: Service ID
            event_id: Event ID
            title: Program title
            start_time: Start time
            duration: Duration in seconds
            description: Program description
        """
        self.service_id = service_id
        self.event_id = event_id
        self.title = title
        self.start_time = start_time
        self.duration = duration
        self.description = description

    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'service_id': self.service_id,
            'event_id': self.event_id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'duration': self.duration,
            'description': self.description,
        }


class SITables:
    """DVB SI Tables parser."""

    # Common SI Table PIDs
    PAT_PID = 0x00      # Program Association Table
    CAT_PID = 0x01      # Conditional Access Table
    PMT_BASE_PID = 0x10 # Program Map Table (base)
    SDT_PID = 0x11      # Service Description Table
    BAT_PID = 0x12      # Bouquet Association Table
    EIT_PID = 0x12      # Event Information Table
    TDT_PID = 0x14      # Time and Date Table
    TOT_PID = 0x14      # Time Offset Table

    def __init__(self):
        """Initialize SI Tables parser."""
        self.pat_data = {}  # Program Association Table
        self.pmt_data = {}  # Program Map Tables
        self.sdt_data = {}  # Service Description Table
        self.epg_data: Dict[int, List[EPGEntry]] = {}  # EPG by service_id
        
        logger.info("SI Tables parser initialized")

    def parse_pat(self, data: bytes) -> Dict:
        """Parse PAT (Program Association Table).
        
        Args:
            data: PAT section data
            
        Returns:
            Parsed PAT dictionary
        """
        # Simplified PAT parsing
        logger.debug("Parsing PAT")
        # In real implementation, would parse binary data
        return {}

    def parse_pmt(self, data: bytes) -> Dict:
        """Parse PMT (Program Map Table).
        
        Args:
            data: PMT section data
            
        Returns:
            Parsed PMT dictionary
        """
        # Simplified PMT parsing
        logger.debug("Parsing PMT")
        # In real implementation, would parse binary data
        return {}

    def parse_sdt(self, data: bytes) -> Dict:
        """Parse SDT (Service Description Table).
        
        Args:
            data: SDT section data
            
        Returns:
            Parsed SDT dictionary
        """
        # Simplified SDT parsing
        logger.debug("Parsing SDT")
        # In real implementation, would parse binary data
        return {}

    def parse_eit(self, data: bytes) -> Dict:
        """Parse EIT (Event Information Table).
        
        Args:
            data: EIT section data
            
        Returns:
            Parsed EIT dictionary
        """
        # Simplified EIT parsing
        logger.debug("Parsing EIT")
        # In real implementation, would parse binary data
        return {}

    def add_epg_entry(self, entry: EPGEntry):
        """Add EPG entry.
        
        Args:
            entry: EPG entry
        """
        service_id = entry.service_id
        if service_id not in self.epg_data:
            self.epg_data[service_id] = []
        
        self.epg_data[service_id].append(entry)
        logger.debug(f"Added EPG entry: {entry.title} on service {service_id}")

    def get_epg(self, service_id: int) -> List[EPGEntry]:
        """Get EPG for service.
        
        Args:
            service_id: Service ID
            
        Returns:
            List of EPG entries
        """
        return self.epg_data.get(service_id, [])

    def get_current_program(self, service_id: int) -> Optional[EPGEntry]:
        """Get currently airing program.
        
        Args:
            service_id: Service ID
            
        Returns:
            Current program or None
        """
        epg = self.get_epg(service_id)
        now = datetime.now()
        
        for entry in epg:
            if entry.start_time <= now and \
               (entry.start_time.timestamp() + entry.duration) > now.timestamp():
                return entry
        
        return None

    def get_next_program(self, service_id: int) -> Optional[EPGEntry]:
        """Get next program.
        
        Args:
            service_id: Service ID
            
        Returns:
            Next program or None
        """
        epg = self.get_epg(service_id)
        now = datetime.now()
        
        future_programs = [
            e for e in epg
            if e.start_time > now
        ]
        
        if future_programs:
            return min(future_programs, key=lambda x: x.start_time)
        
        return None

    def export_epg(self) -> Dict:
        """Export all EPG data.
        
        Returns:
            EPG dictionary
        """
        return {
            service_id: [e.to_dict() for e in entries]
            for service_id, entries in self.epg_data.items()
        }

    def __repr__(self) -> str:
        return f"SITables(services={len(self.epg_data)})"
