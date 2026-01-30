"""
Fixed messages sender implementation for the coding experiments library.

This module provides a sender implementation that cycles through a fixed
set of pre-defined messages. It's useful for reproducible experiments and
testing scenarios where specific message sequences are required.
"""

import time
from typing import Sequence, Iterator, List, Optional
from .base import BaseSender
from ..interfaces import Encoder
from ..types import (
    Message,
    SourceChar,
    ChannelChar,
    TransmissionLogger,
    TransmissionEvent,
    TransmissionLog,
)
from ..logger import NullLogger

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["FixedMessagesSender"]


class FixedMessagesSender(BaseSender[SourceChar, ChannelChar]):
    """
    Sender that cycles through a fixed set of source messages.

    This sender repeatedly sends messages from a provided list, wrapping
    around to the beginning when the end is reached. Each message is
    assigned a unique ID for tracking purposes.

    Attributes:
        _messages: List of source messages to send
        _message_id: Counter for assigning unique message IDs
        _index: Current position in the messages list
    """

    def __init__(
        self,
        encoder: Encoder[SourceChar, ChannelChar],
        messages: List[Sequence[SourceChar]],
        logger: TransmissionLogger = NullLogger(),
    ) -> None:
        """
        Initialize the fixed messages sender.

        Args:
            encoder: Encoder instance for converting source to channel symbols
            messages: List of source messages to send
            logger: Logger for recording transmission events (defaults to NullLogger)

        Raises:
            ValueError: If messages list is empty
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        super().__init__(encoder, logger)
        self._messages = messages
        """List of source messages to send."""

        self._message_id = 0
        """Counter for assigning unique message IDs."""

        self._index = 0
        """Current position in the messages list."""

    def message_stream(
        self, stream_len: Optional[int] = None
    ) -> Iterator[Message[ChannelChar]]:
        """
        Generate a stream of encoded messages from the fixed list.

        If stream_len is not specified, generates one encoded message
        for each source message in the list. If stream_len exceeds the
        number of messages, the sender wraps around to the beginning.

        Args:
            stream_len: Number of messages to generate. If None, uses
                       the length of the messages list.

        Yields:
            Encoded messages wrapped in Message containers with unique IDs

        Raises:
            ValueError: If stream_len <= 0
        """
        if stream_len is None:
            stream_len = len(self._messages)

        if stream_len <= 0:
            raise ValueError(f"stream_len must be positive, got {stream_len}")

        for _ in range(stream_len):
            # Get the next source message from the list
            source_message = Message(
                id=self._message_id, data=self._messages[self._index]
            )

            # Update tracking state
            self._last_message = source_message
            self._message_id += 1
            self._index = (self._index + 1) % len(self._messages)
            self._logger.log(
                TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.SOURCE_GENERATED,
                    message=source_message,
                    data={"index": self._index},
                )
            )
            # Encode the message
            encoded_data = self._encoder.encode(source_message.data)
            encoded_message = Message(id=source_message.id, data=encoded_data)
            self._logger.log(
                TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.ENCODED,
                    message=encoded_message,
                    data={},
                )
            )

            yield encoded_message

    def reset(self) -> None:
        """
        Reset the sender to its initial state.

        This method resets the message index and ID counter, allowing
        the sender to restart from the beginning of the messages list.
        """
        self._index = 0
        self._message_id = 0
