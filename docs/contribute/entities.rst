.. index:: Entity

Entities
========

With the term *entities* we refer to all those in-game elements whose difference
of behaviour is purely due to a difference between the parameters they are
intialised with. We use this term to mark a clear distintion with the
:doc:`plugins`.

This means that to contribute a new entity to the game (for example a new
aeroport map) **you do not need to be able to program**. In fact ATC-NG uses
:term:`YAML` to describe all its in-game *entities*. YAML is a
*human friendly data serialization standard*, and this means that is
very straightforward to create new entities or modify the existing ones.

You can have a preview of how the yaml files look like for each of the
implemented entities by browsing through the `appropriate folder`_ of the main
repo.

.. _`appropriate folder`: https://github.com/quasipedia/atc-ng/tree/master/entities/data

Please observe that there is yet no guarantee this is the final format for the
game. As soon as the format will be deemed stable for the 1.x series, this
page will be expanded with an explanation of each entity data.

.. index::
   pair:Aeroplane; Entity

Aeroplane models
----------------
Stub.

.. index::
   pair:Aeroport; Entity

Aeroports
---------
Stub.

.. index::
   pair:Scenario; Entity

Scenarios
---------
Also contains Beacons and Gates.
Stub.
