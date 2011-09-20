.. index:: Scoring

Aeroplane sprites
=================

Aeroplanes :term:`sprites<sprite>` are designed to convey some basic information
in a symbolical and intuitive way.

Orientation
-----------
The most obvious piece of information is given by the orientation of the sprite,
which always matches the **current heading** the aircraft.

.. _sprites-shapes:

Shapes
------
A second piece of information is given by the shape of the sprite. The shape
provides information on the class the model of the aircraft belongs to. In turn
the class of the aircraft conveys information on certain in-game properties.

Currently three classes have been implemented:

+--------------------------+---------------------------------------------------+
| Shape                    | Meaning                                           |
+==========================+===================================================+
| .. image:: /_static/     | *Propeller planes*                                |
|    sprite-propeller.png  |                                                   |
|    :align: center        | Planes in this class have a top speed of maximum  |
|    :scale: 50%           | 600 kph.                                          |
|    :alt: propeller       |                                                   |
|                          | Despite of the class name, this class typically   |
|                          | comprises small general aviation aeroplanes       |
|                          | regardless of what mean of propulsion they use.   |
|                          |                                                   |
+--------------------------+---------------------------------------------------+
| .. image:: /_static/     | *Jet planes*                                      |
|    sprite-jet.png        |                                                   |
|    :scale: 50%           | Planes in this class have a top speed comprised   |
|    :align: center        | between 600 and 1225 kph (in case you wonder:     |
|    :alt: jet engine      | that's Mach 1 at standard atmosphere conditions)  |
|                          |                                                   |
|                          | All airliners but the Concorde belong to this     |
|                          | class.                                            |
|                          |                                                   |
+--------------------------+---------------------------------------------------+
| .. image:: /_static/     | *Supersonic jet planes*                           |
|    sprite-supersonic.png |                                                   |
|    :scale: 50%           | Planes in this class have a top speed above       |
|    :align: center        | 1225 kph.                                         |
|    :alt: supersonic jet  |                                                   |
|                          | Most military fighters and the Concorde belong    |
|                          | to this class.                                    |
|                          |                                                   |
+--------------------------+---------------------------------------------------+

.. _sprites-colours:

Colours
-------
Finally, the third piece of information conveyed by sprites is the current
status of the plane, which is associated to the sprite colour.

.. figure:: /_static/sprite-colours.png
   :align: center

   A side-by-side comparison of the possible colours for a sprite.

+-----------------------+------------------------------------------------------+
| Colour                | Meaning                                              |
+=======================+======================================================+
| *White*               | The aeroplane is ready to accept orders.             |
|                       |                                                      |
|                       | All queued orders have already been processed.       |
|                       |                                                      |
+-----------------------+------------------------------------------------------+
| *Gray*                | The aeroplane is currently manoeuvring and it is     |
|                       | unable to perform a new order (albeit it is still    |
|                       | possible to issue ``ABORT`` or ``SQUAWK`` commands). |
|                       |                                                      |
|                       | It is possible to queue orders.                      |
|                       |                                                      |
+-----------------------+------------------------------------------------------+
| *Magenta*             | The aeroplane is "locked" it is not possible to      |
|                       | perform any operation but ``SQUAWK``. Typically this |
|                       | is the plane status during the final phases of       |
|                       | landings and during take off's                       |
|                       |                                                      |
|                       | It is **not** possible to queue orders.              |
|                       |                                                      |
+-----------------------+------------------------------------------------------+
| *Yellow*              | The aeroplane needs a priority landing (most likely  |
|                       | because of a :ref:`fuel emergency<fuel-emergency>`). |
|                       |                                                      |
|                       | This status overrides the *white* and *gray* colours |
|                       | The command ``SHOWQUEUE`` can help to verify if the  |
|                       | plane is currently processing any order.             |
|                       |                                                      |
+-----------------------+------------------------------------------------------+
| *Red*                 | The aeroplane is at danger of collision with another |
|                       | aeroplane (:term:`TCAS`) or with the ground.         |
|                       |                                                      |
|                       | You can't do anything else than praying, as you      |
|                       | can't issue or queue orders when the plane is in     |
|                       | such condition.                                      |
|                       |                                                      |
+-----------------------+------------------------------------------------------+
