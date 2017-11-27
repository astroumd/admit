""" .. _PVSlice-AT-api:

   **PVSlice_AT** --- Creates a position-velocity slice through a cube.
   --------------------------------------------------------------------

   This module defines the PVSlice_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.bdp.PVSlice_BDP import PVSlice_BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.Moment_BDP import Moment_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP


from admit.util.Image import Image
from admit.util import APlot
from admit.util import utils
from admit.util import stats
import admit.util.ImPlot as ImPlot
import admit.util.casautil as casautil
from admit.util.AdmitLogging import AdmitLogging as logging

from copy import deepcopy
import numpy as np
import numpy.ma as ma
import numpy.linalg as la
import math

try:
  import casa
  import taskinit
except:
  print "WARNING: No CASA; PVSlice task cannot function."

class PVSlice_AT(AT):
    """Create a PV Slice through a cube.

    See also :ref:`PVSlice-AT-Design` for the design document.

    **Keywords**
      **slice**: 4 element list 
        Beginning and ending positions of the slice: [x0,y0,x1,y1]
        Only (0 based) pixel coordinates are allowed.

      **slit**: 4 element list
        XCenter, Ycenter, SlitLength and SlitPA.
        Pixel coordinates for now, for both center (0 based) and
        length.  PA in degrees, east of north,
        in the traditional astronomy convention.

      **width**: int
        Width of the slice/slit in the XY plane. Higher numbers will of
        course increase the signal to noise, but also blurr the
        signal in velocity if there are velocity gradients across
        the slit, defeating the purpose if this PVSlice is used.
        for LineID.
        Numbers need to be odd, since it includes the central pixel,
        as well as a number on either side of the slit/slice.
        Warning: large widths can also cause CASA's impv program
        to crash as it runs over the edge near the endpoints of
        the slit.
        **Default:** 1.

      **clip**: float
        Clip value applied to input Moment_BDP map in case the slice/slit is to
        be derived from an automated moment of inertia analysis. It is interpreted
        as a "numsigma", i.e. how many times over the noise in the map it should
        use. If no signal is found, it iteratively lowers this value until some
        signal is found (but probably creating a lousy PV Slice)
        **Default:**  0.0.

      **gamma**: float
        Gamma factor applied to input Moment_BDP map in case the slice/slit is to
        be derived from an automated moment of inertia analysis.
        **Default:**  1.0.

      **pvsmooth**: list of 2
        Smoothing (in pixels) to apply to PV Slice. By default no smoothing is done.
        Currently no further processing on this smoothed version is done, although
        it is available for inspection.
        **Default:**  [].

      **zoom**: int
        Image zoom ratio applied to the map plots. This does not
        impact the base (CASA) images. Default: 1.

    **Input BDPs**

      **SpwCube_BDP**: count: 1
        Spectral window cube, as from an `Ingest_AT <Ingest_AT.html>`_ or
        `ContinuumSub_AT <ContinuumSub_AT.html>`_.

      **Moment_BDP**: count: 1 (optional)
        Map from a `CubeSum_AT <CubeSum_AT.html>`_ or
        `Moment_AT <Moment_AT.html>`_
        where a moment of inertia is used to derive a best slice.

      **CubeStats_BDP**: count: 1 (optional)
        The peakpoints from this table are used to compute a moment of inertia
        to obtain a best slice. Normally the output of a
        `CubeStats_AT <CubeStats_AT.html>`_.
    
    **Output BDPs**

      **PVSlice_BDP**: count: 1
        Output PV Slice, a 2D map.
        Naming convention:    extension replaced with "pv"  (e.g. x.im -> x.pv).

    Parameters
    ----------
    keyval : dictionary, optional

    Attributes
    ----------
    _version : string
    """

    def __init__(self,**keyval):
        keys = {"slice"    : [],            # x0,y0,x1,y1    ? could be line= ?
                "slit"     : [],            # xc,yc,len,pa   pick one of slice= or slit=
                "width"    : 1,             # odd integer!
                "clip"     : 0.0,           # clip value (in terms of sigma)
                "gamma"    : 1.0,           # gamma factor for analyzing map MOI
                "pvsmooth" : [],            # P and V smoothing (in pixel)
                "zoom"     : 1,             # default map plot zoom ratio
                #"major"   : True,          # (TODO) major or minor axis, not used yet
                }
        AT.__init__(self,keys,keyval)
        self._version       = "1.1.3"
        self.set_bdp_in([(Image_BDP,     1, bt.REQUIRED),      # SpwCube
                         (Moment_BDP,    1, bt.OPTIONAL),      # Moment0 or CubeSum
                         (CubeStats_BDP, 1, bt.OPTIONAL)])     # was: PeakPointPlot
        self.set_bdp_out([(PVSlice_BDP,  1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           PVSlice_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | pvcorr   | list     |   correlation diagram             |
              +----------+----------+-----------------------------------+
           
           Parameters
           ----------
           None

           Returns
           -------
           dict
               Dictionary of SummaryEntry
        """
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """Runs the task.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        self._summary = {}
        pvslicesummary = []
        sumslicetype = 'slice'
        sliceargs = []
        dt = utils.Dtime("PVSlice")
        # import here, otherwise sphinx cannot parse
        from impv     import impv
        from imsmooth import imsmooth

        pvslice = self.getkey('slice')       # x_s,y_s,x_e,y_e (start and end of line)
        pvslit  = self.getkey('slit')        # x_c,y_c,len,pa  (center, length and PA of line)

        # BDP's used :

        #   b10 = input BDP
        #   b11 = input BDP (moment)
        #   b12 = input BDP (new style cubestats w/ maxpos)
        #   b2 = output BDP

        b10 = self._bdp_in[0]                 # input SpwCube
        fin = b10.getimagefile(bt.CASA)       # input name

        b11 = self._bdp_in[1]                 # 
        b12 = self._bdp_in[2]

        clip  = self.getkey('clip')           # clipping to data for Moment-of-Inertia
        gamma = self.getkey('gamma')          # gamma factor to data for Moment-of-Inertia

        if b11 != None and len(pvslice) == 0 and len(pvslit) == 0:
            # if a map (e.g. cubesum ) given, and no slice/slit, get a best pvslice from that
            (pvslice,clip) = map_to_slit(self.dir(b11.getimagefile(bt.CASA)),clip=clip,gamma=gamma)
        elif b12 != None and len(pvslice) == 0 and len(pvslit) == 0:
            # PPP doesn't seem to work too well yet
            logging.debug("testing new slice computation from a PPP")
            max     = b12.table.getColumnByName("max")
            maxposx = b12.table.getColumnByName("maxposx")
            maxposy = b12.table.getColumnByName("maxposy")
            if maxposx == None:
              raise Exception,"PPP was not enabled in your CubeStats"
            (pvslice,clip) = tab_to_slit([maxposx,maxposy,max],clip=clip,gamma=gamma)
        sliceargs = deepcopy(pvslice)
        if len(sliceargs)==0:
            logging.warning("no slice for plot yet")
        # ugh, this puts single quotes around the numbers
        formattedslice = str(["%.2f" % a for a in sliceargs])
        taskargs = "slice="+formattedslice
        dt.tag("slice")

        pvname = self.mkext(fin,'pv')        # output image name
        b2 = PVSlice_BDP(pvname)
        self.addoutput(b2)

        width   = self.getkey('width')       # @todo also:  "4arcsec"  (can't work since it's a single keyword)

        if len(pvslice) == 4:
            start = pvslice[:2]   # @todo also allow:   ["14h20m20.5s","-30d45m25.4s"]
            end   = pvslice[2:]
            impv(self.dir(fin), self.dir(pvname),"coords",start=start,end=end,width=width,overwrite=True)
        elif len(pvslit) == 4:
            sumslicetype = 'slit'
            sliceargs = deepcopy(pvslit)
            formattedslice = str(["%.2f" % a for a in sliceargs])
            taskargs = "slit="+formattedslice
            # length="40arcsec" same as {"value": 40, "unit": "arcsec"})
            center = pvslit[:2]   # @todo also:   ["14h20m20.5s","-30d45m25.4s"].
            length = pvslit[2]    # @todo also:   "40arcsec", {"value": 40, "unit": "arcsec"})
            if type(pvslit[3]) is float or type(pvslit[3]) is int:
                pa = "%gdeg" % pvslit[3]
            else:
                pa = pvslit[3]
            impv(self.dir(fin), self.dir(pvname),"length",center=center,length=length,pa=pa,width=width,overwrite=True)
        else:
            raise Exception,"no valid input  slit= or slice= or bad Moment_BDP input"
        sliceargs.append(width)
        taskargs = taskargs + " width=%d" % width
        dt.tag("impv")

        smooth = self.getkey('pvsmooth')
        if len(smooth) > 0:
            if len(smooth) == 1:
                smooth.append(smooth[0])
            major = '%dpix' % smooth[0]
            minor = '%dpix' % smooth[1]
            logging.info("imsmooth PV slice: %s %s" % (major,minor))
            imsmooth(self.dir(pvname), outfile=self.dir(pvname)+'.smooth',kernel='boxcar',major=major,minor=minor)
            dt.tag("imsmooth")
            # utils.rename(self.dir(pvname)+'.smooth',self.dir(pvname))
            # @todo  we will keep the smooth PVslice for inspection, no further flow work

        # get some statistics
        data = casautil.getdata_raw(self.dir(pvname))
        rpix = stats.robust(data.flatten())
        r_mean = rpix.mean()
        r_std  = rpix.std()
        r_max = rpix.max()
        logging.info("PV stats: mean/std/max %f %f %f" % (r_mean, r_std, r_max))
        logging.regression("PVSLICE: %f %f %f" % (r_mean, r_std, r_max))

        myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())

        # hack to get a slice on a mom0map 
        # @todo   if pmode is not png, can viewer handle this?
        figname   = pvname + ".png"
        slicename = self.dir(figname)
        overlay   = pvname+"_overlay" 
        if b11 != None:
            f11 = b11.getimagefile(bt.CASA)
            tb = taskinit.tbtool()
            tb.open(self.dir(f11))
            data = tb.getcol('map')
            nx = data.shape[0]
            ny = data.shape[1]
            tb.close()
            d1 = np.flipud(np.rot90 (data.reshape((nx,ny))))
            if len(pvslice) == 4:
              segm = [[pvslice[0],pvslice[2],pvslice[1],pvslice[3]]]
              pa = np.arctan2(pvslice[2]-pvslice[0],pvslice[1]-pvslice[3])*180.0/np.pi
              title = "PV Slice location : slice PA=%.1f" % pa
              xcen = (pvslice[0]+pvslice[2])/2.0
              ycen = (pvslice[1]+pvslice[3])/2.0
            elif len(pvslit) == 4:
              # can only do this now if using pixel coordinates
              xcen = pvslit[0]
              ycen = pvslit[1]
              slen = pvslit[2]
              pard = pvslit[3]*np.pi/180.0
              cosp = np.cos(pard)
              sinp = np.sin(pard)
              halflen = 0.5*slen
              segm = [[xcen-halflen*sinp,xcen+halflen*sinp,ycen+halflen*cosp,ycen-halflen*cosp]]
              pa   = pvslit[3]
              title = "PV Slice location : slit PA=%g" % pa
            else:
              # bogus, some error in pvslice
              logging.warning("bogus segm since pvslice=%s" % str(pvslice))
              segm = [[10,20,10,20]]
              pa   = -999.999
              title = "PV Slice location - bad PA"
            logging.info("MAP1 segm %s %s" % (str(segm),str(pvslice)))
            if d1.max() < clip:
              logging.warning("datamax=%g,  clip=%g" % (d1.max(), clip))
              title = title + ' (no signal over %g?)' % clip
              myplot.map1(d1,title,overlay,segments=segm,thumbnail=True,
                          zoom=self.getkey("zoom"),star=[xcen,ycen])
            else:
              myplot.map1(d1,title,overlay,segments=segm,range=[clip],thumbnail=True,
                          zoom=self.getkey("zoom"),star=[xcen,ycen])
            dt.tag("plot")
            overlayname = myplot.getFigure(figno=myplot.figno,relative=True)
            overlaythumbname = myplot.getThumbnail(figno=myplot.figno,relative=True)
            Qover = True
        else:
            Qover = False

        implot = ImPlot(pmode=self._plot_mode,ptype=self._plot_type,abspath=self.dir())
        implot.plotter(rasterfile=pvname, figname=pvname, colorwedge=True)
        thumbname = implot.getThumbnail(figno=implot.figno,relative=True)
        figname   = implot.getFigure(figno=implot.figno,relative=True)
        if False:
            # debug:
            #
            # @todo    tmp1 is ok, tmp2 is not displaying the whole thing
            #          use casa_imview, not casa.imview - if this is enabled.
            # old style:   viewer() seems to plot full image, but imview() wants square pixels?
            casa.viewer(infile=self.dir(pvname), outfile=self.dir('tmp1.pv.png'), gui=False, outformat="png")
            casa.imview(raster={'file':self.dir(pvname),  'colorwedge' : True, 'scaling':-1},
                    axes={'y':'Declination'},
                    out=self.dir('tmp2.pv.png'))
            #
            # -> this one works, axes= should be correct
            # imview(raster={'file':'x.pv',  'colorwedge' : True, 'scaling':-1},axes={'y':'Frequency'})
            #
            # @TODO big fixme, we're going to reuse 'tmp1.pv.png' because implot give a broken view
            figname = 'tmp1.pv.png'
                    
        # @todo   technically we don't know what map it was overlay'd on.... CubeSum/Moment0
        overlaycaption = "Location of position-velocity slice overlaid on a CubeSum map"
        pvcaption = "Position-velocity diagram through emission centroid"
        pvimage = Image(images={bt.CASA : pvname, bt.PNG : figname},thumbnail=thumbname,thumbnailtype=bt.PNG, description=pvcaption)
        b2.setkey("image",pvimage)
        b2.setkey("mean",float(r_mean))
        b2.setkey("sigma",float(r_std))
        if Qover:
          thispvsummary = [sumslicetype,sliceargs,figname,thumbname,pvcaption,overlayname,overlaythumbname,overlaycaption,pvname,fin]
        else:
          thispvsummary = [sumslicetype,sliceargs,figname,thumbname,pvcaption,pvname,fin]
        
        # Yes, this is a nested list.  Against the day when PVSLICE can
        # compute multiple slices per map.
        pvslicesummary.append(thispvsummary)
        self._summary["pvslices"] = SummaryEntry(pvslicesummary,"PVSlice_AT",self.id(True),taskargs)

        dt.tag("done")
        dt.end()


# Big Fat Warning (using the default image in CASA) about images in CASA and numpy/astropy
#
# ia.maketestimage()
# data = ia.getchunk().squeeze()
# data.shape -> 113,76 = NX,NY
# data[1,0]  = -0.0927   data[ix,iy]
#
#
#  from astropy.io import fits
#  hdu = fits.open('tmp.fits')
#  data = hdu[0].data
#  data.shape -> 76,113  = NY,NX
#  data[1,0]  = 0.407   data[iy,ix]


def map_to_slit(fname, clip=0.0, gamma=1.0):
    """take all values from a map over clip, compute best slit for PV Slice
    """
    ia = taskinit.iatool()
    ia.open(fname)
    imshape = ia.shape()
    pix = ia.getchunk().squeeze()     # this should now be a numpy pix[ix][iy] map
    pixmax = pix.max()
    pixrms = pix.std()
    if False:
        pix1 = pix.flatten()
        rpix = stats.robust(pix1)
        logging.debug("stats: mean: %g %g" % (pix1.mean(), rpix.mean()))
        logging.debug("stats: rms: %g %g" % (pix1.std(), rpix.std()))
        logging.debug("stats: max: %g %g" % (pix1.max(), rpix.max()))
        logging.debug('shape: %s %s %s' % (str(pix.shape),str(pix1.shape),str(imshape)))
    ia.close()
    nx = pix.shape[0]
    ny = pix.shape[1]
    x=np.arange(pix.shape[0]).reshape( (nx,1) )
    y=np.arange(pix.shape[1]).reshape( (1,ny) )
    if clip > 0.0:
        nmax = nx*ny
        clip = clip * pixrms
        logging.debug("Using initial clip=%g for rms=%g" % (clip,pixrms))
        m=ma.masked_less(pix,clip)
        while m.count() == 0:
          clip = 0.5 * clip
          logging.debug("no masking...trying lower clip=%g" % clip)
          m=ma.masked_less(pix,clip)
        else:
          logging.debug("Clip=%g now found %d/%d points" % (clip,m.count(),nmax))
        
    else:
        #@ todo   sigma-clipping with iterations?  see also astropy.stats.sigma_clip()
        rpix = stats.robust(pix.flatten())
        r_mean = rpix.mean()
        r_std  = rpix.std()
        logging.info("ROBUST MAP mean/std: %f %f" % (r_mean,r_std))
        m=ma.masked_less(pix,-clip*r_std)
    logging.debug("Found > clip=%g : %g" % (clip,m.count()))
    if m.count() == 0:
        logging.warning("Returning a dummy slit, no points above clip %g" % clip)
        edge = 3.0
        #slit = [edge,0.5*ny,nx-1.0-edge,0.5*ny]          # @todo    file a bug, this failed
        #  RuntimeError: (/var/rpmbuild/BUILD/casa-test/casa-test-4.5.7/code/imageanalysis/ImageAnalysis/PVGenerator.cc : 334) Failed AlwaysAssert abs( (endPixRot[0] - startPixRot[0]) - sqrt(xdiff*xdiff + ydiff*ydiff) ) < 1e-6
        slit = [edge,0.5*ny-0.1,nx-1.0-edge,0.5*ny+0.1]
    else:
        slit = convert_to_slit(m,x,y,nx,ny,gamma)
    return (slit,clip)

def tab_to_slit(xym, clip=0.0, gamma=1.0):
    """take all values from a map over clip, compute best slit for PV Slice
    """
    x = xym[0]   # maxposx
    y = xym[1]   # maxposy
    m = xym[2]   # max

    logging.debug("CLIP %g" % clip)

    slit = convert_to_slit(m,x,y,0,0,gamma,expand=2.0)
    return (slit,clip)

def convert_to_slit(m,x,y,nx,ny,gamma=1.0,expand=1.0):
    """compute best slit for PV Slice from set of points or masked array
    using moments of inertia
    m=mass (intensity)  x,y = positions
    """
    # sanity
    if len(m) == 0: return []
    if type(m) == ma.core.MaskedArray:
      if m.count() == 0:  return []
    # apply gamma factor
    logging.debug("Gamma = %f" % gamma)
    mw = ma.power(m,gamma)
    # first find a rough center
    smx = ma.sum(mw*x)
    smy = ma.sum(mw*y)
    sm  = ma.sum(mw)
    xm = smx/sm
    ym = smy/sm
    logging.debug('MOI::center: %f %f' % (xm,ym))
    (xpeak,ypeak) = np.unravel_index(mw.argmax(),mw.shape)
    logging.debug('PEAK: %f %f' % (xpeak,ypeak))
    if True:
      # center on peak
      # @todo but if (xm,ym) and (xpeak,ypeak) differ too much, e.g.
      #       outside of the MOI body, something else is wrong
      xm = xpeak
      ym = ypeak
    # take 2nd moments w.r.t. this center
    x = x-xm
    y = y-ym
    mxx=m*x*x
    mxy=m*x*y
    myy=m*y*y
    #
    smxx=ma.sum(mxx)/sm
    smxy=ma.sum(mxy)/sm
    smyy=ma.sum(myy)/sm
    #  MOI2
    moi = np.array([smxx,smxy,smxy,smyy]).reshape(2,2)
    w,v = la.eig(moi)
    a   = math.sqrt(w[0])
    b   = math.sqrt(w[1])
    phi = -math.atan2(v[0][1],v[0][0])
    if a < b:  
        phi = phi + 0.5*np.pi
    logging.debug('MOI::a,b,phi(deg): %g %g %g' % (a,b,phi*180.0/np.pi))
    #  ds9.reg format (image coords)
    sinp = np.sin(phi)
    cosp = np.cos(phi)
    # compute the line take both a and b into account,
    # since we don't even know or care which is the bigger one
    r  = np.sqrt(a*a+b*b)
    x0 = xm - expand*r*cosp 
    y0 = ym - expand*r*sinp 
    x1 = xm + expand*r*cosp 
    y1 = ym + expand*r*sinp 
    # add 1 for ds9, which used 1 based pixels
    logging.debug("ds9 short line(%g,%g,%g,%g)" % (x0+1,y0+1,x1+1,y1+1))
    if nx > 0:
      s = expand_line(x0,y0,x1,y1,nx,ny)
      logging.debug("ds9 full line(%g,%g,%g,%g)" % (s[0],s[1],s[2],s[3]))
      return [float(s[0]),float(s[1]),float(s[2]),float(s[3])]
    else:
      return [float(x0),float(y0),float(x1),float(y1)]


def expand_line(x0,y0,x1,y1,nx,ny,edge=6):
    """expand a line, but stay inside the box [0..nx,0..ny]
    sadly casa.impv cannot think outside the box,
    this routine takes a line, and makes it fit within the box, minus
    edge pixels from the edges, since that's what impv wants.
    CASA bug?   edge=2 is advertised should work, but 5 still fails, 6 is ok
    
    returns: [x0,y0,x1,y1]
    """
    def d2(x0,y0,x1,y1):
        """squared distance between two points"""
        return (x0-x1)*(x0-x1) + (y0-y1)*(y0-y1)
    def inside(x,e,n):
        """return if x is within e and n-e-1
        """
        if x < e: return False
        if x > n-e-1: return False
        return True
    # bypass everything
    if False:
        return [x0,y0,x1,y1]
    # pathetic cases
    if x0==x1: return [x0, edge, x1, ny-1-edge]
    if y0==y1: return [edge, y0, nx-1-edge, y1]
    # slope and center point of line
    a = (y1-y0)/(x1-x0)
    xc = (x0+x1)/2.0
    yc = (y0+y1)/2.0
    # intersections with the box vertices
    x_e = xc + (edge-yc)/a
    y_e = yc + a*(edge-xc)
    x_n = xc + (ny-edge-1-yc)/a
    y_n = yc + a*(nx-edge-1-xc)
    print "x,y(0)  x,y(1):",x0,y0,x1,y1
    print "x,y(e)  x,y(n):",x_e,y_e,x_n,y_n
    e = []
    if inside(x_e,edge,nx):  
        e.append(x_e)
        e.append(edge)
    if inside(y_e,edge,ny):
        e.append(edge)
        e.append(y_e)
    if inside(x_n,edge,nx):
        e.append(x_n)
        e.append(ny-edge-1)
    if inside(y_n,edge,ny):
        e.append(nx-edge-1)
        e.append(y_n)
    if len(e) != 4:
        # can happen for small maps?
        msg = "Math Error in expand_line: ",e
        raise Exception,msg
    return e


def expand_slice(slice, expand=1.2):
    x0 = slice[0]
    y0 = slice[1]
    x1 = slice[2]
    y1 = slice[3]
    dx = x1-x0
    dy = y1-y0
    x0 = x0 - expand*dx
    y0 = y0 - expand*dy
    x1 = x1 + expand*dx
    y1 = y1 + expand*dy
    return [x0,y0,x1,y1]

