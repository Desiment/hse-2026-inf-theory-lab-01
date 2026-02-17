# tests/test_senders/test_probabilistic.py
"""Tests for the probabilistic sender module."""

import pytest

from codinglab.types import Message, TransmissionEvent
from codinglab.logger import PlainLogger, NullLogger
from codinglab.senders.probabilistic import ProbabilisticSender


class TestProbabilisticSender:
    """Tests for ProbabilisticSender."""

    @pytest.fixture
    def simple_encoder(self):
        """Simple encoder for testing."""

        class SimpleEncoder:
            def encode(self, data):
                return [str(x) for x in data]

            @property
            def code_table(self):
                return None

        return SimpleEncoder()

    @pytest.fixture
    def uniform_probabilities(self):
        """Uniform probability distribution."""
        return {0: 0.5, 1: 0.5}

    @pytest.fixture
    def skewed_probabilities(self):
        """Skewed probability distribution."""
        return {0: 0.9, 1: 0.1}

    @pytest.fixture
    def three_symbol_probabilities(self):
        """Three-symbol probability distribution."""
        return {"A": 0.5, "B": 0.3, "C": 0.2}

    def test_initialization_valid(self, simple_encoder, uniform_probabilities):
        """Test valid initialization."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            seed=42,
        )

        assert sender._encoder == simple_encoder
        assert sender._probabilities == uniform_probabilities
        assert sender._alphabet == [0, 1]
        assert sender._weights == [0.5, 0.5]
        assert sender._min_len == 2
        assert sender._max_len == 5
        assert sender._message_id == 0
        assert isinstance(sender._logger, NullLogger)

    def test_initialization_with_logger(self, simple_encoder, uniform_probabilities):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            logger=logger,
        )

        assert sender._logger == logger

    def test_initialization_probabilities_not_sum_to_one(self, simple_encoder):
        """Test that probabilities must sum to 1.0."""
        with pytest.raises(ValueError, match="Probabilities must sum to 1.0"):
            ProbabilisticSender(
                encoder=simple_encoder,
                probabilities={0: 0.3, 1: 0.3},
                message_length_range=(2, 5),
            )

    def test_initialization_invalid_min_length(
        self, simple_encoder, uniform_probabilities
    ):
        """Test that minimum length must be positive."""
        with pytest.raises(ValueError, match="Minimum message length must be positive"):
            ProbabilisticSender(
                encoder=simple_encoder,
                probabilities=uniform_probabilities,
                message_length_range=(0, 5),
            )

    def test_initialization_max_less_than_min(
        self, simple_encoder, uniform_probabilities
    ):
        """Test that max length must be >= min length."""
        with pytest.raises(
            ValueError, match="Maximum message length .* must be >= minimum"
        ):
            ProbabilisticSender(
                encoder=simple_encoder,
                probabilities=uniform_probabilities,
                message_length_range=(5, 3),
            )

    def test_alphabet_property(self, simple_encoder, three_symbol_probabilities):
        """Test alphabet property returns correct symbols."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=three_symbol_probabilities,
            message_length_range=(2, 5),
        )

        assert set(sender.alphabet) == {"A", "B", "C"}

    def test_message_stream_basic(self, simple_encoder, uniform_probabilities):
        """Test basic message stream generation."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 3),
            seed=42,  # Fixed seed for reproducibility
        )

        messages = list(sender.message_stream(5))

        assert len(messages) == 5
        assert all(isinstance(msg, Message) for msg in messages)
        assert all(isinstance(msg.data, list) for msg in messages)
        assert all(len(msg.data) >= 2 for msg in messages)
        assert all(len(msg.data) <= 3 for msg in messages)

        # Check message IDs are sequential
        assert [msg.id for msg in messages] == [0, 1, 2, 3, 4]

    def test_message_stream_zero_length_raises_error(
        self, simple_encoder, uniform_probabilities
    ):
        """Test message_stream with zero length."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
        )

        with pytest.raises(ValueError, match="stream_len must be positive, got 0"):
            list(sender.message_stream(0))

    def test_message_stream_negative_length_raises_error(
        self, simple_encoder, uniform_probabilities
    ):
        """Test message_stream with negative length."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
        )

        with pytest.raises(ValueError, match="stream_len must be positive, got -3"):
            list(sender.message_stream(-3))

    def test_message_stream_updates_last_message(
        self, simple_encoder, uniform_probabilities
    ):
        """Test that _last_message is updated correctly."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 3),
            seed=42,
        )

        assert sender.get_last_message() is None

        list(sender.message_stream(3))

        last = sender.get_last_message()
        assert last is not None
        assert last.id == 2  # Last message ID
        assert isinstance(last.data, list)

    def test_message_stream_logs_events(self, simple_encoder, uniform_probabilities):
        """Test that source generation events are logged."""
        logger = PlainLogger()
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 3),
            logger=logger,
            seed=42,
        )

        list(sender.message_stream(3))

        # Should have SOURCE_GENERATED events for each message
        source_events = [
            log
            for log in logger.logs
            if log.event == TransmissionEvent.SOURCE_GENERATED
        ]
        assert len(source_events) == 3

        for i, log in enumerate(source_events):
            assert log.message.id == i
            assert "length" in log.data
            assert "alphabet" in log.data
            assert "probabilities" in log.data

    def test_reset(self, simple_encoder, uniform_probabilities):
        """Test reset method resets message ID counter."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 3),
            seed=42,
        )

        list(sender.message_stream(5))
        assert sender._message_id == 5

        sender.reset()
        assert sender._message_id == 0

    def test_reset_affects_subsequent_streams(
        self, simple_encoder, uniform_probabilities
    ):
        """Test that reset affects message IDs in subsequent streams."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 3),
            seed=42,
        )

        messages1 = list(sender.message_stream(2))
        assert messages1[0].id == 0
        assert messages1[1].id == 1

        sender.reset()

        messages2 = list(sender.message_stream(2))
        assert messages2[0].id == 0  # IDs reset
        assert messages2[1].id == 1

    def test_reproducible_with_seed(self, simple_encoder, uniform_probabilities):
        """Test that same seed produces same messages."""
        sender1 = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            seed=123,
        )

        sender2 = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            seed=123,
        )

        messages1 = list(sender1.message_stream(10))
        messages2 = list(sender2.message_stream(10))

        # Messages should be identical with same seed
        for msg1, msg2 in zip(messages1, messages2):
            assert msg1.data == msg2.data

    def test_different_seeds_produce_different_messages(
        self, simple_encoder, uniform_probabilities
    ):
        """Test that different seeds produce different messages."""
        sender1 = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            seed=123,
        )

        sender2 = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=uniform_probabilities,
            message_length_range=(2, 5),
            seed=456,
        )

        messages1 = list(sender1.message_stream(10))
        messages2 = list(sender2.message_stream(10))

        # At least some messages should differ
        assert any(msg1.data != msg2.data for msg1, msg2 in zip(messages1, messages2))

    def test_probability_distribution_respected(
        self, simple_encoder, skewed_probabilities
    ):
        """Test that generated symbols follow approximate probabilities."""
        sender = ProbabilisticSender(
            encoder=simple_encoder,
            probabilities=skewed_probabilities,
            message_length_range=(100, 100),  # Fixed length
            seed=42,
        )

        # Generate many messages and count symbol frequencies
        all_symbols = []
        for msg in sender.message_stream(1000):
            all_symbols.extend(msg.data)  # Use encoded data (strings)

        # Convert back to ints for counting
        symbol_counts = {0: 0, 1: 0}
        for s in all_symbols:
            symbol_counts[int(s)] += 1

        total = sum(symbol_counts.values())

        # Should be approximately 90% zeros, 10% ones
        assert 0.85 <= symbol_counts[0] / total <= 0.95
        assert 0.05 <= symbol_counts[1] / total <= 0.15
