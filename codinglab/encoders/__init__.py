"""
Encoder implementations for the coding experiments library.

This module provides encoder implementations for converting source symbols
into channel symbols. It includes identity encoders, prefix code encoders,
and the data structures needed for tree-based decoding.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__description__ = "Encoder implementations for coding experiments"

# Re-export encoder implementations
from .identity import IdentityEncoder as IdentityEncoder
from .prefix_coder import PrefixEncoderDecoder as PrefixEncoderDecoder
from .prefix_code_tree import (
    PrefixCodeTree as PrefixCodeTree,
    TreeNode as TreeNode,
)

__all__ = [
    "IdentityEncoder",
    "PrefixEncoderDecoder",
    "PrefixCodeTree",
    "TreeNode",
]
