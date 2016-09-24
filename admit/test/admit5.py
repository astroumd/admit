#! /usr/bin/env casarun
#
# Example multi-file admit flow, hardcoded for a specific 4-spw case
#
# REMOVE existing project directory before running script for the first time!
#
import admit

# Master project.
p = admit.Project('all-cubes.admit',commit=False)

# Flow tasks.
t0  = p.addtask(admit.Ingest_AT(file='concat.spw17.image.fits'))
t1  = p.addtask(admit.CubeStats_AT(), [t0])
t2  = p.addtask(admit.CubeSum_AT(numsigma=5.0, sigma=1.0), [t0, t1])
t3  = p.addtask(admit.CubeSpectrum_AT(alias='spec11'), [t0, t2])
t4  = p.addtask(admit.LineSegment_AT(minchan=4, maxgap=4, numsigma=6.0), [t1, t3])
t5  = p.addtask(admit.ContinuumSub_AT(fitorder=1, pad=40),[t0, t4])
t5a = p.addtask(admit.CubeStats_AT(), [t5])
t6  = p.addtask(admit.CubeSpectrum_AT(alias='spec12'), [t5, t2])
t7  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t5, t1])
t8  = p.addtask(admit.PVSlice_AT(clip=0.3, width=5), [t5, t2])
t9  = p.addtask(admit.PVCorr_AT(), [t8, t1])
t10 = p.addtask(admit.LineID_AT(csub=[1,1], minchan=3, maxgap=4, numsigma=6.0), [t5a, t6])
t11 = p.addtask(admit.LineCube_AT(pad=40), [t5, t10])
t12 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t11, t1])
t13 = p.addtask(admit.CubeSpectrum_AT(), [t11, t12])

p.run()

# Flow tasks.
t20  = p.addtask(admit.Ingest_AT(file='concat.spw19.image.fits'))
t21  = p.addtask(admit.CubeStats_AT(), [t20])
t22  = p.addtask(admit.CubeSum_AT(numsigma=4.0, sigma=1), [t20, t21])
t24  = p.addtask(admit.CubeSpectrum_AT(alias='spec13'), [t20, t22])
t26  = p.addtask(admit.LineSegment_AT(minchan=3, numsigma=4.0), [t21, t24])
t26a = p.addtask(admit.ContinuumSub_AT(fitorder=1, pad=60),[t20, t26])
t26b = p.addtask(admit.CubeSpectrum_AT(alias='spec14'), [t26a, t21])
t23  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t26a, t21])
t25  = p.addtask(admit.PVSlice_AT(clip=0.3, width=5), [t26a, t22])
t27  = p.addtask(admit.PVCorr_AT(), [t25, t21])
t28  = p.addtask(admit.LineID_AT(minchan=3, numsigma=4.0), [t21, t26b])
t29  = p.addtask(admit.LineCube_AT(pad=40), [t26a, t28])
t210 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t29, t21])
t211 = p.addtask(admit.CubeSpectrum_AT(), [t29, t210])

p.run()

# Flow tasks.
t30  = p.addtask(admit.Ingest_AT(file='concat.spw21.image.fits'))
t31  = p.addtask(admit.CubeStats_AT(ppp=True), [t30])
t32  = p.addtask(admit.CubeSum_AT(numsigma=4.0, sigma=1.0), [t30, t31])
t34  = p.addtask(admit.CubeSpectrum_AT(alias='spec5'), [t30, t32])
t36  = p.addtask(admit.LineSegment_AT(csub=[1, 1], minchan=3, numsigma=8.0), [t31, t34])
t36a = p.addtask(admit.ContinuumSub_AT(fitorder=1, pad=60),[t30, t36])
t36c = p.addtask(admit.CubeStats_AT(alias='stats2'), [t36a])
t36d = p.addtask(admit.CubeSum_AT(numsigma=4.0, sigma=1, alias='sum2'), [t36a, t36c])
t36b = p.addtask(admit.CubeSpectrum_AT(alias='spec6'), [t36a, t36d])
t33  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t36a, t36c])
t35  = p.addtask(admit.PVSlice_AT(clip=0.3, width=5), [t36a, t36d])
t37  = p.addtask(admit.PVCorr_AT(), [t35, t36c])
t38  = p.addtask(admit.LineID_AT(minchan=3, numsigma=6.0), [t36c, t36b])
t39  = p.addtask(admit.LineCube_AT(pad=60), [t36a, t38])
t310 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t39, t36c])
t311 = p.addtask(admit.CubeSpectrum_AT(), [t39, t310])
#
p.run()

# Flow tasks.
t40  = p.addtask(admit.Ingest_AT(file='concat.spw23.image.fits'))
t41  = p.addtask(admit.CubeStats_AT(), [t40])
t42  = p.addtask(admit.CubeSum_AT(numsigma=4.0, sigma=1), [t40, t41])
t44  = p.addtask(admit.CubeSpectrum_AT(alias='spec7'), [t40, t42])
t46  = p.addtask(admit.LineSegment_AT(csub=[1, 1], minchan=3, numsigma=4.0), [t41, t44])
t46a = p.addtask(admit.ContinuumSub_AT(fitorder=1, pad=60),[t40, t46])
t46b = p.addtask(admit.CubeSpectrum_AT(alias='spec8'), [t46a, t41])
t43  = p.addtask(admit.Moment_AT(mom0clip=2.0, numsigma=[3.0]), [t46a, t41])
t45  = p.addtask(admit.PVSlice_AT(clip=0.3, width=5), [t46a, t42])
t47  = p.addtask(admit.PVCorr_AT(), [t45, t41])
t48  = p.addtask(admit.LineID_AT(csub=[1, 1], minchan=3, numsigma=4.0), [t41, t46b])
t49  = p.addtask(admit.LineCube_AT(pad=40), [t46a, t48])
t410 = p.addtask(admit.Moment_AT(mom0clip=2.0, moments=[0, 1, 2]), [t49, t41])
t411 = p.addtask(admit.CubeSpectrum_AT(), [t49, t410])

p.run()
