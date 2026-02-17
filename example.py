"""
Demo script for the coding experiments library.

This script demonstrates a basic experiment using the DummyEncoder
with fixed-length codes, a FixedMessagesSender, a NoiselessChannel,
and a TrackingReceiver. It shows how to set up components, run an
experiment, and analyze the results.

Author: Mikhail Mikhailov
License: MIT
"""

from codinglab import (
    FixedMessagesSender,
    SourceChar,
    ChannelChar,
    PrefixCodeTree,
    PrefixEncoderDecoder,
    NoiselessChannel,
    TrackingReceiver,
    ExperimentRunner,
    ConsoleLogger,
    Channel,
)

from typing import Sequence


class DummyEncoder(PrefixEncoderDecoder[SourceChar, ChannelChar]):
    """
    Fixed-length prefix encoder-decoder.

    This encoder assigns fixed-length codes to source symbols by
    enumerating all possible code sequences of a given length in
    lexicographic order. All codes have the same length, making
    it inefficient for non-uniform symbol distributions but
    simple to implement and understand.

    Attributes:
        _code_length: Fixed length of all code sequences
    """

    def __init__(
        self,
        source_alphabet: Sequence[SourceChar],
        channel_alphabet: Sequence[ChannelChar],
        code_length: int = 1,
    ) -> None:
        """
        Initialize the dummy encoder with fixed code length.

        Args:
            source_alphabet: Sequence of source symbols to encode
            channel_alphabet: Sequence of channel symbols for encoding
            code_length: Fixed length of all code sequences (default: 1)

        Raises:
            ValueError: If code_length is not positive, or if there
                       aren't enough unique codes for all source symbols
        """
        self._code_length = code_length
        """Fixed length of all code sequences."""
        super().__init__(source_alphabet, channel_alphabet)

    def _build_prefix_code_tree(self) -> None:
        """
        Build a prefix code tree with fixed-length codes.

        This method constructs a prefix code tree where each source
        symbol gets a code of exactly _code_length channel symbols.
        Codes are assigned in lexicographic order based on the
        enumeration of all possible code sequences.

        Raises:
            ValueError: If code_length is not positive, or if the
                       channel alphabet doesn't provide enough unique
                       codes for all source symbols
        """
        if self._code_length <= 0:
            raise ValueError(f"Code length must be positive, got {self._code_length}")

        # Calculate maximum number of unique codes available
        max_unique_codes = len(self._channel_alphabet) ** self._code_length
        if max_unique_codes < len(self._source_alphabet):
            raise ValueError(
                f"Cannot encode {len(self._source_alphabet)} symbols with "
                f"code length {self._code_length} and alphabet size "
                f"{len(self._channel_alphabet)} (maximum unique codes: {max_unique_codes})"
            )

        # Build the tree directly
        self._tree = PrefixCodeTree()
        channel_len = len(self._channel_alphabet)
        for i, symbol in enumerate(self._source_alphabet):
            # Generate code for symbol using base-channel_len representation
            code = []
            temp_i = i

            # Convert index i to base-(channel_len) representation
            for _ in range(self._code_length):
                code.append(self._channel_alphabet[temp_i % channel_len])
                temp_i //= channel_len

            # Reverse the code because we generated from least significant digit
            reversed_code = list(reversed(code))

            # Insert code into tree
            self._tree.insert_code(reversed_code, symbol)


def main() -> None:
    """Run a demonstration experiment."""

    print("=" * 60)
    print("Coding Experiments Library - Demo")
    print("=" * 60)

    # Prepare messages
    messages = ["hello", "world", "test", "message", "python", "coding"]

    logger = ConsoleLogger()

    # Extract unique characters from all messages
    all_chars = set()
    for msg in messages:
        for char in msg:
            all_chars.add(char)
    print("\n1. Preparing components:")
    print(f"   Source alphabet: {sorted(all_chars)}")
    print(f"   Number of messages: {len(messages)}")

    # Create encoder with binary channel alphabet
    encoder = DummyEncoder(
        source_alphabet=sorted(all_chars),
        channel_alphabet=["0", "1", "2", "3"],
        code_length=3,
    )

    print("   Encoder: DummyEncoder with code_length=3")
    print(f"   Channel alphabet: {encoder.channel_alphabet}")

    # Create sender with fixed messages
    sender = FixedMessagesSender(
        encoder=encoder,
        messages=list(list(s) for s in messages),
        logger=logger,
    )
    # Create channel
    channel: Channel = NoiselessChannel(logger=logger)

    # Create tracking receiver
    receiver = TrackingReceiver(encoder, logger=logger)

    print("\n2. Running experiment with 3 messages...")

    # Create and run experiment
    runner = ExperimentRunner(sender, channel, receiver)
    result = runner.run(num_messages=3)

    print("\n3. Experiment Results:")
    print(f"   Duration: {result.duration:.4f} seconds")
    print(f"   Total messages: {result.stats.total_messages}")
    print(f"   Successful: {result.stats.successful_messages}")
    print(f"   Failed: {result.stats.failed_messages}")
    print(f"   Success rate: {result.stats.success_rate:.2%}")
    print(f"   Total source symbols: {result.stats.total_source_symbols}")
    print(f"   Total channel symbols: {result.stats.total_channel_symbols}")
    print(f"   Compression ratio: {result.stats.compression_ratio:.2f}")
    print(f"   Average code length: {result.stats.average_code_len:.2f}")
    print(f"   Avg. processing time: {result.stats.avg_message_time:.6f} s/msg")

    print("\n4. Encoding table:")
    if encoder.code_table:
        for symbol, code in sorted(encoder.code_table.items()):
            code_str = "".join(code)
            print(f"   '{symbol}' -> {code_str}")

    print("\n5. Sample encoding/decoding:")

    # Test encoding and decoding directly
    test_message = "hello world"
    print(f"   Test message: '{test_message}'")

    try:
        # Convert string to list of characters
        source_data = list(test_message)
        encoded = encoder.encode(source_data)
        decoded = encoder.decode(encoded)
        decoded_str = "".join(decoded)

        print(f"   Encoded: {''.join(encoded)}")
        print(f"   Decoded: '{decoded_str}'")
        print(f"   Match: {test_message == decoded_str}")
    except ValueError as e:
        print(f"   Error: {e}")
        print(
            f"   Note: Some characters in '{test_message}' may not be in the source alphabet"
        )

    print("\n6. Statistics summary:")
    print(f"   Success rate: {result.stats.success_rate:.1%}")
    print(f"   Compression: {result.stats.compression_ratio:.2f}x")
    print(f"   Code efficiency: {1.0 / result.stats.average_code_len:.1%}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
