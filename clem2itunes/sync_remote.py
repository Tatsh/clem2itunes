"""Sync remote library to local machine."""
from __future__ import annotations

from pathlib import Path
from shlex import quote
from shutil import which
import asyncio
import importlib.resources as ir
import logging
import os

import click

from .utils import osascript, rsync, ssh

__all__ = ('sync',)

USER = os.environ.get('USER', 'default')
log = logging.getLogger(__name__)


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
@click.option('--splitcue-cache-dir',
              default=f'/home/{USER}/.cache/splitcue',
              help='Remote directory to save split CUE data.')
@click.option('-S', '--size-limit', help='Size limit in GB.', default=32, type=int)
@click.option('-l',
              '--local-dir',
              default=Path.home() / 'Music/import',
              type=click.Path(dir_okay=True, exists=True, path_type=Path),
              help='Local directory to sync to.')
@click.option('-r',
              '--remote-dir',
              default=f'/home/{USER}/import',
              help='Remote directory to sync.')
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
    asyncio.run(
        _do_sync(host,
                 local_dir,
                 remote_create_lib,
                 remote_dir,
                 splitcue_cache_dir,
                 size_limit,
                 threshold,
                 user,
                 include_no_cover=include_no_cover,
                 no_si=no_si))
