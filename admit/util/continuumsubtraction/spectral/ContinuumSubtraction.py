""" .. _spectralcontinsub:

    ContinuumSubtraction --- Subtracts the continuum from a spectrum.
    -----------------------------------------------------------------

    This module defines the class for continuum subtraction from spectra.
"""

from admit.util import utils, stats
import math
import numpy as np
import logging
from admit.util.segmentfinder import SegmentFinder

class ContinuumSubtraction(object):
    """ Perform continuum subtraction on a spectrum. There are several
        algorithms to choose from, using the algorithm keyword. This
        class defines a consistent API for spectral continuum subtraction
        in ADMIT. Any continuum subtraction method can be added provided
        it is a class with the following:

        - init signature of (self, x, y), where x is the x axis as a numpy
          and y is the spectrum as a masked array
        - run method with the signature (self, \*\*keyval), where keyval
          is a dictionary which contains all the arguments for the method
          as key value pairs, the run method should have the ability to
          ignore keywords that it does not know about.
        - the run method should return the continuum as a numpy array

        Parameters
        ----------
        None (all parameters are passed to the run method)

        Attributes
        ----------
        None

    """
    def __init__(self):
        pass

    def run(self, id, spec, freq, segmentfinder, segargs, algorithm, **keyval):
        """ Calculate the continuum using the given parameters. The method is as
            follows:

            locate regions of spectral emission
            mask out these regions
            pass the masked spectra to the given algorithm

            Parameters
            ----------
            id : int
                Task id of the AT calling this method

            spec : numpy array
                The spectrum from which the continuum is determined

            freq : numpy array
                The frequency axis of the spectrum

            segmentfinder : str
                The segment finder to use (i.e. ADMIT, ASAP, etc.)

            segargs : dict
                Dictionary containing the arguments for the segmentfinder

            algorithm : str
                The continuum finding algorithm to use (i.e. SplineFit, SVD_Vander, etc.)

            keyval : dict
                Dictionary containing the arguments for the continuum finding algorithm

        """
        cspec = np.zeros(len(spec))
        # auto add spectral info to segment finder args. 
        if not "spec" in segargs:
             segargs["spec"] = spec
        if not "freq" in segargs:
             segargs["freq"] = freq

        segments = None
        for i in [0, 1]:
            spectrum = spec.copy() - cspec
            # first get the segments of potential line emission
            sfargs = {}
            # double the minimum intensity, we just want to remove the strongest peaks
            # set other arguments for the segment finder
            sfargs["pmin"] = 2.0
            sfargs["name"] = "Line_ID.csub.%i.asap" % (id)
            sfargs["spec"] = spectrum
            sfargs["freq"] = freq
            sfargs.update(segargs)
            if i == 0:
                sfargs["abs"]  = True
            sfinder = SegmentFinder.SegmentFinder(spectrum, freq, 
                            segmentfinder, 5.0,
                            3.0, 2.0, True)
            segs, statcutoff, noise, mean = sfinder.find()
            sf = utils.getClass("util.segmentfinder", 
                               segmentfinder + "SegmentFinder", 
                               sfargs)
            #sf.set_options(threshold=math.sqrt(sfargs["pmin"]), 
            #               min_nchan=sfargs["minchan"], box_size=0.1, 
            #               average_limit=1, noise_box="box")
            # find the lines
            #segs, statcutoff, noise, mean = sfinder.find()
            if segs == segments:
                # no need to continue, we found the best fit
                return cspec

            keyval["noise"] = noise
            # now set the identified regions to 0.0
            for ch in segs:
                for i in range(ch[0],ch[1] + 1):
                    spectrum[i] = 0.0
            # mask all values that are 0.0, effectively masking all line data
            # this should leave only continuum
            if len(segs) == 0:
                mspec = np.ma.array(spectrum,mask=False,copy=True,shrink=False)
            else:
                mspec = np.ma.masked_values(spectrum,0.0,atol=1e-10,copy=True,shrink=False)
            tempc = np.array([noise] * len(mspec))
            keyval["chisq"] = stats.reducedchisquared(mspec, tempc, 1, noise)

            # calculate the continuum
            cs = utils.getClass("util.continuumsubtraction.spectral.algorithms",
                                algorithm, {"y" : mspec, "x" : np.arange(len(mspec))})
            continuum = cs.run(**keyval)
            if continuum is not None:
                cspec += continuum
            else:
                logging.warning("Setting continuum to a constant value of: " + str(noise))
                return tempc
        return cspec
