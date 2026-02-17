"""
Prefix code tree data structure for the coding experiments library.

This module implements a prefix code tree (also known as a decoding tree
or code tree) used for efficient decoding of prefix codes. The tree
enables unique decoding of variable-length codes without separators
between codewords.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["TreeNode", "PrefixCodeTree"]

from typing import Dict, Generic, Optional, List, Tuple
from graphviz import Digraph
from dataclasses import dataclass, field
from ..types import SourceChar, ChannelChar


@dataclass(kw_only=True)
class TreeNode(Generic[ChannelChar, SourceChar]):
    """
    Node in a prefix code tree.
    Each node in the tree represents either:

    - An internal node (value is None): has children for possible next symbols in a code sequence
    - A leaf node (value is not None): represents a complete code for a source symbol

    Attributes:
        value: Source symbol at this node (None for internal nodes)
        children: Dictionary mapping channel symbols to child nodes
    """

    value: Optional[SourceChar] = None
    """Source symbol at this node, or None for internal nodes."""

    children: Dict[ChannelChar, "TreeNode[ChannelChar, SourceChar]"] = field(
        default_factory=dict
    )
    """Dictionary mapping channel symbols to child nodes."""

    def leaf(self) -> bool:
        """
        Check if this node is a leaf node.

        A leaf node has no children, meaning it represents a complete
        code for a source symbol.

        Returns:
            True if this node has no children (is a leaf),
            False otherwise (is an internal node)
        """
        return len(self.children.items()) == 0


class PrefixCodeTree(Generic[ChannelChar, SourceChar]):
    """
    Prefix code tree for efficient decoding.

    This tree data structure enables decoding of prefix codes by
    traversing from the root to leaves based on the input sequence.
    Each leaf corresponds to a source symbol, and the path from root
    to leaf defines the code for that symbol.

    Attributes:
        root: Root node of the prefix code tree
    """

    def __init__(
        self, root: Optional[TreeNode[ChannelChar, SourceChar]] = None
    ) -> None:
        """
        Initialize a prefix code tree.

        Args:
            root: Optional root node for the tree. If None, creates
                  a new empty root node.
        """
        self.root = TreeNode() if root is None else root
        """Root node of the prefix code tree."""

    def insert_code(self, code: List[ChannelChar], symbol: SourceChar) -> None:
        """
        Insert a code sequence into the tree.

        This method builds the tree by adding a path from the root
        corresponding to the code sequence, ending with a leaf node
        containing the source symbol.

        Args:
            code: Sequence of channel symbols representing the code
            symbol: Source symbol that this code represents

        Raises:
            ValueError: If the code conflicts with existing codes
                       (violates prefix property)
        """
        node = self.root
        # Traverse the tree following the code sequence
        for char in code:
            if char not in node.children.keys():
                # Create new internal node if path doesn't exist
                node.children[char] = TreeNode()
            # Move to child node
            node = node.children[char]

            # Check for prefix violation: if we encounter a leaf
            # before finishing the code, this code is a prefix of
            # an existing code
            if node.value is not None:
                raise ValueError(
                    f"Code prefix conflict: {code} is a prefix of existing code for {node.value}"
                )

        # Check for prefix violation: if node has children,
        # an existing code is a prefix of this new code
        if node.children:
            raise ValueError(
                f"Code prefix conflict: existing code is a prefix of new code for {symbol}"
            )

        # Set the leaf node value to the source symbol
        node.value = symbol

    def decode(
        self, sequence: List[ChannelChar], position: int = 0
    ) -> Tuple[Optional[SourceChar], int]:
        """
        Decode a symbol from a sequence starting at the given position.

        This method traverses the tree from the root, following
        symbols from the sequence until it reaches a leaf node.
        It returns the decoded symbol and the new position in the
        sequence (after consuming the code).

        Args:
            sequence: List of channel symbols to decode
            position: Starting position in the sequence (default: 0)

        Returns:
            Tuple of (decoded_symbol, new_position) where:
            - decoded_symbol: Source symbol decoded, or None if decoding failed
            - new_position: Position in sequence after consuming the code

        Raises:
            ValueError: If the sequence is incomplete or contains
                       symbols not in the tree
        """
        node = self.root

        # Traverse the tree until we reach a leaf
        while not node.leaf():
            if position >= len(sequence):
                raise ValueError(
                    f"Cannot decode sequence {sequence} at position {position}: sequence incomplete"
                )

            current_symbol = sequence[position]

            if current_symbol not in node.children:
                raise ValueError(
                    f"Cannot decode sequence {sequence} at position {position}: symbol '{current_symbol}' not in tree"
                )

            # Move to child node and advance position
            node = node.children[current_symbol]
            position += 1

        # Return the leaf value and current position
        return node.value, position

    def vizualize(self) -> Digraph:  # codespell:ignore vizualize
        dot = Digraph()

        def add(n: TreeNode[ChannelChar, SourceChar], idx: str):
            dot.node(idx, str(n.value) if n.value else "")
            for char, child in n.children.items():
                cidx = f"{idx}_{char}"
                dot.edge(idx, cidx, label=str(char))
                add(child, cidx)

        add(self.root, "r")
        return dot
