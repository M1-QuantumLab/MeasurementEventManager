Measurement definitions
=======================


Measurements are defined using plain-text key-value (PTKV) data which is
then packaged in
:doc:`MeasurementParams </autoapi/measurement_event_manager/measurement_params/MeasurementParams>`
objects.

.. note::

   Although the user is not required to directly interact with MeasurementParams
   objects at any point, it is helpful to understand their behaviour as they
   provide constraints on the components of a measurement definition.

A measurement definition is constructured from a dict or Python mapping,
with several top-level keys corresponding to attributes of the resulting
MeasurementParams object.
For user-input-based usage, it is recommended to store the measurement
definition in a YAML file, which can be read and parsed by a Guide client.
For programmatic usage, a ``dict`` or mapping-like object can be used directly.


submitter
---------

``str`` identifying the person or entity submitting the
measurement.

Example (YAML):

::

   submitter: brian


metadata
--------

``dict`` with any user-specified key-value pairs.
To be used for identifiers describing the measurement, for example a
sample identifier, cooldown identifier, measurement type, etc.
These will be passed to the instrument server plugin, generally intended for
storing in the resulting output files.

Example (YAML):

::

   metadata:
      measurement_type: vna_spectroscopy
      sample_id: 12
      cooldown: "J-14"


output
------

``dict`` consisting of the following entries:

- ``data_dir``, specifying a path to the output directory.
- ``filename``, specifying a name or template for the output file.
- ``channels``, a list of dicts corresponding to the instruments/sources from
  which measurement data is to be read.
  The exact details of this specification depend on the instrument server
  plugin, but will typically involve the instrument nickname, and a
  specification of which device/channel/etc. to read from.

Example (YAML):

::

   ## Targeting the pyHegel server plugin
   output:
      data_dir: "data/raw/"
      filename: "A2024-03-10_0123.csv"
      channels:
         - instrument: vna
           device: readval
         - instrument: temp_control
           device: fetch


setvals
-------

``dict`` consisting of entries with instrument nicknames as keys and ``dict``
values.
These are specifications indicating which value each instrument channel will be
set to, *before* the measurement starts.

Example (YAML):

::

   setvals:
      vna:
         bandwidth: 100
         freq_start: 4.0e+9
         freq_stop: 8.0e+9
         npoints: 8001
         traces: ["S21", "S11"]
      smu:
         output_1_volt: 2.5
         output_2_volt: -1.2


sweep
-----

``list`` consisting of sweep specification ``dict`` entries.
Each sweep specification represents a single channel in a single instrument
whose values will be varied throughout the measurement.

.. note::

   The sweeps are *slow* to *fast*, i.e. the last sweep in the list will act as
   the innermost loop.

Example (YAML):

::

   sweep:
      - instrument: smu
        channel: output_3_volt
        sweep_type: lin
        start_value: -0.1
        stop_value: 0.1
        n_pts: 101
      - instrument: vna
        device: port_power_dBm
        sweep_type: lin
        start_value: -30
        stop_value: 5
        n_pts: 36
