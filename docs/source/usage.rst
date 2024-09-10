Usage
=====

.. _structure:
.. _installation:
.. _eventmanager:


Structure
---------

The MEM ecosystem consists of at least three components, running as separate
processes on the same or different host computer(s).
This package provides the core EventManager service, which acts as a
coordinating hub, as well as the Controller service, which controls the
execution of an individual measurement.

In typical usage, a Guide service is also required to interface with the
EventManager.
Here are some publicly-available Guide clients:
- `samsguideclient <https://github.com/SamWolski/samsguideclient/>`_

In case none of the Guide client applications suit your needs, you can write
your own!
You can use any language supporting `ZeroMQ <https://zeromq.org>`_, and your
application should conform to the appropriate version of the MEM Client
protocol.


Installation
------------

foo bar