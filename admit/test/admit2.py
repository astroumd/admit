#! /usr/bin/env casarun
#

#   admit2.py :  process continuum data, with optional repeat at lower significance
#
#   Usage:      $ADMIT/admit/test/admit2.py  [cont.fits [alias]] 
#
#   this will create a cont.admit directory with all the
#   BDP's and associated data products inside. 
#   if you want to process line+cont, use admit1.py
#
#   Options:
#   -p  pb.fits        (normally pbcor.fits is the associated PB corrrected file)
#   -a  alias
#   -r  apar_file
#   -2               
#
#   Notes:
#   - consistent with CASA's importfits(), *.fits.gz files are also handled transparently
#
#
# =================================================================================================================
# python system modules
import sys, os, math
import argparse as ap

import admit

version  = '19-dec-2017'

#  ===>>> set some parameters for this run <<<=================================================================
#
#  !!! do not change these defaults, these are meant to be our desired defaults    !!!
#  !!! in an ideal universe. Instead, use the commented section below to enable    !!!
#  !!! them, or add your favorites to some new value to experiment with.           !!!


file     = ''               # the default FITS input name to be ingested (basename is used for apar file)
basename = ''               # --basename: use a short alias basename instead of the possibly long basename?
pb       = ''               # --pb:       add if the input map was already pbcorrected, we need to undo this
apar     = ''               # --apar:     add this apar as well (file.apar is also checked for)
out      = ''               # --out:      alternative output admit name (instead of file.admit)
stop     = ''               # --stop:     early labeled bailout ('ingest', ...)

plot     = 't'              #
#
useMask  = True             # use a mask where fits data == 0.0
vlsr     = None             # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
maxpos   = []               # default to the peak in the cube for CubeSpectrum
robust   = ['hin',1.5]      # default hinges-fences
doClean  = True             # clean up the previous admit tree, i.e. no re-running
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
insmooth = []               # smooth inside of Ingest_AT, in pixels
inbox    = []               # grab subset in image
smooth   = []               # if set, smooth the cube right after ingest
smooth2  = []               # if set, smooth the cube for the 2nd run (in pixels)
numsigma = 6.0              # default 
repeat   = False            # repeat run at lower significance

#robust  = ['hinge',-1]                   # stats method, you need CASA 4.4 or above for this
#robust  = ['hinges-fences',1.5]          # stats method, you need CASA 4.4 or above for this
#robust  = ['fit-half','mean']            # stats method, you need CASA 4.5 or above for this
#robust  = ['fit-half','median', False]   # stats method, you need CASA 4.4 or above for this
#robust  = ['fit-half','zero']            # stats method, you need CASA 4.4 or above for this
#robust  = ['classic','tiled']            # stats method, you need CASA 4.4 or above for this
#robust  = ['chauvenet',-1]               # stats method, you need CASA 4.4 or above for 
robust  = []
#insmooth = [4,4]            # image smooth during ingest (gaussian pixels)    BUG: Ingest works around loosing OBJECT name
#smooth = [10,10]            # image smooth right after ingest (Smooth_AT)     BUG: _do_plot ?
#loglevel = 20               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
#useMask  = False
#plotmode = admit.PlotControl.INTERACTIVE

#-----------------------------------------------------------------------------------------------------------------------
#-------------------- command line parsing -----------------------------------------------------------------------------
#                     @todo cannot overload casa, it parses first (e.g. -c)
sys.argv = admit.utils.casa_argv(sys.argv)

parser = ap.ArgumentParser(description='Process a single FITS continuum and optional PB correction')
parser.add_argument('-p','--pb'       ,nargs=1, help='Primary Beam Correction map')
parser.add_argument('-b','--basename' ,nargs=1, help='Basename alias')
parser.add_argument('-o','--out'      ,nargs=1, help='Optional output admit directory basename, instead derived from file')
parser.add_argument('-r','--apar'     ,nargs=1, help='ADMIT parameter file (in addition to "file.apar"')
parser.add_argument('-s','--stop'     ,nargs=1, help='early bailout label')
parser.add_argument('file'            ,nargs=1, help='FITS, CASA or MIRIAD image) [extra .gz allowed]')
parser.add_argument('-2',  action="store_true", help='add repeat run with lower significance', dest='repeat', default=False)
parser.add_argument('--version', action='version', version='%(prog)s ' + version)
try:
    args = vars(parser.parse_args())
except:
    sys.exit(1)

if args['file']     != None: file     = args['file'][0]
if args['pb']       != None: pb       = args['pb'][0]
if args['basename'] != None: basename = args['basename'][0]
if args['apar']     != None: apar     = args['apar'][0]
if args['out']      != None: out      = args['out'][0]
if args['stop']     != None: stop     = args['stop'][0]

admit.utils.assert_files([file,pb])                # this will halt the script if something doesn't exist

#if plot == "f": 
#    plotmode=admit.PlotControl.NONE

#-----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------- start of script -----------------------------------------------

#  announce version
print 'ADMIT2: Version ',version

#  do the work in a proper ".admit" directory
adir =  admit.utils.admit_dir(file,out)
#   dirty method, it really should check if adir is an admit directory
if doClean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False

for ap1 in ['admit2.apar', file+".apar", apar]:         # loop over 3 possible apar files
    if ap1 != "" and os.path.isfile(ap1):
        print "Found parameter file to execfile:",ap1
        execfile(ap1)
    else:
        print "Skipping ",ap1
        
    
# open admit
a = admit.Project(adir,name='Testing ADMIT2 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    print "Starting a new ADMIT using ",file
    cmd = 'cp -a %s %s' % (sys.argv[0],adir)
    os.system(cmd)
    a.set(admit_dir=adir)
    #
    for ap1 in ['admit2.apar', file+".apar", apar]:         # loop over 3 possible apar files
        if ap1 != "" and os.path.isfile(ap1):
            print "Found parameter file to cp:",ap1
            os.system('cp %s %s' % (ap1,adir))
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

# Ingest
ingest1 = a.addtask(admit.Ingest_AT(file=file,basename=basename))
a[ingest1].setkey('mask',useMask) 
a[ingest1].setkey('smooth',insmooth)
a[ingest1].setkey('pb',pb)
if len(inbox) > 0:
    a[ingest1].setkey('box',inbox)
bandcube1 = (ingest1,0)    # output noise flat image
pbmap1 = (ingest1,1)       # output primary beam

#   need to run to see if there is a pbmap1
#   or could SFind2D for example be doing this check????
a.run()
if len(a[ingest1]) == 1:
    pbmap1 = None

if stop == 'ingest':  a.exit(1)

if len(smooth) > 0:
    smooth1 = a.addtask(admit.Smooth_AT(), [bandcube1])
    a[smooth1].setkey('bmaj',{'value':smooth[0], 'unit':'pixel'})  
    a[smooth1].setkey('bmin',{'value':smooth[1], 'unit':'pixel'})
    a[smooth1].setkey('bpa',0.0)                       
    
    bandcube2 = (smooth1,0)
    # Forget about the original, so we can continue the flow with the smoothed cube
    # in this model, it would be better to use insmooth= for Ingest_AT, it doesn't
    # need the extra space to hold bandcube1
    #
    # Another model could be to have two flows in this script, up to LineID,
    # one with each (or more) smoothing factor and decide which one to continue with
    # or do LineID with bandcube2, but make linecube's from bandcube1
    bandcube1 = bandcube2
    
    if stop == 'smooth':  a.exit(1)

# CubeStats - will also do log(Noise),log(Peak) plot
cubestats1 = a.addtask(admit.CubeStats_AT(), [bandcube1])
a[cubestats1].setkey('robust',robust)
a[cubestats1].setkey('ppp',False)
csttab1 = (cubestats1,0)

if stop == 'cubestats':  a.exit(1)

# SFind2D
if pbmap1 == None:
    sfind1 = a.addtask(admit.SFind2D_AT(), [bandcube1,csttab1])
else:
    sfind1 = a.addtask(admit.SFind2D_AT(), [bandcube1,pbmap1,csttab1])
a[sfind1].setkey('numsigma',numsigma)

if repeat:
    print "REPEAT mode on:"
    # smooth the noise-flat map

    if len(smooth2) == 0:
        beam2 = [15,15]               # wild guess, should use 2x smooth1 or else from beam
    else:
        beam2 = smooth2
        
    smooth2 = a.addtask(admit.Smooth_AT(), [bandcube1])
    a[smooth2].setkey('bmaj',{'value':beam2[0], 'unit':'pixel'})
    a[smooth2].setkey('bmin',{'value':beam2[1], 'unit':'pixel'})
    a[smooth2].setkey('bpa',0.0)                       
    
    bandcube2 = (smooth2,0)
    # Forget about the original, so we can continue the flow with the smoothed cube
    # in this model, it would be better to use insmooth= for Ingest_AT, it doesn't
    # need the extra space to hold bandcube1
    #
    # Another model could be to have two flows in this script, up to LineID,
    # one with each (or more) smoothing factor and decide which one to continue with
    # or do LineID with bandcube2, but make linecube's from bandcube1
    
    # sfind with a lower detection
    
    # CubeStats - will also do log(Noise),log(Peak) plot
    cubestats2 = a.addtask(admit.CubeStats_AT(), [bandcube2])
    a[cubestats2].setkey('robust',robust)
    a[cubestats2].setkey('ppp',False)
    csttab2 = (cubestats2,0)

    # SFind2D
    if pbmap1 == None:
        sfind2 = a.addtask(admit.SFind2D_AT(), [bandcube2,csttab2])
    else:
        sfind2 = a.addtask(admit.SFind2D_AT(), [bandcube2,pbmap1,csttab2])
    a[sfind2].setkey('numsigma',numsigma-1.0)

#OLD
#a[sfind1].setkey('numsigma',6.0)
#a[sfind1].setkey('sigma',-1.0)
#a[sfind1].setkey('robust',())
#a[sfind1].setkey('robust',('classic','auto'))
#a[sfind1].setkey('robust',('hin',1.5))
#a[sfind1].setkey('robust',('chau',-1.0))
#a[sfind1].setkey('robust',('fit-half','zero'))      # bug
#a[sfind1].setkey('snmax',40.0)

# finish off !
a.run()

a.showsetkey(adir+'/admit.apar')

