#!/usr/bin/env casarun
""".. _Archive_Pipeline-api:

   **Archive_Pipeline** --- Produces standard JAO ADMIT pipeline products for spectral line plus continuum images.
   ===========================================================

   Example Usage: 
       admit_recipe Archive_Pipeline Spectral-Cube Continuum-Image

   or
       admit.recipe("Archive_Pipeline","Spectral-Cube","Continuum-Image")

   If primary beam files given: 
       admit_recipe Archive_Pipeline Spectral-Cube Continuum-Image specpb="Spectral-Primary-Beam" contpb="Continuum-Primary-Beam"

   or
       admit.recipe("Archive_Pipeline","Spectral-Cube","Continuum-Image", specpb="Spectral-Primary-Beam", contpb="Continuum-Primary-Beam")

   This ADMIT script makes standard ADMIT pipeline products for a local dataset.  The flow is:

   #. Ingest the cube and optional continuum image into ADMIT doing primary beam correction  if PB file(s) supplied. This will create CASA images if inputs are FITS.
   #. Calculate statistics on cube for later use
   #. Make a zeroth moment map over all emission in the cube.
   #. Make a position-velocity (PV) slice oriented on the moment emission from the previous step.
   #. Find segments with emission or absorption and try to ID the line(s)
   #. Cut out cubes for each line found; cube name is line name
   #. Calculate moment 0,1,2 maps for each line cube
   #. Make a spectrum at the peak in each moment map
   #. Make a PV slice through the peak in each moment map
   #. Compute statistics on continuum map
   #. Search for sources in the continuum map down to a given cutoff.
   #. Make a spectrum at each source found from in the previous step.

   Parameters
   ---------- 
   param1 : spectral image cube
     Your CASA or FITS spectral line image cube.  If the cube is not primary beam
     corrected, then do not supply a primary beam for it. Default cubes from *clean*
     are not primary beam corrected: The noise does not rise up at the edge of the field

   param2 : continuum image, optional
     Your CASA or FITS continuum image. This image should have one channel (NAXIS3=1).
     If the image is not primary beam corrected, then do not supply the primary beam for it.


   Optional Keywords
   -----------------
   - *specpb*  Spectral primary beam image
     The CASA or FITS primary beam image for the spectral line cube.  Cubes from 
     the ALMA archive are often primary beam corrected.  In these images,
     the noise rises out from the center of the imaged field. In this 
     case, you need to input both the image file and the primary beam 
     cube. Both are available to you from the archive.

   - *conpb*  Continuum primary beam image
     The CASA or FITS primary beam image for the continuum image.  

   - *numsigma* in LineID_AT: typically use 6.0 to 8.0 for 4000 channels;
     4.0 if you only have a few hundred channels
     3.0 if you want to dig deep but then expect to get fake lines too.

   - *minchan* in LineID_AT: minimum width of line in channels to assume when searching for lines.

   - *pad* in Linecube_AT: this controls how many "extra" channels are added to either end of the line sub-cube to be cut from the  input cube.  It should generally be comparable to your line width

   - *cutoff* in Moment_AT: number of sigma for cut levels in making moment maps: one value for each requested moment map.  Must be a Python list: [1.0, 2.0,3.0] for example for moment 0, 1 and 2 maps 

   - *width* in PVSlice_AT: width in channels orthogonal to the slice length to sum.
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
OPTARGS = ["Continuum-Image"]

# Keywords recognized by this program and their default values.
# Non-matching keywords given on command line will be ignored.
#KEYS = {"minchan" :4, "numsigma": 5.0, "cutoff":[1.5,3.0,3.0], "width":5, "pad":50 , "specpb":None, "contpb":None}
KEYS = {"minchan" :4, "numsigma": 5.0, "cutoff":[2.0], "width":1, "pad":5 , "specpb":None, "contpb":None}

# Brief description of accepted keywords
KEYDESC = { 
           "specpb"  : "Primary beam file to correct spectral cube. Default:None",                  # required
           "contpb"  : "Primary beam file to correct continuum image. Default:None",                # optional
           "numsigma": "number of sigma cutoff for LineID_AT. Default:%s" % str(KEYS['numsigma']),
           "minchan" : "minimum channel width of line when searching for lines. Default:%s" % str(KEYS['minchan']),
           "pad"     : "number of extra channels added to either end of LineCubes. Default: %s" % str(KEYS['pad']),
           "cutoff"  : "list giving number of sigma for cut levels for output moment maps. Default:%s" % str(KEYS['cutoff']),
           "width"   : "width in channels of position-velocity slice in PVSlice_AT. Default:%s" % str(KEYS['width']),
          }

# put the functionality in a method so that it is not executed when
# sphinx imports it to make the documentation.  The method name starts
# with _ so that the method is not listed in the sphinx-generated documentation
def _run(argv):

    # Verify arguments are good
    if ( not admit.recipeutils._processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,__doc__)): return

    cubefile = argv[1]
    contfile = None
    if len(argv) == 3:
        contfile = argv[2]
    projdir = os.path.splitext(argv[1])[0] + '.admit'
    loglevel = 10   # INFO = 15 should be user default

    # convert key values from string
    try:
        KEYS["minchan"]  = int(KEYS["minchan"])
        KEYS["numsigma"] = float(KEYS["numsigma"])
        KEYS["pad"]      = int(KEYS["pad"])
        KEYS["width"]    = int(KEYS["width"])
        KEYS["cutoff"]   = ast.literal_eval(str(KEYS["cutoff"]))
    except Exception, e:
        print("Exception converting keyword value to number:",e)
        return

    #========================================================================
    # Master project.  Beginning for ADMIT Commands
    # 
    p = admit.Project(projdir,commit=False,loglevel=loglevel)
    
    # list object for Tasks so we don't have to individually name them
    Tasks = []
    #
    # Set-up all ADMIT Flow tasks for execution including their aliases and connections
    # The aliases allow you to refer to a task's input by the alias name of the (previous) 
    # task providing that input.
    #

    # Add spectral line processing to flow
    if KEYS["specpb"] == None:
        Tasks.append(p.addtask(admit.Ingest_AT(file=cubefile, alias='incube')))
    else:
        Tasks.append(p.addtask(admit.Ingest_AT(file=cubefile, alias='incube', pb=KEYS["specpb"])))

    Tasks.append(p.addtask(admit.CubeStats_AT      (alias='instats'),                                                                  ['incube']))
    Tasks.append(p.addtask(admit.CubeSum_AT        (alias='insum',    sigma=1, numsigma=3.0),                                          ['incube', 'instats']))
    Tasks.append(p.addtask(admit.CubeSpectrum_AT   (alias='spec1'),                                                                    ['incube', 'insum']))
    Tasks.append(p.addtask(admit.PVSlice_AT        (                  width=KEYS["width"]),                                            ['incube', 'insum']))
    Tasks.append(p.addtask(admit.LineID_AT         (alias='lines',    csub=[0,0], minchan=KEYS["minchan"], numsigma=KEYS["numsigma"]), ['instats','spec1']))
    Tasks.append(p.addtask(admit.LineCube_AT       (alias='cutcubes', pad=KEYS["pad"]),                                                ['incube', 'lines']))
    Tasks.append(p.addtask(admit.Moment_AT         (alias='linemom',  mom0clip=2.0, numsigma=KEYS["cutoff"], moments=[0, 1, 2]),       ['cutcubes', 'instats']))
    Tasks.append(p.addtask(admit.CubeSpectrum_AT   (alias='linespec'),                                                                 ['cutcubes', 'linemom']))
    # While 'linemom' produces 3 moment image BDPs, the default input is taken 
    # here, which is the first BDP which is the zeroth moment.  This relies on
    # Moment_AT's default behavior of putting the zeroth moment in the 
    # BDP index 0.
    Tasks.append(p.addtask(admit.PVSlice_AT        (                  width=KEYS["width"]),                                            ['cutcubes', 'linemom']))


    # If given, add continuum map processing to flow
    if contfile != None:
        if KEYS["contpb"] == None:
            Tasks.append(p.addtask(admit.Ingest_AT (alias='incont',     file=contfile)))
        else:
            Tasks.append(p.addtask(admit.Ingest_AT (alias='incont',     file=contfile, pb=KEYS["contpb"])))

        Tasks.append(p.addtask(admit.CubeStats_AT  (alias='contstats'),                                                                ['incont']))
        Tasks.append(p.addtask(admit.SFind2D_AT    (alias='contsfind'),                                                                ['incont','contstats']))

        # Only add this CubeSpectrum_at to flow if SFind2D found at least one source.
        # This can only be known by running up the flow to now.
        p.run()

        if p['contsfind'][0] != None and len(p['contsfind'][0]) > 0:
            Tasks.append(p.addtask(admit.CubeSpectrum_AT (alias='contspec'),                                                           ['cutcubes','contsfind']))

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
