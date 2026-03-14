from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Classe base para todos os models SQLAlchemy.
    Importante: O Alembic usa essa Base para detectar mudancas e gerar migrations (versionar banco).
    """

    pass


class SubmissionModel(Base):
    """
    Model SQLAlchemy da tabela submissions.
    """

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Status usa o ENUM nativo do Postgres criado no schema.sql
    status: Mapped[str] = mapped_column(
        Enum(
            "PENDING",
            "PROCESSING",
            "COMPLETED",
            "FAILED",
            name="submission_status",
            create_constraint=False,
            create_type=False,
        ),
        nullable=False,
        default="PENDING",
    )

    # Nota com 2 casas decimais/None
    score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"SubmissionModel(id={self.id!r}, "
            f"student_id={self.student_id!r}, "
            f"status={self.status!r})"
        )
