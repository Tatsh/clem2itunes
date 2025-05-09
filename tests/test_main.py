from __future__ import annotations

from typing import TYPE_CHECKING

from clem2itunes.main import main

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest_mock import MockerFixture


def test_sync_runs_all_steps(mocker: MockerFixture, runner: CliRunner) -> None:
    mock_logger = mocker.patch('clem2itunes.sync_remote.log')
    mock_which = mocker.patch('clem2itunes.sync_remote.which', return_value=True)
    mock_osascript = mocker.patch('clem2itunes.sync_remote.osascript',
                                  new_callable=mocker.AsyncMock)
    mock_rsync = mocker.patch('clem2itunes.sync_remote.rsync', new_callable=mocker.AsyncMock)
    mock_ssh = mocker.patch('clem2itunes.sync_remote.ssh', new_callable=mocker.AsyncMock)
    result = runner.invoke(main, [
        'sync', 'host.example.com', '--remote-create-lib', 'remote_script', '--splitcue-cache-dir',
        '/splitcue', '-S', '10', '-l', '/dev', '-r', '/a/remote', '-u', 'testuser', '-t', '0.9',
        '--include-no-cover', '--no-si'
    ])
    assert result.exit_code == 0
    mock_which.assert_called_once_with('osascript')
    mock_logger.error.assert_not_called()
    mock_ssh.assert_called_once_with(
        'testuser@host.example.com',
        ('remote_script create-library include-no-cover --no-si --max-size 10 --threshold 0.9 '
         '--split-dir /splitcue /a/remote'))
    mock_rsync.assert_called_once_with('--force', '--delete-before', 'rtdLqc',
                                       'testuser@host.example.com:/a/remote/', '/dev')
    mock_osascript.assert_called_once_with('-l', 'JavaScript', mocker.ANY)


def test_sync_aborts_if_not_macos(mocker: MockerFixture, runner: CliRunner) -> None:
    mock_which = mocker.patch('clem2itunes.sync_remote.which', return_value=False)
    mock_asyncio_run = mocker.patch('clem2itunes.sync_remote.asyncio.run')
    mock_logger = mocker.patch('clem2itunes.sync_remote.log')
    result = runner.invoke(main, ['sync', 'host.example.com', '-l', '/dev'])
    assert result.exit_code != 0
    mock_which.assert_called_once_with('osascript')
    mock_logger.error.assert_called_once_with('This script must be run from macOS.')
    mock_asyncio_run.assert_not_called()
