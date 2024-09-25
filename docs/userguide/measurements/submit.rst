Submitting measurements
=======================


Measurements are submitted using a Guide client.
Under the hood, a Guide client uses ZeroMQ to send measurement definitions and
other associated requests to the running EventManager, receiving and parsing
the responses.

The rules of the messaging protocol dictate what requests are possible,
although a Guide client is free to provide whatever interface to these requests
best suits the user.

The following examples show the process using
`samsguideclient <https://github.com/SamWolski/samsguideclient/>`_
which will be integrated into the MEM distribution in the near future.
The package provides both a scripting API and an interactive command-line
interface.

.. note::

   Currently, the examples in this section require the ``samsguideclient``
   package.


Interactive command-line interface
----------------------------------

The interactive command-line interface can be invoked from a terminal using

::

   $ sgc -i

The following commands are available in the sgc shell:

- ``add <measurement_path> [<measurement_path_2> ...]`` submits the
  measurement definitions loaded from the files at the various locations
  provided.
- ``remove <index> [<index_2> ...]`` removes measurements at the given indices
  from the queue.
  Any single value or Python slice can be used as an index, for example ``5``,
  ``1:4``, and ``4:6:-1`` are all valid specifications.
  Multiple index specifications will be parsed *before* any deletions are
  carried out, so ``remove 0 3`` will not unintentionally remove the
  item at index 4 (which would be at index 3 once index 0 is removed).
- ``query [<target>]`` fetches the current state of the queue, i.e. all the
  measurement definitions that currently make up the queue.
  These are written to the ``target`` (a file-like object), or if no target is
  provided, printed to the standard output.
- ``len`` fetches the current length of the queue (the number of measurements).
- ``fetch [<counter_value>]`` interacts with the fetch counter.
  If no argument is provided, it gets the current value.
  If an argument is provided, in this case a single integer, the fetch counter
  will be set to this value.
  Note that any negative value will be set to -1 for consistency.
