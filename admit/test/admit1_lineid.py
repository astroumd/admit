#! /usr/bin/env casarun

#  Special followup version of a previous admit1.py run where only
#  LineID needs to be run (good for quick regression testing)
#
#  All files and BDP's prior to the AT's the LineID uses can
#  be bogus links, if you want to save disk space.  (TBD)
#
#  It will also write a status flag in admit.xml, so the flow
#  can be limited to running just LineID. 
#
#
# =================================================================================================================
# python system modules
import sys, os, math
# admit modules
import admit.Admit as admit
import admit.util.PlotControl as PlotControl

#  tag which AT's are allowed, but only one should be present
valid_ats = ['LineID_AT', 'LineUID_AT']

# open admit in the current directory
a = admit.Admit()                    

if a.new:
    m1 = "Cannot continue, there is no ADMIT project here. "
    m2 = "You need to run this from within the .admit directory"
    raise Exception,m1+m2

#  to find the correct "lid", run admit1 on the foobar.admit directory
ats = a.fm.find(lambda at: at._type in valid_ats)
if len(ats) == 1:
    lid = ats[0].id()
    print "Found %s with taskid = %d" % (ats[0]._type, lid)
else:
    print "Could not find an AT in your flow with names",valid_ats
    a.exit(1)

if not a.has("test_lineid"):
    first_time = True
    # first time: remove below LineID, stale the AT itself
    print "First time running, preparing to clean the flow for regression in",a.get("admit_dir")
    a.set(test_lineid=0)
    a.fm.remove(lid,True)
    a.fm.stale(lid)
    cmd = "find . -type d -exec rm -rf '{}' \;"
    print "CMD-1:",cmd
    os.system(cmd)
else:
    # mark it stale again, so it's always running
    first_time = False
    test_lineid = a.get("test_lineid")
    a.set(test_lineid=test_lineid+1)
    a.fm.stale(lid)

### Task 6 (4): LineID_AT

# Change plotting?
# a[lid]._plot_mode = PlotControl.INTERACTIVE

# Change keywords?
# a[lid].setkey('tier1width', 0.0 )
# a[lid].setkey('minchan', 5 )
# a[lid].setkey('maxgap', 3 )
# a[lid].setkey('segment', 'ADMIT' )
#a[lid].setkey('segment', 'ASAP' )
# a[lid].setkey('idwidth', 1.0 )
# a[lid].setkey('smooth', (None,0) )
#a[lid].setkey('smooth', ('savgol', {'window_size': 7, 'order': 3, 'deriv': 0}) )
# a[lid].setkey('method', {'PeakFinder': {'min_width': 5, 'thresh': 0.0, 'min_sep': 5}} )
# a[lid].setkey('pmin', 2.0 )
#a[lid].setkey('pmin', 3.0 )
# a[lid].setkey('recombLevel', shallow )
# a[lid].setkey('mode', ONE )
# a[lid].setkey('tol', 5.0 )
# a[lid].setkey('identifyLines', True )
# a[lid].setkey('allowExotics', False )
# a[lid].setkey('vlsr', 6278.0 )

if True:
    a.run()
    a.write()
else:
    print "Doesn't work yet"
    #a[lid].execute() -> bug
    #a[lid].run()

if first_time:
    # this might be a bit tricky, the currently running script has
    # dumped a lineid_base.log in this directory, flushing should
    # be safe on most (?) systems
    aname = a.get('admit_dir')
    if aname.find('/') >= 0:
        # both /foo/bar.fits and foo/bar.fits won't work in this schema
        print "no support for subdirectories yet",aname
        a.exit(1)
    cmd   = 'cd ..;tar cf %s.tar %s' % (aname,aname)
    print 'CMD-2:',cmd
    os.system(cmd)
