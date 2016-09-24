#! /usr/bin/env casarun
# python system modules
import sys, os, math
import argparse as ap
import datetime as dt

import admit
import matplotlib
matplotlib.use('Agg')

sys.argv = admit.utils.casa_argv(sys.argv)
parser = ap.ArgumentParser(description='Process a single FITS cube with optional continuum and PB correction')
parser.add_argument('dir'         ,nargs=1, help='FITSCube (or CASA image, or MIRIAD image)')


try:
    args = vars(parser.parse_args())
except:
    sys.exit(1)

if args['dir'] is None:
     raise Exception("Root directory must be specified")

today = dt.date.today()
date = "%i-%02i-%02i" % (today.year, today.month, today.day)
plot     = 't'              #
#
vlsr     = 0.0             # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
loglevel = 10               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL

transitions = [[["13COv=0", [110.15, 110.25], 6.0, 30.0, 5.0]],  # 0 single 13CO line

               [["CH3CNv=0",[110.21, 110.5], 8.5, 15.0, 0.0]],   # 2 Methyl cyanide cluster

               [["N2H+v=0", [93.1, 93.2], 15.5, 0.25, 0.0]],     # 4 narrow, blended hyperfines

               [["COv=0", [115.2, 115.3], 5.5, 20.0, -30.0],     # 6 galactic emission type spectrum
                ["COv=0", [115.2, 115.3], 5.0, 20.0, 30.0]],

               [["COv=0", [115.2, 115.3], 5.5, 20.0, -30.0],     # 8 P-cygni type profile
                ["COv=0", [115.2, 115.3], -5.0, 20.0, 30.0]],

                # @todo: the following one will take a long time to do the peak matching
               [["(CH3)2COv=0", [240.0,242.0], 10.0, 5.0, 0.0],  # 10 complex molecules
                ["CH3OCHOv=0", [240.0,242.0], 15.0, 3.0, 1.0],
                ["CH3CH2CNv=0", [240.0,242.0], 20.0, 5.0, 0.0],
                ["CH3OCH3", [240.0,242.0], 5.0, 5.0, 0.0],
                ["CH3OHvt=0", [240.0,242.0], 20.0, 5.0, 0.0],
                ["CH3OHvt=1", [240.0,242.0], 5.0, 5.0, 0.0]],

               [["COv=0", [115.2, 115.3], 3.0, 30.0, -40.0 ],    # 12 outflow type spectrum
                ["COv=0", [115.2, 115.3], 3.0, 30.0, 40.0 ],
                ["COv=0", [115.2, 115.3], 6.0, 8.0, 15.0 ],
                ["COv=0", [115.2, 115.3], 5.5, 8.0, -15.0 ],
                ["COv=0", [115.2, 115.3], -3.5, 8.0, 0.0 ]],

               [["CH3CH2CNv=0", [93.65,93.7], 8.0, 2.0, 0.0],
                ["CH3OCH3", [93.65, 93.7], 6.5, 2.0, 0.0]],       # 14 blended lines from different molecules

               [["H&alpha;", [99.02, 99.025], 4.0, 55.0, -10.0],
                ["CH3CHOvt=1", [99.02, 99.025], 4.0, 5.0, 0.0]],   # 16 wide and narrow blended lines

               [["N2H+v=0", [93.1, 93.2], -15.5, 0.25, 0.0]],     # 18 pure absorption

               [["NH2CHO", [102.2, 102.25], 5.5, 17.0, -40.0],
                ["NH2CHO", [102.2, 102.25], 5.0, 17.0, 40.0],
                ["CH3CCHv=0", [102.5,102.55], 30.0, 17.0, -39.0],
                ["CH3CCHv=0", [102.5,102.55], 25.0, 17.0, 39.0],
                ["H2CS", [103.0,103.1], 6.5, 17.0, -40.0],
                ["H2CS", [103.0, 103.1], 5.7, 17.0, 40.0],
                ["DNCO", [101.9,102.1], 3.5, 10.0, 39.5]],        # 20 glactic emission with multiple non-tier 1 molecules

               [["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 0.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 4.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -4.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -8.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 8.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -12.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 12.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 16.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -16.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 20.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -20.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 24.0],
                ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -24.0]],   # 22 wide plateu like line

               [["NH2CHO", [102.2, 102.25], 3.5, 8.0, 1.0],
                ["CH3CCHv=0", [102.5,102.55], 2.2, 4.0, -1.5],
                ["H2CS", [103.0, 103.1], 4.5, 5.2, 0.0],
                ["DNCO", [101.9,102.1], 3.0, 3.5, 0.5]],         # 24 few weak lines

               [["CH3OCH3", [90.935, 90.94], 12.0, 0.5, 0.1]]]    # 26 pure triplet of lines
delta = [0.5, 0.5, 0.005, 0.5, 0.5, 0.5, 0.1, 0.1, 0.2, 0.005, 0.4, 0.2, 0.5, 0.025]  #MHz
contin = [0.5, 1.3, 0.1, 3.0, 1.2, 0.5, 0.1, 1.2, 2.0, 1.0, 10.0, 3.0, 0.0, 1.5, 2.5]  #SNR
seed = [10, 25, 15, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
freq = [110.25, 110.3, 93.175, 115.271, 115.3, 241.0, 115.26, 93.68, 99.0, 93.175, 102.5, 102.52, 102.55, 90.94] #GHz
nchan = [1000, 500, 2000, 1000, 1000, 4000, 1000, 1000, 1000, 2100, 4000, 800, 4000, 1000]


projdir = "%s/%s" % (args['dir'][0], date)
print "##################  PROJECTDIR = %s  ################" % projdir

admit.util.utils.rmdir(projdir)

a = admit.Project(projdir,name='Testing LineID', create=True, loglevel=loglevel)

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)


for i in range(len(transitions)):
    spec = a.addtask(admit.GenerateSpectrum_AT(seed=seed[i], nchan=nchan[i], contin=contin[i], delta=delta[i], freq=freq[i], transitions=transitions[i], alias="test_%i" % (i)))
    bdp_in = [(spec,0)]

    lineid1 = a.addtask(admit.LineID_AT(vlsr=0.0,segment="ADMIT", csub=[1,1]), bdp_in)
    a[lineid1].setkey('numsigma',2.0)
    a[lineid1].setkey('minchan',5)
    a[lineid1].setkey('maxgap',3)    # 20 for the SB outflows
    print "################## RUNNING TRANSITION %d ######################### " % i

    # keep run() inside loop so that failures won't
    # prevent us seeing output from previous tasks in the flow
    a.run()
    # note: explicit call to a.updateHTML() is not needed -- a.run() already calls it.
