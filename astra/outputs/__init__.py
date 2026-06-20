"""Outputs module."""

from astra.outputs.udp_output import UDPMulticastOutput
from astra.outputs.http_output import HTTPStreamingOutput
from astra.outputs.hls_output import HLSOutput
from astra.outputs.srt_output import SRTOutput
from astra.outputs.rtsp_output import RTSPServer

__all__ = [
    'UDPMulticastOutput',
    'HTTPStreamingOutput',
    'HLSOutput',
    'SRTOutput',
    'RTSPServer',
]
