from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import subprocess as sp

from anyio import Path as AnyioPath
from clem2itunes.main import main
import pytest

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest_mock import MockerFixture
from clem2itunes.utils import (
    can_read_file,
    create_library,
    get_songs_from_db,
    has_cover,
    is_mp3_stream_valid,
    runner,
    split_cue,
    try_split_cue,
)


def test_create_library_split_dir_same_as_output(mocker: MockerFixture, runner: CliRunner) -> None:
    mock_log_error = mocker.patch('clem2itunes.main.log.error')
    with runner.isolated_filesystem() as fake_root:
        fake_root_path = Path(fake_root)
        output_dir = fake_root_path / 'output'
        output_dir.mkdir()
        result = runner.invoke(main,
                               ('create-library', str(output_dir), '--split-dir', str(output_dir)))
    assert result.exit_code != 0
    mock_log_error.assert_called_once_with(
        'Split CUE cache directory cannot be same as output directory.')


def test_create_library_from_main(mocker: MockerFixture, runner: CliRunner) -> None:
    mock_asyncio_run = mocker.patch('clem2itunes.main.asyncio.run')
    mock_log_error = mocker.patch('clem2itunes.main.log.error')
    with runner.isolated_filesystem() as fake_root:
        fake_root_path = Path(fake_root)
        output_dir = fake_root_path / 'output'
        output_dir.mkdir()
        split_dir = fake_root_path / 'split-dir'
        split_dir.mkdir()
        result = runner.invoke(main,
                               ('create-library', str(output_dir), '--split-dir', str(split_dir)))
    assert result.exit_code == 0
    mock_log_error.assert_not_called()
    mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
async def test_runner_non_zero_return(mocker: MockerFixture) -> None:
    mock_process = mocker.MagicMock()
    mock_process.stderr.read = mocker.AsyncMock(return_value=b'error message')
    mock_process.stdout.read = mocker.AsyncMock(return_value=b'')
    mock_process.wait = mocker.AsyncMock()
    mock_process.returncode = 1
    mocker.patch('clem2itunes.utils.asp.create_subprocess_exec', return_value=mock_process)
    tool = runner('tool')
    with pytest.raises(sp.CalledProcessError) as e:
        await tool('arg', 'arg2')
    assert e.value.returncode == 1
    assert e.value.stderr == 'error message'


@pytest.mark.asyncio
async def test_runner_normal_check(mocker: MockerFixture) -> None:
    mock_process = mocker.MagicMock()
    mock_process.stderr.read = mocker.AsyncMock(return_value=b'error message')
    mock_process.stdout.read = mocker.AsyncMock(return_value=b'')
    mock_process.wait = mocker.AsyncMock()
    mock_process.returncode = 0
    mocker.patch('clem2itunes.utils.asp.create_subprocess_exec', return_value=mock_process)
    tool = runner('tool')
    p = await tool('arg', 'arg2')
    assert p == mock_process


@pytest.mark.asyncio
async def test_runner_non_zero_return_not_decodable(mocker: MockerFixture) -> None:
    mock_process = mocker.MagicMock()
    mock_read = mocker.AsyncMock()
    mock_bytes = mocker.MagicMock(spec=bytes)
    mock_bytes.decode.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'test')
    mock_read.return_value = mock_bytes
    mock_process.stderr.read = mock_read
    mock_process.stdout.read = mocker.AsyncMock(return_value=b'')
    mock_process.wait = mocker.AsyncMock()
    mock_process.returncode = 1
    mocker.patch('clem2itunes.utils.asp.create_subprocess_exec', return_value=mock_process)
    tool = runner('tool')
    with pytest.raises(UnicodeDecodeError):
        await tool('arg', 'arg2')


@pytest.mark.asyncio
async def test_runner_non_zero_return_not_text(mocker: MockerFixture) -> None:
    mock_process = mocker.MagicMock()
    mock_process.stderr.read = mocker.AsyncMock(return_value=b'')
    mock_process.stdout.read = mocker.AsyncMock(return_value=b'')
    mock_process.wait = mocker.AsyncMock()
    mock_process.returncode = 1
    mocker.patch('clem2itunes.utils.asp.create_subprocess_exec', return_value=mock_process)
    tool = runner('tool', text=False)
    with pytest.raises(sp.CalledProcessError) as e:
        await tool('arg', 'arg2')
    assert e.value.returncode == 1
    assert e.value.stderr is None
    assert e.value.stdout is None


@pytest.mark.asyncio
async def test_split_cue_candidate_exists(mocker: MockerFixture) -> None:
    mock_mp3splt = mocker.patch('clem2itunes.utils.mp3splt')
    mock_candidate = mocker.AsyncMock()
    mock_candidate.exists = mocker.AsyncMock(return_value=True)
    temp_dir = mocker.AsyncMock()
    temp_dir.__truediv__.return_value = mock_candidate
    candidate = await split_cue(temp_dir, mocker.AsyncMock(), mocker.AsyncMock(), 1)
    mock_mp3splt.assert_not_called()
    assert candidate == mock_candidate


@pytest.mark.asyncio
async def test_split_cue(mocker: MockerFixture) -> None:
    mock_mp3splt = mocker.patch('clem2itunes.utils.mp3splt')
    mock_candidate = mocker.AsyncMock()
    mock_candidate.exists = mocker.AsyncMock(return_value=False)
    mock_cue = mocker.AsyncMock()
    mock_cue.__str__.return_value = 'testfile.cue'
    mock_mp3 = mocker.AsyncMock()
    mock_mp3.__str__.return_value = 'testfile.mp3'
    mock_mp3.stem = 'testfile.mp3'
    temp_dir = mocker.AsyncMock()
    temp_dir.__str__.return_value = 'temp_dir'
    temp_dir.__truediv__.return_value = mock_candidate
    candidate = await split_cue(temp_dir, mock_cue, mock_mp3, 1)
    mock_mp3splt.assert_called_once_with('-xKf', '-C', '8', '-T', '12', '-otestfile.mp3-@n2', '-d',
                                         'temp_dir', '-c', 'testfile.cue', 'testfile.mp3')
    assert candidate == mock_candidate


@pytest.mark.asyncio
async def test_get_songs_from_db_empty_db(mocker: MockerFixture) -> None:
    mock_database = mocker.MagicMock()
    mock_database.__str__.return_value = 'test.db'
    mock_conn = mocker.MagicMock()
    mock_conn.execute.return_value.__aenter__.return_value = mocker.MagicMock()
    mock_aiosqlite_connect = mocker.patch('clem2itunes.utils.aiosqlite.connect')
    mock_aiosqlite_connect.return_value.__aenter__.return_value = mock_conn
    songs = [gen async for gen in get_songs_from_db(mock_database, 0.4)]
    assert songs == []
    mock_conn.execute.assert_called_once_with(
        ('SELECT rating, artist, title, filename, track FROM songs WHERE rating >= ? AND (filename '
         'LIKE "%.mp3" OR filename LIKE "%.m4a") ORDER BY rating ASC'), (0.4,))


@pytest.mark.asyncio
async def test_get_songs_from_db(mocker: MockerFixture) -> None:
    mock_database = mocker.MagicMock()
    mock_database.__str__.return_value = 'test.db'
    mock_c = mocker.MagicMock()
    mock_c.__aiter__.return_value = iter([
        (0.6, 'artist', 'title', 'file:///filename', 1),
        (0.7, 'artist2', 'title2', 'file:///filename2', 2),
        (0.8, 'artist3', 'title3', 'file:///filename3', 3),
    ])
    mock_conn = mocker.MagicMock()
    mock_conn.execute.return_value.__aenter__.return_value = mock_c
    mock_aiosqlite_connect = mocker.patch('clem2itunes.utils.aiosqlite.connect')
    mock_aiosqlite_connect.return_value.__aenter__.return_value = mock_conn
    songs = [gen async for gen in get_songs_from_db(mock_database)]
    assert songs == [
        (0.6, 'artist', 'title', AnyioPath('/filename'), 1),
        (0.7, 'artist2', 'title2', AnyioPath('/filename2'), 2),
        (0.8, 'artist3', 'title3', AnyioPath('/filename3'), 3),
    ]
    mock_conn.execute.assert_called_once_with(
        ('SELECT rating, artist, title, filename, track FROM songs WHERE rating >= ? AND (filename '
         'LIKE "%.mp3" OR filename LIKE "%.m4a") ORDER BY rating ASC'), (0.6,))


@pytest.mark.asyncio
async def test_get_songs_from_db_flac(mocker: MockerFixture) -> None:
    mock_database = mocker.MagicMock()
    mock_database.__str__.return_value = 'test.db'
    mock_c = mocker.MagicMock()
    mock_c.__aiter__.return_value = iter([
        (0.6, 'artist', 'title', 'file:///filename', 1),
        (0.7, 'artist2', 'title2', 'file:///filename2', 2),
        (0.8, 'artist3', 'title3', 'file:///filename3', 3),
    ])
    mock_conn = mocker.MagicMock()
    mock_conn.execute.return_value.__aenter__.return_value = mock_c
    mock_aiosqlite_connect = mocker.patch('clem2itunes.utils.aiosqlite.connect')
    mock_aiosqlite_connect.return_value.__aenter__.return_value = mock_conn
    songs = [gen async for gen in get_songs_from_db(mock_database, flac=True)]
    assert songs == [
        (0.6, 'artist', 'title', AnyioPath('/filename'), 1),
        (0.7, 'artist2', 'title2', AnyioPath('/filename2'), 2),
        (0.8, 'artist3', 'title3', AnyioPath('/filename3'), 3),
    ]
    mock_conn.execute.assert_called_once_with(
        ('SELECT rating, artist, title, filename, track FROM songs WHERE rating >= ? AND (filename '
         'LIKE "%.mp3" OR filename LIKE "%.m4a" OR filename LIKE "%.flac") ORDER BY rating ASC'),
        (0.6,))


@pytest.mark.asyncio
async def test_can_read_file(mocker: MockerFixture) -> None:
    mock_path = mocker.AsyncMock()
    mock_path.open.return_value.__aenter__.return_value = mocker.MagicMock()
    result = await can_read_file(mock_path)
    assert result is True
    mock_path.open.assert_called_once_with('rb')


@pytest.mark.asyncio
async def test_can_read_file_false(mocker: MockerFixture) -> None:
    mock_path = mocker.AsyncMock()
    mock_path.open.return_value.__aenter__.side_effect = OSError
    result = await can_read_file(mock_path)
    assert result is False
    mock_path.open.assert_called_once_with('rb')


@pytest.mark.asyncio
async def test_is_mp3_stream_valid(mocker: MockerFixture) -> None:
    mock_path = mocker.AsyncMock()
    mock_path.__str__.return_value = 'testfile.mp3'
    mock_mp3check = mocker.patch('clem2itunes.utils.mp3check')
    result = await is_mp3_stream_valid(mock_path)
    assert result is True
    mock_mp3check.assert_called_once_with('-e', '-GSBTY', 'testfile.mp3')


@pytest.mark.asyncio
async def test_is_mp3_stream_valid_ignorable_error(mocker: MockerFixture) -> None:
    mock_path = mocker.AsyncMock()
    mock_path.__str__.return_value = 'testfile.mp3'
    mock_mp3check = mocker.patch('clem2itunes.utils.mp3check')
    mock_mp3check.side_effect = sp.CalledProcessError(1, 'mp3check',
                                                      'bytes of junk after last frame')
    result = await is_mp3_stream_valid(mock_path)
    assert result is True
    mock_mp3check.assert_called_once_with('-e', '-GSBTY', 'testfile.mp3')


@pytest.mark.asyncio
async def test_is_mp3_stream_valid_no(mocker: MockerFixture) -> None:
    mock_path = mocker.AsyncMock()
    mock_path.__str__.return_value = 'testfile.mp3'
    mock_mp3check = mocker.patch('clem2itunes.utils.mp3check')
    mock_mp3check.side_effect = sp.CalledProcessError(1, 'mp3check', 'other error')
    result = await is_mp3_stream_valid(mock_path)
    assert result is False
    mock_mp3check.assert_called_once_with('-e', '-GSBTY', 'testfile.mp3')


@pytest.mark.asyncio
async def test_try_split_cue_not_exists(mocker: MockerFixture) -> None:
    mock_file = mocker.MagicMock()
    mock_file.with_suffix.return_value.exists = mocker.AsyncMock(return_value=False)
    returned_file = await try_split_cue(mock_file, mocker.MagicMock(), 1, '', '')
    assert returned_file == mock_file


@pytest.mark.asyncio
async def test_try_split_cue(mocker: MockerFixture) -> None:
    mocker.patch('clem2itunes.utils.split_cue')
    mock_file = mocker.MagicMock()
    mock_file.with_suffix.return_value.exists = mocker.AsyncMock(return_value=True)
    mock_split_dir = mocker.MagicMock()
    mock_split_dir.__truediv__.return_value.mkdir = mocker.AsyncMock()
    returned_file = await try_split_cue(mock_file, mock_split_dir, 1, '', '')
    assert returned_file != mock_file


@pytest.mark.asyncio
async def test_try_split_cue_error_1(mocker: MockerFixture) -> None:
    mocker.patch('clem2itunes.utils.split_cue', side_effect=sp.CalledProcessError(1, '', '', ''))
    mock_file = mocker.MagicMock()
    mock_file.with_suffix.return_value.exists = mocker.AsyncMock(return_value=True)
    mock_split_dir = mocker.MagicMock()
    mock_split_dir.__truediv__.return_value.mkdir = mocker.AsyncMock()
    with pytest.raises(sp.CalledProcessError):
        await try_split_cue(mock_file, mock_split_dir, 1, '', '')


@pytest.mark.asyncio
async def test_try_split_cue_error_2(mocker: MockerFixture) -> None:
    mocker.patch('clem2itunes.utils.split_cue',
                 side_effect=sp.CalledProcessError(1, '', '',
                                                   'error: the splitpoints are not in order'))
    mock_file = mocker.MagicMock()
    mock_file.with_suffix.return_value.exists = mocker.AsyncMock(return_value=True)
    mock_split_dir = mocker.MagicMock()
    mock_split_dir.__truediv__.return_value.mkdir = mocker.AsyncMock()
    returned_file = await try_split_cue(mock_file, mock_split_dir, 1, '', '')
    assert returned_file is None


@pytest.mark.asyncio
async def test_has_cover_mp3(mocker: MockerFixture) -> None:
    mock_id3ted = mocker.patch('clem2itunes.utils.id3ted')
    mock_id3ted.return_value = mocker.MagicMock(stdout=mocker.MagicMock(read=mocker.AsyncMock(
        return_value=b'APIC: image/jpeg\n')))
    mock_file = mocker.MagicMock()
    mock_file.suffix = '.mp3'
    mock_file.__str__.return_value = 'testfile.mp3'
    ret = await has_cover(mock_file)
    assert ret is True
    mock_id3ted.assert_called_once_with('-l', 'testfile.mp3')


@pytest.mark.asyncio
async def test_has_cover_m4a(mocker: MockerFixture) -> None:
    mock_atomic = mocker.patch('clem2itunes.utils.atomic_parsley')
    mock_atomic.return_value = mocker.MagicMock(stdout=mocker.MagicMock(read=mocker.AsyncMock(
        return_value=b'Atom "covr" contains: \n')))
    mock_file = mocker.MagicMock()
    mock_file.suffix = '.m4a'
    mock_file.__str__.return_value = 'testfile.m4a'
    ret = await has_cover(mock_file)
    assert ret is True
    mock_atomic.assert_called_once_with('testfile.m4a', '-t')


@pytest.mark.asyncio
async def test_has_cover_flac(mocker: MockerFixture) -> None:
    mock_ffprobe = mocker.patch('clem2itunes.utils.ffprobe')
    mock_ffprobe.return_value = mocker.MagicMock(stdout=mocker.MagicMock(read=mocker.AsyncMock(
        return_value=b'"codec_name": "mjpeg"')))
    mock_file = mocker.MagicMock()
    mock_file.suffix = '.flac'
    mock_file.__str__.return_value = 'testfile.flac'
    ret = await has_cover(mock_file)
    assert ret is True
    mock_ffprobe.assert_called_once_with('-v', 'quiet', '-print_format', 'json', '-show_format',
                                         '-show_streams', 'testfile.flac')


@pytest.mark.asyncio
async def test_has_cover_decode_error(mocker: MockerFixture) -> None:
    mock_atomic = mocker.patch('clem2itunes.utils.atomic_parsley')
    mock_atomic.return_value = mocker.MagicMock(stdout=mocker.MagicMock(read=mocker.AsyncMock(
        side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test'))))
    mock_file = mocker.MagicMock()
    mock_file.suffix = '.m4a'
    mock_file.__str__.return_value = 'testfile.m4a'
    with pytest.raises(UnicodeDecodeError):
        await has_cover(mock_file)
    mock_atomic.assert_called_once_with('testfile.m4a', '-t')


@pytest.mark.asyncio
async def test_create_library(mocker: MockerFixture) -> None:
    song1 = mocker.MagicMock(
        suffix='.mp3',
        resolve=mocker.AsyncMock(),
        stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)),
        unlink=mocker.AsyncMock())
    song2 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)))
    song3 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)))
    song4 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)))
    song5 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)))
    song6 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 10)))
    song7 = mocker.MagicMock(
        suffix='.mp3', stat=mocker.AsyncMock(return_value=mocker.MagicMock(st_size=1024 ** 2)))

    mocker.patch('clem2itunes.utils.can_read_file',
                 side_effect=[True, True, False, True, True, True])
    mock_c = mocker.MagicMock()
    mock_c.__aiter__.return_value = iter([
        (0.6, 'artist', 'title', song1, 1),  # Normal
        (0.6, 'Artist 1', 'Title', song2, 1),  # Normal
        (0.6, 'Artist 2', 'Title', song2, 1),  # Skipped due to `file in file`
        (0.6, 'Artist', 'Title', song3, 1),  # Skipped due to artist/title `in uniques`
        (0.6, 'Artist 3', 'Title', song4, 1),  # Skipped due unreadability
        (0.6, 'Artist 4', 'Title', song5, 1),  # Skipped due to no cover
        (0.6, 'Artist 6', 'Title', song7, 1),  # Skipped due to invalid CUE
        (0.6, 'Artist 5', 'Title', song6, 1),  # Skipped due to size
    ])
    mocker.patch('clem2itunes.utils.get_songs_from_db', return_value=mock_c)
    mocker.patch('clem2itunes.utils.has_cover', side_effect=[True, True, False, True, True])
    mocker.patch('clem2itunes.utils.is_mp3_stream_valid')
    mocker.patch('clem2itunes.utils.try_split_cue', side_effect=[song1, song2, song3, None, song6])
    mock_outdir_p = mocker.MagicMock()
    mock_outdir_p.__truediv__.return_value = mocker.MagicMock()
    mock_outdir_p.__truediv__.return_value.exists = mocker.AsyncMock(
        side_effect=[False, True, True])
    mock_outdir_p.__truediv__.return_value.unlink = mocker.AsyncMock()
    mock_outdir_p.__truediv__.return_value.symlink_to = mocker.AsyncMock()
    mock_outdir_p.__truediv__.return_value.open = mocker.AsyncMock()
    mock_outdir_p.mkdir = mocker.AsyncMock()
    mock_outdir_p_iterdir_obj = mocker.MagicMock()
    mock_outdir_p_iterdir_obj.__aiter__.return_value = iter([song1])
    mock_outdir_p.iterdir.return_value = mock_outdir_p_iterdir_obj
    mock_split_dir = mocker.AsyncMock()
    mock_database = mocker.MagicMock()
    await create_library(mock_outdir_p, mock_split_dir, mock_database, max_size=1)
    song1.resolve.assert_called_once_with(strict=True)
    song1.unlink.assert_called_once()
