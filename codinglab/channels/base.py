"""
Noiseless channel implementation for the coding experiments library.

This module provides a simple channel implementation that transmits
messages without any modification, noise, or errors. It serves as a
baseline for comparing with more complex channel models.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["NoiselessChannel"]

import time
from typing import Iterator
from ..interfaces import Channel
from ..types import (
    Message,
    ChannelChar,
    TransmissionEvent,
    TransmissionLog,
    TransmissionLogger,
)
from ..logger import NullLogger


class NoiselessChannel(Channel[ChannelChar]):
    """
    Channel that transmits messages without modification.

    This channel implementation faithfully transmits all messages
    without introducing any noise, errors, or delays. It serves as
    an ideal baseline channel for testing and comparison.

    Attributes:
        _logs: List of transmission log entries (for debugging/monitoring)
    """

    def __init__(self, logger: TransmissionLogger = NullLogger()) -> None:
        """
        Initialize a noiseless channel.

        The channel starts with an empty log for tracking transmissions.
        """
        self._logger = logger
        """List of transmission log entries for monitoring/debugging."""

    def transmit_stream(
        self, messages: Iterator[Message[ChannelChar]]
    ) -> Iterator[Message[ChannelChar]]:
        """
        Transmit a stream of messages without modification.

        This implementation simply passes through each message unchanged,
        while logging the transmission event for monitoring purposes.

        Args:
            messages: Iterator of encoded messages to transmit

        Yields:
            The same messages, unchanged

        Note:
            This channel maintains a log of all transmissions in the
            _logs attribute, which can be useful for debugging or
            monitoring channel activity.
        """
        for message in messages:
            # Log the transmission event
            self._logger.log(
                TransmissionLog(
                    event=TransmissionEvent.TRANSMITTED,
                    timestamp=time.time(),
                    message=message,
                    data={"channel_type": "noiseless"},
                )
            )

            yield message
