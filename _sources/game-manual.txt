How to play
===========

Objective
---------
The objective of the game is to safely guide aeroplanes to their destinations.
This is done by issuing commands to individual planes.

Game inteface
-----------------
All the interaction with the game happens through the command console. You can
find an in-depth presentation of the game interface in the :doc:`dedicated
section<game-interface>`

.. toctree::
   :hidden:

   Break-down of the game interface <game-interface>

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

See the :doc:`list of all available aeroplane commands<plane-commands>` for
details.

.. toctree::
   :hidden:

   List of available commands <plane-commands>


Landing
-------
Landing at airports is done with the help of **ILS (Instrument Landing
System)**. This means that once the aeroplane is cleared for landing, it will
try to intercept the gliding path for the foot of the runway.

There are a few things to consider when clearing an aeroplane for landing:

* The angle between the current heading of the aeroplane and the runway
  orientation must be less or equal than 60 degrees.

* The aeroplane will **first** try to align itself with the runway, and
  **then** it will adjust its altitude and speed.

* The gliding angle for an ILS is always the standard 3°.

* The speed of the aeroplane will be kept constant as long as possible, then it
  will be progressively reduced in order for the plane to touch down at its
  nominal landing speed. This behaviour makes easier to maintain separation
  between planes approaching the same runway.

* The runway will be busy (i.e. unavailable for other planes to land / take off
  for 30 seconds after touchdown.

Tips & Tricks
-------------
A list of tips and tricks is available :doc:`here<tips>`.

.. toctree::
   :hidden:

   Tips & Tricks<tips>
