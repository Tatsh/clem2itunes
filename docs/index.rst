clem2itunes
===========

.. only:: html

   .. image:: https://img.shields.io/pypi/pyversions/clem2itunes.svg?color=blue&logo=python&logoColor=white
      :target: https://www.python.org/
      :alt: Python versions

   .. image:: https://img.shields.io/pypi/v/clem2itunes
      :target: https://pypi.org/project/clem2itunes/
      :alt: PyPI - Version

   .. image:: https://img.shields.io/github/v/tag/Tatsh/clem2itunes
      :target: https://github.com/Tatsh/clem2itunes/tags
      :alt: GitHub tag

   .. image:: https://img.shields.io/github/license/Tatsh/clem2itunes
      :target: https://github.com/Tatsh/clem2itunes/blob/master/LICENSE.txt
      :alt: License

   .. image:: https://img.shields.io/github/commits-since/Tatsh/clem2itunes/v0.1.2/master
      :target: https://github.com/Tatsh/clem2itunes/compare/v0.1.2...master
      :alt: GitHub commits since latest release

   .. image:: https://github.com/Tatsh/clem2itunes/actions/workflows/codeql.yml/badge.svg
      :target: https://github.com/Tatsh/clem2itunes/actions/workflows/codeql.yml
      :alt: CodeQL

   .. image:: https://github.com/Tatsh/clem2itunes/actions/workflows/qa.yml/badge.svg
      :target: https://github.com/Tatsh/clem2itunes/actions/workflows/qa.yml
      :alt: QA

   .. image:: https://github.com/Tatsh/clem2itunes/actions/workflows/tests.yml/badge.svg
      :target: https://github.com/Tatsh/clem2itunes/actions/workflows/tests.yml
      :alt: Tests

   .. image:: https://coveralls.io/repos/github/Tatsh/clem2itunes/badge.svg?branch=master
      :target: https://coveralls.io/github/Tatsh/clem2itunes?branch=master
      :alt: Coverage Status

   .. image:: https://readthedocs.org/projects/clem2itunes/badge/?version=latest
      :target: https://clem2itunes.readthedocs.org/?badge=latest
      :alt: Documentation Status

   .. image:: https://www.mypy-lang.org/static/mypy_badge.svg
      :target: http://mypy-lang.org/
      :alt: mypy

   .. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
      :target: https://github.com/pre-commit/pre-commit
      :alt: pre-commit

   .. image:: https://img.shields.io/badge/pydocstyle-enabled-AD4CD3
      :target: http://www.pydocstyle.org/en/stable/
      :alt: pydocstyle

   .. image:: https://img.shields.io/badge/pytest-zz?logo=Pytest&labelColor=black&color=black
      :target: https://docs.pytest.org/en/stable/
      :alt: pytest

   .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
      :target: https://github.com/astral-sh/ruff
      :alt: Ruff

   .. image:: https://static.pepy.tech/badge/clem2itunes/month
      :target: https://pepy.tech/project/clem2itunes
      :alt: Downloads

   .. image:: https://img.shields.io/github/stars/Tatsh/clem2itunes?logo=github&style=flat
      :target: https://github.com/Tatsh/clem2itunes/stargazers
      :alt: Stargazers

   .. image:: https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpublic.api.bsky.app%2Fxrpc%2Fapp.bsky.actor.getProfile%2F%3Factor%3Ddid%3Aplc%3Auq42idtvuccnmtl57nsucz72%26query%3D%24.followersCount%26style%3Dsocial%26logo%3Dbluesky%26label%3DFollow%2520%40Tatsh&query=%24.followersCount&style=social&logo=bluesky&label=Follow%20%40Tatsh
      :target: https://bsky.app/profile/Tatsh.bsky.social
      :alt: Follow @Tatsh

   .. image:: https://img.shields.io/mastodon/follow/109370961877277568?domain=hostux.social&style=social
      :target: https://hostux.social/@Tatsh
      :alt: Mastodon Follow

Crazy way to synchronise a remote Strawberry rated library to Music.app using Python, JXA and SSH.

Requires the following programs on the source side:

- `AtomicParsley <https://github.com/wez/atomicparsley>`_
- `id3ted <https://github.com/xyb3rt/id3ted>`_
- `mp3check <https://code.google.com/p/mp3check/>`_
- `mp3splt <https://mp3splt.sourceforge.net>`_

Commands
--------

.. click:: clem2itunes.main:main
  :prog: clem2itunes
  :nested: full

``create-library`` is useful for creating a maximally sized library of music for copying to any
device based on song ratings. It tries to avoid duplicates, and splits MP3s (losslessly) using CUE
files.

``sync`` is only for use on macOS to copy songs over, add them to iTunes/Music, and set ratings.

Sync a library to an Android device
-----------------------------------

Assumes the library is at ``~/import``. You have to create the ``/sdcard/Music/import`` directory on
the device first.

.. code-block:: shell

   for i in ~/import/*; do adb push --sync -Z "$(readlink -f "$i")" /sdcard/Music/import; done

If your machine lacks ``readlink``, use ``perl -MCwd -le 'print Cwd::abs_path shift' ...`` instead.

.. only:: html

   Library
   -------
   .. automodule:: clem2itunes.utils
      :members:
      :exclude-members: setup_logging

   Indices and tables
   ==================
   * :ref:`genindex`
   * :ref:`modindex`
