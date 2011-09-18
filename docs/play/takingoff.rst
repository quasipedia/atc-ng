.. index:: Taking off

Taking off
==========
Aeroplanes that are due to leave an airport are shown on the radar screen as
stationing at the geographical centre of the airport itself.

Planes can be instructed to take off by issuing the command ``TAKEOFF`` followed
by the number of the runway to use. For example:

>>> ABC1234 TAKEOFF 36C

The takeoff itself will keep the runway busy for 30 seconds, and the aeroplane
will appear as airborne at the end of the runway it took off from.

By default, the plane will keep on climbing until its maximum flight altitude
and its maximum flight speed, maintaining the heading of the runway it departed
from. This behaviour can be overridden by issuing the command in combination
with ``HEADING``, ``ALTITUDE`` or ``SPEED``. Some examples:

>>> ABC1234 TAKEOFF 01L

The aeroplane will take off, maintain heading 010, climb to its maximum flying
altitude, and accelerate to its maximum speed.

>>> ABC1234 TAKEOFF 01L H300 S500 A15

The aeroplane will take off, and immediately begin to manoeuvre to reach 1500
metres asl, course 300 and speed 500kpm.

>>> ABC1234 TAKEOFF 01L A15

The aeroplane will take off maintaining the heading of the runway and
accelerating till its maximum flying speed, but it will only climb to 1500
metres asl.
