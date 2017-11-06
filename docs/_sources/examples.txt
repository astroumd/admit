*********************************
How To Write Your Own ADMIT Task 
*********************************

So here you are: you love ADMIT so much you want to write your own ADMIT Task.  This guide
provides you with the instructions to do so.   We assume you already understand
the concept of input and output `Basic Data Products`_ (BDPs) and how they relate to 
`ADMIT Tasks`_ (ATs).    In a typical new task, you will want to read in an image cube, do something
to it, and write out the modified cube, and perhaps a table.  For this, you don't need
to define any new type of BDP, so can use the :ref:`template method <The-Quick-Way>`.
If for some reason the BDP base types we have already defined (Image, Table, Line)
are not sufficient for your purposes, you need to :ref:`start from scratch <Basic-example>`
However, you should probably begin with writing a simple task using the template anyway, so you become 
familiar with the basics of AT operation.

.. _The-Quick-Way:

The Quick Way
==============

The easiest way to write your own task is to start with an existing AT
and make modifications to it.   Lucky for you we have provided a template,
aptly called :ref:`Template_AT<Template-AT-api>`, specifically for this use.
Template_AT includes the basic steps of
reading in an image cube, writing out Table and Image BDPs, and writing information about the task to the
:ref:`Summary <Summary-api>` so that you can view your results in the web page.


.. _Basic-example:

Starting from Scratch
======================

Below are basic (Hello World level) examples of how to write a BDP and AT. This is followed by documentation on how
to incorporate new BDPs and ATs into the ADMIT system. The following :ref:`section <Complex-example>`
shows more complex examples. Each example file can be located in admit/doc/examples if you want a closer inspection
or to play with them.

.. _HelloWorld-BDP:

HelloWorld_BDP
~~~~~~~~~~~~~~

The Basic Data Product (BDP) is the basic unit of data storage in Admit. Each BDP is specified in a single
file in admit/bdp. The file contains a single class which holds the data. Every BDP must inherit from the BDP
base class, or one or more other BDPs. There should be only a minimal number of methods defined in each BDP
as they are not meant to do much if any processing.

.. literalinclude:: ../examples/HelloWorld_BDP.py
   :linenos:
   :language: python

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+------------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                    |
+============+==========================================================================================+
| 1-5        | Initial docstring documentation. See the section on :ref:`Documentation` for details.    |
+------------+------------------------------------------------------------------------------------------+
| 6          | Required import statement -- the class that HelloWorld_BDP inherits from, others (e.g.   |
|            | Line_BDP, Image_BDP, & Table_BDP) can also be used. Any other needed includes should be  |
|            | added here.                                                                              |
+------------+------------------------------------------------------------------------------------------+
| 8          | The BDP class name with inheritance. The class name must match the file name (except for |
|            | the .py), in this example the file is called HelloWorld_BDP.py. Also be sure to include  |
|            | any inheritance.                                                                         |
+------------+------------------------------------------------------------------------------------------+
| 9-27       | Notes and documentation for the class. See the section on :ref:`Documentation` for       |
|            | details.                                                                                 |
+------------+------------------------------------------------------------------------------------------+
| 28         | The __init__ function signature. The method takes only 3 arguments: self, xmlfile, and   |
|            | keyval, and no others. This is so that any BDP can be initialized with empty parentheses |
|            | (e.g. a = HelloWorld_BDP()).                                                             |
+------------+------------------------------------------------------------------------------------------+
| 29         | Initialize the base class or any other parent classes.                                   |
+------------+------------------------------------------------------------------------------------------+
| 30-32      | Initialization of attributes. Any attributes that need to be saved when the BDP is       |
|            | written to disk must be initialized here along with default values. The default values   |
|            | must be of the same type of data that the attribute will hold. Attributes can be of any  |
|            | python basic data type (integer, long, float, string, boolean, list, dictionary, set,    |
|            | and tuple) and numpy arrays. To store tables, molecular or atomic data, or images,       |
|            | inherit from :ref:`Table-BDP-Design`, :ref:`Line-BDP-Design`, or :ref:`Image-BDP-Design` |
|            | respectively. The following attribute names are reserved and cannot be used:             |
|            | project, sous, gous, mous, _date, _type, xmlFile _updated, _taskid,                      |
|            | _usedby, uid, and alias. Those that start with an "_" should not be modified by code in  |
|            | a BDP or AT, they are system variables that are set and maintained in the background.    |
|            | The following method names are reserved and cannot be overloaded: getfiles, show,        |
|            | depends_on, report, set, get, setkeys, write, and delete.                                |
+------------+------------------------------------------------------------------------------------------+
| 33         | This method call sets any given key-value pairs passed in via keyval and must be after   |
|            | the parent class initialization and attribute definition.                                |
+------------+------------------------------------------------------------------------------------------+

.. _HelloWorld-AT:

HelloWorld_AT
~~~~~~~~~~~~~

The Admit Task (AT) is the basic unit of processing in Admit. All AT's have the same __init__ signature and
must inherit from the AT base class, or one or more other AT's.

.. literalinclude:: ../examples/HelloWorld_AT.py
   :linenos:
   :language: python

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+------------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                    |
+============+==========================================================================================+
| 1-5        | Initial docstring documentation. See the section on :ref:`Documentation` for details.    |
+------------+------------------------------------------------------------------------------------------+
| 6          | Required import string. Most ATs will inherit only from the base AT class. See the       |
|            | :ref:`Complex-AT` for information on how to inherit from any other AT.                   |
+------------+------------------------------------------------------------------------------------------+
| 7          | Any BDPs that are used (either as inputs or outputs) by the AT should be imported next.  |
+------------+------------------------------------------------------------------------------------------+
| 9          | The AT class name with inheritance. As with the BDPs, the AT class name must match the   |
|            | name of the file it is defined in (minus the .py extension, in this case                 |
|            | HelloWorld_AT.py.                                                                        |
+------------+------------------------------------------------------------------------------------------+
| 10-20      | Notes and documentation for the class. See the section on :ref:`Documentation` for       |
|            | details.                                                                                 |
+------------+------------------------------------------------------------------------------------------+
| 21         | The __init__ function signature. The method takes only 2 arguments: self and keyval      |
|            | and no others. This is so that any AT can be initialized with empty parentheses          |
|            | (e.g. a = HelloWorld_AT()).                                                              |
+------------+------------------------------------------------------------------------------------------+
| 23-24      | Define all keywords and assign default values. Unlike BDPs the AT keywords are kept in a |
|            | single dictionary where the key is the keyword for the dictionary entry. As with BDPs    |
|            | every keyword and attribute must have a default value of the same type as the data are   |
|            | expected to hold. Any data stored in the keyword dictionary or defined in the __init__   |
|            | method will be saved to disk. Attributes can be of any                                   |
|            | python basic data type (integer, long, float, string, boolean, list, dictionary, set,    |
|            | and tuple) and numpy arrays. The following attribute names are reserved and cannot be    |
|            | used:                                                                                    |
|            | _stale, _enabled, _do_polt, _plot_mode, _type, _bdp_out, _bdp_out_map, _bdp_in,          |
|            | _bdp_in_map, _valid_bdp_in, _valid_bdp_out, _taskid, _version, and _needToSave. Reserved |
|            | method names are: markUpToDate, markChanged, uptodate, isstale, show, check, setkey,     |
|            | getkey, haskey, checktype, addoutput, addinput, clearinputs, clearoutputs, getVersion,   |
|            | getdtd, write, save, execute, checkfiles, copy, and validateinput.                       |
+------------+------------------------------------------------------------------------------------------+
| 25         | Initialize the parent class, passing both the dictionary of keywords and values and the  |
|            | input keyval argument.                                                                   |
+------------+------------------------------------------------------------------------------------------+
| 26         | Set some of the static attributes, in this case the version.                             |
+------------+------------------------------------------------------------------------------------------+
| 27         | Set the :ref:`_valid_bdp_in <bdp-in>`, and/or :ref:`_valid_bdp_out <bdp-out>`. See the   |
|            | following sections for a description of how to use :ref:`_valid_bdp_in <bdp-in>` and     |
|            | :ref:`_valid_bdp_out <bdp-out>`.                                                         |
+------------+------------------------------------------------------------------------------------------+
| 29         | Define the run method, which takes no arguments except self. Every AT should implement   |
|            | the run method as this is the method that does all of the work of the AT.                |
+------------+------------------------------------------------------------------------------------------+
| 32         | Clear the output BDP array. If this call is not made then any produced BDPs will be      |
|            | added to the existing list, until slots run out.                                         |
+------------+------------------------------------------------------------------------------------------+
| 35         | Initialize the HelloWorld BDP which is the output of this AT.                            |
+------------+------------------------------------------------------------------------------------------+
| 36-38      | Set some of the BDP values based on attributes in the AT. THe use of getkey is the only  |
|            | supported method of getting the value of an AT keyword. Similarly setkey is the only     |
|            | supported method of changing the value of a keyword.                                     |
+------------+------------------------------------------------------------------------------------------+
| 43         | Add the BDP to the AT output list. Any BDPs that are the products of the AT must be      |
|            | added to the AT with this call.                                                          |
+------------+------------------------------------------------------------------------------------------+

Adding New BDPs and ATs to ADMIT
================================

New BDP files need to be placed in admit/bdp and new AT files need to be placed in admit/at. Once they are
in place run the dtdGenerator. Also if
the attributes of any BDP or AT are changed the :ref:`dtdGenerator<dtdGenerator-sec>` should be run. Now go ahead and start using
your new BDP/AT in ADMIT.

Writing Unit and Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each AT there should be two test programs written: a unit test and an integration test. Below are
examples for the HelloWorld_AT.

Unit Test
^^^^^^^^^

The purpose of the unit test is to test the functionality of the AT itself and need not
have much dependence on outside systems. The test should test as much of the AT code as possible.
There is also not a specific formula for the unit tests.
Here is the unit test for the HelloWorld AT:

.. literalinclude:: ../../admit/at/test/test_helloworld.py
   :linenos:
   :lines: 1-23,32-55,62-97
   :language: python

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-23       | Documentation and description of the module.                                            |
+------------+-----------------------------------------------------------------------------------------+
| 24-27      | Import the needed classes and modules.                                                  |
+------------+-----------------------------------------------------------------------------------------+
| 29         | Define the run function. It can take arguments but does not have to.                    |
+------------+-----------------------------------------------------------------------------------------+
| 31         | Instantiate the Admit main class.                                                       |
+------------+-----------------------------------------------------------------------------------------+
| 34         | Instantiate the AT being tested, HelloWorld_AT in this case.                            |
+------------+-----------------------------------------------------------------------------------------+
| 36         | Add the task to Admit. In many instances input BDPs will need to be added, but since    |
|            | HelloWorld_AT has no input BDPs, it is not done in this instance.                       |
+------------+-----------------------------------------------------------------------------------------+
| 38-39      | Set some of the keys for the AT.                                                        |
+------------+-----------------------------------------------------------------------------------------+
| 42         | Run the Admit tree.                                                                     |
+------------+-----------------------------------------------------------------------------------------+
| 45         | Write it out to disk.                                                                   |
+------------+-----------------------------------------------------------------------------------------+
| 47         | Instantiate another Admit class, it will automatically see and read the files that were |
|            | just written.                                                                           |
+------------+-----------------------------------------------------------------------------------------+
| 51-66      | Printing information to the screen for comparison.                                      |
+------------+-----------------------------------------------------------------------------------------+
| 68-75      | Compare elements and report the results: PASS or FAIL.                                  |
+------------+-----------------------------------------------------------------------------------------+
| 77-83      | Code to automatically execute the run method if this script is executed on the command  |
|            | line.                                                                                   |
+------------+-----------------------------------------------------------------------------------------+



Integration Test
^^^^^^^^^^^^^^^^

The purpose of the integration test is to test the AT inside of the ADMIT system. The integration test
has a more stringent style than the unit test. Here is the integration test for HelloWorld AT:

.. literalinclude:: ../../admit/at/test/runtest_helloworld.py
   :linenos:
   :language: python

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-20       | Documentation on the test and description of the module.                                |
+------------+-----------------------------------------------------------------------------------------+
| 21-23      | Import the needed classes and modules.                                                  |
+------------+-----------------------------------------------------------------------------------------+
| 24         | Required import of the unittest module.                                                 |
+------------+-----------------------------------------------------------------------------------------+
| 26         | Class definition and required inheritance from unittest.TestCase.                       |
+------------+-----------------------------------------------------------------------------------------+
| 28-31      | The required setup method. The purpose of this method is to prepare the environment     |
|            | for the test. In this case it just calls another method to clean up any files that may  |
|            | have been left over from a previous run.                                                |
+------------+-----------------------------------------------------------------------------------------+
| 33-32      | teardown() is another required method, called when the test is done to do any cleanup.  |
+------------+-----------------------------------------------------------------------------------------+
| 36-42      | The cleanup method called by the above setup and teardown methods.                      |
+------------+-----------------------------------------------------------------------------------------+
| 46         | The required runTest method. This method does all of the work of the test.              |
+------------+-----------------------------------------------------------------------------------------+
| 49         | Instantiate an Admit object.                                                            |
+------------+-----------------------------------------------------------------------------------------+
| 52         | Instantiate the AT being tested.                                                        |
+------------+-----------------------------------------------------------------------------------------+
| 54         | Add the AT to the Admit class.                                                          |
+------------+-----------------------------------------------------------------------------------------+
| 57         | Verify that all requirements (input BDP) are met before running.                        |
+------------+-----------------------------------------------------------------------------------------+
| 60         | Run Admit and write out the results.                                                    |
+------------+-----------------------------------------------------------------------------------------+
| 62         | Instantiate another Admit object, this one will detect the files from the previous run  |
|            | and load them.                                                                          |
+------------+-----------------------------------------------------------------------------------------+
| 53-72      | Do some tests by asserting results.                                                     |
+------------+-----------------------------------------------------------------------------------------+
| 74-80      | Print some information out to the screen for comparison.                                |
+------------+-----------------------------------------------------------------------------------------+
| 89         | Set up the test to run.                                                                 |
+------------+-----------------------------------------------------------------------------------------+
| 90         | Run the test.                                                                           |
+------------+-----------------------------------------------------------------------------------------+


Some Inner Workings You Should Know
===================================

.. _BDP-Types:

The bdp_types.py File
~~~~~~~~~~~~~~~~~~~~~

Since Python does not directly support enumerated types the ADMIT system has chosen to use static strings
in order to facilitate comparisons of BDP and AT types and other internal data management. These strings
are defined in the admit/util/bdp_types.py file. Any additions to this file should not be made directly
but via the :ref:`dtdGenerator<dtdGenerator-sec>` as it generates the contents of the bdp_types file based
on an internal list and detected AT and BDP files.

.. _dtdGenerator-sec:

The dtdGenerator
~~~~~~~~~~~~~~~~

The ADMIT I/O system relies on Document Type Definition (dtd) files to verify the data as it is written
and read from disk. These dtd files are automatically generated by introspection of the BDP and AT classes.
The dtdGenerator module does this functionality. To run the generator just type

.. code-block:: python

   import admit.xmlio.dtdGenerator as dtd
   dtd.generate()

That's it. Any time a new AT or BDP is added to the system or any attributes or keys are added, removed,
or change type, the dtdGenerator must be run.

The dtdGenerator also creates the __init__.py files in both the at and bdp directories, to facilitate
imports, and the bdp_types.py file in admit/util.

.. _bdp-in:

The valid_bdp_in Attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~

In order for the ADMIT system to know what BDPs an AT will take as input, each AT will specify the numbers
and types of BDPs it expects in the _valid_bdp_in attribute. The _valid_bdp_in attribute is a list of tuples,
where each tuple specifies one type of input. The tuple consists of 3 parts: BDP type, number, and whther
they are required or optional. Lets take the following examples:
::

    (Moment_BDP,1,bt.REQUIRED)

    (LineList_BDP,0,bt.OPTIONAL)


The first example states that 1 Moment_BDP (or any BDP that inherits from Moment_BDP) is required as input, the
second states the zero or more LineList_BDPs (or any BDP that inherits from LineList_BDP)
are optional inputs. To combine them together one would write:
::

    self.set_bdp_in([(Moment_BDP,  1, bt.REQUIRED),
                     (LineList_BDP,0, bt.OPTIONAL)])

Order is important when specifying the _valid_bdp_in, the Flow Manager will fill in the inputs based on what order
they appear, and optional BDPs must come after all required BDPs. If one wants to specify that one or more of a BDP
type can be an input it can be written as:
::

    self.set_bdp_in([(Moment_BDP, 1, bt.REQUIRED),
                     (Moment_BDP, 0, bt.OPTIONAL)])

Note: may need more work.

.. _bdp-out:

The valid_bdp_out Attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to the _valid_bdp_in attribute, the _valid_bdp_out attribute is used to tell the Flow Manager what type(s)
of BDPs to be produced by each AT. The _valid_bdp_out is a list of tuples, where each tuple contains the type of
BDP and the number to expect. For example:
::

    (Moment_BDP,2)

    (SpwCube_BDP,0)

The first example states that 2 Moment_BDPs will be the output, and the second states that zero or more SpwCube_BDPs
will be output. As with the _valid_bdp_in these can be combined:
::

    self.set_bdp_out([(Moment_BDP, 2),
                      (SpwCube_BDP,0)])

Order is important, so in this example the first two BDPs in the output BDPs will be of type Moment_BDP and any
others will be of type SpwCube_BDP.

Files to be checked (in) when adding an AT and/or BDP
=======================================================

Summarizing, when you add (or even modify) a new AT and/or BDP, there are quite a few
files (some generated after running dtdGenerator) that may need to be
checked into the system. Taking the example of HelloWorld you could
have the following (up to 15) files:

.. see admit_050.txt, although there we concluded there were 11 files

+--------------------------------------------------+------------------+
| File                                             |  Notes           |
+==================================================+==================+
| admit/at/HelloWorld_AT.py                        | authored         |
+--------------------------------------------------+------------------+
| admit/at/__init__.py                             | dtdGenerator     |
+--------------------------------------------------+------------------+
| admit/bdp/HelloWorld_BDP.py                      | authored         |
+--------------------------------------------------+------------------+
| admit/bdp/__init__.py                            | dtdGenerator     |
+--------------------------------------------------+------------------+
| admit/util/bdp_types.py                          | dtdGenerator     |
+--------------------------------------------------+------------------+
| admit/xmlio/dtd/admit.dtd                        | dtdGenerator     |
+--------------------------------------------------+------------------+
| admit/xmlio/dtd/HelloWorld_AT.dtd                | dtdGenerator     |
+--------------------------------------------------+------------------+
| admit/xmlio/dtd/HelloWorld_BDP.dtd               | dtdGenerator     |
+--------------------------------------------------+------------------+
| doc/sphinx/module/admit.at/HelloWorld_AT.rst     | authored         |
+--------------------------------------------------+------------------+
| doc/sphinx/module/admit.bdp/HelloWorld_BDP.rst   | authored         |
+--------------------------------------------------+------------------+
| admit/at/test/test_helloworld.py                 | authored         |
+--------------------------------------------------+------------------+
| admit/at/test/integrationtest_helloworld.py      | authored         | 
+--------------------------------------------------+------------------+
| admit/Summary.py                                 | authored         | 
+--------------------------------------------------+------------------+
| doc/sphinx/design.rst                            | new section      |
+--------------------------------------------------+------------------+
| doc/sphinx/examples.rst                          | new section      |
+--------------------------------------------------+------------------+

The last two entries, a section in the design document, and relevant
descriptions in the examples document, are optional, but recommended of course.
The additional code in Summary.py depends on any Summary items that needs
to be written to the ADMIT database.


Using Tables, Images, Lines and Sources
=======================================

This section shows you how to use the Table, Image, and Line BDPs and their underlying classes.

.. _Table-example:

Table BDP
~~~~~~~~~

The Table_BDP (:ref:`design<Table-BDP-Design>`, :ref:`api<Table-bdp-api>`) is essentially a BDP wrapper
for the Table (:ref:`design<Table-base-Design>`, :ref:`api<Table-api>`) class. The Table_BDP class has a single non-inherited attribute: table, which is an instance of the Table class. The Table class has the following attributes:

+------------------+------------------------------------------------------------------------------------+
| columns          | A List containing the names of the columns, columns can be retrieved by name or by |
|                  | column number (0 based index).                                                     |
+------------------+------------------------------------------------------------------------------------+
| units            | A List containing the units for the columns.                                       |
+------------------+------------------------------------------------------------------------------------+
| planes           | A List containing the names for each plane (3D only) in the table.                 |
+------------------+------------------------------------------------------------------------------------+
| description      | A string for a description or caption of the table.                                |
+------------------+------------------------------------------------------------------------------------+
| data             | A NumPy array of the actual data, can contain a mix of types.                      |
+------------------+------------------------------------------------------------------------------------+

Any of the attributes can be set via the constructor or via the setkey command. Below is an example of
constructing a Table_BDP.

.. code-block:: python
   :linenos:

   from admit.bdp.Table_BDP import Table_BDP

   cols = ["Number","Square"]
   units = [None,None]
   dat = np.array([[1,1],[2,4],[3,9]])
   desc = "Numbers and their square"
   tbl = Table_BDP()
   tbl.table.setkey("columns",cols)
   tbl.table.setkey("units",units)
   tbl.table.setkey("data",dat)
   tbl.table.setkey("description",desc)

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1          | Import the needed class.                                                                |
+------------+-----------------------------------------------------------------------------------------+
| 3          | Create the column labels.                                                               |
+------------+-----------------------------------------------------------------------------------------+
| 4          | Create the units, in this case there are none, but we set them for completeness.        |
+------------+-----------------------------------------------------------------------------------------+
| 5          | Create the numpy array for the data, in many cases this may come from one or more       |
|            | external tasks.                                                                         |
+------------+-----------------------------------------------------------------------------------------+
| 6          | Create the description of the table.                                                    |
+------------+-----------------------------------------------------------------------------------------+
| 7          | Instantiate a Table_BDP.                                                                |
+------------+-----------------------------------------------------------------------------------------+
| 8-11       | Set the individual data members for the table.                                          |
+------------+-----------------------------------------------------------------------------------------+

In this simple Table example the data members were created and then set individually in the Table_BDP
class. There is no checking for the number of columns to match either the length of the column or units
lists as they can be set in any order and will not match until they are all set. Below is a more complex
example where the data columns are of different data types.

.. code-block:: python
   :linenos:

   from admit.bdp.Table_BDP import Table_BDP
   from admit.util.Table import Table

   cols = ["Atom","# electrons"]
   desc = "Listing of the atoms and number of electrons."
   atoms = np.array(["Hydrogen", "Helium", "Oxygen", "Nitrogen"])
   electrons = np.array([1,2,8,7])
   edata = np.column_stack((atoms.astype("object"),electrons))
   table = Table(columns = cols, description = desc, data = edata)
   tbdp = Table_BDP(table = table)

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-2        | Import the needed classes.                                                              |
+------------+-----------------------------------------------------------------------------------------+
| 4          | Create the column labels                                                                |
+------------+-----------------------------------------------------------------------------------------+
| 5          | Create the description of the table                                                     |
+------------+-----------------------------------------------------------------------------------------+
| 6-7        | Create columns of data, these may come from external tasks.                             |
+------------+-----------------------------------------------------------------------------------------+
| 8          | Stack the columns together to create a single 2D array. Note that the first column      |
|            | (atoms) has the addition of .astype("object"). This is necessary if you are creating    |
|            | a table with different data types (strings and ints in this case), as it will preserve  |
|            | the data type in the array. Otherwise all columns will be converted to the lowest       |
|            | possible type (strings in this case).                                                   |
+------------+-----------------------------------------------------------------------------------------+
| 9          | Create a Table with the given parameters.                                               |
+------------+-----------------------------------------------------------------------------------------+
| 10         | Create a Table_BDP with the given table as its contents.                                |
+------------+-----------------------------------------------------------------------------------------+


.. _Image-example:

Image BDP
~~~~~~~~~

The Image_BDP (:ref:`design<Image-BDP-Design>`, :ref:`api<Image-bdp-api>`) is essentially a BDP wrapper
for the Image (:ref:`design<Image-base-Design>`, :ref:`api<Image-api>`) class. The Image_BDP class has a single non-inherited attribute: image, which is an instance of the Image class. The Image class has the following attributes:

+------------------+-----------------------------------------------------------------------------------+
| images           | A Dictionary containing the names of the image files as values and image formats  |
|                  | as keys.                                                                          |
+------------------+-----------------------------------------------------------------------------------+
| thumbnail        | A string for the thumbnail image file name.                                       |
+------------------+-----------------------------------------------------------------------------------+
| thumbnailtype    | A string for the format of the thumbnail image.                                   |
+------------------+-----------------------------------------------------------------------------------+
| auxiliary        | A string for the auxiliary file name.                                             |
+------------------+-----------------------------------------------------------------------------------+
| auxtype          | A string for the format of the auxiliary file.                                    |
+------------------+-----------------------------------------------------------------------------------+
| description      | A string for a caption or description of the image.                               |
+------------------+-----------------------------------------------------------------------------------+

Any of the attributes can be set via the constructor or with the setkey command. Below is an example of
constructing an Image_BDP.

.. code-block:: python
   :linenos:

   import admit.util.bdp_types as bt
   from admit.bdp.Image_BDP import Image_BDP

   image = {"bt.CASA": "moment.im",
            "bt.PNG" : "moment.png"}
   thumb = "moment.thumb.png"
   thumbform = bt.PNG
   desc = "A 1st moment map of the source"
   im = Image_BDP()
   im.image.setkey("images", image)
   im.image.setkey("thumbnail", thumb)
   im.image.setkey("thumbnailtype", thumbform)
   im.image.setkey("description", desc)

   im2 = Image_BDP(images = image, thumbnail = thumb, thumbnailtype = thumbform, description = desc)

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-2        | Class and utility imports.                                                              |
+------------+-----------------------------------------------------------------------------------------+
| 4-5        | Create the image dictionary with format : file name. In this instance two images are    |
|            | included, one CASA format and one PNG format. Both images must show the same picture,   |
|            | however no internal check is made.                                                      |
+------------+-----------------------------------------------------------------------------------------+
| 6          | Create the thumbnail entry, a PNG image in this instance.                               |
+------------+-----------------------------------------------------------------------------------------+
| 7          | Create the thumbnail format entry, bt.PNG is hard coded to "PNG" and makes catching     |
|            | errors easier.                                                                          |
+------------+-----------------------------------------------------------------------------------------+
| 8          | Create the description of the image.                                                    |
+------------+-----------------------------------------------------------------------------------------+
| 9          | Instantiate the Image_BDP class.                                                        |
+------------+-----------------------------------------------------------------------------------------+
| 10-13      | Set the different attributes of the class.                                              |
+------------+-----------------------------------------------------------------------------------------+
| 15         | Identical to lines 9-13, but all in one line.                                           |
+------------+-----------------------------------------------------------------------------------------+

There is a lightweight convenience class in ADMIT for transporting (adding or retrieving) an single image to/from
the Image_BDP class. This class is called imagedescriptor and has the following three attributes.

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+-----------------------------------------------------------------------------------------+
| file       | A string for the image file name.                                                       |
+------------+-----------------------------------------------------------------------------------------+
| format     | The format of the image (e.g. bt.PNG, bt.JPG).                                          |
+------------+-----------------------------------------------------------------------------------------+
| type       | The type of the image: bt.AUX (for auxiliary file), bt.THUMB (for thumbnail image), or  |
|            | bt.DATA (for the main image). Default is bt.DATA.                                       |
+------------+-----------------------------------------------------------------------------------------+

To add an image to the above example:

.. code-block:: python
   :linenos:

   import admit.util.Image as Image

   im3 = Image.imagedescriptor(file = "moment.jpg", format = bt.JPG, type = bt.DATA)

   im.image.addimage(im3)

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1          | Import the needed module.                                                               |
+------------+-----------------------------------------------------------------------------------------+
| 3          | Create an imagedescriptor with a file moment.jpg, a JPG format, and set it for the main |
|            | image.                                                                                  |
+------------+-----------------------------------------------------------------------------------------+
| 5          | Add the new image to the previous class. The class now contains 3 images with 3         |
|            | different formats. If an image of the given format already exists then the existing     |
|            | entry is overwritten.                                                                   |
+------------+-----------------------------------------------------------------------------------------+

There are several ways to get a specific image from the Image_BDP, either by retrieving an imagedescriptor
or by jet getting the file name.

.. code-block:: python
   :linenos:

   id1 = im.getimage(bt.THUMB)
   id2 = im.getimage(bt.PNG)

   imfile = im.getimagefile(bt.PNG)

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1          | Get an imagedescriptor of the thumbnail image.                                          |
+------------+-----------------------------------------------------------------------------------------+
| 2          | Get an imagedescriptor of the PNG format of the image.                                  |
+------------+-----------------------------------------------------------------------------------------+
| 4          | Get just the file name of the PNG formatted image.                                      |
+------------+-----------------------------------------------------------------------------------------+

.. _Line-example:

Line BDP
~~~~~~~~

The Line_BDP (:ref:`design<Line-BDP-Design>`, :ref:`api<Line-bdp-api>`) is essentially a BDP wrapper
for the Line (:ref:`design<Line-base-Design>`, :ref:`api<Line-api>`) class. The Line_BDP class has a single non-inherited attribute: line, which is an instance of the Line class. The Line class has the following attributes:

+------------------+-----------------------------------------------------------------------------------+
| name             | String for the name of the molecule or atom.                                      |
+------------------+-----------------------------------------------------------------------------------+
| formula          | The chemical formula of the molecule/atom.                                        |
+------------------+-----------------------------------------------------------------------------------+
| transition       | String for the transition/quantum number information.                             |
+------------------+-----------------------------------------------------------------------------------+
| energies         | A List of length 2, to hold the lower and upper state energies of the transition. |
+------------------+-----------------------------------------------------------------------------------+
| energyunits      | String for the units of thetransition energies (e.g. K, cm\ :sup:`-1`\ ).         |
+------------------+-----------------------------------------------------------------------------------+
| linestrength     | Float for the intensity/line strength of the transition.                          |
+------------------+-----------------------------------------------------------------------------------+
| lsunits          | String for the units of the line strength (e.g. Debye\ :sup:`2`\ ).               |
+------------------+-----------------------------------------------------------------------------------+
| frequency        | Float for the frequency of the transition.                                        |
+------------------+-----------------------------------------------------------------------------------+
| funits           | String for the units of the frequency (e.g. MHz, GHz)                             |
+------------------+-----------------------------------------------------------------------------------+
| blend            | Integer denoting the index of a blend (0 means no blend)                          |
+------------------+-----------------------------------------------------------------------------------+

Any of the attributes can be set via the constructor or with the setkey command. Below is an example of
constructing an Line_BDP.

.. code-block:: python
   :linenos:

   from admit.bdp.Line_BDP import Line_BDP
   from admit.util.Line import Line

   name = "Carbon monoxide"
   form = "CO"
   trans = "1-0"
   energies = [0.0,5.53]
   energyun = "K"
   linestr = 0.012
   lsunits = "Debye^2"
   freq = 115.27120
   funits = "GHz"

   line = Line(name = name, formula = form, transition = trans, energies = energies,
               energyunits = energyun, linestrength = linestr, lsunits = lsunits,
               frequency = freq, funits = funits)

   lbdp = Line_BDP(line = line)

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-2        | Import the needed classes.                                                              |
+------------+-----------------------------------------------------------------------------------------+
| 4-12       | Set variables to hold the different line parameters.                                    |
+------------+-----------------------------------------------------------------------------------------+
| 14-16      | Instantiate the Line class with the values.                                             |
+------------+-----------------------------------------------------------------------------------------+
| 18         | Instantiate the Line_BDP and setting the line attribute.                                |
+------------+-----------------------------------------------------------------------------------------+

.. _SourceList-example:

SourceList BDP
~~~~~~~~~~~~~~

The SourceList_BDP (:ref:`api<SourceList-bdp-api>`) contains a table describing
the following source attributes:


+------------------+-----------------------------------------------------------------------------------+
| name             | Name/Label of the source                                                          |
+------------------+-----------------------------------------------------------------------------------+
| ra               | String representing the RA (in CASA hms notation)                                 |
+------------------+-----------------------------------------------------------------------------------+
| dec              | String representing the DEC (in CASA dms notation)                                |
+------------------+-----------------------------------------------------------------------------------+
| flux             | Float for the total flux, in Jy.                                                  |
+------------------+-----------------------------------------------------------------------------------+
| peak             | Float for the peak flux, in Jy/beam                                               |
+------------------+-----------------------------------------------------------------------------------+
| major            | Major axis of the fitted gaussian. This includes the beam                         |
+------------------+-----------------------------------------------------------------------------------+
| minor            | Minor axis of the fitted gaussian. This includes the beam                         |
+------------------+-----------------------------------------------------------------------------------+
| pa               | Position angle of the beam, east from north, in degrees                           |
+------------------+-----------------------------------------------------------------------------------+

Any of the attributes can be set via the constructor or with the setkey
command.

.. _Complex-example:

More Complex Examples
=====================

This section presents more complex examples of BDPs and ATs, including how to inherit from other BDP types.

.. _Complex-BDP:

Complex BDP
~~~~~~~~~~~

.. literalinclude:: ../examples/HelloWorld_Inherit_BDP.py
   :linenos:
   :language: python

.. tabularcolumns:: |p{1cm}|p{14.5cm}|

+------------+-----------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                   |
+============+=========================================================================================+
| 1-5        | Initial docstring documentation. See the section on :ref:`Documentation` for details.   |
+------------+-----------------------------------------------------------------------------------------+
| 6-7        | Import the parent classes, in this case Image_BDP and Line_BDP.                         |
+------------+-----------------------------------------------------------------------------------------+
| 9          | The class name with inheritance from two classes.                                       |
+------------+-----------------------------------------------------------------------------------------+
| 10-28      | Class documentation, giving all parameters and attributes.                              |
+------------+-----------------------------------------------------------------------------------------+
| 29         | Class initialization definition, including the inheritance from Image_BDP and           |
|            | Table_BDP.                                                                              |
+------------+-----------------------------------------------------------------------------------------+
| 30-31      | Initialize the parent classes, passing only the xmlFile.                                |
+------------+-----------------------------------------------------------------------------------------+
| 32-34      | Initialize the attributes for the class.                                                |
+------------+-----------------------------------------------------------------------------------------+
| 35         | This method call sets any attributes to the given values in keyval.                     |
+------------+-----------------------------------------------------------------------------------------+

The HelloWorld_Inherit_BDP can be treated just like any other BDP, and has the additional attributes
of image and line, which were inherited from the Image_BDP and Table_BDP parent classes.

.. _Complex-AT:

Complex AT
~~~~~~~~~~

This section is incomplete at this time.


Image cube manipulation sample template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have provided more complete :ref:`template AT<Template-AT-api>` which you can use
to develop your own cube analysis routines.   Template_AT includes the basic steps of
reading in an image cube, writing out Table and Image BDPs, and writing information about the task to the
:ref:`Summary <Summary-api>`.

Line Detection With ADMIT
=========================

The primary AT used for line detetion and identification is the LineID_AT. The AT does not rely on a
single method of detecting a line, but has several methods available to the user. Additional line
detection modules can be added provided they adhere to the following standards:

* The method must be defined as a class with the code stored in admit/util/linfinder

* The __init__ method must take \*\*keyval as its only argument (aside from self). The method then needs
  to process any inputs given, ignoring any it does not need. The input spectrum (1D, list of intensities)
  will always be given as spec= in the input dictionary.

* The class must specify a set_options method that takes \*\*keyval as its only argument (aside from self).
  The method must process any inpuy keywords it gets and ignore any that are not needed.

* The class must specify a find method that takes \*\*keyval as its only argument (aside from self).
  The method must process any inpuy keywords it gets and ignore any that are not needed.

See the admit/util/linefinder/AdmitLineFinder.py for an example.

.. _Basic Data Products: module/admit.bdp/BDP.html
.. _ADMIT Tasks:        module/admit/AT.html
