"""
Base receiver implementation for the coding experiments library.

This module provides a base implementation of the Receiver protocol that
handles message decoding and tracking. It can be extended with additional
functionality like error detection, validation, or statistics collection.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = [
    "BaseReceiver",
]

import time
from typing import Iterator, Optional
from ..interfaces import Receiver, Decoder
from ..types import (
    SourceChar,
    ChannelChar,
    Message,
    TransmissionEvent,
    TransmissionLog,
    TransmissionLogger,
)
from ..logger import NullLogger


class BaseReceiver(Receiver[SourceChar, ChannelChar]):
    """
    Base implementation of the Receiver protocol.

    This class provides common functionality for receiving and decoding
    messages from a channel. It tracks the last successfully decoded
    message and can be extended with additional processing logic.

    Attributes:
        _decoder: Decoder instance for converting channel to source symbols
        _last_decoded: The last successfully decoded source message
        _logger: Logger for recording transmission events
    """

    def __init__(
        self,
        decoder: Decoder[SourceChar, ChannelChar],
        logger: TransmissionLogger = NullLogger(),
    ) -> None:
        """
        Initialize the base receiver with a decoder and logger.

        Args:
            decoder: Decoder instance for converting channel symbols
                    back to source messages
            logger: Logger for recording transmission events
                    (defaults to NullLogger)
        """
        self._decoder = decoder
        """Decoder instance for channel-to-source symbol conversion."""

        self._last_decoded: Optional[Message[SourceChar]] = None
        """The last successfully decoded source message, or None."""

        self._logger = logger
        """Logger for recording transmission events."""

    def receive_stream(
        self, messages: Iterator[Message[ChannelChar]]
    ) -> Iterator[bool]:
        """
        Receive and decode a stream of messages.

        This implementation decodes each message and yields True for
        successful decoding. It logs both the reception and decoding events.

        Args:
            messages: Iterator of messages received from a channel

        Yields:
            True for each successfully received and decoded message

        Note:
            This implementation always returns True; subclasses may
            override to perform validation and return False for failed
            messages.
        """
        for message in messages:
            # Log message reception
            self._logger.log(
                TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.RECEIVED,
                    message=message,
                    data={"channel_data": message.data},
                )
            )

            try:
                # Decode the message
                decoded_data = self._decoder.decode(message.data)

                # Create decoded message with the same ID
                decoded_message = Message(id=message.id, data=decoded_data)
                self._last_decoded = decoded_message

                # Log successful decoding
                self._logger.log(
                    TransmissionLog(
                        timestamp=time.time(),
                        event=TransmissionEvent.DECODED,
                        message=decoded_message,
                        data={"original_channel_data": message.data},
                    )
                )

                yield True

            except Exception as e:
                # Log decoding error
                self._logger.log(
                    TransmissionLog(
                        timestamp=time.time(),
                        event=TransmissionEvent.ERROR,
                        message=message,
                        data={"error": str(e), "error_type": type(e).__name__},
                    )
                )
                yield False

    def get_last_message(self) -> Optional[Message[SourceChar]]:
        """
        Get the last successfully decoded message.

        Returns:
            The last decoded source message, or None if no messages
            have been successfully decoded yet
        """
        return self._last_decoded
