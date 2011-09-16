.. Notes on the logging feature of the ATC-NG game

   ©2011 Mac Ryan - Licensed under GPL v.3

   This file is intended to work with the ATC-NG game available at
   https://github.com/quasipedia/atc-ng

Logging
=======

Logs are an important tool for the developers to reproduce the bugs that players
might find. If you think you did find a bug, please attach the log of the game
in which you found the bug to the bug description.

Bug descriptions can be filed on the `GitHub issue tracker`_.

ATC-NG will keep up to ``LOG_NUMBER`` logs in this directory (where
``LOG_NUMBER`` can be changed in the ``settings.yml`` file). After that, the
oldest log will be deleted every time a new log needs to be inserted.

.. _GitHub issue tracker: https://github.com/quasipedia/atc-ng/issues
