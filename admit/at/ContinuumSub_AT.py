""" .. _ContinuumSub-at-api:

   **ContinuumSub_AT** --- Subtracts continuum emission from a cube.
   -----------------------------------------------------------------

   This module defines the ContinuumSub_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
import admit.util.casautil as casautil
import admit.util.Image as Image
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
import admit.util.Segments as Segments
from admit.bdp.SpwCube_BDP import SpwCube_BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.LineList_BDP import LineList_BDP
from admit.bdp.LineSegment_BDP import LineSegment_BDP
import admit.util.utils as utils
import admit.util.filter.Filter1D as Filter1D
from admit.util.AdmitLogging import AdmitLogging as logging
import numpy as np
import numpy.ma as ma
from copy import deepcopy

import types
import os
try:
  import casa
  import taskinit
except:
  print "WARNING: No CASA; ContinuumSub task cannot function."

class ContinuumSub_AT(AT):
    """Continuum subtraction from a cube. Produces a line cube and continuum map.

    Based on line segments found (usually from LineSegments_AT from a CubeStats_BDP)
    this AT will fit the continuum in channels not covered by the line segments.
    The continuum segments can also be explicitly given.
    This AT is meant for the automated continuum subtraction via LineSegments_AT.

    Although both are optional, you need to given either a LineSegment list, or
    explicitly define the **contsub** continuum segments.
    
    **Keywords**

        **contsub**: list of tuples 
            List a set of channel segments, 0 based and edges included,
            where the continuum is fitted. For example [(100,200),(800,900)].
            **Default**: []

        **pad**: integer
            Widen the line segments from a LineList_BDP if that was given.
            For insane reasons negative numbers are also allowed to narrow
            the segments. It will apply pad channels on either side of the segments.
            **Default**: 5
        
        **fitorder**: integer
            Order of continuum fit polynomial.
            **Default**: 0

    **Input BDPs**

        **SpwCube_BDP**: count: 1
            Input spectral window cube; e.g., as output by
            `Ingest_AT <Ingest_AT.html>`_. 

        **LineSegemnt_BDP** or **LineList_BDP**: count: 1 (optional)
            Optional line list, usually derived from 
            `LineSegment_AT <LineSegment_AT.html>`_, although
            `LineID_AT <LineID_AT.html>`_ output should also work. If given, the
            contsub= is ignored.
 
    **Output BDPs**

        **SpwCube_BDP**: 1
            Output Line Cube which should now be continuum free.
            New extension will be ".lim"

        **Image_BDP**: 1
            Output Continuum Map. 
            New extension will be ".cim"

    **Graphics Produced**
        TBD

    Parameters
    ----------
        keyval : dictionary, optional

    Attributes
    ----------
        _version : string
    """

    def __init__(self, **keyval):
        keys = {
            "contsub"    : [],      # list of tuples
            "pad"        : 5,       # see also LineCube_AT
            "fitorder"   : 0,       # polynomial order
        }
        AT.__init__(self,keys,keyval)
        self._version = "1.1.0"
        self.set_bdp_in([(SpwCube_BDP,      1, bt.REQUIRED),        # input spw cube 
                         (LineList_BDP,     1, bt.OPTIONAL),        # will catch SegmentList as well
                        ])
        self.set_bdp_out([(SpwCube_BDP,  1),                        # output line cube (.lim)
                          (Image_BDP,    1)],                       # output cont map  (.cim)
                        )

    def run(self):
        """ The run method creates the BDP.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        dt = utils.Dtime("ContinuumSub")         # tagging time
        self._summary = {}                       # an ADMIT summary will be created here

        contsub = self.getkey("contsub")
        pad = self.getkey("pad")
        fitorder = self.getkey("fitorder")

        # x.im -> x.cim + x.lim

        # b1  = input spw BDP
        # b1a = optional input {Segment,Line}List
        # b1b = optional input Cont Map (now deprecated)
        # b2  = output line cube
        # b3  = output cont map
        b1 = self._bdp_in[0]
        f1 = b1.getimagefile(bt.CASA)

        b1a = self._bdp_in[1]
        # b1b = self._bdp_in[2]      
        b1b = None                   # do not allow continuum maps to be input

        f2 = self.mkext(f1,'lim')
        f3 = self.mkext(f1,'cim')
        f3a = self.mkext(f1,'cim3d')      # temporary cube name, map is needed
        b2 = SpwCube_BDP(f2)
        b3 = Image_BDP(f3)

        self.addoutput(b2)
        self.addoutput(b3)

        ia = taskinit.iatool()

        ia.open(self.dir(f1))
        s = ia.summary()
        nchan = s['shape'][2]                # ingest has guarenteed this to the spectral axis
                        
        if b1a != None:                      # if a LineList was given, use that
            if len(b1a.table) > 0:
                # this section of code actually works for len(ch0)==0 as well
                #
                ch0 = b1a.table.getFullColumnByName("startchan")
                ch1 = b1a.table.getFullColumnByName("endchan")
                if pad != 0:                 # can widen or narrow the segments
                    if pad > 0:
                        logging.info("pad=%d to widen the segments" % pad)
                    else:
                        logging.info("pad=%d to narrow the segments" % pad)
                    ch0 = np.where(ch0-pad <  0,     0,       ch0-pad)
                    ch1 = np.where(ch1+pad >= nchan, nchan-1, ch1+pad)
                s = Segments(ch0,ch1,nchan=nchan)
                ch = s.getchannels(True)     # take the complement of lines as the continuum
            else:
                ch = range(nchan)            # no lines?  take everything as continuum (probably bad)
                logging.warning("All channels taken as continuum. Are you sure?")
        elif len(contsub) > 0:               # else if contsub[] was supplied manually
            s = Segments(contsub,nchan=nchan)
            ch = s.getchannels()
        else:
            raise Exception,"No contsub= or input LineList given"
            
        if len(ch) > 0:
            ia.open(self.dir(f1))
            ia.continuumsub(outline=self.dir(f2),outcont=self.dir(f3a),channels=ch,fitorder=fitorder)
            ia.close()
            dt.tag("continuumsub")
            casa.immoments(self.dir(f3a),-1,outfile=self.dir(f3))      # mean of the continuum cube (f3a)
            utils.remove(self.dir(f3a))                                # is the continuum map (f3)
            dt.tag("immoments")
            if b1b != None:
                # this option is now deprecated (see above, by setting b1b = None), no user option allowed
                # there is likely a mis-match in the beam, given how they are produced. So it's safer to
                # remove this here, and force the flow to smooth manually
                print "Adding back in a continuum map"
                f1b = b1b.getimagefile(bt.CASA)
                f1c = self.mkext(f1,'sum')
                # @todo   notice we are not checking for conforming mapsize and WCS
                #         and let CASA fail out if we've been bad.
                casa.immath([self.dir(f3),self.dir(f1b)],'evalexpr',self.dir(f1c),'IM0+IM1')
                utils.rename(self.dir(f1c),self.dir(f3))
                dt.tag("immath")
        else:
            raise Exception,"No channels left to determine continuum. pad=%d too large?" % pad

        # regression
        rdata = casautil.getdata(self.dir(f3)).data
        logging.regression("CSUB: %f %f" % (rdata.min(),rdata.max()))

        # Create two output images for html and their thumbnails, too
        implot = ImPlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())
        implot.plotter(rasterfile=f3,figname=f3,colorwedge=True)
        figname   = implot.getFigure(figno=implot.figno,relative=True)
        thumbname = implot.getThumbnail(figno=implot.figno,relative=True)
        b2.setkey("image", Image(images={bt.CASA:f2}))
        b3.setkey("image", Image(images={bt.CASA:f3, bt.PNG : figname}))
        dt.tag("implot")

        if len(ch) > 0:
          taskargs = "pad=%d fitorder=%d contsub=%s" % (pad,fitorder,str(contsub))
          imcaption = "Continuum map"
          self._summary["continuumsub"] = SummaryEntry([figname,thumbname,imcaption],"ContinuumSub_AT",self.id(True),taskargs)
          
        dt.tag("done")
        dt.end()

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           ContinuumSub_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +-------------+--------+---------------------------------------------+
              |   Key       | type   |    Description                              |
              +=============+========+=============================================+
              |continuumsub | list   |    Info about ContinuumSub produced         |
              +-------------+--------+---------------------------------------------+

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
