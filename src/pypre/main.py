import logging.config
from importlib.metadata import version
from typing import cast

import click

from pypre.cbftp import CBFTP
from pypre.commands import fxp, pre, upload
from pypre.config import config
from pypre.manager import CBFTPManager
from pypre.utils.click import CtxObj

logging.config.dictConfig(config.logging)


@click.group(context_settings={"default_map": config.arguments})
@click.version_option(version=version("pypre"), package_name="pypre")
@click.option("--debug", is_flag=True, default=False, help="Set logger level to DEBUG.")
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Answer yes for every confirm dialog.",
)
@click.option(
    "--sort",
    type=click.Choice(["ASC", "DSC"], case_sensitive=False),
    default="ASC",
    show_default=True,
    help="Sorting order of the releases.",
)
@click.option(
    "--psort",
    "--ps",
    is_flag=True,
    default=False,
    help="Use Python sort method. By default, the natsorted method is used.",
)
@click.option(
    "--cbftp",
    type=click.Choice(cast(list[str], config.cbftp.keys())),
    help="Cbftp server to use.",
    required=True,
)
@click.pass_context
def main(
    ctx: click.Context,
    debug: bool,
    yes: bool,
    sort: str,
    psort: bool,
    cbftp: str,
) -> None:
    cbftp_cfg = config.cbftp[cbftp]

    manager = CBFTPManager(
        cbftp=CBFTP(
            name=cbftp,
            proxy=config.proxies.get(cbftp_cfg.proxy) if cbftp_cfg.proxy is not None else None,
            **cbftp_cfg.model_dump(exclude={"proxy"}),
        ),
    )

    ctx.obj = CtxObj(
        debug=debug,
        yes=yes,
        sort_order=sort.upper(),  # type: ignore[arg-type]
        psort=psort,
        manager=manager,
    )


main.add_command(upload)
main.add_command(fxp)
main.add_command(pre)

if __name__ == "__main__":
    main()
