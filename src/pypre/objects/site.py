from typing import Optional

from pydantic import BaseModel, validator


class DirConfig(BaseModel):
    """Directory configuration relative to a specific site."""

    all: Optional[str]
    """The group directory that will be used in all cases."""

    match_group: Optional[bool]
    """Whether to use a directory matching the group tag."""

    default: Optional[str]
    """The default group directory to use if the determined one does not exist."""

    group_map: Optional[dict[str, str]]
    """A mapping used to determine group directory from the group tag."""


class Site(BaseModel):
    """Site configuration."""

    id: str
    """CBFTP site ID."""

    groups_dir: str
    """Path to the groups dir."""

    pre_command: str
    """Pre command template."""

    dir_config: DirConfig
    """Directory configuration."""

    sections_config: dict[str, str] = {}
    """Sections configuration."""

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

    def __hash__(self) -> int:
        return hash(self.id)

    def get_group_dir(self, release_name: str) -> tuple[Optional[str], Optional[str]]:
        """Determine the group directory from the release name.

        Args:
            release_name: The release name to use when determining group directory.

        Returns:
            A two-tuple containing the group directory to use, and a fallback value if the first one
                does not exist on site.

        Raises:
            ValueError: No group directory could be found, or site configuration is invalid.
        """
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
        """Get site section.

        Args:
            release_name: The release name to use to determine section.

        Returns:
            The section string representation for this site.

        Raises:
            ValueError: If no matching section could be found for this release name.
        """
        from pypre.config import config

        for section, regex in config.sections:
            if regex.match(release_name):
                return self.sections_config.get(section, section)
        raise ValueError(f"Couldn't find any matching section for {release_name}")
