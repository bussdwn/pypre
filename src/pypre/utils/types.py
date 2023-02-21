from __future__ import annotations

from typing import Any, TypedDict

from pydantic.env_settings import SettingsSourceCallable
from tqdm import tqdm

SourcesTuple = tuple[SettingsSourceCallable, SettingsSourceCallable, SettingsSourceCallable, SettingsSourceCallable]


class PBarsType(TypedDict):
    job_id: int
    tqdm: tqdm[Any]
    state: dict[str, Any]
