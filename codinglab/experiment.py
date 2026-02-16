"""
Experiment framework for the coding experiments library.

This module provides the infrastructure for running coding experiments,
including experiment runners and result data structures. It enables
systematic evaluation of different coding schemes and channel models.
"""

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["ExperimentResult", "ExperimentRunner"]

import time
from typing import Any, Dict
from dataclasses import dataclass, field
from .interfaces import Sender, Channel, SourceChar, ChannelChar
from .receivers.tracking import TrackingReceiver, TransmissionStats


@dataclass
class ExperimentResult:
    """
    Results from a coding experiment run.

    This class encapsulates all data collected during an experiment,
    including statistics, timing information, and any additional
    metadata. It provides computed properties for common analysis
    and can be serialized for storage or further processing.

    Attributes:
        stats: Transmission statistics collected during the experiment
        start_time: Experiment start time in seconds since epoch
        end_time: Experiment end time in seconds since epoch
        metadata: Additional experiment metadata as key-value pairs
    """

    stats: TransmissionStats
    """Transmission statistics collected during the experiment."""

    start_time: float
    """Experiment start time in seconds since epoch."""

    end_time: float
    """Experiment end time in seconds since epoch."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional experiment metadata as key-value pairs."""

    @property
    def duration(self) -> float:
        """
        Calculate the total duration of the experiment.

        Returns:
            Experiment duration in seconds
        """
        return self.end_time - self.start_time

    def summary(self) -> str:
        """
        Generate a human-readable summary of experiment results.

        Returns:
            Formatted string with key experiment metrics
        """
        return (
            f"Experiment Summary:\n"
            f"  Duration: {self.duration:.3f} seconds\n"
            f"  Messages: {self.stats.total_messages}\n"
            f"  Success Rate: {self.stats.success_rate:.2%}\n"
            f"  Source Symbols: {self.stats.total_source_symbols}\n"
            f"  Channel Symbols: {self.stats.total_channel_symbols}\n"
            f"  Compression Ratio: {self.stats.compression_ratio:.3f}\n"
            f"  Avg. Code Length: {self.stats.average_code_len:.3f}\n"
            f"  Avg. Processing Time: {self.stats.avg_message_time:.6f} s/msg"
        )


class ExperimentRunner:
    """
    Orchestrates and runs coding experiments.

    This class coordinates the interaction between sender, channel,
    and receiver components to run complete transmission experiments.
    It manages the data flow, timing, and result collection.

    Attributes:
        sender: Message source with encoding capability
        channel: Communication channel for message transmission
        receiver: Message receiver with decoding and tracking
    """

    def __init__(
        self,
        sender: Sender[SourceChar, ChannelChar],
        channel: Channel[ChannelChar],
        receiver: TrackingReceiver[SourceChar, ChannelChar],
    ) -> None:
        """
        Initialize the experiment runner with component instances.

        Args:
            sender: Sender instance for generating and encoding messages
            channel: Channel instance for transmitting messages
            receiver: TrackingReceiver instance for receiving, decoding,
                     and collecting statistics

        Raises:
            TypeError: If receiver is not a TrackingReceiver instance
        """
        if not isinstance(receiver, TrackingReceiver):
            raise TypeError("Receiver must be a TrackingReceiver instance")

        self.sender = sender
        """Sender instance for generating and encoding messages."""

        self.channel = channel
        """Channel instance for transmitting messages."""

        self.receiver = receiver
        """TrackingReceiver instance for receiving and decoding messages."""

    def run(
        self,
        num_messages: int = 100,
    ) -> ExperimentResult:
        """
        Run a coding experiment with the configured components.

        This method executes the complete transmission pipeline:
        1. Generate and encode messages using the sender
        2. Transmit messages through the channel
        3. Receive, decode, and track messages using the receiver
        4. Collect and return experiment results

        Args:
            num_messages: Number of messages to transmit (default: 100)
            progress_callback: Optional callback function for reporting
                              progress. It should accept two arguments:
                              current message count and total messages.

        Returns:
            ExperimentResult object containing all experiment data

        Raises:
            ValueError: If num_messages <= 0
        """
        if num_messages <= 0:
            raise ValueError(f"num_messages must be positive, got {num_messages}")

        start_time = time.time()

        # Reset receiver statistics before starting
        self.receiver.reset_stats()

        # Execute the transmission pipeline
        messages = self.sender.message_stream(num_messages)
        transmitted = self.channel.transmit_stream(messages)

        # Process messages and track progress
        results = []
        for i, success in enumerate(self.receiver.receive_stream(transmitted)):
            results.append(success)

        end_time = time.time()

        # Create and return experiment results
        return ExperimentResult(
            stats=self.receiver.get_stats(),
            start_time=start_time,
            end_time=end_time,
            metadata={
                "num_messages": num_messages,
                "success_count": sum(results),
                "failure_count": len(results) - sum(results),
                "components": {
                    "sender_type": type(self.sender).__name__,
                    "channel_type": type(self.channel).__name__,
                    "receiver_type": type(self.receiver).__name__,
                },
            },
        )



