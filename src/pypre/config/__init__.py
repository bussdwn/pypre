from __future__ import annotations

import logging
import os
import re
from getpass import getpass
from pathlib import Path
from typing import Annotated, Any

from typing_extensions import Self

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

try:
    from cryptography.fernet import InvalidToken

    has_crypto = True
except ModuleNotFoundError:
    has_crypto = False

from dotenv import find_dotenv, load_dotenv

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, ValidationError, model_validator, field_serializer
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

from pypre.objects.site import Site

load_dotenv(dotenv_path=find_dotenv(usecwd=True))


class EncryptedTomlConfigSettingsSource(TomlConfigSettingsSource):
    def _read_file(self, file_path: Path) -> dict[str, Any]:
        with open(file_path, "rb") as cfg_file:
            try:
                return tomllib.load(cfg_file)
            except (UnicodeDecodeError, tomllib.TOMLDecodeError) as e:  # Config file is probably encrypted
                if not has_crypto:
                    logging.exception(
                        (
                            "Config file seems to be encrypted but 'cryptography' is missing. "
                            "Try installing pypre with the following dependency: 'pypre[crypto]'."
                        ),
                        exc_info=e,
                    )
                    raise SystemExit()

            from pypre.crypto import decrypt_config

            cfg_file.seek(0)
            encrypted_data = cfg_file.read()
            key_str = os.environ.get("PYPRE_CONFIG_KEY") or getpass("Enter AES passphrase: ")
            try:
                decrypted_config = decrypt_config(key_str, encrypted_data)
            except InvalidToken:
                while True:
                    key_str = getpass("Invalid AES passphrase, try again: ")
                    try:
                        decrypted_config = decrypt_config(key_str, encrypted_data)
                        break
                    except InvalidToken:
                        pass

            return tomllib.loads(decrypted_config.decode())


class Cbftp(BaseModel):
    base_url: AnyHttpUrl
    password: str
    verify: bool = False
    proxy: str | None = None

    @field_serializer("base_url")
    def serialize_base_url(self, value: AnyHttpUrl) -> str:
        return str(value)

def regex_i_flag(value: Any) -> tuple[str, re.Pattern[str]]:
    if not len(value) == 2:
        raise ValueError("'sections' must be defined as a list of 2-tuples")

    return (value[0], re.compile(value[1], flags=re.I))


SectionTuple = Annotated[tuple[str, re.Pattern[str]], BeforeValidator(regex_i_flag)]


class Config(BaseSettings):
    sections: list[SectionTuple]
    sites: dict[str, Site]
    cbftp: dict[str, Cbftp]
    proxies: dict[str, str] = {}
    arguments: dict[str, str] = {}
    logging: dict[str, Any]

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        proxy_names = self.proxies.values()
        for cbftp_cfg in self.cbftp.values():
            proxy_name = cbftp_cfg.proxy
            if proxy_name is not None and proxy_name not in proxy_names:
                raise ValueError(f"{proxy_name} is not defined in the proxies configuration")

        available_sections = [v[0] for v in self.sections]
        for site in self.sites.values():
            if site.sections_config is not None:
                for site_section in site.sections_config.keys():
                    if site_section not in available_sections:
                        raise ValueError(f"{site_section} is not defined in the sections configuration")

        return self

    model_config = SettingsConfigDict(extra="ignore", toml_file=os.environ.get("PYPRE_CONFIG", "config.toml"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (EncryptedTomlConfigSettingsSource(settings_cls),)


try:
    config = Config()  # type: ignore[call-arg]
except ValidationError as e:
    logging.exception("An error has occured when validating config", exc_info=e)
    raise SystemExit()
