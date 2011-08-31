How to play
===========

Objective
---------
The objective of the game is to safely guide aeroplanes to their destinations.
This is done by issuing commands to individual planes.

Game screen
-----------
The game screen is organised in four main areas:

.. image:: _static/game_interface.png

**radar screen** (1)
  You can see here the aeroplanes, aeroports, beacons and gates which are used
  during the game

**command console** (2)
  Here you issue commands either to the game engine (for getting help, pausing,
  quitting...) or to aeroplanes (to alter they course or perform special
  operations)

**flight strips** (3)
  Here you have a list of planes currently under your control, with some data
  which is not available on the main radar screen

**aeroport maps** (4)
  Here you have a detailed map of the map's aeroports: aeroports are also
  visible on radar screen, but in this game area they are big enough for you
  to identify individual runways.

Game commands
-------------
Game commands are those commands that are issued to the game engine (as opposed
to aeroplanes). At present, the only useful implemented command is ``quit``
(to exit the game).

Game commands are issued in the console by prepending them with a ``/``. For
example:

>>> /quit

Aeroplane commands
------------------
Aeroplane commands are those commands that are issued to individual planes (as
opposed to the game engine).

Game commands are **issued** by specifying the flight number, the command and
possibly arguments and/or flags. For example:

>>> AZA1234 HEADING 000 X

where ``AZA1234`` is the flight number ``HEADING`` is the command ``000`` is
the command argument and ``X`` is the command flag.

Certain game commands can be **combined**. For example:

>>> AZA1234 HEADING 000 SPEED 200 ALTITUDE 55

Aeroplanes commands can also be **queued** (meaning that the aeroplane will
execute them only when the command (or command sequence) currently being
executed will have terminated. Multiple command (or command sequences) can be
queued for execution. To append a command (or command sequence) to the queue,
prepend it with a dot (``.``). For example:

>>> .AZA LAND FRA 35L

See the :doc:`list of all available aeroplane commands<planecommands>` for
details.
