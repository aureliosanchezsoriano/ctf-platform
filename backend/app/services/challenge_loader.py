import yaml
import logging
from pathlib import Path
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.challenge import (
    Challenge, ChallengeType, ChallengeDifficulty,
    ChallengeCategory, FlagType
)

logger = logging.getLogger(__name__)


# ── YAML schema ──────────────────────────────────────────────────────────────

class DockerConfig(BaseModel):
    image: str
    port: int
    ttl: int = 7200          # seconds — default 2 hours
    cpu: str = "0.5"
    memory: str = "128m"


class FileConfig(BaseModel):
    path: str = "files/"
    filename: str = "challenge.zip"


class HintSchema(BaseModel):
    cost: int = 0
    text: str


class ChallengeSchema(BaseModel):
    id: str                              # slug, e.g. "web-sqli-01"
    name: str
    description: str
    type: ChallengeType
    category: ChallengeCategory
    difficulty: ChallengeDifficulty
    points: int = 100
    required: bool = True
    owasp: str | None = None
    flag_type: FlagType = FlagType.dynamic
    flag_value: str | None = None        # only for static flags
    docker: DockerConfig | None = None
    file: FileConfig | None = None
    unlocks_after: list[str] = []
    hints: list[HintSchema] = []

    @field_validator("docker", mode="before")
    @classmethod
    def docker_required_for_docker_type(cls, v, info):
        # Validator runs after all fields are set — check in sync step below
        return v

    def validate_consistency(self) -> None:
        """Cross-field validation that Pydantic can't do in field validators."""
        if self.type == ChallengeType.docker and not self.docker:
            raise ValueError(f"Challenge '{self.id}' is type 'docker' but missing 'docker:' config")
        if self.type == ChallengeType.file and not self.file:
            raise ValueError(f"Challenge '{self.id}' is type 'file' but missing 'file:' config")
        if self.flag_type == FlagType.static and not self.flag_value:
            raise ValueError(f"Challenge '{self.id}' has static flag but no 'flag_value'")


# ── Loader ────────────────────────────────────────────────────────────────────

def load_yaml_challenges(challenges_dir: Path) -> list[ChallengeSchema]:
    """
    Scan challenges_dir for challenge.yml files and parse them.
    Raises ValueError immediately if any file is malformed.
    """
    schemas = []
    for yml_path in sorted(challenges_dir.glob("*/challenge.yml")):
        try:
            raw = yaml.safe_load(yml_path.read_text())
            schema = ChallengeSchema(**raw)
            schema.validate_consistency()
            schemas.append(schema)
            logger.info(f"Loaded challenge: {schema.id}")
        except Exception as e:
            raise ValueError(f"Invalid challenge.yml at {yml_path}: {e}") from e
    return schemas


async def sync_challenges(db: AsyncSession, challenges_dir: Path) -> int:
    """
    Sync challenges from YAML files into the database.
    - New challenges are inserted.
    - Existing challenges (matched by slug) are updated.
    - Challenges removed from disk are NOT deleted (preserves attempt history).
    Returns the number of challenges synced.
    """
    schemas = load_yaml_challenges(challenges_dir)

    for schema in schemas:
        result = await db.execute(
            select(Challenge).where(Challenge.slug == schema.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update fields that may have changed in the YAML
            existing.name = schema.name
            existing.description = schema.description
            existing.category = schema.category
            existing.difficulty = schema.difficulty
            existing.points = schema.points
            existing.is_required = schema.required
            existing.owasp_ref = schema.owasp
            existing.flag_type = schema.flag_type
            existing.flag_value = schema.flag_value
            existing.docker_config = schema.docker.model_dump() if schema.docker else None
            existing.file_config = schema.file.model_dump() if schema.file else None
            existing.unlocks_after = schema.unlocks_after[0] if schema.unlocks_after else None
            existing.hints = [h.model_dump() for h in schema.hints]
            logger.info(f"Updated challenge: {schema.id}")
        else:
            challenge = Challenge(
                slug=schema.id,
                name=schema.name,
                description=schema.description,
                type=schema.type,
                category=schema.category,
                difficulty=schema.difficulty,
                points=schema.points,
                is_required=schema.required,
                owasp_ref=schema.owasp,
                flag_type=schema.flag_type,
                flag_value=schema.flag_value,
                docker_config=schema.docker.model_dump() if schema.docker else None,
                file_config=schema.file.model_dump() if schema.file else None,
                unlocks_after=schema.unlocks_after[0] if schema.unlocks_after else None,
                hints=[h.model_dump() for h in schema.hints],
                is_active=False,  # teacher must activate explicitly
            )
            db.add(challenge)
            logger.info(f"Inserted challenge: {schema.id}")

    await db.commit()
    return len(schemas)
