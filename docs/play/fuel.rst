.. index:: Fuel

Fuel
====

Fuel units
----------
In ATC-NG fuel consumption is **constant per unit of space travelled**. This
means that a plane will consume the **same amount of fuel regardless of its
travelling speed**. The only notable exception to this rule is the use of the
flag ``expedite`` in commands: if a command is issued with such flag, the plane
will consume **twice as much** during the time the manouver will take to
complete.

To make possible to compare scores obtained on different maps/scenarios, fuel
units are calculated based on the size of the aerospace, so that the **maximum
fuel capacity for any aeroplane in ATC-NG, is always 1000**, which corresponds
to the amount of fuel needed to travel [1]_ four times along the diagonal of the
aerospace monitored on the radar screen. However **each plane** enters the game
loaded with just enough fuel to fly **four times between its entry and
destination points** [1]_.

.. index::
   pair:Fuel; Emergency

Fuel emergency
--------------
A plane declares **fuel emergency** when its fuel will be twice (or less) the
amount needed to fly the [1]_ distance between the current aeroplane position
and its destination.

Running out of fuel
-------------------
A plane that runs out of fuel doesn't immediately crash. Its flying parameters
get instead modified to simulate an *unpowered glide*:

* Given ``min`` the nominal minimum flying speed for the aeroplane, the speed
  range will be limited to ``min <= speed <= 2*min``
* Given ``max`` the nominal maximum descent ratio for the aeroplane, the climb
  ratio will be limited to ``max/2 <= descent ratio <= max``.

Example: an aeroplane whose normal flight speed range is between 200 and 900
kph, will be limited to 200 to 400 kph. Similarily, if its nominal climbing rate
limits are -30 and +15 m/s, its new ones will be -30 and -15.

.. [1] These distances are calculated "as the crow flies". The actual distance
       *will* be longer unless the aeroplane is already flying straight towards
       its destination.
