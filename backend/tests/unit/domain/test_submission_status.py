import pytest

from src.core.domain.submission_status import SubmissionStatus


@pytest.mark.unit
class TestSubmissionStatusTransitions:
    """Testa todas as transicoes de estado permitidas e bloqueadas."""

    def test_pending_pode_ir_para_processing(self) -> None:
        assert SubmissionStatus.PENDING.can_transition_to(SubmissionStatus.PROCESSING) is True

    def test_pending_nao_pode_ir_para_completed(self) -> None:
        assert SubmissionStatus.PENDING.can_transition_to(SubmissionStatus.COMPLETED) is False

    def test_pending_nao_pode_ir_para_failed(self) -> None:
        assert SubmissionStatus.PENDING.can_transition_to(SubmissionStatus.FAILED) is False

    def test_processing_pode_ir_para_completed(self) -> None:
        assert SubmissionStatus.PROCESSING.can_transition_to(SubmissionStatus.COMPLETED) is True

    def test_processing_pode_ir_para_failed(self) -> None:
        assert SubmissionStatus.PROCESSING.can_transition_to(SubmissionStatus.FAILED) is True

    def test_processing_nao_pode_voltar_para_pending(self) -> None:
        assert SubmissionStatus.PROCESSING.can_transition_to(SubmissionStatus.PENDING) is False

    def test_completed_nao_pode_transicionar_para_nada(self) -> None:
        for status in SubmissionStatus:
            assert SubmissionStatus.COMPLETED.can_transition_to(status) is False

    def test_failed_nao_pode_transicionar_para_nada(self) -> None:
        for status in SubmissionStatus:
            assert SubmissionStatus.FAILED.can_transition_to(status) is False


@pytest.mark.unit
class TestSubmissionStatusProperties:
    """Testa as propriedades auxiliares."""

    def test_completed_e_terminal(self) -> None:
        assert SubmissionStatus.COMPLETED.is_terminal is True

    def test_failed_e_terminal(self) -> None:
        assert SubmissionStatus.FAILED.is_terminal is True

    def test_pending_nao_e_terminal(self) -> None:
        assert SubmissionStatus.PENDING.is_terminal is False

    def test_processing_nao_e_terminal(self) -> None:
        assert SubmissionStatus.PROCESSING.is_terminal is False

    def test_apenas_pending_e_processavel(self) -> None:
        assert SubmissionStatus.PENDING.is_processable is True
        assert SubmissionStatus.PROCESSING.is_processable is False
        assert SubmissionStatus.COMPLETED.is_processable is False
        assert SubmissionStatus.FAILED.is_processable is False

    def test_status_comparavel_com_string(self) -> None:
        """Herda de str"""
        assert SubmissionStatus.PENDING == "PENDING"
        assert SubmissionStatus.COMPLETED == "COMPLETED"
        assert SubmissionStatus.PROCESSING.value == "PROCESSING"
