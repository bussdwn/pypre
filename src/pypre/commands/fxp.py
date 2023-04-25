import io
import itertools
import logging
from pathlib import Path
from typing import Iterable, Optional, cast

import click
from natsort import natsorted

from pypre.config import config
from pypre.manager import CBFTPManager
from pypre.utils.click import CtxObj, GlobPaths


@click.command(name="fxp", short_help="FXP releases to site(s).")
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
    "-f",
    "--from",
    "from_",
    type=click.Choice(cast(list[str], config.sites.keys())),
    required=True,
    help="Site to FXP from.",
)
@click.option(
    "-t",
    "--to",
    type=click.Choice(cast(list[str], config.sites.keys())),
    required=True,
    multiple=True,
    help="Site(s) to FXP to.",
)
@click.option(
    "-w",
    "--wait",
    is_flag=True,
    help="Wait for FXP transfers to complete before exiting.",
)
@click.option("-c", "--check", is_flag=True, help="Check completeness of releases after upload.")
@click.pass_context
def fxp(
    ctx: click.Context,
    releases: tuple[Path, ...],
    glob: tuple[list[Path], ...],
    file: Optional[io.TextIOWrapper],
    from_: str,
    to: tuple[str, ...],
    wait: bool,
    check: bool,
) -> None:
    log = logging.getLogger("pypre.fxp")

    ctx_obj: CtxObj = ctx.obj

    if from_ in to:
        log.critical("Can't FXP to the site the releases were uploaded to.")
        raise SystemExit()

    to_set = set(to)

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

    fxp_releases(ctx_obj.manager, release_names, from_, to_set, wait, check)


def fxp_releases(
    manager: CBFTPManager,
    releases: Iterable[str],
    from_: str,
    to: Iterable[str],
    wait: bool,
    check: bool,
) -> None:
    log = logging.getLogger("pypre.fxp")

    upload_jobs = []
    for site in to:
        for release in releases:
            log.info("FXP %s from %s to %s...", release, from_, site)
            transfer_data = manager.fxp(
                src_site=config.sites[from_],
                dst_site=config.sites[site],
                release_name=release,
            )
            upload_jobs.append(transfer_data["id"])

    if wait:
        manager.show_transfer_progress(upload_jobs)
    if check:
        for site in to:
            for release in releases:
                is_complete = manager.check(release, config.sites[site])
                if is_complete:
                    log.info("%s is complete on %s", release, site)
                else:
                    log.warning("%s is incomplete on %s", release, site)
