import concurrent.futures
import functools
import logging
from pathlib import PurePosixPath
from time import sleep
from typing import Any

import click
from tqdm import tqdm

from pypre.cbftp import get_cbftp_client
from pypre.objects.site import Site
from pypre.utils.types import PBarsType


class CBFTPManager:
    def __init__(self, cbftp: str) -> None:
        self.cbftp = get_cbftp_client(cbftp)
        self.log = logging.getLogger("pypre.manager")
        if not self.cbftp.available():
            self.log.critical("The CBFTP server %r is not reachable.", cbftp)
            raise SystemExit()

    def _get_dst_path(self, site: Site, release_name: str) -> PurePosixPath:
        group_dir, default_group_dir = site.get_group_dir(release_name)
        site_group_dirs = self.get_site_group_dirs(site.id, site.groups_dir)

        if group_dir is not None and group_dir.lower().endswith("_int"):
            group_dir = group_dir[:-4]
        if default_group_dir is not None and default_group_dir.lower().endswith("_int"):
            default_group_dir = default_group_dir[:-4]

        if group_dir not in site_group_dirs:
            if default_group_dir is None:
                raise ValueError(f"No group directory matching and no default one provided.")
            if default_group_dir not in site_group_dirs:
                raise ValueError(f"{default_group_dir} does not exist.")
            group_dir = default_group_dir

        return PurePosixPath(site.groups_dir, group_dir)

    def get_sites(self, **kwargs: Any) -> list[str]:
        return self.cbftp.get_sites(**kwargs)

    @functools.cache
    def get_site_group_dirs(self, site_id: str, groups_dir: str, **kwargs: Any) -> list[str]:
        list_path = self.cbftp.list_path(site=site_id, path=groups_dir, type="DIR", **kwargs)
        return [path["name"] for path in list_path]

    def upload(self, site: Site, release_name: str, src_path: str | None = None, **kwargs: Any) -> dict[str, Any]:
        dst_path = self._get_dst_path(site, release_name)
        json = {"dst_site": site.id, "dst_path": str(dst_path), "name": release_name}
        if src_path is not None:
            json["src_path"] = src_path
        transferjobs: dict[str, Any] = self.cbftp._post("/transferjobs", json=json, **kwargs)
        return transferjobs

    def fxp(self, src_site: Site, dst_site: Site, release_name: str, **kwargs: Any) -> dict[str, Any]:
        src_path = self._get_dst_path(src_site, release_name)
        dst_path = self._get_dst_path(dst_site, release_name)

        json = {
            "src_site": src_site.id,
            "src_path": str(src_path),
            "dst_site": dst_site.id,
            "dst_path": str(dst_path),
            "name": release_name,
        }
        transferjobs: dict[str, Any] = self.cbftp._post("/transferjobs", json=json, **kwargs)
        return transferjobs

    def pre(self, release_name: str, sites: list[Site]) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sites)) as executor:
            futures = {}
            for site in sites:
                section = site.get_section(release_name)
                path = self._get_dst_path(site, release_name)
                command = site.pre_command.format(release=release_name, section=section)
                futures[executor.submit(self.cbftp.raw, command, sites=site.id, path=path)] = site

            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                site_id = futures[future].id
                self.log.debug("%s response: %s", site_id, data)

    def check(self, release_name: str, site: Site) -> bool:
        release_dir = self._get_dst_path(site, release_name) / release_name
        list_path = self.cbftp.list_path(site=site.id, path=release_dir)
        return any("COMPLETE" in path["name"].upper() for path in list_path)

    def show_transfer_progress(self, upload_jobs: list[int]) -> None:
        sleep(1)  # Necessary to be sure that cbftp returns the correct number of estimated bytes
        try:
            pbars: list[PBarsType] = [
                {
                    "job_id": job_id,
                    "tqdm": tqdm(
                        total=self.cbftp.get_transferjob(id=job_id)["size_estimated_bytes"],
                        desc=f"Upload #{job_id}",
                        unit="B",
                        position=i,
                        unit_scale=True,
                    ),
                    "state": self.cbftp.get_transferjob(id=job_id),
                }
                for i, job_id in enumerate(upload_jobs)
            ]

            while not all(pbar["state"]["status"] == "DONE" for pbar in pbars):
                for pbar in pbars:
                    pbar["state"] = self.cbftp.get_transferjob(id=pbar["job_id"])
                    pbar["tqdm"].update(pbar["state"]["size_progress_bytes"] - pbar["tqdm"].n)
                sleep(2)
        except KeyboardInterrupt:
            abort = click.confirm("Do you want to abort all running transfer jobs?")
            for pbar in pbars:
                pbar["tqdm"].close()
                if abort:
                    self.cbftp.abort_transferjob(id=pbar["job_id"])
            raise


_managers: dict[str, CBFTPManager] = {}


def get_manager(name: str) -> CBFTPManager:
    manager = _managers.get(name)
    if manager is None:
        manager = CBFTPManager(name)
        _managers[name] = manager
    return manager
