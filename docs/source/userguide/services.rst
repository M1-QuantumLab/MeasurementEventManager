Services
--------


The MEM ecosystem consists of at least three components, running as separate
processes on the same (or different!) host computer(s).

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
