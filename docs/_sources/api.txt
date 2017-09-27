Python Scripting Interface (API)
================================

ADMIT offers an extensive collection of pre-defined modules for creating
data processing scripts in Python. The programming interface is divided into
several importable packages, whose contents are detailed in the following
sections. Names in **boldface** indicate the name of the class as imported into
the top-level ``admit`` module (e.g., ``admit.Ingest_AT``); these are the names
users will see in scripts. Otherwise, class names reside within the
corresponding module only (e.g., ``admit.xmlio.Parser``). The detailed
documentation for each item contains the full, low-level Python class name
(e.g., ``admit.at.Ingest_AT.Ingest_AT``), which indicates where the class's
Python code can be found within the ADMIT source tree.


Module `admit`
--------------

.. toctree::
   :glob:

   module/admit/*


Module `admit.at`
-----------------

.. toctree::
   :glob:

   module/admit.at/*



Module `admit.bdp`
------------------

.. toctree::
   :glob:

   module/admit.bdp/*


Module `admit.recipes`
----------------------

.. toctree::
   :maxdepth: 1
   :glob:

   module/admit.recipes/*


Module `admit.util`
-------------------

.. toctree::
   :glob:

   module/admit.util/*


Module `admit.util.continuumsubtraction`
----------------------------------------

.. toctree::
   :glob:

   module/admit.util.continuumsubtraction/*
   module/admit.util.continuumsubtraction/spectral/*
   module/admit.util.continuumsubtraction/spectral/algorithms/*


Module `admit.util.filter`
--------------------------

.. toctree::
   :glob:

   module/admit.util.filter/*


Module `admit.util.peakfinder`
------------------------------

.. toctree::
   :glob:

   module/admit.util.peakfinder/*


Module `admit.util.segmentfinder`
---------------------------------

.. toctree::
   :glob:

   module/admit.util.segmentfinder/*


Module `admit.xmlio`
--------------------

.. toctree::
   :glob:

   module/admit.xmlio/*
