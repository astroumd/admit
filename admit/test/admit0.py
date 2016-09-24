#! /usr/bin/env casarun

#
#  meant to run from inside an admit directory
#  useful to test re-running
#
#  A slightly easier way to re-run, although one can also teach
#  each admit1.py style script to do the re-run.
#  If you use admit0, this is the procedure:
#
#  admit1.py foobar.fits        # this will also write an admit.apar
#  cd foobar.admit
#  $EDITOR admit.apar           # edit the parameter file
#  admit0.py                    # rerun it
#
#     
#  Warning: if an AT fails, it's quite possible the state of 
#           ADMIT is not consistent, and the next re-run would
#           result in irreproducable errors.  
#           If so, go back to step 1.
#           Also, and this is a more serious problem, if the flow
#           produces a variable number of BDPs, the static flow
#           doesn't know how to handle this, and the flow will crash.
#           If so, go back to step 1 as well.
#
# =================================================================================================================
# python system modules
import sys, os, math
# admit modules
import admit.Admit as admit
import admit.util.PlotControl as PlotControl


# open admit in the current directory
a = admit.Admit()                    

if a.new:
    m1 = "Cannot continue, there is no ADMIT project here. "
    m2 = "You need to run this from within the .admit directory"
    raise Exception,m1+m2

# test
#print "OBJECT:", a.summaryData['object']


# if you want to change the plotting characteristics for the existing flow,
# you need expert mode per AT.  
# You  can however change any new AT's with the global ADMIT plotting parameters:
# e.g.
a.plotparams(PlotControl.BATCH,PlotControl.PNG)
# a.plotparams(PlotControl.INTERACTIVE,PlotControl.PNG)

for ap in ['admit.apar']:
    if ap != "" and os.path.isfile(ap):
        print "Found parameter file ",ap
        lines = open(ap).readlines()
        for line in lines:
            exec(line.strip())

try:
    a.run()
except:
    print "some run/write error"

