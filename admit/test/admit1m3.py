#! /usr/bin/env casarun
#
#
#   admit1.py :  an example ADMIT pipeline/flow for line cubes with an optional continuum map
#
#   Usage:      $ADMIT/admit/test/admit1.py  [line.fits [alias]] [cont.fits]
#
#   this will create a line.admit directory with all the
#   BDP's and associated data products inside. Linecubes will
#   have their own directory with their associates products
#   within that directory.
#   Optionally you can give a continuum image, cont.fits, but it
#   is currently not used for much.
#
#   if you give an admit directory, it will try and re-run in that directory.
#   although it is suggested to use admit0.py as a template, edit this,
#   and re-run ADMIT to compute different instances of the flow

version  = '30-jul-2015'

#  ===>>> set some parameters for this run <<<=================================================================

file     = 'foobar.fits'    # the default FITS input name to be ingested
cont     = ''               # add this continuum fits file to the ingestion process?
useMask  = True             # use a mask where fits data == 0.0
alias    = ''               # use a short alias instead of the possibly long basename?
vlsr     = None             # either set it below, or make get_vlsr() to work (else vlsr=0 will be used)
maxpos   = []               # default to the peak in the cube for CubeSpectrum
robust   = ('hin',1.5)      # default hinges-fences
clean    = True             # clean up the previous admit tree, i.e. no re-running
plotmode = 0                # 0=batch   1=interactive   2=interactive at the very end of all plots
plottype = 'png'            # jpg, png, svg, ....(standard matplotlib options)
loglevel = 15               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
usePeak  = True             # LineCubeSpectra through peak of a Moment0 map? (else pos[] or SpwCube Peak)
useCSM   = False            # if usePeak, should CubeSum (CSM) be used (instead of mom0 from LineCube)
pvslice  = []               # PV Slice (x0,y0,x1,y1)
pvslit   = []               # PV Slice (xc,yc,len,pa)  if none given, it will try and find out
useUID   = False            # True = LineUID is more robust, but no real lineID  
usePPP   = True             # create and use PeakPointPlot?
useMOM   = True             # if no lines are found, do a MOM0,1,2 anyways ?
pvSmooth = [10,10]          # smooth the PVslice ?   Pos or Pos,Vel pixel numbers

# =================================================================================================================
# python system modules
import sys, os, math

# essential admit modules
from admit.AT import AT
import admit.Admit as admit
import admit.util.bdp_types as bt

# AT's we need (we normally don't need BDP's in user code such as this)
from admit.at.Ingest_AT        import Ingest_AT
from admit.at.CubeStats_AT     import CubeStats_AT
from admit.at.CubeSpectrum_AT  import CubeSpectrum_AT
from admit.at.CubeSum_AT       import CubeSum_AT
from admit.at.FeatureList_AT   import FeatureList_AT
from admit.at.LineID_AT        import LineID_AT
from admit.at.LineUID_AT       import LineUID_AT
from admit.at.LineCube_AT      import LineCube_AT
from admit.at.Moment_AT        import Moment_AT
from admit.at.PVSlice_AT       import PVSlice_AT
from admit.at.PVCorr_AT        import PVCorr_AT

# Example how to get predefined position(s) for CubeSpectrum
def get_pos(i):
    """ return key positions in N253 (1..10) from Meier's Table 2:
         0 = blank, if you want to use the peak in the cube
        11 = map center, the reference position of N253
        See also http://adsabs.harvard.edu/abs/2015ApJ...801...63M
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

# placeholder until we have an official way to find the VLSR of a source
def get_vlsr(source, vlsr=None):
    """simple vlsr (by source) lookup 
    """
    vcat = { 'NGC253'   :  236.0,
             'NGC3256'  : 2794.2,     # test0 (foobar.fits)
             'NGC6503'  :   25.0,
             '185'      :    4.0,     # test201
             '188'      :    4.0,     # test202
             'Serpens_Main': 8.0,
             'SERPSNW'  :    8.0,
             'L1551 NE' :    7.0,     # test1 (should be 6.9 ???)
             'ST11'     :  280.0,     # in the LMC, but not sure if the VLSR to close enough
    }

    # if it was given, return that
    if vlsr != None : return vlsr

    # if it was in our cute catalog, return that
    if vcat.has_key(source): return vcat[source]

    # if all else fails, return 0, or go hunt down NED or SIMBAD (astroquery?)
    print "GET_VLSR: unknown source %s, using vlsr=0.0" % source
    print "Known sources are: ",vcat.keys()
    return 0.0

def admit_dir(file):
    """ create the admit directory name from a filename 
    This filename can be a FITS file (usually with a .fits extension
    or a directory, which would be assumed to be a CASA image or
    a MIRIAD image
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

def get_admit_vars(module_name):
    module = globals().get(module_name, None)
    book = {}
    if module:
        book = {key: value for key, value in module.__dict__.iteritems() if not (key.startswith('__') or key.startswith('_'))}
    return book

# Before command line parsing, attempt to find 'admit_vars.py' with variables to override the admit vars here
# this doesn't work yet, since CASA modifies the python environment
try:
    print 'Trying admit_vars'
    import admit_vars
    book = get_admit_vars('admit_vars')
    for key,val in book.iteritems():
        # print "ADMIT_VAR: ",key,val,type(key),type(val)
        exec(key + '=' + repr(val))
except:
    print "No admit_vars.py found, and that's ok."


# allow a command line argument to be the fits file name
argv = admit.casa_argv(sys.argv)
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

#-----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------- start of script -----------------------------------------------

#  announce version
print 'ADMIT1: Version ',version

#  do the work in a proper ".admit" directory
adir = admit_dir(file)
#   dirty method, it really should check if adir is an admit directory
if clean and adir != file:
    print "Removing previous results from ",adir
    os.system('rm -rf %s' % adir)
    create=True
else:
    create=False

a = admit.Admit(adir,name='Testing ADMIT1 style pipeline - version %s' % version,create=create,loglevel=loglevel)

if a.new:
    print "Starting a new ADMIT using ",argv[0]
    os.system('cp -a %s %s' % (argv[0],adir))
else:
    print "All done, we just read an existing admit.xml and it should do nothing"
    print "Use admit0.py to re-run inside of your admit directory"
    #
    a.show()
    a.showsetkey()
    sys.exit(0)

# Default ADMIT plotting environment
a.plotmode(plotmode,plottype)

# Ingest
ingest1 = a.addtask(Ingest_AT(file=file,alias=alias))
a[ingest1].setkey('mask',useMask) 
bandcube1 = (ingest1,0)   

if cont != '':
    ingest2 = a.addtask(Ingest_AT(file=cont,alias=alias+'-cont'))
    contmap = (ingest2,0)
    #
    cubestats2 = a.addtask(CubeStats_AT(), [contmap])
    #a[cubestats1].setkey('robust',robust)
    csttab2 = (cubestats2,0)
    featurelist2 = a.addtask(FeatureList_AT(), [contmap])

# CubeStats - will also do log(Noise),log(Peak) plot
cubestats1 = a.addtask(CubeStats_AT(), [bandcube1])
a[cubestats1].setkey('robust',robust)
a[cubestats1].setkey('ppp',usePPP)
csttab1 = (cubestats1,0)

# CubeSum
moment1 = a.addtask(CubeSum_AT(), [bandcube1,csttab1])
a[moment1].setkey('numsigma',2.0)   # Nsigma clip in cube
a[moment1].setkey('sigma',99.9)     # force single cuberms sigma from cubestats
csmom0 = (moment1,0)

# CubeSpectrum 
if len(maxpos) > 0:
    cubespectrum1 = a.addtask(CubeSpectrum_AT(), [bandcube1])
    a[cubespectrum1].setkey('pos',maxpos)
else:
    #cubespectrum1 = a.addtask(CubeSpectrum_AT(), [bandcube1,csttab1])
    cubespectrum1 = a.addtask(CubeSpectrum_AT(), [bandcube1,csmom0])
csptab1 = (cubespectrum1,0)

# PVSlice
if len(pvslice) == 4:
    # hardcoded with a start,end
    slice1 = a.addtask(PVSlice_AT(slice=pvslice,width=11),[bandcube1])
elif len(pvslit) == 4:
    # hardcoded with a center,len,pa
    slice1 = a.addtask(PVSlice_AT(slit=pvslit,width=11),[bandcube1])
else:
    # use cubesum's map to generate the best slice
    # the PPP method didn't seem to work so well yet, and is slow, so still commented out here
    #slice1 = a.addtask(PVSlice_AT(width=5),[bandcube1,csttab1])
    slice1 = a.addtask(PVSlice_AT(width=5),[bandcube1,csmom0])
    a[slice1].setkey('clip',0.3)        # TODO: this is an absolute number for mom0
    a[slice1].setkey('gamma',1.0)       # SB185 works better with gamma=4
a[slice1].setkey('smooth',pvSmooth)     # smooth, in pixel numbers
pvslice1 = (slice1,0)

corr1 = a.addtask(PVCorr_AT(),[pvslice1,csttab1])
pvcorr1 = (corr1,0)

a.run()     # run now, LineID_AT needs the VLSR here
a.write()
print "OBJECT 1:", a.summaryData.get('object')
vlsr = get_vlsr(a.summaryData.get('object')[0].getValue()[0],vlsr)
print "VLSR = ",vlsr

if useUID:
    lineid4 = a.addtask(LineUID_AT(vlsr=vlsr,method=2), [csttab1]) 
    a[lineid4].setkey('pmin',4.0)
    a[lineid4].setkey('minchan',6)
    a[lineid4].setkey('maxgap',5)    # 20 for the SB outflows
    a[lineid4].setkey('bottom',True)
    lltab1 = (lineid4,0)
else:
    lineid1 = a.addtask(LineID_AT(vlsr=vlsr,segment="ADMIT"), [csptab1,csttab1])
    lltab1 = (lineid1,0)

a.run()   # run now, we need nlines
a.write()

nlines = len(a[lltab1[0]][0])
print "nlines=",nlines

# LineCube
linecube1 = a.addtask(LineCube_AT(), [bandcube1,lltab1])

a.run()    # run again, we need to find out how many cubes created
a.write()

nlines = len(a[linecube1])
print "Found %d lines during runtime" % nlines

x = range(nlines)    # place holder to contain mol/line
m = {}               # task id for moment on this mol/line
sp= {}               # task id for cubespectrum on this mol/line
st= {}               # task id for cubestats

# loop over all lines  ; produce linecubes, moments and spectra
for i in range(nlines):
    x[i] = a[linecube1][i].getimagefile(bt.CASA)
    print "LineDir:", i, x[i]
    # Moment maps from the LineCube
    linecubei = (linecube1,i)
    m[x[i]] = a.addtask(Moment_AT(),[linecubei,csttab1])
    print "MOMENT_AT:",m[x[i]]
    a[m[x[i]]].setkey('moments',[0,1,2])
    #a[m[x[i]]].setkey('cutoff',[2.0,3.0,3.0])
    a[m[x[i]]].setkey('numsigma',[2.0])
    a[m[x[i]]].setkey('mom0clip',2.0)        # TODO: this is still an absolute value
    if usePeak:
        if useCSM:
            momenti0 = csmom0               # CubeSum mom0
        else:
            momenti0 = (m[x[i]],0)          # this linecube mom0
        # CubeSpectrum through the line cube where the mom0 map has peak
        sp[x[i]] = a.addtask(CubeSpectrum_AT(),[linecubei,momenti0])
    elif len(maxpos) > 0:
        # CubeSpectrum through the line cube at given point, 
        # use the same maxpos for all linecubes as we used before
        sp[x[i]] = a.addtask(CubeSpectrum_AT(),[linecubei])
        a[sp[x[i]]].setkey('pos',maxpos)
        # CubeStats
        st[x[i]] = a.addtask(CubeStats_AT(),[linecubei])        
    else:
        # CubeSpectrum last resort, where it takes the peak from cube maximum
        sp[x[i]] = a.addtask(CubeSpectrum_AT(),[linecubei,csttab1])

if useMOM and nlines == 0:
    # if no lines found, take a moment (0,1,2) over the whole cube
    moment1 = a.addtask(Moment_AT(),[bandcube1,csttab1])
    a[moment1].setkey('moments',[0,1,2])
    a[moment1].setkey('numsigma',[2.0])
    a[moment1].setkey('mom0clip',2.0)       # Nsigma

# final run and save
a.run()
a.write()

linelist = a.summaryData.getLinelist()
print "LINES FOUND: " 
for line in linelist[0]:
    print line

# symlink resources and write out index.html
a.updateHTML()

