import logging.config
from typing import cast

import click

from pypre import __version__
from pypre.commands import fxp, pre, upload
from pypre.config import config

logging.config.dictConfig(config.logging)


@click.group(context_settings={"default_map": config.arguments})
@click.version_option(version=__version__, package_name="pypre")
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
)
@click.pass_context
def main(
    ctx: click.Context,
    debug: bool,
    yes: bool,
    sort: str,
    psort: bool,
    cbftp: str | None,
) -> None:

    ctx.obj = {"debug": debug, "yes": yes, "sort": sort, "psort": psort, "cbftp": cbftp}


main.add_command(upload)
main.add_command(fxp)
main.add_command(pre)

if __name__ == "__main__":
    main()
