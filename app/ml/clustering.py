from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans

DEFAULT_K = 4
RANDOM_STATE = 42


@dataclass
class ClusterResult:
    labels: np.ndarray
    centroids: np.ndarray
    k: int


def cluster_candidates(features: np.ndarray, k: int = DEFAULT_K) -> ClusterResult:
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
