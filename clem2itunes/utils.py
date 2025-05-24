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

__all__ = ('atomic_parsley', 'can_read_file', 'create_library', 'get_db_file_path',
           'get_songs_from_db', 'has_cover', 'id3ted', 'is_mp3_stream_valid', 'mp3check', 'mp3splt',
           'osascript', 'rsync', 'runner', 'setup_logging', 'setup_logging', 'split_cue', 'ssh',
           'try_split_cue')

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
    """
    Create a function to run a command with the given arguments.

    Arguments are based on :py:func:`subprocess.run`.
    """
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
ffprobe = runner('ffprobe')
"""Run ``ffprobe`` command."""
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


async def get_db_file_path() -> Path:  # pragma: no cover
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
                      f'{mp3_file.stem}-@n2', '-d', str(temp_dir), '-c', str(cue_file),
                      str(mp3_file))
    assert p.stdout is not None
    log.debug((await p.stdout.read()).strip())
    return candidate


async def get_songs_from_db(database: Path | None = None,
                            threshold: float = 0.6,
                            *,
                            flac: bool = False) -> AsyncIterator[tuple[float, str, str, Path, int]]:
    """
    Get song information from the Strawberry database.

    Yields
    ------
    tuple[float, str, str, Path, int]
        A tuple containing the rating, artist, title, filename, and track number.
    """
    database = database or await get_db_file_path()
    log.debug('Database file: %s', database)
    is_clementine = database.name.endswith('clementine.db')
    filename_column = 'filename' if is_clementine else 'url AS filename'
    like_column = 'filename' if is_clementine else 'url'
    flac_part = f' OR {like_column} LIKE "%.flac"' if flac else ''
    query = (
        f'SELECT rating, artist, title, {filename_column}, track FROM songs WHERE '  # noqa: S608
        f'rating >= ? AND ({like_column} LIKE "%.mp3" OR {like_column} LIKE "%.m4a"{flac_part}) '
        'ORDER BY rating ASC')
    log.debug('Query: %s', query)
    async with aiosqlite.connect(str(database)) as conn, conn.execute(query, (threshold,)) as c:
        async for rating, artist, title, uri, track in c:
            yield rating, artist, title, Path(re.sub(_FILE_URI_REGEX, '', uri)), track


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


async def try_split_cue(file: Path, split_dir: Path, track: int, artist: str,
                        title: str) -> Path | None:
    """
    Try to split a MP3 file using its associated CUE file.

    Raises
    ------
    sp.CalledProcessError
        If the CUE file cannot be processed.
    """  # noqa: DOC502,DOC501
    cue_file = file.with_suffix('.cue')
    if await cue_file.exists():
        tempdir = split_dir / file.parent.name
        await tempdir.mkdir(parents=True, exist_ok=True)
        log.debug('Splitting track %d (`%s` - `%s`) out of `%s` (tempdir = `%s`).', track, artist,
                  title, file.name, tempdir)
        try:
            return await split_cue(tempdir, cue_file, file, track)
        except sp.CalledProcessError as e:
            if 'the splitpoints are not in order' in e.stderr:
                log.warning('CUE file `%s` split points are not order.', cue_file)
                return None
            log.exception('Check encoding of the CUE file %s.', cue_file)
            log.exception('STDERR: %s', e.stderr)
            log.exception('STDOUT: %s', e.stdout)
            raise
    return file


async def has_cover(file: Path) -> bool:
    """
    Check if a file has an embedded cover.

    Raises
    ------
    NotImplementedError
        If the file type is not supported.
    UnicodeDecodeError
        If tag output cannot be decoded as UTF-8.
    """
    if file.suffix == '.mp3':
        completed_process = await id3ted('-l', str(file))
    elif file.suffix == '.m4a':
        completed_process = await atomic_parsley(str(file), '-t')
    elif file.suffix == '.flac':
        completed_process = await ffprobe('-v', 'quiet', '-print_format', 'json', '-show_format',
                                          '-show_streams', str(file))
    else:  # pragma: no cover
        raise NotImplementedError(str(file))
    assert completed_process.stdout is not None
    try:
        data = (await completed_process.stdout.read()).decode()
    except UnicodeDecodeError as e:
        log.exception('Data from file `%s` failed to decode to UTF-8.', file)
        log.exception('Start: %d, End: %d, Reason: %s', e.start, e.end, e.reason)
        raise
    return ((file.suffix == '.mp3' and 'APIC: image/jpeg' in data)
            or (file.suffix == '.m4a' and 'Atom "covr" contains: ' in data)
            or (file.suffix == '.flac' and '"codec_name": "mjpeg"' in data))


async def create_library(outdir_p: Path,
                         split_dir: Path,
                         database: Path | None = None,
                         threshold: float = 0.6,
                         max_size: int = 32,
                         *,
                         flac: bool = False,
                         include_no_cover: bool = False,
                         use_si: bool = True) -> None:
    """
    Create a curated music library from a Strawberry or Clementine database.

    Parameters
    ----------
    outdir_p : Path
        Directory to save the curated library.

    split_dir : Path
        Directory to save split CUE data.

    database : Path | None
        Path to the database file. If not passed, the Strawberry database file will be used.

    threshold : float
        Rating threshold out of 1.0.

    max_size : int
        Maximum size of the library in GiB or GB. If `use_si` is True, the size is in GB,
        otherwise it is in GiB.

    flac : bool
        If ``True``, allow FLAC files. Otherwise, only MP3 and M4A files are allowed.

    include_no_cover : bool
        If ``True``, include files without embedded cover art.

    use_si : bool
        If True, use SI units (GB) for the maximum size. Otherwise, use binary units (GiB).
    """
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
    await split_dir.mkdir(parents=True, exist_ok=True)
    await outdir_p.mkdir(parents=True, exist_ok=True)
    async for item in outdir_p.iterdir():
        old_listing.append(str(await item.resolve(strict=True)))
        await item.unlink()
    async for rating, artist, title, file, track in get_songs_from_db(database,
                                                                      threshold,
                                                                      flac=flac):
        if file in files:
            log.debug('File already in list: %s', file)
            continue
        if (artist.lower(), title.lower()) in uniques:
            log.debug('Artist `%s` + title `%s` (file: `%s`) are already in unique list.', artist,
                      title, file)
            continue
        if not (await can_read_file(file)):
            log.warning('Bad data in database. File not found or is not readable: %s.', file)
            continue
        actual_file = (await try_split_cue(file, split_dir, track, artist, title)
                       if file.suffix == '.mp3' else file)
        if not actual_file:
            log.warning('File `%s` has an invalid CUE file. Not including.', file)
            continue
        file = actual_file  # noqa: PLW2901
        filesize = (await file.stat()).st_size
        if total_size + filesize > max_size:
            log.info('Hit limit for maximum total size of data.')
            break
        total_size += filesize
        if not include_no_cover and not await has_cover(file):
            log.warning('No cover found in `%s`. Skipping.', file)
            no_cover.add(file)
            continue
        if file.suffix == '.mp3' and not await is_mp3_stream_valid(file):
            log.warning('Stream check failed for %s. Not including.', file)
            stream_failures.add(file)
            continue
        if file.suffix == '.m4a':  # pragma: no cover
            log.debug('Stream checking for M4A not implemented yet (file: `%s`).', file)
        if file.suffix == '.flac':  # pragma: no cover
            log.debug('Stream checking for FLAC not implemented yet (file: `%s`).', file)
        log.debug('Adding: %s', file)
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
