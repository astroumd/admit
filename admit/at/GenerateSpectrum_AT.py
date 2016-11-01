""" .. _GenerateSpectrum-at-api:

   **GenerateSpectrum_AT** --- Generates synthetic test spectra.
   -------------------------------------------------------------

   This module defines the GenerateSpectrum_AT class.
"""
from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.CubeSpectrum_BDP import CubeSpectrum_BDP
import admit.util.filter.Filter1D as Filter1D

import admit.util.Table as Table
import admit.util.utils as utils
from admit.util import APlot
import admit.util.Image as Image
from admit.util import SpectralLineSearch
from admit.Summary import SummaryEntry

import os
import numpy as np
from copy import deepcopy

class GenerateSpectrum_AT(AT):
    """ Define a synthetic CubeSpectrum for testing.

    This task is only intended to generate synthetic spectra with noise, and
    to efficiently test LineID with a CubeSpectrum_BDP input. You can add continuum
    as well, and add any number of gaussian's, or even optionally read
    in an ASCII spectrum, and add noise and gaussians to this. Multiple spectra
    can be in the CubeSpectrum_BDP.

    When noise is added, spectra have a fixed RMS = 1.0, i.e. spectra are assumed
    to be in dimensionless S/N units.

    **Keywords**
      **file**: string
        Name of an ASCII file that contains a spectrum, optional. The first column must be frequency
        and the second column must be the intensity. If you just want to read a spectrum
        and not add noise, set seed=-1.
        Default: blank.

      **nchan**: int
        Number of output channels per spectrum. Ignored when file= given.
        Default: 1000.

      **nspectra**: int
        Number of output spectra. More than one are meant for different
        random realizations of the input conditions (either from file=
        and/or from lines= via seed=), but they are all written to the same
        BDP.
        Default: 1.

      **seed**: int
        Seed for random number generator.
        0 is a special value that uses a random
        realization per call, e.g. time of the day.
        Use any other positive value to seed with a repeatable random
        sequence.
        -1 is a special value to disable the random number generator noise
        (for example if an input spectrum should not be polluted with random noise).
        Default: 0.

      **contin**: float
        Continuum level level added to the noise spectra. You can only add a continuum
        level when noise is added as well, i.e. when seed >= 0.
        Default: 0.0.

      **freq**: float
        The central frequency of the band in GHz.
        Default: 115.2712018.

      **delta**: float
        The size of each channel in MHz.
        Default: 0.5.

      **lines**: list of tuples
        Parameters for each Gaussian line. Intensity (SNR), center frequency in GHz, FHWM in km/s.
        Examples:

        [(15.0, 110.201, 22.0)]

        Produce a single Gaussian centered at 110.201 GHz that is 15.0 sigma tall with a FWHM of
        22.0 km/s.

        [(12.0, 109.98, 15.3), (6.0, 110.0, 15.0)]

        Produce two Gaussians, one centered at 109.98 GHz with a peak of 12.0 sigma and FWHM of 15.3
        kms, and a second centered at 110.0 GHz with an intensity of 6.0 sigma and FWHM of 15.0 km/s.

        Default: [].

      **transitions**: list
        List of any transitions to be included in the spectrum. Each entry should be a list
        containing the molecule name, frequency range (in GHz), intensity(SNR), FWHM in km/s and 
        offset in km/s. 
        Any tranitions from the given molecule(s) and frequency range will be
        included. Example of entry:

        [("13COv=0", [110.15, 110.25], 6.0, 30.0, 5.0),
         ("CH3CNv=0", [110.2, 110.5], 4.5, 10.0, 0.0)]

        This will produce a single 13CO line with a peak intensity of 6 sigma, FWHM of 30.0 km/s
        and centered at a offset velocity of 5.0 km/s; and a set of 6 of CH3CN lines (with hyperfine
        components), with the highest line strength transition peaking at 4.5 sigma, and the rest
        proportionally weaker based on line strength, all with a FWHM of 10.0 km/s and no offset.
        Molecules can be given multiple times for the purpose of having multiple velocity components.
        Default: [].

      **hanning**: bool
        If True then do a final (1/4,1/2,1/4) hanning smooth over 3 channels.
        Default: False.

    **Input BDPs**
      None

    **Output BDPs**

      **CubeSpectrum_BDP**: count: 1
        Spectrum through the cube. Stored as a single multi-plane table if nspectra > 1.
        Output BDP name takes from the input Image by replacing the extension with "csp".
        See also :ref:`CubeSpectrum-bdp-api`.

    Parameters
    ----------
    keyval : dictionary, optional
      Keyword values.

    Attributes
    ----------
    _version : string
      Version string.
    """

    def __init__(self,**keyval):
        keys = {"file"        : "",
                "nchan"       : 1000,
                "nspectra"    : 1,
                "seed"        : 0,               # -1 is special for no noise 
                "contin"      : 0.0,
                "freq"        : 115.2712018,
                "delta"       : 0.5,             # channel width in MHz
                "lines"       : [],              # [(snr,freq0,fwhm),...]
                "transitions" : [],
                "hanning"     : False,
        }
        AT.__init__(self,keys,keyval)
        self._version       = "1.0.0"
        self.set_bdp_in([])
        self.set_bdp_out([(CubeSpectrum_BDP,1)])
        self.spec_description = []   # for summary() 

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           GenerateSpectrum_AT adds the following to ADMIT summary:

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
        seed = self.getkey("seed")
        if seed <= 0:
            np.random.seed()
        else:
            np.random.seed(seed)
        #print "RANDOM.GET_STATE:",np.random.get_state()
        contin = self.getkey("contin")
        rms = 1.0        # not a user parameter, we do all spectra in S/N space
        f0 = self.getkey("freq")     # central frequency in band
        df = self.getkey("delta") / 1000.0      # channel width (in GHz)
        nspectra = self.getkey("nspectra")
        taskargs = " contin=%f freq=%f delta=%f nspectra=%f " % (contin,f0,df,nspectra)
        spec = range(nspectra)
        dt.tag("start")
        if self.getkey("file") != "":
            print "READING spectrum from",self.getkey("file") 
            (freq, spec[0]) = getspec(self.getkey("file"))
            nchan = len(freq)
            print "Spectrum %d chans from %f to %f: min/max = %f %f" % (nchan, freq.min(), freq.max(), spec[0].min(), spec[0].max())
            # @todo nspectra>1 not tested
            for i in range(1,nspectra):
                spec[i] = deepcopy(spec[0])
            dt.tag("getspec")                
        else:
            nchan = self.getkey("nchan")
            freq = np.arange(nchan, dtype=np.float64)
            center = int(nchan/2)
            for i in range(nchan):
                freq[i] = f0 + (float((i - center)) * df)
            for i in range(nspectra):
                spec[i] = np.zeros(nchan)
        chans = np.arange(nchan)
        taskargs += " nchan = %d" % nchan
        for i in range(nspectra):
            if seed >= 0:
                spec[i] += np.random.normal(contin, rms, nchan)
#            print "MEAN/STD",spec[i].mean(),spec[i].std()
        lines = self.getkey("lines")
        sls = SpectralLineSearch(False)
        for item in self.getkey("transitions"):
            kw = {"include_only_nrao" : True,
                  "line_strengths": ["ls1", "ls2"],
                  "energy_levels" : ["el2", "el4"],
                  "fel" : True,
                  "species" : item[0]
                  }
            results = sls.search(item[1][0], item[1][1], "off", **kw)
            # look at line strengths
            if len(results) > 0:
                mx = 0.0
                indx = -1
                for i in range(len(results)):
                    if results[i].getkey("linestrength") > mx:
                        indx = i
                        mx = results[i].getkey("linestrength")
                for res in results:
                    if mx > 0.0:
                        lines.append([item[2] * res.getkey("linestrength") / mx, res.getkey("frequency") +
                                      utils.veltofreq(item[4], res.getkey("frequency")), item[3]])
                    else:
                        lines.append([item[2], res.getkey("frequency") + utils.veltofreq(item[4], 
                                      res.getkey("frequency")), item[3]])
        for item in lines:
            for i in range(nspectra):
                spec[i] += utils.gaussian1D(freq, item[0], item[1], utils.veltofreq(item[2], item[1]))

        if self.getkey("hanning"):
            for i in range(nspectra):
                filter = Filter1D.Filter1D(spec[i], "hanning", **{"width" : 3})
                spec[i] = filter.run()
            dt.tag("hanning")
        center = int(nchan/2)
        dt.tag("open")
        bdp_name = self.mkext("Genspec","csp")
        b2 = CubeSpectrum_BDP(bdp_name)
        self.addoutput(b2)
        images = {}                                      # png's accumulated
        for i in range(nspectra):
            sd = []
            caption = "Generated Spectrum %d" % i
            # construct the Table for CubeSpectrum_BDP 
            # @todo note data needs to be a tuple, later to be column_stack'd
            labels = ["channel" ,"frequency" ,"flux" ]
            units  = ["number"  ,"GHz"       ,""   ]
            data   = (chans     ,freq       ,spec[i]   )

            # plane 0 : we are allowing a multiplane table, so the first plane is special
            if i==0:
                table = Table(columns=labels,units=units,data=np.column_stack(data),planes=["0"])
            else:
                table.addPlane(np.column_stack(data),"%d" % i)
            # example plot , one per position for now
            x = chans
            xlab  = 'Channel'
            y = [spec[i]]
            sd.append(xlab)

            myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode, abspath=self.dir())
            ylab  = 'Flux'
            p1 = "%s_%d" % (bdp_name,i)
            myplot.plotter(x,y,"",p1,xlab=xlab,ylab=ylab,thumbnail=True)
            # Why not use p1 as the key?
            ii = images["pos%d" % i] = myplot.getFigure(figno=myplot.figno,relative=True)
            thumbname = myplot.getThumbnail(figno=myplot.figno,relative=True)

            image = Image(images=images, description="CubeSpectrum")
            sd.extend([ii, thumbname, caption])
            self.spec_description.append(sd)

        self._summary["spectra"] = SummaryEntry(self.spec_description,"GenerateSpectrum_AT",self.id(True), taskargs)
        

        dt.tag("table")
        b2.setkey("image",image)
        b2.setkey("table",table)
        b2.setkey("sigma",rms)
        b2.setkey("mean",contin)

        dt.tag("done")
        dt.end()

# @todo  this could go as a very generic routine in utils
#
def getspec(file, xcol=0, ycol=1):
        """  read a spectrum/table from column 1,2 

        returns:   (freq,spec) 
        """
        lines = open(file).readlines()
        x = []
        y = []
        mincol = max(xcol,ycol) + 1
        for line in lines:
            if line[0] == '#':
                continue
            w = line.split()
            if len(w) < mincol:
                continue
            x.append(float(w[xcol]))
            y.append(float(w[ycol]))
        return (np.array(x),np.array(y))
        
