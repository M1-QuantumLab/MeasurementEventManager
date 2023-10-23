import setuptools

## Dependencies
_requires = [ r for r in
              open('requirements.txt', 'r')\
              .read().split('\n') if len(r)>1 ]

setuptools.setup(
    name='MeasurementEventManager',
    version="0.0.2",
    description='Server for measurement queuing and processing',
    author='Sam Wolski',
    python_requires='>=2.7',
    packages=["measurement_event_manager"],
    install_requires=_requires,
    entry_points={
        'console_scripts': [
            'mem_server = measurement_event_manager.cmdline:mem_server',
            'mem_launch_measurement = measurement_event_manager.cmdline:mem_launch_measurement',
            ],
        },
)