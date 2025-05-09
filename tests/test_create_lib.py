from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from clem2itunes.main import main

if TYPE_CHECKING:

    from click.testing import CliRunner
    from pytest_mock import MockerFixture


def test_create_library_split_dir_same_as_output(mocker: MockerFixture, runner: CliRunner) -> None:
    mock_log_error = mocker.patch('clem2itunes.create_lib.log.error')
    with runner.isolated_filesystem() as fake_root:
        fake_root_path = Path(fake_root)
        output_dir = fake_root_path / 'output'
        output_dir.mkdir()
        result = runner.invoke(main,
                               ('create-library', str(output_dir), '--split-dir', str(output_dir)))
    assert result.exit_code != 0
    mock_log_error.assert_called_once_with(
        'Split CUE cache directory cannot be same as output directory.')
