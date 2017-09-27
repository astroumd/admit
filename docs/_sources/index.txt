.. ADMIT documentation master file, created by
   sphinx-quickstart on Thu Jan 22 18:48:45 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The ALMA Data Mining Toolkit
============================

The ALMA Data Mining Toolkit (ADMIT) is a value-added Python software package
which integrates with the ALMA archive and CASA to provide scientists with
quick access to traditional science data products such as moment maps,
as well as with new innovative tools for exploring data cubes and their many
derived products. The goals of the package are to:

- make the scientific value of ALMA data more immediate to all users

- create an analysis infrastructure that allows users to build new tools

- provide new types of tools for mining the science in ALMA data

- increase the scientific value of the rich data archive that ALMA is creating

- re-execute and explore the robustness of the initial pipeline results.

ADMIT is funded as an `ALMA Development Project,
<https://science.nrao.edu/facilities/alma/alma-development-2015/alma-development/alma-development-north-america>`_
and was introduced as version 1.0 in May 2016, with
a final delivery to NRAO in October 2016 as version 1.1, but under continued development in git.

Beginners' User Guide
---------------------

.. toctree::
   :maxdepth: 2

   userguideintro

For Advanced Users
------------------
.. toctree::
   :maxdepth: 2

   api
   multiflows
   examplescripts
..   shcasa

Developer Zone
--------------

Information of interest to developers.

.. toctree::
   :maxdepth: 1

   installguide
   design
   style
   examples
   casapython
   tricks
..   doctest


Indices
-------

.. only:: html

  * :ref:`genindex`
  * :ref:`modindex`
  * :ref:`search`
  * `Todo List <todo.html>`_
