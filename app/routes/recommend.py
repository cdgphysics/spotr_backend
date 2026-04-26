from fastapi import APIRouter, HTTPException, Query

from app.ml.clustering import DEFAULT_K
from app.ml.recommender import recommend

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/{user_id}")
def get_recommendations(
    user_id: int,
    k: int = Query(DEFAULT_K, ge=1, le=20),
    limit: int = Query(20, ge=1, le=100),
):
    result = recommend(user_id=user_id, k=k, limit=limit)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result
