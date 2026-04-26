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
    """Return ranked recommendations for a user.

    Args:
        user_id: ID of the target `SpotrUser`.
        k: Desired number of k-means clusters (1-20).
        limit: Maximum number of candidates to return (1-100).

    Returns:
        The dict produced by `recommend`, containing ``clusters`` and
        ``recommendations`` keys.

    Raises:
        HTTPException: ``404`` if no user exists with `user_id`.
    """
    result = recommend(user_id=user_id, k=k, limit=limit)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result
