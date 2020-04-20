""" .. _CubeSum-at-api:

   **CubeSum_AT** --- Sums the emission in a cube.
   -----------------------------------------------

   This module defines the CubeSum_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
from admit.util import APlot
import admit.util.bdp_types as bt
import admit.util.casautil as casautil
import admit.util.Image as Image
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
import admit.util.Segments as Segments
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
  print "WARNING: No CASA; CubeSum task cannot function."

class CubeSum_AT(AT):
    """Creates a moment-0 map of a cube, with optional channel segment selection.

    In optical astronomy this would be called a white light image.  In
    radio astronomy it's often called a Moment-0 map.  CubeSum_AT is a
    special version of Moment_AT, mostly used to produce an unbiased
    reference line emission image, one that eliminates most of the
    (optionally frequency dependent) noise. Since it is not interested
    in the possibly many lines in the cube, it only adds up the
    emission.  Higher order moments are thus meaningless. Use the
    LineID_AT/LineCube_AT/Moment_AT sequence to get meaningful higher
    order moments. This image is often used as a reference image to
    extract positions for CubeSpectrum_AT, or for PVSlice_AT to compute
    a best slice based on the moments of inertia in this map.

    An optional CubeStats_BDP can be given, which will also contain
    the variation of the RMS accross the channels in this spectral window, from
    which one can judge if a channel based RMS clipping is really
    needed. In most cases this is not.
    NOTE: Currently channel based RMS clipping can be slow.

    Also optionally a LineList_BDP (from LineSegment_AT or LineID_AT) can
    be added to the input, in which case you can select if the line
    segments are used to form an even better CubeSum. You can also select its complement,
    using linesum=False, in effect creating an image where only noise
    should be present (assuming the continuum had been subtracted properly).
    numsigma=0 is recommended in this case. This image is recommended
    to test your continuum subtraction strategy and should thus only contain
    noise and no obvious source structure.

    See also :ref:`CubeSum-AT-Design` for the design document.

    **Keywords**

        **numsigma**: float
            The cutoff level for the moment map in terms of the characterictic
            noise, sigma. How sigma is determined, can be set via the sigma= keyword.
            Note that the values above numsigma*sigma and below -numsigma*sigma
            will be taken into the sum in order for this imagine to be unbiased,
            and for properly continuum subtracted cubes display absorbtion signal.
            **Default**: 2.0.

        **sigma**: float
            The noise level to be used for calculating the cutoff values. 
            If a CubeStats_BDP is provided and sigma is provided negative, then CubeSum_AT
            uses the frequency-dependent sigma from the CubeStats_BDP used in
            the cutoff. This sigma was determined for each plane in the input cube.
            If a CubeStats_BDP is provided and sigma is provided positive, then the sigma
            is taken from its cube rms value and the actual value of sigma is ignored.
            If a CubeStats_BDP is not provided, sigma must be set to a positive value
            for masking. Otherwise, an exception will be thrown. A negative value is
            not allowed in this case.
            **Default**: -1.0. Units are those of the input image, typically Jy/beam.
        
        **linesum**: boolean
            Only used if a LineList_BDP is part of the input. In that case by default
            the line segments will be used to add to the Moment-0. If linesum=False,
            its complement (supposedly just noise) will be used.
            **Default**: True.

        **pad**: integer
            Extra channels added on either side of a line (as given by
            the LineList).  
            **Default**: 5.

        **zoom**: int
          Image zoom ratio applied to the moment map plots. This does not
          affect the base (CASA) image itself. Default: 1.


    **Input BDPs**

        **SpwCube_BDP**: count: 1
           Input spectral window cube; usually the output of an
           `Ingest_AT <Ingest_AT.html>`_.

        **CubeStats_BDP**: count: 1 (optional)
            Optional input for the global RMS or channel-based RMS (if
            sigma>0). Note that tracking channel-based RMS is currently very
            expensive. Normally the output of a
            `CubeStats_AT <CubeStats_AT.html>`_.
 
        **LineList_BDP**: count: 1 (optional)
            Optional input of a LineList in case channels segments are selected
            or rejected to be included; usually the output of a
            `LineID_AT <LineID_AT.html>`_. A LineSegment_BDP (from
            `LineSegment_AT <LineSegment_AT.html>`_) is also allowed.

    **Output BDPs**

        **Moment_BDP**: count: 1

    **Graphics Produced**
        TBD

    Parameters
    ----------
        keyval : dictionary, optional

    Attributes
    ----------
        _version : string

    """
    
    ### deprecated keywords
    
    """
        **smooth** : tuple   (NOTE: THIS IS NOW A LIST, with a standard interface)                                                                     
            A tuple of length 2. The first element is a string giving the                 
            smoothing method to use; choices are: 'savgol', 'boxcar', 'gaussian', 'hanning',                  
            'triangle', and 'welch'. The second element is a dictionary given any keyword/value
            arguments for the smoothing algorithm. See :ref:`filter1D` for details on the 
            individual methods and their keywords. For example
            {"window_size" : 7, "order" : 3, "deriv" : 0}
            This keyword is also used by LineID_AT.
            **Default**: ()
    """
 
    # @todo  it should also write a theoretical sigma into the header, based on the sigma
    #        in the spw cube and # channels (sigma/sqrt(N)) used.
    #
       
    def __init__(self, **keyval):
        keys = {
            "numsigma"   : 2.0,    # default to 2.0*sigma cutoff
            "sigma"      : -1.0,   # default to CubeStats rms(freq)
            "linesum"    : True,   # Select line segments for from the (optional) LineList
            "pad"        : 5,      # number of channels to pad onto the line segments from LineList
            "zoom"       : 1,      # default map plot zoom ratio
            # "cont"     : True,   # force averaging to make it a continuum     @todo
        }
        AT.__init__(self,keys,keyval)
        self._version = "1.1.0-issue34"
        self.set_bdp_in([(Image_BDP,     1, bt.REQUIRED),
                         (CubeStats_BDP, 1, bt.OPTIONAL),
                         (LineList_BDP,  1, bt.OPTIONAL)])    # LineSegment_BDP also allowed
        self.set_bdp_out([(Moment_BDP,1)])

    def run(self):
        """ The run method creates the BDP

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        dt = utils.Dtime("CubeSum")              # tagging time
        self._summary = {}                       # an ADMIT summary will be created here
 
        numsigma = self.getkey("numsigma")       # get the input keys
        sigma = self.getkey("sigma")
        use_lines = self.getkey("linesum")
        pad = self.getkey("pad") 

        b1  = self._bdp_in[0]                    # spw image cube
        b1a = self._bdp_in[1]                    # cubestats (optional)
        b1b = self._bdp_in[2]                    # linelist  (optional)

        ia = taskinit.iatool()

        f1 =  b1.getimagefile(bt.CASA)
        ia.open(self.dir(f1))
        s = ia.summary()
        nchan = s['shape'][2]

        if b1b != None:
            ch0 = b1b.table.getFullColumnByName("startchan")
            ch1 = b1b.table.getFullColumnByName("endchan")
            s = Segments(ch0,ch1,nchan=nchan)
            # @todo something isn't merging here as i would have expected,
            #       e.g. test0.fits [(16, 32), (16, 30), (16, 29)]
            if pad > 0:
                for (c0,c1) in s.getsegmentsastuples():
                    s.append([c0-pad,c0])
                    s.append([c1,c1+pad])
            s.merge()
            s.recalcmask()
            # print "PJT segments:",s.getsegmentsastuples()
            ns = len(s.getsegmentsastuples())
            chans = s.chans(not use_lines)
            if use_lines:
                msum = s.getmask()
            else:
                msum = 1 - s.getmask()
            logging.info("Read %d segments" % ns)
            # print "chans",chans
            # print "msum",msum

        #  from a deprecated keyword, but kept here to pre-smooth the spectrum before clipping
        #  examples are:  ['boxcar',3]    ['gaussian',7]    ['hanning',5] 
        smooth= []
                
        sig_const = False                        # figure out if sigma is taken as constant in the cube
        if b1a == None:                          # if no 2nd BDP was given, sigma needs to be specified 
            if sigma <= 0.0:
                raise Exception,"Neither user-supplied sigma nor CubeStats_BDP input given. One is required."
            else:
                sig_const = True                 # and is constant
        else:
            if sigma > 0:
                sigma = b1a.get("sigma")
                sig_const = True

        if sig_const:
            logging.info("Using constant sigma = %f" % sigma)
        else:
            logging.info("Using varying sigma per plane")

        infile = b1.getimagefile(bt.CASA)          # ADMIT filename of the image (cube)
        bdp_name = self.mkext(infile,'csm')        # morph to the new output name with replaced extension 'csm'
        image_out = self.dir(bdp_name)             # absolute filename
        
        args = {"imagename" : self.dir(infile)}    # assemble arguments for immoments()
        args["moments"] = 0                        # only need moments=0 (or [0] is ok as well)
        args["outfile"] = image_out                # note full pathname

        dt.tag("start")

        if sig_const:
            args["excludepix"] = [-numsigma*sigma, numsigma*sigma]        # single global sigma
            if b1b != None:
                # print "PJT: ",chans
                args["chans"] = chans
        else:
            # @todo    in this section bad channels can cause a fully masked cubesum = bad
            # cubestats input
            sigma_array = b1a.table.getColumnByName("sigma")              # channel dependent sigma
            sigma_pos = sigma_array[np.where(sigma_array>0)]
            smin = sigma_pos.min()
            smax = sigma_pos.max()
            logging.info("sigma varies from %f to %f" % (smin,smax))
            maxval = b1a.get("maxval")                                    # max in cube
            nzeros = len(np.where(sigma_array<=0.0)[0])                   # check bad channels
            if nzeros > 0:
                logging.warning("There are %d NaN channels " % nzeros)
                # raise Exception,"need to recode CubeSum or use constant sigma" 
            dt.tag("grab_sig")

            if len(smooth) > 0:
                # see also LineID and others
                filter = Filter1D.Filter1D(sigma_array,smooth[0],**Filter1D.Filter1D.convertargs(smooth))
                sigma_array = filter.run()
                dt.tag("smooth_sig")
            # create a CASA image copy for making the mirror sigma cube to mask against
            file = self.dir(infile)
            mask = file+"_mask"
            ia.fromimage(infile=file, outfile=mask)
            nx = ia.shape()[0]
            ny = ia.shape()[1]
            nchan = ia.shape()[2]
            ia.fromshape(shape=[nx,ny,1])
            plane = ia.getchunk([0,0,0],[-1,-1,0])     # convenience plane for masking operation
            dt.tag("mask_sig")

            ia.open(mask) 
            dt.tag("open_mask")
              
            count = 0
            for i in range(nchan):
                if sigma_array[i] > 0:
                    if b1b != None:
                        if msum[i]:
                            ia.putchunk(plane*0+sigma_array[i],blc=[0,0,i,-1])
                            count = count + 1
                        else:
                            ia.putchunk(plane*0+maxval,blc=[0,0,i,-1])                            
                    else:
                        ia.putchunk(plane*0+sigma_array[i],blc=[0,0,i,-1])
                        count = count + 1
                else:
                    ia.putchunk(plane*0+maxval,blc=[0,0,i,-1])
            ia.close()
            logging.info("%d/%d channels used for CubeSum" % (count,nchan))
            dt.tag("close_mask")

            names = [file, mask]
            tmp = file + '.tmp'
            if numsigma == 0.0:
                # hopefully this will also make use of the mask
                exp = "IM0[IM1<%f]" % (0.99*maxval)
            else:
                exp = "IM0[abs(IM0/IM1)>%f]" % (numsigma)
            # print "PJT: exp",exp
            casa.immath(mode='evalexpr', imagename=names, expr=exp, outfile=tmp) 
            args["imagename"] = tmp
            dt.tag("immath")

          
        if nchan == 1:
            logging.info("Assumed continuum - see issue 34")
            args["moments"] = -1    # force continuum   @todo   should we force this via a keyword?
        casa.immoments(**args) 
        dt.tag("immoments")

        if sig_const is False:  
            # get rid of temporary files
            utils.remove(tmp)
            utils.remove(mask)

        # get the flux
        ia.open(image_out)
        st = ia.statistics()
        ia.close()
        dt.tag("statistics")
        # report that flux, but there's no way to get the units from casa it seems
        # ia.summary()['unit'] is usually 'Jy/beam.km/s' for ALMA
        # imstat() does seem to know it.
        if st.has_key('flux'):
            rdata = [st['flux'][0],st['sum'][0]]
            logging.info("Total flux: %f (sum=%f)" % (st['flux'],st['sum']))
        else:
            rdata = [st['sum'][0]]
            logging.info("Sum: %f (beam parameters missing)" % (st['sum']))
        logging.regression("CSM: %s" % str(rdata))
            
        # Create two output images for html and their thumbnails, too
        implot = ImPlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())
        implot.plotter(rasterfile=bdp_name,figname=bdp_name,
                       colorwedge=True,zoom=self.getkey("zoom"))
        figname   = implot.getFigure(figno=implot.figno,relative=True)
        thumbname = implot.getThumbnail(figno=implot.figno,relative=True)
       
        dt.tag("implot")

        thumbtype = bt.PNG            # really should be correlated with self._plot_type!!

        # 2. Create a histogram of the map data
        # get the data for a histogram
        data = casautil.getdata(image_out,zeromask=True).compressed()
        dt.tag("getdata")

        # get the label for the x axis
        bunit = casa.imhead(imagename=image_out, mode="get", hdkey="bunit")

        # Make the histogram plot
        # Since we give abspath in the constructor, figname should be relative
        myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())
        auxname = bdp_name + "_histo"
        auxtype = bt.PNG  # really should be correlated with self._plot_type!!
        myplot.histogram(columns = data,
                         figname = auxname,
                         xlab    = bunit,
                         ylab    = "Count",
                         title   = "Histogram of CubeSum: %s" % (bdp_name),
                         thumbnail=True)
        auxname = myplot.getFigure(figno=myplot.figno,relative=True)
        auxthumb = myplot.getThumbnail(figno=myplot.figno,relative=True)

        images = {bt.CASA : bdp_name, bt.PNG : figname}
        casaimage = Image(images    = images,
                                auxiliary = auxname,
                                auxtype   = auxtype,
                                thumbnail = thumbname,
                                thumbnailtype = thumbtype)

        if hasattr(b1,"line"):                      # SpwCube doesn't have Line
            line = deepcopy(getattr(b1,"line"))
            if type(line) != type(Line):
                line = Line(name="Undetermined")
        else:
            line = Line(name="Undetermined")    # fake a Line if there wasn't one

        self.addoutput(Moment_BDP(xmlFile=bdp_name,moment=0,image=deepcopy(casaimage),line=line))
        imcaption = "Integral (moment 0) of all emission in image cube"
        auxcaption = "Histogram of cube sum for image cube"
        taskargs = "numsigma=%.1f sigma=%g smooth=%s" % (numsigma, sigma, str(smooth))
        self._summary["cubesum"] = SummaryEntry([figname,thumbname,imcaption,auxname,auxthumb,auxcaption,bdp_name,infile],"CubeSum_AT",self.id(True),taskargs)

        ia.done()
        
        dt.tag("done")
        dt.end()

    # @todo i don't see this table in HTML
    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           CubeSum_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +---------+--------+---------------------------------------------+
              |   Key   | type   |    Description                              |
              +=========+========+=============================================+
              | cubesum | list   |    Info about CubeSum produced              |
              +---------+--------+---------------------------------------------+

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
