# clem2itunes

[![Python versions](https://img.shields.io/pypi/pyversions/clem2itunes.svg?color=blue&logo=python&logoColor=white)](https://www.python.org/)
[![PyPI - Version](https://img.shields.io/pypi/v/clem2itunes)](https://pypi.org/project/clem2itunes/)
[![GitHub tag (with filter)](https://img.shields.io/github/v/tag/Tatsh/clem2itunes)](https://github.com/Tatsh/clem2itunes/tags)
[![License](https://img.shields.io/github/license/Tatsh/clem2itunes)](https://github.com/Tatsh/clem2itunes/blob/master/LICENSE.txt)
[![GitHub commits since latest release (by SemVer including pre-releases)](https://img.shields.io/github/commits-since/Tatsh/clem2itunes/v0.1.2/master)](https://github.com/Tatsh/clem2itunes/compare/v0.1.2...master)
[![QA](https://github.com/Tatsh/clem2itunes/actions/workflows/qa.yml/badge.svg)](https://github.com/Tatsh/clem2itunes/actions/workflows/qa.yml)
[![Tests](https://github.com/Tatsh/clem2itunes/actions/workflows/tests.yml/badge.svg)](https://github.com/Tatsh/clem2itunes/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Tatsh/clem2itunes/badge.svg?branch=master)](https://coveralls.io/github/Tatsh/clem2itunes?branch=master)
[![Documentation Status](https://readthedocs.org/projects/clem2itunes/badge/?version=latest)](https://clem2itunes.readthedocs.org/?badge=latest)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pydocstyle](https://img.shields.io/badge/pydocstyle-enabled-AD4CD3)](http://www.pydocstyle.org/en/stable/)
[![pytest](https://img.shields.io/badge/pytest-zz?logo=Pytest&labelColor=black&color=black)](https://docs.pytest.org/en/stable/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Downloads](https://static.pepy.tech/badge/clem2itunes/month)](https://pepy.tech/project/clem2itunes)
[![Stargazers](https://img.shields.io/github/stars/Tatsh/clem2itunes?logo=github&style=flat)](https://github.com/Tatsh/clem2itunes/stargazers)

[![@Tatsh](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpublic.api.bsky.app%2Fxrpc%2Fapp.bsky.actor.getProfile%2F%3Factor%3Ddid%3Aplc%3Auq42idtvuccnmtl57nsucz72%26query%3D%24.followersCount%26style%3Dsocial%26logo%3Dbluesky%26label%3DFollow%2520%40Tatsh&query=%24.followersCount&style=social&logo=bluesky&label=Follow%20%40Tatsh)](https://bsky.app/profile/Tatsh.bsky.social)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109370961877277568?domain=hostux.social&style=social)](https://hostux.social/@Tatsh)

Crazy way to synchronise a remote Strawberry rated library with iTunes using Python, JXA and SSH.

## Installation

### Poetry

```shell
poetry add clem2itunes
```

### Pip

```shell
pip install clem2itunes
```

## Usage

```shell
Usage: clem2itunes [OPTIONS] COMMAND [ARGS]...

  Tools for Strawberry libraries.

Options:
  -d, --debug  Enable debug level logging.
  -h, --help   Show this message and exit.

Commands:
  create-library (c,cl,create,create-lib)
                                  Create a curated music library.
  sync (s)                        Sync remote library to local machine.
```

`create-library` is useful for creating a maximally sized library of music for copying to any device
based on song ratings. It tries to avoid duplicates, and splits MP3s (losslessly) using CUE files.

`sync` is only for use on macOS to copy songs over, add them to iTunes/Music, and set ratings.

### Sync a library to an Android device

Assumes the library is at `~/import`. You have to create the `/sdcard/Music/import` directory on the
device first.

```shell
for i in ~/import/*; do adb push --sync -Z "$(readlink -f "$i")" /sdcard/Music/import; done
```

If your machine lacks `readlink`, use `perl -MCwd -le 'print Cwd::abs_path shift' ...` instead.
