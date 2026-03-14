import re
from decimal import Decimal

from src.core.domain.score import Score
from src.core.domain.submission import SubmissionNotFoundError
from src.core.ports.inbound.use_cases import ProcessSubmissionUseCase
from src.core.ports.outbound.ports import (
    StorageService,
    SubmissionRepository,
)


class ProcessSubmissionUseCaseImpl(ProcessSubmissionUseCase):
    """
    Logica de correcao executada pelo worker.

    Fluxo:
        1. Busca a submissao no banco
        2. Marca como PROCESSING
        3. Le o texto do S3
        4. Calcula a nota
        5. Marca como COMPLETED com nota e feedback
        6. Em caso de erro, incrementa retry(3 vezes) ou marca como FAILED
    """

    # Limite de tentativas antes de marcar como FAILED
    MAX_RETRIES = 3

    # Conectivos que indicam uma boa escrita
    CONNECTIVES = {
        "portanto",
        "porem",
        "contudo",
        "todavia",
        "entretanto",
        "ademais",
        "alem disso",
        "por isso",
        "logo",
        "assim",
        "dessa forma",
        "desse modo",
        "em suma",
        "ou seja",
        "por outro lado",
        "no entanto",
        "em contrapartida",
    }

    def __init__(
        self,
        repository: SubmissionRepository,
        storage: StorageService,
    ) -> None:
        self._repository = repository
        self._storage = storage

    async def execute(self, submission_id: str) -> None:
        # 1: busca a submissao
        submission = await self._repository.find_by_id(submission_id)
        if submission is None:
            raise SubmissionNotFoundError(submission_id)

        try:
            # 2: marca como em processamento
            submission.start_processing()
            await self._repository.update(submission)

            # 3: le o texto do S3
            text = await self._storage.download_text(submission.s3_key)

            # 4: calcula a nota
            score, feedback = self._evaluate(text)

            # 5: marca como concluido
            submission.complete(score=score, feedback=feedback)
            await self._repository.update(submission)

        except Exception:
            # 6: trata falha
            if submission.retry_count >= self.MAX_RETRIES - 1:
                # Marca como FAILED definitivamente
                submission.fail()
            else:
                # Enquanto tentativa < 3 incrementa e deixa para o retry
                submission.increment_retry()
            await self._repository.update(submission)
            raise

    def _evaluate(self, text: str) -> tuple[Score, str]:
        """
        Avalia o texto em 4 criterios e retorna nota e feedback.

        Cada criterio vale 2.5 pontos (total = 10.0).
        """
        scores: dict[str, Decimal] = {
            "extensao": self._score_length(text),
            "vocabulario": self._score_vocabulary(text),
            "estrutura": self._score_structure(text),
            "coesao": self._score_cohesion(text),
        }

        total = sum(scores.values())
        final_score = Score.of(min(total, Decimal("10.0")))

        feedback = self._build_feedback(scores, final_score)
        return final_score, feedback

    def _score_length(self, text: str) -> Decimal:
        """
        Avalia a extensao do texto.
        Menos de 50 palavras = 0.0
        50 a 149 palavras    = 1.25
        150+ palavras        = 2.5
        """
        word_count = len(text.split())
        if word_count >= 150:
            return Decimal("2.5")
        if word_count >= 50:
            return Decimal("1.25")
        return Decimal("0.0")

    def _score_vocabulary(self, text: str) -> Decimal:
        """
        Avalia a diversidade do vocabulario.
        Razao entre palavras unicas e total de palavras.
        Acima de 60% de diversidade = nota maxima.
        """
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return Decimal("0.0")

        diversity = len(set(words)) / len(words)

        if diversity >= 0.6:
            return Decimal("2.5")
        if diversity >= 0.4:
            return Decimal("1.25")
        return Decimal("0.0")

    def _score_structure(self, text: str) -> Decimal:
        """
        Avalia a estrutura do texto.
        Verifica presenca de pontuacao e paragrafos.
        """
        has_punctuation = bool(re.search(r"[.!?]", text))
        has_paragraphs = "\n" in text.strip()
        has_comma = "," in text

        structure_points = sum([has_punctuation, has_paragraphs, has_comma])

        if structure_points >= 3:
            return Decimal("2.5")
        if structure_points >= 2:
            return Decimal("1.25")
        return Decimal("0.0")

    def _score_cohesion(self, text: str) -> Decimal:
        """
        Avalia a escrita, conecteores.
        Conta uso de conectivos que ligam ideias.
        """
        text_lower = text.lower()
        found = sum(1 for c in self.CONNECTIVES if c in text_lower)

        if found >= 3:
            return Decimal("2.5")
        if found >= 1:
            return Decimal("1.25")
        return Decimal("0.0")

    def _build_feedback(
        self,
        scores: dict[str, Decimal],
        final_score: Score,
    ) -> str:
        """Gera um feedback textual baseado nos criterios avaliados."""
        lines = [f"Nota final: {final_score}"]

        criteria_labels = {
            "extensao": "Extensao do texto",
            "vocabulario": "Riqueza de vocabulario",
            "estrutura": "Estrutura e pontuacao",
            "coesao": "Coesao textual",
        }

        for key, label in criteria_labels.items():
            value = scores[key]
            if value >= Decimal("2.5"):
                status = "Excelente"
            elif value >= Decimal("1.25"):
                status = "Regular"
            else:
                status = "Insuficiente"
            lines.append(f"  {label}: {status} ({value}/2.5)")

        if final_score.is_passing:
            lines.append("Resultado: APROVADO")
        else:
            lines.append("Resultado: REPROVADO")

        return "\n".join(lines)
