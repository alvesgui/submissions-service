from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Score:
    """
    Value Object que representa a nota de uma correcao.
    """

    value: Decimal

    MIN_VALUE: Decimal = Decimal("0.0")
    MAX_VALUE: Decimal = Decimal("10.0")

    def __post_init__(self) -> None:
        """Validacao executada automaticamente apos o __init__."""
        if not isinstance(self.value, Decimal):
            raise TypeError(f"Score.value deve ser Decimal, recebeu {type(self.value).__name__}")
        if not (self.MIN_VALUE <= self.value <= self.MAX_VALUE):
            raise ValueError(
                f"Score deve estar entre {self.MIN_VALUE} e {self.MAX_VALUE}, recebeu {self.value}"
            )

    @classmethod
    def of(cls, value: float | int | str | Decimal) -> "Score":
        """
        Aceita qualquer tipo numerico e converte para Decimal com 2 casas.
        """
        decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(value=decimal_value)

    @property
    def is_passing(self) -> bool:
        """Nota de aprovacao (>= 6.0)"""
        return self.value >= Decimal("6.0")

    def __str__(self) -> str:
        return str(self.value)

    def __float__(self) -> float:
        return float(self.value)
