# tests/test_interfaces.py
"""Tests for the interfaces module."""

import pytest
from codinglab.types import Message
from codinglab.interfaces import Encoder, Decoder, Sender, Channel, Receiver
from .conftest import MockEncoder, MockDecoder, MockSender, MockChannel, MockReceiver


class TestEncoder:
    """Tests for Encoder protocol."""

    def test_encoder_protocol_methods(self):
        """Test that Encoder protocol requires encode and code_table."""
        # This is a static test - the protocol defines the interface
        methods = dir(Encoder)
        assert "encode" in methods
        assert "code_table" in methods

    def test_mock_encoder_implements_protocol(self):
        """Test that MockEncoder satisfies the Encoder protocol."""
        encoder = MockEncoder()
        assert isinstance(encoder, Encoder)

    def test_encode_basic(self):
        """Test basic encoding functionality."""
        encoder = MockEncoder({0: "0", 1: "1"})
        result = encoder.encode([0, 1, 0])
        assert result == ["0", "1", "0"]

    def test_encode_with_variable_length_codes(self):
        """Test encoding with variable length code words."""
        code_table = {0: "0", 1: "10", 2: "110"}
        encoder = MockEncoder(code_table)
        result = encoder.encode([1, 0, 2])
        assert result == ["1", "0", "0", "1", "1", "0"]  # "10" + "0" + "110"

    def test_encode_invalid_symbol(self):
        """Test encoding with symbol not in code table."""
        encoder = MockEncoder({0: "0", 1: "1"})
        with pytest.raises(ValueError, match="Symbol not in alphabet"):
            encoder.encode([0, 2, 1])

    def test_code_table_property(self):
        """Test code_table property returns the encoding table."""
        code_table = {0: "0", 1: "1"}
        encoder = MockEncoder(code_table)
        assert encoder.code_table == code_table

    def test_code_table_optional(self):
        """Test that code_table can be None (in protocol, but not in MockEncoder)."""
        # The protocol allows None, but MockEncoder always has a table
        # This tests that the property exists and returns something
        encoder = MockEncoder()
        assert encoder.code_table is not None


class TestDecoder:
    """Tests for Decoder protocol."""

    def test_decoder_protocol_methods(self):
        """Test that Decoder protocol requires decode and code_table."""
        methods = dir(Decoder)
        assert "decode" in methods
        assert "code_table" in methods

    def test_mock_decoder_implements_protocol(self):
        """Test that MockDecoder satisfies the Decoder protocol."""
        decoder = MockDecoder()
        assert isinstance(decoder, Decoder)

    def test_decode_basic(self):
        """Test basic decoding functionality."""
        decoder = MockDecoder({0: "00", 1: "11"})
        result = decoder.decode(["0", "0", "1", "1", "0", "0"])
        assert result == [0, 1, 0]

    def test_decode_with_variable_length_codes(self):
        """Test decoding with variable length code words."""
        code_table = {0: "0", 1: "10", 2: "11"}
        decoder = MockDecoder(code_table)
        # "10" + "0" + "11"
        result = decoder.decode(["1", "0", "0", "1", "1"])
        assert result == [1, 0, 2]

    def test_decode_invalid_sequence(self):
        """Test decoding with invalid code sequence."""
        decoder = MockDecoder({0: "0", 1: "1"})
        with pytest.raises(ValueError, match="Invalid code sequence"):
            decoder.decode(["0", "2", "1"])

    def test_decode_unknown_code(self):
        """Test decoding with code not in reverse table."""
        decoder = MockDecoder({0: "0", 1: "10"})
        with pytest.raises(ValueError, match="Invalid code sequence"):
            decoder.decode(["1", "1"])  # "11" is not a valid code

    def test_code_table_property(self):
        """Test code_table property returns the encoding table."""
        code_table = {0: "0", 1: "1"}
        decoder = MockDecoder(code_table)
        assert decoder.code_table == code_table

    def test_encoder_decoder_compatibility(self):
        """Test that encoder and decoder work together."""
        code_table = {0: "0", 1: "10", 2: "11"}
        encoder = MockEncoder(code_table)
        decoder = MockDecoder(code_table)

        original = [1, 0, 2, 1]
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

        assert decoded == original


class TestSender:
    """Tests for Sender protocol."""

    def test_sender_protocol_methods(self):
        """Test that Sender protocol requires alphabet, message_stream, and get_last_message."""
        methods = dir(Sender)
        assert "alphabet" in methods
        assert "message_stream" in methods
        assert "get_last_message" in methods

    def test_mock_sender_implements_protocol(self):
        """Test that MockSender satisfies the Sender protocol."""
        sender = MockSender()
        assert isinstance(sender, Sender)

    def test_alphabet_property(self):
        """Test alphabet property returns the source alphabet."""
        alphabet = [0, 1, 2]
        sender = MockSender(alphabet)
        assert sender.alphabet == alphabet

    def test_message_stream_basic(self):
        """Test basic message stream generation."""
        sender = MockSender([0, 1])
        messages = list(sender.message_stream(3))

        assert len(messages) == 3
        assert all(isinstance(msg, Message) for msg in messages)
        assert all(isinstance(msg.data[0], str) for msg in messages)  # Encoded to str

    def test_message_stream_zero_or_negative(self):
        """Test message_stream with invalid stream_len."""
        sender = MockSender()

        with pytest.raises(ValueError, match="stream_len must be positive"):
            list(sender.message_stream(0))

        with pytest.raises(ValueError, match="stream_len must be positive"):
            list(sender.message_stream(-1))

    def test_message_stream_content(self):
        """Test content of generated messages."""
        sender = MockSender([0, 1])
        messages = list(sender.message_stream(3))

        # Check message IDs
        assert [msg.id for msg in messages] == [0, 1, 2]

        # Check that data is encoded (should be strings)
        assert all(isinstance(sym, str) for msg in messages for sym in msg.data)

    def test_get_last_message_before_generation(self):
        """Test get_last_message returns None before any messages generated."""
        sender = MockSender()
        assert sender.get_last_message() is None

    def test_get_last_message_after_generation(self):
        """Test get_last_message returns the last source message."""
        sender = MockSender([0, 1])
        list(sender.message_stream(3))  # Generate messages

        last = sender.get_last_message()
        assert last is not None
        assert isinstance(last, Message)
        assert isinstance(last.data[0], int)  # Source message has ints
        # Last message should have data length 3 (since i=2)
        assert len(last.data) == 3


class TestChannel:
    """Tests for Channel protocol."""

    def test_channel_protocol_methods(self):
        """Test that Channel protocol requires transmit_stream."""
        methods = dir(Channel)
        assert "transmit_stream" in methods

    def test_mock_channel_implements_protocol(self):
        """Test that MockChannel satisfies the Channel protocol."""
        channel = MockChannel()
        assert isinstance(channel, Channel)

    def test_transmit_stream_passthrough(self):
        """Test channel with no errors passes messages through unchanged."""
        channel = MockChannel(error_rate=0.0)
        messages = [
            Message(id=0, data=["0", "1", "0"]),
            Message(id=1, data=["1", "1", "0"]),
        ]

        transmitted = list(channel.transmit_stream(iter(messages)))

        assert len(transmitted) == 2
        assert transmitted[0].data == ["0", "1", "0"]
        assert transmitted[1].data == ["1", "1", "0"]
        assert transmitted[0].id == 0
        assert transmitted[1].id == 1

    def test_transmit_stream_with_errors(self):
        """Test channel introduces errors when error_rate > 0."""
        channel = MockChannel(error_rate=0.5)

        # Generate many messages to increase chance of error
        messages = [
            Message(id=i, data=["0"] * 10)  # All zeros
            for i in range(100)
        ]

        transmitted = list(channel.transmit_stream(iter(messages)))

        # Some messages should be corrupted (not all zeros)
        corrupted = [msg for msg in transmitted if any(sym != "0" for sym in msg.data)]
        assert len(corrupted) > 0

        # Check that corrupted messages still have same ID
        for orig, trans in zip(messages, transmitted):
            assert orig.id == trans.id

    def test_transmit_stream_preserves_iterator_state(self):
        """Test that transmit_stream works with any iterator."""
        channel = MockChannel()

        def message_generator():
            for i in range(3):
                yield Message(id=i, data=[str(i)])

        transmitted = list(channel.transmit_stream(message_generator()))
        assert len(transmitted) == 3


class TestReceiver:
    """Tests for Receiver protocol."""

    def test_receiver_protocol_methods(self):
        """Test that Receiver protocol requires __init__, receive_stream, and get_last_message."""
        methods = dir(Receiver)
        assert "__init__" in methods
        assert "receive_stream" in methods
        assert "get_last_message" in methods

    def test_mock_receiver_implements_protocol(self):
        """Test that MockReceiver satisfies the Receiver protocol."""
        decoder = MockDecoder()
        receiver = MockReceiver(decoder)
        assert isinstance(receiver, Receiver)

    def test_receiver_initialization(self):
        """Test receiver initialization with decoder."""
        decoder = MockDecoder()
        receiver = MockReceiver(decoder)
        assert receiver.decoder == decoder
        assert receiver.get_last_message() is None

    def test_receive_stream_successful(self):
        """Test receiving successfully decodable messages."""
        decoder = MockDecoder({0: "0", 1: "1"})
        receiver = MockReceiver(decoder)

        messages = [
            Message(id=0, data=["0", "1", "0"]),
            Message(id=1, data=["1", "1", "0"]),
        ]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [True, True]
        last = receiver.get_last_message()
        assert last is not None
        assert last.id == 1
        assert last.data == [1, 1, 0]

    def test_receive_stream_with_failures(self):
        """Test receiving messages that fail to decode."""
        decoder = MockDecoder({0: "0", 1: "1"})
        receiver = MockReceiver(decoder)

        messages = [
            Message(id=0, data=["0", "1", "0"]),  # Good
            Message(id=1, data=["2", "1", "0"]),  # Bad (contains "2")
            Message(id=2, data=["1", "1", "0"]),  # Good
        ]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [True, False, True]
        last = receiver.get_last_message()
        assert last is not None
        assert last.id == 2  # Last successful message

    def test_receive_stream_empty(self):
        """Test receiving empty stream."""
        decoder = MockDecoder()
        receiver = MockReceiver(decoder)

        results = list(receiver.receive_stream(iter([])))

        assert results == []
        assert receiver.get_last_message() is None

    def test_get_last_message_after_no_success(self):
        """Test get_last_message returns None when no messages succeeded."""
        decoder = MockDecoder({0: "0"})
        receiver = MockReceiver(decoder)

        messages = [
            Message(id=0, data=["1"]),  # Will fail (not in decoder)
            Message(id=1, data=["2"]),  # Will fail
        ]

        list(receiver.receive_stream(iter(messages)))

        assert receiver.get_last_message() is None


class TestIntegration:
    """Integration tests for the complete pipeline."""

    def test_full_pipeline_basic(self):
        """Test complete transmission pipeline with no errors."""
        # Setup
        code_table = {0: "0", 1: "1"}
        MockEncoder(code_table)
        decoder = MockDecoder(code_table)
        sender = MockSender([0, 1])
        channel = MockChannel(error_rate=0.0)
        receiver = MockReceiver(decoder)

        # Generate and transmit
        messages = list(sender.message_stream(5))
        transmitted = list(channel.transmit_stream(iter(messages)))
        results = list(receiver.receive_stream(iter(transmitted)))

        # Verify
        assert results == [True] * 5
        assert receiver.get_last_message() is not None

    def test_full_pipeline_with_errors(self):
        """Test complete transmission pipeline with channel errors."""
        # Setup
        code_table = {0: "00", 1: "11"}
        decoder = MockDecoder(code_table)
        sender = MockSender([0, 1])
        channel = MockChannel(error_rate=0.5)
        receiver = MockReceiver(decoder)

        # Generate and transmit
        messages = list(sender.message_stream(100))
        transmitted = list(channel.transmit_stream(iter(messages)))
        results = list(receiver.receive_stream(iter(transmitted)))

        # Verify some failures occurred
        assert any(results)  # At least one success
        assert not all(results)  # Not all succeeded

    def test_full_pipeline_preserves_message_order(self):
        """Test that message order is preserved through the pipeline."""
        code_table = {0: "0", 1: "1"}
        decoder = MockDecoder(code_table)
        sender = MockSender([0, 1])
        channel = MockChannel(error_rate=0.0)
        receiver = MockReceiver(decoder)

        messages = list(sender.message_stream(10))
        transmitted = list(channel.transmit_stream(iter(messages)))
        list(receiver.receive_stream(iter(transmitted)))

        # Check last message ID
        assert receiver.get_last_message().id == 9
