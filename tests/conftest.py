# tests/conftest.py
"""Common fixtures for testing the coding experiments library."""

import pytest
import time
from typing import Sequence, Dict, Optional, Iterator
from codinglab.types import (
    Message,
    TransmissionLog,
    TransmissionEvent,
    TransmissionLogger,
)
from codinglab.logger import NullLogger
from codinglab.interfaces import Encoder, Decoder, Sender, Channel, Receiver


# ============= Test Data Fixtures =============


@pytest.fixture
def sample_message():
    """Provide a sample message with integer symbols."""
    return Message(id=1, data=[1, 0, 1, 1, 0])


@pytest.fixture
def sample_string_message():
    """Provide a sample message with string symbols."""
    return Message(id=2, data=["A", "B", "C", "A"])


@pytest.fixture
def sample_transmission_log(sample_message):
    """Provide a sample transmission log entry."""
    return TransmissionLog(
        timestamp=time.time(),
        event=TransmissionEvent.ENCODED,
        message=sample_message,
        data={"encoder": "test_encoder", "duration_ms": 0.5},
    )


# ============= Mock Implementations =============


class MockEncoder(Encoder[int, str]):
    """Mock encoder for testing."""

    def __init__(self, code_table: Optional[Dict[int, Sequence[str]]] = None):
        self._code_table = code_table or {0: "0", 1: "1"}

    def encode(self, message: Sequence[int]) -> Sequence[str]:
        if not all(sym in self._code_table for sym in message):
            raise ValueError("Symbol not in alphabet")
        return [code for sym in message for code in self._code_table[sym]]

    @property
    def code_table(self) -> Optional[Dict[int, Sequence[str]]]:
        return self._code_table


class MockDecoder(Decoder[int, str]):
    """Mock decoder for testing."""

    def __init__(self, code_table: Optional[Dict[int, Sequence[str]]] = None):
        self._code_table = code_table or {0: "0", 1: "1"}
        self._reverse_table = {
            "".join(codes): sym for sym, codes in self._code_table.items()
        }

    def decode(self, encoded: Sequence[str], position: int = 0) -> Sequence[int]:
        # Simple variable-length decoding, for codes with length 1 or 2
        if len(encoded) == 0:
            return []
        elif len(encoded) >= 1 and "".join(encoded[0:1]) in self._reverse_table:
            return [self._reverse_table["".join(encoded[0:1])]] + list(
                self.decode(encoded[1:], position=1)
            )
        elif len(encoded) >= 2 and "".join(encoded[0:2]) in self._reverse_table:
            return [self._reverse_table["".join(encoded[0:2])]] + list(
                self.decode(encoded[2:], position=2)
            )
        else:
            raise ValueError(f"Invalid code sequence at position {position}")

    @property
    def code_table(self) -> Optional[Dict[int, Sequence[str]]]:
        return self._code_table


class MockSender(Sender[int, str]):
    """Mock sender for testing."""

    def __init__(
        self,
        alphabet: Sequence[int] = (0, 1),
        logger: TransmissionLogger = NullLogger(),
    ):
        self._alphabet = alphabet
        self._last_message: Optional[Message] = None
        self._encoder = MockEncoder({sym: str(sym) for sym in alphabet})
        self._logger = logger

    @property
    def alphabet(self) -> Sequence[int]:
        return self._alphabet

    def message_stream(self, stream_len: int) -> Iterator[Message[str]]:
        if stream_len <= 0:
            raise ValueError("stream_len must be positive")

        for i in range(stream_len):
            # Generate a simple pattern
            source_data = [self._alphabet[i % len(self._alphabet)]] * (i + 1)
            self._last_message = Message(id=i, data=source_data)
            self._logger.log(
                TransmissionLog(
                    timestamp=time.time(),
                    event=TransmissionEvent.SOURCE_GENERATED,
                    message=self._last_message,
                    data={},
                )
            )
            encoded_data = self._encoder.encode(source_data)
            yield Message(id=i, data=encoded_data)

    def get_last_message(self) -> Optional[Message[int]]:
        return self._last_message


class MockChannel(Channel[str]):
    """Mock channel for testing."""

    def __init__(self, error_rate: float = 0.0):
        self.error_rate = error_rate
        import random

        self.random = random.Random(42)  # Fixed seed for reproducibility

    def transmit_stream(
        self, messages: Iterator[Message[str]]
    ) -> Iterator[Message[str]]:
        for msg in messages:
            if self.random.random() < self.error_rate:
                # Introduce an error by flipping a bit
                corrupted_data = list(msg.data)
                if len(corrupted_data) > 0:
                    idx = self.random.randint(0, len(corrupted_data) - 1)
                    corrupted_data[idx] = "1" if corrupted_data[idx] == "0" else "0"
                yield Message(id=msg.id, data=corrupted_data)
            else:
                yield msg


class MockReceiver(Receiver[int, str]):
    """Mock receiver for testing."""

    def __init__(self, decoder: Decoder[int, str]):
        self.decoder = decoder
        self._last_message: Optional[Message] = None
        self._received_count = 0

    def receive_stream(self, messages: Iterator[Message[str]]) -> Iterator[bool]:
        for msg in messages:
            try:
                decoded_data = self.decoder.decode(msg.data)
                self._last_message = Message(id=msg.id, data=decoded_data)
                self._received_count += 1
                yield True
            except (ValueError, KeyError):
                yield False

    def get_last_message(self) -> Optional[Message[int]]:
        return self._last_message
