# tests/test_loggers.py
"""Tests for the loggers module."""

import pytest
import time
import pandas as pd
from codinglab.types import Message, TransmissionLog, TransmissionEvent
from codinglab.logger import PlainLogger, ConsoleLogger, NullLogger, PandasLogger


class TestPlainLogger:
    """Tests for PlainLogger."""

    def test_initialization(self):
        """Test logger initialization."""
        logger = PlainLogger()
        assert logger.logs == []
        assert isinstance(logger.logs, list)

    def test_log_single_entry(self, sample_transmission_log):
        """Test logging a single entry."""
        logger = PlainLogger()
        logger.log(sample_transmission_log)

        assert len(logger.logs) == 1
        assert logger.logs[0] == sample_transmission_log

    def test_log_multiple_entries(self):
        """Test logging multiple entries."""
        logger = PlainLogger()
        logs = []

        for i in range(5):
            log = TransmissionLog(
                timestamp=time.time(),
                event=TransmissionEvent.ENCODED,
                message=Message(id=i, data=[1, 0, 1]),
                data={"index": i},
            )
            logs.append(log)
            logger.log(log)

        assert len(logger.logs) == 5
        assert logger.logs == logs

    def test_log_different_event_types(self, sample_message):
        """Test logging entries with different event types."""
        logger = PlainLogger()
        timestamp = time.time()

        for event in TransmissionEvent:
            log = TransmissionLog(
                timestamp=timestamp,
                event=event,
                message=sample_message,
                data={"test": True},
            )
            logger.log(log)

        assert len(logger.logs) == len(TransmissionEvent)
        assert [log.event for log in logger.logs] == list(TransmissionEvent)

    def test_log_preserves_order(self):
        """Test that logs maintain insertion order."""
        logger = PlainLogger()

        for i in range(10):
            log = TransmissionLog(
                timestamp=float(i),
                event=TransmissionEvent.SOURCE_GENERATED,
                message=Message(id=i, data=[i]),
                data={},
            )
            logger.log(log)

        assert [log.timestamp for log in logger.logs] == list(range(10))
        assert [log.message.id for log in logger.logs] == list(range(10))

    def test_plain_logger_implements_protocol(self):
        """Test that PlainLogger satisfies TransmissionLogger protocol."""
        logger = PlainLogger()
        from codinglab.types import TransmissionLogger

        assert isinstance(logger, TransmissionLogger)


class TestConsoleLogger:
    """Tests for ConsoleLogger."""

    def test_initialization_default(self):
        """Test logger initialization with default parameters."""
        logger = ConsoleLogger()
        assert logger.verbose is True

    def test_initialization_custom(self):
        """Test logger initialization with custom parameters."""
        logger = ConsoleLogger(verbose=False)
        assert logger.verbose is False

    def test_log_verbose_output(self, sample_transmission_log, capsys):
        """Test verbose logging output."""
        logger = ConsoleLogger(verbose=True)
        logger.log(sample_transmission_log)

        captured = capsys.readouterr()
        expected = f"[{sample_transmission_log.timestamp:.6f}] {sample_transmission_log.event.value}: Message {sample_transmission_log.message.id}: {sample_transmission_log.message.data} // {sample_transmission_log.data}\n"
        assert captured.out == expected

    def test_log_non_verbose_output(self, sample_transmission_log, capsys):
        """Test non-verbose logging output."""
        logger = ConsoleLogger(verbose=False)
        logger.log(sample_transmission_log)

        captured = capsys.readouterr()
        expected = f"{sample_transmission_log.event.value}: Message {sample_transmission_log.message.id}\n"
        assert captured.out == expected

    def test_log_multiple_entries(self, capsys):
        """Test logging multiple entries."""
        logger = ConsoleLogger(verbose=False)

        for i in range(3):
            log = TransmissionLog(
                timestamp=float(i),
                event=TransmissionEvent.ENCODED,
                message=Message(id=i, data=[1, 0]),
                data={},
            )
            logger.log(log)

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "encoded: Message 0"
        assert lines[1] == "encoded: Message 1"
        assert lines[2] == "encoded: Message 2"

    def test_log_with_different_data_types(self, sample_message, capsys):
        """Test logging with different data types in the data dict."""
        logger = ConsoleLogger(verbose=True)

        log = TransmissionLog(
            timestamp=123.456789,
            event=TransmissionEvent.ERROR,
            message=sample_message,
            data={
                "error_type": "ValueError",
                "error_code": 404,
                "details": ["detail1", "detail2"],
                "nested": {"key": "value"},
            },
        )
        logger.log(log)

        captured = capsys.readouterr()
        assert (
            "[123.456789] error: Message 1: [1, 0, 1, 1, 0] // {'error_type': 'ValueError', 'error_code': 404, 'details': ['detail1', 'detail2'], 'nested': {'key': 'value'}}"
            in captured.out
        )

    def test_console_logger_implements_protocol(self):
        """Test that ConsoleLogger satisfies TransmissionLogger protocol."""
        logger = ConsoleLogger()
        from codinglab.types import TransmissionLogger

        assert isinstance(logger, TransmissionLogger)


class TestNullLogger:
    """Tests for NullLogger."""

    def test_initialization(self):
        """Test logger initialization."""
        logger = NullLogger()
        assert logger is not None

    def test_log_does_nothing(self, sample_transmission_log):
        """Test that log method performs no operation."""
        logger = NullLogger()

        # This should not raise any exceptions
        logger.log(sample_transmission_log)

        # NullLogger has no state to check
        assert not hasattr(logger, "logs")

    def test_log_multiple_entries_no_side_effects(self):
        """Test that multiple log calls have no side effects."""
        logger = NullLogger()

        for i in range(100):
            log = TransmissionLog(
                timestamp=float(i),
                event=TransmissionEvent.SOURCE_GENERATED,
                message=Message(id=i, data=[i]),
                data={"i": i},
            )
            logger.log(log)

        # No state to check, just verifying no exceptions

    def test_null_logger_implements_protocol(self):
        """Test that NullLogger satisfies TransmissionLogger protocol."""
        logger = NullLogger()
        from codinglab.types import TransmissionLogger

        assert isinstance(logger, TransmissionLogger)


class TestPandasLogger:
    """Tests for PandasLogger."""

    @pytest.fixture
    def pandas_logger(self):
        """Provide a PandasLogger instance."""
        return PandasLogger()

    @pytest.fixture
    def sample_messages(self):
        """Provide sample messages for testing."""
        return [
            Message(id=0, data=[1, 0, 1]),
            Message(id=1, data=[0, 1, 0]),
            Message(id=2, data=[1, 1, 0]),
        ]

    def test_initialization(self, pandas_logger):
        """Test logger initialization."""
        assert pandas_logger._logs == []
        assert pandas_logger.row_data == {}

    def test_log_single_entry(self, pandas_logger, sample_message):
        """Test logging a single entry."""
        log = TransmissionLog(
            timestamp=123.456,
            event=TransmissionEvent.ENCODED,
            message=sample_message,
            data={},
        )

        pandas_logger.log(log)

        # Check internal storage
        assert len(pandas_logger._logs) == 1
        assert pandas_logger._logs[0] == log

        # Check row_data
        assert 1 in pandas_logger.row_data  # message.id = 1
        assert len(pandas_logger.row_data[1]) == 1
        row = pandas_logger.row_data[1][0]
        assert row["timestamp"] == 123.456
        assert row["event"] == "encoded"
        assert row["message_id"] == 1
        assert row["message_data"] == "10110"

    def test_log_multiple_entries_same_message(self, pandas_logger, sample_message):
        """Test logging multiple entries for the same message."""
        events = [
            TransmissionEvent.SOURCE_GENERATED,
            TransmissionEvent.ENCODED,
            TransmissionEvent.TRANSMITTED,
            TransmissionEvent.RECEIVED,
            TransmissionEvent.DECODED,
        ]

        for i, event in enumerate(events):
            log = TransmissionLog(
                timestamp=float(i),
                event=event,
                message=sample_message,
                data={"step": i},
            )
            pandas_logger.log(log)

        # Check row_data for message 1
        assert len(pandas_logger.row_data[1]) == len(events)

        # Check events in order
        for i, row in enumerate(pandas_logger.row_data[1]):
            assert row["event"] == events[i].value
            assert row["timestamp"] == float(i)

    def test_log_multiple_messages(self, pandas_logger, sample_messages):
        """Test logging entries for multiple messages."""
        for i, msg in enumerate(sample_messages):
            log = TransmissionLog(
                timestamp=float(i),
                event=TransmissionEvent.SOURCE_GENERATED,
                message=msg,
                data={},
            )
            pandas_logger.log(log)

        # Check that we have entries for all messages
        assert len(pandas_logger.row_data) == 3
        assert all(msg_id in pandas_logger.row_data for msg_id in [0, 1, 2])

        # Check each message has one entry
        assert len(pandas_logger.row_data[0]) == 1
        assert len(pandas_logger.row_data[1]) == 1
        assert len(pandas_logger.row_data[2]) == 1

    def test_dataframe_property_empty(self, pandas_logger):
        """Test dataframe property when no logs exist."""
        df = pandas_logger.dataframe

        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert list(df.columns) == ["timestamp", "event", "message_id", "message_data"]

    def test_dataframe_property_with_logs(self, pandas_logger, sample_messages):
        """Test dataframe property with logs."""
        # Add logs
        for i, msg in enumerate(sample_messages):
            for event in [
                TransmissionEvent.SOURCE_GENERATED,
                TransmissionEvent.ENCODED,
            ]:
                log = TransmissionLog(
                    timestamp=float(i), event=event, message=msg, data={}
                )
                pandas_logger.log(log)

        df = pandas_logger.dataframe

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6  # 3 messages * 2 events
        assert set(df.columns) == {"timestamp", "event", "message_id", "message_data"}

        # Check data types
        assert df["timestamp"].dtype == float
        assert df["event"].dtype in ["string", "object"]
        assert df["message_id"].dtype == int
        assert df["message_data"].dtype in ["string", "object"]

    def test_check_message_valid(self, pandas_logger, sample_message):
        """Test check_message with valid message that exists."""
        log = TransmissionLog(
            timestamp=123.456,
            event=TransmissionEvent.SOURCE_GENERATED,
            message=sample_message,
            data={},
        )
        pandas_logger.log(log)

        # Check with same message
        assert pandas_logger.check_message(sample_message) is True

    def test_check_message_different_data(self, pandas_logger, sample_message):
        """Test check_message with message having different data."""
        log = TransmissionLog(
            timestamp=123.456,
            event=TransmissionEvent.SOURCE_GENERATED,
            message=sample_message,
            data={},
        )
        pandas_logger.log(log)

        # Create message with same ID but different data
        different_msg = Message(id=1, data=[0, 0, 0, 0, 0])
        assert pandas_logger.check_message(different_msg) is False

    def test_check_message_not_logged(self, pandas_logger):
        """Test check_message with message that hasn't been logged."""
        msg = Message(id=999, data=[1, 2, 3])

        with pytest.raises(ValueError, match="Message yet to be transmitted"):
            pandas_logger.check_message(msg)

    def test_dataframe_after_logging(self, pandas_logger, sample_messages):
        """Test that dataframe property reflects current logs."""
        # Log some entries
        for msg in sample_messages[:2]:  # Only first two messages
            pandas_logger.log(
                TransmissionLog(
                    timestamp=1.0,
                    event=TransmissionEvent.SOURCE_GENERATED,
                    message=msg,
                    data={},
                )
            )

        df1 = pandas_logger.dataframe
        assert len(df1) == 2

        # Log more entries
        for msg in sample_messages:
            pandas_logger.log(
                TransmissionLog(
                    timestamp=2.0, event=TransmissionEvent.DECODED, message=msg, data={}
                )
            )

        df2 = pandas_logger.dataframe
        assert len(df2) == 5  # 2 + 3

    def test_pandas_logger_implements_protocol(self, pandas_logger):
        """Test that PandasLogger satisfies TransmissionLogger protocol."""
        from codinglab.types import TransmissionLogger

        assert isinstance(pandas_logger, TransmissionLogger)


class TestLoggerIntegration:
    """Integration tests for multiple loggers."""

    def test_multiple_loggers_receive_same_entries(self, sample_transmission_log):
        """Test that multiple loggers can receive the same log entries."""
        plain_logger = PlainLogger()
        console_logger = ConsoleLogger(verbose=False)
        null_logger = NullLogger()
        pandas_logger = PandasLogger()

        loggers = [plain_logger, console_logger, null_logger, pandas_logger]

        # Log to all loggers
        for logger in loggers:
            logger.log(sample_transmission_log)

        # Verify each logger handled the entry appropriately
        assert len(plain_logger.logs) == 1
        assert plain_logger.logs[0] == sample_transmission_log

        assert len(pandas_logger._logs) == 1
        assert pandas_logger._logs[0] == sample_transmission_log
        assert len(pandas_logger.row_data) == 1

        # ConsoleLogger would have printed, but we don't capture here

    def test_logger_composition(self, sample_transmission_log):
        """Test composing loggers (e.g., logging to multiple destinations)."""

        class CompositeLogger:
            def __init__(self, loggers):
                self.loggers = loggers

            def log(self, log_entry):
                for logger in self.loggers:
                    logger.log(log_entry)

        plain_logger = PlainLogger()
        pandas_logger = PandasLogger()

        composite = CompositeLogger([plain_logger, pandas_logger])
        composite.log(sample_transmission_log)

        # Both loggers should have received the entry
        assert len(plain_logger.logs) == 1
        assert len(pandas_logger._logs) == 1
        assert len(pandas_logger.row_data) == 1
