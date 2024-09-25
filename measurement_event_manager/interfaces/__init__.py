## We don't import anything here as we don't want a specific interface
## definition to be dependent on being able to import other interface
## definitions

"""
The various services/applications that make up the MEM ecosystem are defined by
and conform to the communication protocols that dictate how messages between
them are structured and what the expected responses and behaviours to them are.

To separate the public and private functionality of the MEM services, the
internal interfaces are defined as classes in this module.
Instances of these classes should own (in the case of processes which receive
communication) or be owned by (in the case of processes which initiate
communication) their corresponding MEM service objects (eg. an EventManager,
Controller, etc.)
This allows the interface classes to convert API calls to and from the
standardized messages.

For users looking to customize the *user interface* of the Guide or Listener
services, it is only necessary to modify the actual Guide or Listener object
definitions, retaining their relationships to these interfaces as-is.
"""
