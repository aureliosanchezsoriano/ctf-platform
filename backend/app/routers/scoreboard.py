from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, UserRole
from app.models.challenge import Challenge
from app.models.attempt import Attempt

router = APIRouter(prefix="/api/scoreboard", tags=["scoreboard"])


class ScoreboardEntry(BaseModel):
    rank: int
    username: str
    full_name: str
    class_name: str | None
    points: int
    solved_count: int
    last_solve: str | None


@router.get("", response_model=list[ScoreboardEntry])
async def get_scoreboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Step 1 — fetch all students
    users_result = await db.execute(
        select(User).where(User.role == UserRole.student, User.is_active == True)
    )
    students = users_result.scalars().all()

    # Step 2 — fetch all correct attempts with challenge info
    solved_result = await db.execute(
        select(
            Attempt.user_id,
            Challenge.slug,
            Challenge.points,
            Attempt.attempted_at,
        )
        .join(Challenge, Challenge.id == Attempt.challenge_id)
        .where(Attempt.is_correct == True)
    )
    solved_rows = solved_result.fetchall()

    # Build per-user solve data: {user_id: {slug: solve_time}}
    solve_times: dict = {}
    solved_by_user: dict = {}
    for row in solved_rows:
        uid = str(row.user_id)
        if uid not in solved_by_user:
            solved_by_user[uid] = {"points": 0, "count": 0, "last_solve": None}
            solve_times[uid] = {}
        solved_by_user[uid]["points"] += row.points
        solved_by_user[uid]["count"] += 1
        solve_times[uid][row.slug] = row.attempted_at
        if (solved_by_user[uid]["last_solve"] is None or
                row.attempted_at > solved_by_user[uid]["last_solve"]):
            solved_by_user[uid]["last_solve"] = row.attempted_at

    # Step 3 — fetch all hint attempts with timestamps
    hint_result = await db.execute(
        select(
            Attempt.user_id,
            Attempt.submitted_flag,
            Attempt.attempted_at,
            Challenge.slug,
            Challenge.hints,
        )
        .join(Challenge, Challenge.id == Attempt.challenge_id)
        .where(Attempt.submitted_flag.like("hint:%"))
    )
    hint_rows = hint_result.fetchall()

    # Deduct hint costs only if:
    # 1. User solved the challenge
    # 2. Hint was revealed BEFORE the solve
    deductions: dict = {}
    for row in hint_rows:
        uid = str(row.user_id)
        user_solve_times = solve_times.get(uid, {})
        solve_time = user_solve_times.get(row.slug)

        # Skip if never solved
        if solve_time is None:
            continue

        # Skip if hint was revealed after solving
        if row.attempted_at > solve_time:
            continue

        index = int(row.submitted_flag.split(":")[1])
        hints = row.hints or []
        if index < len(hints):
            cost = hints[index]["cost"]
            deductions[uid] = deductions.get(uid, 0) + cost

    # Step 4 — build scored list
    scored = []
    for student in students:
        uid = str(student.id)
        data = solved_by_user.get(uid, {"points": 0, "count": 0, "last_solve": None})
        net_points = max(0, data["points"] - deductions.get(uid, 0))
        scored.append((net_points, data["last_solve"], student, data["count"]))

    scored.sort(key=lambda x: (-x[0], x[1] or '9999'))

    return [
        ScoreboardEntry(
            rank=i + 1,
            username=s.username,
            full_name=s.full_name,
            class_name=s.class_name,
            points=pts,
            solved_count=count,
            last_solve=last.isoformat() if last else None,
        )
        for i, (pts, last, s, count) in enumerate(scored)
    ]
