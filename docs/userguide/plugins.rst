Instrument server plugins
=========================


Recall that the MEM is intended as an enhancement layer over and above the
tools that are already in use in the lab.
This is primarily for the sake of laziness (or efficiency, take your pick), as
a lot of time and money has probably been spent on the lower levels of the
stack.

One such item is the *instrument server*, the software application used to
coordinate communication between different hardware instruments.
Numerous examples exist, some proprietary such as Keysight's Labber, and some
open-source, such as the in-house pyHegel at the Université de Sherbrooke.
What they mostly have in common is that they have a bunch of instrument drivers
associated with them (to communicate with the individual hardware instruments),
and they tend to provide some form of API for scripting access.

The MEM ecosystem communicates with an existing instrument server application
through an *instrument server plugin*, which is an interface between the
MEM Controller service and the instrument server API.
From the perspective of the MEM, the instrument server and instrument drivers
are effectively the "experimental backend", and the goal is then to hide as
much of this lower-level detail from the user as possible.


The MEM aims to make modifications in both "directions" easy:

- For users looking to introduce the MEM into their workflow, the underlying
  instrument communication and coordination remains the same.
  The user experience with regards to the big picture, *i.e.* things that
  matter to the scientific investigation, is (hopefully) improved.
- For existing users, having the MEM as the primary user-facing layer implies
  that changes to the experimental backend, such as replacing instruments or
  the instrument server software, will not affect the big-picture workflow.


Available plugins
-----------------

There are some ready-made plugins that ship with the MEM distribution;
if you're using one of these applications as your instrument server, you should
be good to go straight out the box.

- The :doc:`Sleeper </autoapi/measurement_event_manager/server_plugins/sleeper/SleeperServer>`,
  which is a do-nothing mockup for debugging and testing.
- :doc:`pyHegel </autoapi/measurement_event_manager/server_plugins/pyhegel/PyHegelServer>`,
  by Christian Lupien at the Université de Sherbrooke.

If your instrument server of choice does *not* appear on this list, you will
have to write your own plugin for the MEM to function.
Be sure to inherit from the abstract
:doc:`BaseServer </autoapi/measurement_event_manager/server_plugins/base/BaseServer>`
class, and implement all the required methods.
