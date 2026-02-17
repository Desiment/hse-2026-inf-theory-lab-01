# tests/test_channels/test_noiseless.py
"""Tests for the noiseless channel module."""

import time

from codinglab.types import Message, TransmissionEvent
from codinglab.logger import PlainLogger, NullLogger
from codinglab.channels.base import NoiselessChannel


class TestNoiselessChannel:
    """Tests for NoiselessChannel."""

    def test_initialization_default_logger(self):
        """Test initialization with default NullLogger."""
        channel = NoiselessChannel()
        assert isinstance(channel._logger, NullLogger)

    def test_initialization_with_custom_logger(self):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        channel = NoiselessChannel(logger=logger)
        assert channel._logger == logger

    def test_transmit_stream_passthrough(self):
        """Test that messages pass through unchanged."""
        channel = NoiselessChannel()
        messages = [
            Message(id=0, data=[1, 2, 3]),
            Message(id=1, data=["a", "b", "c"]),
            Message(id=2, data=[True, False]),
        ]

        transmitted = list(channel.transmit_stream(iter(messages)))

        assert len(transmitted) == 3
        assert transmitted[0].id == 0
        assert transmitted[0].data == [1, 2, 3]
        assert transmitted[1].id == 1
        assert transmitted[1].data == ["a", "b", "c"]
        assert transmitted[2].id == 2
        assert transmitted[2].data == [True, False]

    def test_transmit_stream_logs_events(self):
        """Test that transmission events are logged."""
        logger = PlainLogger()
        channel = NoiselessChannel(logger=logger)

        messages = [Message(id=0, data=[1, 2, 3]), Message(id=1, data=[4, 5, 6])]

        list(channel.transmit_stream(iter(messages)))

        assert len(logger.logs) == 2
        assert logger.logs[0].event == TransmissionEvent.TRANSMITTED
        assert logger.logs[0].message.id == 0
        assert logger.logs[0].data["channel_type"] == "noiseless"
        assert logger.logs[1].event == TransmissionEvent.TRANSMITTED
        assert logger.logs[1].message.id == 1

    def test_transmit_stream_empty_iterator(self):
        """Test with empty iterator."""
        channel = NoiselessChannel()
        transmitted = list(channel.transmit_stream(iter([])))
        assert transmitted == []

    def test_transmit_stream_preserves_timestamps(self):
        """Test that timestamps are recorded for each transmission."""
        logger = PlainLogger()
        channel = NoiselessChannel(logger=logger)

        messages = [Message(id=i, data=[i]) for i in range(3)]

        start_time = time.time()
        list(channel.transmit_stream(iter(messages)))
        end_time = time.time()

        for log in logger.logs:
            assert start_time <= log.timestamp <= end_time
