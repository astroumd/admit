""" .. _MapSources-at-api:

   **MapSources_AT** --- Create SourceList in a map
   ------------------------------------------------

   This module defines the MapSources_AT class.
"""
from copy import deepcopy
import numpy as np
import numpy.ma as ma
import os

from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.Image_BDP        import Image_BDP
from admit.bdp.SpwCube_BDP      import SpwCube_BDP
from admit.bdp.LineCube_BDP     import LineCube_BDP
from admit.bdp.Moment_BDP       import Moment_BDP
from admit.bdp.CubeSpectrum_BDP import CubeSpectrum_BDP
from admit.bdp.CubeStats_BDP    import CubeStats_BDP
from admit.bdp.SourceList_BDP   import SourceList_BDP
from admit.Summary import SummaryEntry

import admit.util.Table as Table
import admit.util.Image as Image
from admit.util import APlot
import admit.util.utils as utils
import admit.util.PlotControl as PlotControl
from admit.util.AdmitLogging import AdmitLogging as logging

try:
  from taskinit import iatool as iatool
  import casa
except:
  try:
    import casatasks as casa
    from casatools import image         as iatool
  except:
    print("WARNING: No CASA; MapSources task cannot function.")

class MapSources_AT(AT):
    """ Create SourceList from another SourceList

    Either a list of positions is given directly (via the **pos=** keyword) or a set
    of BDP's can be given, each of which will accumulate its positions
    to a list of points for which the spectra are computed, as detailed below.

    See also :ref:`MapSources-AT-Design` for the design document.

    **Keywords**
      **pos**: list of int or string 
        List of ra-dec position pairs.
        Each pair will produce a separate spectrum and plot. 
        Positions can be given as two integers, in which case they are interpeted
        as (0 based) pixel coordinates, e.g. pos=[121,119],
        or in CASA's ra/dec region format,
        e.g. pos=['00h47m33.159s','-25d17m17.41s'].  Different pairs do not
        need to be of the same type, so you can mix int's and strings.
        If no positions are given, a position will be derived from the
        input BDPs. See below how this is done. This also means if an input BDP
        is given, the keyword values are ignored.
        If no input pos is given, and no optional BPD's, the center
        of the map is used.

      **sources** : list of int
        A python list of source indices (0 being the first) from the
        SourceList_BDP to be selected for a spectrum. A blank list, [],
        selects all. Normally the SourceList is ordered by total flux.
        Default : [0]

      **xaxis**: string
        Select the X axis plotting style:  channel number (the default),
        frequency (in GHz), or velocity (for this the restfreq needs to be in the image header).
        Currently ignored, channel is defaulted for SpwCube_BDP, and velocity for LineCube_BDP.

    **Input BDPs**

      **Moment_BDP**: count: 1 (required)
        If given, the maxpos from this moment map will be used for pos=[].
        Note : currently this is computed on the fly, as maps don't store
        their maxpos. Typically the output of a
        `CubeSum_AT <CubeSum_AT.html>`_ or `Moment_AT <Moment_AT.html>`_.

      **CubeStats_BDP**: count: 1 (required)
        If given, the cube maxpos from this table will be used for pos=[].
        Normally the output of a `CubeStats_AT <CubeStats_AT.html>`_.

    
      **SourceList_BDP**: count: 1 (required)
        If given, the positions in this source list will be used. By default
        only the strongest source (index 0) is selected. Typically the output
        from `SFind2D_AT <SFind2D_AT.html>`_ on a continuum map is given here.

    **Output BDPs**

      **SourceList_BDP**: count: 1
        The list of sources identified at the input positions.
        Output BDP name takes from the input Image by replacing the extension with **"csp"**.
        See also :ref:`SourceList-bdp-api`.

    Parameters
    ----------
    keyval : dictionary, optional

    Attributes
    ----------
    _version : string
    """

    ### todo's

    """
        ***Missing Features***

      This code was derived from CubeSpectrum

      In the design document a number of options were mentioned that have not been implemented, see
      also  :ref:`MapSources-AT-Design` for that design document.

        1) Only points can be selected, not regions. Or sizes around points.
           NOTE the treatment of the bug in imval when > 1 pixel was used.

        2) No magic names for pos=.  The "xpeak,ypeak" is essentually when pos=[] left blank and
           no other BDP are given, but there is no way to select the reference point "xref,yref"

        3) Smoothing option is absent.  There are filters that can be applied in LineID_AT though.
           See also Smooth_AT, where you cann create a smoother version of the input cube.

    """


    

    def __init__(self,**keyval):
        keys = {"pos"     : [],    # one or more pairs of int's or ra/dec strings
                "sources" : [0],   # select which sources from a SourceList
                "xaxis"   : "",    # currently still ignored
        }
        AT.__init__(self,keys,keyval)
        self._version       = "1.3.0"
        self.set_bdp_in( [(Moment_BDP,      1,bt.REQUIRED),     # 0: map, uses the max in this image as pos=
                          (CubeStats_BDP,   1,bt.REQUIRED),     # 1: stats, uses rms
                          (SourceList_BDP,  1,bt.OPTIONAL)])    # 2: source list, for positions
        self.set_bdp_out([(SourceList_BDP,1)])

    def run(self):
        """Runs the task.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        logging.study7("# mapsources")
        logging.warning("MapSources in development - not in final form")

        self._summary = {}
        dt = utils.Dtime("MapSources")

        b1 = self._bdp_in[0]
        fin = b1.getimagefile(bt.CASA)
        if self._bdp_in[0]._type != bt.MOMENT_BDP:
            logging.error("0: Not a moment map")

        if self._bdp_in[1]._type != bt.CUBESTATS_BDP:
            logging.error("1: Not a cubestats")

        if self._bdp_in[2] != None:
            if self._bdp_in[2]._type != bt.SOURCELIST_BDP:
                logging.error("2: Not a sourcelist")
            logging.study7("# %s" % fin)
            b2 = self._bdp_in[2]
            ra   = b2.table.getFullColumnByName("RA")
            dec  = b2.table.getFullColumnByName("DEC")
            peak = b2.table.getFullColumnByName("Peak")
            smaj = b2.table.getFullColumnByName("Major")
            smin = b2.table.getFullColumnByName("Minor")
            spa  = b2.table.getFullColumnByName("PA")
            nppb = 31.0    # @todo
            if str(ra) == "None":
               logging.study("# no sources")
            else:
                for (r,d,p,j,n,a) in zip(ra,dec,peak,smaj,smin,spa):
                    rdc = convert_sexa(r,d)
                    # this is tricky, to stay under 1 pixel , or you get a 2x2 back.
                    # see CubeSpectrum comments
                    region = 'centerbox[[%s,%s],[1pix,1pix]]' % (rdc[0],rdc[1])
                    imval = casa.imval(self.dir(fin),region=region)
                    peak  = imval['data']
                    flux  = peak * j * n / nppb
                    if len(flux.shape) > 1:     # rare case if we step on a boundary between cells?
                        logging.warning("source %d has spectrum shape %s: averaging the spectra" % (i,repr(flux.shape)))
                        flux = np.average(flux,axis=0)
                    rdc = convert_sexa(r,d,True)
                    snr = -1.0   # @todo
                    logging.study7("S %s %s   %g %g %g %g %g %g" % (rdc[0],rdc[1],peak,flux,j,n,a,snr))
                    # S  [w_id l_id ] ra dec peak flux smaj smin spa snr

        dt.end()

    def maxpos_im(self, im):
        """Find the position of the maximum in an image.
        Helper function returns the position of the maximum value in the
        image as an [x,y] list in 0-based pixel coordinates.

        Parameters  
        ----------
        im :  String, CASA image name

        Returns
        -------
        list
            [x,y] list in 0-based pixel coordinates.
        """
        # 2D images don't store maxpos/maxval yet, so we need to grab them
        # imstat on a 512^2 image is about 0.032 sec
        # ia.getchunk is about 0.008, about 4x faster. (but this was without grabbing mask)
        # we're going to assume 2D images fit in memory and always use getchunk
        # @todo  review the use of the new casautil.getdata() style routines
        if True:
            ia = iatool()
            ia.open(im)
            plane = ia.getchunk(blc=[0,0,0,-1],trc=[-1,-1,-1,-1],dropdeg=True)
            mask  = ia.getchunk(blc=[0,0,0,-1],trc=[-1,-1,-1,-1],dropdeg=True, getmask=True)
            #v = ma.masked_invalid(plane)
            v=ma.masked_where(mask == False,plane)

            ia.close()
            mp = np.unravel_index(v.argmax(), v.shape)
            maxval = v[mp[0],mp[1]]
            maxpos = [int(mp[0]),int(mp[1])]
        else:
            imstat0 = casa.imstat(im)
            maxpos = imstat0["maxpos"][:2].tolist()
            maxval = imstat0["max"][0]
        return (maxpos,maxval)

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           MapSources_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | sources  | table    |   table of source parameters      |
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


def convert_sexa(ra,de, to_deg=False):
    """ this peculiar function converts something like
               '18:29:56.713', '+01.13.15.61'
        to
               '18h29m56.713s', '+01d13m15.61s'

        if to_deg = True, the conversion is to degrees

        It's a mystery why the output format from casa.sourcefind()
        has this peculiar H:M:S/D.M.S format
    """
    if to_deg:
      ran = ra.replace(':',' ',1).replace(':',' ',1).split()
      den = de.replace('.',' ',1).replace('.',' ',1).split()
      rad = (float(ran[0]) + (float(ran[1]) + float(ran[2])/60.0)/60.0)*15.0
      if float(den[0]) < 0:
        ded = float(den[0]) - (float(den[1]) - float(den[2])/60.0)/60.0
      else:
        ded = float(den[0]) + (float(den[1]) + float(den[2])/60.0)/60.0
      return rad,ded
    
    ran = ra.replace(':','h',1).replace(':','m',1)+'s'
    den = de.replace('.','d',1).replace('.','m',1)+'s'
    return ran,den

