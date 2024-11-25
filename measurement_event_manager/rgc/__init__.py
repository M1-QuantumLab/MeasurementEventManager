"""
This module provides a reference implementation of a Guide client application
with various user interface paradigms.

The Guide application is the intended means of user interaction with the MEM
ecosystem.
In particular, the Guide application translates the user's commands, be they
specified in a script, an interactive shell, or otherwise, into MEM requests
transmitted to the server.
A sophisticated Guide application can also relay the server's responses back
to the user, and while this is highly recommended, it is strictly speaking not
required.

The core of this reference implementation is the ReferenceGuideClient class.
This class can be instantiated and used directly in a script or interactive
Python interpreter. 
This provides an API-style access to typical Guide service features in a more
user-friendly way than interacting with a GuideRequestInterface object
directly.

The classes provided here are *not* intended as bases which all user-extended
classes must inherit from (although of course the user is welcome to do so).
The interfaces are instead the objects whose APIs should be conformed to.
"""

from .rgc import ReferenceGuideClient
