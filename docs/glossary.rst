.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   \*nix
      The term *unix-like* (sometimes shortened to \*nix to circumvent trademark
      issues) is widely used to describe operating systems that share many of
      the characteristics of the original UNIX, which was written in 1969 by Ken
      Thompson at Bell Labs. GNU/Linux and BSD are amongst the unix-like family
      of operating systems.

      Traditionally, users of \*nix systems are very versed in the shell
      environment, a commandline interface operated from keyboard only, hence
      the auxiliary origin of the ATC-NG game, which operates purely through
      keyboard input.

   Airway
      Airways are corridors of controlled airspace with a defined lower and
      upper base. In ATC-NG airways start/finish at the edge of the aerospace
      generating the so called :term:`gates<gate>`. All aeroplanes that are not
      on ground must enter and exit the aerospace from them.

   Flight level
      In ATC-NG, a flight level is the standard nominal altitude of an aircraft
      above the sea level, expressed in hundreds of metres. For example FL 05
      means "500 metres asl".

      Flight levels are the parameter for the ``ALTITUDE`` command.

   Gate
      Gates in ATC-NG are the entry/exit points for the aircrafts. An
      explanation of how to instruct an aeroplane to use a exit through a gate
      is available :doc:`here<play/leaving-aerospace>`

   IATA
      IATA stands for *International Air Transport Association*. IATA's mission
      is to represent, lead, and serve the airline industry. IATA represents
      some 230 airlines comprising 93% of scheduled international air traffic.

      ATC-NG uses the IATA airport designators, for example ``ARN`` for the
      Stockholm Arlanda airport and ``FRA`` for the Frankfurt Main one.

   ICAO
      ICAO stands for *International Civil Aviation Organization*. ICAO is a
      specialized agency of the United Nations. It codifies the principles and
      techniques of international air navigation and fosters the planning and
      development of international air transport to ensure safe and orderly
      growth.

      ATC-NG uses the ICAO airline designators, for example ``SAS`` for
      Scandinavian Airlines or ``DLH`` for Lufthansa.

   ILS
      ILS stands for *Instrument Landing System*. ILS is a system that provides
      precision guidance to an aircraft approaching and landing on a runway,
      using a combination of radio signals and, in many cases, high-intensity
      lighting arrays to enable a safe landing.

      ATC-NG simulates the presence of ILS at each runways of each aeroport on
      in the scenario. The AI pilots use the simulated ILS to touch down
      autonomously when instructed to land.

   TCAS
      TCAS stands for *Traffic Collision Avoidance System*. TCAS is an aircraft
      collision avoidance system designed to reduce the incidence of mid-air
      collisions between aircraft. It monitors the airspace around an aircraft
      for other aircraft equipped with a corresponding active transponder,
      independent of air traffic control, and warns pilots of the presence of
      other transponder-equipped aircraft which may present a threat of mid-air
      collision.

      ATC-NG simulates the presence of a TCAS on each aircraft in the game
      in the scenario. Whenever the player fails to maintain separation between
      two or more aeroplanes, the TCAS will instruct the AI pilots to steer away
      from each other.

   Markup language
      A mark-up language is a modern system for annotating a text in a way that
      is syntactically distinguishable from that text. The idea and terminology
      evolved from the "marking up" of manuscripts. Markup is typically omitted
      from the version of the text which is displayed for end-user consumption.

      ATC-NG uses two markup languages internally: :term:`reStructuredText` for
      its documentation and :term:`YAML` for its entities, although it should be
      mentioned that the latter is not a markup in the strict sense of the word.

   reStructuredText
      reStructuredText is an easy-to-read, what-you-see-is-what-you-get
      plaintext markup syntax and parser system. reStructuredText is a revision
      and reinterpretation of the StructuredText and Setext lightweight markup
      systems. More info on the format are available on the
      `reStructuredText website`_.

.. _reStructuredText website: http://docutils.sourceforge.net/rst.html

   Runway
      According to ICAO a runway is a *"defined rectangular area on a land
      aerodrome prepared for the landing and take-off of aircraft."*

      Runways are named by a number between 01 and 36, which is generally one
      tenth of the magnetic azimuth of the runway's heading: a runway numbered
      09 points east (90°), runway 18 is south (180°), runway 27 points west
      (270°) and runway 36 points to the north (360° rather than 0°). If there
      is more than one runway pointing in the same direction (parallel runways),
      each runway is identified by appending Left (L), Center (C) and Right (R)
      to the number.

      ATC-NG models its aeroport on real ones, and therefore the size and naming
      of the runways is the real one. ATC-NG - though - doesn't simulate Earth's
      magnetic field, and thus the orientation of runways is relative to the
      geographical north.

   YAML
      YAML is a human-readable data serialization format (that is: a format for
      displaying computer-readable data which is nice to the eye of humans).
      YAML is a recursive acronym for "YAML Ain't Markup Language". Early in its
      development, YAML was said to mean "Yet Another Markup Language", but was
      retronymed to distinguish its purpose as data-oriented, rather than
      document markup. More info on the format are available on the
      `YAML website`_.

.. _YAML website: http://yaml.org/
