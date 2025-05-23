"""Main script."""
from __future__ import annotations

from shlex import quote
from shutil import which
import asyncio
import importlib.resources as ir
import logging
import os

from anyio import Path
from click_aliases import ClickAliasedGroup
from platformdirs import user_cache_dir
import click

from .utils import create_library as do_create_library, osascript, rsync, setup_logging, ssh

__all__ = ('main',)

USER = os.environ.get('USER', 'default')
log = logging.getLogger(__name__)


@click.command()
@click.argument('directory',
                default=f'{os.getenv("HOME")}/import',
                nargs=1,
                type=click.Path(file_okay=False, path_type=Path, resolve_path=True, writable=True))
@click.option('--database',
              help='Path to the database file.',
              type=click.Path(file_okay=True, path_type=Path, dir_okay=False, resolve_path=True))
@click.option('--include-no-cover', help='Include files without embedded cover art.', is_flag=True)
@click.option('--no-si', help='Do not use SI units.', is_flag=True)
@click.option('--split-dir',
              default=f'{user_cache_dir(ensure_exists=True)}/clem2itunes/split',
              help='Directory to store MP3 files generated by splitting them by their CUE file.',
              type=click.Path(file_okay=False, path_type=Path, resolve_path=True, writable=True))
@click.option('-m', '--max-size', default=32, help='Maximum size in GB.', type=int)
@click.option('--flac', help='Allow FLAC files.', is_flag=True)
@click.option('-t', '--threshold', default=0.6, help='Rating threshold out of 1.', type=float)
def create_library(directory: Path,
                   split_dir: Path,
                   database: Path | None = None,
                   max_size: int = 32,
                   threshold: float = 0.6,
                   *,
                   flac: bool = False,
                   include_no_cover: bool = False,
                   no_si: bool = True) -> None:
    """Create a curated music library from a Strawberry or Clementine database."""  # noqa: DOC501
    if directory == split_dir:
        log.error('Split CUE cache directory cannot be same as output directory.')
        raise click.Abort
    asyncio.run(
        do_create_library(directory,
                          split_dir,
                          database,
                          threshold,
                          max_size,
                          flac=flac,
                          include_no_cover=include_no_cover,
                          use_si=not no_si))


async def _do_sync(host: str,
                   local_dir: Path,
                   remote_create_lib: str,
                   remote_dir: str,
                   splitcue_cache_dir: str,
                   size_limit: int,
                   threshold: float,
                   user: str,
                   *,
                   include_no_cover: bool = False,
                   no_si: bool = False) -> None:
    """Sync remote library to local machine."""
    include_no_cover_arg = ('include-no-cover',) if include_no_cover else ()
    no_si_arg = ('--no-si',) if no_si else ()
    await ssh(
        f'{user}@{host}', ' '.join(
            quote(x) for x in (remote_create_lib, 'create-library', *include_no_cover_arg,
                               *no_si_arg, '--max-size', str(size_limit), '--threshold',
                               str(threshold), '--split-dir', splitcue_cache_dir, remote_dir)))
    await rsync('--force', '--delete-before', 'rtdLqc', f'{user}@{host}:{remote_dir}/',
                str(local_dir))
    with ir.as_file(ir.files('clem2itunes')) as p:
        await osascript('-l', 'JavaScript', str(p / 'dist/index.js'))


@click.command()
@click.argument('host')
@click.option('--include-no-cover', help='Include files without embedded cover art.', is_flag=True)
@click.option('--no-si', help='Do not use SI units.', is_flag=True)
@click.option('--remote-create-lib',
              default='clem2itunes',
              help='Remote create-lib script (full path or a file in PATH).')
@click.option(
    '--splitcue-cache-dir',
    default='/home/%(username)s/.cache/splitcue',
    help=('Remote directory to save split CUE data (%(username)s will be replaced with the'
          ' current username or the argument to --user).'))
@click.option('-S', '--size-limit', help='Size limit in GB.', default=32, type=int)
@click.option('-l',
              '--local-dir',
              default=f'/home/{USER}/Music/import',
              type=click.Path(dir_okay=True, exists=True, path_type=Path),
              help='Local directory to sync to.')
@click.option('-r',
              '--remote-dir',
              default='/home/%(username)s/import',
              help=('Remote directory to sync (%(username)s will be replaced with the'
                    ' current username or the argument to --user).'))
@click.option('-u', '--user', default=USER, help='Remote username.')
@click.option('-t', '--threshold', default=0.8, help='Minimum rating out of 1.', type=float)
def sync(host: str,
         local_dir: Path,
         remote_create_lib: str,
         remote_dir: str,
         splitcue_cache_dir: str,
         size_limit: int = 32,
         threshold: float = 0.8,
         user: str = USER,
         *,
         include_no_cover: bool = False,
         no_si: bool = True) -> None:
    """Sync remote library to local machine."""  # noqa: DOC501
    if not which('osascript'):
        log.error('This script must be run from macOS.')
        raise click.Abort
    params = {'user': user}
    asyncio.run(
        _do_sync(host,
                 local_dir,
                 remote_create_lib,
                 remote_dir % params,
                 splitcue_cache_dir % params,
                 size_limit,
                 threshold,
                 user,
                 include_no_cover=include_no_cover,
                 no_si=no_si))


@click.group(cls=ClickAliasedGroup, context_settings={'help_option_names': ('-h', '--help')})
@click.option('-d', '--debug', help='Enable debug level logging.', is_flag=True)
def main(*, debug: bool = False) -> None:  # pragma: no cover
    """Tools for Strawberry libraries."""
    setup_logging(debug=debug)


main.add_command(create_library, aliases=('c', 'cl', 'create', 'create-lib'))
main.add_command(sync, aliases=('s',))
