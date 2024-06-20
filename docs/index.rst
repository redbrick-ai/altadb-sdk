======================================
AltaDB SDK and CLI
======================================
RedBrick AI is a SaaS platform for annotating medical images. RedBrick AI provides web based annotation tools, quality control capabilities, collaboration tools, and SDK/CLI to integrate with MLOps.
AltaDB is a product of RedBrick AI, and is a platform for managing medical imaging data, annotations.

.. important:: Please visit our `website <https://redbrickai.com>`_ to learn more about RedBrick AI, or request for a free-trial. You can visit the platform documentation here `<https://docs.redbrickai.com/>`_.

The AltaDB SDK and CLI are useful for managing data IO operations, and programmatically interacting with the application. The CLI is best for simple operations like import and export; whereas, the SDK is best for complex operations like importing annotations, searching through data, etc.

**Installation**

The SDK and CLI are available on PyPI and can be installed using `pip`.

.. code:: bash

   $ pip install altadb

**Authentication**

To use the SDK and CLI, you need a API key. You can fetch the API key from the AltaDB dashboard, found on the right sidebar "API keys".

.. image:: _static/api2.png


**Organization ID**

For most methods in the CLI and SDK you will need an Organization ID. It can be found from the URL.

.. image:: _static/id2.png

Command Line Interface
=======================================
The AltaDB CLI offers a simple interface tointeract with your datasets, and perform other high-level actions.

.. card::
   :link: cli
   :link-type: ref

   :material-regular:`link;1.5rem;sd-mr-2` See the :ref:`cli` documentation for more information.

.. toctree::
   :hidden:
   :maxdepth: 2

   cli
