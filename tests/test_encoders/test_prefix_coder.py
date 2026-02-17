# tests/test_encoders/test_prefix_encoder_decoder.py
"""Tests for the prefix encoder-decoder module."""

import pytest

from codinglab.encoders.prefix_code_tree import PrefixCodeTree
from codinglab.encoders.prefix_coder import PrefixEncoderDecoder


class TestPrefixEncoderDecoder:
    """Tests for PrefixEncoderDecoder abstract base class."""

    @pytest.fixture
    def concrete_encoder(self):
        """Create a concrete implementation for testing."""

        class TestEncoder(PrefixEncoderDecoder):
            def __init__(self, source_alphabet, channel_alphabet):
                super().__init__(source_alphabet, channel_alphabet)

            def _build_prefix_code_tree(self):
                # Build a simple fixed tree for testing
                self._tree = PrefixCodeTree()
                self._tree.insert_code(["0"], "A")
                self._tree.insert_code(["1", "0"], "B")
                self._tree.insert_code(["1", "1"], "C")

        return TestEncoder(["A", "B", "C"], ["0", "1"])

    def test_initialization_valid(self):
        """Test valid initialization."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._tree = PrefixCodeTree()

        encoder = TestEncoder(["A", "B"], ["0", "1"])

        assert encoder.source_alphabet == ["A", "B"]
        assert encoder.channel_alphabet == ["0", "1"]
        assert encoder._code_table is not None
        assert encoder._tree is not None

    def test_initialization_empty_source_alphabet(self):
        """Test initialization with empty source alphabet."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                pass

        with pytest.raises(ValueError, match="Source alphabet cannot be empty"):
            TestEncoder([], ["0", "1"])

    def test_initialization_empty_channel_alphabet(self):
        """Test initialization with empty channel alphabet."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                pass

        with pytest.raises(ValueError, match="Channel alphabet cannot be empty"):
            TestEncoder(["A", "B"], [])

    def test_build_table_from_tree(self, concrete_encoder):
        """Test building code table from tree."""
        encoder = concrete_encoder

        # _build_table_from_tree is called in __init__
        assert encoder._code_table is not None
        assert encoder._code_table["A"] == ["0"]
        assert encoder._code_table["B"] == ["1", "0"]
        assert encoder._code_table["C"] == ["1", "1"]

    def test_build_tree_from_table(self):
        """Test building tree from code table."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                # Build code table directly
                self._code_table = {"A": ["0"], "B": ["1", "0"], "C": ["1", "1"]}
                self._build_tree_from_table()

        encoder = TestEncoder(["A", "B", "C"], ["0", "1"])

        assert encoder._tree is not None
        # Test tree works for decoding
        assert encoder._tree.decode(["0"], 0)[0] == "A"
        assert encoder._tree.decode(["1", "0"], 0)[0] == "B"
        assert encoder._tree.decode(["1", "1"], 0)[0] == "C"

    def test_build_tree_from_empty_table_raises_error(self):
        """Test building tree from empty table raises error."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._code_table = None
                self._build_tree_from_table()

        with pytest.raises(
            RuntimeError, match="Cannot build tree from empty code table"
        ):
            TestEncoder(["A"], ["0", "1"])

    def test_build_table_from_empty_tree_raises_error(self):
        """Test building table from empty tree raises error."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._tree = None
                self._build_table_from_tree()

        with pytest.raises(RuntimeError, match="Cannot build table from empty tree"):
            TestEncoder(["A"], ["0", "1"])

    def test_encode_basic(self, concrete_encoder):
        """Test basic encoding."""
        encoder = concrete_encoder

        result = encoder.encode(["A", "B", "C"])
        assert result == ["0", "1", "0", "1", "1"]

    def test_encode_empty_message(self, concrete_encoder):
        """Test encoding empty message."""
        encoder = concrete_encoder

        result = encoder.encode([])
        assert result == []

    def test_encode_symbol_not_in_alphabet(self, concrete_encoder):
        """Test encoding symbol not in alphabet."""
        encoder = concrete_encoder

        with pytest.raises(ValueError, match="Symbol D not in source alphabet"):
            encoder.encode(["A", "D", "B"])

    def test_encode_without_code_table(self):
        """Test encoding when code table not built."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._tree = PrefixCodeTree()

        encoder = TestEncoder(["A"], ["0", "1"])

        with pytest.raises(RuntimeError, match="Code table not built"):
            encoder._code_table = None
            encoder.encode(["A"])

    def test_decode_basic(self, concrete_encoder):
        """Test basic decoding."""
        encoder = concrete_encoder

        result = encoder.decode(["0", "1", "0", "1", "1"])
        assert result == ["A", "B", "C"]

    def test_decode_empty_sequence(self, concrete_encoder):
        """Test decoding empty sequence."""
        encoder = concrete_encoder

        result = encoder.decode([])
        assert result == []

    def test_decode_invalid_sequence(self, concrete_encoder):
        """Test decoding invalid sequence."""
        encoder = concrete_encoder

        with pytest.raises(ValueError, match="Cannot decode sequence"):
            encoder.decode(["0", "1", "0", "1"])  # Incomplete last code

    def test_decode_without_tree(self):
        """Test decoding when tree not built."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._tree = PrefixCodeTree()

        encoder = TestEncoder(["A"], ["0", "1"])

        with pytest.raises(RuntimeError, match="Decoding tree not built"):
            encoder._tree = None
            encoder.decode(["0"])

    def test_code_table_property(self, concrete_encoder):
        """Test code_table property."""
        encoder = concrete_encoder

        table = encoder.code_table
        assert table is not None
        assert table["A"] == ["0"]
        assert table["B"] == ["1", "0"]
        assert table["C"] == ["1", "1"]

    def test_tree_property(self, concrete_encoder):
        """Test tree property."""
        encoder = concrete_encoder

        tree = encoder.tree
        assert tree is not None
        assert tree.decode(["0"], 0)[0] == "A"

    def test_source_alphabet_property(self, concrete_encoder):
        """Test source_alphabet property."""
        encoder = concrete_encoder

        assert encoder.source_alphabet == ["A", "B", "C"]

    def test_channel_alphabet_property(self, concrete_encoder):
        """Test channel_alphabet property."""
        encoder = concrete_encoder

        assert encoder.channel_alphabet == ["0", "1"]

    def test_encode_decode_roundtrip(self, concrete_encoder):
        """Test that encode then decode returns original message."""
        encoder = concrete_encoder

        original = ["A", "B", "C", "A", "B"]
        encoded = encoder.encode(original)
        decoded = encoder.decode(encoded)

        assert decoded == original

    def test_collect_codes_from_node(self):
        """Test recursive code collection from tree."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                # Build tree manually
                self._tree = PrefixCodeTree()
                self._tree.insert_code(["0"], "A")
                self._tree.insert_code(["1", "0"], "B")

        encoder = TestEncoder(["A", "B"], ["0", "1"])

        # Code table should have been built
        assert encoder._code_table is not None
        assert encoder._code_table["A"] == ["0"]
        assert encoder._code_table["B"] == ["1", "0"]

    def test_abstract_method_must_be_implemented(self):
        """Test that abstract method must be implemented."""

        class IncompleteEncoder(PrefixEncoderDecoder):
            pass  # Doesn't implement _build_prefix_code_tree

        with pytest.raises(TypeError):
            IncompleteEncoder(["A"], ["0", "1"])

    def test_multiple_calls_to_encode(self, concrete_encoder):
        """Test that encode can be called multiple times."""
        encoder = concrete_encoder

        result1 = encoder.encode(["A", "B"])
        result2 = encoder.encode(["C", "A"])

        assert result1 == ["0", "1", "0"]
        assert result2 == ["1", "1", "0"]

    def test_multiple_calls_to_decode(self, concrete_encoder):
        """Test that decode can be called multiple times."""
        encoder = concrete_encoder

        result1 = encoder.decode(["0", "1", "0"])
        result2 = encoder.decode(["1", "1", "0"])

        assert result1 == ["A", "B"]
        assert result2 == ["C", "A"]

    def test_encode_with_different_alphabets(self):
        """Test encoding with non-binary alphabets."""

        class TestEncoder(PrefixEncoderDecoder):
            def _build_prefix_code_tree(self):
                self._tree = PrefixCodeTree()
                self._tree.insert_code(["00"], "X")
                self._tree.insert_code(["01"], "Y")
                self._tree.insert_code(["10"], "Z")

        encoder = TestEncoder(["X", "Y", "Z"], ["00", "01", "10"])

        result = encoder.encode(["X", "Y", "Z"])
        assert result == ["00", "01", "10"]

        decoded = encoder.decode(result)
        assert decoded == ["X", "Y", "Z"]
