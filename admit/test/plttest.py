#!/usr/bin/env python

import admit
from admit.AT import AT
import admit.Admit as admit
import admit.util.bdp_types as bt
import admit.util.PlotControl as pc

# AT's we need (we normally don't need BDP's in user code such as this)
from admit.at.Flow11_AT import Flow11_AT
from admit.at.File_AT import File_AT

a = admit.Admit("/tmp",name='testing plot type inheritance')
a.plotparams(pc.NOPLOT,pc.PNG)
f1 = File_AT(file="/tmp/deleteme_1",touch=False,exist=False)
at1 = a.addtask(f1)
f2=Flow11_AT(file="/tmp/deleteme_2",touch=False,exist=False)
at2 = a.addtask(f2,[(at1,0)])
a.plotparams(pc.INTERACTIVE,pc.PDF)
f3=Flow11_AT(file="/tmp/deleteme_3",touch=False,exist=False)
at3 = a.addtask(f3 , [(at2,0)])
a.run()
print "F1: plotmode = %d plottype = %d" % (f1._plot_mode,f1._plot_type)
print "F2: plotmode = %d plottype = %d" % (f2._plot_mode,f2._plot_type)
print "F3: plotmode = %d plottype = %d" % (f3._plot_mode,f3._plot_type)

