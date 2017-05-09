""" .. _Export-at-api:

   **Export_AT** --- Exports an Image_BDP to FITS.
   -----------------------------------------------

   This module defines the Export_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
import admit.util.casautil as casautil
import admit.util.Image as Image
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.LineList_BDP import LineList_BDP
from admit.bdp.Moment_BDP import Moment_BDP
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
  print "WARNING: No CASA; Export task cannot function."

class Export_AT(AT):
    """Creates a FITS file from an image BDP.

    Unlike the more automated export facility in ADMIT, this allows you to
    add a true FITS export atomically to the flow, with all of its flow
    dependencies.

    At a future date this task will also export other types of BDPs, e.g. tables

    Note that the output file is always overwritten.

    **Keywords**

        **basename**: string
            Basename of the file. If left blank, it will be derived from the input
            BDP by replacing the extension (usually .im, .cim, .lim) with "fits".
            This will thus also normally include whatever directory structure
            exists with the ADMIT tree.
            If the basename starts with "/" or "./", it is presumed to refer to
            an absolute reference, not something within the ADMIT directory.
            Default: "".
    
    **Input BDPs**

        **Image_BDP**: count: 1
           Input 2-D or 3-D image, such as output by
           `Ingest_AT <Ingest_AT.html>`_,
           `LineCube_AT <LineCube_AT.html>`_ or
           `Moment_AT <Moment_AT.html>`_.

    **Output BDPs**
        None

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
            "basename"   : "",     # defaults to BDP derived
        }
        AT.__init__(self,keys,keyval)
        self._version = "1.0.0"
        self.set_bdp_in([(Image_BDP,     1, bt.REQUIRED)])
        self.set_bdp_out([])

    def run(self):
        """ The run method creates the BDP

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        dt = utils.Dtime("Export")                 # tagging time

        basename = self.getkey("basename")

        nbdp = len(self._bdp_in)
        logging.info("Found %d input BDPs" % nbdp)
        if nbdp > 1:
            logging.info("Only dealing with 1 BDP now")
        
 
        b1  = self._bdp_in[0]                      # image/cube
        infile = b1.getimagefile(bt.CASA)          # ADMIT filename of the image (cube)

        if len(basename) == 0:
            fitsname = self.mkext(infile,'fits')   # morph to the new output name with replaced extension '
            image_out = self.dir(fitsname)         # absolute filename
        else:
            if basename[0:2] == './' or basename[0] == '/':
                image_out = basename + ".fits"
            else:
                image_out = self.dir(basename + ".fits")
        
        dt.tag("start")

        logging.info("Writing FITS %s" % image_out)

        # @todo   check self.dir(image_out)
        casa.exportfits(self.dir(infile), image_out, overwrite=True)
        
        dt.tag("done")
        dt.end()

    # no summary for Export_AT
    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           Export_AT does not add anything to the Summary.

           Parameters
           ----------
           None

           Returns
           -------
           dict
               Dictionary of SummaryEntry
        """
        return {}
