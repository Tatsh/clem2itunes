"""Utility functions."""
from __future__ import annotations

from datetime import timezone
from shlex import quote
from typing import TYPE_CHECKING, Any
import asyncio.subprocess as asp
import datetime
import difflib
import logging
import logging.config
import math
import re
import subprocess as sp

from anyio import Path
from platformdirs import user_data_dir
import aiosqlite

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Coroutine

__all__ = (
    'atomic_parsley',
    'can_read_file',
    'id3ted',
    'mp3check',
    'mp3splt',
    'osascript',
    'rsync',
    'runner',
    'setup_logging',
    'split_cue',
)

_FILE_URI_REGEX = re.compile(r'^file\://')
log = logging.getLogger(__name__)


def setup_logging(*,
                  debug: bool = False,
                  force_color: bool = False,
                  no_color: bool = False) -> None:  # pragma: no cover
    """Set up logging configuration."""
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'root': {
            'handlers': ('console',),
            'level': 'DEBUG' if debug else 'INFO',
        },
        'formatters': {
            'default': {
                '()': 'colorlog.ColoredFormatter',
                'force_color': force_color,
                'format':
                    '%(log_color)s%(levelname)-8s%(reset)s | %(light_green)s%(name)s%(reset)s:'
                    '%(light_red)s%(funcName)s%(reset)s:%(blue)s%(lineno)d%(reset)s - %(message)s',
                'no_color': no_color,
            },
        },
        'handlers': {
            'console': {
                'class': 'colorlog.StreamHandler',
                'formatter': 'default',
            },
        },
        'loggers': {
            'clem2itunes': {
                'handlers': ('console',),
                'propagate': False,
            },
        },
    })


def runner(name: str,
           *,
           stderr: int | None = None,
           stdout: int | None = asp.PIPE,
           check: bool = True,
           text: bool = True) -> Callable[..., Coroutine[Any, Any, asp.Process]]:
    """Create a function to run a command with the given arguments."""
    async def cb(*args: str) -> asp.Process:
        resolved_args = list(args)
        quoted_cmd = ' '.join(quote(x) for x in resolved_args)
        log.debug('Running: %s %s', name, quoted_cmd)
        p = await asp.create_subprocess_exec(name, *resolved_args, stdout=stdout, stderr=stderr)
        await p.wait()
        if check and p.returncode != 0:
            stderr_: str | bytes = await p.stderr.read() if p.stderr else b''
            stdout_: str | bytes = await p.stdout.read() if p.stdout else b''
            if text:
                assert isinstance(stderr_, bytes)
                assert isinstance(stdout_, bytes)
                try:
                    stderr_ = stderr_.decode()
                    stdout_ = stdout_.decode()
                except UnicodeDecodeError:
                    log.exception('Failed to decode output of `%s`. Maybe set text=False?',
                                  quoted_cmd)
                    raise
            raise sp.CalledProcessError(p.returncode or -1, quoted_cmd,
                                        None if not text else stdout_,
                                        None if not text else stderr_)
        return p

    return cb


atomic_parsley = runner('AtomicParsley')
"""Run ``AtomicParsley`` command."""
id3ted = runner('id3ted')
"""Run ``id3ted`` command."""
mp3check = runner('mp3check')
"""Run ``mp3check`` command."""
mp3splt = runner('mp3splt', stderr=sp.PIPE)
"""Run ``mp3splt`` command."""
osascript = runner('osascript')
"""Run ``osascript`` command."""
rsync = runner('rsync')
"""Run ``rsync`` command."""
ssh = runner('ssh')
"""Run ``ssh`` command."""


async def get_db_file_path() -> Path:
    """Get the path to the Strawberry database file."""
    return await (Path(user_data_dir('strawberry')) / 'strawberry' /
                  'strawberry.db').resolve(strict=True)


async def split_cue(temp_dir: Path, cue_file: Path, mp3_file: Path, track: int) -> Path:
    """Split MP3 file using a CUE file."""
    candidate = temp_dir / f'{mp3_file.stem}-{track:02d}.mp3'
    if await candidate.exists():
        log.debug('Found candidate `%s`.', candidate)
        return candidate
    log.debug('Candidate split MP3 does not exist.')
    p = await mp3splt('-xKf', '-C', '8', '-T', '12', '-o'
                      f'{mp3_file.stem}-@n', '-d', str(temp_dir), '-c', str(cue_file),
                      str(mp3_file))
    assert p.stdout is not None
    log.debug((await p.stdout.read()).strip())
    return candidate


async def get_songs_from_db(
        database: Path | None = None,
        threshold: float = 0.6) -> AsyncIterator[tuple[float, str, str, Path, int]]:
    """
    Get song information from the Strawberry database.

    Yields
    ------
    aiosqlite.Row
        A row containing the rating, artist, title, filename, and track number.
    """
    database = database or await get_db_file_path()
    log.debug('Database file: %s', database)
    is_clementine = database.name.endswith('clementine.db')
    filename_column = 'filename' if is_clementine else 'url AS filename'
    like_column = 'filename' if is_clementine else 'url'
    query = (
        f'SELECT rating, artist, title, {filename_column}, track FROM songs WHERE '  # noqa: S608
        f'rating >= ? AND ({like_column} LIKE "%.mp3" OR {like_column} LIKE "%.m4a") '
        'ORDER BY rating ASC')
    log.debug('Query: %s', query)
    async with aiosqlite.connect(database.name) as conn, conn.execute(query, (threshold,)) as c:
        async for row in c:
            yield (row['rating'], row['artist'], row['title'],
                   Path(re.sub(_FILE_URI_REGEX, '', row['filename'])), row['track'])


async def can_read_file(file: Path) -> bool:
    """Try to read a file."""
    try:
        async with await file.open('rb'):
            return True
    except OSError:
        return False


async def is_mp3_stream_valid(file: Path) -> bool:
    """Check if the MP3 stream is valid."""
    try:
        # Stream check, -TY may make this useless?
        await mp3check('-e', '-GSBTY', str(file))
    except sp.CalledProcessError as e:
        return 'bytes of junk after last frame' in e.stdout
    return True


async def try_split_cue(file: Path, split_dir: Path, track: int, artist: str, title: str) -> Path:
    """Try to split a MP3 file using its associated CUE file."""  # noqa: DOC501
    cue_file = file.with_suffix('.cue')
    if cue_file.exists():
        tempdir = split_dir / file.parent.name
        await tempdir.mkdir(parents=True, exist_ok=True)
        log.debug('Splitting track %d (`%s` - `%s`) out of `%s` (tempdir = `%s`).', track, artist,
                  title, file.name, tempdir)
        try:
            return await split_cue(tempdir, cue_file, file, track)
        except sp.CalledProcessError as e:
            if ('error: the splitpoints are not in order' not in e.stderr
                    and 'cue error: invalid cue file' not in e.stdout):
                log.exception('STDERR: %s', e.stderr)
                log.exception('STDOUT: %s', e.stdout)
                raise
            log.warning('mp3splt: STDERR: %s', e.stderr)
            log.warning('mp3splt: STDOUT: %s', e.stdout)
    return file


async def has_cover(file: Path) -> bool:
    """
    Check if a file has an embedded cover.

    Raises
    ------
    NotImplementedError
        If the file type is not supported.
    """
    async with await file.open('rb'):
        if file.suffix == '.mp3':
            completed_process = await id3ted('-l', str(file))
        elif file.suffix == '.m4a':
            completed_process = await atomic_parsley(str(file), '-t')
        else:
            raise NotImplementedError(str(file))
    assert completed_process.stdout is not None
    try:
        data = (await completed_process.stdout.read()).decode()
    except UnicodeDecodeError as e:
        log.exception('Data from tool for file `%s` failed to decode to UTF-8. Not including.',
                      file)
        log.exception('Start: %d, End: %d, Reason: %s', e.start, e.end, e.reason)
    return ((file.suffix == '.mp3' and 'APIC: image/jpeg' not in data)
            or (file.suffix == '.m4a' and 'Atom "covr" contains: ' not in data))


async def create_library(outdir_p: Path,
                         split_dir: Path,
                         database: Path | None = None,
                         threshold: float = 0.6,
                         max_size: int = 32,
                         *,
                         include_no_cover: bool = False,
                         use_si: bool = True) -> None:
    files: set[Path] = set()
    max_size *= (1000 ** 3) if use_si else (1024 ** 3)
    new_listing: list[str] = []
    no_cover: set[Path] = set()
    old_listing: list[str] = []
    ratings: list[tuple[float, Path]] = []
    stream_failures: set[Path] = set()
    total_size = 0
    uniques: set[tuple[str, str]] = set()
    log.info('Cleaning out directory.')
    await outdir_p.mkdir(parents=True, exist_ok=True)
    async for item in outdir_p.iterdir():
        old_listing.append(str(await item.resolve(strict=True)))
        await item.unlink()
    async for rating, artist, title, file, track in get_songs_from_db(database, threshold):
        if file in files:
            log.debug('File already in list: %s', file)
            continue
        if (artist.lower(), title.lower()) in uniques:
            log.debug('Artist `%s` + title `%s` are already in unique list.', artist, title)
            continue
        if not (await can_read_file(file)):
            log.warning('Bad data in database. File not found or is not readable: %s.', file)
            continue
        file = await try_split_cue(file, split_dir, track, artist, title)  # noqa: PLW2901
        filesize = (await file.stat()).st_size
        if total_size + filesize > max_size:
            log.info('Hit limit for maximum total size of data.')
            break
        total_size += filesize
        if not await has_cover(file) and not include_no_cover:
            log.warning('No cover found in `%s`. Skipping.', file)
            no_cover.add(file)
            continue
        if file.suffix == '.mp3' and not await is_mp3_stream_valid(file):
            log.warning('Stream check failed for %s. Not including.', file)
            stream_failures.add(file)
            continue
        if file.suffix == '.m4a':  # pragma: no cover
            log.debug('Stream checking for M4A not implemented yet (file: `%s`).', file)
        files.add(file)
        new_listing.append(str(file))
        ratings.append((math.trunc(min(rating * 5, 5)), file))
        uniques.add((artist.lower(), title.lower()))
    log.info('%.2f GB (%.2f GiB) of data found.', total_size / (1000 ** 3),
             total_size / (1024 ** 3))
    for fn, out in ((fn, outdir_p / fn.name) for fn in files):
        log.debug('%s -> %s', fn, out)
        if await out.exists():
            await out.unlink()
        await out.symlink_to(fn)
    async with await (outdir_p / '.timestamp').open('w') as ft:
        await ft.write(f'{datetime.datetime.now(tz=timezone.utc)}\n')
    async with await (outdir_p / '.ratings').open('w') as ft:
        for rating, rated_file in ratings:
            await ft.write(f'{rating} {rated_file.name}\n')
    log.info('Total number of files: %d', len(files))
    log.info('Number of files with no cover: %d', len(no_cover))
    log.info('Number of files with stream errors: %d', len(stream_failures))
    log.debug('Difference: %s', '\n'.join(difflib.Differ().compare(sorted(old_listing),
                                                                   sorted(new_listing))))
