# tests/test_senders/test_fixed_messages.py
"""Tests for the fixed messages sender module."""

import pytest
from typing import Sequence

from codinglab.types import TransmissionEvent
from codinglab.logger import PlainLogger, NullLogger
from codinglab.senders.fixed import FixedMessagesSender


class TestFixedMessagesSender:
    """Tests for FixedMessagesSender."""

    @pytest.fixture
    def simple_encoder(self):
        """Simple encoder for testing."""

        class SimpleEncoder:
            def encode(self, data: Sequence[int]) -> Sequence[str]:
                return [str(x) for x in data]

            @property
            def code_table(self):
                return {1: "1", 2: "2", 3: "3"}

        return SimpleEncoder()

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [[1, 2, 3], [4, 5], [6, 7, 8, 9]]

    def test_initialization_valid(self, simple_encoder, sample_messages):
        """Test valid initialization."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)
        assert sender._encoder == simple_encoder
        assert sender._messages == sample_messages
        assert sender._message_id == 0
        assert sender._index == 0
        assert isinstance(sender._logger, NullLogger)

    def test_initialization_with_logger(self, simple_encoder, sample_messages):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        sender = FixedMessagesSender(simple_encoder, sample_messages, logger=logger)
        assert sender._logger == logger

    def test_initialization_empty_messages_raises_error(self, simple_encoder):
        """Test that empty messages list raises ValueError."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            FixedMessagesSender(simple_encoder, [])

    def test_message_stream_default_length(self, simple_encoder, sample_messages):
        """Test message_stream with default length."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        messages = list(sender.message_stream())  # No arg = use list length

        assert len(messages) == len(sample_messages)
        assert messages[0].id == 0
        assert messages[0].data == ["1", "2", "3"]  # Encoded
        assert messages[1].id == 1
        assert messages[1].data == ["4", "5"]
        assert messages[2].id == 2
        assert messages[2].data == ["6", "7", "8", "9"]

    def test_message_stream_explicit_length(self, simple_encoder, sample_messages):
        """Test message_stream with explicit length."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        messages = list(sender.message_stream(5))

        assert len(messages) == 5
        # Should wrap around: 0,1,2,0,1
        assert messages[0].id == 0
        assert messages[0].data == ["1", "2", "3"]
        assert messages[1].id == 1
        assert messages[1].data == ["4", "5"]
        assert messages[2].id == 2
        assert messages[2].data == ["6", "7", "8", "9"]
        assert messages[3].id == 3
        assert messages[3].data == ["1", "2", "3"]  # Wrapped to first message
        assert messages[4].id == 4
        assert messages[4].data == ["4", "5"]  # Wrapped to second message

    def test_message_stream_zero_length_raises_error(
        self, simple_encoder, sample_messages
    ):
        """Test message_stream with zero length."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        with pytest.raises(ValueError, match="stream_len must be positive, got 0"):
            list(sender.message_stream(0))

    def test_message_stream_negative_length_raises_error(
        self, simple_encoder, sample_messages
    ):
        """Test message_stream with negative length."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        with pytest.raises(ValueError, match="stream_len must be positive, got -3"):
            list(sender.message_stream(-3))

    def test_message_stream_updates_last_message(self, simple_encoder, sample_messages):
        """Test that _last_message is updated correctly."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        assert sender.get_last_message() is None

        list(sender.message_stream(2))

        last = sender.get_last_message()
        assert last is not None
        assert last.id == 1
        assert last.data == [4, 5]  # Source message, not encoded

    def test_message_stream_logs_events(self, simple_encoder, sample_messages):
        """Test that source generation and encoding events are logged."""
        logger = PlainLogger()
        sender = FixedMessagesSender(simple_encoder, sample_messages, logger=logger)

        list(sender.message_stream(2))

        assert len(logger.logs) == 4  # 2 messages * (SOURCE_GENERATED + ENCODED)

        # Check first message events
        assert logger.logs[0].event == TransmissionEvent.SOURCE_GENERATED
        assert logger.logs[0].message.id == 0
        assert logger.logs[0].message.data == [1, 2, 3]

        assert logger.logs[1].event == TransmissionEvent.ENCODED
        assert logger.logs[1].message.id == 0
        assert logger.logs[1].message.data == ["1", "2", "3"]

        # Check second message events
        assert logger.logs[2].event == TransmissionEvent.SOURCE_GENERATED
        assert logger.logs[2].message.id == 1
        assert logger.logs[2].message.data == [4, 5]

        assert logger.logs[3].event == TransmissionEvent.ENCODED
        assert logger.logs[3].message.id == 1
        assert logger.logs[3].message.data == ["4", "5"]

    def test_reset(self, simple_encoder, sample_messages):
        """Test reset method returns sender to initial state."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        # Generate some messages
        list(sender.message_stream(5))
        assert sender._index == 2  # After 5 messages with 3-item list: 5 % 3 = 2
        assert sender._message_id == 5

        # Reset
        sender.reset()
        assert sender._index == 0
        assert sender._message_id == 0

    def test_reset_affects_subsequent_streams(self, simple_encoder, sample_messages):
        """Test that reset affects subsequent message streams."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        # First stream
        messages1 = list(sender.message_stream(2))
        assert messages1[0].id == 0
        assert messages1[0].data == ["1", "2", "3"]
        assert messages1[1].id == 1
        assert messages1[1].data == ["4", "5"]

        # Reset
        sender.reset()

        # Second stream should start from beginning
        messages2 = list(sender.message_stream(2))
        assert messages2[0].id == 0  # IDs reset too
        assert messages2[0].data == ["1", "2", "3"]
        assert messages2[1].id == 1
        assert messages2[1].data == ["4", "5"]

    def test_message_stream_preserves_order(self, simple_encoder, sample_messages):
        """Test that messages are sent in the correct order."""
        sender = FixedMessagesSender(simple_encoder, sample_messages)

        messages = list(sender.message_stream(7))

        # Check source message order (by checking encoded data)
        expected_pattern = [
            ["1", "2", "3"],  # Message 0
            ["4", "5"],  # Message 1
            ["6", "7", "8", "9"],  # Message 2
            ["1", "2", "3"],  # Message 3 (wrap)
            ["4", "5"],  # Message 4
            ["6", "7", "8", "9"],  # Message 5
            ["1", "2", "3"],  # Message 6
        ]

        for i, msg in enumerate(messages):
            assert msg.data == expected_pattern[i]

    def test_message_stream_with_single_message(self, simple_encoder):
        """Test with a single message in the list."""
        messages = [[42, 43, 44]]
        sender = FixedMessagesSender(simple_encoder, messages)

        result = list(sender.message_stream(5))

        assert len(result) == 5
        for i, msg in enumerate(result):
            assert msg.id == i
            assert msg.data == ["42", "43", "44"]
