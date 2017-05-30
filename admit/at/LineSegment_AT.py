""" .. _LineSegment-at-api:

   **LineSegment_AT** --- Finds segments of line emission in spectra.
   ------------------------------------------------------------------

   This module defines the LineSegment_AT class.
"""

# system imports
import numpy as np

# ADMIT imports
import admit
from admit.AT import AT
from admit.Summary import SummaryEntry
from admit.util import utils, specutil
import admit.util.bdp_types as bt
from admit.bdp.LineSegment_BDP import LineSegment_BDP
from admit.bdp.CubeSpectrum_BDP import CubeSpectrum_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.util import APlot
from admit.util.Image import Image
from admit.util.AdmitLogging import AdmitLogging as logging


#(see :ref:`tier-one-lineid`).
class LineSegment_AT(AT):
    """ Task for detecting segments of emission from an input spectrum, given cutoffs based on the rms noise.

        The produced LineSegment_BDP contains a list of all line segments found in the input spectrum. 
        Additionally a spectral plot with overlaid segments is produced for each input spectrum.

        **Keywords**
          **numsigma**: float
            Minimum intensity, in terms of one sigma rms noise, to consider a given channel
            to not be noise. Default: 5.0.

          **minchan**: int
            Minimum number of consecutive channels above numsigma to consider them
            part of a line. Default: 5.

          **maxgap**: int
            The maximum gap to allow between clusters of channels to consider
            them to be separate lines. Default: 3.

          **segment**: string
            The name of the segment finder algorithm to use; choices are: ASAP
            and ADMIT. (see :ref:`asapsegment` and :ref:`admitsegment` for details of each)
            Default: "ADMIT".

          **smooth**: list
            Use this parameter to smooth the input spectrum.  Format is a list containing the name of the 
            smoothing algorithm followed by the parameters for
            the algorithm, given in the order they are defined in the documentation.
            The algorithms are: boxcar, gaussian, hanning, savgol, triangle, and welch. 
            All but savgol take a single integer parameter for the width. See :ref:`filter1D` for 
            details on the individual algorithms and their keywords. 
            To do no smoothing, set the value to []. Example: ["boxcar", 7] will do
            a boxcar smooth with a width of 7.
            Default: [].

          **recalcnoise**: bool
            A boolean to indicate whether the noise should be recalculated after smoothing. True
            indicates that the noise should be recalculated, False indicates that the noise of the
            unsmoothed spectrum should be used.
            Default: False.

          **csub**: list
            The polynomial order to use for fitting the continuum of CubeStats
            and CubeSpec based spectra. All CubeStats based spectra must be
            continuum subtracted in order to obtain proper fits (peak, fwhm),
            but continuum subtraction for CubeSpectrum based spectra is optional.
            The first argument in the list is the order of polynomial to use for
            the CubeStats based spectrum and the second is the order of fit to
            use for CubeSpec based spectra.
            Default: [1, None]  (1st order for CubeStat and no fitting for
            Cubespec based spectra).

          **iterate**: bool
            If True then iterate for both the segment finder and the peak finder
            to make them both sensitive to wide and strong narrow lines.
            Default: True.

        **Input BDPs**
          At least one of the following BDPs must be specified.

          **CubeSpectrum_BDP**: count: 1 (optional)
            Input spectrum, as from `CubeSpectrum_AT <CubeSpectrum_AT.html>`_.

          **CubeStats_BDP**: count: 1 (optional)
            Alternative input spectrum, as from
            `CubeStats_AT <CubeStats_AT.html>`_.

        **Output BDPs**

          **LineSegment_BDP**: count: 1
            List of line segments.

    """
    def __init__(self, **keyval):
        keys = {"numsigma"     : 5.0,
                "minchan"      : 4,
                "maxgap"       : 3,
                "segment"      : "ADMIT",
                "smooth"       : [],
                "recalcnoise"  : False,
                "csub"         : [1, None],
                "iterate"      : True,
               }
        self.boxcar = True
        AT.__init__(self, keys, keyval)
        self._version = "1.0.3"
        self.set_bdp_in([(CubeSpectrum_BDP, 1, bt.OPTIONAL),
                         (CubeStats_BDP,    1, bt.OPTIONAL)])
        self.set_bdp_out([(LineSegment_BDP, 1)])

    def _taskargs(self):
        """ generate a task argument string for the summary taskbar """
        taskargs = " numsigma="    + str(self.getkey("numsigma"))
        taskargs = taskargs + " minchan=" + str(self.getkey("minchan"))
        taskargs = taskargs + " maxgap="  + str(self.getkey("maxgap"))
        #taskargs = taskargs + " segment=" + self.getkey("segment")
        if len(self.getkey("smooth")) != 0:
           taskargs = taskargs + " smooth="  + str(self.getkey("smooth"))
           taskargs = taskargs + " recalcnoise="  + str(self.getkey("recalcnoise"))
        taskargs = taskargs + " csub="    + str(self.getkey("csub"))
        taskargs = taskargs + " iterate="    + str(self.getkey("iterate"))
        return taskargs

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           LineSegment_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +---------+--------+---------------------------------------------+
              |   Key   | type   |    Description                              |
              +=========+========+=============================================+
              | segments| table  | table of parameters of discovered segments  |
              +---------+--------+---------------------------------------------+
              | spectra | list   | the spectral plot of signal, noise, and S/N |
              +---------+--------+---------------------------------------------+

           Parameters
           ----------
           None

           Returns
           -------
           dict
               Dictionary of SummaryEntry
        """
        if hasattr(self, "_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """ The run method, locates lines, attempts to identify them, and
            creates the BDP

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        if not self.boxcar:
            logging.info("Boxcar smoothing turned off.")
        self._summary = {}
        self.freq = []
        self.chan = []
        dt = utils.Dtime("LineSegment")  # timer for debugging
        spec_description = []
        taskargs = self._taskargs()
        statbdp = None                   # for the CubeStats BDP
        specbdp = None                   # for the CubeSpectrum BDP
        specs = []                  # to hold the input CubeSpectrum based spectra
        statspec = []             # to hold the input CubeStats based spectrum
        statseg = []                # to hold the detected segments from statspec
        specseg = []                # to hold the detected segments from specs
        #statcutoff = []           # cutoff for statspec line finding
        #speccutoff = []             # cutoff for specs line finding
        infile = ""
        if self.getkey("minchan") < 1:
            raise Exception("minchan must eb a positive value.")
        elif self.getkey("minchan") == 1 and self.getkey("iterate"):
            logging.info("iterate=True is not allowed for minchan=1, setting iterate to False")
            self.setkey("iterate",False)

        vlsr = 0.0
        # get the input bdp
        if self._bdp_in[0] is not None:
            specbdp = self._bdp_in[0]
            infile = specbdp.xmlFile
        if self._bdp_in[1] is not None:
            statbdp = self._bdp_in[1]
            infile = statbdp.xmlFile
        # still need to do this check since all are optional inputs
        if specbdp == statbdp is None:
            raise Exception("No input BDP's found.")
        imbase = self.mkext(infile, 'lseg')

        # grab any optional references overplotted on the "ll" plots

        # instantiate a plotter for all plots made herein
        self._plot_type = admit.util.PlotControl.SVG
        myplot = APlot(ptype=self._plot_type, pmode=self._plot_mode, abspath=self.dir())
        dt.tag("start")

        ############################################################################
        #  Smoothing and continuum (baseline) subtraction of input spectra         #
        ############################################################################

        # get and smooth all input spectra
        basicsegment = {"method": self.getkey("segment"),
                        "minchan": self.getkey("minchan"),
                        "maxgap": self.getkey("maxgap"),
                        "numsigma": self.getkey("numsigma"),
                        "iterate": self.getkey("iterate"),
                        "nomean": True}

       
        segargsforcont = {"name":    "Line_Segment.%i.asap" % self.id(True),
                     "pmin":    self.getkey("numsigma"),
                     "minchan": self.getkey("minchan"),
                     "maxgap":  self.getkey("maxgap")}

        if specbdp is not None:
            # get the spectrum
            specs = specutil.getspectrum(specbdp, vlsr, self.getkey("smooth"),
                                         self.getkey("recalcnoise"), basicsegment)
            # remove the continuum, if requested
            if self.getkey("csub")[1] is not None:
                logging.info("Attempting Continuum Subtraction for Input Spectra")
                order = self.getkey("csub")[1]
                specutil.contsub(self.id(True),specs, self.getkey("segment"), segargsforcont,algorithm="PolyFit",**{"deg" : order})
            else:
                for spec in specs:
                    spec.set_contin(np.zeros(len(spec)))

            for spec in specs:
                self.freq,self.chan = specutil.mergefreq(self.freq,self.chan,spec.freq(False), spec.chans(False))

        # get any input cubestats
        if statbdp is not None:
            statspec = specutil.getspectrum(statbdp, vlsr, self.getkey("smooth"),
                                            self.getkey("recalcnoise"),basicsegment)
            # remove the continuum
            if self.getkey("csub")[0] is not None:
                logging.info("Attempting Continuum Subtraction for Input CubeStats Spectra")
                order = self.getkey("csub")[0]
                specutil.contsub(self.id(True),statspec, self.getkey("segment"), segargsforcont,algorithm="PolyFit",**{"deg" : order})

            # The 'min' spectrum is inverted for segment finding.
            # Doesn't this mean it will also be plotted upside down?
            if len(statspec) > 0: statspec[1].invert()

            for spec in statspec:
                self.freq,self.chan = specutil.mergefreq(self.freq,self.chan,spec.freq(False), spec.chans(False))

        dt.tag("getspectrum")

        if isinstance(self.freq, np.ndarray):
            self.freq = self.freq.tolist()
        if isinstance(self.chan, np.ndarray):
            self.chan = self.chan.tolist()

        # search for segments of spectral line emission

        #NB: this is repetitive with basicsegment above.
        method=self.getkey("segment") 
        minchan=self.getkey("minchan")
        maxgap=self.getkey("maxgap") 
        numsigma=self.getkey("numsigma")
        iterate=self.getkey("iterate")
        
        if specbdp is not None:
            logging.info("Detecting segments in CubeSpectrum based data")
            values = specutil.findsegments(specs, method, minchan, maxgap, numsigma, iterate)
            for i, t in enumerate(values):
                specseg.append(t[0])
                specs[i].set_noise(t[2])

        if statbdp is not None:
            logging.info("Detecting segments in CubeStats based data")
            values = specutil.findsegments(statspec, method, minchan, maxgap, numsigma, iterate)
            for i, t in enumerate(values):
                statseg.append(t[0])
                # print ("MWP LINESEGMENT %d Setting noise=%f minchan=%d",(i,t[2],minchan))
                statspec[i].set_noise(t[2])
                #statcutoff.append(t[1])

        dt.tag("segment finder")            
        lsbdp = LineSegment_BDP(imbase)

        finalsegs = utils.mergesegments([statseg,specseg],len(self.freq))
        lines = specutil.linedatafromsegments(self.freq,self.chan,finalsegs,specs,statspec)
        llist = []
        for l in lines:
           lsbdp.addRow(l)
           llist.append(l)

        rdata = []

        # create the output
        label = ["Peak/Noise", "Minimum/Noise"]
        caption = ["Potential lines overlaid on peak intensity plot from CubeStats_BDP.",
                    "Potential lines overlaid on minimum intensity plot from CubeStats_BDP."]

        xlabel = "Frequency (GHz)"
        for i, spec in enumerate(statspec):
            freqs = []
            for ch in statseg[i]:
                frq = [min(spec.freq()[ch[0]], spec.freq()[ch[1]]),
                       max(spec.freq()[ch[0]], spec.freq()[ch[1]])]
                freqs.append(frq)
                rdata.append(frq)
                #print("Stats segment, peak, ratio, fwhm ",lname,peak,ratio,fwhm)
            mult = 1.
            if i == 1:
                mult = -1.
#            print("MWP statspec plot cutoff[%d] = %f, contin=%f" % (i, (statspec[i].contin() + mult*(statspec[i].noise() * self.getkey("numsigma")))[0], statspec[i].contin()[0] ) )
            myplot.segplotter(spec.freq(), spec.spec(csub=False),
                              title="Detected Line Segments", xlab=xlabel,
                              ylab=label[i], figname=imbase + "_statspec%i" % i,
                              segments=freqs, cutoff= (spec.contin() + mult*(spec.noise() * self.getkey("numsigma"))),
                              continuum=spec.contin(), thumbnail=True)
            imname = myplot.getFigure(figno=myplot.figno, relative=True)
            thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)
            image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                          thumbnailtype=bt.PNG, description=caption[i])
            lsbdp.image.addimage(image, "statspec%i" % i)
            spec_description.append([lsbdp.ra, lsbdp.dec, "", xlabel,
                                         imname, thumbnailname, caption[i],
                                         infile])

        for i in range(len(specs)):
            freqs = []
            for ch in specseg[i]:
                frq = [min(specs[i].freq()[ch[0]], specs[i].freq()[ch[1]]),
                       max(specs[i].freq()[ch[0]], specs[i].freq()[ch[1]])]
                freqs.append(frq)
                rdata.append(frq)
            myplot.segplotter(specs[i].freq(), specs[i].spec(csub=False),
                              title="Detected Line Segments", xlab=xlabel,
                              ylab="Intensity", figname=imbase + "_spec%03d" % i,
                              segments=freqs, cutoff=specs[i].contin() + (specs[i].noise() * self.getkey("numsigma")),
                              continuum=specs[i].contin(), thumbnail=True)
            imname = myplot.getFigure(figno=myplot.figno, relative=True)
            thumbnailname = myplot.getThumbnail(figno=myplot.figno,
                                                relative=True)
            caption = "Detected line segments from input spectrum #%i." % (i)
            image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                          thumbnailtype=bt.PNG, description=caption)
            lsbdp.image.addimage(image, "spec%03d" % i)
            spec_description.append([lsbdp.ra, lsbdp.dec, "", xlabel,
                                         imname, thumbnailname, caption,
                                         infile])

        caption = "Merged segments overlaid on CubeStats spectrum"

        myplot.summaryspec(statspec, specs, None, imbase + "_summary", llist)
        imname = myplot.getFigure(figno=myplot.figno, relative=True)
        thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)
        caption = "Identified segments overlaid on Signal/Noise plot of all spectra."

        image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                      thumbnailtype=bt.PNG, description=caption)

        lsbdp.image.addimage(image, "summary")
        spec_description.append([lsbdp.ra, lsbdp.dec, "", "Signal/Noise",
                                     imname, thumbnailname, caption,
                                     infile])


        self._summary["segments"] = SummaryEntry(lsbdp.table.serialize(),
                                                 "LineSegment_AT",
                                                 self.id(True), taskargs)
        self._summary["spectra"] = [SummaryEntry(spec_description,
                                                "LineSegment_AT",
                                                self.id(True), taskargs)]
        
        self.addoutput(lsbdp)
        logging.regression("LINESEG: %s" % str(rdata))
        dt.tag("done")
        dt.end()
