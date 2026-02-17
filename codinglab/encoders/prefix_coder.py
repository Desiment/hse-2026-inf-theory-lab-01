"""
Base class for prefix code encoder-decoders for the coding experiments library.

This module provides an abstract base class for implementing prefix codes,
which are variable-length codes where no codeword is a prefix of another.
This property enables unique decoding without separators between codewords.
Common examples include Huffman coding, Shannon-Fano coding, and others.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["PrefixEncoderDecoder"]

from typing import Sequence, Dict, Optional, List
from abc import ABC, abstractmethod
from .prefix_code_tree import PrefixCodeTree, TreeNode
from ..interfaces import Encoder, Decoder
from ..types import SourceChar, ChannelChar


class PrefixEncoderDecoder(
    Encoder[SourceChar, ChannelChar], Decoder[SourceChar, ChannelChar], ABC
):
    """
    Abstract base class for prefix code encoder-decoders.

    This class implements the common functionality for prefix codes,
    including encoding, decoding, and maintaining both a code table
    and a decoding tree. Concrete implementations must define how to
    build the prefix code tree based on their specific algorithm.

    Attributes:
        _source_alphabet: Alphabet of source symbols to encode
        _channel_alphabet: Alphabet of channel symbols for encoding
        _code_table: Mapping from source symbols to their code sequences
        _tree: Prefix code tree used for decoding
    """

    def __init__(
        self,
        source_alphabet: Sequence[SourceChar],
        channel_alphabet: Sequence[ChannelChar],
    ) -> None:
        """
        Initialize the prefix encoder-decoder with alphabets.

        Args:
            source_alphabet: Sequence of source symbols to be encoded
            channel_alphabet: Sequence of channel symbols available for encoding

        Raises:
            ValueError: If either alphabet is empty
        """
        if not source_alphabet:
            raise ValueError("Source alphabet cannot be empty")
        if not channel_alphabet:
            raise ValueError("Channel alphabet cannot be empty")

        self._source_alphabet = source_alphabet
        """Alphabet of source symbols to encode."""

        self._channel_alphabet = channel_alphabet
        """Alphabet of channel symbols for encoding."""

        self._code_table: Optional[Dict[SourceChar, Sequence[ChannelChar]]] = {}
        """Mapping from source symbols to their code sequences."""

        self._tree: Optional[PrefixCodeTree[ChannelChar, SourceChar]] = None
        """Prefix code tree used for decoding."""
        self._build_prefix_code_tree()
        self._build_table_from_tree()

    @abstractmethod
    def _build_prefix_code_tree(self) -> None:
        """
        Abstract method to build the prefix code tree.

        Concrete subclasses must implement this method to construct
        a prefix code tree according to their specific algorithm.
        The implementation should populate either _code_table or _tree,
        and then call the appropriate helper method to ensure both
        representations are available.
        """
        pass

    def _build_tree_from_table(self) -> None:
        """
        Build a decoding tree from the code table.

        This method constructs a prefix code tree by inserting each
        code sequence from the code table into the tree. After calling
        this method, the tree can be used for efficient decoding.

        Raises:
            RuntimeError: If the code table is empty or None
        """
        if self._code_table is None or not self._code_table:
            raise RuntimeError("Cannot build tree from empty code table")

        self._tree = PrefixCodeTree()
        for symbol, code in self._code_table.items():
            self._tree.insert_code(list(code), symbol)

    def _build_table_from_tree(self) -> None:
        """
        Build a code table from the decoding tree.

        This method traverses the prefix code tree and constructs a
        mapping from source symbols to their code sequences. After
        calling this method, the code table can be used for encoding.

        Raises:
            RuntimeError: If the tree is empty or None
        """
        if self._tree is None or self._tree.root is None:
            raise RuntimeError("Cannot build table from empty tree")

        self._code_table = {}
        self._collect_codes_from_node(self._tree.root, [])

    def _collect_codes_from_node(
        self, node: TreeNode[ChannelChar, SourceChar], current_code: List[ChannelChar]
    ) -> None:
        """
        Recursively collect code sequences from the tree.

        This helper method performs a depth-first traversal of the
        prefix code tree, building code sequences for each leaf node
        and storing them in the code table.

        Args:
            node: Current node in the tree traversal
            current_code: Code sequence accumulated so far

        Note:
            This method modifies self._code_table in place.
        """
        assert self._code_table is not None
        if node.value is not None:
            # Leaf node: store the accumulated code for this symbol
            self._code_table[node.value] = list(current_code)

        for char, child_node in node.children.items():
            # Recursively traverse child nodes
            self._collect_codes_from_node(child_node, current_code + [char])

    def encode(self, message: Sequence[SourceChar]) -> Sequence[ChannelChar]:
        """
        Encode a source message using the prefix code.

        Args:
            message: Sequence of source symbols to encode

        Returns:
            Sequence of channel symbols representing the encoded message

        Raises:
            RuntimeError: If the code table has not been built
            ValueError: If any symbol in the message is not in the source alphabet
        """
        if self._code_table is None or not self._code_table:
            raise RuntimeError("Code table not built")

        encoded: List[ChannelChar] = []
        for symbol in message:
            if symbol not in self._code_table.keys():
                raise ValueError(f"Symbol {symbol} not in source alphabet")
            encoded.extend(self._code_table[symbol])
        return encoded

    def decode(self, encoded: Sequence[ChannelChar]) -> Sequence[SourceChar]:
        """
        Decode a sequence of channel symbols using the prefix code tree.

        Args:
            encoded: Sequence of channel symbols to decode

        Returns:
            Sequence of source symbols representing the decoded message

        Raises:
            RuntimeError: If the decoding tree has not been built
            ValueError: If the encoded sequence cannot be decoded
        """
        if self._tree is None:
            raise RuntimeError("Decoding tree not built")

        position = 0
        decoded = []
        encoded_list = list(encoded)

        while position < len(encoded_list):
            symbol, new_position = self._tree.decode(encoded_list, position)
            if symbol is None:
                raise ValueError(
                    f"Cannot decode sequence {encoded}. Processed to {position}"
                )
            decoded.append(symbol)
            position = new_position

        return decoded

    @property
    def code_table(self) -> Optional[Dict[SourceChar, Sequence[ChannelChar]]]:
        """
        Get the encoding table if available.

        Returns:
            Dictionary mapping source symbols to their code sequences,
            or None if no code table has been built
        """
        return self._code_table

    @property
    def tree(self) -> Optional[PrefixCodeTree[ChannelChar, SourceChar]]:
        """
        Get the decoding tree if available.

        Returns:
            Prefix code tree used for decoding, or None if no tree
            has been built
        """
        return self._tree

    @property
    def source_alphabet(self) -> Sequence[SourceChar]:
        """
        Get the source alphabet.

        Returns:
            Sequence of source symbols that can be encoded
        """
        return self._source_alphabet

    @property
    def channel_alphabet(self) -> Sequence[ChannelChar]:
        """
        Get the channel alphabet.

        Returns:
            Sequence of channel symbols available for encoding
        """
        return self._channel_alphabet
