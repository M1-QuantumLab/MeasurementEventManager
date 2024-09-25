Design philosophy
=================


Preamble
--------


In most domains, scientific experiments are carried out by the coordinated
setting of parameters and stimuli, and reading recorded values, to and from
several specialized hardware instruments to a single computer.

The user controls the measurement process through an *instrument server*: an
application (either open or proprietary) that is responsible for coordinating
this communication between the instruments and the computer. 
Via instrument-specific driver modules, this can be done across different
interfaces (serial, GPIB, TCP/IP) using communications protocols such as SCPI,
with all the nitty-gritty details hidden from the user by abstraction layers.

The user specifies stimulus values through the instrument server interface,
either programmatically or through a GUI, runs a measurement that returns some
recorded values, and then analyzes the data using further tools.

At the time of writing, the growth of quantum technologies has led to a
somewhat fractioned (and at times frustrating) landscape of instrument server
software in microwave-domain quantum devices research.
Hardware instruments often ship with proprietary drivers and/or instrument
server software, imposing constraints on data formats and workflow styles.
Research groups in both the public and private sectors can find themselves
sticking to inferior or limiting software in order not to disrupt a hard-earned
legacy workflow, or group members can find themselves siloed off from their
colleagues with different levels of workflow flexibility.


Motivation & objectives
-----------------------


The primary objective of the MeasurementEventManager (MEM) ecosystem is to
facilitate carrying out measurements for scientific experiments, subscribing to
the following criteria:

#. The software structure should be designed to **track measurement
   provenance**, systematically and with minimal user input, maintaining a
   robust relationship between inputs/definitions and the resulting data
   without relying on the instrument server.
#. The measurement specification should be **agnostic** to lower layers in the
   stack (instrument server, drivers, hardware), as well as generation method
   (programmatic or manual). 
   This prevents proprietary vendor lock-in, and allows measurements to be
   recreated effortlessly with the same experimental system, and with minimal
   effort with a different one.
#. There should be a separation between measurement **definition** and
   **execution**, allowing for flexible batch measurements, queueing, and
   programmatically/autonomously generating specifications based on the
   analyzed results of prior measurements.


Design principles
-----------------


In terms of actual implementation, design principles which are industry
standards in software engineering are (regrettably) often overlooked in the
quick-and-dirty world of scientific computing.
However, appreciating the following in particular is instrumental to
understanding the functioning of the MEM.

**Different responsibilities belong to different elements of the software.**
Typically, this refers to functions or classes dedicated to a specific
purpose, but in the MEM this is taken further to a simple form of
micro-service architecture, where the responsibilities of user interaction,
hardware instrument communication ("measurement"), data processing, and
overall coordination are handled by distinct processes/"applications".

**Logic and data specifications are treated and stored differently.**
*Data* refers to the input and output values that define the experimental
process, and *logic* refers to the actual (Python) code that interprets,
processes, and acts on the data.
Typically, they intermingle in a Python script, inviting unwelcome limitations
to the scientific process.
In contrast, data without logic can be stored and transmitted effortlessly,
in formats much better suited for provenance tracking and archiving.
Logic stored without data, on the other hand, leads to an easily-maintained
codebase (no hard-coding!) with an unpolluted version control history.
