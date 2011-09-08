Aeroplane commands
==================
Aeroplane commands are those commands that are issued to individual planes (as
opposed to the game engine).

Game commands are **issued** by specifying the flight number, the command and
possibly arguments and/or flags. For example:

>>> AZA1234 HEADING 000 X

where ``AZA1234`` is the flight number ``HEADING`` is the command ``000`` is
the command argument and ``X`` is the command flag.

Compatible aeroplane commands can be **combined**. For example:

>>> AZA1234 HEADING 000 SPEED 200 ALTITUDE 55

Incompatible commands (e.g.: ``CIRCLE`` and ``LAND``) will generate an error in
the console.

Aeroplanes commands can also be **queued** (meaning that the aeroplane will
execute them only when the command (or command sequence) currently being
executed will have terminated. Multiple command (or command sequences) can be
queued for execution. To append a command (or command sequence) to the queue,
prepend it with a dot (``.``). For example:

>>> .AZA LAND FRA 35L

Aeroplane commands
==================
Following is a list of all implemented aeroplane commands.

.. include:: ../pcommands.inc
