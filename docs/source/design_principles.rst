Design principles
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


Design goals
------------


The design goals of the MeasurementEventManager (MEM) ecosystem are to carry
out measurements for scientific experiments in a way that:
1. There should be a separation between measurement *definition* and
*execution*, allowing for flexible batch measurements, queueing, and
generating specifications based on the analyzed results of prior measurements.
2. The measurement specification should be agnostic to lower layers in the
stack (instrument server, drivers, hardware), as well as generation method
(programmatic or manual).

From the these goals, the following principles were established for the MEM
ecosystem:
1. Measurement definition and execution are handled by separate processes,
which may even run on separate computers.
2. The measurement specification is plain-text key-value (PTKV), such as a YAML
file which can be interpreted as a Python dictionary.


Motivations
-----------


At the time of writing, the growth of quantum technologies has led to a
somewhat fractioned (and at times frustrating) landscape of instrument server
software in microwave-domain quantum devices research.
Hardware instruments often ship with proprietary drivers and/or instrument
server software, imposing constraints on data formats and workflow styles.
Research groups in both the public and private sectors can find themselves
sticking to inferior or limiting software in order not to disrupt a hard-earned
legacy workflow, or group members can find themselves siloed off from their
colleagues with different levels of workflow flexibility.

A possible mitigation arises through the addition of an additional abstraction
layer.
