#!/usr/bin/env python
#
#   example admit3 script for test0.fits
#   - re-execute fails
#   - not all tasks work yet, but those are commented out
#
import os, sys
import admit

argv = admit.utils.casa_argv(sys.argv)
#argv = sys.argv
if len(argv) < 2:
  cubefile = 'test0.fits'
  projdir = 'test0.admit'
else:
  cubefile = argv[1]
  projdir = os.path.splitext(argv[1])[0] + '.admit'

#  for now, clean up before
os.system('rm -rf %s' % projdir)

# Master project.
p = admit.Project(projdir, commit=False)

beam = {'value': 10.0, 'unit':'arcsec'}

# Flow tasks.
t0  = p.addtask(admit.Ingest_AT(file=cubefile))
t00 = p.addtask(admit.Smooth_AT(bmaj=beam, bmin=beam), [t0])
t1  = p.addtask(admit.CubeStats_AT(ppp=True), [t00])
t2  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[1]), [t00, t1])
t3  = p.addtask(admit.CubeSpectrum_AT(), [t00, t2])
t5  = p.addtask(admit.LineSegment_AT(maxgap=10, minchan=2, numsigma=10.0, csub=[0,0]), [t1, t3])
t6  = p.addtask(admit.ContinuumSub_AT(), [t00, t5])

# now on new cube  (t6,0) or t6 is the line cube     (t6,1) is the cont map
t7  = p.addtask(admit.CubeStats_AT(ppp=True), [t6])
t8  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[1]), [t6, t7])
t9  = p.addtask(admit.CubeSpectrum_AT(), [t6, t8])

if True:
  #  now "slsearch()" cannot be found
  t10  = p.addtask(admit.LineID_AT(allowexotics=True, maxgap=10, minchan=2, numsigma=8.0, recomblevel='deep',
                                   tier1width=10.0, vlsr=8.0, csub=[0,None]), [t7, t9])

  t11 = p.addtask(admit.LineCube_AT(), [t6, t10])

  t12 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t11, t7])
  t13 = p.addtask(admit.CubeSpectrum_AT(), [t11, t12])


# Update project.
p.run()
