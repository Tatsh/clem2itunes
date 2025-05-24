from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anyio import Path
from clem2itunes.utils import create_library
import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from click.testing import CliRunner
    from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_do_create_library_stream_fail(mocker: MockerFixture, runner: CliRunner) -> None:
    outdir_p = mocker.AsyncMock()
    fake_file = mocker.AsyncMock()
    fake_file.exists = mocker.AsyncMock(return_value=False)
    fake_file.name = 'song.mp3'
    fake_file.resolve = mocker.AsyncMock(return_value=fake_file)
    fake_file.stat = mocker.AsyncMock(return_value=mocker.Mock(st_size=100))
    fake_file.suffix = '.mp3'
    fake_file.symlink_to = mocker.AsyncMock()
    fake_file.unlink = mocker.AsyncMock()
    fake_file.__truediv__.return_value = fake_file
    outdir_p.iterdir = mocker.AsyncMock(return_value=[])
    outdir_p.mkdir = mocker.AsyncMock()
    outdir_p.__truediv__.return_value = fake_file

    async def async_iter(  # noqa: RUF029
            *args: Any, **kwargs: Any) -> AsyncIterator[tuple[float, str, str, Path, int]]:
        yield (0.8, 'Artist', 'Title', fake_file, 1)

    mocker.patch('clem2itunes.utils.can_read_file', return_value=True)
    mocker.patch('clem2itunes.utils.get_songs_from_db', async_iter)
    mocker.patch('clem2itunes.utils.has_cover', return_value=True)
    mocker.patch('clem2itunes.utils.is_mp3_stream_valid', return_value=False)
    mocker.patch('clem2itunes.utils.try_split_cue', return_value=fake_file)
    with runner.isolated_filesystem() as fake_root:
        fake_root_path = Path(fake_root)
        output_dir = fake_root_path / 'output'
        await output_dir.mkdir()
        split_dir = fake_root_path / 'split-dir'
        await split_dir.mkdir()
        await create_library(output_dir, split_dir, max_size=1, include_no_cover=True)
    fake_file.symlink_to.assert_not_called()
