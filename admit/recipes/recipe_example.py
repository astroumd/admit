#!/usr/bin/env casarun
"""ADMIT Recipe:  Archive_Pipeline

  Produces locally standard JAO ADMIT pipeline products.

  This ADMIT script makes standard ADMIT pipeline products for a local dataset.  The flow is:

   #. Ingest the cube and continuum image into ADMIT doing primary beam correction  if PB file(s) supplied. This will create CASA images if inputs are FITS.
   #. Calculate statistics on cube for later use
   #. Make a zeroth moment map over all emission in the cube.
   #. Make a position-velocity (PV) slice oriented on the moment emission from the previous step.
   #. Find segments with emission or absorption and try to ID the line(s)
   #. Cut out cubes for each line found; cube name is line name
   #. Calculate moment 0,1,2 maps for each line cube
   #. Make a spectrum at the peak in each moment map
   #. Make a PV slice through the peak in each moment map
   #. Search for sources in the continuum map down to a given cutoff.
   #. Make a spectrum at each source found from in the previous step.

"""

import os, sys
import admit
import admit.scripts.recipeutils

# Give a descriptive name to required optional keyless arguments 
# to be used in help string.
REQARGS = ["Input-Cube1", "Input-Cube2"]

# Give a descriptive name to optional keyless arguments to be used 
# in help string.
OPTARGS = ["Input-PB1", "Input-PB2"]

# Keywords recognized by this program and their default values.
# Non-matching keywords given on command line will be ignored.
KEYS = {"foo": "bar", "minchan" :2, "numsigma": 5.0}

# Brief description of accepted keywords
KEYDESC = {"foo"      : "the foo parameter",
           "minchan"  : "The minimum number of channels",
           "numsigma" : "Number of 1-sigma rms for cutoff level"
          }

# Minimum required keyless arguments
MINARGS = len(REQARGS)  

# Number of optional keyless arguments  (max args = MINARGS+OPTARGS)
# Note: rule is that if user provides one optional keyless argument,
#       user must supply them all.  That's the only way to know
#       which optional keyless argument is which.
NUMOPTARGS = len(OPTARGS)  

def _run(argv):
    print "ARGV=",argv

    if ( not admit.recipeutils._processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,__doc__)): return

    # Ensure argv is a list.  It could be a tuple if it came in
    # through admit_recipe.  That's probably ok, but we just want 
    # consistency downstream
    argv = list(argv)

    print KEYS
    print argv

if __name__ == "__main__":

    # Command line processing to pick-up file name and define
    #        ADMIT directory that you will be creating
    argv = admit.utils.casa_argv(sys.argv)

    # now do the work
    _run(argv)
