import math
from collections import OrderedDict

import pytest

from codinglab.encoders.shannon_fano_elias import (
    BinaryAlphabet,
    ShannonFanoEliasBinaryCoder,
)


@pytest.fixture()
def simple_coder() -> ShannonFanoEliasBinaryCoder:
    probs: OrderedDict[str, float] = OrderedDict([("a", 0.75), ("b", 0.25)])
    return ShannonFanoEliasBinaryCoder(probs)


@pytest.fixture()
def example_coder() -> ShannonFanoEliasBinaryCoder:
    probs: OrderedDict[str, float] = OrderedDict(
        [("a", 0.75), ("b", 0.025), ("c", 0.1), ("d", 0.05), ("e", 0.075)]
    )
    return ShannonFanoEliasBinaryCoder(probs)


class TestValidation:
    def test_zero_probability_raises(self) -> None:
        probs: OrderedDict[str, float] = OrderedDict(
            [("a", 0.5), ("b", 0.0), ("c", 0.5)]
        )
        with pytest.raises(ValueError, match="positive"):
            ShannonFanoEliasBinaryCoder(probs)

    def test_negative_probability_raises(self) -> None:
        probs: OrderedDict[str, float] = OrderedDict([("a", 1.2), ("b", -0.2)])
        with pytest.raises(ValueError, match="positive"):
            ShannonFanoEliasBinaryCoder(probs)

    def test_probabilities_not_summing_to_one_raises(self) -> None:
        probs: OrderedDict[str, float] = OrderedDict([("a", 0.5), ("b", 0.3)])
        with pytest.raises(ValueError, match="sum"):
            ShannonFanoEliasBinaryCoder(probs)

    def test_valid_probabilities_do_not_raise(self) -> None:
        probs: OrderedDict[str, float] = OrderedDict([("a", 0.5), ("b", 0.5)])
        coder = ShannonFanoEliasBinaryCoder(probs)
        assert coder is not None


class TestCodeLengths:
    def test_code_length_single_dominant(
        self, simple_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert simple_coder._code_lengths["a"] == 2

        assert simple_coder._code_lengths["b"] == 3

    def test_code_lengths_example(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        coder = example_coder
        for symbol, prob in coder._probabilities.items():
            expected = math.ceil(-math.log2(prob)) + 1
            assert coder._code_lengths[symbol] == expected, (
                f"Wrong code length for {symbol!r}: expected {expected}, "
                f"got {coder._code_lengths[symbol]}"
            )


class TestCodeTable:
    def test_code_table_not_empty(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert example_coder.code_table is not None
        assert len(example_coder.code_table) == 5

    def test_all_symbols_present(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert example_coder.code_table is not None
        for sym in ["a", "b", "c", "d", "e"]:
            assert sym in example_coder.code_table

    def test_codeword_lengths_match(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert example_coder.code_table is not None
        for symbol, code in example_coder.code_table.items():
            expected_len = example_coder._code_lengths[symbol]
            assert len(code) == expected_len, (
                f"Symbol {symbol!r}: expected code length {expected_len}, "
                f"got {len(code)}"
            )

    def test_codewords_use_binary_alphabet(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert example_coder.code_table is not None
        for code in example_coder.code_table.values():
            for bit in code:
                assert bit in BinaryAlphabet


class TestEncodeDecodeRoundtrip:
    @pytest.mark.parametrize(
        "message",
        [
            ["a"],
            ["a", "b"],
            ["a", "a", "a", "b"],
            ["e", "c", "d", "a", "b"],
        ],
    )
    def test_roundtrip(
        self,
        example_coder: ShannonFanoEliasBinaryCoder,
        message: list,
    ) -> None:
        encoded = example_coder.encode(message)
        decoded = example_coder.decode(encoded)
        assert list(decoded) == message

    def test_roundtrip_long_sequence(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        message = ["a", "c", "e", "b", "d"] * 20
        encoded = example_coder.encode(message)
        decoded = example_coder.decode(encoded)
        assert list(decoded) == message


class TestInformationTheory:
    def test_entropy_binary(self, simple_coder: ShannonFanoEliasBinaryCoder) -> None:
        expected = -(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        assert math.isclose(simple_coder.entropy, expected, rel_tol=1e-9)

    def test_expected_code_length_positive(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        assert example_coder.expected_code_length > 0

    def test_expected_code_length_above_entropy(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        h = example_coder.entropy
        l_avg = example_coder.expected_code_length
        assert l_avg >= h - 1e-9, f"L={l_avg:.4f} must be >= H={h:.4f}"
        assert l_avg < h + 2.0, f"L={l_avg:.4f} must be < H+2={h + 2:.4f}"

    def test_coding_efficiency_between_zero_and_one(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        eta = example_coder.coding_efficiency
        assert 0.0 < eta <= 1.0

    def test_coding_efficiency_formula(
        self, example_coder: ShannonFanoEliasBinaryCoder
    ) -> None:
        expected = example_coder.entropy / example_coder.expected_code_length
        assert math.isclose(example_coder.coding_efficiency, expected, rel_tol=1e-9)
