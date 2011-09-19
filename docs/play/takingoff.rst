.. index:: Taking off

Taking off
==========
Aeroplanes that are due to leave an airport are shown on the radar screen as
stationing at the geographical centre of the airport itself.

Planes can be instructed to take off by issuing the command ``TAKEOFF`` followed
by the number of the runway to use. For example:

>>> ABC1234 TAKEOFF 36C

Setting a post-take off course
------------------------------
By default, the plane will keep on climbing until its maximum flight altitude
and its maximum flight speed, maintaining the heading of the runway it departed
from. This behaviour can be overridden by issuing the command in combination
with ``HEADING``, ``ALTITUDE`` or ``SPEED``. Some examples:

>>> ABC1234 TAKEOFF 01L

The aeroplane will take off, maintain heading 010, climb to its maximum flying
altitude, and accelerate to its maximum speed.

>>> ABC1234 TAKEOFF 01L H300 S500 A15

The aeroplane will take off, and immediately begin to manoeuvre to reach 1500
metres a.s.l., course 300 and speed 500kpm.

>>> ABC1234 TAKEOFF 01L A15

The aeroplane will take off maintaining the heading of the runway and
accelerating till its maximum flying speed, but it will only climb to 1500
metres a.s.l..

Take off phases
---------------
A take off is split in three separate phases:

#. **Acceleration**: the aeroplane accelerates until its lift off speed.
#. **Climbing**: the aeroplane keeps on climbing (not beyond the desired
   altitude, anyhow) while overflying the runway.
#. **Veering**: once the end of the runway have been overflown, if a different
   heading than the one of the runway has been inserted, the plane will veer
   to match it.

Use of runways
--------------
The runway used for taking off will be unavailable to other aircraft until the
end of the climbing phase and however for **not less than 30 seconds**.
