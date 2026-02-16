"""
Core protocol interfaces for the coding experiments library.

This module defines the abstract interfaces (protocols) for all major
components in the transmission pipeline: encoders, decoders, senders,
channels, and receivers.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["Encoder", "Decoder", "Sender", "Channel", "Receiver"]

from typing import Protocol, Sequence, Iterator, Optional, Dict, runtime_checkable
from abc import abstractmethod
from .types import SourceChar, ChannelChar, Message


@runtime_checkable
class Encoder(Protocol[SourceChar, ChannelChar]):
    """
    Protocol for encoding source messages into channel symbols.

    An encoder transforms sequences of source alphabet symbols into
    sequences of channel alphabet symbols, typically with the goal
    of compression, error correction, or format adaptation.
    """

    @abstractmethod
    def encode(self, message: Sequence[SourceChar]) -> Sequence[ChannelChar]:
        """
        Encode a source message into channel symbols.

        Args:
            message: Sequence of source symbols to encode

        Returns:
            Sequence of channel symbols representing the encoded message

        Raises:
            ValueError: If the message contains symbols not in the encoder's alphabet
        """
        ...

    @property
    @abstractmethod
    def code_table(self) -> Optional[Dict[SourceChar, Sequence[ChannelChar]]]:
        """
        Get the encoding table if available.

        Returns:
            Dictionary mapping source symbols to their channel code sequences,
            or None if no explicit code table exists
        """
        ...


@runtime_checkable
class Decoder(Protocol[SourceChar, ChannelChar]):
    """
    Protocol for decoding channel symbols back into source messages.

    A decoder performs the inverse operation of an encoder, reconstructing
    source messages from sequences of channel symbols.
    """

    @abstractmethod
    def decode(self, encoded: Sequence[ChannelChar]) -> Sequence[SourceChar]:
        """
        Decode channel symbols back into a source message.

        Args:
            encoded: Sequence of channel symbols to decode

        Returns:
            Sequence of source symbols representing the decoded message

        Raises:
            ValueError: If the encoded sequence cannot be decoded
            KeyError: If a code sequence is not found in the decoding table
        """
        ...

    @property
    @abstractmethod
    def code_table(self) -> Optional[Dict[SourceChar, Sequence[ChannelChar]]]:
        """
        Get the encoding table if available.

        Returns:
            Dictionary mapping source symbols to their channel code sequences,
            or None if no explicit code table exists
        """
        ...


@runtime_checkable
class Sender(Protocol[SourceChar, ChannelChar]):
    """
    Protocol for message sources with encoding capability.

    A sender generates source messages and encodes them for transmission
    through a channel. It maintains state about the last generated message.
    """

    @property
    @abstractmethod
    def alphabet(self) -> Sequence[SourceChar]:
        """
        Get the source alphabet used by this sender.

        Returns:
            Sequence of source symbols that can appear in messages
        """
        ...

    @abstractmethod
    def message_stream(self, stream_len: int) -> Iterator[Message[ChannelChar]]:
        """
        Generate a stream of encoded messages.

        Args:
            stream_len: Number of messages to generate

        Yields:
            Encoded messages wrapped in Message containers

        Raises:
            ValueError: If stream_len <= 0
        """
        ...

    @abstractmethod
    def get_last_message(self) -> Optional[Message[SourceChar]]:
        """
        Get the last generated source message.

        Returns:
            The last source message generated, or None if no messages
            have been generated yet
        """
        ...


@runtime_checkable
class Channel(Protocol[ChannelChar]):
    """
    Protocol for communication channels.

    A channel transmits messages from sender to receiver, potentially
    introducing noise, delays, or other channel effects.
    """

    @abstractmethod
    def transmit_stream(
        self, messages: Iterator[Message[ChannelChar]]
    ) -> Iterator[Message[ChannelChar]]:
        """
        Transmit a stream of messages through the channel.

        Args:
            messages: Iterator of encoded messages to transmit

        Yields:
            Transmitted messages (potentially modified by channel effects)

        Note:
            The channel may maintain state between messages (e.g., for
            modeling channel memory effects)
        """
        ...


@runtime_checkable
class Receiver(Protocol[SourceChar, ChannelChar]):
    """
    Protocol for message receivers with decoding capability.

    A receiver accepts messages from a channel, decodes them, and
    provides access to the received messages.
    """

    @abstractmethod
    def __init__(self, decoder: Decoder[SourceChar, ChannelChar]) -> None:
        """
        Initialize the receiver with a decoder.

        Args:
            decoder: Decoder instance for converting channel symbols
                    back to source messages
        """
        ...

    @abstractmethod
    def receive_stream(
        self, messages: Iterator[Message[ChannelChar]]
    ) -> Iterator[bool]:
        """
        Receive and process a stream of messages.

        Args:
            messages: Iterator of messages received from a channel

        Yields:
            True for each successfully received and decoded message,
            False for messages that failed to decode

        Note:
            The receiver may perform validation, error checking, or
            other processing on received messages
        """
        ...

    @abstractmethod
    def get_last_message(self) -> Optional[Message[SourceChar]]:
        """
        Get the last successfully decoded message.

        Returns:
            The last decoded source message, or None if no messages
            have been successfully decoded yet
        """
        ...
