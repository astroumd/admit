#! /usr/bin/env casarun
#
#
#   admit1.py :  a toy example ADMIT pipeline/flow
#
#   Usage:      $ADMIT/admit/test/admit1.py  [options]  spwcube.fits
#
#   this will create a spwcube.admit directory with all the
#   BDP's and associated data products inside. Linecubes will
#   have their own directory with their associates products
#   within that directory.
#   Options:
#   -c  cont.fits          (not for continuum subtraction)
#   -p  pb.fits
#   -b  basename           (used to be called --alias)
#   -r  apar_file
#   -o  alternate_admit
#   -s  stop_label
#   -l  logging_level      (needs the integers)
#   -0  rerun with admit0  (really for testing only)
#
#   Notes:
#   - there are a lot of options in this script, some of them have organically
#     grown and can easily cause havoc if you combine options that were never
#     tested as such
#   - if you give an admit directory, it will try and re-run in that directory.
#     although it is suggested to use admit0.py as a template and edit this.
#   - If you create a flow with script foo.py, re-run it *only* with script foo.py,
#     never any other script (and for re-running, only limited editing of foo.py is
#     allowed even then).
#   - because of the current "/usr/bin/env casasun" interface, some of the short options
#     will be eaten by casa's parser. Use the long options to be safe
#   - consistent with CASA's importfits(), *.fits.gz files are also handled transparently
#

# =================================================================================================================
# python system modules
import sys, os, math
import argparse as ap

import admit

version  = '21-dec-2017'

#  ===>>> set some parameters for this run <<<=================================================================
#
#  !!! do not change these defaults, these are meant to be our desired defaults    !!!
#  !!! in an ideal universe. Instead, use the commented section below to enable    !!!
#  !!! them, or add your favorites to some new value to experiment with.           !!!
#  !!! or better yet, add them to your foobar.fits.apar file to override defaults  !!!
#  !!! or add a -apar APAR_FILE command line argument                              !!!


file     = ''               # the default FITS input name to be ingested (basename is used for apar file)
basename = ''               # --basename: use a short alias basename instead of the possibly long basename?
cont     = ''               # --cont:     add this continuum fits file to the ingestion process?  (??pbcor??)
pb       = ''               # --pb:       add if the input map was already pbcorrected, we need to undo this
apar     = ''               # --apar:     add this apar as well (file.apar is also checked for)
out      = ''               # --out:      alternative output admit name (instead of file.admit)
stop     = ''               # --stop:     early labeled bailout ('ingest', ...)
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL

admit0   = False            # rerun using admit0 ?

plot     = 't'              #
#
useMask  = True             # use a mask where fits data == 0.0
vlsr     = None             # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
restfreq = None             # set it to the line freq in GHz if this determined VLSRf 
maxpos   = []               # default to the peak in the cube for CubeSpectrum
robust   = ['hin',1.5]      # default hinges-fences
doClean  = True             # clean up the previous admit tree, i.e. no re-running, on a fits file
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
incontsub= []               # cont subtraction in Ingest_AT list of tuples (if set, contsub is not used) DEPRECATED
contsub  = [None]           # ContinuumSub_AT (list of tuples; only if incontsub is not used)
insmooth = []               # smooth inside of Ingest_AT, in pixels = convolving beam
inbox    = []               # box to cut in Ingest_AT  [x0,y0,x1,y1] or [x0,y0,z0,x1,y1,z1] or [z0,z1]
inedge   = []               # edges to cut in Ingest_AT [zleft,zright]
                            # [0] and [1] are spatial
                            # [2] is frequency:    1=>Hanning  >1 Boxcar
smooth   = []               # if set, smooth the cube right after ingest (list of 2 or 3 can be given, pixels) = desired beam
useSmooth = True            # use the smoothed cube for LineCube?
usePeak  = True             # LineCubeSpectra through peak of a Moment0 map? (else pos[] or SpwCube Peak)
useCSM   = False            # if usePeak, should CubeSum (CSM) be used (instead of mom0 from LineCube)
pvslice  = []               # PV Slice (x0,y0,x1,y1)
pvslit   = []               # PV Slice (xc,yc,len,pa)  if none given, it will try and find out
pvwidth  = 5                # width of a slit in PV (>1 will decrease the noise in PV)
usePV    = True             # make a PVSlice?
usePPP   = True             # create and use PeakPointPlot?
psample  = -1               # create a PeakStats plot with this spatial sampling rate (1,2,...)
useMOM   = True             # if no lines are found, do a MOM0,1,2 anyways ?
minOI    = 0                # If at least minOI linecubes present, use them in an OverlapIntegral; 0 turns off OI
pvSmooth = [10,10]          # smooth the PVslice ?   Pos or Pos,Vel pixel numbers
maxlines = -1               # limit the # linecubes? (set to 0 if you want to exit after LineID_AT)
linebdp  = [True, True, False]    #  use of [CSP,CST,PVC] for LineID?
contbdp  = [True, True]           #  use of [CSP,CST] for LineSegment
cspbdp   = [True, True, True]     #  use of [CST,CSM, SL] for initial CubeSpectrum
sources  = [0]                    #  SourceList numbers to  be used for CubeSpectrum
lineUID  = False                  # if True, this would run LineID(identifylines=False) [old relic]
lineSEG  = True                   # if True, it also runs LineSegment (aiding in automated ContinuumSub)
pad      = 5                      # padding channels for LineSegment and LineCube
linepar  = ()                     # if set, (numsigma,minchan,maxgap); both LineSegment and LineID
tier1width = 0.0                  # lineID
iterate  = True                   # iterate to find narrower higher S/N peaks
online   = False                  # use splatalogue online?
reflist  = 'etc/tier1_lines.list' # pick one from $ADMIT/etc 
llsmooth = []                     # if set, apply this smoothing to the inputs for LineSegment and LineId
numsigma = 4.0

# -- above here are sensible default meant to automate a flow. Don't edit them above this line --
# -- below here you can tinker with some of the above reasonable defaults                      --
#maxpos   = [174,160]           # N253.ce cubes
#maxpos   = get_pos(6)+get_pos(5)     # the RA,DEC positions from table in Meier et al. (use 1..10 here, 0 to disable)
#maxpos   = [170,170,160,160]   # two positions 
#maxpos   = [70,105,100,107]    # test21.fits
#robust  = ['hinge',-1]                   # stats method, you need CASA 4.4 or above for this
#robust  = ['hinges-fences',1.5]          # stats method, you need CASA 4.4 or above for this
#robust  = ['fit-half','mean']            # stats method, you need CASA 4.5 or above for this
#robust  = ['fit-half','median', False]   # stats method, you need CASA 4.4 or above for this
#robust  = ['fit-half','zero']            # stats method, you need CASA 4.4 or above for this
#robust  = ['classic','tiled']            # stats method, you need CASA 4.4 or above for this
#robust  = ['chauvenet',-1]               # stats method, you need CASA 4.4 or above for 
robust  = []
#pvslice = [78.5,227.1,270.4,100.1]    # n253.ce slice (start,end)
#pvslice = [8.18218,129,103,19.5053]   # test21 after Ingest_AT:setkey('box',[35,21,144,156])             # test21,22,23
#pvslice = [93.6705,6,17.6295,129]     # test22
#pvslice = [6,119.735,103,14.7013]     # test23
#pvslit = [174.0,163.0,250.0,57.0]    # n253.ce slit (center,len,pa)
# pvslit = [158,173,250,57]           # right on pos=#7
#pvslice = [10,10,90,90]    # 
#### N6503:  17h49m26.4s +70d08m40s 
#pvslit = [162,122,360,120.0]       # N6503-1996 VLA data len=415?
#pvslit = [128,128,200,120.0]       # N6503-1983 VLA data len=285?
#pvslit = [248,242,300,57.0]        # sb185 along a disk?
#pvslice = [104,13,141,187]         # Bittle ic10
#
#pvSmooth = []
#
#inbox = [0,0,10,99,99,20]          # blc trc in 3D
#inbox = [0,0,10,99,99,20]          # blc trc in 3D
#inbox = [200,200,300,300]          # blc trc in 2D, take all channels?
#inbox = [85,85,255,255]            # blc trc in 2D, take all channels?    spw1 proof for pvslice
#inbox = [10,10,20,20]              # blc trc in 2D, take all channels?    spw1 proof for pvslice
#inbox = [200,200,320,320]          # blc trc in 2D, take all channels?    spw1 proof for 
#inbox = [0,0,13,370,250,77]        # n6503 narrow test
#inbox = [10,10,10,20,20,20]
#inbox = [1,49]
#inbox = [0,198]                    # test83.fits (HD163296_CO_2_1.image.fits)  (works on all HD's)
#inbox = [10,10,20,20]
#inbox = [35,21,144,156]            # tighter view in test21,22,23 for a demo
#inbox = [45,32,56,42]              # tighter view in NGC2480
#inbox = [27,27,76,76]              # tighter view in NGC2480
#inbox = [10,10,10,350,240,80]

#insmooth = [0,0,1]          # image smooth during ingest (gaussian pixels)    BUG: Ingest works around loosing OBJECT name
#insmooth = [4,4,1]          # image smooth during ingest (gaussian pixels, hannning in freq)
#insmooth = [1,1,3]           # image smooth during ingest (gaussian pixels, hannning in freq)

#insmooth = [0,0,1]          # image smooth during ingest (gaussian pixels)    BUG: Ingest works around loosing OBJECT name
#insmooth = [4,4,4]          # image smooth during ingest (gaussian pixels, hannning in freq)
#smooth = [10,10]            # image smooth right after ingest (Smooth_AT)
#
#llsmooth = ['savgol',7,3,0]  # window_size,odd order of the poynomial fit,number of the derivative to compute (0 = just smooth)
#llsmooth = ['boxcar',3]      # Number of channels to average together
#llsmooth = ['gaussian',7]    # Number of channels to span with the gaussian
#llsmooth = ['hanning',5]     # Number of channels to include in the cos
#llsmooth = ['triangle',5]    # Number of channels to span with the triangle
#llsmooth = ['welch',5]       # Number of channels to use in the function
#
#vlsr = 6.9                  # test1 will not detect it at 6.9, but ok at 7.0
#pvwidth  = 1
#usePeak = False
#useCSM  = True
#useMask  = False
#useMOM = False
#usePPP = False
#plotmode = admit.PlotControl.INTERACTIVE

pvwidth = 5

# given as example here, you would stick this in your personal .apar file for your object(s)
def get_pos(i):
    """ return key positions in N253 (1..10) from Meier's Table 2:
         0 = blank, if you want to use the peak in the cube
        11 = map center, the reference position of N253
    """
    pos = [ [],                                     # 0 = blank
            ['00h47m33.041s',	'-25d17m26.61s'	],  # pos 1
            ['00h47m32.290s',	'-25d17m19.10s'	],  #     2
            ['00h47m31.936s',	'-25d17m29.10s'	],  #     3
            ['00h47m32.792s',	'-25d17m21.10s'	],  #     4
            ['00h47m32.969s',	'-25d17m19.50s'	],  #     5
            ['00h47m33.159s',	'-25d17m17.41s'	],  #     6
            ['00h47m33.323s',	'-25d17m15.50s'	],  #     7
            ['00h47m33.647s',	'-25d17m13.10s'	],  #     8
            ['00h47m33.942s',	'-25d17m11.10s'	],  #     9
            ['00h47m34.148s',	'-25d17m12.30s'	],  # pos 10
            ['00h47m33.100s',   '-25d17m17.50s' ],  # map reference 
          ]
    return pos[i]

#maxpos   = get_pos(1)+get_pos(2)+get_pos(3)+get_pos(4)+get_pos(5)+get_pos(6)+get_pos(7)+get_pos(8)+get_pos(9)+get_pos(10)
# 0:47:33.317 -25.17.15.926 = pos 7

#-----------------------------------------------------------------------------------------------------------------------
#-------------------- command line parsing -----------------------------------------------------------------------------
#                     @todo cannot overload casa, it parses first (e.g. -c)
sys.argv = admit.utils.casa_argv(sys.argv)
parser = ap.ArgumentParser(description='Process a single FITS cube with optional continuum and PB correction')
parser.add_argument('-p','--pb'        ,nargs=1, help='Primary Beam Correction cube')
parser.add_argument('-c','--cont'      ,nargs=1, help='Continuum map')
parser.add_argument('-b','--basename'  ,nargs=1, help='Basename alias')
parser.add_argument('-o','--out'       ,nargs=1, help='Optional output admit directory basename, instead derived from file')
parser.add_argument('-r','--apar'      ,nargs=1, help='ADMIT parameter file (in addition to "file.apar"')
parser.add_argument('-s','--stop'      ,nargs=1, help='early bailout label')
parser.add_argument('-l','--loglevel'  ,nargs=1, help='logging level [20]')
parser.add_argument('-0','--admit0'    ,action='store_true', help='Rerun using admit0?')
parser.add_argument('file'             ,nargs=1, help='FITS, CASA or MIRIAD image) [extra .gz allowed]')
parser.add_argument('--version', action='version', version='%(prog)s ' + version)
try:
    args = vars(parser.parse_args())
except:
    sys.exit(1)

if args['file']     != None: file     = args['file'][0]
if args['pb']       != None: pb       = args['pb'][0]
if args['cont']     != None: cont     = args['cont'][0]
if args['basename'] != None: basename = args['basename'][0]
if args['apar']     != None: apar     = args['apar'][0]
if args['out']      != None: out      = args['out'][0]
if args['stop']     != None: stop     = args['stop'][0]
if args['loglevel'] != None: loglevel = int(args['loglevel'][0])
admit0 = args['admit0']

admit.utils.assert_files([file,pb,cont])                # this will halt the script if something doesn't exist

#-----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------- start of script -----------------------------------------------

#  announce version
print 'ADMIT1: Version ',version,'loglevel ',loglevel

#  do the work in a proper ".admit" directory
adir = admit.utils.admit_dir(file,out)
#  dirty method, it really should check if adir is an admit directory
if doClean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False

if admit0:
    run_admit0 = adir + '/' + 'admit0.py'    

# parse apar file(s) first, overwriting local apar variables
for ap1 in ['admit1.apar', file+".apar", apar]:         # loop over 3 possible apar files, set parameters
    if ap1 != "" and os.path.isfile(ap1):
        print "Found parameter file to execfile",ap1
        execfile(ap1)
    else:
        print "Skipping ",ap1

# open admit
a = admit.Project(adir,name='Testing ADMIT1 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    print "Starting a new ADMIT using",file
    cmd = 'cp -a %s %s' % (sys.argv[0],adir)               # copy the script into the admit directory (@todo is that right one?)
    os.system(cmd)
    a.set(admit_dir=adir)                                  # why was this again?
    #
    for ap in ['admit1.apar', file+".apar", apar]:         # loop over 3 possible apar files, backup copy
        if ap != "" and os.path.isfile(ap):
            print "Found parameter file to cp:",ap
            os.system('cp %s %s' % (ap,adir))
else:
    print "All done, we just read an existing admit.xml and it should do nothing"
    print "Use admit0.py to re-run inside of your admit directory"
    #
    a.fm.diagram(a.dir()+'admit.dot')
    a.show()
    a.showsetkey()
    sys.exit(0)     # doesn't work properly in IPython, leaves the user with a confusing mess

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)

# ingest
ingest1 = a.addtask(admit.Ingest_AT(file=file,basename=basename))
a[ingest1].setkey('mask',useMask) 
a[ingest1].setkey('pb',pb)
a[ingest1].setkey('smooth',insmooth)
if vlsr != None:
    a[ingest1].setkey('vlsr',vlsr)
if restfreq != None:
    a[ingest1].setkey('restfreq',restfreq)
if len(inbox) > 0:
    a[ingest1].setkey('box',inbox)
if len(inedge) > 0:
    a[ingest1].setkey('edge',inedge)
bandcube1 = (ingest1,0)

if False:
    # test File_AT:
    file1 = a.addtask(admit.File_AT(file=file))

if stop == 'ingest':  a.exit(1)

# smooth
if len(smooth) > 0:
    smooth1 = a.addtask(admit.Smooth_AT(), [bandcube1])
    a[smooth1].setkey('bmaj',{'value':smooth[0], 'unit':'pixel'}) 
    a[smooth1].setkey('bmin',{'value':smooth[1], 'unit':'pixel'})
    a[smooth1].setkey('bpa',0.0)                       
    if len(smooth) > 2:
        a[smooth1].setkey('velres',{'value':smooth[2], 'unit':'pixel'})
    
    bandcube2 = (smooth1,0)
    # Forget about the original, so we can continue the flow with the smoothed cube
    # in this model, it would be better to use insmooth= for Ingest_AT, it doesn't
    # need the extra space to hold bandcube1
    #
    # Another model could be to have two flows in this script, up to LineID,
    # one with each (or more) smoothing factor and decide which one to continue with
    # or do LineID with bandcube2, but make linecube's from bandcube1
    bandcube1_orig = bandcube1
    bandcube1 = bandcube2

    if stop == 'smooth':  a.exit(1)
else:    
    bandcube1_orig = ()


# ingest-cont:  only used for source finding for CubeSpectrum, this map is not used
#               to subtract the continuum, since there is no guarentee about the
#               resolution ('cont' maps usually mismatch, 'mfs' maps are ok but not
#               part of the ALMA pipeline
if cont != '':
    # @todo   note we don't have an option here to do pb?
    ingest2 = a.addtask(admit.Ingest_AT(file=cont,basename=basename,alias='sfcont'))
    contmap = (ingest2,0)
    a.run()
    #
    cubestats2 = a.addtask(admit.CubeStats_AT(), [contmap])
    #a[cubestats1].setkey('robust',robust)
    csttab2 = (cubestats2,0)
    sfind2 = a.addtask(admit.SFind2D_AT(), [contmap,csttab2])
    cslist = (sfind2,0)
    a.run()
    ncs = len(a[cslist[0]][0])
    print "N Cont sources in ingested contmap :",ncs
    if ncs == 0:
        cslist = ()
else:
    cslist = ()

# cubestats
cubestats1 = a.addtask(admit.CubeStats_AT(), [bandcube1])
a[cubestats1].setkey('robust',robust)
a[cubestats1].setkey('ppp',usePPP)
a[cubestats1].setkey('psample',psample)
csttab1 = (cubestats1,0)

if stop == 'cubestats':  a.exit(1)


# CubeSum
moment1 = a.addtask(admit.CubeSum_AT(), [bandcube1,csttab1])
a[moment1].setkey('numsigma',4.0)   # Nsigma clip in cube
a[moment1].setkey('sigma',99.0)     # >0 force single cuberms sigma from cubestats
#a[moment1].setkey('sigma',-1.0)    # use rms(freq) table
a[moment1].setkey('pad',pad)  
csmom0 = (moment1,0)

if False:
    # testing Export_AT()
    fits000 = a.addtask(admit.Export_AT(basename="testCubeSum"), [csmom0])

if stop == 'cubesum':  a.exit(1)    

# SFind2D on CSM 
if True:
    # @todo this would crash on mom0 (CAS-8616; now fixed in rev 37066)
    # @todo better sigma in csmom0??? 
    try:
        sfind1 = a.addtask(admit.SFind2D_AT(alias='csm'), [csmom0])
        a[sfind1].setkey('numsigma',numsigma)
        a.run()
        ncs = len(a[sfind1][0])
        print "N sources in CSM:",ncs
        if ncs > 0:
            cslist = (sfind1,0)
    except:
        print "SFind2D failed on the CSM map... Continuing on"
    # PJT testing
    # a.exit(1)

# CubeSpectrum
if len(maxpos) > 0:
    cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1])
    a[cubespectrum1].setkey('pos',maxpos)
else:
    bdp_in = [bandcube1]
    if cspbdp[0] and len(csttab1) > 0: bdp_in.append(csttab1)
    if cspbdp[1] and len(csmom0)  > 0: bdp_in.append(csmom0)
    if cspbdp[2] and len(cslist)  > 0: bdp_in.append(cslist)     # could be CONT or CSM
    #print "CSP: using %d bpd's" % (len(bdp_in))
    #print "BDP_IN",bdp_in
    cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), bdp_in)
    a[cubespectrum1].setkey('sources',sources)
     
csptab1 = (cubespectrum1,0)

if stop == 'cubespectrum':  a.exit(1)    

# Find line segments from cubestats and/or cubespect
# For SD maps cubestats should not be used, since there is a false (negative) continuum
if lineSEG:
    bdp_in = []
    if contbdp[0]:  bdp_in.append(csptab1)  # CubeSpectrum
    if contbdp[1]:  bdp_in.append(csttab1)  # CubeStats
    segment1 = a.addtask(admit.LineSegment_AT(),bdp_in)
    if len(linepar) > 0:
        a[segment1].setkey('numsigma',linepar[0])
        a[segment1].setkey('minchan', linepar[1])
        a[segment1].setkey('maxgap',  linepar[2])
    else:
        a[segment1].setkey('numsigma',5.0)
        a[segment1].setkey('minchan',4)
        a[segment1].setkey('maxgap',3)
    #a[segment1].setkey('csub',[1,1])
    a[segment1].setkey('csub',[0,0])
    a[segment1].setkey('smooth',llsmooth)
    a[segment1].setkey('iterate',iterate)
    lstab1 = (segment1, 0)
    a.run()

    nsegments = len(a[lstab1[0]][0])
    print "Found %d segments in LineSegment" % nsegments
    
    if stop == 'linesegments':  a.exit(1)    
else:
    nsegments = 0


# ContinuumSub 
if (len(contsub)>0 and contsub[0]==None) or nsegments == 0:
    print "No ContinuumSub needed"
else:
    bdp_in = [bandcube1]
    if len(contsub) == 0:
        bdp_in.append(lstab1)
    csub1 = a.addtask(admit.ContinuumSub_AT(alias="cs"), bdp_in)
    if len(contsub) > 0:        
        a[csub1].setkey('contsub',contsub)
    a[csub1].setkey('pad',pad)
    bandcube3 = (csub1,0)
    contmap3  = (csub1,1)
    # continue with this new linecube
    bandcube1 = bandcube3

    # cubestats on the contmap3, and SFind2D
    if True:
        cubestats2 = a.addtask(admit.CubeStats_AT(alias='cscont'), [contmap3])
        #a[cubestats2].setkey('robust',robust)
        csttab2 = (cubestats2,0)
        sfind2 = a.addtask(admit.SFind2D_AT(alias='sfcont'), [contmap3,csttab2])
        cslist = (sfind2,0)
        a.run()
        ncs = len(a[cslist[0]][0])
        print "N Cont sources in contmap :",ncs
        if ncs == 0:
            cslist = ()


    # new cubestats
    cubestats1 = a.addtask(admit.CubeStats_AT(alias='line'), [bandcube1])
    a[cubestats1].setkey('robust',robust)
    a[cubestats1].setkey('ppp',usePPP)
    a[cubestats1].setkey('psample',psample)    
    csttab1 = (cubestats1,0)

    # new CubeSum
    moment1 = a.addtask(admit.CubeSum_AT(), [bandcube1,csttab1])
    a[moment1].setkey('numsigma',4.0)
    a[moment1].setkey('sigma',99.0)
    csmom0 = (moment1,0)

    if nsegments > 0:
        # @todo   if no segments found, but still doing a manual contsub=[] this doesn't work
        # testing-a: show the "line", with clipping
        moment1a = a.addtask(admit.CubeSum_AT(alias='test_line'), [bandcube1,csttab1,lstab1])
        a[moment1a].setkey('numsigma',4.0)
        a[moment1a].setkey('sigma',99.0)
        a[moment1a].setkey('linesum',True)
        a[moment1a].setkey('pad',pad)
        
        # testing-b:  show the "continuum", no clipping, and following sigma(freq) as test
        moment1b = a.addtask(admit.CubeSum_AT(alias='test_cont'), [bandcube1,csttab1,lstab1])
        a[moment1b].setkey('numsigma',0.0)
        a[moment1b].setkey('sigma',-1.0)
        a[moment1b].setkey('linesum',False)
        a[moment1b].setkey('pad',pad)
    else:
        # @todo   cubesum needs 
        print "No test maps produced since no segments were found"


    # new CubeSpectrum
    # @todo  clone the method from above here as well
    if len(maxpos) > 0:
        cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1])
        a[cubespectrum1].setkey('pos',maxpos)
    elif len(cslist) > 0:
        cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1,cslist])    
    else:
        #cubespectrum1 = a.addtask(CubeSpectrum_AT(), [bandcube1,csttab1])
        cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1,csmom0])
    csptab1 = (cubespectrum1,0)

    if stop == 'contsub':  a.exit(1)    

if usePV:        
    # PVSlice
    if len(pvslice) == 4:
        # hardcoded with a start,end
        slice1 = a.addtask(admit.PVSlice_AT(slice=pvslice,width=pvwidth),[bandcube1,csmom0])
    elif len(pvslit) == 4:
        # hardcoded with a center,len,pa
        slice1 = a.addtask(admit.PVSlice_AT(slit=pvslit,width=pvwidth),[bandcube1,csmom0])
    else:
        # use cubesum's map to generate the best slice
        # the PPP method didn't seem to work so well yet, and is slow, so still commented out here
        #slice1 = a.addtask(PVSlice_AT(width=5),[bandcube1,csttab1])     <--  BUG with summary needed a figure CSM style input makes
        slice1 = a.addtask(admit.PVSlice_AT(width=pvwidth),[bandcube1,csmom0])
    a[slice1].setkey('clip',2.0)            # this is like a numsigma factor (sigma determined internally)
    a[slice1].setkey('gamma',1.0)           # SB185 works better with gamma=4
    a[slice1].setkey('pvsmooth',pvSmooth)   # pvsmooth, in pixel numbers
    pvslice1 = (slice1,0)

    if stop == 'pvslice':  a.exit(1)

    corr1 = a.addtask(admit.PVCorr_AT(),[pvslice1,csttab1])
    #a[corr1].setkey('chans',[530,584])     # this is automated, but here you pick a channel range line
    #a[corr1].setkey('nchan',10)
    #a[corr1].setkey('numsigma',3.0)
    pvcorr1 = (corr1,0)

    if stop == 'pvcorr':  a.exit(1)

a.run()
source = a.summaryData.get('object')[0].getValue()[0]
print "OBJECT = ", source

# lineID  
bdp_in = []
if linebdp[0]:  bdp_in.append(csptab1)
if linebdp[1]:  bdp_in.append(csttab1)
if linebdp[2]:  bdp_in.append(pvcorr1)
if vlsr == None:
    # let vlsr be inherited by the Summary
    lineid1 = a.addtask(admit.LineID_AT(), bdp_in)
else:
    # @todo  problem: vlsr is also in the Summary, and can be different from this vlsr
    lineid1 = a.addtask(admit.LineID_AT(vlsr=vlsr), bdp_in)

# hidden!!
#a[lineid1].boxcar  = False
#
if lineUID:
    a[lineid1].setkey('identifylines',False)
#a[lineid1].setkey('recomblevel','OFF')
#a[lineid1].setkey('recomblevel','DEEP')
if len(linepar) > 0:
    a[lineid1].setkey('numsigma',linepar[0])     # 5.0
    a[lineid1].setkey('minchan', linepar[1])     # 4
    a[lineid1].setkey('maxgap',  linepar[2])     # 3
#a[lineid1].setkey('mode','ALL')
a[lineid1].setkey('smooth',llsmooth)
a[lineid1].setkey('tier1width',tier1width)
#a[lineid1].setkey('pattern','AUTO')
a[lineid1].setkey('iterate',iterate)
a[lineid1].setkey('csub',[0, 0])
a[lineid1].setkey('online',online)
a[lineid1].setkey('references',reflist)

lltab1 = (lineid1,0)

a.run()

if stop == 'lineid':  a.exit(1)    

nlines = len(a[lltab1[0]][0])
print "Found %d lines in LineID" % nlines

# special case, exit here if you don't want any linecubes
if maxlines == 0:
    print "maxlines=0; no linecube's will be produced - end of admit1"
    a.exit(1)

#
if len(bandcube1_orig) > 0 and not useSmooth: bandcube1 = bandcube1_orig
# LineCube
linecube1 = a.addtask(admit.LineCube_AT(), [bandcube1,lltab1])
a[linecube1].setkey('pad',pad)         # +growth on either side

#a.exit(1)

# RUN_1: now we need to run the flow, since we need to 
# know the number of Lines found and produce the linecubes 
# for the next for-loop.
a.run()

nlines = len(a[linecube1])
print "Found %d lines in LineCube" % nlines

if stop == 'linecube':  a.exit(1)    


x = range(nlines)    # place holder to contain mol/line
m = {}               # task id for moment on this mol/line
sp= {}               # task id for cubespectrum on this mol/line
st= {}               # task id for cubestats

# loop over all lines  
# produce moments and spectra from the linecubes just created
for i in range(nlines):
    x[i] = a[linecube1][i].getimagefile()
    print "LineDir:", i, x[i]
    # Moment maps from the LineCube
    linecubei = (linecube1,i)
    m[x[i]] = a.addtask(admit.Moment_AT(),[linecubei,csttab1])
    print "MOMENT_AT:",m[x[i]]
    a[m[x[i]]].setkey('moments',[0,1,2])
    #a[m[x[i]]].setkey('moments',[0])
    #a[m[x[i]]].setkey('cutoff',[2.0,3.0,3.0])
    a[m[x[i]]].setkey('numsigma',[2.0])
    a[m[x[i]]].setkey('mom0clip',2.0)
    if usePeak:
        if useCSM:
            momenti0 = csmom0               # CubeSum mom0
        else:
            momenti0 = (m[x[i]],0)          # this linecube mom0
        # CubeSpectrum through the line cube where the mom0 map has peak
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei,momenti0])
    elif len(maxpos) > 0:
        # CubeSpectrum through the line cube at given point, 
        # use the same maxpos for all linecubes as we used before
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei])
        a[sp[x[i]]].setkey('pos',maxpos)
        # CubeStats
        st[x[i]] = a.addtask(admit.CubeStats_AT(),[linecubei])        
    else:
        # CubeSpectrum last resort, where it takes the peak from cube maximum
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei,csttab1])

if useMOM:
    if nlines == 0:
        # if no lines found, take a moment (0,1,2) over the whole cube
        moment1 = a.addtask(admit.Moment_AT(),[bandcube1,csttab1])
        a[moment1].setkey('moments',[0,1,2])
        a[moment1].setkey('numsigma',[2.0])
        a[moment1].setkey('mom0clip',2.0)       # Nsigma
    else:
        # if lines were found, do a moment 0, so we get the flux (table) plot
        moment1 = a.addtask(admit.Moment_AT(),[bandcube1,csttab1])
        a[moment1].setkey('moments',[0])
        a[moment1].setkey('numsigma',[3.0])
        a[moment1].setkey('mom0clip',2.0)       # Nsigma

# OverlapIntegral and PrincipalComponent
if minOI > 0 and  nlines >= minOI:
    print "Testing OverlapIntegral, just take the strongest 3 lines"
    fluxlist = a.summaryData.getLinefluxes()
    print "GOT %d FLUXES IN LIST" % len(fluxlist)
    fluxes = []
    for line in fluxlist:
        fluxes.append((fluxlist[line],line))
    print "FLUXES0::",fluxes
    fluxes = sorted(fluxes,reverse=True)
    print "FLUXES1::",fluxes
    print fluxes[0]
    print fluxes[1]
    print fluxes[2]
    r = (m[fluxes[0][1]],0)
    g = (m[fluxes[1][1]],0)
    b = (m[fluxes[2][1]],0)
    oi1 = a.addtask(admit.OverlapIntegral_AT(),[r,g,b])
    pca1 = a.addtask(admit.PrincipalComponent_AT(),[r,g,b])
elif minOI > 0:
    print "Only found %d lines, need %d for OverlapIntegral" % (nlines,minOI)


# final run and save
a.run()

#a.showsetkey(adir+'/admit.apar')

if admit0:
    print "RE-RUN: ",run_admit0
    os.system(run_admit0)
