#! /usr/bin/env casarun
#
# admit-example1 version using new package style
#
#   admit-example2.py :  a second example ADMIT pipeline/flow
#
#   Usage:      $ADMIT/admit/test/admit-example2.py  [spwcube.fits [alias]] [cont.fits]
#
#   This will create a spwcube.admit directory with all the
#   BDP's and associated data products inside. Linecubes will
#   have their own directory with their associates products
#   within that directory.
#   Optionally you can give a continuum image, cont.fits
#
#   If you give an admit directory, it will try and re-run in that directory.

# ========================================================================================
# python system modules
import sys, os, math

# Always import admit!
import admit

version  = '29-oct-2015'

#  ===>>> set some parameters for this run <<<========================================================
#
file     = 'foobar.fits'    # the default FITS input name to be ingested
alias    = ''               # use a short alias instead of the possibly long basename?
cont     = ''               # add this continuum fits file to the ingestion process?
#
useMask  = True             # use a mask where fits data == 0.0
vlsr     = None             # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
maxpos   = []               # default to the peak in the cube for CubeSpectrum
clean    = True             # clean up the previous admit tree, i.e. no re-running
plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
plottype = admit.PlotControl.PNG   # output image format. PNG, JPG, etc.
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
insmooth = []               # smooth inside of Ingest_AT, in pixels
inbox    = []               # box to cut in Ingest_AT  [x0,y0,x1,y1] or [x0,y0,z0,x1,y1,z1]
inedge   = []               # edges to cut in Ingest_AT [zleft,zright]
                            # [0] and [1] are spatial
                            # [2] is frequency:    1=>Hanning  >1 Boxcar
smooth   = []               # if set, smooth the cube right after ingest
usePeak  = True             # LineCubeSpectra through peak of a Moment0 map? (else pos[] or SpwCube Peak)
pvslice  = []               # PV Slice (x0,y0,x1,y1)
pvslit   = []               # PV Slice (xc,yc,len,pa)  if none given, it will try and find out
usePPP   = True             # create and use PeakPointPlot?
useMOM   = True             # if no lines are found, do a MOM0,1,2 anyways ?
pvSmooth = [10,10]          # smooth the PVslice ?   Pos or Pos,Vel pixel numbers
robust  = ()                # Robust statistics method, () = default.
minOI    = 3                # If at least minOI linecubes present, use them in an OverlapIntegral

# placeholder until we have an official way to find the VLSR of a source
# this is a remnant from how we did this in milestone2.py
# See the file $ADMIT/etc/vlsr.tab if you want to add sources
def get_vlsr(source, vlsr=None):
    if vlsr != None : return vlsr
    vq = admit.VLSR()
    return vq.vlsr(source.upper())

def admit_dir(file):
    """ Create the admit directory name from a filename.
    This filename can be a FITS file (usually with a .fits extension
    or a directory, which would be assumed to be a CASA image or
    a MIRIAD image. It can be an absolute or relative address.
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
if len(argv) > 1:
    file  = argv[1]
    alias = ""
if len(argv) > 2:
    file  = argv[1]
    alias = argv[2]
if len(argv) > 3:
    file  = argv[1]
    alias = argv[2]
    cont  = argv[3]

#----------------------------------------------------------------------
#--------------------------- start of script --------------------------

#  announce version
print 'ADMIT2: Version ',version

#  do the work in a proper ".admit" directory
adir = admit_dir(file)
#   dirty method, it really should check if adir is an admit directory
if clean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False

a = admit.Project(adir,name='Testing ADMIT2 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    # copy the script into the admit directory
    print "Starting a new ADMIT using ",argv[0]
    os.system('cp -a %s %s' % (argv[0],adir))     
else:
    print "All done, we just read an existing admit.xml and it should do nothing"
    print "Use admit0.py to re-run inside of your admit directory"
    #
    a.fm.diagram(a.dir()+'admit.dot')
    a.show()
    a.showsetkey()
    sys.exit(0)     # doesn't work properly in IPython!

# Default ADMIT plotting environment
a.plotparams(plotmode,plottype)

# Ingest
ingest1 = a.addtask(admit.Ingest_AT(file=file,alias=alias))
a[ingest1].setkey('mask',useMask) 
a[ingest1].setkey('smooth',insmooth)
if len(inbox) > 0:
    a[ingest1].setkey('box',inbox)
if len(inedge) > 0:
    a[ingest1].setkey('edge',inedge)
bandcube1 = (ingest1,0)   

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
    bandcube1 = bandcube2


# If a continuum image was given, set up to ingest it and run
# source-find on it.
if cont != '':
    ingest2 = a.addtask(admit.Ingest_AT(file=cont,alias=alias+'-cont'))
    contmap = (ingest2,0)
    cubestats2 = a.addtask(admit.CubeStats_AT(), [contmap])
    csttab2 = (cubestats2,0)
    sfind2 = a.addtask(admit.SFind2D_AT(), [contmap,csttab2])
    cslist = (sfind2,0)
else:
    cslist = ()

# CubeStats - will also do log(Noise),log(Peak) plot
cubestats1 = a.addtask(admit.CubeStats_AT(), [bandcube1])
a[cubestats1].setkey('robust',robust)
a[cubestats1].setkey('ppp',usePPP)
csttab1 = (cubestats1,0)

# CubeSum
moment1 = a.addtask(admit.CubeSum_AT(), [bandcube1,csttab1])
a[moment1].setkey('numsigma',4.0)   # Nsigma clip in cube
# >0 force single cuberms sigma from cubestats; <0 would use rms(freq) table
a[moment1].setkey('sigma',99.0)     
csmom0 = (moment1,0)

# CubeSpectrum 
if len(maxpos) > 0:
    cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1])
    a[cubespectrum1].setkey('pos',maxpos)
elif len(cslist) > 0:
    cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1,cslist])    
else:
    cubespectrum1 = a.addtask(admit.CubeSpectrum_AT(), [bandcube1,csmom0])
csptab1 = (cubespectrum1,0)


# PVSlice
if len(pvslice) == 4:
    # hardcoded with a start,end
    slice1 = a.addtask(admit.PVSlice_AT(slice=pvslice,width=5),[bandcube1,csmom0])
elif len(pvslit) == 4:
    # hardcoded with a center,len,pa
    slice1 = a.addtask(admit.PVSlice_AT(slit=pvslit,width=5),[bandcube1,csmom0])
else:
    # use cubesum's map to generate the best slice
    slice1 = a.addtask(admit.PVSlice_AT(width=5),[bandcube1,csmom0])
    a[slice1].setkey('clip',0.3)        # TODO: this is an absolute number for mom0
    a[slice1].setkey('gamma',1.0)       # SB185 works better with gamma=4
a[slice1].setkey('smooth',pvSmooth)     # smooth, in pixel numbers
pvslice1 = (slice1,0)

corr1 = a.addtask(admit.PVCorr_AT(),[pvslice1,csttab1])
pvcorr1 = (corr1,0)


#----------- Workaround because ALMA data don't include VLSR in header -----------------
# Need to run now, since LineID_AT needs the vlsr
a.run()
a.write()
source = a.summaryData.get('object')[0].getValue()[0]
vlsr = get_vlsr(source,vlsr)
print "OBJECT = %s VLSR = ", (source, vlsr)
#---------------------------------------------------------------------------------------

# LineID uses integer segment=<STRING>:   pick ASAP or ADMIT 
lineid1 = a.addtask(admit.LineID_AT(vlsr=vlsr,segment="ADMIT"), [csptab1,csttab1,pvcorr1]) 
lltab1 = (lineid1,0)

# LineCube
linecube1 = a.addtask(admit.LineCube_AT(), [bandcube1,lltab1])
a[linecube1].setkey('grow',10)          # +growth

# RUN_1: now we need to run the flow, since we need to 
# know the number of Lines found and produce the linecubes 
# for the next for-loop.
a.run()
a.write()


nlines = len(a[linecube1])
print "Found %d lines during runtime" % nlines

x = range(nlines)    # place holder to contain mol/line
m = {}               # task id for moment on this mol/line
sp= {}               # task id for cubespectrum on this mol/line
st= {}               # task id for cubestats

# loop over all lines  
# produce moments and spectra from the linecubes just created
for i in range(nlines):
    x[i] = a[linecube1][i].getimagefile(admit.bdp_types.CASA)
    print "LineDir:", i, x[i]
    # Moment maps from the LineCube
    linecubei = (linecube1,i)
    m[x[i]] = a.addtask(admit.Moment_AT(),[linecubei,csttab1])
    print "MOMENT_AT:",m[x[i]]
    a[m[x[i]]].setkey('moments',[0,1,2])
    a[m[x[i]]].setkey('numsigma',[2.0])
    a[m[x[i]]].setkey('mom0clip',2.0)        # TODO: this is still an absolute value
    if usePeak:
        momenti0 = (m[x[i]],0)          # this linecube mom0
        # CubeSpectrum through the line cube where the mom0 map has peak
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei,momenti0])
    elif len(maxpos) > 0:
        # CubeSpectrum through the line cube at given point, 
        # use the same maxpos for all linecubes as we used before
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei])
        a[sp[x[i]]].setkey('pos',maxpos)
    else:
        # CubeSpectrum last resort, where it takes the peak from cube maximum
        sp[x[i]] = a.addtask(admit.CubeSpectrum_AT(),[linecubei,csttab1])

if useMOM and nlines == 0:
    # if no lines found, take a moment (0,1,2) over the whole cube
    moment1 = a.addtask(admit.Moment_AT(),[bandcube1,csttab1])
    a[moment1].setkey('moments',[0,1,2])
    a[moment1].setkey('numsigma',[2.0])
    a[moment1].setkey('mom0clip',2.0)       # Nsigma

# OverlapIntegral
if minOI > 0 and nlines >= minOI:
    #  would really like to take the 3 strongest lines
    print "Testing OverlapIntegral, just take the first 3 lines"
    r = (m[x[0]],0)
    g = (m[x[1]],0)
    b = (m[x[2]],0)
    oi1 = a.addtask(admit.OverlapIntegral_AT(),[r,g,b])
elif minOI > 0:
    print "Only found %d lines, need %d for OverlapIntegral" % (nlines,minOI)


# final run and save
a.run()
a.write()

# symlink resources, create dot file, and write out index.html
a.updateHTML()

