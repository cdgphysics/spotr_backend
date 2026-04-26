import json
from typing import List, Optional

import numpy as np

from app.ml.data import UserBundle
from app.models.user_interest import UserInterest

WORKOUT_TYPES = ["weights", "cardio", "calisthenics", "sports", "other"]
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
FEATURE_DIM = 1 + len(WORKOUT_TYPES) + len(DAYS) + 4


def _parse_workout_types(raw: Optional[object]) -> List[str]:
    """Normalize stored workout types into a list of lowercased strings.

    Handles values coming back as a Python list, a JSON-encoded string, or a
    legacy comma-separated string.

    Args:
        raw: The raw `workout_types` value as loaded from the database.

    Returns:
        A list of lowercased workout-type tags. Empty if `raw` is falsy.
    """
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(s).strip().lower() for s in raw if str(s).strip()]
    text = str(raw).strip()
    try:
        decoded = json.loads(text)
        if isinstance(decoded, list):
            return [str(s).strip().lower() for s in decoded if str(s).strip()]
    except (ValueError, TypeError):
        pass
    return [s.strip().lower() for s in text.split(",") if s.strip()]


def _parse_days(raw: Optional[str]) -> List[str]:
    """Split a comma-separated days string into lowercased tokens.

    Args:
        raw: Stored `days` string, e.g. ``"mon,tue,wed"``.

    Returns:
        A list of lowercased day tokens. Empty if `raw` is falsy.
    """
    if not raw:
        return []
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _time_to_fraction(t: Optional[str]) -> float:
    """Convert an ``HH:MM`` time string into a fraction of a day.

    Args:
        t: Time string in ``HH:MM`` format (or ``None``).

    Returns:
        ``minutes_since_midnight / 1440`` as a float in ``[0, 1]``. Returns
        ``0.0`` for missing or malformed inputs.
    """
    if not t:
        return 0.0
    try:
        h, m = t.split(":")
        return (int(h) * 60 + int(m)) / 1440.0
    except (ValueError, AttributeError):
        return 0.0


def _interest_vector(interest: UserInterest) -> np.ndarray:
    """Encode a single `UserInterest` row as a numeric vector.

    Layout: workout-type one-hot, day one-hot, start-time fraction, end-time
    fraction, normalized min_age, normalized max_age.

    Args:
        interest: A `UserInterest` row.

    Returns:
        A 1-D ``float32`` array of length ``FEATURE_DIM - 1`` (excluding the
        user's own age, which is added in `build_user_vector`).
    """
    vec = np.zeros(FEATURE_DIM - 1, dtype=np.float32)
    offset = 0

    wt = set(_parse_workout_types(interest.workout_types))
    for i, name in enumerate(WORKOUT_TYPES):
        vec[offset + i] = 1.0 if name in wt else 0.0
    offset += len(WORKOUT_TYPES)

    days = set(_parse_days(interest.days))
    for i, name in enumerate(DAYS):
        vec[offset + i] = 1.0 if name in days else 0.0
    offset += len(DAYS)

    vec[offset] = _time_to_fraction(interest.start_time)
    vec[offset + 1] = _time_to_fraction(interest.end_time)
    vec[offset + 2] = (interest.min_age or 0) / 100.0
    vec[offset + 3] = (interest.max_age or 0) / 100.0
    return vec


def build_user_vector(bundle: UserBundle) -> np.ndarray:
    """Build a single feature vector for a user.

    The first feature is the user's age (normalized by 100). The remaining
    features are the mean of `_interest_vector` over all of the user's
    `UserInterest` rows. Users with no interests get a zero tail.

    Args:
        bundle: The user's `UserBundle` (user row plus their interests).

    Returns:
        A 1-D ``float32`` array of length `FEATURE_DIM`.
    """
    age = (bundle.user.age or 0) / 100.0
    if bundle.interests:
        stacked = np.stack([_interest_vector(i) for i in bundle.interests])
        rest = stacked.mean(axis=0)
    else:
        rest = np.zeros(FEATURE_DIM - 1, dtype=np.float32)
    return np.concatenate(([age], rest)).astype(np.float32)


def build_feature_matrix(bundles: List[UserBundle]) -> np.ndarray:
    """Stack user vectors into a 2-D feature matrix suitable for clustering.

    Args:
        bundles: Candidate `UserBundle` instances to encode.

    Returns:
        A ``float32`` array of shape ``(len(bundles), FEATURE_DIM)``. When
        `bundles` is empty, returns a ``(0, FEATURE_DIM)`` array.
    """
    if not bundles:
        return np.zeros((0, FEATURE_DIM), dtype=np.float32)
    return np.stack([build_user_vector(b) for b in bundles]).astype(np.float32)
