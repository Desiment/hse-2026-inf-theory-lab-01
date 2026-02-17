.. _user-guide:

User Guide
==========

This guide provides an introduction to the codinglab library, a framework for designing,
implementing, and evaluating coding experiments.

.. _installation:

Installation
------------

For installation, clone the repository and install via poetry:

.. code-block:: bash

   git clone https://github.com/yourusername/codinglab.git
   cd codinglab
   poetry install

Dependencies
~~~~~~~~~~~~

codinglab requires Python 3.11 or higher and depends on the following packages:

* numpy (>=2.4.1) - Numerical operations
* matplotlib (>=3.10.8) - Visualization
* pandas (>=3.0.0) - Data analysis
* graphviz (>=0.21) - Tree visualization

Development dependencies (optional):

* pytest - Testing framework
* mypy - Static type checking
* ruff - Code linting
* sphinx - Documentation generation

.. _basic-concepts:

Basic Concepts
--------------

The codinglab library is built around a modular pipeline architecture for communication
systems. Understanding these core concepts will help you effectively use the library.

The Communication Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~

At its heart, codinglab models a complete communication system as a pipeline of components:

.. code-block:: text

   [Source] → [Encoder] → [Channel] → [Decoder] → [Sink]

Each component in this pipeline is represented by a protocol (interface) in the library,
making it easy to mix and match different implementations.

.. _message:

Message
~~~~~~~

Messages are the fundamental units of data flowing through the pipeline. A `Message` is a
simple container with two attributes:

.. code-block:: python

   from codinglab.types import Message

   # Create a message with integer symbols
   msg1 = Message(id=0, data=[1, 0, 1, 1, 0])

   # Messages can contain any hashable type
   msg2 = Message(id=1, data=["A", "B", "C", "A"])
   msg3 = Message(id=2, data=[True, False, True])

Each message has a unique `id` for tracking purposes and a sequence of `data` symbols.

.. _symbol-types:

Symbol Types
~~~~~~~~~~~~

The library uses type variables to distinguish between different kinds of symbols:

* `SourceChar`: Symbols in the source alphabet (input to encoder)
* `ChannelChar`: Symbols in the channel alphabet (output from encoder)

This type distinction helps ensure type safety when composing components:

.. code-block:: python

   from typing import Sequence
   from codinglab.types import SourceChar, ChannelChar
   from codinglab.interfaces import Encoder

   # An encoder that converts integers to binary strings
   class IntToBinaryEncoder(Encoder[int, str]):
       def encode(self, message: Sequence[int]) -> Sequence[str]:
           return [format(x, 'b') for x in message]

       @property
       def code_table(self):
           return None

.. _encoder-decoder:

Encoder and Decoder
~~~~~~~~~~~~~~~~~~~

Encoders transform source messages into channel symbols. Decoders perform the inverse
operation. The library provides several encoder implementations:

* `PrefixEncoderDecoder`: Base class for prefix codes (Huffman, etc.)
* Custom encoders can implement the `Encoder` protocol

.. code-block:: python

   from codinglab.encoders import PrefixEncoderDecoder

   class MyHuffmanEncoder(PrefixEncoderDecoder):
       def _build_prefix_code_tree(self):
           # Implement Huffman algorithm here
           # Build the code tree and set self._tree
           pass

   encoder = MyHuffmanEncoder(["A", "B", "C"], ["0", "1"])

.. _sender:

Sender
~~~~~~

A sender generates and encodes messages. The library includes two sender implementations:

* `FixedMessagesSender`: Cycles through a predefined list of messages
* `ProbabilisticSender`: Generates random messages with specified probabilities

.. code-block:: python

   from codinglab.senders import FixedMessagesSender, ProbabilisticSender
   from codinglab.encoders import IdentityEncoder

   encoder = IdentityEncoder()

   # Fixed messages sender
   fixed_sender = FixedMessagesSender(
       encoder=encoder,
       messages=[[1,0,1], [0,1,0], [1,1,1]]
   )

   # Probabilistic sender with 80% zeros, 20% ones
   prob_sender = ProbabilisticSender(
       encoder=encoder,
       probabilities={0: 0.8, 1: 0.2},
       message_length_range=(5, 10),
       seed=42  # For reproducibility
   )

.. _channel:

Channel
~~~~~~~

Channels transmit messages, potentially introducing errors. Available channels:

* `NoiselessChannel`: Perfect transmission without errors
* Custom channels can implement the `Channel` protocol

.. code-block:: python

   from codinglab.channels import NoiselessChannel

   # Noiseless channel with logging
   from codinglab.logger import PlainLogger
   logger = PlainLogger()
   channel = NoiselessChannel(logger=logger)

.. _receiver:

Receiver
~~~~~~~~

Receivers accept messages from channels and decode them. The library provides:

* `BaseReceiver`: Simple receiver with basic decoding
* `TrackingReceiver`: Receiver that collects detailed statistics

.. code-block:: python

   from codinglab.receivers import TrackingReceiver
   from codinglab.logger import PandasLogger

   decoder = MyHuffmanEncoder(["A", "B", "C"], ["0", "1"])
   logger = PandasLogger()
   receiver = TrackingReceiver(decoder, logger=logger)

.. _logger:

Logger
~~~~~~

Loggers record transmission events for analysis. Available loggers:

* `PlainLogger`: Stores logs in memory as a list
* `ConsoleLogger`: Prints logs to console
* `NullLogger`: Discards logs (no-op)
* `PandasLogger`: Stores logs in a pandas DataFrame for analysis

.. code-block:: python

   from codinglab.logger import ConsoleLogger, PandasLogger

   # Real-time monitoring
   console_logger = ConsoleLogger(verbose=True)

   # Data analysis with pandas
   pandas_logger = PandasLogger()

   # Later, analyze results
   df = pandas_logger.dataframe
   correct_count = pandas_logger.correctly_decoded

.. _prefix-code-tree:

Prefix Code Tree
~~~~~~~~~~~~~~~~

The library includes a `PrefixCodeTree` data structure for efficient decoding of
prefix codes (where no codeword is a prefix of another). This enables unique
decoding without separators between codewords.

.. code-block:: python

   from codinglab.prefix_code_tree import PrefixCodeTree

   # Build a tree for codes: A="0", B="10", C="11"
   tree = PrefixCodeTree()
   tree.insert_code(["0"], "A")
   tree.insert_code(["1", "0"], "B")
   tree.insert_code(["1", "1"], "C")

   # Decode a sequence
   sequence = ["0", "1", "0", "1", "1"]
   pos = 0
   symbols = []
   while pos < len(sequence):
       symbol, pos = tree.decode(sequence, pos)
       symbols.append(symbol)
   print(symbols)  # ['A', 'B', 'C']

   # Visualize the tree (requires graphviz)
   dot = tree.vizualize() #codespell
   dot.render("code_tree", format="png")

.. _experiment:

Running Experiments
~~~~~~~~~~~~~~~~~~~

The `ExperimentRunner` orchestrates the complete pipeline and collects results:

.. code-block:: python

   from codinglab.experiment import ExperimentRunner
   from codinglab.receivers import TrackingReceiver
   from codinglab.channels import NoiselessChannel
   from codinglab.senders import ProbabilisticSender
   from codinglab.encoders import IdentityEncoder

   # Setup components
   encoder = IdentityEncoder()
   sender = ProbabilisticSender(
       encoder=encoder,
       probabilities={0: 0.5, 1: 0.5},
       message_length_range=(10, 20),
       seed=123
   )
   channel = NoiselessChannel()
   receiver = TrackingReceiver(encoder)

   # Create and run experiment
   runner = ExperimentRunner(sender, channel, receiver)
   result = runner.run(num_messages=100)

   # Analyze results
   print(result.summary())
   print(f"Success rate: {result.stats.success_rate:.2%}")
   print(f"Compression ratio: {result.stats.compression_ratio:.3f}")

.. _statistics:

Statistics and Analysis
~~~~~~~~~~~~~~~~~~~~~~~

The `TrackingReceiver` collects detailed statistics accessible via `TransmissionStats`:

.. code-block:: python

   stats = receiver.get_stats()

   print(f"Total messages: {stats.total_messages}")
   print(f"Successful: {stats.successful_messages}")
   print(f"Failed: {stats.failed_messages}")
   print(f"Decode errors: {stats.decode_errors}")
   print(f"Source symbols: {stats.total_source_symbols}")
   print(f"Channel symbols: {stats.total_channel_symbols}")
   print(f"Avg. code length: {stats.average_code_len:.3f}")
   print(f"Compression ratio: {stats.compression_ratio:.3f}")
   print(f"Avg. processing time: {stats.avg_message_time:.6f}s")

For detailed logging with pandas:

.. code-block:: python

   from codinglab.logger import PandasLogger

   logger = PandasLogger()
   receiver = TrackingReceiver(decoder, logger=logger)

   # Run experiment...

   # Analyze with pandas
   df = logger.dataframe
   decoded_msgs = df[df["event"] == "decoded"]
   print(decoded_msgs.groupby("message_id").count())

.. _next-steps:

Next Steps
----------
For more information, see API Reference
