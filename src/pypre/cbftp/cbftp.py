from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, TypeVar
from urllib.parse import urlencode, urljoin

import requests
from requests import ConnectionError, HTTPError

from pypre.cbftp.exceptions import CommandFailure
from pypre.config import Cbftp, config

C = TypeVar("C", bound="CBFTP")


class CBFTP:
    def __init__(
        self,
        base_url: str,
        password: str,
        verify: bool = False,
        proxy: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if proxy is not None and config.proxies.get(proxy):
            self.session.proxies.update({"all": config.proxies[proxy]})
        self.session.auth = ("", password)
        self.session.verify = verify

    @classmethod
    def from_config(cls: type[C], cbftp_cfg: Cbftp) -> C:
        return cls(**cbftp_cfg.dict())

    def available(self) -> bool:
        try:
            self._request("head", "/")
        except HTTPError:
            # Got response from API (even if not a 2XX one)
            pass
        except ConnectionError:
            return False
        return True

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = urljoin(self.base_url, endpoint)
        rq = self.session.request(method, url, **kwargs)
        rq.raise_for_status()
        return rq.json()

    def _get(self, endpoint: str, params: dict[str, str] | None = None, **kwargs: Any) -> Any:
        return self._request("get", endpoint, params=params, **kwargs)

    def _post(self, endpoint: str, json: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._request("post", endpoint, json=json, **kwargs)

    def raw(
        self,
        command: str,
        is_async: bool = False,
        sites_all: bool = False,
        sites: list[str] | str | None = None,
        sites_with_sections: list[str] | None = None,
        path: PurePosixPath | str | None = None,
        path_section: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if sites_all and (sites is not None or sites_with_sections is not None):
            raise ValueError("Can't request with 'sites_all' and 'sites' or 'sites_with_sections'.")
        if path is not None and path_section is not None:
            raise ValueError("Can't request with 'path' and 'path_section'.")

        if isinstance(sites, str):
            sites = [sites]

        json = {
            "command": command,
            "async": is_async,
            "sites_all": sites_all,
            "sites": sites,
            "sites_with_sections": sites_with_sections,
            "path": str(path),
            "path_section": path_section,
            "timeout": timeout,
        }
        json = {k: v for k, v in json.items() if v is not None}

        cmd_data: dict[str, Any] = self._post("/raw", json=json, **kwargs)
        if cmd_data["failures"]:
            raise CommandFailure(command, cmd_data["failures"])
        return cmd_data

    def get_sites(self, **kwargs: Any) -> list[str]:
        sites: list[str] = self._get("/sites", **kwargs)
        return sites

    def list_path(
        self,
        site: str,
        path: PurePosixPath | str | None,
        type: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        params = {"site": site, "path": str(path)}
        if type is not None:
            params["type"] = type
        # We need to explicitly set params as cbftp isn't decoding urlencoded params
        paths: list[dict[str, Any]] = self._get(f"/path?{urlencode(params, safe='/')}", **kwargs)
        return paths

    def get_transferjob(self, *, name: str | None = None, id: int | None = None, **kwargs: Any) -> dict[str, Any]:
        transferjob: dict[str, Any]
        if name is not None:
            transferjob = self._get(f"/transferjobs/{name}", params={"id": "false"}, **kwargs)
        elif id is not None:
            transferjob = self._get(f"/transferjobs/{id}", params={"id": "true"}, **kwargs)
        else:
            raise ValueError("Either name or id must be provided.")
        return transferjob

    def abort_transferjob(self, *, name: str | None = None, id: int | None = None, **kwargs: Any) -> dict[str, Any]:
        abort_info: dict[str, Any]
        if name is not None:
            abort_info = self._post(f"/transferjobs/{name}/abort", params={"id": "false"}, **kwargs)
        elif id is not None:
            abort_info = self._post(f"/transferjobs/{id}/abort", params={"id": "true"}, **kwargs)
        else:
            raise ValueError("Either name or id must be provided.")
        return abort_info


_clients: dict[str, CBFTP] = {}


def get_cbftp_client(name: str) -> CBFTP:
    client = _clients.get(name)
    if client is None:
        cbftp_cfg = config.cbftp.get(name)
        if cbftp_cfg is None:
            raise ValueError(f"No cbftp configuration found for {name}.")
        client = CBFTP.from_config(cbftp_cfg)
        _clients[name] = client
    return client
