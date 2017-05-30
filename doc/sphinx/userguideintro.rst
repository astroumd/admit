Overview of ADMIT
=================

The ALMA Data-Mining Toolkit (ADMIT) is an execution environment and set of
tools for analyzing image data cubes. ADMIT is based on python and designed
to be fully compliant with CASA_ and to utilize CASA_ routines where possible.
ADMIT has a flow-oriented approach, executing a series of ADMIT Tasks (ATs)
in a sequence to produce a sequence of outputs. For the beginner, ADMIT can
be driven by simple scripts that can be run at the Unix level or from inside
of CASA_. ADMIT provides a simple browser interface for looking at the data
products, and all major data products are on disk as CASA_ images and graphics
files. For the advanced user, ADMIT is a python environment for data analysis
and for creating new tools for analyzing data.

The primary operations supported by ADMIT 
are focused on analysis of images commonly produced by ALMA and similar radio 
telescopes. ADMIT has three primary functionalities: 

#. An automatic pipeline flow which produces a fixed set of science `data products`_ which are ingested into the ALMA Archive and available to the requester from the ALMA Archive. These ADMIT products are created from the ALMA image cubes after they are accepted as valid by the observatory. ADMIT products are not currently available from the ALMA Archive -- they should become available later in 2016.

#. A desktop environment where the astronomer can quickly create flows to produce and inspect ADMIT `data products`_ via a web or graphic file browser and access information in the form of XML table, PNG files, and FITS files.  Because ADMIT is a Python environment, the user can choose to examine the data using the Python capabilities.  

#. A capability for astronomers to rerun pipeline flows with hand-tuned parameters and to modify flows based on existing ADMIT Tasks. Additionally, the advanced user may create new ADMIT tasks to suit the needs of their scientific goals.

Typically an astronomer will interact with ADMIT in one of two ways:

* By retrieving the ADMIT products from the ALMA Archive. These products will be in a gzipped tar file of size a few to a few tens of megabytes. Once untar'ed on the disk, these products can be viewed with a browser utilizing the index.html file provided or inspected directly with Unix or xml tools. Archive products available later in 2016.

* By creating a local ADMIT flow to do the user requested analysis, inspect the results, and then modify and improve the flow parameters to achieve the desired final data products.

*ADMIT does not interact with u,v data or create images from u,v data*; 
CASA_ should be used to create images. ADMIT provides a number of ways to inspect
your image cubes. The astronomer can then decide whether the ALMA image
cubes need to be improved, which requires running standard CASA_ routines
to re-image the u,v data. If new images are made, the ADMIT
flow can be run on these new image cubes to produce new set
of ADMIT products. 

ADMIT requires that you have the image cubes local to the execution
machine to create new data products. You do not need to have the image
cubes local to view pre-existing ADMIT products. The tarball from the
ALMA archive will contain ADMIT products without the image cubes. If
you wish to modify parameters and make new ADMIT products, you need to
download the appropriate data cubes from the ALMA archive and then
re-run the ADMIT flow.


A Short Summary of the Technical Side of ADMIT
==============================================

ADMIT is Python-based software which utilizes CASA_ routines where possible
and reads CASA_ image format or FITS.  ADMIT is an add-on package to CASA_
and designed to be compatable with the CASA_ Python environment. Currently,
compatability with CASA_ forces incompatability with some commonly used
Python packages (e.g., APLpy, astropy). CASA_ must be installed on your
computer and instantiated in your working shell in order to use ADMIT. ADMIT
software must be installed on your system (see `Install Guide`_).

The basic components of ADMIT are:

*   `ADMIT Task`_ (AT): An ADMIT task is a Python script that accomplishes a specfic job. Each task has a specific set of keywords and a set of outputs. Most tasks follow a load-and-execute model so that they can be run automatically based on set inputs.

*  `Basic Data Product`_ (BDP): A Basic Data Product is an output from an AT and often the input to another AT. The content of the BDP is defined by the AT that produces it. It can consist of XML, PNG images, and image data in CASA_ or FITS format. BDPs are written to disk.

*  Flow_:  `ADMIT Tasks`_ are generally run sequentially to create a set of BDPs. Tasks are created and added to the Flow_, and once the flow is set up, the user runs the flow which runs each task in turn. Tasks are connected to each other via BDPs -- the output BDP of an AT is used as the input BDP to another AT downstream.  ADMIT has a `Flow Manager`_ which maintains information about the sequence of ATs and the input and output BDPs. The `Flow Manager`_ allows the astronomer to re-run any sequence and only execute tasks whose input parameters have changed.  Furthermore, if an input BDP or keyword value for one AT in a flow is altered, the `Flow Manager`_ knows to execute not only that AT, but any ATs further along in the flow that depend on the output of altered AT.

ADMIT operates on individual ALMA data cubes. The output BDPs are written to
a directory named *input-cube-name.admit*, where the originating FITS file
would be *input-cube-name.fits*. (As ALMA FITS file names can be rather
long, the the user has the option to give an alias for the basename).
Each data cube is associated with its own *input-cube-name.admit*
directory. Within that directory, the admit.xml file contains metadata
about the BDPs and the summary information that that is used to create the
index.html file for displaying the BDPs in the browser. Each BDP created
by an AT has a xml file (file extension .bdp) in this directory which
contains information about the BDP and pointers to any PNG or image files
associated with the BDP.  Most users will never examine admit.xml or a BDP file directly, rather they will use the web browser interface or Python methods.


ADMIT expects to be in control the contents of its BDPs so users should
not delete files in the *input-cube-name.admit* directory. Furthermore,
if the *input-cube-name.admit* directory is deleted at the Unix level,
all information about the flow and all data products are deleted. 

Getting Started with ADMIT (for Linux users)
============================================

You should have already installed ADMIT on your local machine (see `Install Guide`_).

In the shell that you want to work, there must be a path to CASA_.

.. code-block:: none

      which casa        

on your Unix command line and you should see the path to CASA_. If not,
you need to either install CASA or invoke your local script that
defines your path to CASA_. Similarly, admit should be in your path

.. code-block:: none

        which admit
   or   echo $ADMIT

on your Unix command line and you should see the path to ADMIT.
If you do not, go to the directory where ADMIT was installed and
source the admit start-up script:

.. code-block:: tcsh

       source admit_start.csh

You can type "echo $ADMIT" again and now you should see the path.

Now you are ready. If you have downloaded an ADMIT products tarball from
the ALMA archive and just want to look at the products, you can skip
down to the `ADMIT in Your Web Browser`_ section on viewing data products. 
Right now, since ADMIT products are not yet in the archive, you should 
proceed to the next section to create simple ADMIT data products
from an ALMA image in FITS or CASA_ format.

Getting Started with ADMIT (for OS X users)
============================================

You should have already installed ADMIT on your local machine (see `Install Guide`_).

In the shell that you want to work, there must be a path to CASA_.

.. code-block:: tcsh

      which casa        

on your OS X command line and you should see the path to CASA_. If not,
you need to either install CASA or invoke your local script that
defines your path to CASA_. Similarly, admit should be in your path

.. code-block:: tcsh

          which admit
   or     echo $ADMIT

on your OS X command line and you should see the path to ADMIT.
If you do not, go to the directory where ADMIT was installed and
source the admit start-up script:

.. code-block:: tcsh

      source admit_start.csh

You can type "echo $ADMIT" again and now you should see the path.

There are now two more steps. First, CASA must be able to "see" where ADMIT is. 
The mac executable 'casa' or 'casapy' overwrites the system supplied path. To 
fix this, edit (in your home directory) the ~/.casa/init.py file to reflect both the 
ADMIT path and the ADMIT/bin path. 

.. code-block:: python
        
    import os
    import sys
    

    try:
       admit_path = os.environ['ADMIT']
       sys.path.append(admit_path)
           os.environ["PATH"] += os.pathsep + admit_path + '/bin/'  + os.pathsep + '/usr/local/bin/'
    except KeyError:
           print("ADMIT path not defined. If you wish to use ADMIT, source the admit_start.[c]sh file.")
    

(you can find a template of this script in *$ADMIT/scripts/casa.init.py*)
The second thing that must be done is that calls to the ADMIT-supplied script
'casarun' must be replaced with calls to the CASA-supplied command 'casa-config.' 
As an explicit example, one test that is run to establish the Python-path as seen 
by CASA is performed by running

.. code-block:: tcsh

     make python1 

This command in the Makefile reads 'casarun bin/python-env', and it will hang on OS X.
Instead, this should be edited to read 'casa-config --exec bin/python-env'. 


Now you are ready. If you have downloaded an ADMIT products tarball from
the ALMA archive and just want to look at the products, you can skip
down to the `ADMIT in Your Web Browser`_ section on viewing data products. 
Right now, since ADMIT products are not yet in
the ALMA archive, you should proceed to the next section 
to create simple ADMIT data products from an ALMA image FITS file or CASA image.


Prepared ADMIT Recipes
======================
ADMIT will provide standard recipe scripts for common flows.  These can
be invoked in CASA or at the shell command line.  For example, to
invoke the recipe Line_Moment_ in CASA:

.. code-block:: python

   CASA<1>: import admit
   CASA<2>: admit.recipe("Line_Moment","myimage.fits")

and at the shell command line:

.. code-block:: csh

   admit_recipe Line_Moment myimage.fits

To see the list of available recipes, type *admit_recipe* with no arguments.  There are some advanced
Unix scripts to run ADMIT flows, but these are discussed below. See :ref:`runa1-script`.


Making an ADMIT Data Product
============================

ADMIT Tasks -- which do the work -- can be run directly 
within CASA_ from the command line, or from scripts in either the Unix or
CASA_ environment.
The goal of ADMIT is to produce, reproduce and simplify the production
of data products of scientific interest to you, so ADMIT must internally keep track of
what you are doing. To do this, ADMIT will create a "your-name-choice".admit
directory and store information there. This tracking capability also means
that simple ADMIT usage will involve a couple of administrative steps.

Let's start in the CASA environment. At the CASA prompt, type:

.. code-block:: python

   CASA <1>: import admit
   CASA <2>: p  = admit.Project('your-name-choice.admit',dataserver=True)
   CASA <3>: t0 = p.addtask(admit.Ingest_AT(file='your-image-cube-name.fits', vlsr=10.0))

The admit.Project command initiates the project, opens the directory
with the name that you gave and creates a Python 'Admit object' in memory named
"p". The "p" can be anything that you choose; as it will become the first
piece of every project command you type, a short name is recommended.  The
dataserver=True flag causes ADMIT to start up a webpage for showing the
results; more on that later (in `ADMIT in Your Web Browser`_).  The webpage
will be blank until you actually perform calculations.

The ``addtask()`` method (see `Admit Project`_) puts an ADMIT task into your
flow---in this case, `Ingest_AT`_---and returns a handle to the task (the
task's ID number). The `Ingest_AT`_ brings an image cube
into ADMIT. If it is a FITS file, the image cube will be read into a CASA_
image on disk. If it is a CASA_ image, `Ingest_AT`_ will just create an ADMIT
information file.

.. note::
  Since CASA_ images generally do not have information about
  your source Vlsr, `Ingest_AT`_ is typically a good place to input it
  (in km/sec).

The "t0" (or whatever name you choose) is the ADMIT task number, which
provides a handle to the `Basic Data Product`_ (BDP)---in some cases,
multiple BDPs---produced by the task. BDP outputs from a task are numbered from
zero and referred to with Python tuples such as (*t0*,0), which represents the
*first* BDP output from task *t0*. (Since many tasks produce only one BDP, for
convenience tuples such as (*t0*,0) can be abbreviated simply to *t0*, as
shown in the following example.)

To make a moment map, such as zero, first and second moment maps, from the
image cube, you would then type:

.. code-block:: python

     CASA <4>: t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t0])
     CASA <5>: t2  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t0, t1])

The `CubeStats_AT`_ will produce a series of statistics about its input data
[*t0*]---shorthand for [(*t0*,0)]---which will be output in BDP (*t1*,0), the
first (and only) BDP generated by the task, *t1*. The `Moment_AT`_ produces the
requested moment map(s)---by default, just moment-0---for the image cube
*t0* that you digested. In this case, for the entire cube (all spectral
channels) with a S/N cutoff of 3 times the RMS noise determined by CubeStats
(the *t1* input), and with the higher moment maps (1,2,3...) clipped to be
valid only where the moment zero map is greater than 2 times the RMS. (In this
example, no higher-order moments are produced.)

.. note::
  The moments=[...] argument to `Moment_AT`_ specifies the list of moments
  to produce, each in its own BDP. For example, adding moments=[0,1,2] to
  the preceding call will direct `Moment_AT`_ to produce moment-0, moment-1 and
  moment-2 maps, which can be input to other tasks using the BDP handles
  (*t2*,0), (*t2*,1) and (*t2*,2), respectively.

Up to this point, you have just been creating a flow; the data products have
not actually been calculated yet. You should have seen an "INFO" message as you
entered each of the above lines. To execute your flow and create the BDPs,
type:

.. code-block:: python

      CASA <6>: p.run()

``p.run()`` causes ADMIT to calculate your data products. The data products can
be viewed in your local browser window---there should be one now created by
ADMIT. If not, you can start up the data browser by typing

.. code-block:: python

      CASA <7>: p.startDataServer()

If you already have a data server running, the above command, will inform you:

.. code-block:: none
		
      A data server for this Admit object is already running on localhost:NNNNN

where NNNNN is a port number.  If so, look through the webpages in your
browser to see if it is hiding among your tabs, or copy and paste the
*localhost:NNNNN* to a new tab.  You should now have a browser page
with bars for Ingest, CubeStats and Moment, as well as a flow diagram. Click on
the bars to see the products. In this case, the most interesting one is
probably the moment-0 map, which is the emission in your cube integrated over
frequency. Examining the flow diagram is a good way to visually explore how the
tasks in your flow relate to each other.

Great. Now let's say that you want a spectrum at the highest peak in your
moment map. ADMIT can do that automatically given the `Moment_AT`_ output.
To make the spectrum, you use the `CubeSpectrum_AT`_:

.. code-block:: python

     CASA <8>: t3 = p.addtask(admit.CubeSpectrum_AT(), [t0, t2])
     CASA <9>: p.run()

The p.run() command is needed again---the addtask() puts
the task into the flow and p.run() executes it. Your browser page should
now have a new line at the bottom which is labeled CubeSpectrum. Click
on the bar and you will see your spectrum.

The ADMIT tasks, as they execute, create a python structure in memory
containing all of the task and flow information, and they write out information,
images, and files to the "your-name-choice".admit directory. As long
as you remain in your CASA_ session, you have access to the contents
of the structure---you can add tasks to and re-execute the flow and your browser
page will continue to update accordingly.

.. note::
  To minimize execution time, ADMIT re-runs projects intelligently. Each time
  you add a task and re-run the flow, *only* the task(s) which have not yet
  been run (or are otherwise out-of-date; e.g., due to changing the task
  arguments) are executed. Unchanged tasks are skipped.


Using ADMIT Scripts
===================
ADMIT can also be run from script files using either the Unix
command line or the CASA_ command line. The direct connection
to the browser page and the ability to dynamically add to flows from the
command line is only available from within CASA_ because the
CASA session keeps your python structures in active memory. When a
script is run from the Unix command line, all memory-based products
disappear when the script ends; however, ADMIT writes all of the products to
persistent disk files so you can view your ADMIT products using the browser, as
described in the next section, or modify and re-run the flow using a script
file.

An ADMIT script looks very much like what you would type
on the CASA_ command line. For example, the script below will
create all of the same products in the CASA session of the previous section.

.. code-block:: python

 #!/usr/bin/env casarun
 # set up admit in the casa environment
 import admit
 # define project name
 p = admit.Project('your-name-choice.admit',dataserver=True )
 # Flow tasks.
 t0  = p.addtask(admit.Ingest_AT(file='your-image-cube-name.fits'))
 t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t0])
 t2  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t0, t1])
 t3  = p.addtask(admit.CubeSpectrum_AT(), [t0, (t2,0)])
 p.run()

The script can be run in CASA_ using the "execfile" command, or
from the Unix command line by making the script file executable
(``chmod +x``) and then executing it. The file containing your
script can be named 'anything-you-want.py'.

The 'your-name-choice.admit' directory includes a file, admit0.py, containing a 
transcript (an ADMIT script) of the flow that created 'your-name-choice.admit'.
Comparing this script to the graphical representation of the flow (shown in the
"Flow Diagram" tab at the top of the data browser window) can be instructive
when learning how to create your own ADMIT scripts.

.. warning::
  Flow transcripts are *not* intended to be used directly as script templates
  (although this will work in simple cases). In particular, flows containing
  tasks producing a variable number of BDP outputs, such as `LineCube_AT`_,
  require special care---the transcript includes all literal outputs of such
  *variadic* tasks, whereas user scripts should assume only a single,
  placeholder output is present (see the following section for an example).

Molecular Line Identification
=============================
ADMIT is very useful for finding spectral lines in your data,
identifying the molecular species and transition of the line,
and cutting out a sub-cube which contains only the channels
with line emission. The primary tasks for this purpose are
`LineID_AT`_ and `LineCube_AT`_. `LineID_AT`_ find the
channel intervals with emission above a user-selected 
noise level and then tries to identify the lines in the
Splatalog database. `LineCube_AT`_ cuts out sub-cubes for
each identified line emission region and writes out a
separate CASA_ image file for each.

Information about the Vlsr of your object is not passed down the ALMA
imaging pipeline to your ALMA image cubes. Hence, ADMIT does not
have access to the Vlsr or spectral line information that
you input in your observing set up and correlator setting in the ALMA OT. 
The proper identification of lines is greatly aided by having the
approximately correct Vlsr of your target source. You are allowed to put
this value into ADMIT when you ingest your image cube, and/or when you run
`LineID_AT`_. If you use the Vlsr keyword in `LineID_AT`_ it overrides
the value used in `Ingest_AT`_.

A typical use of `LineID_AT`_ would look like this in a script:

.. code-block:: python

 #!/usr/bin/env casarun
 # set up admit in the casa environment
 import admit
 # Master project.
 p = admit.Project('you-name-choice.admit', Dataserver=True)
 # Flow tasks.
 t0  = p.addtask(admit.Ingest_AT(file='your-image-cube-name.fits'))
 t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t0])
 t2  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t0, t1])
 t3  = p.addtask(admit.CubeSpectrum_AT(), [t0, t2])
 t4  = p.addtask(admit.LineID_AT(csub=[0, 0], minchan=4, maxgap=6, numsigma=5.0), [t1, t3])
 t5 = p.addtask(admit.LineCube_AT(pad=40), [t0, t4])
 t6 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t5, t1])
 t7 = p.addtask(admit.CubeSpectrum_AT(), [t5, (t6,0)])
 p.run()

The `CubeStats_AT`_ is done to get the RMS noise in the cube and to generate two
spectra: one consisting of the maximum flux density in each channel and the
other the minimum. The `CubeSpectrum_AT`_ is run to get the spectrum at the
position of the peak total integrated emission. Both of these BDPs are input
to `LineID_AT`_ to estimate the emission segments and do the line
identification. `LineCube_AT`_ produces one data cube for each segment found.
`Moment_AT`_ and `CubeSpectrum_AT`_ are then repeated for each emission
segment identified. (ADMIT automatically replicates the latter two tasks in the
flow for each `LineCube_AT`_ output it finds---do not do this manually!)

At the present time, some (perhaps many) ALMA total power line cubes have
baselines that are not "average" zero in the non-line channels. There are
infrequently cases where the 7-m or 12-m interferometric maps have incorrect
continuum subtractions but you are best off to correct that by remaking the
maps in CASA_ based on a new continuum subtracted u,v dataset. For the
total power data, the sequence would be similar to the above with the
insertion of two new tasks: `LineSegment_AT`_ and `ContinuumSub_AT`_.
`LineSegment_AT`_ finds the channel segments with emission above your
set noise level; `ContinuumSub_AT`_ does a spatial pixel by spatial pixel
baseline removal in the spectral direction with the emission segments
ignored in determining the baseline fit. The output of `ContinuumSub_AT`_ is
a new image cube with the baseline removed -- and that is then fed forward
to the rest of the script.

.. code-block:: python

 #!/usr/bin/env casarun
 # set up admit in the casa environment
 import admit
 # Master project.
 p = admit.Project('you-name-choice.admit', dataserver=True)
 # Flow tasks.
 t0  = p.addtask(admit.Ingest_AT(file='your-image-cube-name.fits'))
 t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t0])
 t2  = p.addtask(admit.CubeSum_AT(numsigma=5.0, sigma=99.0), [t0, t1])
 t3  = p.addtask(admit.CubeSpectrum_AT(), [t0, t2])
 t4  = p.addtask(admit.LineSegment_AT(csub=[0, 0], minchan=4, maxgap=6, numsigma=5.0), [t1, t3])
 t5 = p.addtask(admit.ContinuumSub_AT(fitorder=1, pad=60),[t0, t4])
 t6 = p.addtask(admit.CubeStats_AT(ppp=True), [t5])
 t7 = p.addtask(admit.CubeSpectrum_AT(), [t5, t6])
 t8 = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t5, t6])
 t9 = p.addtask(admit.LineID_AT(csub=[0, 0], minchan=4, maxgap=6, numsigma=5.0), [t6, t7])
 t10 = p.addtask(admit.LineCube_AT(pad=40), [t5, t9])
 t11 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t10, t6])
 t11 = p.addtask(admit.CubeSpectrum_AT(), [t10, t11])
 p.run()

Interacting with Line ID
========================

The identification of emission/absorption from specific molecular species and transitions is important
to the scientific analysis of ALMA data. The general case of
species/transition identification is a difficult problem due to the possibilities
of complex line shapes and line blending, and the high density of potential matching lines
in the Splatalog database. Add to this the range of physical conditions giving
rise to molecular emission in the Universe (cold cores, hot cores, evolved stars, galaxies
diffuse ISM) and the perfect identification of species/transition is not practical
without significant a priori information, which is not available from the ALMA archive
data at present.

`LineID_AT`_ attempts to identify lines based first on the most commonly observed
species and transitions. CO, CS, HCN, CN, H2CO, and other such common species
are given preference in a first search for indentification. The :ref:`Tier1DB`
contains a list of these molecules along with their transitions. See the following
section for a more detailed description of the database.
After that a deeper
search is done with either the CASA slsearch task or the online splatalogue database. 
There are several keywords in `LineID_AT`_ for controlling
aspects of the search and identification. The following are the keywords that may be of the
most use to the user.

.. tabularcolumns:: |p{2cm}|p{13.5cm}|

+-----------------+------------------------------------------------------------------------------------------+
| Keyword         | Description                                                                              |
+=================+==========================================================================================+
| vlsr            | The vlsr of the source in km/s. The closer this is to the source's average vlsr, the     |
|                 | more accurate the results will be.                                                       |
+-----------------+------------------------------------------------------------------------------------------+
| numsigma        | Minimum intensity, in terms of the rms noise of the individual sepctra, to consider a    |
|                 | given channel to not be noise. Default is 5.0, but lower values may be more appropriate  |
|                 | in the cases of lower overall S/N.                                                       |
+-----------------+------------------------------------------------------------------------------------------+
| minchan         | Minimum number of consecutive channels above numsigma to consider them part of a line.   |
|                 | The default is 4, but smaller or larger values may give better results depending on the  |
|                 | typical width of lines in the spectra.                                                   |
+-----------------+------------------------------------------------------------------------------------------+
| smooth          | Smooth the input spectra with one of the several available soothing algorithms. The      |
|                 | default is to not smooth, but in cases of noisy spectra it is advisable to smooth the    |
|                 | data.                                                                                    |
+-----------------+------------------------------------------------------------------------------------------+
| force           | If there is a transition that you want to mark specifically, use the force keyword to    |
|                 | pass the information to `LineID_AT`_. Any other transitions will be forbidden from the   |
|                 | specified channel region.                                                                |
+-----------------+------------------------------------------------------------------------------------------+
| reject          | If there are specific molecules or transitions that you do not want to be considered for |
|                 | identifications, the reject keyword can be used to pass this to `LineID_AT`_.            |
+-----------------+------------------------------------------------------------------------------------------+
| csub            | `LineID_AT`_ works best when there is no continuum in the input spectra. If the spectra  |
|                 | are not continuum free then the csub keyword can be used to remove the continua from the |
|                 | spectra. By definition the spectra from `CubeStats_AT`_ have a continuum that needs to   |
|                 | be removed. The default ([1, None]) removes this continuum, but leaves all other spectra |
|                 | as they are.                                                                             |
+-----------------+------------------------------------------------------------------------------------------+


The output of `LineID_AT`_ in the browser page includes
a table of emission segments found, and identification for each segment if found.
The LineId Editor mode in the browser (see tabs along the second line from the
top of the ADMIT page for your data prducts). Click on that button and you
initiate the capability to edit the results from `LineID_AT`_. You can: change the
frequency, id, and channel range of an emission region. You can reject an
emission segment; then you can write out your estimate of the best line
identification as a replacement for the original `LineID_AT`_ BDP, 
which can be fed into `LineCube_AT`_ to cut line cubes. You can also use
the force and reject buttons as input advise to a second run of `LineID_AT`_.

The interaction mode with LineID Editor can only be used if your ADMIT
file is created or opened from within your current CASA session. The
editing mode requires that your ADMIT flow be present as an active 
python memory structure. The interactive edits that you make within
LineID Editor are not saved to the flow so, at present, you cannot
automatically recreated your final data products by re-running the
flow from the scratch.

.. _Tier1DB:

Tier 1 Database
~~~~~~~~~~~~~~~

The Tier 1 Database (DB) contains the transitions of molecules
that if present, are expected to be a dominant emission peak in the spectrum. The allowed 
frequency/velocity ranges for these transitions are relaxed compared to those of others. In gneneral
any peak detected within 30 km/s (galactic source) and 200 km/s (extragalactic source) of a Tier 1
rest frequency will be assigned the identification of that transition. Additionally, the identified
peak is traced down to the cutoff level and any additional peaks found along the way are also labeled
the Tier 1 transition. Tier 1 molecules are:

.. tabularcolumns:: |p{1.5cm}|p{6cm}|

+------------+-------------------------------------------------------------------+
| Molecule   | Constraints                                                       |
+============+===================================================================+
| CO         | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| 13CO       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| C17O       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| HCO+       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| HDO        | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| CCH        | 31.0 - 950.0 GHz, HFL                                             |
+------------+-------------------------------------------------------------------+
| CN         | 31.0 - 950.0 GHz, HFL, weakest lines eliminated                   |
+------------+-------------------------------------------------------------------+
| HCN        | 31.0 - 950.0 GHz, HFL                                             |
+------------+-------------------------------------------------------------------+
| HNC        | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| 13CN       | 31.0 - 950.0 GHz, HFL, weakest lines eliminated                   |
+------------+-------------------------------------------------------------------+
| H13CN      | 31.0 - 950.0 GHz, HFL                                             |
+------------+-------------------------------------------------------------------+
| HN13C      | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| N2H+       | 31.0 - 950.0 GHz, HFL                                             |
+------------+-------------------------------------------------------------------+
| C18O"      | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| H13CO+     | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| DCO+       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| H2CO       | 31.0 - 950.0 GHz, weakest lines eliminated, limited to Eu < 200 K |
+------------+-------------------------------------------------------------------+
| DCN        | 31.0 - 950.0 GHz, HFL                                             |
+------------+-------------------------------------------------------------------+
| CS         | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| SiO        | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| SO         | 31.0 - 950.0 GHz, weakest lines eliminated                        |
+------------+-------------------------------------------------------------------+
| HC3N       | 31.0 - 950.0 GHz, HFL, weakest lines eliminated                   |
+------------+-------------------------------------------------------------------+
| 13CS       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+
| C34S       | 31.0 - 950.0 GHz                                                  |
+------------+-------------------------------------------------------------------+

HFL indicates hyperfine lines, these transitions are treated specially in that only
the strongest hyperfine line is searched for initially. If that line is found then
the rest of the hyperfine components are searched for. There are currently 962 transitions
in the DB (542 primary transitions and 420 hyperfine transitions).

You can query the DB directly through python as follows:

.. code-block:: python

  from admit.util.Tier1DB import Tier1DB
  # connect to the DB
  t1db = Tier1DB()
  # query for all primary transitions between 90.0 and 90.1 GHz
  t1db.searchtransitions(freq=[90.0, 90.1])
  # get the results as LineData objects
  results = t1db.getall()
  # look for any with hyperfine transitions (hfnum > 0) and get them
  for line in results:
    if line.getkey("hfnum") > 0:
      t1db.searchhfs(line.getkey("hfnum"))
      hfsresults = t1db.getall()


ADMIT in Your Web Browser
=========================

ADMIT Data Products are most easily viewed from your favorite
web browser utilizing the index.html file that is present within the
*input-cube-name.admit* (default, or *your-alias-name.admit*) directory. 


You can do this
To do so, start up CASA and instantiate an ADMIT object of the
output data:

.. code-block:: python

   CASA <1>: import admit
   CASA <2>: a = admit.Project('/path/to/input-cube-name.admit',dataserver=True)

This will open a new page in your default browser (or new browser
window if none was open) and load the ADMIT products web page view of
the specified directory.   The page is divided into 4 separate
tabs:  *Flow View*, *Form View*, *ADMIT Log*, *LineID Editor*, and
*ADMIT Documentation*.

*Flow View*
  This view shows the tasks in the order in which they were executed. 
  At the top is the directed acyclic graph of the entire ADMIT Flow.
  Each task has a bar giving the task name and arguments.  If you click on
  the bar, that section will expand to show all the output from that task.
  Clicking on a thumbnail of an image will display a larger version of the 
  image.

*Form View* 
  This view allows you to edit task parameters and re-run the ADMIT flow.
  Similar to Flow View, the tasks are show in execution order and clicking
  on each bar will expand to give an editable form of the task keywords.
  Once you are done editting keywords, click on *Re-run ADMIT Flow" button*
  at the bottom of the page.  This will communicate your changes back to
  your CASA session and re-run the tasks that you changed (and any that
  depended on them).

*ADMIT Log*
  This is the full log file of the ADMIT process/script that created your
  ADMIT data.

*LineID Editor*
  This allows you do modify the results of LineID_AT.  **Currently in prototype stage.**

*ADMIT Documentation*
  Link to the on-line ADMIT documentation webpages.

ADMIT output for multiple projects can be loaded one at a time into
separate browser pages. The browser pages do not interact.

For simply viewing the products without a CASA session, you
can enter the full directory path into an open browser
(``file:///full-directory-path`` as the url) or by using the ADMIT *aopen*.

    *aopen index.html* or *aopen sub-directory-name/index.html*

However, note you do not get the Form or LineID Editor functionality with
this mode.





.. _ADMIT Project:      module/admit/Admit.html
.. _ADMIT Tasks:        module/admit/AT.html
.. _ADMIT Task:         module/admit/AT.html
.. _BDP:                module/admit.bdp/BDP.html
.. _Basic Data Product: module/admit.bdp/BDP.html
.. _data products:      module/admit.bdp/BDP.html
.. _CASA:               http://casaguides.nrao.edu/index.php/Main_Page
.. _Flow Manager:       module/admit/FlowManager.html
.. _Flow:               design.html#workflow-management
.. _Install Guide:      installguide.html
.. _Ingest_AT:          module/admit.at/Ingest_AT.html
.. _CubeStats_AT:       module/admit.at/CubeStats_AT.html
.. _Moment_AT:          module/admit.at/Moment_AT.html
.. _CubeSpectrum_AT:    module/admit.at/CubeSpectrum_AT.html
.. _LineID_AT:          module/admit.at/LineID_AT.html
.. _LineCube_AT:        module/admit.at/LineCube_AT.html
.. _LineSegment_AT:     module/admit.at/LineSegment_AT.html
.. _ContinuumSub_AT:    module/admit.at/ContinuumSub_AT.html
.. _Line_Moment:        module/admit.recipes/Line_Moment.html
