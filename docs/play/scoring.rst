.. index:: Scoring

Scoring System
==============

Rationale
---------
The scoring system is based on the following chart:

+-------------------+-----------------------------+----------------------------+
|                   | REWARDED                    | PENALISED                  |
+===================+=============================+============================+
| **Aeroplane       | - landing at designated     | - landing at wrong         |
| fate**            |   airport                   |   airport                  |
|                   | - leaving map from          | - leaving map at any other |
|                   |   designated gate           |   point than the           |
|                   |                             |   one                      |
|                   |                             | - crashing                 |
+-------------------+-----------------------------+----------------------------+
| **Flight          |                             | - triggering the TCAS      |
| safety**          |                             |   (Traffic Collision       |
|                   |                             |   Avoidance System)        |
|                   |                             | - getting aeroplanes into  |
|                   |                             |   fuel emergency           |
+-------------------+-----------------------------+----------------------------+
| **Fuel            |                             | - using fuel               |
| consumption**     |                             | - using the expedite flag  |
+-------------------+-----------------------------+----------------------------+
| **Controller      | - handling several planes   | - issuing commands         |
| proficiency**     |   at once                   |   (except squawk/touch)    |
|                   | - handling planes in a      |                            |
|                   |   complex scenario          |                            |
+-------------------+-----------------------------+----------------------------+

Events
------
The following events imply a variation of the score:

.. tabularcolumns:: |L|R|C|

=================================================  ================  =======
Event                                              Score variation   Notes
=================================================  ================  =======
Plane lands at correct airport                      +500             [1]_
Plane leaves map at correct gate                    +300             [1]_
The (X+1) :sup:`th` airborn plane enters the game   +50*X            [2]_
Burning one unit of fuel                              -1
Waiting one second for takeoff                        -1
Issuing a command (except touch/squawk)              -10
Plane lands at wrong airport                        -200             [1]_
Plane leaves map at wrong gate                      -200             [1]_
Triggering fuel emergency                           -250
TCAS activation (per plane)                         -250
Plane does not leave map at gate                    -500             [1]_
Plane crashes                                      -1000             [1]_
=================================================  ================  =======

.. [1] Onboard fuel will affect this number as described in the `fuel`_ section
.. [2] See the `controller's proficiency`_ section for details

.. _fuel:

.. index::
   pair:Fuel; Scoring

Fuel
----
Beside the "burning one unit of fuel" and "triggering fuel emergency" events
above, fuel influences score when an aeroplane terminate its existence. In
particular an **amount of points equal to the amount of fuel still onboard**
at the moment in which the plane terminates is added or subtracted to the score
according to whether the end-of-life event was rewarded or penalised.

For example a plane crashing with 250 units of fuel will affect the overall
score by -1250 points, while a plane landing with 123 units of fuel will change
the score of +623 points.

Also note that during manoeuvres performed with the ``expedite`` flag, fuel
consumption happens twice as fast.

For an accurate description of the fuel modelling in ATC-NG see the :doc:`fuel
explanation<fuel>` page.

.. _`controller's proficiency`:

Controller's proficiency
-------------------------
Controller's proficiency is taken into account in two ways.

The **number of airborne planes** in the aerospace affects the score assigned
every time a new plane enters the aerospace. For example: if a player has five
aeroplanes on radar, of which three airborne, and a sixth aeroplane appears
*from a gate*, the player will receive:

  50 (bonus unit) x 3 (airborne planes) = 150 points

On the other hand, the player won't receive any points if the plane appears at
an airport.

Secondly **the complexity of the scenario** influences the amount any score
event is multiplied by. That means that any point gained with any of the events
described above is still multiplied by a factor (between 1 and 2).
