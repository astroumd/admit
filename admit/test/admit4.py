#! /usr/bin/env casarun
#
#
#   admit4.py :  example flow to read in an ascii spectrum and run it through LineSegments and LineID
#                The spectrum needs freq (in GHz) in col1 and intensity (arbitrary units) in col5.
#
#   Usage:      $ADMIT/admit/test/admit4.py  [options] spectrum.tab
#
#   this will create a spectrum.admit directory with all the BDP's and associated data products inside.
#
#   Note that the current ADMIT will create files like testCubeSpectrum.tab, testCubeStats.tab and
#   testPVCorr.tab inside the .admit directory for you to run them through admit4.py
#
#   A typical run with 100 channels takes about 10" (fair amount of casa overhead,
#   even though none is used here; cpu in the 3 tasks is only little over 4")
#
#   time $ADMIT/admit/test/admit4.py --alias x testCubeSpectrum.tab > testCubeSpectrum.tab.log
#   7.584u 2.345s 0:10.15 97.7%	0+0k 0+2584io 0pf+0w
#   TIMING : Dtime: CubeSpectrum END [ 0.294537   0.4536109]
#   TIMING : Dtime: LineSegment END [ 2.14727     2.17343116]
#   TIMING : Dtime: LineID END [ 2.105823    2.14143705]
#
#   Options:
#   -a  alias          (doesn't actually work)
#   -r  apar_file
#   -o  output_dir
#   -s  stop_label
#
#   @todo  make it also understand bdp's
#
# =================================================================================================================
# python system modules
import sys, os, math
import argparse as ap

import admit

version  = '30-mar-2016'

#  ===>>> set some parameters for this run <<<=================================================================
#
#  !!! do not change these defaults, these are meant to be our desired defaults    !!!
#  !!! in an ideal universe. Instead, use the commented section below to enable    !!!
#  !!! them, or add your favorites to some new value to experiment with.           !!!


file     = ''               # the default FITS input name to be ingested (basename is used for apar file)
alias    = ''               # -a --alias : use a short alias instead of the possibly long basename?
apar     = ''               # -r --apar:   add this apar as well (file.apar is also checked for)
out      = ''               # -o --out:    alternative output admit name (instead of file.admit)
stop     = ''               # -s --stop:   early labeled bailout ('ingest', ...)

plot     = 't'              #
#
vlsr     = 0.0              # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
loglevel = 10               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
#
doClean  = True
lineUID  = False            # if True, this would run LineID(identifylines=False) [old relic]
linepar  = ()               # if set, (numsigma,minchan,maxgap)
llsmooth = []               # smooothing for LineSegment and LineID
iterate  = True             #
csub     = None             # or 0,1,2,....
online   = False
tier1width = 0.0            #
#
reflist  = 'etc/co_lines.list'    # pick one from $ADMIT/etc
#-----------------------------------------------------------------------------------------------------------------------
#-------------------- command line parsing -----------------------------------------------------------------------------
#                     @todo cannot overload casa, it parses first (e.g. -c)
sys.argv = admit.utils.casa_argv(sys.argv)

parser = ap.ArgumentParser(description='Process a single FITS continuum and optional PB correction')
parser.add_argument('-a','--alias' ,nargs=1, help='Alias')
parser.add_argument('-o','--out'   ,nargs=1, help='Optional output admit directory basename, instead derived from file')
parser.add_argument('-r','--apar'  ,nargs=1, help='ADMIT parameter file (in addition to "file.apar"')
parser.add_argument('-s','--stop'  ,nargs=1, help='early bailout label')
parser.add_argument('file'         ,nargs=1, help='FITSMap (or CASA image, or MIRIAD image)')
parser.add_argument('--version', action='version', version='%(prog)s ' + version)
try:
    args = vars(parser.parse_args())
except:
    sys.exit(1)

if args['file']   != None: file   = args['file'][0]
if args['alias']  != None: alias  = args['alias'][0]
if args['apar']   != None: apar   = args['apar'][0]
if args['out']    != None: out    = args['out'][0]
if args['stop']   != None: stop   = args['stop'][0]

admit.utils.assert_files([file])                # this will halt the script if something doesn't exist

#if plot == "f": 
#    plotmode=admit.PlotControl.NONE

#-----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------- start of script -----------------------------------------------

#  announce version
print 'ADMIT4: Version ',version

#  do the work in a proper ".admit" directory
adir =  admit.utils.admit_dir(file,out)
#   dirty method, it really should check if adir is an admit directory
if doClean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False


# parse apar file(s) first, overwriting local apar variables
for ap1 in ['admit4.apar', file+".apar", apar]:         # loop over 3 possible apar files, set parameters
    if ap1 != "" and os.path.isfile(ap1):
        print "Found parameter file ",ap1
        execfile(ap1)
        
a = admit.Project(adir,name='Testing ADMIT4 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    print "Starting a new ADMIT using ",file
    cmd = 'cp -a %s %s' % (sys.argv[0],adir)
    os.system(cmd)
    a.set(admit_dir=adir)
    #
    for ap in ['admit4.apar', file+".apar", apar]:         # loop over 3 possible apar files
        if ap != "" and os.path.isfile(ap):
            print "Found parameter file ",ap
            os.system('cp %s %s' % (ap,adir))
else:
    print "All done, we just read an existing admit.xml and it should do nothing"
    print "Use admit0.py to re-run inside of your admit directory"
    #
    a.fm.diagram(a.dir()+'admit.dot')
    a.show()
    a.showsetkey()
    sys.exit(0)      # doesn't work in IPython!

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)

# GenerateSpectrum
# here we use a little backdoor in GenerateSpectrum_AT that reads in
# a spectrum 
gs1 = a.addtask(admit.GenerateSpectrum_AT(file=file,seed=-1,alias=alias))
gstab1 = (gs1,0)

if stop == 'generate':  a.exit(1)

# LineSegment
ls1 = a.addtask(admit.LineSegment_AT(),[gstab1])
if len(linepar) > 0:
    a[ls1].setkey('numsigma',linepar[0])
    a[ls1].setkey('minchan', linepar[1])
    a[ls1].setkey('maxgap',  linepar[2])
a[ls1].setkey('csub',[0,csub])
a[ls1].setkey('iterate',iterate)
a[ls1].setkey('smooth',llsmooth)
lstab1 = (ls1,0)

if stop == 'segment':  a.exit(1)

# LineID
ll1 = a.addtask(admit.LineID_AT(),[gstab1])
if len(linepar) > 0:
    a[ll1].setkey('numsigma',linepar[0])
    a[ll1].setkey('minchan', linepar[1])
    a[ll1].setkey('maxgap',  linepar[2])
if lineUID:
    a[ll1].setkey('identifylines',False)
a[ll1].setkey('csub',[0,csub])
a[ll1].setkey('iterate',iterate)
a[ll1].setkey('smooth',llsmooth)
a[ll1].setkey('vlsr',vlsr)
a[ll1].setkey('references',reflist)
a[ll1].setkey('online',online)
a[ll1].setkey('tier1width',tier1width)

lltab1 = (ll1,0)

# finish off !
a.run()

a.showsetkey(adir+'/admit.apar')

