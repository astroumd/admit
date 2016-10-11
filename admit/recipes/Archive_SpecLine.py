#!/usr/bin/env casarun
""".. _Archive_SpecLine-api:

   **Archive_SpecLine** --- Produces standard JAO ADMIT pipeline products for spectral line images.
   ===========================================================

   Usage: admit_recipe Archive_SpecLine Your-Image-Cube [Your-Primary-Beam]

   or

   admit.recipe("Archive_SpecLine","Your-Image-Cube","Your-Primary-Beam")

   This ADMIT script makes standard ADMIT pipeline products for a local dataset.  The flow is:

   #. Ingest your cube into ADMIT (creates a CASA image if starts as FITS)
   #. Calculate statistics on cube for later use
   #. Calculate simple sum of all channels to decide where to make a spectrum
   #. Make a spectrum at the peak in the sum map from step #3
   #. Make a PV slice through the sum map
   #. Find segments with emission or absorption and try to ID the line(s)
   #. Cut out cubes for each line found; cube name is line name
   #. Calculate moment 0,1,2 maps for each line cube
   #. Make a spectrum at the peak in each moment map
   #. Make a PV slice through the peak in each moment map

   Parameters
   ---------- 
   param1 : image
     Your CASA or FITS image. If the image file is not primary beam
     corrected, then input only this cube. Default cubes from *clean*
     are like this. The noise does not rise up at the edge of the field

   param2 : image, optional
     Your CASA or FITS primary beam image.  Cubes from 
     the ALMA archive are often primary beam corrected.  In these images,
     the noise rises out from the center of the imaged field. In this 
     case, you need to input both the image file and the primary beam 
     cube. Both are available to you from the archive.

   Optional Keywords
   -----------------
   - *numsigma* in LineID_AT: typically use 6.0 to 8.0 for 4000 channels;
     4.0 if you only have a few hundred channels
     3.0 if you want to dig deep but then expect to get 
     fake lines too. Default:6

   - *minchan* in LineID_AT: minimum width of line in channels to assume when searching for lines. Default:5

   - *pad* in Linecube_AT: this controls how many "extra" channels are added to either end of the line sub-cube to be cut from the  input cube.  It should generally be comparable to your line width. Default:50

   - *cutoff* in Moment_AT: number of sigma for cut levels in making moment maps: one value for each requested moment map.  Must be a Python list: [1.0, 2.0,3.0] for example for moment 0, 1 and 2 maps.  Default:[1.5,3,3]

   - *width* in PVSlice_AT: width in channels orthogonal to the slice length to sum. Default:5

   - *box* in Ingest_AT: Box to select when ingesting a cube. Default: entire image"
"""
#
# Required imports
#
import os, sys
import ast
import admit
# Give a descriptive name to required optional keyless arguments 
# to be used in help string.
REQARGS = ["Spectral-Cube"]

# Give a descriptive name to optional keyless arguments to be used 
# in help string.
OPTARGS = ["Spectral-Primary-Beam"]


# Keywords recognized by this program and their default values.
# Non-matching keywords given on command line will be ignored.
KEYS = {"minchan" :5, "numsigma": 6.0, "cutoff":[1.5,3.0,3.0], "width":5, "pad":50, "box":[] }

# Brief description of accepted keywords
KEYDESC = { 
           "numsigma": "number of sigma cutoff for LineID_AT. Default:%s" % str(KEYS['numsigma']),
           "minchan" : "minimum channel width of line when searching for lines. Default:%s" % str(KEYS['minchan']),
           "pad"     : "number of extra channels added to either end of LineCubes. Default: %s" % str(KEYS['pad']),
           "cutoff"  : "list giving number of sigma for cut levels for output moment maps. Default:%s" % str(KEYS['cutoff']),
           "width"   : "width in channels of position-velocity slice in PVSlice_AT. Default:%s" % str(KEYS['width']),
           "box"     : "Select a box region in when ingesting the cube. blc,tlc (a list of 2, 4 or 6 integers). Default: %s" % str(KEYS['box'])
          }


# put the functionality in a method so that it is not executed when
# sphinx imports it to make the documentation.  The method name starts
# with _ so that the method is not listed in the sphinx-generated documentation
def _run(argv):

    # Verify arguments are good
    if ( not admit.recipeutils._processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,__doc__)): return

    cubefile = argv[1]
    projdir = os.path.splitext(argv[1])[0] + '.admit'
    pbcorfile = None
    if len(argv) == 3:
        pbcorfile = argv[2]
    #========================================================================
    # Master project.  Beginning for ADMIT Commands
    # 
    p = admit.Project(projdir,commit=False)

    # convert key values from string
    try:
        KEYS["minchan"]  = int(KEYS["minchan"])
        KEYS["numsigma"] = float(KEYS["numsigma"])
        KEYS["pad"]      = int(KEYS["pad"])
        KEYS["width"]    = int(KEYS["width"])
        KEYS["cutoff"]   = ast.literal_eval(str(KEYS["cutoff"]))
        KEYS["box"]      = ast.literal_eval(str(KEYS["box"]))
    except Exception, e:
        print("Exception converting keyword value to number:",e)
        return
    #
    # Set-up all ADMIT Flow tasks for execution including their aliases and connections
    # The aliases allow you to refer to a task's input by the alias name of the (previous) 
    # task providing that input.
    #

    # list object for Tasks so we don't have to individually name them
    Tasks = []
    if pbcorfile == None:
        Tasks.append(p.addtask(admit.Ingest_AT(alias='incube',file=cubefile,box=KEYS["box"])))
    else:
        Tasks.append(p.addtask(admit.Ingest_AT(alias='incube',file=cubefile, pb=pbcorfile,box=KEYS["box"])))

    Tasks.append(p.addtask(admit.CubeStats_AT(alias='instats'), ['incube']))
    Tasks.append(p.addtask(admit.CubeSum_AT(sigma=1, numsigma=3.0, alias='insum'), ['incube', 'instats']))
    Tasks.append(p.addtask(admit.CubeSpectrum_AT(alias='spec1'), ['incube', 'insum']))
    Tasks.append(p.addtask(admit.PVSlice_AT(alias="cubepv",width=KEYS["width"]), ['incube', 'insum']))
    Tasks.append(p.addtask(admit.LineID_AT(csub=[1,1], minchan=KEYS["minchan"], numsigma=KEYS["numsigma"], alias='lines'), ['instats','spec1']))
    Tasks.append(p.addtask(admit.LineCube_AT(alias='cutcubes', pad=KEYS["pad"]), ['incube', 'lines']))
    Tasks.append(p.addtask(admit.Moment_AT(alias='linemom', mom0clip=3.0, numsigma=KEYS["cutoff"], moments=[0, 1, 2]), ['cutcubes', 'instats']))
    Tasks.append(p.addtask(admit.CubeSpectrum_AT(alias='linespec'), ['cutcubes', 'linemom']))
    # While 'linemom' produces 3 moment image BDPs, the default input is taken 
    # here, which is the first BDP which is the zeroth moment.  This relies on
    # Moment_AT's default behavior of putting the zeroth moment in the 
    # BDP index 0.
    Tasks.append(p.addtask(admit.PVSlice_AT(alias="linepv",width=KEYS["width"]), ['cutcubes', 'linemom']))
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
