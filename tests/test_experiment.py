# tests/test_experiment.py
"""Tests for the experiment module."""

import pytest
import time

from codinglab.types import Message
from codinglab.receivers.tracking import TrackingReceiver, TransmissionStats
from codinglab.experiment import ExperimentResult, ExperimentRunner
from codinglab.logger import PandasLogger

# Import mocks from conftest
from .conftest import MockSender, MockChannel, MockDecoder


class TestExperimentResult:
    """Tests for ExperimentResult dataclass."""

    def test_initialization(self):
        """Test ExperimentResult initialization."""
        stats = TransmissionStats(
            total_messages=10,
            successful_messages=8,
            total_source_symbols=20,
            total_channel_symbols=25,
            total_processing_time=1.5,
            decode_errors=2,
            decoded_messages=8,
            failed_messages=2,
            validation_errors=0,
            avg_message_time=0.15,
        )

        result = ExperimentResult(
            stats=stats, start_time=100.0, end_time=101.5, metadata={"test": "value"}
        )

        assert result.stats.total_messages == 10
        assert result.stats.successful_messages == 8
        assert result.start_time == 100.0
        assert result.end_time == 101.5
        assert result.metadata == {"test": "value"}

    def test_duration_property(self):
        """Test duration property calculation."""
        stats = TransmissionStats()
        result = ExperimentResult(stats=stats, start_time=100.0, end_time=105.0)
        assert result.duration == 5.0

    def test_summary_formatting(self):
        """Test summary string contains expected metrics."""
        stats = TransmissionStats(
            total_messages=50,
            successful_messages=45,
            total_source_symbols=100,
            total_channel_symbols=150,
            total_processing_time=2.0,
            decode_errors=5,
            decoded_messages=45,
            failed_messages=5,
            validation_errors=0,
            avg_message_time=0.04,
        )

        result = ExperimentResult(stats=stats, start_time=100.0, end_time=102.0)

        summary = result.summary()
        assert "Experiment Summary:" in summary
        assert "Duration: 2.000" in summary
        assert "Messages: 50" in summary
        assert "Success Rate: 90.00%" in summary
        assert "Source Symbols: 100" in summary
        assert "Channel Symbols: 150" in summary
        assert "Compression Ratio: 0.667" in summary
        assert "Avg. Code Length: 1.500" in summary


class TestExperimentRunner:
    """Tests for ExperimentRunner."""

    @pytest.fixture
    def base_logger(self):
        """Provide a logger."""
        return PandasLogger()

    @pytest.fixture
    def mock_sender(self, base_logger):
        """Provide a mock sender."""
        return MockSender([0, 1], logger=base_logger)

    @pytest.fixture
    def mock_channel(self):
        """Provide a mock channel."""
        return MockChannel(error_rate=0.0)

    @pytest.fixture
    def tracking_receiver(self, base_logger):
        """Provide a TrackingReceiver with mock decoder."""
        decoder = MockDecoder({0: "0", 1: "1"})
        return TrackingReceiver(decoder, logger=base_logger)

    @pytest.fixture
    def experiment_runner(self, mock_sender, mock_channel, tracking_receiver):
        """Provide an experiment runner."""
        return ExperimentRunner(mock_sender, mock_channel, tracking_receiver)

    def test_initialization_valid(self, mock_sender, mock_channel, tracking_receiver):
        """Test valid initialization."""
        runner = ExperimentRunner(mock_sender, mock_channel, tracking_receiver)
        assert runner.sender == mock_sender
        assert runner.channel == mock_channel
        assert runner.receiver == tracking_receiver

    def test_initialization_with_non_tracking_receiver_raises_error(
        self, mock_sender, mock_channel
    ):
        """Test that non-TrackingReceiver raises TypeError."""
        from codinglab.receivers.base import BaseReceiver

        decoder = MockDecoder()
        base_receiver = BaseReceiver(decoder)

        with pytest.raises(
            TypeError, match="Receiver must be a TrackingReceiver instance"
        ):
            ExperimentRunner(mock_sender, mock_channel, base_receiver)  # type: ignore

    def test_run_basic(self, experiment_runner):
        """Test basic experiment run."""
        result = experiment_runner.run(num_messages=100)

        assert isinstance(result, ExperimentResult)
        assert result.stats.total_messages == 100
        assert result.stats.decoded_messages == 100
        assert result.duration > 0
        assert result.metadata["num_messages"] == 100
        assert result.metadata["success_count"] == 100
        assert result.metadata["failure_count"] == 0
        assert "components" in result.metadata
        assert result.metadata["components"]["sender_type"] == "MockSender"
        assert result.metadata["components"]["channel_type"] == "MockChannel"
        assert result.metadata["components"]["receiver_type"] == "TrackingReceiver"

    def test_run_with_zero_messages_raises_error(self, experiment_runner):
        """Test run with zero messages."""
        with pytest.raises(ValueError, match="num_messages must be positive, got 0"):
            experiment_runner.run(num_messages=0)

    def test_run_with_negative_messages_raises_error(self, experiment_runner):
        """Test run with negative messages."""
        with pytest.raises(ValueError, match="num_messages must be positive, got -3"):
            experiment_runner.run(num_messages=-3)

    def test_run_with_channel_errors(self, mock_sender, tracking_receiver):
        """Test run with channel introducing errors."""
        channel = MockChannel(error_rate=0.5)
        runner = ExperimentRunner(mock_sender, channel, tracking_receiver)
        result = runner.run(num_messages=20)
        assert result.stats.total_messages == 20
        assert result.stats.decoded_messages == 20
        assert result.stats.successful_messages < 20  # Some messages failed
        assert result.stats.validation_errors > 0
        assert result.metadata["failure_count"] > 0
        assert result.metadata["success_count"] + result.metadata["failure_count"] == 20

    def test_run_resets_stats_between_runs(self, experiment_runner):
        """Test that stats are reset for each run."""
        result1 = experiment_runner.run(num_messages=5)
        assert result1.stats.total_messages == 5

        result2 = experiment_runner.run(num_messages=10)
        assert result2.stats.total_messages == 10
        assert result2.stats.total_messages != result1.stats.total_messages

    def test_run_pipeline_integration(
        self, mock_sender, mock_channel, tracking_receiver
    ):
        """Test all pipeline components work together."""
        runner = ExperimentRunner(mock_sender, mock_channel, tracking_receiver)
        result = runner.run(num_messages=7)
        assert result.stats.total_messages == 7

    def test_run_timing(self, experiment_runner):
        """Test that timing is recorded."""
        start = time.time()
        result = experiment_runner.run(num_messages=10)
        end = time.time()

        assert result.start_time >= start
        assert result.end_time <= end
        assert result.duration <= (end - start) + 0.1  # Allow small overhead

    def test_run_single_message(self, experiment_runner):
        """Test run with a single message."""
        result = experiment_runner.run(num_messages=1)

        assert result.stats.total_messages == 1
        assert result.duration >= 0

    def test_run_large_number_of_messages(self, experiment_runner):
        """Test run with a large number of messages."""
        result = experiment_runner.run(num_messages=100)

        assert result.stats.total_messages == 100
        assert result.metadata["num_messages"] == 100

    def test_multiple_runs_sequential(self, experiment_runner):
        """Test running multiple experiments sequentially."""
        results = []
        for i in range(3):
            result = experiment_runner.run(num_messages=5 * (i + 1))
            results.append(result)

        assert len(results) == 3
        assert [r.stats.total_messages for r in results] == [5, 10, 15]

    def test_metadata_contains_component_info(self, experiment_runner):
        """Test metadata includes component type information."""
        result = experiment_runner.run(num_messages=3)

        assert "components" in result.metadata
        assert result.metadata["components"]["sender_type"] == "MockSender"
        assert result.metadata["components"]["channel_type"] == "MockChannel"
        assert result.metadata["components"]["receiver_type"] == "TrackingReceiver"

    def test_success_failure_counts(self, mock_sender, tracking_receiver):
        """Test success and failure counts are correct."""

        # Channel that corrupts every other message
        class AlternatingChannel(MockChannel):
            def __init__(self):
                super().__init__(error_rate=0.0)
                self.counter = 0

            def transmit_stream(self, messages):
                for msg in messages:
                    self.counter += 1
                    if self.counter % 2 == 0:
                        # Corrupt even-numbered messages in stream
                        corrupted_data = ["X" if x == "0" else "Y" for x in msg.data]
                        yield Message(id=msg.id, data=corrupted_data)
                    else:
                        yield msg

        channel = AlternatingChannel()
        runner = ExperimentRunner(mock_sender, channel, tracking_receiver)

        result = runner.run(num_messages=10)

        # Half should succeed, half fail
        assert result.metadata["success_count"] == 5
        assert result.metadata["failure_count"] == 5
        assert result.stats.decode_errors == 5

    def test_stats_consistency(self, experiment_runner):
        """Test that stats in result are consistent."""
        result = experiment_runner.run(num_messages=10)

        stats = result.stats
        metadata = result.metadata

        assert stats.total_messages == metadata["num_messages"]
        assert stats.decoded_messages == metadata["success_count"]
        assert stats.decode_errors == metadata["failure_count"]
        assert stats.total_messages == stats.decoded_messages + stats.decode_errors
