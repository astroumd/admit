""" .. _CubeSpectrum-at-api:

   **CubeSpectrum_AT** --- Cuts one or more spectra through a cube.
   ----------------------------------------------------------------

   This module defines the CubeSpectrum_AT class.
"""
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
from admit.util.AdmitLogging import AdmitLogging as logging

from copy import deepcopy
import numpy as np
import numpy.ma as ma
import os

try:
  import taskinit
  import casa
except:
  print "WARNING: No CASA; CubeSpectrum task cannot function."

class CubeSpectrum_AT(AT):
    """ Define one (or more) spectra through a cube.

    Either a list of positions is given directly (via the **pos=** keyword) or a set
    of BDP's can be given, each of which will accumulate its positions
    to a list of points for which the spectra are computed, as detailed below.

    See also :ref:`CubeSpectrum-AT-Design` for the design document.

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

      **SpwCube_BDP** or **LineCube_BDP**: count: 1
        One of more spectra are taken through this cube, as from an
        `Ingest_AT <Ingest_AT.html>`_,
        `ContinuumSub_AT <ContinuumSub_AT.html>`_ or
        `LineCube_AT <LineCube_AT.html>`_.

      **CubeStats_BDP**: count: 1 (optional)
        If given, the cube maxpos from this table will be used for pos=[].
        Normally the output of a `CubeStats_AT <CubeStats_AT.html>`_.

      **Moment_BDP**: count: 1 (optional)
        If given, the maxpos from this moment map will be used for pos=[].
        Note : currently this is computed on the fly, as maps don't store
        their maxpos. Typically the output of a
        `CubeSum_AT <CubeSum_AT.html>`_ or `Moment_AT <Moment_AT.html>`_.
    
      **SourceList_BDP**: count: 1 (optional)
        If given, the positions in this source list will be used. By default
        only the strongest source (index 0) is selected. Typically the output
        from `SFind2D_AT <SFind2D_AT.html>`_ on a continuum map is given here.

    **Output BDPs**

      **CubeSpectrum_BDP**: count: 1
        Spectra through the cube. Stored as a single multi-plane table if more than one
        point was used.
        Output BDP name takes from the input Image by replacing the extension with **"csp"**.
        See also :ref:`CubeSpectrum-bdp-api`.

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

      In the design document a number of options were mentioned that have not been implemented, see
      also  :ref:`CubeSpectrum-AT-Design` for that design document.

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
        self._version       = "1.1.0"
        self.set_bdp_in( [(Image_BDP,       1,bt.REQUIRED),     # 0: cube: SpwCube or LineCube allowed
                          (CubeStats_BDP,   1,bt.OPTIONAL),     # 1: stats, uses maxpos
                          (Moment_BDP,      1,bt.OPTIONAL),     # 2: map, uses the max in this image as pos=
                          (SourceList_BDP,  1,bt.OPTIONAL)])    # 3: source list, for positions
        self.set_bdp_out([(CubeSpectrum_BDP,1)])

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
        dt = utils.Dtime("CubeSpectrum")

        # our BDP's
        # b1  = input BDP
        # b1s = optional input CubeSpectrum
        # b1m = optional input Moment
        # b1p = optional input SourceList for positions
        # b2  = output BDP

        b1 = self._bdp_in[0]                                            # check input SpwCube (or LineCube)
        fin = b1.getimagefile(bt.CASA)
        if self._bdp_in[0]._type == bt.LINECUBE_BDP:
            use_vel = True
        else:
            use_vel = False

        sources = self.getkey("sources")
        pos = []                     # blank it first, then try and grab it from the optional bdp_in's
        cmean  = 0.0
        csigma = 0.0
        smax  = []                   # accumulate max in each spectrum for regression
        self.spec_description = []   # for summary()

        # get the tools
        ia = taskinit.iatool()

        if self._bdp_in[1] != None:                                      # check if CubeStats_BDP
            #print "BDP[1] type: ",self._bdp_in[1]._type
            if self._bdp_in[1]._type != bt.CUBESTATS_BDP:
                raise Exception,"bdp_in[1] not a CubeStats_BDP, should never happen"
            # a table (cubestats)
            b1s = self._bdp_in[1]
            pos.append(b1s.maxpos[0])
            pos.append(b1s.maxpos[1])
            logging.info('CubeStats::maxpos,val=%s,%f' % (str(b1s.maxpos),b1s.maxval))
            cmean  = b1s.mean
            csigma = b1s.sigma
            dt.tag("CubeStats-pos")
            
        if self._bdp_in[2] != None:                                      # check if Moment_BDP (probably from CubeSum)
            # print "BDP[2] type: ",self._bdp_in[2]._type
            if self._bdp_in[2]._type != bt.MOMENT_BDP:
                raise Exception,"bdp_in[2] not a Moment_BDP, should never happen"
            b1m = self._bdp_in[2]
            fim = b1m.getimagefile(bt.CASA)
            pos1,maxval = self.maxpos_im(self.dir(fim))     # compute maxpos, since it is not in bdp (yet)
            logging.info('CubeSum::maxpos,val=%s,%f' % (str(pos1),maxval))
            pos.append(pos1[0])
            pos.append(pos1[1])
            dt.tag("Moment-pos")

        if self._bdp_in[3] != None:                                      # check if SourceList
            # print "BDP[3] type: ",self._bdp_in[3]._type
            # a table (SourceList)
            b1p = self._bdp_in[3]
            ra   = b1p.table.getFullColumnByName("RA")
            dec  = b1p.table.getFullColumnByName("DEC")
            peak = b1p.table.getFullColumnByName("Peak")
            if sources == []:
                # use the whole SourceList
                for (r,d,p) in zip(ra,dec,peak):
                  rdc = convert_sexa(r,d)
                  pos.append(rdc[0])
                  pos.append(rdc[1])
                  logging.info('SourceList::maxpos,val=%s,%f' % (str(rdc),p))
            else:                  
                # select specific ones from the source list
                for ipos in sources:
                    if ipos < len(ra):
                        radec =  convert_sexa(ra[ipos],dec[ipos])
                        pos.append(radec[0])
                        pos.append(radec[1])
                        logging.info('SourceList::maxpos,val=%s,%f' % (str(radec),peak[ipos]))
                    else:
                        logging.warning('Skipping illegal source number %d' % ipos)

            dt.tag("SourceList-pos")

        # if pos[] still blank, use the AT keyword.
        if len(pos) == 0:
            pos = self.getkey("pos")

        # if still none, try the map center
        if len(pos) == 0:
            # @todo  this could result in a masked pixel and cause further havoc
            # @todo  could also take the reference pixel, but that could be outside image
            ia.open(self.dir(fin))
            s = ia.summary()
            pos = [int(s['shape'][0])/2, int(s['shape'][1])/2]
            logging.warning("No input positions supplied, map center choosen: %s" % str(pos))
            dt.tag("map-center")

        # exhausted all sources where pos[] can be set; if still zero, bail out
        if len(pos) == 0:
            raise Exception,"No positions found from input BDP's or pos="

        # convert this regular list to a list of tuples with duplicates removed
        # sadly the order is lost.
        pos = list(set(zip(pos[0::2],pos[1::2])))
        npos = len(pos)
        
        dt.tag("open")

        bdp_name = self.mkext(fin,"csp")
        b2 = CubeSpectrum_BDP(bdp_name)
        self.addoutput(b2)

        imval  = range(npos)                             # spectra, one for each pos (placeholder)
        planes = range(npos)                             # labels for the tables (placeholder)
        images = {}                                      # png's accumulated

        for i in range(npos):                            # loop over pos, they can have mixed types now
            sd = []
            caption = "Spectrum"
            xpos = pos[i][0]
            ypos = pos[i][1]
            if type(xpos) != type(ypos):
                print "POS:",xpos,ypos
                raise Exception,"position pair not of the same type"
            if type(xpos)==int:
                # for integers, boxes are allowed, even multiple
                box = '%d,%d,%d,%d' % (xpos,ypos,xpos,ypos)
                # convention for summary is (box)
                cbox = '(%d,%d,%d,%d)' % (xpos,ypos,xpos,ypos)
                # use extend here, not append, we want individual values in a list
                sd.extend([xpos,ypos,cbox])
                caption = "Average Spectrum at %s" % cbox
                if False:
                    # this will fail on 3D cubes (see CAS-7648)
                    imval[i] = casa.imval(self.dir(fin),box=box)
                else:
                    # work around that CAS-7648 bug 
                    # another approach is the ia.getprofile(), see CubeStats, this will
                    # also integrate over regions, imval will not (!!!)
                    region = 'centerbox[[%dpix,%dpix],[1pix,1pix]]' % (xpos,ypos)
                    caption = "Average Spectrum at %s" % region
                    imval[i] = casa.imval(self.dir(fin),region=region)
            elif type(xpos)==str:
                # this is tricky, to stay under 1 pixel , or you get a 2x2 back.
                region = 'centerbox[[%s,%s],[1pix,1pix]]' % (xpos,ypos)
                caption = "Average Spectrum at %s" % region
                sd.extend([xpos,ypos,region])
                imval[i] = casa.imval(self.dir(fin),region=region)
            else:
                print "Data type: ",type(xpos)
                raise Exception,"Data type for region not handled"
            dt.tag("imval")

            flux  = imval[i]['data']
            if len(flux.shape) > 1:     # rare case if we step on a boundary between cells?
                logging.warning("source %d has spectrum shape %s: averaging the spectra" % (i,repr(flux.shape)))
                flux = np.average(flux,axis=0)
            logging.debug('minmax: %f %f %d' % (flux.min(),flux.max(),len(flux)))
            smax.append(flux.max())
            if i==0:                                              # for first point record few extra things
                if len(imval[i]['coords'].shape) == 2:                   # normal case: 1 pixel
                    freqs = imval[i]['coords'].transpose()[2]/1e9        # convert to GHz  @todo: input units ok?
                elif len(imval[i]['coords'].shape) == 3:                 # rare case if > 1 point in imval()
                    freqs = imval[i]['coords'][0].transpose()[2]/1e9     # convert to GHz  @todo: input units ok?
                else:
                    logging.fatal("bad shape %s in freq return from imval - SHOULD NEVER HAPPEN" % imval[i]['coords'].shape)
                chans = np.arange(len(freqs))                     # channels 0..nchans-1
                unit  = imval[i]['unit']
                restfreq = casa.imhead(self.dir(fin),mode="get",hdkey="restfreq")['value']/1e9    # in GHz
                dt.tag("imhead")
                vel   = (1-freqs/restfreq)*utils.c                #  @todo : use a function (and what about relativistic?)

            # construct the Table for CubeSpectrum_BDP 
            # @todo note data needs to be a tuple, later to be column_stack'd
            labels = ["channel" ,"frequency" ,"flux" ]
            units  = ["number"  ,"GHz"       ,unit   ]
            data   = (chans     ,freqs       ,flux   )

            if i==0:
                # plane 0 : we are allowing a multiplane table, so the first plane is special
                table = Table(columns=labels,units=units,data=np.column_stack(data),planes=["0"])
            else:
                # planes 1,2,3.... are stacked onto the previous one
                table.addPlane(np.column_stack(data),"%d" % i)

            # example plot , one per position for now
            if use_vel:
                x = vel
                xlab = 'VLSR (km/s)'
            else:
                x = chans
                xlab  = 'Channel'
            y = [flux]
            sd.append(xlab)
            if type(xpos)==int:
                # grab the RA/DEC... kludgy
                h = casa.imstat(self.dir(fin),box=box)
                ra  = h['blcf'].split(',')[0]
                dec = h['blcf'].split(',')[1]
                title = '%s %d @ %d,%d = %s,%s' % (bdp_name,i,xpos,ypos,ra,dec)
            else:
                title = '%s %d @ %s,%s' % (bdp_name,i,xpos,ypos)       # or use box, once we allow non-points

            myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode, abspath=self.dir())
            ylab  = 'Flux (%s)' % unit
            p1 = "%s_%d" % (bdp_name,i)
            myplot.plotter(x,y,title,p1,xlab=xlab,ylab=ylab,thumbnail=True)
            # Why not use p1 as the key?
            ii = images["pos%d" % i] = myplot.getFigure(figno=myplot.figno,relative=True)
            thumbname = myplot.getThumbnail(figno=myplot.figno,relative=True)
            sd.extend([ii, thumbname, caption, fin])
            self.spec_description.append(sd)

        logging.regression("CSP: %s" % str(smax))

        image = Image(images=images, description="CubeSpectrum")
        b2.setkey("image",image)
        b2.setkey("table",table)
        b2.setkey("sigma",csigma)   # TODO: not always available
        b2.setkey("mean",cmean)     # TODO: not always available

        if True:
            #       @todo     only first plane due to limitation in exportTable()
            islash = bdp_name.find('/')
            if islash < 0:
                tabname = self.dir("testCubeSpectrum.tab")
            else:
                tabname = self.dir(bdp_name[:islash] + "/testCubeSpectrum.tab")
            table.exportTable(tabname,cols=["frequency" ,"flux"])
        dt.tag("done")
        # For a single spectrum this is
        # SummaryEntry([[data for spec1]], "CubeSpectrum_AT",taskid)
        # For multiple spectra this is
        # SummaryEntry([[data for spec1],[data for spec2],...], "CubeSpectrum_AT",taskid)
        self._summary["spectra"] = SummaryEntry(self.spec_description,"CubeSpectrum_AT",self.id(True))
        taskargs = "pos="+str(pos)
        taskargs += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; <span style="background-color:white">&nbsp;' + fin.split('/')[0] + '&nbsp;</span>'
        for v in self._summary:
            self._summary[v].setTaskArgs(taskargs)
        dt.tag("summary")
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
        # ia.getchunk is about 0.008, about 4x faster.
        # we're going to assume 2D images fit in memory and always use getchunk
        # @todo  review the use of the new casautil.getdata() style routines
        if True:
            ia = taskinit.iatool()
            ia.open(im)
            plane = ia.getchunk(blc=[0,0,0,-1],trc=[-1,-1,-1,-1],dropdeg=True)
            v = ma.masked_invalid(plane)
            ia.close()
            mp = np.unravel_index(v.argmax(), v.shape)
            maxval = v[mp[0],mp[1]]
            maxpos = [int(mp[0]),int(mp[1])]
        else:
            imstat0 = casa.imstat(im)
            maxpos = imstat0["maxpos"][:2].tolist()
            maxval = imstat0["max"][0]
        #print "MAXPOS_IM:::",maxpos,maxval,type(maxpos[0])
        return (maxpos,maxval)

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           CubeSpectrum_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +---------+----------+---------------------------+
              |   Key   | type     |    Description            |
              +=========+==========+===========================+
              | spectra | list     |   the spectral plots      |
              +---------+----------+---------------------------+
           
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


def convert_sexa(ra,de):
    """ this peculiar function converts something like
               '18:29:56.713', '+01.13.15.61'
        to
               '18h29m56.713s', '+01d13m15.61s'

        It's a mystery why the output format from casa.sourcefind()
        has this peculiar H:M:S/D.M.S format
    """
    ran = ra.replace(':','h',1).replace(':','m',1)+'s'
    den = de.replace('.','d',1).replace('.','m',1)+'s'
    return ran,den

