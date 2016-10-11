#!/usr/bin/env casarun
""".. _recipe_example-api:

  **Recipe Example** --- An example recipe that you can use to create your own.
  ============================================================================

  This script is similar to the recipe Archive_Pipeline that
  produces locally standard JAO ADMIT pipeline products.
  The flow is:

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

   Required non-keyword arguments are set in the REQARGS list and option
   non-keyword arguments are set in the OPTARGS list.  You can create
   keywords for the script to use by modifying the  KEYS and KEYSDESC
   dictionaries.
"""

import os, sys
import admit
import admit.recipes.recipeutils

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


def _run(argv):
    """The functionality is not in 'main' so that it doesn't get executed when 
    sphinx imports it to make the documentation.  The method name starts 
    with _ so that the method is not listed in the sphinx-generated 
    documentation.
    """
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
