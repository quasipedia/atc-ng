Tips & Tricks
=============

This section of the manual contains some advice that you might find useful for
increasing your performance while playing.

Shorthand notation
------------------
Since ``HEADING``, ``SPEED`` and ``ALTITUDE`` are the most used command in the
game, the parsing engine also accept them in a *shorthand notation* which saves
a few keystrokes. The shorthand notation allows to issue these commands by their
initial **joint** with their argument. Example:

>>> QFA1234 H210 S200 A25

Autocompletion
--------------
The command line provides a *contex-aware* autocompletion (that you can activate
by pressing the :kbd:`TAB` key). *Context-aware* means that ATC-NG will only try
to complete a word with makes sense according to the command grammar.

Example: in a scenario with a fligh numbered `ABC1234` and an airport `AZZ`, the
autocompletion will react differently:

>>> A
>>> ABC1234

>>> AZA1234 LAND A
>>> AZA1234 LAND AZZ

This is especially useful for flight numbers, that can be tedious to be
memorised.

Command history
---------------
By pressing the :kbd:`Up` and :kbd:`Down` keys, it is possible to browse the
command history.

Deletion
--------
Beside the standard :kbd:`Backspace` key, it is also possible to:

* completely erase the prompt line with :kbd:`Esc`,
* delete the last word on the prompt with :kbd:`Control-Backspace`.

Approaching
-----------
Make sure to approach the airport for landing at a reasonable speed: **the
slowest the speed, the easier** it will be for the aeroplane to *adjust their
altitude* to that required for ILS approach.

A slower speed also means that it will be easier for palnes to *keep separation*
(just before landing, planes drop their speed to the minimum, so there is a
risk for oncoming planes in the landing queue to come too close).
