# codinglab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Desiment/hse-2026-inf-theory-lab-01/actions/workflows/ci.yml/badge.svg)](https://github.com/Desiment/hse-2026-inf-theory-lab-01/actions/workflows/ci.yml)
[![Coverage - pytest](https://img.shields.io/badge/coverage-pytest-brightgreen.svg)](https://github.com/Desiment/hse-2026-inf-theory-lab-01/actions)

A modular, type-safe library for experiments with information coding algorithms in educational and research contexts. The library implements a streaming pipeline architecture with clear separation of responsibilities between components.


## Installation

```bash
git clone https://github.com/Desiment/hse-2026-inf-theory-lab-01
cd codinglab
poetry install
```

In case you want to play around, you probably should enter poetry shell
```bash
poetry shell
```


## Quick Start
```python

from codinglab import (
    ProbabilisticSender,
    NoiselessChannel,
    TrackingReceiver,
    IdentityEncoder,
    ExperimentRunner,
)

# Setup components
encoder = IdentityEncoder()
sender = ProbabilisticSender(
    encoder=encoder,
    probabilities={0: 0.5, 1: 0.5},
    message_length_range=(10, 20),
    seed=42
)
channel = NoiselessChannel()
receiver = TrackingReceiver(encoder)

# Run experiment
runner = ExperimentRunner(sender, channel, receiver)
result = runner.run(num_messages=100)

# Analyze results
print(result.summary())
```

## Development
Prerequisites
- Python 3.11 or higher
- Poetry for dependency management

```bash

# Clone the repository
git clone https://github.com/Desiment/codinglab.git
cd codinglab

# Install dependencies
poetry install --with dev,docs

# Run tests
poetry run pytest

# Run type checking
poetry run mypy codinglab

# Run linting
poetry run ruff check codinglab
poetry run ruff format codinglab
```
