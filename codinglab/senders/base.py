"""
Base sender implementation for the coding experiments library.

This module provides a base implementation of the Sender protocol that
can be extended by concrete sender implementations. It handles common
functionality like encoder integration and message tracking.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["BaseSender"]

from typing import Sequence, Optional
from ..interfaces import Sender, Encoder
from ..types import SourceChar, ChannelChar, Message, TransmissionLogger
from ..logger import NullLogger


class BaseSender(Sender[SourceChar, ChannelChar]):
    """
    Base implementation of the Sender protocol.

    This class provides common functionality for all sender implementations,
    including encoder integration and tracking of the last generated message.
    Concrete sender implementations should inherit from this class and
    implement the message_stream method.

    Attributes:
        _encoder: Encoder instance for converting source to channel symbols
        _last_message: The last generated source message, if any
        _logger: A TransmissionLogger instance, default NullLogger
    """

    def __init__(
        self,
        encoder: Encoder[SourceChar, ChannelChar],
        logger: TransmissionLogger = NullLogger(),
    ) -> None:
        """
        Initialize the base sender with an encoder.

        Args:
            encoder: Encoder instance for converting source messages
                    to channel symbols
        """
        self._encoder = encoder
        """Encoder instance for source-to-channel symbol conversion."""

        self._last_message: Optional[Message[SourceChar]] = None
        """The last generated source message, or None if none generated yet."""

        self._logger = logger
        """A TransmissionLogger instance."""

    @property
    def alphabet(self) -> Sequence[SourceChar]:
        """
        Get the source alphabet from the encoder's code table.

        This implementation extracts the alphabet from the encoder's
        code table. If no code table is available, returns an empty list.

        Returns:
            Sequence of source symbols that can appear in messages

        Note:
            Subclasses may override this to provide a different alphabet
            source or validation mechanism.
        """
        # Extract alphabet from encoder's code table if available
        if self._encoder.code_table is not None:
            return list(self._encoder.code_table.keys())
        return []

    def get_last_message(self) -> Optional[Message[SourceChar]]:
        """
        Get the last generated source message.

        Returns:
            The last source message generated, or None if no messages
            have been generated yet
        """
        return self._last_message
