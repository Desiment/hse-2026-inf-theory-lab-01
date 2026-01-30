"""
Coding Experiments Library (co)

A modular, type-safe library for experiments with information coding algorithms
in educational and research contexts. The library implements a streaming pipeline
architecture with clear separation of responsibilities between components.

Author: Mikhail Mikhailov
License: MIT
"""

# Re-export from interfaces module
from .interfaces import (
    Sender as Sender,
    Encoder as Encoder,
    Decoder as Decoder,
    Channel as Channel,
    Receiver as Receiver,
)

# Re-export from types module
from .types import (
    TransmissionLog as TransmissionLog,
    TransmissionEvent as TransmissionEvent,
    TransmissionLogger as TransmissionLogger,
    Message as Message,
    Symbol as Symbol,
    SourceChar as SourceChar,
    ChannelChar as ChannelChar,
)

# Re-export from loggers module
from .logger import (
    PlainLogger as PlainLogger,
    ConsoleLogger as ConsoleLogger,
    NullLogger as NullLogger,
    PandasLogger as PandasLogger
)

# Re-export from senders module
from .senders.base import BaseSender as BaseSender
from .senders.fixed import FixedMessagesSender as FixedMessagesSender
from .senders.probabilistic import ProbabilisticSender as ProbabilisticSender

# Re-export from channels module
from .channels.base import NoiselessChannel as NoiselessChannel

# Re-export from receivers module
from .receivers.base import BaseReceiver as BaseReceiver
from .receivers.tracking import (
    TrackingReceiver as TrackingReceiver,
    TransmissionStats as TransmissionStats,
)

# Re-export from encoders module
from .encoders.prefix_coder import PrefixEncoderDecoder as PrefixEncoderDecoder
from .encoders.prefix_code_tree import (
    PrefixCodeTree as PrefixCodeTree,
    TreeNode as TreeNode,
)

# Re-export from experiment module
from .experiment import (
    ExperimentRunner as ExperimentRunner,
    ExperimentResult as ExperimentResult,
)

# Explicit __all__ for public API
__all__ = [
    # Interfaces
    "Sender",
    "Encoder",
    "Decoder",
    "Channel",
    "Receiver",
    # Types
    "TransmissionLog",
    "TransmissionEvent",
    "TransmissionLogger",
    "Message",
    "Symbol",
    "SourceChar",
    "ChannelChar",
    # Loggers
    "PlainLogger",
    "PandasLogger",
    "ConsoleLogger",
    "NullLogger",
    # Senders
    "BaseSender",
    "FixedMessagesSender",
    "ProbabilisticSender",
    # Channels
    "NoiselessChannel",
    # Receivers
    "BaseReceiver",
    "TrackingReceiver",
    "TransmissionStats",
    # Encoders
    "PrefixEncoderDecoder",
    "PrefixCodeTree",
    "TreeNode",
    # Experiment framework
    "ExperimentRunner",
    "ExperimentResult",
]

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__description__ = "A library for experiments with information coding algorithms"
