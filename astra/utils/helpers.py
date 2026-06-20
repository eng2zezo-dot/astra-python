"""Helper utilities."""

import socket
import struct
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


def parse_uri(uri: str) -> dict:
    """Parse URI into components.
    
    Args:
        uri: URI string (e.g., 'udp://239.1.1.1:5000')
        
    Returns:
        Dictionary with parsed components
    """
    parsed = urlparse(uri)
    return {
        'scheme': parsed.scheme,
        'hostname': parsed.hostname,
        'port': parsed.port,
        'path': parsed.path,
        'params': parse_qs(parsed.query),
    }


def is_valid_ip(ip: str) -> bool:
    """Check if string is valid IP address.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_multicast_ip(ip: str) -> bool:
    """Check if IP is multicast address.
    
    Args:
        ip: IP address string
        
    Returns:
        True if multicast, False otherwise
    """
    try:
        addr = struct.unpack('!I', socket.inet_aton(ip))[0]
        return (addr >= 0xE0000000) and (addr <= 0xEFFFFFFF)
    except socket.error:
        return False


def format_bitrate(bitrate: int) -> str:
    """Format bitrate in human readable format.
    
    Args:
        bitrate: Bitrate in bits/second
        
    Returns:
        Formatted string
    """
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps']:
        if bitrate < 1000:
            return f"{bitrate:.2f} {unit}"
        bitrate /= 1000
    return f"{bitrate:.2f} Tbps"


def format_size(size: int) -> str:
    """Format size in human readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
