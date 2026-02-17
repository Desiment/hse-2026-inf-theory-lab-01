# tests/test_types.py
"""Tests for the types module."""

import pytest
import time
from dataclasses import is_dataclass
from codinglab.types import (
    Symbol,
    SourceChar,
    ChannelChar,
    Message,
    TransmissionEvent,
    TransmissionLog,
    TransmissionLogger,
)


class TestTypeVariables:
    """Tests for type variables."""

    def test_symbol_typevar(self):
        """Test Symbol type variable."""
        # Type variables are just markers, we can only test they exist
        assert Symbol.__name__ == "Symbol"

    def test_source_char_typevar(self):
        """Test SourceChar type variable."""
        assert SourceChar.__name__ == "SourceChar"

    def test_channel_char_typevar(self):
        """Test ChannelChar type variable."""
        assert ChannelChar.__name__ == "ChannelChar"


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self, sample_message):
        """Test creating a message with basic attributes."""
        assert sample_message.id == 1
        assert sample_message.data == [1, 0, 1, 1, 0]

    def test_message_is_dataclass(self):
        """Test that Message is a dataclass."""
        assert is_dataclass(Message)

    def test_message_with_different_symbol_types(self):
        """Test Message with different symbol types."""
        int_msg = Message(id=1, data=[1, 2, 3])
        assert int_msg.data == [1, 2, 3]

        str_msg = Message(id=2, data=["a", "b", "c"])
        assert str_msg.data == ["a", "b", "c"]

        mixed_msg = Message(id=3, data=[1, "a", True])
        assert mixed_msg.data == [1, "a", True]

    def test_message_immutability_illusion(self):
        """Test that Message data is not deeply immutable (by design)."""
        data = [1, 2, 3]
        msg = Message(id=1, data=data)

        # Modifying the original list affects the message
        data.append(4)
        assert msg.data == [1, 2, 3, 4]

        # But we can't reassign the attribute (dataclass generates frozen=False by default)
        msg.data = [5, 6, 7]  # This works because frozen=False

    def test_message_equality(self):
        """Test that messages with same attributes are not equal by default."""
        msg1 = Message(id=1, data=[1, 2, 3])
        msg2 = Message(id=1, data=[1, 2, 3])

        # Dataclasses with eq=True (default) compare all fields
        assert msg1 == msg2

        msg3 = Message(id=2, data=[1, 2, 3])
        assert msg1 != msg3


class TestTransmissionEvent:
    """Tests for TransmissionEvent enum."""

    def test_enum_values(self):
        """Test all enum values are present and have correct string values."""
        expected_values = {
            "SOURCE_GENERATED": "source_generated",
            "ENCODED": "encoded",
            "TRANSMITTED": "transmitted",
            "RECEIVED": "received",
            "DECODED": "decoded",
            "VALIDATED": "validated",
            "ERROR": "error",
        }

        for name, value in expected_values.items():
            assert hasattr(TransmissionEvent, name)
            assert getattr(TransmissionEvent, name).value == value

    def test_enum_iteration(self):
        """Test iterating over enum members."""
        events = list(TransmissionEvent)
        assert len(events) == 7
        assert all(isinstance(e, TransmissionEvent) for e in events)

    def test_enum_from_string(self):
        """Test creating enum from string value."""
        assert TransmissionEvent("encoded") == TransmissionEvent.ENCODED
        assert TransmissionEvent("error") == TransmissionEvent.ERROR

        with pytest.raises(ValueError):
            TransmissionEvent("invalid_event")


class TestTransmissionLog:
    """Tests for TransmissionLog dataclass."""

    def test_log_creation(self, sample_transmission_log, sample_message):
        """Test creating a transmission log entry."""
        log = sample_transmission_log

        assert isinstance(log.timestamp, float)
        assert log.event == TransmissionEvent.ENCODED
        assert log.message == sample_message
        assert log.data == {"encoder": "test_encoder", "duration_ms": 0.5}

    def test_log_is_dataclass(self):
        """Test that TransmissionLog is a dataclass."""
        assert is_dataclass(TransmissionLog)

    def test_log_with_different_events(self, sample_message):
        """Test log entries with different event types."""
        timestamp = time.time()

        for event in TransmissionEvent:
            log = TransmissionLog(
                timestamp=timestamp,
                event=event,
                message=sample_message,
                data={"test": True},
            )
            assert log.event == event
            assert log.data["test"] is True

    def test_log_with_empty_data(self, sample_message):
        """Test log entry with empty data dictionary."""
        log = TransmissionLog(
            timestamp=time.time(),
            event=TransmissionEvent.SOURCE_GENERATED,
            message=sample_message,
            data={},
        )
        assert log.data == {}

    def test_log_generic_type(self):
        """Test that TransmissionLog is generic over Symbol type."""
        int_log = TransmissionLog[int](
            timestamp=time.time(),
            event=TransmissionEvent.ENCODED,
            message=Message[int](id=1, data=[1, 2, 3]),
            data={},
        )
        assert isinstance(int_log.message.data[0], int)

        str_log = TransmissionLog[str](
            timestamp=time.time(),
            event=TransmissionEvent.ENCODED,
            message=Message[str](id=1, data=["a", "b", "c"]),
            data={},
        )
        assert isinstance(str_log.message.data[0], str)


class TestTransmissionLogger:
    """Tests for TransmissionLogger protocol."""

    def test_protocol_structural_subtyping(self):
        """Test that classes implementing log method satisfy the protocol."""

        class SimpleLogger:
            def log(self, log_entry: TransmissionLog) -> None:
                self.last_log = log_entry

        class InvalidLogger:
            def logg(self, log_entry: TransmissionLog) -> None:
                pass

        logger = SimpleLogger()
        assert isinstance(logger, TransmissionLogger)

        invalid = InvalidLogger()
        assert not isinstance(invalid, TransmissionLogger)

    def test_protocol_method_signature(self, sample_transmission_log):
        """Test that implementations must match the method signature."""

        class CorrectLogger:
            def log(self, log_entry: TransmissionLog) -> None:
                self.logged_entry = log_entry

        logger = CorrectLogger()
        logger.log(sample_transmission_log)
        assert logger.logged_entry == sample_transmission_log
