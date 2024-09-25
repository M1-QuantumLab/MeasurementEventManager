Measurements
============


The administration and execution of measurements is the core of the MEM
workflow.
Here, a "measurement" refers to a single measurement event with respect to the
instrument server application.
That is to say, the execution of a single measurement begins when the
user would normally press "start" in the instrument server application, and
ends when control would be returned to the user with all systems ready for the
next set of inputs.
In particular, the measurement includes any parameter sweeps or pre-programmed
delays, but is nonetheless considered as a single unit.


.. toctree::

   measurements/definitions
   measurements/submit

