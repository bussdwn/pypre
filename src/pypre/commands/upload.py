import io
import itertools
import logging
from pathlib import Path
from typing import Optional, cast

import click
from natsort import natsorted

from pypre.config import config
from pypre.utils.click import CtxObj, GlobPaths


@click.command(name="upload", short_help="Upload releases to site(s).")
@click.option(
    "-r",
    "--releases",
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
    multiple=True,
    help="Releases to be uploaded, relative to the working directory.",
)
@click.option(
    "-g",
    "--glob",
    type=GlobPaths(at_least_one=False, readable_only=True, files_okay=False, resolve=True),
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
    help="Site(s) to upload to.",
)
@click.option("-w", "--wait", is_flag=True, help="Wait for uploads to complete before exiting.")
@click.option("-c", "--check", is_flag=True, help="Check completeness of releases after upload.")
@click.option(
    "--fxp",
    type=click.Choice(cast(list[str], config.sites.keys())),
    default=None,
    multiple=True,
    help="Site(s) to FXP to. Must be different from the upload site(s).",
)
@click.pass_context
def upload(
    ctx: click.Context,
    releases: tuple[Path, ...],
    glob: tuple[list[Path], ...],
    file: Optional[io.TextIOWrapper],
    site: tuple[str, ...],
    wait: bool,
    check: bool,
    fxp: Optional[tuple[str, ...]],
) -> None:
    log = logging.getLogger("pypre.upload")

    ctx_obj: CtxObj = ctx.obj

    sites = set(site)
    if fxp is not None:
        fxp_set = set(fxp)
        if not sites.isdisjoint(fxp):
            log.critical("Can't FXP to the site(s) the releases were uploaded to.")
            raise SystemExit()

    manager = ctx_obj.manager
    available_sites = set(manager.get_sites())
    if fxp_set is not None and not sites.union(fxp_set).issubset(available_sites):
        log.critical(
            "The following sites are not available: %s",
            ", ".join(sites.union(fxp_set) - available_sites),
        )
        raise SystemExit()

    releases_set = set(itertools.chain(releases, *glob))

    if file is not None:
        file_list = file.read().splitlines()
        for rel in file_list:
            p = Path(rel)
            if p.exists() and p.is_dir():
                releases_set.add(p.resolve())
            else:
                log.warning("%s does not exist or is not a directory, and will be skipped.", rel)

    releases_list = list(filter(None, releases_set))

    reverse = ctx_obj.sort_order == "DSC"
    if ctx_obj.psort:
        releases_list.sort(reverse=reverse)
    else:
        releases_list = natsorted(releases_list, reverse=reverse)

    if not releases_list:
        log.info("No releases provided. Exiting.")
        raise SystemExit()

    upload_jobs = []
    for site_key in sites:
        for release in releases_list:
            log.info("Uploading %s to %s...", release, site_key)
            up_data = manager.upload(
                site=config.sites[site_key],
                release_name=release.name,
                src_path=str(release.parent),
            )
            upload_jobs.append(up_data["id"])

    if wait:
        manager.show_transfer_progress(upload_jobs)
    if check:
        for site_key in sites:
            for release in releases_list:
                release_name = release.name
                is_complete = manager.check(release_name, config.sites[site_key])
                if is_complete:
                    log.info("%s is complete on %s", release, site_key)
                else:
                    log.warning("%s is incomplete on %s", release, site_key)
