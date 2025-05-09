"""Main script."""
from __future__ import annotations

from click_aliases import ClickAliasedGroup
import click

from .create_lib import create_library
from .sync_remote import sync
from .utils import setup_logging

__all__ = ('main',)


@click.group(cls=ClickAliasedGroup, context_settings={'help_option_names': ('-h', '--help')})
@click.option('-d', '--debug', help='Enable debug level logging.', is_flag=True)
def main(*, debug: bool = False) -> None:  # pragma: no cover
    """Tools for Strawberry libraries."""
    setup_logging(debug=debug)


main.add_command(create_library, aliases=('c', 'cl', 'create', 'create-lib'))
main.add_command(sync, aliases=('s',))
