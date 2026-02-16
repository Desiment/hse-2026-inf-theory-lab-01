"""
Tracking receiver implementation for the coding experiments library.

This module provides a receiver implementation that collects detailed
statistics about message reception, including success rates, processing
times, and compression metrics. It's designed for experimental analysis
and performance evaluation.

Author: Mikhail Mikhailov
License: MIT
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["TransmissionStats", "TrackingReceiver"]

import time
from typing import Iterator, Optional
from dataclasses import dataclass
from ..interfaces import Receiver, Decoder
from ..types import (
    TransmissionLog,
    TransmissionEvent,
    SourceChar,
    ChannelChar,
    Message,
    TransmissionLogger,
)
from ..logger import NullLogger


@dataclass
class TransmissionStats:
    """
    Statistics collected during message transmission and reception.

    This class tracks various metrics about the transmission process,
    including message counts, symbol counts, error rates, and timing
    information. It also provides computed properties for common
    performance indicators.

    Attributes:
        total_messages: Total number of messages processed
        successful_messages: Number of messages, that's were correctly decoded
        decoded_messages: Number of decoded messages
        failed_messages: Number of messages that failed to decode
        total_source_symbols: Total number of source symbols processed
        total_channel_symbols: Total number of channel symbols processed
        decode_errors: Number of decoding errors encountered
        validation_errors: Number of validation errors (currently unused)
        total_processing_time: Total time spent processing messages (seconds)
        avg_message_time: Average processing time per message (seconds)
    """

    total_messages: int = 0
    """Total number of messages processed."""

    successful_messages: int = 0
    """Number of correctly decoded messages."""

    decoded_messages: int = 0
    """Number of decoded messages."""

    failed_messages: int = 0
    """Number of messages that failed to decode."""

    total_source_symbols: int = 0
    """Total number of source symbols processed."""

    total_channel_symbols: int = 0
    """Total number of channel symbols processed."""

    decode_errors: int = 0
    """Number of decoding errors encountered."""

    validation_errors: int = 0
    """Number of validation errors (reserved for future use)."""

    total_processing_time: float = 0.0
    """Total time spent processing messages (seconds)."""

    avg_message_time: float = 0.0
    """Average processing time per message (seconds)."""

    @property
    def success_rate(self) -> float:
        """
        Calculate the success rate of message transmission.

        Returns:
            Ratio of successful messages to total messages, or 0.0
            if no messages have been processed
        """
        if self.total_messages > 0:
            return self.successful_messages / self.total_messages
        return 0.0

    @property
    def compression_ratio(self) -> float:
        """
        Calculate the compression ratio achieved by encoding.

        Returns:
            Ratio of source symbols to channel symbols, or 0.0
            if no channel symbols have been processed

        Note:
            Values greater than 1.0 indicate compression (fewer channel
            symbols than source symbols), while values less than 1.0
            indicate expansion.
        """
        if self.total_channel_symbols > 0:
            return self.total_source_symbols / self.total_channel_symbols
        return 0.0

    @property
    def average_code_len(self) -> float:
        """
        Calculate the average code length per source symbol.

        Returns:
            Average number of channel symbols per source symbol, or 0.0
            if no source symbols have been processed
        """
        if self.total_source_symbols > 0:
            return self.total_channel_symbols / self.total_source_symbols
        return 0.0


class TrackingReceiver(Receiver[SourceChar, ChannelChar]):
    """
    Receiver that tracks detailed statistics about message reception.

    This receiver not only decodes messages but also collects extensive
    statistics about the reception process, including timing information,
    success rates, and compression metrics. It's ideal for experimental
    analysis and performance evaluation.

    Attributes:
        _decoder: Decoder instance for converting channel to source symbols
        _stats: Statistics collected during message reception
        _last_message: The last successfully decoded source message
        _logger: Logger for recording transmission events

    Note: stats does not contain failed_messages and successful_messages as
    their value can be computed based only on knowning messages sent by
    sender.
    """

    def __init__(
        self,
        decoder: Decoder[SourceChar, ChannelChar],
        logger: TransmissionLogger = NullLogger(),
    ) -> None:
        """
        Initialize the tracking receiver.

        Args:
            decoder: Decoder instance for converting channel symbols
                    back to source messages
            logger: Logger for recording transmission events
                    (defaults to NullLogger)
        """
        self._decoder = decoder
        """Decoder instance for channel-to-source symbol conversion."""

        self._stats = TransmissionStats()
        """Statistics collected during message reception."""

        self._last_message: Optional[Message[SourceChar]] = None
        """The last successfully decoded source message."""

        self._logger = logger
        """Logger for recording transmission events."""

    def receive_stream(
        self, messages: Iterator[Message[ChannelChar]]
    ) -> Iterator[bool]:
        """
        Receive, decode, and track statistics for a stream of messages.

        This implementation decodes each message, tracks detailed statistics
        about the decoding process, logs events, and yields True for
        successful decoding or False for failures.

        Args:
            messages: Iterator of messages received from a channel

        Yields:
            True for each successfully received and decoded message,
            False for messages that failed to decode

        Note:
            All statistics are updated incrementally as messages are
            processed, allowing real-time monitoring of performance.
        """
        for encoded_message in messages:
            start_time = time.time()

            # Log message reception
            self._logger.log(
                TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.RECEIVED,
                    message=encoded_message,
                    data={},
                )
            )

            self._stats.total_messages += 1
            try:
                # Decode the message
                decoded_data = self._decoder.decode(encoded_message.data)
                decoded_message = Message(id=encoded_message.id, data=decoded_data)

                # Update tracking state
                self._last_message = decoded_message

                # Update statistics for successful decoding
                self._stats.total_source_symbols += len(decoded_data)
                self._stats.total_channel_symbols += len(encoded_message.data)
                # Log successful decoding
                decode_log = TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.DECODED,
                    message=decoded_message,
                    data={
                        "encoded_length": len(encoded_message.data),
                        "decoded_length": len(decoded_data),
                        "encoded_message": encoded_message,
                    },
                )
                self._logger.log(decode_log)
                self._stats.decoded_messages += 1
                if hasattr(self._logger, "check_message"):
                    if self._logger.check_message(decoded_message):
                        self._stats.successful_messages += 1
                        success = True
                    else:
                        self._stats.validation_errors += 1
                        success = False
                else:
                    success = True
            except Exception as e:
                # Update statistics for failed decoding
                self._stats.decode_errors += 1
                # Log decoding error
                self._logger.log(
                    TransmissionLog(
                        timestamp=time.time(),
                        event=TransmissionEvent.ERROR,
                        message=encoded_message,
                        data={"error": str(e), "error_type": type(e).__name__},
                    )
                )

                success = False

            # Update timing statistics
            processing_time = time.time() - start_time
            self._stats.total_processing_time += processing_time
            if self._stats.total_messages > 0:
                self._stats.avg_message_time = (
                    self._stats.total_processing_time / self._stats.total_messages
                )

            yield success

    def get_last_message(self) -> Optional[Message[SourceChar]]:
        """
        Get the last successfully decoded message.

        Returns:
            The last decoded source message, or None if no messages
            have been successfully decoded yet
        """
        return self._last_message

    def get_stats(self) -> TransmissionStats:
        """
        Get the current transmission statistics.

        Returns:
            Copy of the current TransmissionStats object with all
            collected metrics
        """
        return self._stats

    def reset_stats(self) -> None:
        """
        Reset all statistics and logs to their initial state.

        This method clears all collected statistics and logs, allowing
        the receiver to start fresh for a new experiment or test run.
        """
        self._stats = TransmissionStats()
