"""
Channel implementations for the coding experiments library.

This module provides concrete channel implementations for message transmission,
ranging from ideal noiseless channels to channels with various error models.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__description__ = "Channel implementations for coding experiments"

# Re-export channel implementations
from .base import NoiselessChannel as NoiselessChannel

__all__ = [
    "NoiselessChannel",
]
