from __future__ import annotations

from typing import Any, TypedDict

from tqdm import tqdm


class PBarsType(TypedDict):
    job_id: int
    tqdm: tqdm[Any]
    state: dict[str, Any]
