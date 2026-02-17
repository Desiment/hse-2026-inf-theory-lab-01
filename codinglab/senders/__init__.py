"""
Sender implementations for the coding experiments library.

This module provides sender implementations for generating source messages,
ranging from fixed message sequences to probabilistic sources.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__description__ = "Sender implementations for coding experiments"

# Re-export sender implementations
from .base import BaseSender as BaseSender
from .fixed import FixedMessagesSender as FixedMessagesSender
from .probabilistic import ProbabilisticSender as ProbabilisticSender

__all__ = [
    "BaseSender",
    "FixedMessagesSender",
    "ProbabilisticSender",
]
