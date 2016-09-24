#!/usr/bin/env casarun
#
# Use: % Line_Moment.py Your-Cube-File-Name Your-cube's-primary-beam-file
#            
#           Input only "Your-Cube" if the image file is not primary beam
#                 corrected. Default cubes from clean are like this.
#                 The noise does not rise up at the edge of the field.
#
#           Cubes from the ALMA archive are often primary beam corrected.
#                 In these images the noise rises out from the center of
#                 the imaged field. In this case, you need to input both
#                 the image file and the primary beam cube. Both are
#                 available to you from the archive.
#=========================================================================
#
# This ADMIT script for making a simple moment map from an
#  ALMA interferometer data cube. The flow below:
#     0. Ingest your cube into ADMIT (creates a casa image if starts as FITS)
#     1. Calculate statistics on cube for later use
#     2. Calculate simple sum of all channels to decide where to make a spectrum
#     3. Make a spectrum at the peak in the sum map from step #3
#     4. Find segments with emission or absorption and try to ID the line(s)
#     5. Cut out cubes for each line found; cube name is line name
#     6. Calculate moment 0,1,2 maps for each line cube
#     7. Make a spectrum at the peak in each moment map.
#=======================================================================
#  Most common AT key word to change in the flow below:
#   - numsigma in LineID_AT: typically use 6.0 to 8.0 for 4000 channels;
#                            4.0 if you only have a few hundred channels
#                            3.0 if you want to dig deep but then expect
#                                to get fake lines too.
#   - pad in Linecube_AT: this controls how many "extra" channels are
#                            added to either end of the line sub-cube 
#                            to be cut from the input cube.  It should 
#                            generally be comparable to your line width 
#                            measured in channels
#=======================================================================
""".. _Line-Moment-api:

   **Line_Moment** --- Image cube to line moment map analysis.
   ===========================================================

   Usage: Line_Moment.py Your-Image-Cube [Your-Primary-Beam]

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

   param2: image, optional
     Your CASA or FITS primary beam image.  Cubes from 
     the ALMA archive are often primary beam corrected.  In these images,
     the noise rises out from the center of the imaged field. In this 
     case, you need to input both the image file and the primary beam 
     cube. Both are available to you from the archive.

   Notes
   -----
   (If you are editing a version of this script yourself).
   The common AT key word to change in the flow:

   - *numsigma* in LineID_AT: typically use 6.0 to 8.0 for 4000 channels;
     4.0 if you only have a few hundred channels
     3.0 if you want to dig deep but then expect to get 
     fake lines too.

   - *pad* in Linecube_AT: this controls how many "extra" channels are
     added to either end of the line sub-cube to be cut from the 
     input cube.  It should generally be comparable to your line width 
     measured in channels
"""
#
# Required imports
#
import os, sys
import admit

# put the functionality in a method so that it is not executed when
# sphinx imports it to make the documentation.  The method name starts
# with _ so that the method is not listed in the sphinx-generated documentation
def _run(argv):
    pbcorfile = None
    if len(argv) < 2 or len(argv) > 3:
        arg0 = os.path.basename(argv[0])
        # add this === line to separate it from CASA startup spew.
        print "====================================================================================="
        print "%s requires on input line the name of image file(s) with extension if any." % arg0
        print "Accepts either FITS or CASA image format files."
        print "  Usage: %s Your-Cube-File-Name [Your-Primary-Beam-File]" % arg0
        return;
    else:
        cubefile = argv[1]
        projdir = os.path.splitext(argv[1])[0] + '.admit'
    if len(argv) == 3:
        pbcorfile = argv[2]
    #========================================================================
    # Master project.  Beginning for ADMIT Commands
    # 
    p = admit.Project(projdir,commit=False)
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
    Task4  = p.addtask(admit.LineID_AT(csub=[1,1], minchan=5, numsigma=6.0, alias='lines'), ['instats','spec1'])
    Task5  = p.addtask(admit.LineCube_AT(pad=50, alias='cutcubes'), ['incube', 'lines'])
    Task6  = p.addtask(admit.Moment_AT(mom0clip=3.0, numsigma=[1.5, 3.0, 3.0], moments=[0, 1, 2], alias='linemom'), ['cutcubes', 'instats'])
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
