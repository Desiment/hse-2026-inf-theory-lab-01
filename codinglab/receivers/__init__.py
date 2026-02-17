"""
Receiver implementations for the coding experiments library.

This module provides receiver implementations for decoding messages
and collecting transmission statistics.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__description__ = "Receiver implementations for coding experiments"

# Re-export receiver implementations
from .base import BaseReceiver as BaseReceiver
from .tracking import (
    TrackingReceiver as TrackingReceiver,
    TransmissionStats as TransmissionStats,
)

__all__ = [
    "BaseReceiver",
    "TrackingReceiver",
    "TransmissionStats",
]
