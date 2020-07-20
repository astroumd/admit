#!/usr/bin/env python
#
# This is essentially the admit0.py for "runa1 test0.fits", in the new python3 style
# In true ADMIT3 python has to execute this, in CASA5 style, the 'casarun' wrapper
# needs to run this.
#
#  - always cleans up the admit folder since re-run not working in P3 yet
#  - no aliases, not working in P3 yet
#

import os, sys
import admit

# Command line processing.
argv = admit.utils.casa_argv(sys.argv)
if len(argv) < 2:
  cubefile = 'test0.fits'
  projdir = 'test0.admit'
else:
  cubefile = argv[1]
  projdir = os.path.splitext(argv[1])[0] + '.admit'

#  for now, clean up before
os.system('rm -rf %s' % projdir)

# Master project.
p = admit.Project(projdir, commit=False, loglevel=15)

# Flow tasks.
t0  = p.addtask(admit.Ingest_AT(basename='x', file=cubefile))
t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t0])
t2  = p.addtask(admit.CubeSum_AT(numsigma=4.0, sigma=99.0), [t0, t1])
t3  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t0, t1])
t4  = p.addtask(admit.SFind2D_AT(numsigma=4.0, sigma=2.573442400847699), [t2])
t5  = p.addtask(admit.PVSlice_AT(clip=2.0, pvsmooth=[10, 10], width=5), [t0, t2])
t6  = p.addtask(admit.CubeSpectrum_AT(), [t0, t1, t2, t4])
t7  = p.addtask(admit.PVCorr_AT(), [t5, t1])
t8  = p.addtask(admit.LineSegment_AT(csub=[0, 0]), [t6, t1])
t9  = p.addtask(admit.LineID_AT(csub=[0, 0], references='etc/tier1_lines.list'), [t6, t1])
t10 = p.addtask(admit.LineCube_AT(), [t0, t9])
t11 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t10, t1])
t12 = p.addtask(admit.CubeSpectrum_AT(), [t10, t11])

# Update project.
p.run()
