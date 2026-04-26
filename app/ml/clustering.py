from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans

DEFAULT_K = 4
RANDOM_STATE = 42


@dataclass
class ClusterResult:
    """Output of `cluster_candidates`.

    Attributes:
        labels: 1-D array of shape ``(n_samples,)`` mapping each candidate to
            its cluster index.
        centroids: 2-D array of shape ``(k, n_features)`` with each cluster's
            centroid.
        k: The number of clusters actually produced (may be smaller than the
            requested `k` when the candidate pool is small).
    """

    labels: np.ndarray
    centroids: np.ndarray
    k: int


def cluster_candidates(features: np.ndarray, k: int = DEFAULT_K) -> ClusterResult:
    """Run k-means on a candidate feature matrix.

    Falls back to a single-cluster result when the candidate pool is too small
    for the requested `k`, so callers don't have to special-case empty/tiny
    inputs.

    Args:
        features: 2-D ``float`` array of shape ``(n_samples, n_features)``.
        k: Desired number of clusters. Effective k is clamped to
            ``min(k, n_samples)`` and floored at 1.

    Returns:
        A `ClusterResult` containing per-sample labels, centroids, and the
        effective `k`. For an empty input, ``labels`` is empty and ``k`` is 0.
    """
    n_samples = features.shape[0]
    if n_samples == 0:
        return ClusterResult(
            labels=np.empty((0,), dtype=np.int32),
            centroids=np.empty((0, features.shape[1] if features.ndim == 2 else 0)),
            k=0,
        )

    # KMeans needs n_clusters <= n_samples; collapse to a single cluster otherwise.
    effective_k = max(1, min(k, n_samples))
    if effective_k == 1:
        centroid = features.mean(axis=0, keepdims=True)
        labels = np.zeros(n_samples, dtype=np.int32)
        return ClusterResult(labels=labels, centroids=centroid, k=1)

    model = KMeans(n_clusters=effective_k, n_init="auto", random_state=RANDOM_STATE)
    labels = model.fit_predict(features)
    return ClusterResult(
        labels=labels.astype(np.int32),
        centroids=model.cluster_centers_,
        k=effective_k,
    )
