""" .. _Line-at-api:

   **LineForest_AT** --- Identifies molecular lines in spectra.
   -----------------------------------------------------------

   This module defines the LineForest_AT class.
"""

# system imports
import copy
import math
import numpy as np
import numpy.ma as ma

# ADMIT imports
import admit
from admit.AT import AT
from admit.Summary import SummaryEntry
from admit.util import utils, specutil
import admit.util.bdp_types as bt
from admit.bdp.LineList_BDP import LineList_BDP
from admit.bdp.CubeSpectrum_BDP import CubeSpectrum_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.PVCorr_BDP import PVCorr_BDP
import admit.util.PlotControl as PlotControl
import admit.util.filter.Filter1D as Filter1D
from admit.util import APlot
from admit.util.Image import Image
from admit.util.Tier1DB import Tier1DB
from admit.util.AdmitLogging import AdmitLogging as logging
from admit.util import SpectralLineSearch
from admit.util import LineData
from admit.util import Segments

class LineForest_AT(AT):
    """ Task for detecting and identifying spectral lines from input spectra. All
        input spectra are assumed to be from the same data set.

        If slsearch finds no results then the line is labeled as unidentified.

        **Keywords**
          **vlsr**: float
            VLSR of the source (km/s). Default: -999999.99.

          **numsigma**: float
            Minimum intensity, in terms of the rms noise of the individual sepctra, to consider a
            given channel to not be noise. In the case of CubeStats, where the units of the spectra
            are sigma, this refers to the rms noise of the sigma spectra (noise of the noise).
            Default: 5.0.

          **minchan**: int
            Minimum number of consecutive channels above numsigma to consider them
            part of a line. Default: 4.

          **maxgap**: int
            The maximum gap to allow between clusters of channels to consider
            them to be separate lines. Default: 3.

          **identifylines**: boolean
            If True then attempt to identify any detected spectral lines. If False, then just locate
            regions of line emission and stop.
            Lines are now all marked as "U" (unidentified)
            False is useful if the rest frequency/vlsr are not known.
            If no vlsr set, this will be forced to be False, if it had been set True.
            Default: True.

          **allowexotics**: bool
            If True then do not limit the molecules that can be detected. If False, do not allow
            transitions from molecules with "exotic" atoms to be included in lists. In
            this case an exotic atom is one that is uncommon, but possible to be
            detected in the right environment. The current list of "exotic" atoms is:
            "Al", "Cl", "Mg", "Mn", "F", "Li", "Na", "K", and "Ti".
            Default: False.

          **recomblevel**: string
            What level of recombination line searching is requested. Three
            levels are available

            + `off`      no recombination lines are allowed in the results.
            + `shallow`  only H and He, alpha and beta lines are allowed in the results.
            + `deep`     any recombination line is allowed in the results.

            Default: "shallow".

          **segment**: string
            The name of the segment finder algorithm to use; choices are: ASAP
            and ADMIT. (see :ref:`asapsegment` and :ref:`admitsegment` for
            details of each)
            Default: "ADMIT".

          **online**: bool
            If True then use the online splatalogue interface for searching for transitions. If
            False the use the internal CASA slsearch. You must have an internet connection to use
            the splatalogue interface.
            Default: False.

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

          **method**: dictionary
            A dictionary containing the peak finding algorithm(s) to use as the
            keys (string) and dictionary containing the keyword/value arguments
            for the algorithm as the value. Available methods are: PeakUtils,
            FindPeaksCWT, and PeakFinder (see :ref:`peakutils`, :ref:`findpeaks`,
            and :ref:`peakfinder` for the specifics of each). If more than one
            algorithm is given then each will be used in turn.
            Default: {"PeakFinder" : {"thres"    : 0.0,
            "min_sep"   : self.minchan,
            "min_width" : self.minchan}.

          **pattern**: str
            String indicating if pattern detection is done. Patterns are defined as sets of peaks
            which have the same separation which is caused by cloud rotation, expansion, etc. A
            detailed explanation is given in the design documentation. Pattern detection works well
            so long as there are not too many lines in the spectra. The code can determine whether
            this criteria has been met. Available modes are:

            + 'ON'   Force pattern find to be on no matter what
            + 'AUTO' Run pattern detection as long as there are not too many lines
            + 'OFF'  No pattern detection

            Default: "AUTO".

          **mode**: string
            If more than one peak finding algorithms is given in **method**, how
            should the results be interpreted. Available modes are:

            + `ONE` Consider a peak to be valid if it was found by any of the
                    given methods
            + `TWO` Consider a peak to be valid if it was found by at least two
                    of the methods. (if only 1 method is specified then this
                    choice is ignored)
            + `ALL` Consider a peak to be valid if it was detected by all given
                    methods.(if only 1 method is specified then this choice is ignored)

            Default: "ONE".

          **tier1width**: float
            The width over which to search for Tier 1 lines in km/s. Any lines
            detected within this distance of a Tier 1 line will be identified
            as that line. Defaults to 300.0 for sources with a VLSR of 150 km/s
            and above, and 40.0 for sources with a VLSR below 150 km/s.

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

          **references**: str
            The filename of a references list for optional overplotting in the
            LineID plots. This is an ASCII file containing two columns:
            one column of frequencies (a float), and one column of a reference
            (line, a string). You can specify file references relative to
            `$ADMIT`, e.g., references="etc/ngc253_lines.list"
            this is preferred to keep scripts portable, but an absolute filename
            is perfectly legal.
            Default: "".

          **iterate**: bool
            If True then iterate for both the segment finder and the peak finder
            to make them both sensitive to wide and strong narrow lines.
            Default: True.

          **force**: list of tuples or LineData objects
            Force a given channel interval to be a specific line identification.
            If force is given, LineID_AT will not try to find any lines in the
            specified channel range, but rather take your input as correct.
            Format:
            [(frequency, UID, formula, name, transition, velocity, startchan, endchan)]
            Examples:
            [(115.2712, 'CO', 'CO(1-0)', 'carbon monoxide', 'J=1-0', 123.456, 23, 87)]

            [(342.998, 'Fred', 'Flintsone', 'unknown', 'unknown', 0, 64, 128),
             (238.012, 'My Favorite Molecule', 'N/A', 'N/A', 'N/A', 0, 4, 39)]

            [LineData(frequency=115.271, name='Carbon Monoxide', formula='CO',
                      uid='CO_115.271', transition='1-0', velocity=225.3,
                      chans=[25, 119])]

            Note uid is what is the label used in the plots that LineID_AT creates.
            LineData objects can be used instead of a tuple, as the contents of the tuple
            is converted to a LineData object internally anyway.
            Default: [].

          **reject**: list of tuples
            Reject a specific line identification.  Format: [(name, frequency)],
            e.g., [("carbon monoxide", 115.2712), ("carbon monosulfide", 97.981)].
            Name is case insensitive. Frequency should be given to enough
            precision that it uniquely identifies a line (a comparison is made at the
            1 part in 10^6 for matching).
            If frequency is None, all lines from the given molecule
            will be rejected, i.e. [("carbon monoxide", None)] rejects all
            CO transitions, including isotopomers: 12CO, 13CO, C18O etc.

            Default: [].

        **Input BDPs**
          At least one of the following BDPs must be specified.

          **CubeSpectrum_BDP**: count: 1 (optional)
            Input spectrum, may contain several spectra. Typically the output
            of a `CubeSpectrum_AT <CubeSpectrum_AT.html>`_ or
            `GenerateSpectrum_AT <GenerateSpectrum_AT.html>`_.

          **CubeStats_BDP**: count: 1 (optional)
            Alternative input spectrum, as from a
            `CubeStats_AT <CubeStats_AT.html>`_.

          **PVCorr_BDP**: count: 1 (optional)
            Spectrum based on the output of `PVCorr_AT <PVCorr_AT.html>`_.

        **Output BDPs**

          **LineList_BDP**: count: 1
            List of spectral lines.

    """
    def __init__(self, **keyval):
        keys = {"vlsr"         : -999999.99,         # see also Ingest_AT
                "numsigma"     : 5.0,
                "minchan"      : 4,
                "maxgap"       : 3,
                "identifylines": True,
                "allowexotics" : False,
                "recomblevel"  : "shallow",
                "segment"      : "ADMIT",
                "online"       : False,
                "smooth"       : [],
                "recalcnoise"  : False,
                "method"       : {"PeakFinder" : {"thresh"   : 0.0}},
                "pattern"      : "AUTO",
                "mode"         : "ONE",
                "tier1width"   : 0.0,
                "csub"         : [1, None],
                "references"   : "",
                "iterate"      : True,
                "force"        : [],
                "reject"       : []
               }
        AT.__init__(self, keys, keyval)
        self._version = "0.1.0"
        self.set_bdp_in([(CubeSpectrum_BDP, 1, bt.REQUIRED)])
        self.set_bdp_out([(LineList_BDP, 1)])

    def _taskargs(self):
        taskargs = ""
        identifylines = self.getkey("identifylines")
        vlsr = self.getkey("vlsr")
        if vlsr != 0.0 and identifylines and vlsr > -999998:
            taskargs = taskargs + " vlsr=%g" % vlsr
            
        taskargs = taskargs + " numsigma="    + str(self.getkey("numsigma"))
        taskargs = taskargs + " minchan=" + str(self.getkey("minchan"))
        taskargs = taskargs + " maxgap="  + str(self.getkey("maxgap"))
        if len(self.getkey("smooth")) != 0:
           taskargs = taskargs + " smooth="  + str(self.getkey("smooth"))
           taskargs = taskargs + " recalcnoise="  + str(self.getkey("recalcnoise"))
        taskargs = taskargs + " csub="    + str(self.getkey("csub"))
        taskargs = taskargs + " iterate=" + str(self.getkey("iterate"))
        taskargs = taskargs + " tier1width="+ str(self.getkey("tier1width"))
        taskargs = taskargs + " identifylines=%s" % identifylines
        if self.getkey("allowexotics"):
            taskargs = taskargs + " allowexotics=True"
        taskargs = taskargs + " recomb="  + self.getkey("recomblevel")
        return taskargs


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
        self.dt = utils.Dtime("LineForest")

        self._summary = {}
        self.spec_description = []
        taskargs = self._taskargs()
        statbdp = None                   # for the CubeStats BDP
        pvbdp = None                     # for the PVCorr BDP
        specbdp = None                   # for the CubeSpectrum BDP
        self.specs = []                  # to hold the input CubeSpectrum based spectra
        self.freq = None
        self.statspec = []               # to hold the input CubeStats based spectrum
        self.pvspec = None
        self.pvseg = []
        self.statseg = []                # to hold the detected segments from statspec
        self.specseg = []                # to hold the detected segments from specs
        self.chan = []                   # to hold the channel numbers for each channel for specs
        self.statcutoff = []             # cutoff for statspec line finding
        self.speccutoff = []             # cutoff for specs line finding
        self.infile = ""
        self.tol = self.getkey("minchan")
        self.blendcount = 1
        self.tier1chans = []             # to hold lists of Tier1 channels
        self.tier1freq = []
        self.tier1list = []
        self.force = []
        self.forcechans = []
        self.forcefreqs = []
        self.reject = self.getkey("reject")
        self.pattern = self.getkey("pattern").upper()

        if self.getkey("minchan") < 1:
            raise Exception("minchan must be a positive integer.")
        elif self.getkey("minchan") == 1 and self.getkey("iterate"):
            logging.info("iterate=True is not allowed for minchan=1, setting iterate to False")
            self.setkey("iterate", False)
        havesomething = False

        # get the input bdp
        specbdp = self._bdp_in[0]
        self.infile = specbdp.xmlFile
            
        imbase = self.mkext(self.infile, 'll')

        llbdp = LineList_BDP(imbase)

        self.vlsr = self.getkey("vlsr")
        self.identifylines = self.getkey("identifylines")
        self._plot_type = admit.util.PlotControl.SVG
        vlsr = self.vlsr 

        self.specs = specutil.getspectrum(specbdp, vlsr, self.getkey("smooth"),self.getkey("recalcnoise"), basicsegment)

        # remove the continuum, if requested
        if self.getkey("csub")[1] is not None:
            order = self.getkey("csub")[1]
            logging.info("Attempting Continuum Subtraction for Input Spectra")
            specutil.contsub(self.id(True),self.specs, self.getkey("segment"), segargsforcont,algorithm="PolyFit",**{"deg" : order})
        else:
            for spec in self.specs:
                spec.set_contin(np.zeros(len(spec)))
        for spec in self.specs:
            self.freq,self.chan = specutil.mergefreq(self.freq,self.chan,spec.freq(False), spec.chans(False))
        self.dt.tag("getspectrum-cubespecs")

        # Add spectra to the output BDPs.
        for indx, spec in enumerate(self.specs):
            llbdp.addSpectrum(spec, "CubeSpectrum_%i" % (indx))

        self._summary["linelist"] = SummaryEntry(llbdp.table.serialize(), "LineForest_AT",
                                                 self.id(True), taskargs)

        self._summary["spectra"] = [SummaryEntry(self.spec_description, "LineForest_AT",
                                                 self.id(True), taskargs)]
        self.addoutput(llbdp)
        self.dt.tag("done")
        self.dt.end()

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           LineForest_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +---------+--------+---------------------------------------------+
              |   Key   | type   |    Description                              |
              +=========+========+=============================================+
              | linelist| table  | table of parameters of discovered lines     |
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

