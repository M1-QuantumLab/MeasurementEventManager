Application components
======================


The MEM ecosystem consists of several component applications, running as
separate processes on the same (or different!) host computer(s).

- The **EventManager** service acts as a coordinating server, maintaining a queue
  of measurements based on user requests, initiating their launches, and
  broadcasting the results.
- The **Controller** service is spawned by the EventManager when a measurement is
  launched, and acts as an interface between the EventManager (and thus the MEM
  ecosystem as a whole) and an instrument server application, and by extension
  the hardware instruments.
- The **Guide** service provides an interface for the user, allowing sending
  commands to and receiving information from the EventManager.
- The **Listener** service (optional) allows for automated data processing,
  executing and passing data to analysis functions when a measurement
  completes.

The services communicate with each other through *messages* (via the ZeroMQ
library), so the "connections" between them should be thought of as transient,
rather than continuous.

In brief, the control flow for an experimental session is:

- The EventManager and any Listener services must be started by the user and
  left running for the duration of the session (daemons).
  They will act autonomously upon receiving requests from any Guide services
  (for the EventManager) and the EventManager (for Listeners).
- Guide services can take any form convenient for the user, involving
  script-based execution, an interactive UI, or a daemon for feedback loops.
  User requests are communicated to the EventManager.
- Controller services are launched without user intervention, and are
  effectively invisible to the user if everything runs correctly.

.. note::

   The EventManager is the only application that must run on the experiment
   control computer.
   In principle, the other services can be run on the experiment control
   computer or communicate over a network, as desired.

This package provides the core
:doc:`EventManager </autoapi/measurement_event_manager/event_manager/EventManager>`
and
:doc:`Controller </autoapi/measurement_event_manager/controller/Controller>`
services.

Here are some publicly-available Guide clients:

- `samsguideclient <https://github.com/SamWolski/samsguideclient/>`_

In case none of the Guide client applications suit your needs, you can write
your own!
You can use any language supporting `ZeroMQ <https://zeromq.org>`_, and your
application should conform to the appropriate version of the MEM Client
protocol.
