import io
import itertools
import logging
from pathlib import Path
from time import sleep
from typing import Optional, cast

import click
from natsort import natsorted

from pypre.config import config
from pypre.manager import CBFTPManager
from pypre.utils.click import CtxObj, GlobPaths


@click.command(name="pre", short_help="Pre releases to site(s).")
@click.option(
    "-r",
    "--releases",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    multiple=True,
    help="Releases to be transferred, relative to the working directory.",
)
@click.option(
    "-g",
    "--glob",
    type=GlobPaths(at_least_one=False, readable_only=False, files_okay=False),
    multiple=True,
    help="Process releases matching the provided pattern(s).",
)
@click.option("--file", type=click.File(), help="Process releases from a file list.")
@click.option(
    "-s",
    "--site",
    type=click.Choice(cast(list[str], config.sites.keys())),
    required=True,
    multiple=True,
    help="Site(s) to pre.",
)
@click.option(
    "-c",
    "--cooldown",
    type=click.FloatRange(min=1.0),
    default=5.0,
    show_default=True,
    help="Cooldown between each pre.",
)
@click.pass_context
def pre(
    ctx: click.Context,
    releases: tuple[Path, ...],
    glob: tuple[list[Path], ...],
    file: Optional[io.TextIOWrapper],
    site: tuple[str, ...],
    cooldown: float,
) -> None:
    sites = set(site)

    ctx_obj: CtxObj = ctx.obj

    releases_set = set(itertools.chain(releases, *glob))

    if file is not None:
        file_list = file.read().splitlines()
        for rel in file_list:
            if rel.strip():
                releases_set.add(Path(rel))

    release_names = [release.name for release in filter(None, releases_set)]

    reverse = ctx_obj.sort_order == "DSC"
    if ctx_obj.psort:
        release_names.sort(reverse=reverse)
    else:
        release_names = natsorted(release_names, reverse=reverse)

    pre_releases(ctx_obj.manager, release_names, sites, cooldown)


def pre_releases(manager: CBFTPManager, releases: list[str], sites_keys: set[str], cooldown: float) -> None:
    log = logging.getLogger("pypre.pre")

    sites = [config.sites[site] for site in sites_keys]

    for release_name in releases:
        log.info("Preing %s...", release_name)
        manager.pre(release_name, sites)
        if release_name != releases[-1]:
            sleep(cooldown)
