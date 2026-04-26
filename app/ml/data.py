from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.database.session import engine
from app.models.spotr_user import SpotrUser
from app.models.user_gym import UserGym
from app.models.user_interest import UserInterest


@dataclass
class UserBundle:
    user: SpotrUser
    interests: List[UserInterest] = field(default_factory=list)
    gym_ids: List[int] = field(default_factory=list)


@dataclass
class RecommendationContext:
    target: UserBundle
    candidates: List[UserBundle] = field(default_factory=list)


def load_recommendation_context(user_id: int) -> Optional[RecommendationContext]:
    with Session(engine) as session:
        target = session.get(SpotrUser, user_id)
        if not target:
            return None

        target_gym_ids = [
            row.gym_id
            for row in session.exec(
                select(UserGym).where(UserGym.user_id == user_id)
            ).all()
        ]
        if not target_gym_ids:
            return RecommendationContext(target=UserBundle(user=target, gym_ids=[]))

        target_interests = session.exec(
            select(UserInterest).where(UserInterest.user_id == user_id)
        ).all()

        candidate_id_rows = session.exec(
            select(UserGym.user_id)
            .where(UserGym.gym_id.in_(target_gym_ids))
            .where(UserGym.user_id != user_id)
        ).all()
        candidate_ids = list({uid for uid in candidate_id_rows})
        if not candidate_ids:
            return RecommendationContext(
                target=UserBundle(
                    user=target,
                    interests=list(target_interests),
                    gym_ids=target_gym_ids,
                )
            )

        candidate_users = session.exec(
            select(SpotrUser).where(SpotrUser.id.in_(candidate_ids))
        ).all()
        candidate_users = [
            u for u in candidate_users
            if getattr(u, "accountSetupComplete", None) == "active"
        ]

        interests_by_user: Dict[int, List[UserInterest]] = {}
        for ui in session.exec(
            select(UserInterest).where(UserInterest.user_id.in_(candidate_ids))
        ).all():
            interests_by_user.setdefault(ui.user_id, []).append(ui)

        gyms_by_user: Dict[int, List[int]] = {}
        for row in session.exec(
            select(UserGym).where(UserGym.user_id.in_(candidate_ids))
        ).all():
            gyms_by_user.setdefault(row.user_id, []).append(row.gym_id)

        candidates = [
            UserBundle(
                user=u,
                interests=interests_by_user.get(u.id, []),
                gym_ids=gyms_by_user.get(u.id, []),
            )
            for u in candidate_users
        ]

        return RecommendationContext(
            target=UserBundle(
                user=target,
                interests=list(target_interests),
                gym_ids=target_gym_ids,
            ),
            candidates=candidates,
        )
