# tests/test_encoders/test_prefix_code_tree.py
"""Tests for the prefix code tree module."""

import pytest

from codinglab.encoders.prefix_code_tree import TreeNode, PrefixCodeTree


class TestTreeNode:
    """Tests for TreeNode class."""

    def test_initialization_default(self):
        """Test default initialization."""
        node = TreeNode()
        assert node.value is None
        assert node.children == {}

    def test_initialization_with_value(self):
        """Test initialization with a value."""
        node = TreeNode(value="A")
        assert node.value == "A"
        assert node.children == {}

    def test_initialization_with_children(self):
        """Test initialization with children."""
        child = TreeNode(value="B")
        node = TreeNode(children={"0": child})
        assert node.value is None
        assert "0" in node.children
        assert node.children["0"] == child

    def test_leaf_method_with_no_children(self):
        """Test leaf() returns True when node has no children."""
        node = TreeNode(value="A")
        assert node.leaf() is True

    def test_leaf_method_with_children(self):
        """Test leaf() returns False when node has children."""
        node = TreeNode()
        node.children["0"] = TreeNode()
        assert node.leaf() is False

    def test_leaf_method_internal_node_with_value(self):
        """Test leaf() returns False for internal node with value (shouldn't happen in valid tree)."""
        node = TreeNode(value="A")
        node.children["0"] = TreeNode()
        assert node.leaf() is False


class TestPrefixCodeTree:
    """Tests for PrefixCodeTree class."""

    @pytest.fixture
    def empty_tree(self):
        """Provide an empty prefix code tree."""
        return PrefixCodeTree()

    @pytest.fixture
    def simple_tree(self):
        """Provide a tree with some basic codes."""
        tree = PrefixCodeTree()
        tree.insert_code(["0"], "A")
        tree.insert_code(["1", "0"], "B")
        tree.insert_code(["1", "1"], "C")
        return tree

    def test_initialization_without_root(self):
        """Test initialization without providing root."""
        tree = PrefixCodeTree()
        assert tree.root is not None
        assert tree.root.value is None
        assert tree.root.children == {}

    def test_initialization_with_root(self):
        """Test initialization with custom root."""
        root = TreeNode(value="root")
        tree = PrefixCodeTree(root=root)
        assert tree.root == root
        assert tree.root.value == "root"

    def test_insert_code_single_symbol(self, empty_tree):
        """Test inserting a single-symbol code."""
        empty_tree.insert_code(["0"], "A")

        assert "0" in empty_tree.root.children
        assert empty_tree.root.children["0"].value == "A"
        assert empty_tree.root.children["0"].leaf() is True

    def test_insert_code_multi_symbol(self, empty_tree):
        """Test inserting a multi-symbol code."""
        empty_tree.insert_code(["1", "0", "1"], "B")

        # Check path exists
        node = empty_tree.root
        assert "1" in node.children
        node = node.children["1"]
        assert "0" in node.children
        node = node.children["0"]
        assert "1" in node.children
        node = node.children["1"]
        assert node.value == "B"
        assert node.leaf() is True

    def test_insert_multiple_codes(self, simple_tree):
        """Test inserting multiple codes."""
        # A: "0"
        assert "0" in simple_tree.root.children
        assert simple_tree.root.children["0"].value == "A"

        # B: "10"
        assert "1" in simple_tree.root.children
        node = simple_tree.root.children["1"]
        assert "0" in node.children
        assert node.children["0"].value == "B"

        # C: "11"
        assert "1" in node.children
        assert "1" in node.children
        assert node.children["1"].value == "C"

    def test_insert_code_prefix_conflict_new_is_prefix_of_existing(self, simple_tree):
        """Test inserting a code that is a prefix of existing code."""
        # "1" is a prefix of existing "10" and "11"
        with pytest.raises(ValueError, match="prefix conflict"):
            simple_tree.insert_code(["1"], "D")

    def test_insert_code_prefix_conflict_existing_is_prefix_of_new(self, simple_tree):
        """Test inserting a code where existing code is prefix of new."""
        # "0" is already a complete code for A, can't add "01"
        with pytest.raises(ValueError, match="prefix conflict"):
            simple_tree.insert_code(["0", "1"], "D")

    def test_decode_single_symbol(self, simple_tree):
        """Test decoding a single symbol."""
        sequence = ["0", "1", "0"]
        symbol, new_pos = simple_tree.decode(sequence, 0)

        assert symbol == "A"
        assert new_pos == 1

    def test_decode_multi_symbol(self, simple_tree):
        """Test decoding a multi-symbol code."""
        sequence = ["1", "0", "1"]
        symbol, new_pos = simple_tree.decode(sequence, 0)

        assert symbol == "B"
        assert new_pos == 2

    def test_decode_multiple_codes_in_sequence(self, simple_tree):
        """Test decoding multiple codes from a sequence."""
        sequence = ["0", "1", "0", "1", "1"]

        pos = 0
        symbols = []
        while pos < len(sequence):
            symbol, pos = simple_tree.decode(sequence, pos)
            symbols.append(symbol)

        assert symbols == ["A", "B", "C"]

    def test_decode_with_offset(self, simple_tree):
        """Test decoding starting from a position."""
        sequence = ["x", "x", "0", "1", "0"]  # Skip first two

        symbol, new_pos = simple_tree.decode(sequence, 2)

        assert symbol == "A"
        assert new_pos == 3

    def test_decode_incomplete_sequence(self, simple_tree):
        """Test decoding with incomplete sequence."""
        sequence = ["1"]  # Incomplete code

        with pytest.raises(ValueError, match="sequence incomplete"):
            simple_tree.decode(sequence, 0)

    def test_decode_invalid_symbol(self, simple_tree):
        """Test decoding with invalid symbol."""
        sequence = ["2"]  # '2' not in tree

        with pytest.raises(ValueError, match="symbol '2' not in tree"):
            simple_tree.decode(sequence, 0)

    def test_decode_empty_sequence(self, simple_tree):
        """Test decoding empty sequence."""
        sequence = []

        with pytest.raises(ValueError, match="sequence incomplete"):
            simple_tree.decode(sequence, 0)

    def test_vizualize_returns_digraph(self, simple_tree):
        """Test that vizualize returns a Digraph object."""
        dot = simple_tree.vizualize()

        # Check that it's a graphviz object
        assert dot.name is None
        assert hasattr(dot, "node")
        assert hasattr(dot, "edge")
