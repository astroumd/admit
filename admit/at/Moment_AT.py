""" .. _Moment-at-api:

   **Moment_AT** --- Generates various moment maps of a cube.
   ----------------------------------------------------------

   This module defines the Moment_AT class.
"""

# ADMIT imports
import admit
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.bdp.Moment_BDP import Moment_BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
import admit.util.Image as Image
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
import admit.util.utils as utils
import admit.util.casautil as casautil
from admit.util import APlot
from admit.util.AdmitLogging import AdmitLogging as logging

# CASA imports
try:
    import taskinit
    import casa
    from makemask import makemask
except:
    print "WARNING: No CASA; Moment task cannot function."

# system imports
import math
import numpy as np
import numpy.ma as ma
from copy import deepcopy


class Moment_AT(AT):
    """ AT for generating moments from an input cube BDP.

        See also :ref:`Moment-AT-design` for design documentation.

        The produced Moment_BDP(s) hold moment images and line information
        for the produced moments.

        **Keywords**
          **moments**: list of ints
            The moments to be computed. An individual BDP is created for each
            moment. See CASA's immoments documentation for a description of the
            moments that can be computed. Default: [0]. Moments are:

            + \-1   - mean value of the spectrum
            + 0   - integrated value of the spectrum
            + 1   - intensity weighted coordinate;traditionally used to get 'velocity fields'
            + 2   - intensity weighted dispersion of the coordinate; traditionally used to get "velocity dispersion"
            + 3   - median of I
            + 4   - median coordinate
            + 5   - standard deviation about the mean of the spectrum
            + 6   - root mean square of the spectrum
            + 7   - absolute mean deviation of the spectrum
            + 8   - maximum value of the spectrum
            + 9   - coordinate of the maximum value of the spectrum
            + 10  - minimum value of the spectrum


          **numsigma**: list of floats
            The lower cutoff level for each moment in terms of sigma, an entry
            for each moment can be given, or a single value can be given which
            will be applied to all moments.
            Default: [2.0].

          **sigma**: float
            The noise level to be used for calculating the cutoff values.
            Negative values indicate that the AT should compute the value.
            Inherited from the global RMS found in the CubeStats_BDP, if 
            provided.
            Default: -1.0.

          **chans**: string
            The 0-based channels to operate on, in normal CASA style. Examples are "2~10"
            for channels 2 through 10.
            Default: "" (all channels).

          **mom0clip**: float
            The clip level in the mom0 map below which other moment maps will
            be masked, but not to the mom0 map. This is in sigma units
            of that moment-0 map.
            Default: 0.0 (not applied).

          **zoom**: int
            Image zoom ratio applied to the moment map plots. This does not
            affect the base (CASA) image itself. Default: 1.

        **Input BDPs**

          **SpwCube_BDP** or **LineCube_BDP**: count: 1
            Spectral cube to take the moment(s) of, as from an
            `Ingest_AT <Ingest_AT.html>`_,
            `ContinuumSub_AT <ContinuumSub_AT.html>`_ or
            `LineCube_AT <LineCube_AT.html>`_.

          **CubeStats_BDP**: count: 1 (optional)
            Use for determining the noise level for cutoffs.
            Normally from a `CubeStats_AT <CubeStats_AT.html>`_.

        **Output BDPs**

          **Moment_BDP**: count: `varies`
            Calculated moments, one for each moment requested.

        Parameters
        ----------
        keyval : dictionary of keyword:value pairs, optional

        Attributes
        ----------
        _version : string
          Version information.
    """
    def __init__(self, **keyval):
        keys = {
            "moments"  : [0],          # default to moment 0
            "numsigma" : [2.0],        # default to 2 sigma
            "sigma"    : -1.0,         # default to determine sigma internally
            "chans"    : "",           # default to select all channels
            "mom0clip" : 0.0,          # default to not clip
            "variflow" : False,        # default to manual sub-flow management
            "zoom"     : 1,            # default map plot zoom ratio
        }
        AT.__init__(self, keys, keyval)
        self._version = "1.1.0"
        # set input types
        self.set_bdp_in([(Image_BDP,     1, bt.REQUIRED),
                         (CubeStats_BDP, 1, bt.OPTIONAL)])
        # set output types
        self.set_bdp_out([(Moment_BDP, 0)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.
        """
        if hasattr(self, "_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """ The run method, calculates the moments and creates the BDP(s)

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        self._summary = {}
        momentsummary = []
        dt = utils.Dtime("Moment")

        # variable to track if we are using a single cutoff for all moment maps
        allsame = False
        moments = self.getkey("moments")
        numsigma = self.getkey("numsigma")
        mom0clip = self.getkey("mom0clip")
        # determine if there is only 1 cutoff or if there is a cutoff for each moment
        if len(moments) != len(numsigma):
            if len(numsigma) != 1:
                raise Exception("Length of numsigma and moment lists do not match. They must be the same length or the length of the cutoff list must be 1.")
            allsame = True
        # default moment file extensions, this is information copied from casa.immoments()
        momentFileExtensions = {-1: ".average",
                                 0: ".integrated",
                                 1: ".weighted_coord",
                                 2: ".weighted_dispersion_coord",
                                 3: ".median",
                                 4: "",
                                 5: ".standard_deviation",
                                 6: ".rms",
                                 7: ".abs_mean_dev",
                                 8: ".maximum",
                                 9: ".maximum_coord",
                                10: ".minimum",
                                11: ".minimum_coord",
                                }

        logging.debug("MOMENT: %s %s %s" %  (str(moments), str(numsigma), str(allsame)))

        # get the input casa image from bdp[0]
        # also get the channels the line actually covers (if any)
        bdpin = self._bdp_in[0]
        infile = bdpin.getimagefile(bt.CASA)
        chans = self.getkey("chans")
        # the basename of the moments, we will append _0, _1, etc.
        basename = self.mkext(infile, "mom")
        fluxname = self.mkext(infile, "flux")
        # beamarea = nppb(self.dir(infile))
        beamarea = 1.0  # until we have it from the MOM0 map

        sigma0 = self.getkey("sigma")
        sigma  = sigma0

        ia = taskinit.iatool()

        dt.tag("open")

        # if no CubseStats BDP was given and no sigma was specified, find a 
        # noise level via casa.imstat()
        if self._bdp_in[1] is None and sigma <= 0.0:
            raise Exception("A sigma or a CubeStats_BDP must be input to calculate the cutoff")
        elif self._bdp_in[1] is not None:
            sigma = self._bdp_in[1].get("sigma")

        # immoments is a bit peculiar. If you give one moment, it will use 
        # exactly the outfile you picked for multiple moments, it will pick
        # extensions such as .integrated [0], .weighted_coord [1] etc.
        # we loop over the moments and will use the numeric extension instead. 
        # Might be laborious loop for big input cubes
        #
        # arguments for immoments
        args = {"imagename" : self.dir(infile),
                "moments"   : moments,
                "outfile"   : self.dir(basename)}

        # set the channels if given
        if chans != "":
            args["chans"] = chans
        # error check the mom0clip input
        if mom0clip > 0.0 and not 0 in moments:
            logging.warning("mom0clip given, but no moment0 map was requested. One will be generated anyway.")
            # add moment0 to the list of computed moments, but it has to be first
            moments.insert(0,0)
            if not allsame:
                numsigma.insert(0, 2.0*sigma)

        if allsame:
            # this is only executed now if len(moments) > 1 and len(cutoff)==1
            args["excludepix"] = [-numsigma[0] * sigma, numsigma[0] * sigma]
            casa.immoments(**args)
            dt.tag("immoments-all")
        else:
            # this is execute if len(moments)==len(cutoff) , even when len=1
            for i in range(len(moments)):
                args["excludepix"] = [-numsigma[i] * sigma, numsigma[i] * sigma]
                args["moments"] = moments[i]
                args["outfile"] = self.dir(basename + momentFileExtensions[moments[i]])
                casa.immoments(**args)
                dt.tag("immoments-%d" % moments[i])

        taskargs = "moments=%s numsigma=%s" % (str(moments), str(numsigma)) 
        if sigma0 > 0:
            taskargs = taskargs + " sigma=%.2f" % sigma0
        if mom0clip > 0:
            taskargs = taskargs + " mom0clip=%g" % mom0clip
        if chans == "": 
            taskargs = taskargs + " chans=all"
        else:
            taskargs = taskargs + " chans=%s" % str(chans)
        taskargs += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; <span style="background-color:white">&nbsp;' + basename.split('/')[0] + '&nbsp;</span>'

        # generate the mask to be applied to all but moment 0
        if mom0clip > 0.0:
            # get the statistics from mom0 map
            # this is usually a very biased map, so unclear if mom0sigma is all that reliable
            args = {"imagename": self.dir(infile)}
            stat = casa.imstat(imagename=self.dir(basename + momentFileExtensions[0]))
            mom0sigma = float(stat["sigma"][0])
            # generate a temporary masked file, mask will be copied to other moments
            args = {"imagename" : self.dir(basename + momentFileExtensions[0]),
                    "expr"      : 'IM0[IM0>%f]' % (mom0clip * mom0sigma),
                    "outfile"   : self.dir("mom0.masked")
                    }
            casa.immath(**args)
            # get the default mask name
            ia.open(self.dir("mom0.masked"))
            defmask = ia.maskhandler('default')
            ia.close()
            dt.tag("mom0clip")

        # loop over moments to rename them to _0, _1, _2 etc.
        # apply a mask as well for proper histogram creation
        map = {}
        myplot = APlot(pmode=self._plot_mode,ptype=self._plot_type,abspath=self.dir())
        implot = ImPlot(pmode=self._plot_mode,ptype=self._plot_type,abspath=self.dir())

        for mom in moments:
            figname = imagename = "%s_%i" % (basename, mom)
            tempname = basename + momentFileExtensions[mom]
            # rename and remove the old one if there is one
            utils.rename(self.dir(tempname), self.dir(imagename))
            # copy the moment0 mask if requested; this depends on that mom0 was done before
            if mom0clip > 0.0 and mom != 0:
                #print "PJT: output=%s:%s" % (self.dir(imagename), defmask[0])
                #print "PJT: inpmask=%s:%s" % (self.dir("mom0.masked"),defmask[0])
                makemask(mode="copy", inpimage=self.dir("mom0.masked"),
                         output="%s:%s" % (self.dir(imagename), defmask[0]),
                         overwrite=True, inpmask="%s:%s" % (self.dir("mom0.masked"),
                                                            defmask[0]))
                ia.open(self.dir(imagename))
                ia.maskhandler('set', defmask)
                ia.close()
                dt.tag("makemask")
            if mom == 0:
                beamarea = nppb(self.dir(imagename))
            implot.plotter(rasterfile=imagename,figname=figname,
                           colorwedge=True,zoom=self.getkey("zoom"))
            imagepng  = implot.getFigure(figno=implot.figno,relative=True)
            thumbname = implot.getThumbnail(figno=implot.figno,relative=True)
            images = {bt.CASA : imagename, bt.PNG  : imagepng}
            thumbtype=bt.PNG
            dt.tag("implot")

            # get the data for a histogram (ia access is about 1000-2000 faster than imval())
            map[mom] = casautil.getdata(self.dir(imagename))
            data = map[mom].compressed()
            dt.tag("getdata")

            # make the histogram plot

            # get the label for the x axis
            bunit = casa.imhead(imagename=self.dir(imagename), mode="get", hdkey="bunit")
            # object for the caption
            objectname = casa.imhead(imagename=self.dir(imagename), mode="get", hdkey="object")

            # Make the histogram plot
            # Since we give abspath in the constructor, figname should be relative
            auxname = imagename + '_histo'
            auxtype = bt.PNG
            myplot.histogram(columns = data,
                             figname = auxname,
                             xlab    = bunit,
                             ylab    = "Count",
                             title   = "Histogram of Moment %d: %s" % (mom, imagename), thumbnail=True)

            casaimage = Image(images    = images,
                                    auxiliary = auxname,
                                    auxtype   = auxtype,
                                    thumbnail = thumbname,
                                    thumbnailtype = thumbtype)
            auxname = myplot.getFigure(figno=myplot.figno,relative=True)
            auxthumb = myplot.getThumbnail(figno=myplot.figno,relative=True)

            if hasattr(self._bdp_in[0], "line"):   # SpwCube doesn't have Line
                line = deepcopy(getattr(self._bdp_in[0], "line"))
                if not isinstance(line, Line):
                    line = Line(name="Unidentified")
            else:
                # fake a Line if there wasn't one
                line = Line(name="Unidentified")
            # add the BDP to the output array
            self.addoutput(Moment_BDP(xmlFile=imagename, moment=mom,
                           image=deepcopy(casaimage), line=line))
            dt.tag("ren+mask_%d" % mom)

            imcaption = "%s Moment %d map of Source %s" % (line.name, mom, objectname)
            auxcaption = "Histogram of %s Moment %d of Source %s" % (line.name, mom, objectname)
            thismomentsummary = [line.name, mom, imagepng, thumbname, imcaption,
                                 auxname, auxthumb, auxcaption, infile]
            momentsummary.append(thismomentsummary)

        if map.has_key(0) and map.has_key(1) and map.has_key(2):
            logging.debug("MAPs present: %s" % (map.keys()))

            # m0 needs a new mask, inherited from the more restricted m1 (and m2)
            m0 = ma.masked_where(map[1].mask,map[0])
            m1 = map[1]
            m2 = map[2]
            m01 = m0*m1
            m02 = m0*m1*m1
            m22 = m0*m2*m2
            sum0 = m0.sum()
            vmean = m01.sum()/sum0
            # lacking the full 3D cube, get two estimates and take the max
            sig1  = math.sqrt(m02.sum()/sum0 - vmean*vmean)
            sig2  = m2.max()
            #vsig = max(sig1,sig2)
            vsig = sig1
            
            # consider clipping in the masked array (mom0clip)
            # @todo   i can't use info from line, so just borrow basename for now for grepping
            #         this also isn't really the flux, the points per beam is still in there
            loc = basename.rfind('/')
            sum1 = ma.masked_less(map[0],0.0).sum()   # mom0clip
            # print out:   LINE,FLUX1,FLUX0,BEAMAREA,VMEAN,VSIGMA for regression
            # the linechans parameter in bdpin is not useful to print out here, it's local to the LineCube
            s_vlsr = admit.Project.summaryData.get('vlsr')[0].getValue()[0]
            s_rest = admit.Project.summaryData.get('restfreq')[0].getValue()[0]/1e9
            s_line = line.frequency
            if loc>0:
                if basename[:loc][0:2] == 'U_':
                    # for U_ lines we'll reference the VLSR w.r.t. RESTFREQ in that band
                    if abs(vmean) > vsig:
                        vwarn = '*'
                    else:
                        vwarn = ''
                    vlsr = vmean + (1.0-s_line/s_rest)*utils.c
                    msg = "MOM0FLUX: %s %g %g %g %g %g %g" % (basename[:loc],map[0].sum(),sum0,beamarea,vmean,vlsr,vsig)
                else:
                    # for identified lines we'll assume the ID was correct and not bother with RESTFREQ
                    msg = "MOM0FLUX: %s %g %g %g %g %g %g" % (basename[:loc],map[0].sum(),sum0,beamarea,vmean,vmean,vsig)
            else:
                msg = "MOM0FLUX: %s %g %g %g %g %g %g" % ("SPW_FULL"    ,map[0].sum(),sum0,beamarea,vmean,vmean,vsig)
            logging.regression(msg)
            dt.tag("mom0flux")

            # create a histogram of flux per channel

            # grab the X coordinates for the histogram, we want them in km/s
            # restfreq should also be in summary
            restfreq = casa.imhead(self.dir(infile),mode="get",hdkey="restfreq")['value']/1e9    # in GHz
            # print "PJT  %.10f %.10f" % (restfreq,s_rest)
            imval0 = casa.imval(self.dir(infile))
            freqs = imval0['coords'].transpose()[2]/1e9
            x = (1-freqs/restfreq)*utils.c
            # 
            h = casa.imstat(self.dir(infile), axes=[0,1])
            if h.has_key('flux'):
                flux0 = h['flux']
            else:
                flux0 = h['sum']/beamarea
            flux0sum = flux0.sum() * abs(x[1]-x[0])
            # @todo   make a flux1 with fluxes derived from a good mask
            flux1 = flux0 
            # construct histogram
            title = 'Flux Spectrum (%g)' % flux0sum
            xlab = 'VLSR (km/s)'
            ylab = 'Flux (Jy)'
            myplot.plotter(x,[flux0,flux1],title=title,figname=fluxname,xlab=xlab,ylab=ylab,histo=True)
            dt.tag("flux-spectrum")
            
        self._summary["moments"] = SummaryEntry(momentsummary, "Moment_AT", 
                                                self.id(True), taskargs)
        # get rid of the temporary mask
        if mom0clip > 0.0: 
            utils.rmdir(self.dir("mom0.masked"))

        dt.tag("done")
        dt.end()

def nppb(image):
    """work out the flux correction, number of points per beam """
    if True:
        # more expensive, but works for non-ALMA data
        # needs to be done on the MOM0 map
        s = casa.imstat(image)
        if s.has_key('flux'):
            beamarea = s['sum'][0]/s['flux'][0]
        else:
            beamarea = 1.0
        return beamarea
    else:
        h = casa.imhead(image, mode='list')
        # @todo should we not use the casa units for this?
        try:
            bmin = h['beamminor']['value']    # beam in arcsec (not always true)
            bmaj = h['beammajor']['value'] 
            cdelt1 = h['cdelt1'] * 206265.0   # cdelt in radians
            cdelt2 = h['cdelt2'] * 206265.0
            return abs(1.13309 * bmaj * bmin / (cdelt1 * cdelt2))
        except:
            return 1.0
