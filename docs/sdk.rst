.. _sdk:

Python SDK
========================================
The SDK is best for writing Python scripts to interact with your RedBrick AI organization & projects. The SDK offers granular
functions for programmatically manipulating data, importing annotations, assigning tasks, and more.

altadb
----------------------
.. automodule:: altadb
   :members: get_dataset
   :member-order: bysource

.. _org:

Organization
----------------------
.. autoclass:: altadb.organization.AltaDBOrganization
   :members: name, org_id



.. _project:

Dataset
----------------------
.. autoclass:: altadb.dataset.AltaDBDataset
   :members: name, org_id
   :show-inheritance:

