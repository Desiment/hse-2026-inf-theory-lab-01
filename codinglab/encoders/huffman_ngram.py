__all__ = ["HuffmanNgramCoder", "PAD"]

import heapq
import itertools
import math
from enum import Enum
from typing import Dict, List, Sequence, Tuple

from ..types import SourceChar
from .prefix_coder import PrefixEncoderDecoder


class BinaryAlphabet(str, Enum):
    zero = "0"
    one = "1"


PAD = "__PAD__"


class HuffmanNgramCoder(PrefixEncoderDecoder[Tuple, BinaryAlphabet]):
    """Кодер Хаффмана для n-грамм.

    Разбиваем символы на блоки длины n и строим код Хаффмана
    над алфавитом n-грамм. Вероятность:
        p(x1, ..., xn) = p(x1) * ... * p(xn)

    Если длина сообщения не кратна n, дополняем символом PAD.
    """

    def __init__(self, n: int, probabilities: Dict[SourceChar, float]) -> None:
        """Инициализация кодера.

        Args:
            n: Длина блока
            probabilities: Словарь символ/вероятность.
                Вероятности положительными и их сумма равна 1.

        Raises:
            ValueError: Если параметры некорректны.
        """
        if n < 1:
            raise ValueError("n must be at least 1")
        if any(p <= 0 for p in probabilities.values()):
            raise ValueError("All probabilities must be positive")
        total = sum(probabilities.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError("Probabilities must sum to 1.0")

        self._n = n
        self._probs = dict(probabilities)

        pad_p = 1e-10
        scale = (1.0 - pad_p) / total
        p_ext: Dict[SourceChar, float] = {
            s: p * scale for s, p in probabilities.items()
        }
        p_ext[PAD] = pad_p  # type: ignore[index]

        self._ngram_p: Dict[Tuple, float] = {}
        for ngram in itertools.product(p_ext.keys(), repeat=n):
            prob = 1.0
            for sym in ngram:
                prob *= p_ext[sym]
            self._ngram_p[ngram] = prob

        super().__init__(
            source_alphabet=list(self._ngram_p.keys()),
            channel_alphabet=list(BinaryAlphabet),
        )

    def _build_prefix_code_tree(self) -> None:
        """Строим дерево через бин кучу."""
        counter = itertools.count()
        heap: List = []
        for ngram, prob in self._ngram_p.items():
            heapq.heappush(heap, (prob, next(counter), {ngram: []}))

        while len(heap) > 1:
            p0, _, t0 = heapq.heappop(heap)
            p1, _, t1 = heapq.heappop(heap)
            merged: Dict[Tuple, List[BinaryAlphabet]] = {}
            for ng, bits in t0.items():
                merged[ng] = [BinaryAlphabet.zero] + bits
            for ng, bits in t1.items():
                merged[ng] = [BinaryAlphabet.one] + bits
            heapq.heappush(heap, (p0 + p1, next(counter), merged))

        if heap:
            _, _, self._code_table = heap[0]
        else:
            self._code_table = {}

        self._build_tree_from_table()

    def encode_text(self, text: Sequence[SourceChar]) -> List[BinaryAlphabet]:
        """Кодируем последовательность символов и если надо добавляем PAD.

        Args:
            text: Последовательность символов

        Returns:
            Список битов
        """
        rem = len(text) % self._n
        if rem:
            text = list(text) + [PAD] * (self._n - rem)  # type: ignore[list-item]
        result: List[BinaryAlphabet] = []
        for i in range(0, len(text), self._n):
            result.extend(self.encode([tuple(text[i : i + self._n])]))
        return result

    def decode_text(self, bits: Sequence[BinaryAlphabet]) -> List[SourceChar]:
        """Декодируем биты и удаляем символы PAD с конца.

        Args:
            bits: Последовательность битов

        Returns:
            Декодированная последовательность символов уже с убранным PAD.
        """
        out: List[SourceChar] = []
        for ngram in self.decode(bits):
            out.extend(ngram)
        while out and out[-1] == PAD:
            out.pop()
        return out

    @property
    def n(self) -> int:
        """Длина блока n-граммы."""
        return self._n

    @property
    def entropy(self) -> float:
        """H(X)"""
        return -sum(p * math.log2(p) for p in self._probs.values())

    @property
    def ngram_entropy(self) -> float:
        """H(X^n) = n * H(X)"""
        return self._n * self.entropy

    @property
    def expected_code_length(self) -> float:
        """Средняя длина кода"""
        if self._code_table is None:
            return 0.0
        return sum(
            self._ngram_p[ng] * len(code) for ng, code in self._code_table.items()
        )

    @property
    def expected_code_length_per_symbol(self) -> float:
        """Средняя длина кода на один символ"""
        return self.expected_code_length / self._n

    @property
    def coding_efficiency(self) -> float:
        """H(X) / (L_avg / n)(эффективность кода)"""
        l_avg = self.expected_code_length_per_symbol
        return 0.0 if l_avg == 0 else self.entropy / l_avg
