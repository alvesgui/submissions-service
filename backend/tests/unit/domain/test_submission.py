from datetime import UTC

import pytest

from src.core.domain.score import Score
from src.core.domain.submission import (
    InvalidStatusTransitionError,
    Submission,
    SubmissionNotFoundError,
)
from src.core.domain.submission_status import SubmissionStatus


@pytest.mark.unit
class TestSubmissionCriacao:
    """Testa o factory method e o estado inicial da entidade."""

    def test_cria_com_status_pending(self) -> None:
        sub = Submission.create(student_id="aluno-1", s3_key="submissions/abc.txt")
        assert sub.status == SubmissionStatus.PENDING

    def test_cria_com_score_nulo(self) -> None:
        sub = Submission.create(student_id="aluno-1", s3_key="key")
        assert sub.score is None

    def test_cria_com_feedback_nulo(self) -> None:
        sub = Submission.create(student_id="aluno-1", s3_key="key")
        assert sub.feedback is None

    def test_cria_com_retry_count_zero(self) -> None:
        sub = Submission.create(student_id="aluno-1", s3_key="key")
        assert sub.retry_count == 0

    def test_ids_sao_unicos(self) -> None:
        sub1 = Submission.create(student_id="a", s3_key="k1")
        sub2 = Submission.create(student_id="a", s3_key="k2")
        assert sub1.id != sub2.id

    def test_id_tem_26_caracteres(self) -> None:
        """ULID tem sempre 26 caracteres."""
        sub = Submission.create(student_id="a", s3_key="k")
        assert len(sub.id) == 26

    def test_timestamps_sao_utc(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        assert sub.created_at.tzinfo == UTC
        assert sub.updated_at.tzinfo == UTC

    def test_student_id_e_preservado(self) -> None:
        sub = Submission.create(student_id="aluno-xyz", s3_key="k")
        assert sub.student_id == "aluno-xyz"

    def test_s3_key_e_preservada(self) -> None:
        sub = Submission.create(student_id="a", s3_key="submissions/2026/03/abc.txt")
        assert sub.s3_key == "submissions/2026/03/abc.txt"


@pytest.mark.unit
class TestSubmissionTransicoes:
    """Testa as transicoes de estado validas e invalidas."""

    def test_start_processing_muda_status(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        assert sub.status == SubmissionStatus.PROCESSING

    def test_complete_muda_status_score_e_feedback(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.complete(score=Score.of(8.5), feedback="Boa redacao.")

        assert sub.status == SubmissionStatus.COMPLETED
        assert sub.score == Score.of(8.5)
        assert sub.feedback == "Boa redacao."

    def test_fail_muda_status_e_incrementa_retry(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.fail()

        assert sub.status == SubmissionStatus.FAILED
        assert sub.retry_count == 1

    def test_increment_retry_nao_muda_status(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.increment_retry()

        assert sub.status == SubmissionStatus.PROCESSING
        assert sub.retry_count == 1

    def test_nao_pode_completar_sem_processar(self) -> None:
        """PENDING -> COMPLETED nao e permitido."""
        sub = Submission.create(student_id="a", s3_key="k")
        with pytest.raises(InvalidStatusTransitionError):
            sub.complete(score=Score.of(7.0), feedback="ok")

    def test_nao_pode_processar_novamente_apos_completar(self) -> None:
        """COMPLETED -> PROCESSING nao e permitido."""
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.complete(score=Score.of(7.0), feedback="ok")

        with pytest.raises(InvalidStatusTransitionError):
            sub.start_processing()

    def test_nao_pode_processar_apos_falhar(self) -> None:
        """FAILED -> PROCESSING nao e permitido."""
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.fail()

        with pytest.raises(InvalidStatusTransitionError):
            sub.start_processing()

    def test_updated_at_muda_apos_transicao(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        before = sub.updated_at
        sub.start_processing()
        assert sub.updated_at >= before


@pytest.mark.unit
class TestSubmissionPropriedades:
    """Testa as propriedades auxiliares da entidade."""

    def test_is_corrected_false_quando_pending(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        assert sub.is_corrected is False

    def test_is_corrected_true_apos_complete(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.complete(score=Score.of(9.0), feedback="Excelente.")
        assert sub.is_corrected is True

    def test_score_value_none_quando_pending(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        assert sub.score_value is None

    def test_score_value_retorna_decimal_apos_complete(self) -> None:
        from decimal import Decimal

        sub = Submission.create(student_id="a", s3_key="k")
        sub.start_processing()
        sub.complete(score=Score.of(8.5), feedback="ok")
        assert sub.score_value == Decimal("8.50")

    def test_repr_contem_id_e_status(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")
        assert sub.id in repr(sub)
        assert "PENDING" in repr(sub)


@pytest.mark.unit
class TestExcecoesDeDominio:
    """Testa que as excecoes carregam as informacoes corretas."""

    def test_invalid_transition_error_tem_contexto(self) -> None:
        sub = Submission.create(student_id="a", s3_key="k")

        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            sub.complete(score=Score.of(7.0), feedback="ok")

        error = exc_info.value
        assert error.current == SubmissionStatus.PENDING
        assert error.next_status == SubmissionStatus.COMPLETED

    def test_not_found_error_tem_id(self) -> None:
        error = SubmissionNotFoundError("id-123")
        assert "id-123" in str(error)
