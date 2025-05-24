clem2itunes
=====================================

Crazy way to synchronise a remote Strawberry rated library to Music.app using Python, JXA and SSH.

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
