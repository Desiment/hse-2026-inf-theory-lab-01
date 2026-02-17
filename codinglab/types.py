"""
Data types and protocols for the coding experiments library.

This module defines the core data structures, type aliases, and protocols
used throughout the library for representing messages, transmission events,
logs, and experimental configurations.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = [
    "Symbol",
    "SourceChar",
    "ChannelChar",
    "Message",
    "TransmissionEvent",
    "TransmissionLog",
    "TransmissionLogger",
]


from dataclasses import dataclass
from typing import Dict, Any, Sequence, TypeVar, Protocol, Generic, runtime_checkable
from enum import Enum

# Type variables for generic symbol types
Symbol = TypeVar("Symbol")
"""Generic type variable representing any symbol type."""

SourceChar = TypeVar("SourceChar")
"""Type variable for source alphabet symbols (input to encoder)."""

ChannelChar = TypeVar("ChannelChar")
"""Type variable for channel alphabet symbols (output from encoder)."""


@dataclass
class Message(Generic[Symbol]):
    """
    A message containing a sequence of symbols.

    This class represents a message as an immutable sequence of symbols
    with a unique identifier for tracking purposes.

    Attributes:
        id: Unique identifier for the message
        data: Sequence of symbols comprising the message
    """

    id: int
    """Unique identifier for the message."""

    data: Sequence[Symbol]
    """Sequence of symbols comprising the message."""


class TransmissionEvent(str, Enum):
    """
    Events that occur during message transmission.

    These events are logged throughout the transmission pipeline
    for monitoring, debugging, and analysis purposes.
    """

    SOURCE_GENERATED = "source_generated"
    """Event when a source message is generated."""

    ENCODED = "encoded"
    """Event when a message is encoded."""

    TRANSMITTED = "transmitted"
    """Event when a message is transmitted through a channel."""

    RECEIVED = "received"
    """Event when a message is received from a channel."""

    DECODED = "decoded"
    """Event when a message is decoded."""

    VALIDATED = "validated"
    """Event when a message is validated."""

    ERROR = "error"
    """Event when an error occurs during transmission."""


@dataclass
class TransmissionLog(Generic[Symbol]):
    """
    Log entry for a transmission event.

    Contains detailed information about a specific event in the
    transmission pipeline, including timing, message data, and
    additional context.

    Attributes:
        timestamp: Time of the event in seconds since epoch
        event: Type of transmission event
        message: The message associated with the event
        data: Additional event-specific data as key-value pairs
    """

    timestamp: float
    """Time of the event in seconds since epoch."""

    event: TransmissionEvent
    """Type of transmission event."""

    message: Message[Symbol]
    """The message associated with the event."""

    data: Dict[str, Any]
    """Additional event-specific data as key-value pairs."""


@runtime_checkable
class TransmissionLogger(Protocol):
    """
    Protocol for logging transmission events.

    Implementations of this protocol are responsible for handling
    log entries generated during message transmission, which can be
    used for monitoring, debugging, or analytics.
    """

    def log(self, log_entry: TransmissionLog) -> None:
        """
        Log a transmission event.

        Args:
            log_entry: The transmission log entry to record
        """
        ...
