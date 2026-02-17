# codinglab/encoders/identity.py
"""
Identity encoder implementation for the coding experiments library.

This module provides an encoder that passes symbols through unchanged.
It's useful as a baseline for testing and as a simple passthrough
when no encoding is needed.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["IdentityEncoder"]

from typing import Sequence, Dict, Optional, TypeVar, Generic
from ..interfaces import Encoder, Decoder
from ..types import SourceChar, ChannelChar


class IdentityEncoder(
    Encoder[SourceChar, ChannelChar],
    Decoder[SourceChar, ChannelChar],
):
    """
    Encoder that passes symbols through unchanged.

    This encoder implements both Encoder and Decoder protocols,
    making it useful as a baseline for testing and as a simple
    passthrough when no actual encoding/decoding is needed.

    The encoder assumes that source and channel alphabets are the same,
    and simply returns the input sequence unchanged.

    Attributes:
        _code_table: Always None for identity encoder
    """

    def __init__(self) -> None:
        """Initialize the identity encoder."""
        self._code_table: Optional[Dict[SourceChar, Sequence[ChannelChar]]] = None

    def encode(self, message: Sequence[SourceChar]) -> Sequence[ChannelChar]:
        """
        Encode a message by returning it unchanged.

        This method assumes that the source symbols can be used as
        channel symbols (i.e., S and C are compatible types).

        Args:
            message: Sequence of source symbols to encode

        Returns:
            The same sequence, unchanged

        Raises:
            ValueError: If the message is empty (optional validation)
        """
        # Cast is safe because we're returning the same sequence
        # and assuming S and C are compatible
        return message  # type: ignore

    def decode(self, encoded: Sequence[ChannelChar]) -> Sequence[SourceChar]:
        """
        Decode a message by returning it unchanged.

        This method assumes that the channel symbols can be used as
        source symbols (i.e., C and S are compatible types).

        Args:
            encoded: Sequence of channel symbols to decode

        Returns:
            The same sequence, unchanged

        Raises:
            ValueError: If the encoded sequence is empty
        """
        # Cast is safe because we're returning the same sequence
        # and assuming C and S are compatible
        return encoded  # type: ignore

    @property
    def code_table(self) -> Optional[Dict[SourceChar, Sequence[ChannelChar]]]:
        """
        Get the encoding table.

        The identity encoder has no code table, so this always returns None.

        Returns:
            None, as the identity encoder doesn't use a code table
        """
        return self._code_table
