#!/usr/bin/env casarun
""".. _Source_Spectra-api:

   **Source_Spectra** --- Generates spectra for a series of map locations.
   ===========================================================

   Usage: admit_recipe Source_Spectra BDP-Source-Table Your-Image-Cube [Your-Primary-Beam]

   or

   admit.recipe("Source_Spectra", "BDP-Source-Table", "Your-Image-Cube","Your-Primary-Beam")

   This ADMIT script to create spectra for a list of positions in a BDP. The flow is:

   #. Ingest BDP which contains the desired source table.
   #. Ingest your cube into ADMIT (creates a CASA image if starts as FITS)
   #. Calculate the spectrum for each position

   Parameters
   ---------- 
   param1 : BDP
     The Basic Data Product that contains the source table of positions where 
     you want spectra. Typically created by SFind2D_AT (or Source_Find.py recipe).

   param2 : image
     Your CASA or FITS image. If the image file is not primary beam
     corrected, then input only this cube. Default cubes from *clean*
     are like this. The noise does not rise up at the edge of the field

   param3 : image, optional
     Your CASA or FITS primary beam image.  Cubes from 
     the ALMA archive are often primary beam corrected.  In these images,
     the noise rises out from the center of the imaged field. In this 
     case, you need to input both the image file and the primary beam 
     cube. Both are available to you from the archive.

   Optional Keywords
   -------------------

   - *xaxis* in CubeSpectrum_AT: sets x-axis type: channel number, frequency,
     velocity. Current default is channel for full cubes and velocity for
     cubes created for each emission line by LineCube_AT. Default:
"""
#
# Required imports
#
import os, sys
import admit

# Give a descriptive name to required optional keyless arguments 
# to be used in help string.
REQARGS = ["SourceList-BDP", "Spectral-Cube"]

# Give a descriptive name to optional keyless arguments to be used 
# in help string.
OPTARGS = ["Spectral-Primary-Beam"]

# Keywords recognized by this program and their default values.
# Non-matching keywords given on command line will be ignored.
KEYS = {"xaxis":"chan"}

# Brief description of accepted keywords
KEYDESC = { "xaxis": "X-axis type for CubeSpectrum_AT (chan,freq,velocity). Default:%s"%str(KEYS["xaxis"])}


# put the functionality in a method so that it is not executed when
# sphinx imports it to make the documentation.  The method name starts
# with _ so that the method is not listed in the sphinx-generated documentation
def _run(argv):

    # Verify arguments are good
    if ( not admit.recipeutils._processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,__doc__)): return

    bdpname = argv[1]
    cubefile = argv[2]
    projdir = os.path.splitext(argv[2])[0] + '.admit'
    pbcorfile = None
    if len(argv) == 4:
        pbcorfile = argv[3]

    #========================================================================
    # Master project.  Beginning for ADMIT Commands
    # 
    p = admit.Project(projdir,commit=False)
    #
    # Set-up all ADMIT Flow tasks for execution including their aliases and connections
    # The aliases allow you to refer to a task's input by the alias name of the (previous) 
    # task providing that input.
    #
    Task0 = p.addtask(admit.BDPIngest_AT( alias='bdptable', file=bdpname
))
    if pbcorfile == None:
        Task1  = p.addtask(admit.Ingest_AT(alias='incube', file=cubefile ))
    else:
        Task1  = p.addtask(admit.Ingest_AT(alias='incube', file=cubefile, pb=pbcorfile))
    Task2  = p.addtask(admit.CubeSpectrum_AT(alias='cubespec',xaxis=KEYS["xaxis"]), ['incube', 'bdptable'])
    #
    #  Execute ADMIT flow
    #
    p.run()

if __name__ == "__main__":

    # Command line processing to pick-up file name and define
    #        ADMIT directory that you will be creating
    argv = admit.utils.casa_argv(sys.argv)

    # now do the work
    _run(argv)
