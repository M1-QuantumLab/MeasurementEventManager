import setuptools

## Dependencies
_requires = [ r for r in
              open('requirements.txt', 'r')\
              .read().split('\n') if len(r)>1 ]

setuptools.setup(
    name='MeasurementEventManager',
    version="0.0.1",
    description='Server for measurement queuing and processing',
    author='Sam Wolski',
    python_requires='>=2.7',
    packages=["measurement_event_manager"],
    install_requires=_requires,
    scripts=[
            "bin/run_mem",
            "bin/launch_measurement",
            ],
)