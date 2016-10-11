#!/usr/bin/env casarun
""".. _Line-Moment-api:

   **Line_Moment** --- Image cube to line moment map analysis.
   ===========================================================

   Usage: admit_recipe Line_Moment Your-Image-Cube [Your-Primary-Beam]

   or

   admit.recipe("Line_Moment","Your-Image-Cube","Your-Primary-Beam")

   This ADMIT script makes a simple moment map from an ALMA interferometer data cube. The flow is:

   #. Ingest your cube into ADMIT (creates a CASA image if starts as FITS)
   #. Calculate statistics on cube for later use
   #. Calculate simple sum of all channels to decide where to make a spectrum
   #. Make a spectrum at the peak in the sum map from step #3
   #. Find segments with emission or absorption and try to ID the line(s)
   #. Cut out cubes for each line found; cube name is line name
   #. Calculate moment 0,1,2 maps for each line cube
   #. Make a spectrum at the peak in each moment map.

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

   - *minchan* in LineID_AT: minimum width of line in # of channels to assume when searching for lines. Default:5

   - *pad* in Linecube_AT: this controls how many "extra" channels are added to either end of the line sub-cube to be cut from the  input cube.  It should generally be comparable to your line width. Default:50

   - *cutoff* in Moment_AT: number of sigma for cut levels in making moment maps: one value for each requested moment map.  Must be a Python list: [1.0, 2.0,3.0] for example for moment 0, 1 and 2 maps.  Default:[1.5,3,3]

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
KEYS = {"minchan" :5, "numsigma": 6.0, "cutoff":[1.5,3.0,3.0], "pad":50}

KEYDESC = { 
           "numsigma": "number of sigma cutoff for LineID_AT. Default:%s" % str(KEYS['numsigma']),
           "minchan" : "minimum channel width of line when searching for lines. Default:%s" % str(KEYS['minchan']),
           "cutoff"  : "list giving number of sigma for cut levels for output moment maps. Default:%s" % str(KEYS['cutoff']),
           "pad"     : "number of extra channels added to either end of LineCubes. Default: %s" % str(KEYS['pad']),
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
        KEYS["cutoff"]   = ast.literal_eval(str(KEYS["cutoff"]))
    except Exception, e:
        print("Exception converting keyword value to number:",e)
        return
    #
    # Set-up all ADMIT Flow tasks for execution including their aliases and connections
    # The aliases allow you to refer to a task's input by the alias name of the (previous) 
    # task providing that input.
    #
    if pbcorfile == None:
        Task0  = p.addtask(admit.Ingest_AT(file=cubefile, alias='incube'))
    else:
        Task0  = p.addtask(admit.Ingest_AT(file=cubefile, pb=pbcorfile,alias='incube'))
    Task1  = p.addtask(admit.CubeStats_AT(alias='instats'), ['incube'])
    Task2  = p.addtask(admit.CubeSum_AT(sigma=1, numsigma=3.0, alias='insum'), ['incube', 'instats'])
    Task3  = p.addtask(admit.CubeSpectrum_AT(alias='spec1'), ['incube', 'insum'])
    Task4  = p.addtask(admit.LineID_AT(csub=[1,1], minchan=KEYS["minchan"], numsigma=KEYS["numsigma"], alias='lines'), ['instats','spec1'])
    Task5  = p.addtask(admit.LineCube_AT(alias='cutcubes', pad=KEYS["pad"]), ['incube', 'lines'])
    Task6  = p.addtask(admit.Moment_AT(mom0clip=3.0, numsigma=KEYS["cutoff"], moments=[0, 1, 2], alias='linemom'), ['cutcubes', 'instats'])
    Task7 = p.addtask(admit.CubeSpectrum_AT(alias='linespec'), ['cutcubes', 'linemom'])
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
