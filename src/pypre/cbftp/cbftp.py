from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Literal
from urllib.parse import urlencode, urljoin

import requests
from requests import ConnectionError, HTTPError

from pypre.cbftp.exceptions import CommandFailure


class CBFTP:
    """A CBFTP client using the REST API.

    Args:
        base_url: The host of the CBFTP instance.
        password: The password to use while authenticating to the API.
        verify: Whether HTTPS requests are verified. As CBFTP is using a self-signed
            certificate, this should be left to `False`.
       proxy: The proxy to use to communicate with the REST API.
    """

    def __init__(
        self,
        base_url: str,
        password: str,
        verify: bool = False,
        proxy: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        if proxy is not None:
            self._session.proxies.update({"all": proxy})
        self._session.auth = ("", password)
        self._session.verify = verify

    @property
    def online(self) -> bool:
        """The CBFTP is online and reachable."""
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
        rq = self._session.request(method, url, **kwargs)
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
        """Send a raw command.

        Args:
            command: The command to send.
            is_async: Whether to wait for the command result.
            sites_all: Send to all available sites.
            sites: Send to the specified sites IDs.
            sites_with_sections: Send to sites with these sections defined.
            path: The path to cwd to before running command.
            path_section: The section to cwd to before running command.
            timeout: Max wait time in seconds before failing.

        Returns:
            Command results from the CBFTP instance.
        """
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
        """Get available sites on the CBFTP instance.

        Args:
            **kwargs: kwargs to be passed to the CBFTP client.

        Returns:
            The list of the site string IDs.
        """
        sites: list[str] = self._get("/sites", **kwargs)
        return sites

    def list_path(
        self,
        site: str,
        path: PurePosixPath | str | None,
        type: Literal["FILE", "DIR"] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """List a directory.

        Args:
            site: The site to be used.
            path: The path to be listed. Can also be a section name.
            type: The type of path to list.
            **kwargs: kwargs to be passed to the CBFTP client.

        Returns:
            A list of path objects.
        """
        params = {"site": site, "path": str(path)}
        # We need to explicitly set params as cbftp isn't decoding urlencoded params
        paths: list[dict[str, Any]] = self._get(f"/path?{urlencode(params, safe='/')}", **kwargs)
        if type is not None:
            return [path for path in paths if path.get("type") == type]
        else:
            return paths

    def get_transferjob(self, *, name: str | None = None, id: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Get data about a transferjob.

        Args:
            name: The name of the transferjob.
            id: The ID of the transferjob to use, if name wasn't provided.

        Returns:
            Data for the transferjob.
        """
        transferjob: dict[str, Any]
        if name is not None:
            transferjob = self._get(f"/transferjobs/{name}", params={"id": "false"}, **kwargs)
        elif id is not None:
            transferjob = self._get(f"/transferjobs/{id}", params={"id": "true"}, **kwargs)
        else:
            raise ValueError("Either name or id must be provided.")
        return transferjob

    def abort_transferjob(self, *, name: str | None = None, id: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Abort a transferjob.

        Args:
            name: The name of the transferjob.
            id: The ID of the transferjob to abort, if name wasn't provided.

        Returns:
            Data for the aborted transferjob.
        """
        abort_info: dict[str, Any]
        if name is not None:
            abort_info = self._post(f"/transferjobs/{name}/abort", params={"id": "false"}, **kwargs)
        elif id is not None:
            abort_info = self._post(f"/transferjobs/{id}/abort", params={"id": "true"}, **kwargs)
        else:
            raise ValueError("Either name or id must be provided.")
        return abort_info
