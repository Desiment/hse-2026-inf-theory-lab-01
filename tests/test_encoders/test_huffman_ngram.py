import math

import pytest

from codinglab.encoders.huffman_ngram import BinaryAlphabet, HuffmanNgramCoder

SIMPLE_PROBS = {"a": 0.5, "b": 0.3, "c": 0.2}
UNIFORM_PROBS = {"a": 0.5, "b": 0.5}


@pytest.fixture()
def coder_n1() -> HuffmanNgramCoder:
    return HuffmanNgramCoder(n=1, probabilities=SIMPLE_PROBS)


@pytest.fixture()
def coder_n2() -> HuffmanNgramCoder:
    return HuffmanNgramCoder(n=2, probabilities=SIMPLE_PROBS)


@pytest.fixture()
def coder_n3() -> HuffmanNgramCoder:
    return HuffmanNgramCoder(n=3, probabilities=SIMPLE_PROBS)


@pytest.fixture()
def coder_uniform_n2() -> HuffmanNgramCoder:
    return HuffmanNgramCoder(n=2, probabilities=UNIFORM_PROBS)


class TestValidation:
    def test_n_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="n must be at least 1"):
            HuffmanNgramCoder(n=0, probabilities=SIMPLE_PROBS)

    def test_negative_n_raises(self) -> None:
        with pytest.raises(ValueError, match="n must be at least 1"):
            HuffmanNgramCoder(n=-1, probabilities=SIMPLE_PROBS)

    def test_zero_probability_raises(self) -> None:
        with pytest.raises(ValueError, match="All probabilities must be positive"):
            HuffmanNgramCoder(n=1, probabilities={"a": 0.5, "b": 0.0, "c": 0.5})

    def test_probs_not_summing_to_one_raises(self) -> None:
        with pytest.raises(ValueError, match="Probabilities must sum to 1.0"):
            HuffmanNgramCoder(n=1, probabilities={"a": 0.5, "b": 0.3})

    def test_valid_input_creates_coder(self) -> None:
        coder = HuffmanNgramCoder(n=1, probabilities=SIMPLE_PROBS)
        assert coder is not None
        assert coder.n == 1


class TestCodeTable:
    def test_ngram_count_n1(self, coder_n1: HuffmanNgramCoder) -> None:
        assert coder_n1.code_table is not None
        assert len(coder_n1.code_table) == 4

    def test_ngram_count_n2(self, coder_n2: HuffmanNgramCoder) -> None:
        assert coder_n2.code_table is not None
        assert len(coder_n2.code_table) == (3 + 1) ** 2

    def test_all_codewords_binary(self, coder_n2: HuffmanNgramCoder) -> None:
        assert coder_n2.code_table is not None
        for code in coder_n2.code_table.values():
            for bit in code:
                assert bit in BinaryAlphabet


class TestRoundtrip:
    @pytest.mark.parametrize(
        "message",
        [
            [("a",)],
            [("a",), ("b",)],
            [("a",), ("c",), ("b",)],
        ],
    )
    def test_roundtrip_n1_direct(
        self, coder_n1: HuffmanNgramCoder, message: list
    ) -> None:
        encoded = coder_n1.encode(message)
        decoded = coder_n1.decode(encoded)
        assert list(decoded) == message

    def test_roundtrip_n2_direct(self, coder_n2: HuffmanNgramCoder) -> None:
        ngrams = [("a", "a"), ("a", "b"), ("b", "c")]
        encoded = coder_n2.encode(ngrams)
        decoded = coder_n2.decode(encoded)
        assert list(decoded) == ngrams


class TestEncodeDecodeText:
    def test_roundtrip_exact_multiple(self, coder_n2: HuffmanNgramCoder) -> None:
        text = ["a", "b", "c", "a", "b", "c"]
        bits = coder_n2.encode_text(text)
        recovered: list[str] = coder_n2.decode_text(bits)
        assert recovered == text

    def test_roundtrip_with_padding(self, coder_n2: HuffmanNgramCoder) -> None:
        text = ["a", "b", "c"]
        bits = coder_n2.encode_text(text)
        recovered: list[str] = coder_n2.decode_text(bits)
        assert recovered == text

    def test_roundtrip_long(self, coder_n3: HuffmanNgramCoder) -> None:
        text = ["a", "b", "c", "a", "a", "b", "c", "a", "b"] * 5
        bits = coder_n3.encode_text(text)
        recovered: list[str] = coder_n3.decode_text(bits)
        assert recovered == text

    def test_single_symbol_padded(self, coder_n2: HuffmanNgramCoder) -> None:
        text = ["a"]
        bits = coder_n2.encode_text(text)
        recovered: list[str] = coder_n2.decode_text(bits)
        assert recovered == text

    def test_encode_text_n1_no_padding_needed(
        self, coder_n1: HuffmanNgramCoder
    ) -> None:
        text = ["a", "b", "c"]
        bits = coder_n1.encode_text(text)
        recovered: list[str] = coder_n1.decode_text(bits)
        assert recovered == text


class TestInformationTheory:
    def test_entropy_positive(self, coder_n1: HuffmanNgramCoder) -> None:
        assert coder_n1.entropy > 0

    def test_entropy_formula(self, coder_n1: HuffmanNgramCoder) -> None:
        expected = -sum(p * math.log2(p) for p in SIMPLE_PROBS.values())
        assert math.isclose(coder_n1.entropy, expected, rel_tol=1e-9)

    def test_ngram_entropy_is_n_times_entropy(
        self, coder_n2: HuffmanNgramCoder
    ) -> None:
        assert math.isclose(coder_n2.ngram_entropy, 2 * coder_n2.entropy, rel_tol=1e-9)

    def test_huffman_optimality_n1(self, coder_n1: HuffmanNgramCoder) -> None:
        h = coder_n1.entropy
        l_sym = coder_n1.expected_code_length_per_symbol
        assert l_sym >= h - 1e-9
        assert l_sym < h + 1.0

    def test_huffman_optimality_n2(self, coder_n2: HuffmanNgramCoder) -> None:
        h = coder_n2.entropy
        l_sym = coder_n2.expected_code_length_per_symbol
        assert l_sym >= h - 1e-9
        assert l_sym < h + 1.0 / coder_n2.n

    def test_efficiency_increases_with_n(self) -> None:
        coders = [HuffmanNgramCoder(n=n, probabilities=SIMPLE_PROBS) for n in [1, 2, 3]]
        efficiencies = [c.coding_efficiency for c in coders]
        for i in range(len(efficiencies) - 1):
            assert efficiencies[i + 1] >= efficiencies[i] - 1e-6, (
                f"Эффективность должна расти с увеличением n: "
                f"eta(n={i + 1})={efficiencies[i]:.4f} > "
                f"eta(n={i + 2})={efficiencies[i + 1]:.4f}"
            )

    def test_uniform_distribution_efficiency_n2(
        self, coder_uniform_n2: HuffmanNgramCoder
    ) -> None:
        assert coder_uniform_n2.coding_efficiency > 0.8
