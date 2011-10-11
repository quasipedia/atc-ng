.. index:: Aerospace; Leaving

Leaving the aerospace
=====================

Aeroplanes can legally leave the aerospace only through :term:`gates<gate>`.

Failing to leave the aerospace from a gate will trigger a penalty as described
in the :doc:`scoring section<scoring>` of the manual. Leaving the aerospace
from a different gate than the designated, will also trigger a penalty, although
not as severe.

**Gates are bi-directional** which means planes can both *enter* and *exit* the
aerospace. To avoid collisions, in ATC-NG, **even flight levels (like 10, 20,
30) are reserved for leaving the aerospace**, while odd ones (like 05, 15, 25)
are reserved for entering it.

Three parameters are considered in evaluating if an aeroplane left the aerospace
correctly:

1. **Exit point**: the exit point must be within the boundaries of the gate,
   clearly identified on the map. In other words: the plane trajectory must
   intersect the edge of the radar map between the two lateral lines marking
   the gate. Crossing the edge of the map outside the boundaries will be
   considered as leaving the map not from a gate.
2. **Flight level**: the :term:`flight level` of the plane at the moment it
   exits the aerospace must be within the minimum and maximum altitudes (both
   included) of the gate (also marked on the map) and must be even. Crossing
   below the minimum FL or above the maximum one will count as leaving the map
   not from a gate, while crossing it at any other altitude than even FL, will
   count as leaving the aerospace from the wrong gate.
3. **Heading**: the plane heading at the moment it exits the aerospace must be
   within ±30 from the :term:`airway` orientation the gate gives access to
   (this information is displayed on the map too). That is: if the gate's
   orientation is marked as "260", the aeroplane heading needs to be between
   230 and 290 degrees. Don't forget you can check the current heading at no
   point penalty with the ``SQUAWK`` command.
