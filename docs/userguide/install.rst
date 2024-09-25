Installation
------------

The MEM is currently only available from the
`GitHub repository <https://github.com/M1-QuantumLab/MeasurementEventManager>`_.

#. `Clone the repo <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository>`_.
#. (Recommended) Create a dedicated Python virtual env (using eg
   `Anaconda <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_
   ). Make sure you use a version of Python supported by the MEM package.
#. Navigate to the package directory in a terminal using ``cd``.
#. ``pip install .``, with the optional ``-e`` flag for develop mode to see
   code changes without reinstalling.

Once the module is installed, the ``mem_server`` application should be
available at the command-line.

The module can also be imported in Python

::

   import measurement_event_manager as mem

when using the API in custom scripts or classes.
