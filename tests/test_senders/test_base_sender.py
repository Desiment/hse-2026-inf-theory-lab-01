# tests/test_senders/test_base.py
"""Tests for the base sender module."""

import pytest
from typing import Sequence, Iterator

from codinglab.types import Message
from codinglab.logger import PlainLogger, NullLogger
from codinglab.senders.base import BaseSender


class BaseSenderImplementation(BaseSender):
    def message_stream(self, stream_len: int) -> Iterator[Message]:
        yield Message(id=1, data="")


class TestBaseSender:
    """Tests for BaseSender."""

    @pytest.fixture
    def encoder_with_table(self):
        """Encoder with a code table."""

        class EncoderWithTable:
            def encode(self, data: Sequence[int]) -> Sequence[str]:
                return [str(x) for x in data]

            @property
            def code_table(self):
                return {1: "1", 2: "2", 3: "3"}

        return EncoderWithTable()

    @pytest.fixture
    def encoder_without_table(self):
        """Encoder without a code table."""

        class EncoderWithoutTable:
            def encode(self, data: Sequence[int]) -> Sequence[str]:
                return [str(x) for x in data]

            @property
            def code_table(self):
                return None

        return EncoderWithoutTable()

    def test_initialization_default_logger(self, encoder_with_table):
        """Test initialization with default NullLogger."""
        sender = BaseSenderImplementation(encoder_with_table)
        assert sender._encoder == encoder_with_table
        assert sender._last_message is None
        assert isinstance(sender._logger, NullLogger)

    def test_initialization_with_custom_logger(self, encoder_with_table):
        """Test initialization with custom logger."""
        logger = PlainLogger()
        sender = BaseSenderImplementation(encoder_with_table, logger=logger)
        assert sender._logger == logger

    def test_alphabet_with_code_table(self, encoder_with_table):
        """Test alphabet property when encoder has code table."""
        sender = BaseSenderImplementation(encoder_with_table)
        alphabet = sender.alphabet
        assert set(alphabet) == {1, 2, 3}

    def test_alphabet_without_code_table(self, encoder_without_table):
        """Test alphabet property when encoder has no code table."""
        sender = BaseSenderImplementation(encoder_without_table)
        assert sender.alphabet == []

    def test_get_last_message_initial(self, encoder_with_table):
        """Test get_last_message returns None initially."""
        sender = BaseSenderImplementation(encoder_with_table)
        assert sender.get_last_message() is None

    def test_get_last_message_after_set(self, encoder_with_table):
        """Test get_last_message returns last message after setting."""
        sender = BaseSenderImplementation(encoder_with_table)
        message = Message(id=42, data=[1, 2, 3])
        sender._last_message = message

        assert sender.get_last_message() == message

    def test_alphabet_subclasses_can_override(self, encoder_with_table):
        """Test that subclasses can override alphabet property."""

        class CustomSender(BaseSenderImplementation):
            @property
            def alphabet(self):
                return ["custom", "alphabet"]

        sender = CustomSender(encoder_with_table)
        assert sender.alphabet == ["custom", "alphabet"]
