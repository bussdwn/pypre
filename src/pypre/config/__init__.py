import logging
import os
import re
from pathlib import Path
from typing import Any, Optional, TypeVar

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

from dotenv import find_dotenv, load_dotenv
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Extra, ValidationError, root_validator, validator

from pypre.objects.site import Site

C = TypeVar("C", bound="Config")


class Cbftp(BaseModel):
    base_url: AnyHttpUrl
    password: str
    verify: bool = False
    proxy: Optional[str] = None


class Config(BaseSettings):
    sections: list[tuple[str, re.Pattern[str]]]
    sites: dict[str, Site]
    cbftp: dict[str, Cbftp]
    proxies: dict[str, str] = {}
    arguments: dict[str, str] = {}
    logging: dict[str, Any]

    @validator("sections", pre=True, each_item=True)
    def tuple_length_is_two(cls, v: tuple[str, str]) -> tuple[str, re.Pattern[str]]:
        if not len(v) == 2:
            raise ValueError("'sections' must be defined as a list of 2-tuples")

        return (v[0], re.compile(v[1], flags=re.I))

    @root_validator(skip_on_failure=True)
    def validate_config(cls, values: dict[str, Any]) -> dict[str, Any]:
        proxies_names = values["proxies"].values()
        for cbftp_cfg in values["cbftp"].values():
            proxy_name = cbftp_cfg.proxy
            if proxy_name is not None and proxy_name not in proxies_names:
                raise ValueError(f"{proxy_name} is not defined in the proxies configuration")

        available_sections = [v[0] for v in values["sections"]]
        for site in values["sites"].values():
            if site.sections_config is not None:
                for site_section in site.sections_config.keys():
                    if site_section not in available_sections:
                        raise ValueError(f"{site_section} is not defined in the sections configuration")

        return values

    class Config:
        extra = Extra.ignore

    @classmethod
    def from_toml(cls: type[C], path: Path) -> C:
        if not path.exists():
            raise FileNotFoundError(f"Config file path ({path}) was not found")
        if not path.is_file():
            raise FileNotFoundError(f"Config file path ({path}) is not to a file.")
        with open(path, "rb") as config_file:
            return cls(**tomllib.load(config_file))


load_dotenv(dotenv_path=find_dotenv(usecwd=True))

try:
    config = Config.from_toml(Path(os.environ.get("PYPRE_CONFIG", "config/config.toml")))
except ValidationError as e:
    logging.exception("An error occurred when validating config", e)
