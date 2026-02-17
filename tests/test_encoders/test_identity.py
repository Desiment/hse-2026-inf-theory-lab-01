# tests/test_encoders/test_identity.py
"""Tests for the identity encoder module."""

import pytest

from codinglab.encoders.identity import IdentityEncoder


class TestIdentityEncoder:
    """Tests for IdentityEncoder."""

    @pytest.fixture
    def encoder(self):
        """Provide an IdentityEncoder instance."""
        return IdentityEncoder()

    def test_initialization(self, encoder):
        """Test encoder initialization."""
        assert encoder.code_table is None

    def test_encode_integers(self, encoder):
        """Test encoding a sequence of integers."""
        message = [1, 2, 3, 4, 5]
        encoded = encoder.encode(message)

        assert encoded == message
        assert encoded is message  # Should be the same object

    def test_encode_strings(self, encoder):
        """Test encoding a sequence of strings."""
        message = ["A", "B", "C", "D"]
        encoded = encoder.encode(message)

        assert encoded == message
        assert encoded is message

    def test_encode_mixed_types(self, encoder):
        """Test encoding a sequence with mixed types."""
        message = [1, "A", True, 3.14]
        encoded = encoder.encode(message)

        assert encoded == message
        assert encoded is message

    def test_encode_single_element(self, encoder):
        """Test encoding a single-element sequence."""
        message = [42]
        encoded = encoder.encode(message)

        assert encoded == [42]
        assert len(encoded) == 1

    def test_decode_integers(self, encoder):
        """Test decoding a sequence of integers."""
        encoded = [1, 2, 3, 4, 5]
        decoded = encoder.decode(encoded)

        assert decoded == encoded
        assert decoded is encoded

    def test_decode_strings(self, encoder):
        """Test decoding a sequence of strings."""
        encoded = ["A", "B", "C", "D"]
        decoded = encoder.decode(encoded)

        assert decoded == encoded
        assert decoded is encoded

    def test_decode_mixed_types(self, encoder):
        """Test decoding a sequence with mixed types."""
        encoded = [1, "A", True, 3.14]
        decoded = encoder.decode(encoded)

        assert decoded == encoded
        assert decoded is encoded

    def test_decode_single_element(self, encoder):
        """Test decoding a single-element sequence."""
        encoded = [42]
        decoded = encoder.decode(encoded)

        assert decoded == [42]
        assert len(decoded) == 1

    def test_encode_decode_roundtrip(self, encoder):
        """Test that encode then decode returns original message."""
        original = [1, 2, 3, 4, 5]
        encoded = encoder.encode(original)
        decoded = encoder.decode(encoded)

        assert decoded == original
        assert decoded is original  # Should be the same object

    def test_encode_decode_roundtrip_with_strings(self, encoder):
        """Test roundtrip with string messages."""
        original = ["Hello", "World", "!"]
        encoded = encoder.encode(original)
        decoded = encoder.decode(encoded)

        assert decoded == original
        assert decoded is original

    def test_encoder_implements_both_protocols(self, encoder):
        """Test that IdentityEncoder implements both Encoder and Decoder."""
        from codinglab.interfaces import Encoder, Decoder

        assert isinstance(encoder, Encoder)
        assert isinstance(encoder, Decoder)

    def test_encode_preserves_order(self, encoder):
        """Test that encoding preserves element order."""
        original = [5, 4, 3, 2, 1]
        encoded = encoder.encode(original)

        assert encoded == [5, 4, 3, 2, 1]
        assert encoded[0] == 5
        assert encoded[-1] == 1

    def test_decode_preserves_order(self, encoder):
        """Test that decoding preserves element order."""
        encoded = [5, 4, 3, 2, 1]
        decoded = encoder.decode(encoded)

        assert decoded == [5, 4, 3, 2, 1]
        assert decoded[0] == 5
        assert decoded[-1] == 1

    def test_with_nested_sequences(self, encoder):
        """Test encoding sequences containing other sequences."""
        message = [[1, 2], [3, 4], [5, 6]]
        encoded = encoder.encode(message)

        assert encoded == message
        assert encoded[0] == [1, 2]
        assert encoded[1] == [3, 4]
        assert encoded[2] == [5, 6]

    def test_with_boolean_values(self, encoder):
        """Test encoding boolean values."""
        message = [True, False, True, True]
        encoded = encoder.encode(message)

        assert encoded == [True, False, True, True]
        assert encoded[0] is True
        assert encoded[1] is False

    def test_code_table_property_always_none(self, encoder):
        """Test that code_table property always returns None."""
        assert encoder.code_table is None

        # Even after operations, should still be None
        encoder.encode([1, 2, 3])
        assert encoder.code_table is None

        encoder.decode([4, 5, 6])
        assert encoder.code_table is None

    def test_type_independence(self):
        """Test that encoder works with different type combinations."""
        # Int to int
        encoder1 = IdentityEncoder[int, int]()
        assert encoder1.encode([1, 2, 3]) == [1, 2, 3]

        # String to string
        encoder2 = IdentityEncoder[str, str]()
        assert encoder2.encode(["A", "B"]) == ["A", "B"]

        # Int to string (should work but might be semantically wrong)
        # This tests that the type system allows it, even if not recommended
        encoder3 = IdentityEncoder[int, str]()  # type: ignore
        result = encoder3.encode([1, 2, 3])
        assert result == [1, 2, 3]

    def test_large_sequences(self, encoder):
        """Test encoding large sequences."""
        message = list(range(1000))
        encoded = encoder.encode(message)

        assert len(encoded) == 1000
        assert encoded[0] == 0
        assert encoded[-1] == 999

    def test_multiple_encode_calls(self, encoder):
        """Test multiple encode calls on same encoder."""
        msg1 = [1, 2, 3]
        msg2 = [4, 5, 6]
        msg3 = [7, 8, 9]

        encoded1 = encoder.encode(msg1)
        encoded2 = encoder.encode(msg2)
        encoded3 = encoder.encode(msg3)

        assert encoded1 == msg1
        assert encoded2 == msg2
        assert encoded3 == msg3

        # Each should be the original object
        assert encoded1 is msg1
        assert encoded2 is msg2
        assert encoded3 is msg3
