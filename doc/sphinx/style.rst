.. _Documentation:

Documentation Style Guide
=========================

In documenting ADMIT's Python codebase, there are three specific items to
consider:

(1) the logical information to include when documenting classes and methods

(2) the physical formatting of the documentation source text

(3) the manner of presentation of the documentation to the user

As `Python <http://www.python.org>`_ has a built-in docstring facility, most
Python documentation packages center around how to structure and process them
in a well-defined way.  Since docstrings are object attributes and hence
readily accessible in any interactive Python session, this is a very natural
and advantageous approach.

Although `Doxygen <http://www.doxygen.org>`_ was very familiar to the ADMIT
team and does support Python, it does **not** parse docstrings for its own
markup, instead relying on special comment blocks (starting with ``##``) in a
manner similar to C/C++. Docstrings can still be used but are basically an
independent documentation channel in this case, appearing as pre-formatted
text blocks in the associated output.  For this reason Doxygen was not chosen
to serve as our primary documentation tool.  For Python code development,
however, doxygen *can* still be useful because of its source browser facility,
which will automatically generate an indexed HTML tree of syntax-highlighted
source code for a project. The ADMIT tree contains a ``Doxyfile``
configuration at the top level which will create this tree (in ``doc/html``),
including docstrings verbatim, when ``doxygen`` is run.

To produce the official user documentation, ADMIT has adopted the
`NumPy/SciPy documentation conventions
<https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_.
These appear not only to be the most widely known (and used) of the
docstring-based systems, but ADMIT users are also close to their own user
community. They address all three of the items mentioned above.

This document is *not* a Python coding style guide; the `Google Python Style
Guide <https://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_
presents one set of guidelines for the latter.

NumPy Documentation
-------------------

* Docstrings are logically divided into sections such as brief and extended
  summaries, parameters and return values (for functions), attributes (for
  classes), etc. The most important sections (listed in order of appearance)
  are:

  **Short Summary**
    A brief description of the module, class, class method or function.

  **Extended Summary**
    An expanded description of the functionality of the entity.

  **Keywords**
    A special section for ADMIT tasks describing supported task keywords,
    including type information and default value.  A distinct format is
    required compared to the following sections since ``numpydoc`` deletes
    unrecognized sections. An example is

    ::

      **Keywords**
        **stale** : bool
          Whether task output BDPs are out of date; defaults to True.

        **enabled** : bool
          Whether task execution is enabled; defaults to True.

        ...

    :Note: This section **must** immediately follow the extended summary.

  **Parameters**
    Description of the function arguments/keywords, including type
    information. For classes, constructor arguments are described here
    with the class, not as part of the ``__init__`` method.  The `self`
    argument to class methods is *not* documented.

  **Returns**
    For functions and class methods, a description of its return value(s),
    including type information. The format follows **Parameters** except that
    return values are unnamed.  If no explicit value is returned, the return
    value is `None` (i.e., do *not* omit the section).

  **Attributes**
    For classes, a description of class (or instance) variables, in
    the same style as **Parameters**.

  **See Also**
    Optional section providing references to related documentation.

  **Notes**
    Optional section discussing background considerations or lower-level
    implementation details.  As such (and in contrast to the preceding
    sections), this material may be more oriented toward developers or power
    users than ordinary users.

  **Examples**
    Optional section for examples, presented using the
    `doctest <http://docs.python.org/library/doctest.html>`_ format.

  Aside from the summary and keyword sections, all other sections are
  delimited by `reStructuredText <http://docutils.sourceforge.net/rst.html>`_
  section titles.

* The reStructuredText_ markup language is used for text formatting. This
  markup is basically the de facto standard for formatting docstrings in
  Python. It's a plain-text markup designed to be easily readable on a
  character terminal (preserving the docstring's usability in interactive
  sessions), while allowing post-processors to produce reasonably attractive
  output in other formats (HTML, PDF, etc.). It includes directives for things
  such as:

  - sectioning

  - lists (bulleted and enumerated)

  - links (e.g., to Python_)

  - font styles (**bold**, *italic*, ``monospace``)

  - preformatted text (e.g., code samples)

    ::

      >>> 123 + 222  # Integer addition
      345
      >>> 1.5 * 4    # Floating-point multiplication
      6.0
      >>> 2 ** 100   # 2 to the power 100
      1267650600228229401496703205376

  Another `reST/Sphinx Cheatsheet
  <http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html>`_
  summarizes these and other items.

* The `Sphinx <http://sphinx.pocoo.org/>`_ package is used for post-processing.
  This is also the package used by the Python project itself to produce the
  `official Python documentation <http://docs.python.org/>`_. It has many
  features and can produce attractive output, as demonstrated by the Sphinx
  website itself, created from reStructuredText files using the Sphinx tool.

  Sphinx is a Python application which works by importing project packages
  and modules in order to process the formatted docstrings contained therein.
  Therefore any import dependencies (e.g., CASA for ADMIT) must be satisfied
  for Sphinx as for any other user of the project.

:Note:
  Processing standard `NumPy <http://www.numpy.org/>`_ docstrings with Sphinx
  requires the `numpydoc <http://python.org/pypi/numpydoc>`_ extension module
  for the latter. (This doesn't affect end-users who *consume* our
  documentation, only developers using Sphinx to generate it). The
  numpydoc_ extension requires Sphinx v1.0.1 or later. RHEL/CentOS 6 uses
  v0.6.6 and hence the standard packages should be removed and replaced with
  the current version before building ADMIT documentation. RHEL/CentOS 7
  satisfies the minimum requirements. The numpydoc_ module must be manually
  installed in either case.

--------


ADMIT Documentation Addenda
---------------------------

The `NumPy documentation guidelines
<https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_
cover most Python components, including
modules, classes, class methods, special class instances, constants and
functions. Although reStructuredText_ includes many features, NumPy
documentation employs a rather limited sub-set for its use. ADMIT developers
are encouraged to do likewise, but in practice are free to use any of the more
advanced features they find useful so long as it does not interfere with
Sphinx output or unduly degrade readability of the plain ASCII docstring.

ADMIT follows the convention that classes are defined within a module of the
same name; e.g., ``FlowManager`` is defined in module ``FlowManager.py``
within the ``admit`` package and hence its canonical Python class name is
``admit.FlowManager.FlowManager``. For better integration with Sphinx,
docstrings for ADMIT *modules* (not classes) should use a section header for
the brief description; these will become page titles in the generated output.
This includes package descriptions (whose docstrings reside in the
corresponding ``__init__.py`` file). For example, here is the docstring for
the `FlowManager module <module/admit/FlowManager.html>`_::

  """Flow Manager
     ------------

     Defines the FlowManager class.
  """

Since the `class documentation
<module/admit/FlowManager.html#admit.FlowManager.FlowManager>`_ for
``FlowManager`` already describes its function in complete detail, such
information should not be repeated in the module description.

In class docstrings, for text referencing internal class methods from outside
said method, it is good style to use bold type to highlight the method name;
e.g., "The use of **foo()** over **bar()** is preferred whenever possible..."
With sufficient care, it is also possible to construct live hyperlink
references to methods and other items using knowledge of the documentation
directory tree structure described below, but this is delicate and will
significantly impact ASCII docstring readability unless embedded URIs are
used; for examples see the `FlowManager
<module/admit/FlowManager.html>`_ **Notes** section and the `admit.at
<module/admit.at/0-index.html>`_ package documentation.

It is vital that all ADMIT docstrings represent valid reStructuredText_ input
as the Sphinx documentation will fail to build otherwise.


Maintaining ADMIT Documentation
-------------------------------

The ADMIT documentation source tree resides in the ``$ADMIT/doc/sphinx``
directory and contains a Makefile to build the documentation; a ``make
html`` will generate the HTML version and place it in the ``_build/html``
sub-directory. This output is relocatable and can be copied to a public web
address or included with download packages.

The reStructuredText_ (.rst) documentation source files for ADMIT classes and
modules---one for each component---must be placed in the appropriate
sub-directory of the ``doc/sphinx/module`` directory, which itself contains
one directory for each ADMIT package, named according to its canonical Python
name. For example, for the ``BDP.py`` module, which resides within the
``admit.bdp`` package (physically, the ``$ADMIT/admit/bdp`` directory), the
corresponding source file is ``module/admit.bdp/BDP.rst``. Although these source
files can contain arbitrary markup and information, for the most part they
are simple Sphinx *autodoc* wrappers, such as this one for
``module/admit/FlowManager.rst``::

  .. automodule:: admit.FlowManager

The ``automodule`` directive instructs Sphinx to import the specified module,
process all docstrings it finds within and automatically generate formatted
documentation for the associated components. Additional text may be appended
to these template files, but in general all relevant information should be
placed in the docstrings themselves so that it is available in interactive
sessions as well.

.. sectionauthor:: Kevin P. Rauch <rauch@astro.umd.edu>
