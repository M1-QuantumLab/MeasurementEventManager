.. _event-manager-launch:

Server launch
=============


The EventManager service can be started by invoking it from the command-line
with

::

   $ mem_server <instrument_config>

where ``<instrument_config>`` should be the path to a yaml-style file that
specifies the instrument launch options (see below).

When the EventManager service is running, the standard output will show a
message and animated "spinner" to indicate its active status:

::

   Server active ▃▅▇

When receiving requests or carrying out actions, log messages will be printed
to the standard output and/or a log file, according to the set logging levels.
These can be modified using the command-line options ``--console-log-level``
and ``--file-log-level``, which accept the
`standard Python logging level names <https://docs.python.org/3/library/logging.html#levels>`_
or corresponding integer values.

Internally, the server repeatedly polls its messaging sockets with a default
interval of 5 seconds.
This can be modified using the ``--tick-interval`` command-line option.

All the available command-line options can be seen with

::

   $ mem_server --help



Instrument config file
----------------------


The instrument config file, required when launching the EventManager, specifies
the launch options for the hardware instruments (or more specifically, their
drivers).
It takes the following form:

::

   <instrument 1 nickname>:
      <instrument 1 driver name>:
         - <launch arg 1>
         - <launch arg 2>
         ...

   <instrument 2 nickname>:
      <instrument 2 driver name>:
         - <launch arg 1>
         - <launch arg 2>
         ...

   ...

The instrument nicknames are those which will be used to refer to the
instrument in the MEM measurement definitions.
For example, if we are connecting to a Rohde & Schwarz ZNB Network Analyzer,
the instrument driver (associated with the instrument server application) may
have a name like ``rs_znb_network_analyzer``, but we can specify its nickname
to be much simpler, like ``vna``.

The launch args are typically just the instrument communication address, for
example an IP or GPIB address, but can include other options supported by the
instrument driver.
Note that these are exclusively *launch* options; any instrument parameters
that are set using key-value associations should be specified elsewhere, such
as in the measurement definitions.

The use of instrument nicknames in the measurement definitions allows us
to decouple the conceptual elements of the measurement definition ("what we
want to measure") from the technical details of the hardware instrument and
its connection.
In particular, if we move our measurement to a different experimental setup,
say using an Agilent PNA-L instead, we need solely to change the instrument
driver name and its launch options, while the ``vna`` nickname remains valid
in all our measurement definitions.
The instruments, of course, must serve the same function, and their interfaces
must be sufficiently compatible, but it is typically clear whether or not this
makes sense for a given set of instruments.
