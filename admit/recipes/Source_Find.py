#!/usr/bin/env casarun
#
""".. _Source_Find-api:

   **Source_Find** --- Finds sources in a 2-D image.
   ===========================================================

   Usage: admit_recipe Source_Find Your-Image [Your-Primary-Beam]

   or

   admit.recipe("Source_Find","Your-Image","Your-Primary-Beam")

   This ADMIT script find sources in a 2-D ALMA interferometer image. The flow is:

   #. Ingest your image into ADMIT (creates a CASA image if starts as FITS)
   #. Calculate statistics on image for later use
   #. Find sources in image

   Parameters
   ---------- 
   param1 : image
     Your CASA or FITS image. If the image file is not primary beam
     corrected, then input only this image. Default images from *clean*
     are like this. The noise does not rise up at the edge of the field

   param2: image, optional
     Your CASA or FITS primary beam image.  Images from 
     the ALMA archive are often primary beam corrected.  In these images,
     the noise rises out from the center of the imaged field. In this 
     case, you need to input both the image file and the primary beam 
     image. Both are available to you from the archive.

   Optional Keywords
   ------------------

   - *numsigma* in SFind2D_AT: typically use 6.0 to 8.0;
     4.0 if you want ot dig deeper. See the next parameter regarding
     limits on dynamic range in the presence of strong sources. Default:8

   - *snmax* in SFind2D_AT: this limits the dynamic range between
     the strongest source detected in the map and the weakest source
     detected. It overrides numsigma*sigma if it is larger. Default:35
"""
#
# Required imports
#
import os, sys
import admit

# Give a descriptive name to required optional keyless arguments 
# to be used in help string.
REQARGS = ["Input-Image"]

# Give a descriptive name to optional keyless arguments to be used 
# in help string.
OPTARGS = ["Input-Primary-Beam"]


# Keywords recognized by this program and their default values.
# Non-matching keywords given on command line will be ignored.
KEYS = {"numsigma": 8.0, "snmax":35.0}

KEYDESC = { 
           "numsigma": "number of sigma cutoff for SFind2D_AT. Default:%s"%str(KEYS["numsigma"]),
           "snmax" :  "dynamic range limit. Default:%s"%str(KEYS["snmax"])
          }

# put the functionality in a method so that it is not executed when
# sphinx imports it to make the documentation.  The method name starts
# with _ so that the method is not listed in the sphinx-generated documentation
def _run(argv):

    # Verify arguments are good
    if ( not admit.recipeutils._processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,__doc__)): return

    imagefile = argv[1]
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
        KEYS["numsigma"] = float(KEYS["numsigma"])
        KEYS["snmax"]   = float(KEYS["snmax"])
    except Exception, e:
        print("Exception converting keyword value to number:",e)
        return
    #
    # Set-up all ADMIT Flow tasks for execution including their aliases and connections
    # The aliases allow you to refer to a task's input by the alias name of the (previous) 
    # task providing that input.
    #
    if pbcorfile == None:
        Task0  = p.addtask(admit.Ingest_AT(alias='inimage',file=imagefile))
    else:
        Task0  = p.addtask(admit.Ingest_AT( alias='inimage', file=imagefile, pb=pbcorfile ))
    Task1  = p.addtask(admit.CubeStats_AT(alias='instats'), ['inimage'])
    Task2  = p.addtask(admit.SFind2D_AT(alias='srcfind',numsigma=KEYS["numsigma"], snmax=KEYS["snmax"]), ['inimage', 'instats'])
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
