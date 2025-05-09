"""Configuration for Pytest."""
from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn
import os

import pytest

if TYPE_CHECKING:
    from click.testing import CliRunner

if os.getenv('_PYTEST_RAISE', '0') != '0':  # pragma no cover

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call: pytest.CallInfo[None]) -> NoReturn:
        assert call.excinfo is not None
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo: pytest.ExceptionInfo[BaseException]) -> NoReturn:
        raise excinfo.value


@pytest.fixture
def runner() -> CliRunner:
    from click.testing import CliRunner
    return CliRunner()
