Tips & Tricks
=============

This section of the manual contains some advice that you might find useful for
increasing your performance while playing.

.. index:: Console; Shorthand notation

Shorthand notation
------------------
Since ``HEADING``, ``SPEED`` and ``ALTITUDE`` are the most used command in the
game, the parsing engine also accept them in a *shorthand notation* which saves
a few keystrokes. The shorthand notation allows to issue these commands by their
initial **joint** with their argument. Example:

>>> QFA1234 H210 S200 A25

.. index:: Console; Autocompletion

Autocompletion
--------------
The command line provides a *contex-aware* autocompletion (that you can activate
by pressing the :kbd:`TAB` key). *Context-aware* means that ATC-NG will only try
to complete a word with makes sense according to the command grammar.

Example: in a scenario with a flight numbered `ABC1234` and an airport `AZZ`, the
autocompletion will react differently:

>>> A
>>> ABC1234

>>> AZA1234 LAND A
>>> AZA1234 LAND AZZ

This is especially useful for flight numbers, that can be tedious to be
memorised.

.. index:: Console; Command history

Command history
---------------
By pressing the :kbd:`Up` and :kbd:`Down` keys, it is possible to browse the
command history.

.. index:: Console; Editing

Cleaning the command line
-------------------------
Beside the standard :kbd:`Backspace` key, it is also possible to:

* completely erase the prompt line with :kbd:`Esc`,
* delete the last word on the prompt with :kbd:`Control-Backspace`.

.. index:: Landing

Approaching
-----------
Make sure to approach the airport for landing at a reasonable speed: **the
slowest the speed, the easier** it will be for the aeroplane to *adjust their
altitude* to that required for :term:`ILS` approach.

A slower speed also means that it will be easier for planes to *keep separation*
(just before landing, planes drop their speed to the minimum, so there is a
risk for oncoming planes in the landing queue to come too close).

.. index:: Taking off

Taking off
----------
Always issue the command in combination with ``SPEED`` and ``ALTITUDE``: a
take-off performed without these parameters will keep the aeroplane busy
until maximum flight altitude and speed are reached. In many scenarios, by the
time the aeroplane will have reached that configuration, it will be flying
extremely fast, and near the edge of the radar screen, and it might be too late
for you to direct it towards its final destination.

.. index:: Fuel

Running out of fuel
-------------------
Since aircraft running out of fuel still have the possibility to glide for quite
some time, if you ever find yourself away from your target and low on fuel,
climbing up will extend your gliding range of various kilometres. Also consider
that given the simplified physics implemented in ATC-NG, the descent ratio is
fixed regardless of the ground speed, so: keep going as fast as you can!
