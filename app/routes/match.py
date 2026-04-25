from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
import json
from typing import List, Dict

from app.database.session import engine
from app.models.spotr_user import SpotrUser
from app.models.user_gym import UserGym
from app.models.user_interest import UserInterest

router = APIRouter(prefix="/match", tags=["match"])


def _parse_days(days_str: str) -> List[str]:
    if not days_str:
        return []
    return [d.strip().lower() for d in days_str.split(",") if d.strip()]


def _time_to_minutes(t: str) -> int:
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0


def _time_overlap(s1: str, e1: str, s2: str, e2: str) -> float:
    a1 = _time_to_minutes(s1)
    b1 = _time_to_minutes(e1)
    a2 = _time_to_minutes(s2)
    b2 = _time_to_minutes(e2)
    if a1 >= b1 or a2 >= b2:
        return 0.0
    start = max(a1, a2)
    end = min(b1, b2)
    if end <= start:
        return 0.0
    overlap = end - start
    shorter = min(b1 - a1, b2 - a2)
    if shorter <= 0:
        return 0.0
    return overlap / shorter


def _score_interest(u_int: UserInterest, c_int: UserInterest, u_age: int, c_age: int) -> float:
    # workout_types stored as JSON text in DB; convert safely
    u_wt = []
    c_wt = []
    try:
        if getattr(u_int, "workout_types"):
            u_wt = json.loads(u_int.workout_types)
    except Exception:
        u_wt = [s.strip().lower() for s in (u_int.workout_types or "").split(",") if s.strip()]
    try:
        if getattr(c_int, "workout_types"):
            c_wt = json.loads(c_int.workout_types)
    except Exception:
        c_wt = [s.strip().lower() for s in (c_int.workout_types or "").split(",") if s.strip()]

    u_wt = [s.lower() for s in u_wt]
    c_wt = [s.lower() for s in c_wt]

    # weights preference (priority)
    weights_score = 40 if ("weights" in u_wt and "weights" in c_wt) else 0

    # days overlap
    u_days = _parse_days(u_int.days or "")
    c_days = _parse_days(c_int.days or "")
    if not u_days or not c_days:
        days_score = 0
    else:
        inter = len(set(u_days) & set(c_days))
        union = len(set(u_days) | set(c_days))
        days_score = 20 * (inter / union) if union > 0 else 0

    # time overlap ratio -> up to 20 points
    time_score = 0
    if u_int.start_time and u_int.end_time and c_int.start_time and c_int.end_time:
        ratio = _time_overlap(u_int.start_time, u_int.end_time, c_int.start_time, c_int.end_time)
        time_score = 20 * ratio

    # age compatibility: mutual within preferred ranges
    age_score = 0
    # if both have min/max, check if ages fit
    try:
        mutual = False
        if u_int.min_age and u_int.max_age:
            if c_age and (u_int.min_age <= c_age <= u_int.max_age):
                mutual = True
        if c_int.min_age and c_int.max_age:
            if u_age and (c_int.min_age <= u_age <= c_int.max_age) and mutual:
                age_score = 20
            elif u_age and (c_int.min_age <= u_age <= c_int.max_age):
                age_score = 10
        elif mutual:
            age_score = 10
    except Exception:
        age_score = 0

    total = weights_score + days_score + time_score + age_score
    return total


@router.get("/weighted/{user_id}")
def find_users_by_weighted_interest(user_id: int, limit: int = 20):
    with Session(engine) as session:
        # verify user
        user = session.get(SpotrUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if getattr(user, "accountSetupComplete", None) != "active":
            raise HTTPException(status_code=403, detail="Account setup not complete")

        # user's gyms
        user_gym_rows = session.exec(select(UserGym).where(UserGym.user_id == user_id)).all()
        gym_ids = [r.gym_id for r in user_gym_rows]
        if not gym_ids:
            return []

        # candidate user ids in same gyms
        cand_stmt = select(UserGym.user_id).where(UserGym.gym_id.in_(gym_ids)).where(UserGym.user_id != user_id)
        candidate_rows = session.exec(cand_stmt).all()
        candidate_ids = list(set(candidate_rows))
        if not candidate_ids:
            return []

        # load candidate users
        candidates = session.exec(select(SpotrUser).where(SpotrUser.id.in_(candidate_ids))).all()
        # filter only active accounts (optional but likely desired)
        candidates = [c for c in candidates if getattr(c, "accountSetupComplete", None) == "active"]
        if not candidates:
            return []

        # load interests for current user and candidates
        user_interests = session.exec(select(UserInterest).where(UserInterest.user_id == user_id)).all()
        candidate_interests_map: Dict[int, List[UserInterest]] = {}
        cand_interest_rows = session.exec(select(UserInterest).where(UserInterest.user_id.in_(candidate_ids))).all()
        for ci in cand_interest_rows:
            candidate_interests_map.setdefault(ci.user_id, []).append(ci)

        # compute gym membership map for common gyms
        cand_gyms_rows = session.exec(select(UserGym).where(UserGym.user_id.in_(candidate_ids))).all()
        cand_gyms_map: Dict[int, List[int]] = {}
        for row in cand_gyms_rows:
            cand_gyms_map.setdefault(row.user_id, []).append(row.gym_id)

        results = []
        for cand in candidates:
            best_score = 0.0
            c_interests = candidate_interests_map.get(cand.id, [])
            if not user_interests or not c_interests:
                # minimal score if workout_types include weights
                # check presence
                # try to compute if any interest lists exist
                pass
            for ui in user_interests:
                for ci in c_interests:
                    sc = _score_interest(ui, ci, user.age or 0, cand.age or 0)
                    if sc > best_score:
                        best_score = sc
            # fallback: if no explicit interests, give small boost if candidate has 'weights' anywhere
            if best_score == 0.0:
                for ci in c_interests:
                    try:
                        c_wt = json.loads(ci.workout_types) if ci.workout_types else []
                    except Exception:
                        c_wt = [s.strip().lower() for s in (ci.workout_types or "").split(",") if s.strip()]
                    if "weights" in [s.lower() for s in c_wt]:
                        best_score = 10.0
                        break

            common_gyms = list(set(gym_ids) & set(cand_gyms_map.get(cand.id, [])))

            results.append({
                "user": {
                    "id": cand.id,
                    "first_name": cand.first_name,
                    "last_name": cand.last_name,
                    "city": cand.city,
                    "state": cand.state,
                    "age": cand.age,
                },
                "score": round(best_score, 2),
                "common_gyms": common_gyms,
            })

        # sort by score desc
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
