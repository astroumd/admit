#! /usr/bin/env casarun
#

#   admit3.py :  process a series of admit projects with PCA
#
#   Usage:      $ADMIT/admit/test/admit3m.py  aproject p1.admit p2.admit p3.admit ....
#
#   this will create a new aproject.admit directory and search through p1,p2,p3,....
#   for moment0 maps to enter into PCA, optional smooth to a common beam.
#
# =================================================================================================================
# python system modules
import sys, os, math

import admit

version  = '29-oct-2015'

#  ===>>> set some parameters for this run <<<=================================================================
#
#  !!! do not change these defaults, these are meant to be our desired defaults    !!!
#  !!! in an ideal universe. Instead, use the commented section below to enable    !!!
#  !!! them, or add your favorites to some new value to experiment with.           !!!


plot     = 't'              #
#
useMask  = True             # use a mask where fits data == 0.0
robust   = ('hin',1.5)      # default hinges-fences
clean    = True             # clean up the previous admit tree, i.e. no re-running
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
insmooth = []               # smooth inside of Ingest_AT, in pixels
smooth   = []               # if set, smooth the cube right after ingest
inbox    = []

#robust  = ('hinge',-1)   # stats method, you need CASA 4.4 or above for this
#robust  = ('hinges-fences',1.5)          # stats method, you need CASA 4.4 or above for this
#robust  = ('fit-half','mean')            # stats method, you need CASA 4.5 or above for this
#robust  = ('fit-half','median', False)       # stats method, you need CASA 4.4 or above for this
#robust  = ('fit-half','zero')           # stats method, you need CASA 4.4 or above for this
#robust  = ('classic','tiled')            # stats method, you need CASA 4.4 or above for this
#robust  = ('chauvenet',-1)               # stats method, you need CASA 4.4 or above for 
robust  = ()
#insmooth = [10,10]           # image smooth during ingest (gaussian pixels)    BUG: Ingest works around loosing OBJECT name
#inbox = [0,200,999,800]      # 
#smooth = [10,10]             # image smooth right after ingest (Smooth_AT)     BUG: _do_plot ?
#loglevel = 20                # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
#useMask  = False
#plotmode = admit.PlotControl.INTERACTIVE


def admit_dir(file):
    """ create the admit directory name from a filename 
    This filename can be a FITS file (usually with a .fits extension
    or a directory, which would be assumed to be a CASA image or
    a MIRIAD image
    It can be an absolute or relative address
    """
    loc = file.rfind('.')
    ext = '.admit'
    if loc < 0:
        return file + ext
    else:
        if file[loc:] == ext:
            print "Warning: assuming a re-run on existing ",file
            return file
        return file[:loc] + ext


# allow a command line argument to be the fits file name, unless you have foobar.fits ;-)
argv = admit.utils.casa_argv(sys.argv)
if len(argv) < 3:
    raise Exception,"Need an admit project name, followed by one or more fits files"
file = argv[1]

if plot == "f": 
    plotmode=admit.PlotControl.NONE

#-----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------- start of script -----------------------------------------------

#  announce version
print 'ADMIT3: Version ',version

#  do the work in a proper ".admit" directory
adir = admit_dir(file)
#   dirty method, it really should check if adir is an admit directory
if clean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False

a = admit.Project(adir,name='Testing ADMIT3 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    print "Starting a new ADMIT using ",argv[0]
    os.system('cp -a %s %s' % (argv[0],adir))
    a.set(admit_dir=adir)
else:
    print "All done, we just read an existing admit.xml and it should do nothing"
    print "Use admit0.py to re-run inside of your admit directory"
    #
    a.fm.diagram(a.dir()+'admit.dot')
    a.show()
    a.showsetkey()
    #sys.exit(0)  doesn't work in IPython!

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)

pm = a.getManager()                            # get ProjectManager


bdps = []
for ap in argv[2:]:                            # loop over projects
    _p = pm.addProject(ap)
    ats = pm.findTask(_p, lambda at: type(at) == type(admit.Moment_AT()))
    print "Found %d Moment_AT's in %s" % (len(ats),ap)
    for at in ats:
        tid = a.addtask(at)                    # add the AT to the 
        bdps.append((tid,0))                   # for now, assume '0' was the mom0
        print "Moment_AT ",ap,tid,0

print "ADIR:",argv[2:]
print "Found %d BDP's" % len(bdps)
print "BDPs:",bdps


#oi1 = a.addtask(admit.OverlapIntegral_AT(),bdps)
pca = a.addtask(admit.PrincipalComponent_AT(),bdps)


# finish off !
a.run()

