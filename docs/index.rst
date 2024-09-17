MeasurementEventManager documentation
=====================================


The MeasurementEventManager (MEM) is an ecosystem for creating, running, and
tracking scientific experiments.

It was originally designed for use in microwave-domain quantum devices research
at the group of Mathieu Juan (M1 Quantum Lab) at the Institut Quantique at the
Université de Sherbrooke in Québec, Canada.
However, it aims to use a generally-agnostic structure and design principles,
so can in principle be used for any scientific experiments where a computer
interfaces with instruments to set stimuli and read recorded values.

The MEM was created to address specific shortcomings and pain points of the
software ecosystem within the target research domain, as discussed under the
section on :doc:`design & structure <design>`.
For **prospective users**, this discussion may help you understand if MEM is
the right tool for your job, and what its strengths and weaknesses are.

The :doc:`user guide <usage>` provides examples to familiarize you with the
MEM workflow and its capabilities.


.. note::

   This project is under active development.


Contents
--------

.. toctree::
   :maxdepth: 2

   About <self>
   design
   usage
   API reference <autoapi/measurement_event_manager/index>
