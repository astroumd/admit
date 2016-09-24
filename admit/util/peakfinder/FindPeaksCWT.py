""" .. _findpeaks:

    FindPeaksCWT --- Peak finding with continuous wavelet transforms.
    -----------------------------------------------------------------

    This module defines a wrapper class for the scipy.signal.find_peaks_cwt
    method.
"""

import types
import numpy as np
try:
  from scipy.signal import find_peaks_cwt
except:
  print "WARNING: No scipy; FindPeaksCWT utility cannot function."

class FindPeaksCWT(object):
    """ FindPeaksCWT

        Parameters
        ----------
        spec : List or numpy array
            The spectrum to be analyzed.

        x : List or numpy array, optional
            The x co-ordinates for the spectrum.
            Default = None.

        kwarg : Dict
            Any additional arguments, see the Attributes list for a complete
            listing.

        Attributes
        ----------
        spec : numpy array
            The spectrum to be analyzed.

        x : numpy array
            The x co-ordinates of the spectrum.

        widths : sequence
            1-D array of widths to use for calculating the CWT matrix. In general, this range should
            cover the expected width of peaks of interest.

        wavelet : callable, optional
            Should take a single variable and return a 1-D array to convolve with vector. Should be
            normalized to unit area.
            Default: None (ricker wavelet).

        max_distances : ndarray, optional
            At each row, a ridge line is only connected if the relative max at row[n] is within
            max_distances[n] from the relative max at row[n+1].
            Default: widths/4.

        gap_thresh : float, optional
            If a relative maximum is not found within max_distances, there will be a gap. A ridge
            line is discontinued if there are more than gap_thresh points without connecting a new
            relative maximum.
            Default: 5.

        min_length : int, optional
            Minimum length a ridge line needs to be acceptable.
            Default: cwt.shape[0] / 4, ie 1/4-th the number of widths.

        min_snr : float, optional
            Minimum SNR ratio. Default 1. The signal is the value of the cwt matrix at the shortest
            length scale (cwt[0, loc]), the noise is the noise_perc-th percentile of datapoints
            contained within a window of `window_size` around cwt[0, loc].
            Default: 3.

        noise_perc : float, optional
            When calculating the noise floor, percentile of data points examined below which to
            consider noise. Calculated using stats.scoreatpercentile.
            Default: 10.
    """
    widths = np.array([5,10,15,20,25,30])
    wavelet = None
    max_distances = None
    gap_thresh = 5.
    min_length = None
    min_snr = 3.
    noise_perc = 10.

    def __init__(self,spec,x=None,**kwargs):
        if type(spec) == types.ListType:
            self.spec = np.array(spec,dtype=float)
        else:
            self.spec = spec.astype(float)
        if x == None:
            self.x = np.arange(float(spec.shape[0]))
        else:
            if type(x) == types.ListType:
                self.spec = np.array(x,dtype=float)
            else:
                self.x = x.astype(float)

        for k,v, in kwargs.iteritems():
            # ingore any attributes we don't have
            if hasattr(self,k):
                setattr(self,k,v)

    def find(self):
        """ Method to find any peaks in the spectrum. A baseline will be subtracted first if requested.

            Parameters
            ----------
            None

            Returns
            -------
            numpy array of floats
                containing the locations of the peaks
        """
        # since some of the argument default values are calculated on the fly the full list needs to be built
        arglist = ["widths","wavelet","max_distances","gap_thresh","min_length","min_snr","noise_perc"]
        args = {}
        for arg in arglist:
            if getattr(self,arg) != None:
                args[arg] = getattr(self,arg)
        return find_peaks_cwt(self.spec, **args)
