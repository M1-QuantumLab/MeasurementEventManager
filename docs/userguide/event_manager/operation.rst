Server operation
================

Once started, the EventManager runs without any further direct interaction from
the user.
Interaction instead takes the form of **requests** sent via ZeroMQ messages
from Guide and Controller services.
Requests via the Guide interface are used to modify or receive information
about the measurement queue.
Requests via the Controller interface, initiated automatically, inform the
EventManager about when measurements start or end.


State variables
---------------


The most important data stored by the EventManager are:

- The **queue** of measurement definitions to be run.
- The **fetch counter**, an integer indicating how many measurements should be
  run before halting.

The queue is simply an ordered container for Measurement objects, allowing for
addition and removal at arbitrary positions.
The EventManager will always attempt to draw measurements from the front of
the queue.

.. note::

   To maximize stability, queue functionality is intentionally rudimentary
   on the server-side.
   Advanced queue operations should be wrapped/automated via custom Guide
   client functionality.


It is worth distinguishing between three qualitatively different modes of
operation based on the value of the fetch counter.

- At 0, no measurements will be launched, so the user can modify the queue,
  set up batch runs, debug and test, etc. without any time pressure.
- At positive values, exactly that number of measurements will be launched,
  decrementing the fetch counter each time.
  This can be used to launch well-defined batches of measurements while
  retaining the ability to freely modify any measurements in the queue beyond.
- At negative values (normalized to -1), the EventManager will run in "endless"
  mode, always attempting to launch any measurement at the front of the queue.


.. note::

   The default value of the fetch counter on EventManager service launch is 0,
   but this can be modified via the ``--fetch-counter`` command-line option.


Order of operations
-------------------

During each iteration of the server event loop, the following operations are
attempted:

1. Trigger a new measurement attempt
2. Process any incoming Guide requests
3. Process any incoming Controller requests

A new measurement attempt will launch the next measurement from the queue when
this is allowed and possible.
In particular, this involves the following checks:

- There is no measurement currently running
- The fetch counter is not zero
- The next measurement can be taken from the queue

If these conditions are all met, the next measurement is launched via a new
Controller process (spawned automatically by the EventManager), and the fetch
counter is decremented.

.. warning::

   Once a measurement has been launched, it is assumed to be continuously
   running until a measurement end message is received from the Controller.
   Consequently, if the measurement freezes or fails externally to the MEM
   services, the EventManager will be left in a soft-locked state wherein it
   can receive and process requests, but cannot launch further measurements.
   Currently, the only resolution is manual termination of the EventManager
   process.
