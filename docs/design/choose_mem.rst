Is MEM right for you?
=====================


Although it tries very hard to be an all-in-one solution, design choices
resulting from the underlying :doc:`objectives </design/philosophy>` mean that
the MEM is naturally suited to some classes of measurements, and their
corresponding administrative tasks, better than others.


Ecosystem requirements
----------------------


- Python 3.9 or later
- An existing instrument server application and associated drivers for hardware
  instruments.
- A :doc:`plugin </userguide/plugins>` for the instrument server's API.
  If you are not using one that has a corresponding plugin that
  :doc:`ships with MEM </autoapi/measurement_event_manager/server_plugins/index>`,
  you may have to write your own.


Strengths & benefits
---------------------


- Focus on the actual science, rather than bookkeeping parameters and
  provenance; no more desperately trying to remember which parameters were used
  as inputs for that one measurement a long time ago.
- Manage upcoming experiments in an interactive queue; no need to stop the
  current measurement because you noticed a mistake in the specifications for
  an upcoming one and need to re-do the batch script.
- Keep your measurement definitions when switching hardware or low-level
  software; no need to keep putting up with proprietary software because their
  hardware is good.


Limitations
-----------

Unfortunately, the MEM will probably not be a good fit for your workflow in
the following cases:

- Fast-feedback measurements, "fast" here indicating that the measurement
  feedback loop is required to take the same order of time as launching an
  individual measurement with the instrument server application.
  MEM works best for managing multiple longer, slower measurements, especially
  in batches.
- Setups where the hardware instrument (and/or driver) *launch* parameters need
  to be changed rapidly. I can't really think of a good example of such a
  situation, but in any case the MEM works best when the EventManager service
  is launched a single time and runs continuously.
- Setups where multiple distinct measurements need to be run in parallel from a
  single controlling computer or server.
  Note that this is *not* the same as receiving output from multiple
  instruments simultaneously as part of a single measurement, which is
  supported.
