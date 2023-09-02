from pathlib import Path
from shutil import which
import importlib.resources as ir
import os

from loguru import logger
import click

from .utils import runner

__all__ = ('sync_remote_main',)

USER = os.environ.get('USER', 'default')

ssh = runner('ssh')
rsync = runner('rsync')
osascript = runner('osascript')


@click.command()
@click.argument('host')
@click.option('--remote-create-lib',
              default='clem2itunes-create-lib',
              help='Remote create-lib script (full path or a file in PATH).')
@click.option('--splitcue-cache-dir',
              default=f'/home/{USER}/.cache/splitcue',
              help='Remote directory to save split CUE data.')
@click.option('-S', '--size-limit', help='Size limit in GB.', default=32, type=int)
@click.option('-l',
              '--local-dir',
              default=str(Path.home() / 'Music/import'),
              type=click.Path(dir_okay=True, exists=True),
              help='Local directory to sync to.')
@click.option('-r',
              '--remote-dir',
              default=f'/home/{USER}/import',
              help='Remote directory to sync.')
@click.option('-t', '--threshold', default=0.8, help='Minimum rating out of 1.', type=float)
@click.option('-u', '--user', default=USER, help='Remote username.')
def sync_remote_main(
    host: str,
    local_dir: str = str(Path.home() / 'Music/import'),
    remote_create_lib: str = 'clem2itunes-create-lib',
    remote_dir: str = f'/home/{USER}/import',
    splitcue_cache_dir: str = f'/home/{USER}/.cache/splitcue',
    size_limit: int = 32,
    threshold: float = 0.8,
    user: str = USER,
) -> None:
    if not which('osascript'):
        logger.error('This script must be run from macOS.')
        raise click.Abort()
    ssh((f'{user}@{host}', f'{remote_create_lib} -m {size_limit} -t {threshold} '
         f'--split-dir {splitcue_cache_dir} {remote_dir}'))
    rsync(('--force', '--delete-before', 'rtdLqc', f'{user}@{host}:{remote_dir}/', local_dir))
    with ir.as_file(ir.files('clem2itunes')) as p:
        osascript(('-l', 'JavaScript', str(p / 'dist/index.js')))
