from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.outbound.postgres.models import SubmissionModel
from src.core.domain.score import Score
from src.core.domain.submission import Submission
from src.core.domain.submission_status import SubmissionStatus
from src.core.ports.outbound.ports import SubmissionRepository


class PostgresSubmissionRepository(SubmissionRepository):
    """
    Implementacao do repositorio usando PostgreSQL + SQLAlchemy.

    Responsabilidades: Mapeia
    - Converter Submission (dominio) -> SubmissionModel (banco)
    - Converter SubmissionModel (banco) -> Submission (dominio)
    - Queries assincronas
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, submission: Submission) -> None:
        """Converte a entidade para model e persiste no banco."""
        model = self._to_model(submission)
        self._session.add(model)
        await self._session.flush()

    async def update(self, submission: Submission) -> None:
        """Atualiza os campos de uma submissao existente."""
        model = await self._session.get(SubmissionModel, submission.id)
        if model is None:
            return

        model.status = submission.status.value
        model.score = float(submission.score_value) if submission.score_value else None
        model.feedback = submission.feedback
        model.retry_count = submission.retry_count
        model.updated_at = submission.updated_at

        await self._session.flush()

    async def find_by_id(self, submission_id: str) -> Submission | None:
        """Busca por ID e converte para entidade. Retorna None se nao existir."""
        model = await self._session.get(SubmissionModel, submission_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def find_by_student_id(
        self,
        student_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Submission]:
        """Lista submissoes de um aluno ordenadas pela mais recente."""
        stmt = (
            select(SubmissionModel)
            .where(SubmissionModel.student_id == student_id)
            .order_by(SubmissionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_student_id(self, student_id: str) -> int:
        """Conta total de submissoes de um aluno para paginacao."""
        stmt = (
            select(func.count())
            .select_from(SubmissionModel)
            .where(SubmissionModel.student_id == student_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # Conversores privados (banco - model / model - banco)

    def _to_model(self, submission: Submission) -> SubmissionModel:
        """Entidade do dominio -> Model do banco."""
        return SubmissionModel(
            id=submission.id,
            student_id=submission.student_id,
            s3_key=submission.s3_key,
            status=submission.status.value,
            score=float(submission.score_value) if submission.score_value else None,
            feedback=submission.feedback,
            retry_count=submission.retry_count,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
        )

    def _to_entity(self, model: SubmissionModel) -> Submission:
        """Model do banco -> Entidade do dominio."""
        score = Score.of(Decimal(str(model.score))) if model.score is not None else None

        return Submission(
            id=model.id,
            student_id=model.student_id,
            s3_key=model.s3_key,
            status=SubmissionStatus(model.status),
            score=score,
            feedback=model.feedback,
            retry_count=model.retry_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
