"""Resume-vs-fresh decision logic for crash recovery.

The 30-minute threshold is ~1/16 of an 8-hour shift cycle: a resume inside this
window is still operating on the same shift's working set; anything older is
treated as a stale partial that should be re-started from scratch with whatever
findings the manifest already captured injected as a summary.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from .manifest import ManifestState

# Staleness threshold: 30 minutes (about 1/16 of an 8-hour shift).
# Resumes within this window are still operating on the same shift's working set;
# anything older is treated as stale and restarted from scratch.
STALE_RESUME_THRESHOLD_MINUTES = 30

Decision = Literal["resume", "fresh"]


def decide(state: ManifestState, now: datetime) -> Decision:
    # Case 1: Empty manifest
    if not state.steps:
        return "fresh"

    # Case 2: Manifest is complete
    if state.complete:
        return "fresh"

    # Case 3: Manifest is incomplete - check staleness
    last_step = state.steps[-1]
    elapsed = now - last_step.ts
    threshold = timedelta(minutes=STALE_RESUME_THRESHOLD_MINUTES)

    if elapsed <= threshold:
        return "resume"
    else:
        return "fresh"
