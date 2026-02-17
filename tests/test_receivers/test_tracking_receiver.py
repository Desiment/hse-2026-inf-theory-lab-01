# tests/test_receivers/test_tracking.py
"""Tests for the tracking receiver module."""

import pytest

from codinglab.types import Message, TransmissionEvent
from codinglab.logger import PlainLogger, NullLogger
from codinglab.receivers.tracking import TrackingReceiver, TransmissionStats


class TestTransmissionStats:
    """Tests for TransmissionStats dataclass."""

    def test_initialization_defaults(self):
        """Test default initialization values."""
        stats = TransmissionStats()

        assert stats.total_messages == 0
        assert stats.successful_messages == 0
        assert stats.decoded_messages == 0
        assert stats.failed_messages == 0
        assert stats.total_source_symbols == 0
        assert stats.total_channel_symbols == 0
        assert stats.decode_errors == 0
        assert stats.validation_errors == 0
        assert stats.total_processing_time == 0.0
        assert stats.avg_message_time == 0.0

    def test_success_rate_with_no_messages(self):
        """Test success_rate when no messages processed."""
        stats = TransmissionStats()
        assert stats.success_rate == 0.0

    def test_success_rate_with_messages(self):
        """Test success_rate calculation."""
        stats = TransmissionStats(total_messages=10, successful_messages=7)
        assert stats.success_rate == 0.7

    def test_compression_ratio_with_no_channel_symbols(self):
        """Test compression_ratio when no channel symbols."""
        stats = TransmissionStats()
        assert stats.compression_ratio == 0.0

    def test_compression_ratio_with_symbols(self):
        """Test compression_ratio calculation."""
        stats = TransmissionStats(total_source_symbols=100, total_channel_symbols=80)
        assert stats.compression_ratio == 1.25  # 100/80 = 1.25

    def test_average_code_len_with_no_source_symbols(self):
        """Test average_code_len when no source symbols."""
        stats = TransmissionStats()
        assert stats.average_code_len == 0.0

    def test_average_code_len_with_symbols(self):
        """Test average_code_len calculation."""
        stats = TransmissionStats(total_source_symbols=50, total_channel_symbols=75)
        assert stats.average_code_len == 1.5  # 75/50 = 1.5


class TestTrackingReceiver:
    """Tests for TrackingReceiver."""

    @pytest.fixture
    def identity_decoder(self):
        """Decoder that returns input unchanged."""

        class IdentityDecoder:
            def decode(self, data):
                return data

            @property
            def code_table(self):
                return None

        return IdentityDecoder()

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

    @pytest.fixture
    def checking_logger(self):
        """Logger with check_message method."""

        class CheckingLogger(PlainLogger):
            def check_message(self, message):
                # Consider messages with even IDs as correct
                return message.id % 2 == 0

        return CheckingLogger()

    def test_initialization_default_logger(self, identity_decoder):
        """Test initialization with default NullLogger."""
        receiver = TrackingReceiver(identity_decoder)

        assert receiver._decoder == identity_decoder
        assert receiver._last_message is None
        assert isinstance(receiver._logger, NullLogger)
        assert isinstance(receiver._stats, TransmissionStats)

    def test_initialization_with_custom_logger(self, identity_decoder):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        receiver = TrackingReceiver(identity_decoder, logger=logger)

        assert receiver._logger == logger

    def test_receive_stream_success(self, identity_decoder):
        """Test successful message reception and decoding."""
        receiver = TrackingReceiver(identity_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [True, True]
        assert receiver._last_message is not None
        assert receiver._last_message.id == 1
        assert receiver._last_message.data == [4, 5, 6]

    def test_receive_stream_failure(self, failing_decoder):
        """Test failed message decoding."""
        receiver = TrackingReceiver(failing_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        results = list(receiver.receive_stream(iter(messages)))

        assert results == [False, False]
        assert receiver._last_message is None

    def test_receive_stream_stats_success(self, identity_decoder):
        """Test stats update on successful decoding."""
        receiver = TrackingReceiver(identity_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5])]

        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_messages == 2
        assert stats.decoded_messages == 2
        assert stats.total_source_symbols == 5  # 3 + 2
        assert stats.total_channel_symbols == 5  # 3 + 2
        assert stats.decode_errors == 0
        assert stats.total_processing_time >= 0

    def test_receive_stream_stats_failure(self, failing_decoder):
        """Test stats update on failed decoding."""
        receiver = TrackingReceiver(failing_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_messages == 2
        assert stats.decoded_messages == 0
        assert stats.total_source_symbols == 0
        assert stats.total_channel_symbols == 0
        assert stats.decode_errors == 2
        assert stats.total_processing_time >= 0

    def test_receive_stream_logs_events(self, identity_decoder):
        """Test that reception and decoding events are logged."""
        logger = PlainLogger()
        receiver = TrackingReceiver(identity_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        assert len(logger.logs) == 2  # RECEIVED and DECODED
        assert logger.logs[0].event == TransmissionEvent.RECEIVED
        assert logger.logs[1].event == TransmissionEvent.DECODED

    def test_receive_stream_logs_errors(self, failing_decoder):
        """Test that errors are logged."""
        logger = PlainLogger()
        receiver = TrackingReceiver(failing_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        assert len(logger.logs) == 2  # RECEIVED and ERROR
        assert logger.logs[0].event == TransmissionEvent.RECEIVED
        assert logger.logs[1].event == TransmissionEvent.ERROR
        assert "error" in logger.logs[1].data
        assert logger.logs[1].data["error_type"] == "ValueError"

    def test_get_stats_returns_copy(self, identity_decoder):
        """Test that get_stats returns a copy that doesn't affect internal stats."""
        receiver = TrackingReceiver(identity_decoder)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_messages == 1

        # Modify the returned stats
        stats.total_messages = 999

        # Internal stats should be unchanged
        assert receiver._stats.total_messages == 1

    def test_reset_stats(self, identity_decoder):
        """Test reset_stats clears all statistics."""
        receiver = TrackingReceiver(identity_decoder)

        messages = [Message(id=0, data=[1, 2, 3])]
        list(receiver.receive_stream(iter(messages)))

        assert receiver._stats.total_messages == 1

        receiver.reset_stats()

        stats = receiver.get_stats()
        assert stats.total_messages == 0
        assert stats.decoded_messages == 0
        assert stats.total_source_symbols == 0
        assert stats.total_channel_symbols == 0
        assert stats.total_processing_time == 0.0

    def test_avg_message_time_calculation(self, identity_decoder):
        """Test average message time calculation."""
        receiver = TrackingReceiver(identity_decoder)

        # Process messages with artificial delay
        messages = [Message(id=i, data=[i + 1]) for i in range(200)]

        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_processing_time >= 0
        assert stats.avg_message_time == stats.total_processing_time / 200

    def test_successful_messages_with_checking_logger(
        self, identity_decoder, checking_logger
    ):
        """Test successful_messages count when logger has check_message."""
        receiver = TrackingReceiver(identity_decoder, logger=checking_logger)

        messages = [
            Message(id=0, data=[1, 2]),  # Even ID -> should be successful
            Message(id=1, data=[3, 4]),  # Odd ID -> should not be successful
            Message(id=2, data=[5, 6]),  # Even ID -> should be successful
        ]

        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_messages == 3
        assert stats.decoded_messages == 3
        assert stats.successful_messages == 2  # IDs 0 and 2
        assert stats.validation_errors == 1  # ID 1

    def test_successful_messages_without_checking_logger(self, identity_decoder):
        """Test successful_messages count when logger lacks check_message."""
        logger = PlainLogger()  # No check_message method
        receiver = TrackingReceiver(identity_decoder, logger=logger)

        messages = [Message(id=0, data=[1, 2]), Message(id=1, data=[3, 4])]

        list(receiver.receive_stream(iter(messages)))

        stats = receiver.get_stats()
        assert stats.total_messages == 2
        assert stats.decoded_messages == 2
        assert stats.successful_messages == 2  # all successful
        assert stats.validation_errors == 0

    def test_get_last_message_initial(self, identity_decoder):
        """Test get_last_message returns None initially."""
        receiver = TrackingReceiver(identity_decoder)
        assert receiver.get_last_message() is None

    def test_get_last_message_after_success(self, identity_decoder):
        """Test get_last_message returns last successful message."""
        receiver = TrackingReceiver(identity_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(receiver.receive_stream(iter(messages)))

        last = receiver.get_last_message()
        assert last is not None
        assert last.id == 1
        assert last.data == [4, 5, 6]

    def test_get_last_message_after_failure(self, failing_decoder):
        """Test get_last_message remains None after all failures."""
        receiver = TrackingReceiver(failing_decoder)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(receiver.receive_stream(iter(messages)))

        assert receiver.get_last_message() is None

    def test_receive_stream_empty(self, identity_decoder):
        """Test with empty message stream."""
        receiver = TrackingReceiver(identity_decoder)
        results = list(receiver.receive_stream(iter([])))

        assert results == []
        assert receiver._last_message is None
        assert receiver._stats.total_messages == 0
