import logging
import os
import re
from getpass import getpass
from pathlib import Path
from typing import Any, Optional

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
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Extra, ValidationError, root_validator, validator
from pydantic.env_settings import SettingsSourceCallable

from pypre.objects.site import Site
from pypre.utils.types import SourcesTuple


def toml_encrypted_config(settings: BaseSettings) -> dict[str, Any]:
    with open(Path(os.environ.get("PYPRE_CONFIG", "config.toml")), "rb") as cfg_file:
        try:
            return tomllib.load(cfg_file)
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as e:  # Config file is probably encrypted
            if not has_crypto:
                logging.exception(
                    (
                        "Config file seems to be encrypted but 'cryptography' is missing."
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
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> SourcesTuple:
            return (init_settings, env_settings, toml_encrypted_config, file_secret_settings)


load_dotenv(dotenv_path=find_dotenv(usecwd=True))

try:
    config = Config()
except ValidationError as e:
    logging.exception("An error has occured when validating config", exc_info=e)
    raise SystemExit()
