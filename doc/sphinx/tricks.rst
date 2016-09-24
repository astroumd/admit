ADMIT tricks and advanced script usage
======================================


In this section we describe some more advanced usages of ADMIT,
particularly in the use of the Unix command line.

Input FITS files: listfitsa
---------------------------

The script **listfitsa** helps to quickly summarizing cube size,
source name, ra/dec/freq and filesize of your FITS files. The script
will accept the usual wild card style arguments. E.g.:

.. code-block:: bash
		
    $ listfitsa *.fits

    concat.spw17.image.fits [118, 118, 4096, 1] Serpens_Main 277.491666667 1.22916666667 244.867618746 0.212
    concat.spw19.image.fits [116, 116, 4096, 1] Serpens_Main 277.491666667 1.22916666667 240.948346249 0.205
    concat.spw21.image.fits [108, 108, 4096, 1] Serpens_Main 277.491666667 1.22916666667 225.785304399 0.178
    concat.spw23.image.fits [110, 110, 4080, 1] Serpens_Main 277.491666667 1.22916666667 229.146014394 0.184
    concat.spw33.image.fits [138, 138, 4096, 1] Serpens_Main 277.491666667 1.22916666667 342.937829665 0.291
    concat.spw35.image.fits [138, 138, 4080, 1] Serpens_Main 277.491666667 1.22916666667 341.196253808 0.289
    concat.spw37.image.fits [144, 144, 4096, 1] Serpens_Main 277.491666667 1.22916666667 354.435171299 0.316
    concat.spw39.image.fits [142, 142, 4096, 1] Serpens_Main 277.491666667 1.22916666667 351.698458419 0.308

The optional **-v** option can be used for a verbose listing of the FITS header.

Output FITS files: image2fits
-----------------------------

If you are in an ADMIT developer environment, your unix shell has direct access to a number of
CASA commands. In particular the

.. code-block:: bash

   $ image2fits in=test0.admit/x.csm out=test0.mom0.fits

(make sure you have a proper 4-element $CASAPATH, otherwise this command will fail).

An alternative is the ADMIT script **casa2fits**, which handles multiple casa images and appends the fits extension:

.. code-block:: bash

   $ casa2fits test1.im test2.im test3.im
   -> test1.im.fits test2.im.fits test3.im.fits

Running ADMIT recipes
---------------------

We already discussed ADMIT recipes earlier, but list them here for completeness. You run them
in the shell as follows:

.. code-block:: bash

   $ admit_recipe Line_Moment test0.fits

and just typing the command **admit_recipe** will list the currently available
recipes.


Export ADMIT projects
---------------------

If you want to share a project with a collaborator, or have a developer look at certain types
of problems, you can turn your ADMIT project into a tar file. The script **admit_export** makes
this a little easier, and also have an option to make a more lightweight version of the project
if your recipient does not need the actual cubes. This is actually the default of the script,

.. code-block:: bash

   $ admit_export test0.admit
   Writing brief test0.admit.tar.gz

   $ admit_export -a test0.admit -b test00.admit
   Writing all in test0.admit.tar.gz
   Writing brief test00.admit.tar.gz


You can export as many projects as you want, and whenever the **-a** or **-b** arguments are mentioned,
subsequent projects are in their respective modes.
		
Native File Browser
-------------------

The **aopen** script is an alternative to the web based review (and
re-run) of an ADMIT project. It will use whatever your native OS has
available to resolve how to *display* a file given the file extension
of magic marker. It will accept a directory name, with no arguments
it will open the current directory.


Line Fitting
------------

In each ADMIT directory where LineID has run you can currently find ascii tables that represent
the different spectra that feed into LineID, albeit via their respective BDP's.

1. testCubeSpectrum.tab (make sure multiple points come out right now)

2. testCubeStats.tab

3. testPVCorr.tab

The tables have two columns, the observed frequency and the "*spectrum*". Technically we
call each of them a spectrum, as they represent some response where we expect a
signal where the transition is. See **admit4.py** below. Of course, within ADMIT these tables
are really properly stored within a BDP (an XML file). For example, the *testCubeSpectrum.tab*
file is probably in a file x.csp.bdp


Doppler Recession
-----------------

Optical, Radio and Relativistic conventions exist.  CASA has conversion routines,
so does astropy, and we have a version in admit.util. Would be good to reference
that here. Add some reminder math as well?

apar files
----------

Some of the ADMIT scripts can use an *apar* file to help you set script parameters.
These are ascii files, actually meant to be
executable python code (the first line should contain a magic ** -*- python -*- ** marker
for emacs zealots)

Scripts will typically support looking at certain default names, in the following order:

1. *<scriptname>.apar* for global parameters (for example admit1.apar)

2. *<fitsname>.apar*  for specific files (for example test0.fits.apar)

3. *<aparname>.apar*  for personal use (for example test123.apar, if your script supported
   the *--apar test123.apar* command line option; admit1.py does).

An example to use executable code is in *$ADMIT/etc/data/test253_spw3.fits.apar*   

.. _runa1-script:

runa1 and admit1.py
-------------------

The **runa1** script is a very simple front-end to the more complex **admit1.py** script,
which is the current (and still evolving) model how to run ADMIT on the pipeline. It contains
some decision making which depends on running an admit project at critical times.

You would only pass the name of a fits file to the script, and the script tries to figure out what
type of ALMA (or non-ALMA) fits file you have and call **admit1.py** appropriately.  The flow of the
script can be controlled by a number of admit parameters (*apar*, see below),
that match certain AT keywords.
You can store these in an *apar* file, but it has to be python executable code.

If you want to use  **runa1**, here's a sample workflow and strategy:

1. Run the script "listfitsa" on the fits file to get the object name for vlsr
   
   .. code-block:: none

      $ listfitsa uid___A001_X12b_X231.NGC_1068_sci.spw17.cube.I.pbcor.fits
      -> [1000, 1000, 3839, 1] NGC_1068 40.6696170833 -0.0133133333333 14.301

   This is a 1000 x 1000 x 3839 cube, source name is NGC_1068,
   RA,DEC are 40.6696170833 -0.0133133333333 and the datasize is 14.3 GB

   If that does not resolve the source name, use "listfitsa -v" and debug the full header
   to find the sourcename (e.g. OBJECT vs. FIELD issue?   use of quotes?)

2. Enter the appropriate VLSR into ADMIT; there are several ways to do this:

   1. enter it into **$ADMIT/etc/vlsr.tab**, but this requires you to be able to write there
      and there is the issue what happens if ADMIT gets updated
   2. enter it into a private apar file:
      
      1. admit1.apar , which is used for all fits files in the working directory
      	 if you use admit1  (other recipes should support this as well)n
      2. test0.fits.apar, which would only be used for that fits file
      

   You can use NED or SIMBAD, but be sure to get the VLSRK, since that's the official
   ALMA frame of reference 
   
   .. code-block:: none
		
      http://ned.ipac.caltech.edu/
      http://simbad.u-strasbg.fr/simbad/

   and stuff this into *admit1.apar* so each fits file will.
   We have this code in VLSR.py, could add a python commandline interface


   If the ALMA source name has spaces, you must use quotes. Otherwise not needed.



3. PB correction is currently very slow in ADMIT (CASA) for large cubes.
   Especially if your imaging area has a large portion outside of the 50%
   you could use a straight ADMIT on the pbcor file, since the inner portion
   is not affected.
   To confirm you can do this, run *admit1.py* with maxlines=0 in admit1.apar
   and inspect the cubesum (CSM) map how much smaller you can make your map.
   e.g.
   
   .. code-block:: bash
		
       $ runa1 uid___A001_X12b_X231.NGC_1068_sci.spw17.cube.I.pbcor.fits
       
   Assuming all your spw's have the same imaging area, add these into admit1.apar
   via the inbox= (and optionally inedge=) keywords for admit1.py:

   .. code-block:: python
		   
       inbox  = [xmin,ymin,xmax,ymax]
       inedge = [2,2]

   and use the full fits name:
   
   .. code-block:: none
		
       runa1 uid___A001_X12b_X231.NGC_1068_sci.spw17.cube.I.pbcor.fits

   If you must go the slow way, the *runa1* script needs the shorter name
   to deal with the **pbcor.fits** and **pb.fits** file, as follows:

   .. code-block:: none
		
       runa1 uid___A001_X12b_X231.NGC_1068_sci.spw17.cube.I

   Example: just Ingest_AT takes 53 mins on this 14GB cube, but in just
   	    **pbcor.fits** mode it was barely 4 mins.

   .. code-block:: none
		
      full:   real/user/sys     100m25.976s / 60m50.785s / 22m35.384s   DIED IN LINEID
      pbcor:  real/user/sys      27m9.151s  / 17m50.085s /  4m10.644s   OK

                  pbcor(")     full(")
      ingest        223        3205
      cubestats     552         602
      cubesum        47          47
      pvslice       479         574
      lineid         19           -
      linecube       90           -


4. If you have a large (>1?) set of fits cubes with the ALMA naming and directory
   (project/SOUS/MOUS/GOUS/products) convention, there's a script *do_aap* in
   ADMIT that can help you processing all data in a clean directory.
   Alternatively you can run admit (e.g. *runa1*) inside of each of the
   (project/SOUS/MOUS/GOUS/products) directories.

   Essentially, the *do_aap* script creates symlinks into those trees but processes
   in local admit directories, outside of the ALMA tree structure.
   See documentation in script, and more examples to come here.

   A version of *do_aap* exists that works from **working/** instead of **product/**, and looks
   for the "\*.cont.residual" files, which are the continuum subtracted cubes.


admit1 apar parameters
^^^^^^^^^^^^^^^^^^^^^^

The ADMIT apar parameters can be placed in up to three files, processed in the following order

1. *admit1.apar* : if present, this apar file will be first parsed

2. *fitsfilename.apar* : if present, this apar file will be parsed next

3. *aparname.apar* : if present as argument to the **--apar** command line argument to **admit1.py**,
   this will be read last.


They normally contain python variables, used by **admit1**, but can also contain python code, if you
parameters need a minor computation.
   

.. code-block:: python
		
   useMask  = False       # Ingest_AT(mask=)
   
This uses a mask where fits data == 0.0. Normally not needed, as ALMA fits
cubes are properly masked where needed.

.. code-block:: python
		
   vlsr     = None        # Ingest_AT(vlsr=) and LineID_AT(vlsr=)

Somewhat peculiar. Normally is a float, so you would use **vlsr=236.0**, but by
setting it to the **None** python value, we tell the AT to try it figure it out
from the RESTFREQ, if present. If no value found, 0.0 will be used and most likely
LineID will not do a great job. Look at the output for Ingest_AT, where it lists
the *VLSRc* value.

.. code-block:: python
		
   maxpos   = []          # CubeSpectrum_AT(pos=)

Paired positions, e.g. *maxpos=[10,10,64,64,128,128]*,  for the probes for a spectrum
through the cube with CubeSpectrum_AT that will also normally serve as input for LineID_AT.
You can also use CASA's RA-DEC position: *maxpos=['00h47m33.041s','-25d17m26.61s']*

.. code-block:: python
		
   robust   = ['hin',1.5]  # CubeStats_AT(robust=)

Robust noise, as an alternative to the default MAD scheme.

.. code-block:: python

   contsub  = [None]           # ContinuumSub_AT(contsub=)

By default no continuum is subtracted. You can set this to either a blank list (*[]*), in
which case the LineSegment_AT() will be used to block out potential lines and determine
the continuum, or a specific number of tuples can be given where the continuum should be
fitted, for example *[(0,99), (900,999)]*


.. code-block:: python
   
   insmooth = []               # smooth inside of Ingest_AT, in pixels
   inbox    = []               # box to cut in Ingest_AT  [x0,y0,x1,y1] or [x0,y0,z0,x1,y1,z1]
   inedge   = []               # edges to cut in Ingest_AT [zleft,zright]
                               # [0] and [1] are spatial
                               # [2] is frequency:    1=>Hanning  >1 Boxcar
   smooth   = []               # if set, smooth the cube right after ingest (list of 2 or 3 can be given)
   usePeak  = True             # LineCubeSpectra through peak of a Moment0 map? (else pos[] or SpwCube Peak)
   useCSM   = False            # if usePeak, should CubeSum (CSM) be used (instead of mom0 from LineCube)
   pvslice  = []               # PV Slice (x0,y0,x1,y1)
   pvslit   = []               # PV Slice (xc,yc,len,pa)  if none given, it will try and find out
   pvwidth  = 5                # width of a slit in PV (>1 will decrease the noise in PV)
   usePV    = True             # make a PVSlice?
   usePPP   = True             # create and use PeakPointPlot?
   useMOM   = True             # if no lines are found, do a MOM0,1,2 anyways ?
   minOI    = 0                # If at least minOI linecubes present, use them in an OverlapIntegral; 0 turns off OI
   pvSmooth = [10,10]          # smooth the PVslice ?   Pos or Pos,Vel pixel numbers
   maxlines = -1               # limit the # linecubes? (set to 0 if you want to exit after LineID_AT)
   linebdp  = [True, True, False]    #  use of [CSP,CST,PVC] for LineID?
   contbdp  = [True, True]           #  use of [CSP,CST] for LineSegment
   cspbdp   = [True, True, True]     #  use of [CST,CSM, SL] for initial CubeSpectrum
   lineUID  = False                  # if True, this would run LineID(identifylines=False) [old relic]
   lineSEG  = True                   # if True, it also runs LineSegment (aiding in automated ContinuumSub)
   linepar  = ()                     # if set, (numsigma,minchan,maxgap); both LineSegment and LineID
   iterate  = True                   # iterate to find narrower higher S/N peaks
   online   = False                  # use splatalogue online?
   reflist  = 'etc/co_lines.list'    # pick one from $ADMIT/etc
   llsmooth = []                     # if set, apply this smoothing to the inputs for LineSegment and LineId

admit1.py
----------

Here is a different descriptive explanation about how guide you through
the darkness of running admit1,
with comments for future expansion of this script.  Again,the parameters
listed are the APAR parameters, which are close to (but not necessarely
identical to) the AT keywords.

A FITS cube (**file=**) is selected for ingestion into the ADMIT
flow. This needs to be a noise flat data cube.  If you get a primary
beam corrected cube (where the noise increases near the edges of the
field), it will need to be multiplied by the primary beam, in order to
get noise flat images.  This is a current limitation of ADMIT, it
works best if the image has more-or-less constant RMS accross the
field, although we do allow it to very per channel.  The **pb=**
keyword is meant to pass a primary beam into the flow, you can leave
it blank if you don't need it.

An optional continuum map (**cont=**) can be added to the flow. This
will be used to find one or more continuum sources, which can then be used
as probes for a spectrum, but more on that below.

At the ingest stage, there are a few procedures worth mentioning:

1. A subregion can be given using **inbox=**. This can be very useful if you
   are certain the source is limited spatially and/or spectrally. This can
   save a huge amount of processing.

2. If no box was given, you can also specify taking out a number of edge
   channels using **inedge=**.

3. Smoothing can be applied to the cube using **insmooth=**. Although there
   is a separate **Smooth_AT** available to do this as a separate step in the
   flow, this will take up extra disk space.  *need to confirm if flux is
   conserved in this step*


The cube can now be smoothed, potentially to help in the line detection.
Once the line detection has succeeded, you can opt to continue with
the original higher resolution cube. You trigger a smoothing operation
with **smooth=**.

Although  **Ingest_AT** will report some global stastics of the cube
(a min,max,RMS), these are not what we call robust statistics (an attempt
to ignore the signal and compute the statistics on the remainder).

Thus the first step after the data has been ingested (and smoothed) is a
thorough analysis of the statistics. This is currently done on a plane
by plane basis, since they can differ. Different methods to reject the
signal and attempt to get a robust statistics is available wiht the
**robust=** keyword.

If the RMS(channel) plot shows suspicious *"lines"* where lines are also
present, this could be the result of:

1. Missing short spacings where there is source structure in a line. You 
   would also expect to see the *minval* to show that line structure

2. Extended emission where even the robust noise detection failed. You can try
   different methods or **robust=**, in particular the half-fit should be less
   sensitive.

3. Continuum emission had not been (properly) subtracted.


More on **CubeSum**, **CubeSpectrum** now. Then go into **LineSegment_AT**

   
After the continuum has been subtracted based on the LineSegment's, a good strategy
to check on its correctness would be to take the new continuum free cube, and extract
a new CubeSum of the line based on the segments, as well as a sum of all the
emission that was not deemed part of the lines (**x-test_line.csm**),
to check if no remaining
line or continuum emission was left. It should be a pure noise map,
and we need a cubestats and histogram for this. Should find the noise
to be *sigma/sqrt(nchan)*. This map is **x-test_cont.csm**.

We now have new CST and CSP and perhaps a PVC. They can be fed into
**LineID_AT** for line identification.



runa2 and admit2.py
-------------------

This is a special version of *admit1* for just continuum maps. The flow will only
call CubeStats_AT and SFind2D_AT and present a list of found sources and fluxes.
The **--cont** option in *admit1* can be used to pass a continuum map and use
the brightest continuum source position as probe for CubeSpectrum_AT in that flow.

runa4 and admit4.py
-------------------

The **runa4** script is a simple front-end for **admit4.py**, which allows you to take an ASCII spectrum
(frequency in column 1, in GHz, spectrum value in column 2, arbitrary units).  For example,
from the Unix command line

.. code-block:: bash

   $ runa4 test0.admit/testCubeSpectrum.tab

would import this table into a CubeSpectrum_BDP and rerun the LineSegment_AT and LineId_AT tasks and allow you
to experiment with LineID_AT. Parameters can be placed in *admit4.apar* or
*testCubeSpectrum.tab.apar* in this specific case.


admit4 apar parameters
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
		
   vlsr     = 0.0              # LineID_AT(vlsr=)

Set the VLSR (remember to use the VLSK frame of reference for ALMA data) for LineID
		
.. code-block:: python
		
   loglevel = 10               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL

The default ADMIT loglevel is 20, and some verbose feedback from the work done in LineSegment
and LineID needs loglevel=10.

.. code-block:: python
		
   lineUID  = False            # LineID_AT(identifylines=True)

This would limit the LineID run to only identifying line segments, and it's output should be
identical to LineSegment. By default lines will be identified.

.. code-block:: python
		
   linepar  = ()               # LineID_AT(numsigma=,minchan=,maxgap=) and LineSegment_AT(...)

A convenience 

.. code-block:: python
		
   llsmooth = []               # LineID_AT(smooth=) and LineSegment_AT(...)

.. code-block:: python
		
   iterate  = True             # LineID_AT(iterate=)

.. code-block:: python
		
   csub     = None             # LineID_AT(csub=) and LineSegment_AT(...)

Since only one spectrum is read, only the CubeSpectrum csub parameter (normally a list) has to be set
as an integer here.

.. code-block:: python
		
   online   = False            # LineID_AT(online=)

By default the CASA internal slsearch() is used to query a smaller version of Splatalogue, but
with online=True the web interface can be used, at the cost of some latency.
   
.. code-block:: python
		
   reflist  = 'etc/co_lines.list'    # LineID(references=)

Pick a references list, a table of names/frequencies (in GHz), to be overplotted on the LineID plots
for comparison. Some example references list files are in *$ADMIT/etc/\*_lines.list*)



.. _Moment:          module/admit.at/Moment_AT.html
.. _OverlapIntegral: module/admit.at/OverlapIntegral_AT.html
.. _unlink():        module/admit/AT.html#admit.AT.AT.unlink

.. sectionauthor:: Peter Teuben <teuben@astro.umd.edu>
