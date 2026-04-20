import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy import Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum


class ChallengeType(str, enum.Enum):
    docker = "docker"
    file = "file"


class ChallengeDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class ChallengeCategory(str, enum.Enum):
    web = "web"
    crypto = "crypto"
    forensics = "forensics"
    pwn = "pwn"
    misc = "misc"


class FlagType(str, enum.Enum):
    dynamic = "dynamic"   # HMAC per user — for Docker challenges
    static = "static"     # same for everyone — for file challenges


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # Slug from challenge.yml — e.g. "web-sqli-01"
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    type: Mapped[ChallengeType] = mapped_column(
        SAEnum(ChallengeType, name="challenge_type"),
        nullable=False,
    )
    category: Mapped[ChallengeCategory] = mapped_column(
        SAEnum(ChallengeCategory, name="challenge_category"),
        nullable=False,
    )
    difficulty: Mapped[ChallengeDifficulty] = mapped_column(
        SAEnum(ChallengeDifficulty, name="challenge_difficulty"),
        nullable=False,
    )
    owasp_ref: Mapped[str | None] = mapped_column(String(16), nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    flag_type: Mapped[FlagType] = mapped_column(
        SAEnum(FlagType, name="flag_type"),
        nullable=False,
        default=FlagType.dynamic,
    )
    # Only populated for static flags
    flag_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Docker-specific config stored as JSON
    docker_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # File-specific config stored as JSON
    file_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Prerequisite — slug of another challenge that must be solved first
    unlocks_after: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Hints stored as JSON array: [{cost: 0, text: "..."}, ...]
    hints: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="challenge",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Challenge {self.slug} ({self.type})>"
