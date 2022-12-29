from typing import Optional

from pydantic import BaseModel, validator


class DirConfig(BaseModel):
    all: Optional[str]
    match_group: Optional[bool]
    default: Optional[str]
    group_map: Optional[dict[str, str]]


class Site(BaseModel):
    id: str
    groups_dir: str
    pre_command: str
    dir_config: DirConfig
    sections_config: dict[str, str] = {}

    @validator("groups_dir")
    def starts_with_slash(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("'groups_dir' must start with '/'")
        return v

    @validator("pre_command")
    def is_pre_command(cls, v: str) -> str:
        if not all(template in v for template in ("{release}", "{section}")):
            raise ValueError("'pre_command' must be a template string containing '{release}' and '{section}'")
        return v

    def get_group_dir(self, release_name: str) -> tuple[str | None, str | None]:
        default = self.dir_config.default
        release_tag = release_name.rsplit("-", 1)[1]

        if self.dir_config.all:
            return (self.dir_config.all, default)
        elif self.dir_config.match_group:
            return (release_tag, default)
        elif self.dir_config.group_map:
            group = self.dir_config.group_map.get(release_tag)
            if group is None and default is None:
                raise ValueError("Couldn't find any matching group, and no default value was provided.")
            return (group, default)
        else:
            raise ValueError("Invalid site configuration.")

    def get_section(self, release_name: str) -> str:
        from pypre.config import config

        for section, regex in config.sections:
            if regex.match(release_name):
                return self.sections_config.get(section, section)
        raise ValueError(f"Couldn't find any matching section for {release_name}")
