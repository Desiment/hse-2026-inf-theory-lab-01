# tests/test_receivers/test_base.py
"""Tests for the base receiver module."""

import pytest

from codinglab.types import Message, TransmissionEvent
from codinglab.logger import PlainLogger, NullLogger
from codinglab.receivers.base import BaseReceiver


class TestBaseReceiver:
    """Tests for BaseReceiver."""

    @pytest.fixture
    def success_decoder(self):
        """Decoder that always succeeds."""

        class SuccessDecoder:
            def decode(self, data):
                return [x * 2 for x in data]  # Simple transformation

            @property
            def code_table(self):
                return None

        return SuccessDecoder()

    @pytest.fixture
    def failing_decoder(self):
        """Decoder that always fails."""

        class FailingDecoder:
            def decode(self, data):
                raise ValueError("Decoding failed")

            @property
            def code_table(self):
                return None

        return FailingDecoder()

    def test_initialization_default_logger(self, success_decoder):
        """Test initialization with default NullLogger."""
        receiver = BaseReceiver(success_decoder)
        assert receiver._decoder == success_decoder
        assert receiver._last_decoded is None
        assert isinstance(receiver._logger, NullLogger)

    def test_initialization_with_custom_logger(self, success_decoder):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        receiver = BaseReceiver(success_decoder, logger=logger)
        assert receiver._logger == logger

    def test_receive_stream_success(self, success_decoder):
        """Test successful message reception and decoding."""
        logger = PlainLogger()
        receiver = BaseReceiver(success_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [True, True]
        assert receiver._last_decoded is not None
        assert receiver._last_decoded.id == 1
        assert receiver._last_decoded.data == [8, 10, 12]  # 4*2, 5*2, 6*2

    def test_receive_stream_failure(self, failing_decoder):
        """Test failed message decoding."""
        logger = PlainLogger()
        receiver = BaseReceiver(failing_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [False, False]
        assert receiver._last_decoded is None

    def test_receive_stream_mixed_success_failure(
        self, success_decoder, failing_decoder
    ):
        """Test mix of successful and failed decodings."""

        # Using a decoder that fails for odd message IDs
        class MixedDecoder:
            def decode(self, data):
                if data and data[0] % 2 == 0:  # Even first element succeeds
                    return [x * 2 for x in data]
                raise ValueError("Decoding failed")

            @property
            def code_table(self):
                return None

        receiver = BaseReceiver(MixedDecoder())

        messages = [
            Message(id=0, data=[2, 4, 6]),  # Should succeed
            Message(id=1, data=[1, 3, 5]),  # Should fail
            Message(id=2, data=[8, 10, 12]),  # Should succeed
        ]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [True, False, True]
        assert receiver._last_decoded is not None
        assert receiver._last_decoded.id == 2
        assert receiver._last_decoded.data == [16, 20, 24]

    def test_receive_stream_logs_events(self, success_decoder):
        """Test that reception and decoding events are logged."""
        logger = PlainLogger()
        receiver = BaseReceiver(success_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        assert len(logger.logs) == 2
        # Should have: RECEIVED, DECODED
        events = [log.event for log in logger.logs]
        assert TransmissionEvent.RECEIVED in events
        assert TransmissionEvent.DECODED in events

    def test_receive_stream_logs_errors(self, failing_decoder):
        """Test that errors are logged."""
        logger = PlainLogger()
        receiver = BaseReceiver(failing_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        assert len(logger.logs) == 2  # RECEIVED, ERROR
        assert logger.logs[0].event == TransmissionEvent.RECEIVED
        assert logger.logs[1].event == TransmissionEvent.ERROR
        assert "error" in logger.logs[1].data
        assert logger.logs[1].data["error_type"] == "ValueError"

    def test_receive_stream_empty(self, success_decoder):
        """Test with empty message stream."""
        receiver = BaseReceiver(success_decoder)
        results = list(receiver.receive_stream(iter([])))
        assert results == []
        assert receiver._last_decoded is None

    def test_get_last_message_initial(self, success_decoder):
        """Test get_last_message returns None initially."""
        receiver = BaseReceiver(success_decoder)
        assert receiver.get_last_message() is None

    def test_get_last_message_after_success(self, success_decoder):
        """Test get_last_message returns last successful message."""
        receiver = BaseReceiver(success_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(receiver.receive_stream(iter(messages)))

        last = receiver.get_last_message()
        assert last is not None
        assert last.id == 1
        assert last.data == [8, 10, 12]

    def test_get_last_message_after_failure(self, failing_decoder):
        """Test get_last_message remains None after all failures."""
        receiver = BaseReceiver(failing_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(receiver.receive_stream(iter(messages)))

        assert receiver.get_last_message() is None
