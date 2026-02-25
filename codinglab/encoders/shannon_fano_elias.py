__all__ = ["ShannonFanoEliasBinaryCoder", "BinaryAlphabet"]

import math
from collections import OrderedDict
from enum import Enum
from typing import Dict, List

from ..types import SourceChar
from .prefix_coder import PrefixEncoderDecoder


class BinaryAlphabet(str, Enum):
    zero = "0"
    one = "1"


class ShannonFanoEliasBinaryCoder(PrefixEncoderDecoder[SourceChar, BinaryAlphabet]):
    """Кодер ШФЭ.

    Для каждого символа x с вероятностью p(x):
        l(x) = ceil(-log2(p(x))) + 1
        F_bar(x) = sum_{a < x} p(a) + p(x) / 2
    """

    def __init__(self, probabilities: OrderedDict[SourceChar, float]) -> None:
        """Инициализация ШФЭ

        Args:
            probabilities: Словарь символ/вероятность.
        """
        if any(p <= 0 for p in probabilities.values()):
            raise ValueError("All probabilities must be positive.")
        total = sum(probabilities.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"Probabilities must sum to 1.0, got {total:.6f}.")

        self._probabilities = probabilities

        # F(x) = sum_{a < x} p(a)
        self._cumulative_probs: Dict[SourceChar, float] = {}
        cumulative = 0.0
        for symbol, prob in probabilities.items():
            self._cumulative_probs[symbol] = cumulative
            cumulative += prob

        # F_bar(x) = F(x) + p(x)/2
        self._modified_cumulative: Dict[SourceChar, float] = {
            s: self._cumulative_probs[s] + p / 2.0 for s, p in probabilities.items()
        }

        # l(x) = ceil(-log2(p(x))) + 1
        self._code_lengths: Dict[SourceChar, int] = {
            s: math.ceil(-math.log2(p)) + 1 for s, p in probabilities.items()
        }

        super().__init__(
            source_alphabet=list(probabilities.keys()),
            channel_alphabet=list(BinaryAlphabet),
        )

    @staticmethod
    def _float_to_binary(value: float, length: int) -> List[BinaryAlphabet]:
        """Преобразуем дробное число в двоичный код заданной длины."""
        bits: List[BinaryAlphabet] = []
        for _ in range(length):
            value *= 2
            if value >= 1.0:
                bits.append(BinaryAlphabet.one)
                value -= 1.0
            else:
                bits.append(BinaryAlphabet.zero)
        return bits

    def _build_prefix_code_tree(self) -> None:
        """Строим таблицу кодов и дерево префиксных кодов."""
        self._code_table = {}
        for symbol in self._probabilities:
            f_bar = self._modified_cumulative[symbol]
            length = self._code_lengths[symbol]
            self._code_table[symbol] = self._float_to_binary(f_bar, length)
        self._build_tree_from_table()

    @property
    def expected_code_length(self) -> float:
        """Ожидаемая длина кода."""
        return sum(
            self._probabilities[s] * self._code_lengths[s] for s in self._probabilities
        )

    @property
    def entropy(self) -> float:
        """Энтропия источника."""
        return -sum(p * math.log2(p) for p in self._probabilities.values())

    @property
    def coding_efficiency(self) -> float:
        """Эффективность кодирования."""
        l_avg = self.expected_code_length
        return 0.0 if l_avg == 0 else self.entropy / l_avg
