#! /usr/bin/env casarun
#
#   admit-example3.py :  process a series of admit projects with PCA
#
#   Usage:      admit-example3.py  aproject p1.admit p2.admit p3.admit ....
#
#   This will create a new aproject.admit directory and search through p1,p2,p3,....
#   for moment0 maps to enter into PCA, optional smooth to a common beam.
#
# ==================================================================================
# python system modules
import sys, os, math

import admit

version  = '29-oct-2015'

#  ===>>> set some parameters for this run <<<=========================================

clean    = True             # clean up the previous admit tree, i.e. no re-running
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL


def admit_dir(file):
    """ create the admit directory name from a filename 
    This filename can be a FITS file (usually with a .fits extension
    or a directory, which would be assumed to be a CASA image or
    a MIRIAD image.  It can be an absolute or relative address
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


# Parse command line arguments
argv = admit.utils.casa_argv(sys.argv)
if len(argv) < 3:
    raise Exception,"Need an admit project name, followed by one or more FITS files"
file = argv[1]

#-------------------------------------------------------------------------------
#--------------- start of script -----------------------------------------------

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
    sys.exit(0)  #doesn't work in IPython!

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)

pm = a.getManager()                            # get ProjectManager

bdps = []
for ap in argv[2:]:                            # loop over projects
    _p = pm.addProject(ap)
    # Search for Moment_AT tasks in the projects
    ats = pm.findTask(_p, lambda at: type(at) == type(admit.Moment_AT()))
    print "Found %d Moment_AT's in %s" % (len(ats),ap)
    for at in ats:
        tid = a.addtask(at)                    # add the AT to the 
        bdps.append((tid,0))                   # for now, assume '0' was the mom0
        print "Moment_AT ",ap,tid,0

print "ADIR:",argv[2:]
print "Found %d BDP's" % len(bdps)
print "BDPs:",bdps

pca = a.addtask(admit.PrincipalComponent_AT(),bdps)

# Run the flow, write the outputs, update the web page.
a.run()
a.write()
a.updateHTML()

