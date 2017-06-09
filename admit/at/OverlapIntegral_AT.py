
""" .. _OverlapIntegral-at-api:

   **OverlapIntegral_AT** --- Computes the overlap integral between images.
   ------------------------------------------------------------------------

   This module defines the OverlapIntegral_AT class.
"""


import numpy as np
import numpy.ma as ma
from copy import deepcopy
import types
import os

from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.util.Image import Image
import admit.util.utils as utils
import admit.util.APlot as APlot
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
import admit.util.Table
from admit.bdp.Image_BDP import Image_BDP
from admit.util.AdmitLogging import AdmitLogging as logging
import admit.util.casautil as casautil

try:
  import scipy
  import scipy.signal
  import casa
  import taskinit
except:
  print "WARNING: No scipy or casa; OverlapIntegral task cannot function."


class OverlapIntegral_AT(AT):
    """Compute an overlap integral between selected images (or cubes).

    Images (or cubes) need to have a confirming WCS. It also makes sense
    if the input maps have the same resolving power, see also
    :ref:`Smooth-at-api` how to achieve this.

    See also :ref:`OverlapIntegral-AT-Design` for the design document.

    **Keywords**

        **chans**: string
           If selected (for cubes), this is the channel range over which
           data is compared. Experimental.

        **normalize**: boolean
           Normalize all data?  Default: False.

        **method**: tuple
           The method name (string) and a dictionary of keywords describing
           the method will determine the way an overlap integral is computed.
           Not used yet.

        **cmap**: string
           A matplotlib name of colormaps available. The default ('jet') will
           have blue at the low end through green yellow to red.

    **Input BDPS**

        **Image_BDP**: count: 2 or more
            Input images (or cubes); for example, from 
            `Ingest_AT <Ingest_AT.html>`_, `LineCube_AT <LineCube_AT.html>`_
            or `Moment_AT <Moment_AT.html>`_.

    **Output BDPs**

        **Image_BDP**: count: 1

    Parameters
    ----------
        keyval : dictionary, optional

    Attributes
    ----------
        _version : string
    """


    def __init__(self, **keyval):
        keys = {
            "chans"     : [],          # 0-based channel range, e.g. [5,10]
            "normalize" : False, 
            "method"    : ("", {"key1": 0, "key2": 1.0, "key3": "abc"}),
            "cmap"      : "jet",
        }
        AT.__init__(self,keys,keyval)
        self._version = "1.0.1"
        self.set_bdp_in([(Image_BDP,     0, bt.REQUIRED)])     # 2 or more should be input

        # @TODO: Why is OverlapIntegral_BDP not used here, 
        # since the output is a Table and an Image
        self.set_bdp_out([(Image_BDP,1)])                      # 1 is output

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           OverlapIntegral_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | overlap  | list     |   output image and information    | 
              |          |          |   about lines used                |
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
        """ Main program for OverlapIntegral
        """
        dt = utils.Dtime("OverlapIntegral")
        self._summary = {}
        chans =self.getkey("chans")
        cmap = self.getkey("cmap")
        normalize = self.getkey("normalize")
        doCross = True
        doCross = False
        myplot = APlot(pmode=self._plot_mode,ptype=self._plot_type,abspath=self.dir())
        
        dt.tag("start")
 
        n = len(self._bdp_in)
        if n==0:
            raise Exception,"Need at least 1 input Image_BDP "
        logging.debug("Processing %d input maps" % n)
        data = range(n)     # array in which each element is placeholder for the data
        mdata = range(n)    # array to hold the max in each array
        summarytable = admit.util.Table()
        summarytable.columns = ["File name","Spectral Line ID"]
        summarytable.description = "Images used in Overlap Integral"
        for i in range(n):
            bdpfile = self._bdp_in[i].getimagefile(bt.CASA)
            if hasattr(self._bdp_in[i],"line"):
                line = getattr(self._bdp_in[i],"line")
                logging.info("Map %d: %s" % (i,line.uid))
                lineid = line.uid
            else:
                lineid="no line"
            data[i] = casautil.getdata(self.dir(bdpfile),chans)
            mdata[i] = data[i].max()
            logging.info("shape[%d] = %s with %d good data" % (i,data[i].shape,data[i].count()))
            if i==0:
                shape = data[i].shape
                outfile = self.mkext("testOI","oi")
            else:
                if shape != data[i].shape:
                    raise Exception,"Shapes not the same, cannot overlap them"
            # collect the file names and line identifications for the summary
            summarytable.addRow([bdpfile,lineid])
        logging.regression("OI: %s" % str(mdata))
                    
        if len(shape)>2 and shape[2] > 1:
            raise Exception,"Cannot handle 3D cubes yet"

        if doCross:
            # debug: produce all cross-corr's of the N input maps (expensive!)
            crossn(data, myplot)
            dt.tag("crossn")

        b1 = Image_BDP(outfile)
        self.addoutput(b1)
        b1.setkey("image", Image(images={bt.CASA:outfile}))

        ia = taskinit.iatool()

        dt.tag("open")

        useClone = True

        # to create an output dataset, clone the first input, but using the chans=ch0~ch1
        # e.g. using imsubimage(infile,outfile=,chans=
        if len(chans) > 0:
            # ia.regrid() doesn't have the chans=
            ia.open(self.dir(self._bdp_in[0].getimagefile(bt.CASA)))
            ia.regrid(outfile=self.dir(outfile))
            ia.close()
        else:
            # 2D for now
            if not useClone:
                logging.info("OVERLAP out=%s" % outfile)
                ia.fromimage(infile=self.dir(self._bdp_in[0].getimagefile(bt.CASA)),
                                      outfile=self.dir(outfile), overwrite=True)
                ia.close()
        dt.tag("fromimage")


        if n==3:
            # RGB
            logging.info("RGB mode")
            out = rgb1(data[0],data[1],data[2], normalize)
        else:
            # simple sum
            out = data[0]
            for i in range(1,n):
                out = out + data[i]

        if useClone:
            casautil.putdata_raw(self.dir(outfile),out,clone=self.dir(self._bdp_in[0].getimagefile(bt.CASA)))
        else:
            ia.open(self.dir(outfile))
            s1 = ia.shape()
            s0 = [0,0,0,0]
            rg = taskinit.rgtool()
            r1 = rg.box(blc=s0,trc=s1)
            pixeldata = out.data
            pixelmask = ~out.mask
            ia.putregion(pixels=pixeldata, pixelmask=pixelmask, region=r1)
            ia.close()

        title = "OverlapIntegral"
        pdata = np.rot90(out.squeeze())
        logging.info("PDATA: %s" % str(pdata.shape))
        
        myplot.map1(pdata,title,"testOI",thumbnail=True,cmap=cmap)
        
        #-----------------------------
        # Populate summary information
        #-----------------------------
        taskargs = "chans=%s cmap=%s" % (chans, cmap)
        imname = ""
        thumbnailname = ""
        # uncomment when ready.
        imname = myplot.getFigure(figno=myplot.figno,relative=True)
        thumbnailname = myplot.getThumbnail(figno=myplot.figno,relative=True)
        #@todo fill in caption with more info - line names, etc.
        caption = "Need descriptive caption here"
        summaryinfo = [summarytable.serialize(),imname,thumbnailname,caption]
        self._summary["overlap"] = SummaryEntry(summaryinfo,
                                   "OverlapIntegral_AT",
                                   self.id(True),taskargs)
        #-----------------------------
        dt.tag("done")
        dt.end()

def crossn(data, myplot):
    """  Run over all possible cross-correlations between the N input data
         CAUTION: Expensive routine
         @todo     divide    cross(i,j)/sqrt(auto(i)*auto(j))
    """
    n = len(data)
    nx = data[0].shape[0]
    ny = data[0].shape[1]
    auto = range(n)         # place holder for the auto's
    for i in range(n):
        idata = data[i].data.squeeze()
        out = scipy.signal.correlate2d(idata,idata,mode='same')
        auto[i] = np.rot90(out.reshape((nx,ny)))
        myplot.map1(auto[i],"autocorr-%d" % i,"testOI-%d-%d" % (i,i),thumbnail=False)        
    for i in range(n):
        idata = data[i].data.squeeze()
        for j in range(i+1,n):
            jdata = data[j].data.squeeze()
            out = scipy.signal.correlate2d(idata,jdata,mode='same')
            #outd = np.rot90(out.reshape((nx,ny))) / np.sqrt(auto[i]*auto[j])
            outd = np.rot90(out.reshape((nx,ny))) 
            myplot.map1(outd,"crosscorr-%d-%d" % (i,j),"testOI-%d-%d" % (i,j),thumbnail=False)


def rgb1(r,g,b, normalize=False):
     """
     """
     rmin = r.min()
     rmax = r.max()
     gmin = g.min()
     gmax = g.max()
     bmin = b.min()
     bmax = b.max()

     # normalize each to [0,1]
     x = (r-rmin)/(rmax-rmin)
     y = (g-gmin)/(gmax-gmin)
     z = (b-bmin)/(bmax-bmin)

     x = np.where(x<0.5, 2*x, 0    )
     y = np.where(y<0.5, 2*y, 2-2*y)
     z = np.where(z<0.5, 0  , 2-2*z)

     return x+y+z
  
def rgb2(a, b, jpgname, f=0.5):
     """ Convert 2 2D-numpy arrays into a colorful JPG image
         f = Color Composition Index
         RGB = (A, B+f*A, B)
     """
     logging.warning("RGB2 not implemented")


def rgb3(r, g, b, jpgname):
     """ Convert 3 2D-numpy arrays into a colorful JPG image
         It needs the PIL module, which CASA doesn't have
         but we would like to try this out one of these moons...
     """
     from PIL import Image

     # skip all the shape tests and being 2D
     sh = r.shape

     rgb = np.zeros((sh[0],sh[1],3), 'uint8')
     rgb[..., 0] = r*256
     rgb[..., 1] = g*256
     rgb[..., 2] = b*256
     img = Image.fromarray(rgb)
     img.save(jpgname)
    
