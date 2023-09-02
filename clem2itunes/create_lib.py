#!/usr/bin/env python
from os import listdir, mkdir, remove as rm, stat, symlink
from os.path import basename, dirname, expanduser, isdir, join as path_join, realpath, splitext
from pathlib import Path
from sqlite3 import connect as sqlite_connect
from typing import cast
import datetime
import difflib
import math
import re
import subprocess as sp

from loguru import logger
import click

from .utils import runner, setup_logging

__all__ = ('create_lib_main',)

FILE_URI_REGEX = re.compile(r'^file\://')

atomic_parsley = runner('AtomicParsley')
id3ted = runner('id3ted')
mp3check = runner('mp3check')
mp3splt = runner('mp3splt', stderr=sp.PIPE)


def get_clementine_db_file_path() -> tuple[str, bool]:
    paths = (expanduser('~/.local/share/strawberry/strawberry/strawberry.db'),
             expanduser('~/.config/Clementine-qt5/clementine.db'),
             expanduser('~/.config/Clementine/clementine.db'))
    for path in paths:
        try:
            with open(path, 'rb'):
                return path, path.endswith('clementine.db')
        except IOError:
            pass
    raise FileNotFoundError('No Clementine database found')


class CandidateError(Exception):
    pass


def splitcue(temp_dir: str, cuefile: str, mp3file: str, track: int) -> str:
    bnmp3 = basename(mp3file)
    mp3root, _ = splitext(bnmp3)
    candidate = path_join(temp_dir, f'{mp3root}-{track:02d}.mp3')
    try:
        with open(candidate, 'rb'):
            logger.debug('Found candidate')
            return candidate
    except IOError:
        logger.debug('Candidate split MP3 does not exist')
    mp3splt_args = [
        '-xKf', '-C', '8', '-T', '12', '-o'
        f'{mp3root}-@n', '-d', temp_dir, '-c', cuefile, mp3file
    ]
    logger.debug(f'mp3splt {" ".join(mp3splt_args)}')
    out = mp3splt(mp3splt_args)
    logger.debug(out.stdout.strip())
    with open(candidate, 'rb'):
        return candidate


@click.command()
@click.argument('directory',
                nargs=1,
                type=click.Path(file_okay=False, writable=True, resolve_path=True))
@click.option('--include-no-cover', is_flag=True)
@click.option('--split-dir', type=click.Path(file_okay=False, writable=True, resolve_path=True))
@click.option('-d', '--debug', is_flag=True)
@click.option('-m', '--max-size', type=int, help='Maximum size in GB', default=32)
@click.option('-t', '--threshold', type=float, default=0.6)
def create_lib_main(split_dir: str,
                    directory: str,
                    threshold: float = 0.6,
                    max_size: int = 32,
                    debug: bool = False,
                    include_no_cover: bool = False) -> None:
    setup_logging(debug)
    if (outdir := directory) == split_dir:
        logger.error('Split CUE cache directory cannot be same as output directory')
        raise click.Abort()
    old_listing = []
    new_listing = []
    logger.info('Cleaning out directory')
    outdir_p = Path(outdir)
    if not outdir_p.exists():
        outdir_p.mkdir()
    for item in listdir(outdir):
        fn = path_join(outdir, item)
        old_listing.append(item)
        rm(fn)
    db_file, is_clementine = get_clementine_db_file_path()
    files = []
    no_cover = []
    stream_failures = []
    ratings = []
    total_size = 0
    max_size = max_size * (1000 ** 3)  # Use SI as iOS/OS X does
    uniques = []
    splitdir = realpath(split_dir)
    logger.debug(f'db_file: {db_file}')
    conn = sqlite_connect(db_file)
    c = conn.cursor()
    filename_column = 'filename' if is_clementine else 'url AS filename'
    like_column = 'filename' if is_clementine else 'url'
    c.execute(
        f'SELECT rating, artist, title, {filename_column}, track FROM songs '
        'WHERE rating >= ? AND '
        f'({like_column} LIKE "%.mp3" OR {like_column} LIKE "%.m4a") '
        'ORDER BY rating ASC', (threshold,))
    for rating, artist, title, filename, track in ((r, a, t, re.sub(
            FILE_URI_REGEX, '',
            f), tr) for r, a, t, f, tr in cast(list[tuple[float, str, str, str,
                                                          int]], c.fetchall())):
        if filename in files:
            continue
        if (artist.lower(), title.lower()) in uniques:
            continue
        try:
            with open(filename, 'rb') as f:
                pass
        except IOError:
            logger.error(f'Bad data in database. File not found or is not readable: {filename}')
            continue
        try:
            with open(filename[:-4] + '.cue', 'rb') as f:
                # Split the segment out of the MP3, very ugly
                tempdir = path_join(splitdir, basename(dirname(filename)))
                if not isdir(tempdir):
                    mkdir(tempdir)

                logger.info(f'Splitting track #{track:d} ({artist} - \'{title}\') out of '
                            f'{basename(filename)} (tempdir = {tempdir})')

                # Only the filename variable has to change and the below code
                # works
                filename = splitcue(tempdir, f.name, filename, track)  # pylint: disable=redefined-loop-name
        except FileNotFoundError:
            pass
        except sp.CalledProcessError as e:
            if ('error: the splitpoints are not in order' not in e.stderr
                    and 'cue error: invalid cue file' not in e.stdout):
                logger.error(f'STDERR: {e.stderr}')
                logger.error(f'STDOUT: {e.stdout}')
                raise e
            logger.warning(f'splitcue: STDERR: {e.stderr}')
            logger.warning(f'splitcue: STDOUT: {e.stdout}')
        filesize = stat(filename).st_size
        cover_found = True
        with open(filename, 'rb') as f:
            if filename.endswith('.mp3'):
                try:
                    completed_process = id3ted(['-l', filename])
                except UnicodeDecodeError as e:
                    logger.error(f'Data from tool for file {filename} failed to decode to UTF-8. '
                                 'Not including.')
                    logger.exception(e)
                    logger.error(f'Start: {e.start:d}, End: {e.end:d}, Reason: {e.reason}')
                    continue
            elif filename.endswith('.m4a'):
                completed_process = atomic_parsley([filename, '-t'])
            else:
                raise NotImplementedError(filename)
        try:
            data = completed_process.stdout
        except UnicodeDecodeError as e:
            logger.error(
                f'Data from tool for file {filename} failed to decode to UTF-8. Not including.')
            logger.exception(e)
            logger.error(f'Start: {e.start:d}, End: {e.end:d}, Reason: {e.reason}')
            continue
        # Cover check
        if filename.endswith('.mp3') and 'APIC: image/jpeg' not in data:
            cover_found = False
        elif (filename.endswith('.m4a') and 'Atom "covr" contains: ' not in data):
            cover_found = False
        if not cover_found and not include_no_cover:
            no_cover.append(filename)
            logger.warning(f'Cover check failed for {filename}. Skipping.')
            continue
        # Stream check, -TY may make this useless?
        if filename.endswith('.mp3'):
            try:
                mp3check(['-e', '-GSBTY', filename])
            except sp.CalledProcessError as e:
                if 'bytes of junk after last frame' in e.stdout:
                    pass
                else:
                    stream_failures.append(filename)
                    logger.error(f'Stream check failed for {filename}. Not including.')
                    continue
        else:
            logger.debug(f'Stream checking for M4A not implemented yet (file: {filename})')
        if total_size + filesize > max_size:
            logger.info('Hit limit for maximum total size of data')
            break
        total_size += filesize
        files.append(filename)
        new_listing.append(basename(filename))
        uniques.append((
            artist.lower(),
            title.lower(),
        ))
        # pylint: disable=redefined-loop-name
        rating *= 5
        rating = min(rating, 5)
        rating = math.trunc(rating)
        # pylint: enable=redefined-loop-name
        ratings.append((
            rating,
            basename(filename),
        ))
    conn.close()
    logger.info(
        f'{total_size / (1000 ** 3):.2f} GB ({total_size / (1024 ** 3):.2f} GiB) of data found')
    for fn in files:
        out = path_join(outdir, basename(fn))
        logger.info(f'{fn} -> {out}')
        try:
            symlink(fn, out)
        except FileExistsError:
            rm(out)
            symlink(fn, out)
    with open(path_join(outdir, '.timestamp'), 'w') as ft:
        ft.write(f'{datetime.datetime.today()}\n')
    with open(path_join(outdir, '.ratings'), 'w') as ft:
        for rating, filename in ratings:
            ft.write(f'{rating} {filename}\n')
    if debug:
        logger.debug('\n'.join(difflib.Differ().compare(sorted(old_listing), sorted(new_listing))))
