from typing import Any, Dict, List, Optional

import numpy as np

from app.ml.clustering import DEFAULT_K, cluster_candidates
from app.ml.data import RecommendationContext, load_recommendation_context
from app.ml.features import build_feature_matrix, build_user_vector


def _candidate_payload(
    bundle, target_gym_ids: List[int], cluster_rank: int, distance: float
) -> Dict[str, Any]:
    """Build the JSON-serializable payload for a single candidate.

    Args:
        bundle: The candidate's `UserBundle`.
        target_gym_ids: Gym IDs the target user belongs to. Used to compute
            ``common_gyms``.
        cluster_rank: 1-based rank of the candidate's cluster (1 = closest
            cluster centroid to the target).
        distance: Euclidean distance from the candidate's feature vector to
            the target's feature vector.

    Returns:
        A dict containing the candidate's basic profile fields, the assigned
        ``cluster_rank``, the rounded ``distance``, and the list of
        ``common_gyms``.
    """
    common_gyms = list(set(target_gym_ids) & set(bundle.gym_ids))
    return {
        "user": {
            "id": bundle.user.id,
            "first_name": bundle.user.first_name,
            "last_name": bundle.user.last_name,
            "city": bundle.user.city,
            "state": bundle.user.state,
            "age": bundle.user.age,
        },
        "cluster_rank": cluster_rank,
        "distance": round(float(distance), 4),
        "common_gyms": common_gyms,
    }


def recommend(user_id: int, k: int = DEFAULT_K, limit: int = 20) -> Optional[Dict[str, Any]]:
    """Generate ranked candidate recommendations for a user.

    Pipeline: load same-gym candidates from the database, build feature
    vectors, run k-means, rank clusters by Euclidean distance from the
    cluster centroid to the target user's feature vector, then sort
    candidates by ``(cluster_rank, intra-cluster distance)``.

    Args:
        user_id: ID of the target `SpotrUser`.
        k: Desired number of clusters. Clamped to the candidate pool size by
            `cluster_candidates`.
        limit: Maximum number of recommendations to return.

    Returns:
        A dict with two keys:
            - ``clusters``: list of cluster summaries
              (``cluster_id``, ``rank``, ``centroid_distance``, ``size``)
              ordered from closest to farthest from the target.
            - ``recommendations``: list of candidate payloads from
              `_candidate_payload`, sorted by cluster rank then distance,
              truncated to `limit`.
        Returns ``None`` if no user exists with `user_id`. When the user has
        no candidates (no gym, or no shared-gym users), both lists are empty.
    """
    ctx: Optional[RecommendationContext] = load_recommendation_context(user_id)
    if ctx is None:
        return None
    if not ctx.candidates:
        return {"clusters": [], "recommendations": []}

    target_vector = build_user_vector(ctx.target).reshape(1, -1)
    features = build_feature_matrix(ctx.candidates)
    result = cluster_candidates(features, k=k)

    centroid_distances = np.linalg.norm(result.centroids - target_vector, axis=1)
    cluster_order = np.argsort(centroid_distances)
    rank_by_cluster = {int(c): rank + 1 for rank, c in enumerate(cluster_order)}

    target_gym_ids = ctx.target.gym_ids
    candidate_distances = np.linalg.norm(features - target_vector, axis=1)

    recommendations = []
    for idx, bundle in enumerate(ctx.candidates):
        cluster_id = int(result.labels[idx])
        recommendations.append(
            _candidate_payload(
                bundle,
                target_gym_ids=target_gym_ids,
                cluster_rank=rank_by_cluster[cluster_id],
                distance=candidate_distances[idx],
            )
            | {"cluster_id": cluster_id}
        )

    recommendations.sort(key=lambda r: (r["cluster_rank"], r["distance"]))

    clusters = [
        {
            "cluster_id": int(c),
            "rank": rank_by_cluster[int(c)],
            "centroid_distance": round(float(centroid_distances[int(c)]), 4),
            "size": int((result.labels == c).sum()),
        }
        for c in cluster_order
    ]

    return {
        "clusters": clusters,
        "recommendations": recommendations[:limit],
    }
