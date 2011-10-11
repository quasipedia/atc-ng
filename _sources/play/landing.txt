.. index:: Landing

Landing
=======
Landing at airports is done with the help of :term:`ILS` **(Instrument Landing
System)**. This means that once the aeroplane is cleared for landing, it will
autonomously try to intercept the gliding path that leads to the foot of the
indicated runway.

A typical landing command looks similar to:

>>> ABC1234 LAND ARN 01L

Landing phases
--------------
A take off is split in five different phases:

#. **Intercepting**: The plane keeps current heading, altitude and speed and
   waits for the right moment to turn into the ILS projection on the ground. In
   other words, at the end of this phase the aeroplane will be aligned with the
   runway. The plane *aborts* if the ILS vector doesn't pass in front of its
   nose, or if the plane current position is too close for the plane to veer
   into the ILS vector (as the turning radius would be too big).
#. **Merging**: The plane maintains speed and altitude and veer into the ILS
   projection.
#. **Matching**: The plane maintains heading and speed, and adjusts its altitude
   to precisely fly along the ILS vector (the line starting from the foot of the
   runway and going up at 3° angle). The plane *aborts* if the plane is flying
   above the ILS and its speed is too high to lose altitude quick enough to
   intercept the ILS vector before the runway.
#. **Gliding**: The plane follows the ILS vector maintaining speed until the
   moment comes to slow down to landing speed. The plane *aborts* if at the
   beginning of the glide its speed is already too high for it to slow down to
   landing speed by the foot of the runway. The plane also *aborts* if at
   altitude under 100 metres above the runway foot the runway will result in use
   by any other aircraft, if not, this is also the moment in which such runway
   will be marked as "busy" by the landing plane.
#. **Taxiing**: During this time the aircraft will gently roll over the runway
   until it reaches the taxiway. Once the taxiway is reached, the runway is
   made available again and the score for the landing is computed.

Aborting and the locked status
------------------------------
The landing sequence can be stopped at any moment using the appropriate
``ABORT`` command. However, once the aeroplane reaches decision altitude, the
crew will take over any decision and for this reason they will stop responding
to your commands. To remind you of this, the aeroplane icon will switch to the
:ref:`locked colour<sprites-colour>`.

Other landing "gotchas"
-----------------------
There are a few things to consider when clearing an aeroplane for landing:

* The angle between the current heading of the aeroplane and the runway
  orientation must be less or equal than 30 degrees.

* The gliding angle for an :term:`ILS` is always the standard 3°.

* The speed of the aeroplane will be kept constant as long as possible, then it
  will be progressively reduced in order for the plane to touch down at its
  nominal landing speed. This behaviour makes easier to maintain separation
  between planes approaching the same runway.

* The runway will be busy (i.e. unavailable for other planes to land / take off
  for 30 seconds after touchdown.
