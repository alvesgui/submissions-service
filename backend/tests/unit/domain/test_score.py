from decimal import Decimal

import pytest

from src.core.domain.score import Score


@pytest.mark.unit
class TestScoreCriacao:
    """Testa a criacao do Score via factory method."""

    def test_criar_score_de_float(self) -> None:
        score = Score.of(8.5)
        assert score.value == Decimal("8.50")

    def test_criar_score_de_inteiro(self) -> None:
        score = Score.of(10)
        assert score.value == Decimal("10.00")

    def test_criar_score_de_string(self) -> None:
        score = Score.of("7.25")
        assert score.value == Decimal("7.25")

    def test_criar_score_de_decimal(self) -> None:
        score = Score.of(Decimal("6.00"))
        assert score.value == Decimal("6.00")

    def test_score_minimo_zero(self) -> None:
        score = Score.of(0)
        assert score.value == Decimal("0.00")

    def test_score_maximo_dez(self) -> None:
        score = Score.of(10)
        assert score.value == Decimal("10.00")

    def test_score_arredonda_half_up(self) -> None:
        # 8.555 deve arredondar para 8.56
        score = Score.of("8.555")
        assert score.value == Decimal("8.56")


@pytest.mark.unit
class TestScoreValidacao:
    """Testa as regras de validacao do Score."""

    def test_score_acima_do_maximo_levanta_erro(self) -> None:
        with pytest.raises(ValueError, match="entre"):
            Score.of(10.01)

    def test_score_abaixo_do_minimo_levanta_erro(self) -> None:
        with pytest.raises(ValueError, match="entre"):
            Score.of(-0.01)

    def test_score_e_imutavel(self) -> None:
        """frozen=True -- Value Objects nao podem ser alterados."""
        score = Score.of(8.0)
        with pytest.raises(Exception):
            score.value = Decimal("9.0")  # type: ignore


@pytest.mark.unit
class TestScorePropriedades:
    """Testa as propriedades auxiliares."""

    def test_nota_acima_de_seis_e_aprovacao(self) -> None:
        assert Score.of(6.0).is_passing is True
        assert Score.of(10.0).is_passing is True

    def test_nota_abaixo_de_seis_e_reprovacao(self) -> None:
        assert Score.of(5.9).is_passing is False
        assert Score.of(0.0).is_passing is False

    def test_representacao_em_string(self) -> None:
        assert str(Score.of(8.5)) == "8.50"

    def test_conversao_para_float(self) -> None:
        assert float(Score.of(8.5)) == 8.5

    def test_dois_scores_com_mesmo_valor_sao_iguais(self) -> None:
        """Value Object: igualdade por valor, nao por identidade."""
        score_a = Score.of(7.0)
        score_b = Score.of(7.0)
        assert score_a == score_b
        assert score_a is not score_b
