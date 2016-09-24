""" .. _peakdetect:

    PeakDetect --- Peak detection of peaks and valleys.
    ---------------------------------------------------

    This module defines a peak detection utility that looks for local 
    maxima and minima.  It is based on code by Marcos Duarte,
    https://github.com/demotu/BMC.

"""

# The MIT License (MIT)
#
# Copyright (c) 2015 Marcos Duarte, https://github.com/demotu/BMC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np
import copy

__version__ = "1.0.4"


class PeakDetect(object):
    """ Detect peaks in data based on their amplitude and other features.

        Parameters
        ----------
        spec : 1D array_like
            The input spectra to search for peaks.

        x : 1D array_like
            The x co-ordinates for the spectrum (optional).
            Default: None.

        kwarg : Dict
            Any additional arguments, see the Attributes list for a complete
            listing.

        Attributes
        ----------
        spec : 1D array_like
            The input spectra to search for peaks.

        x : 1D array_like
            The x co-ordinates for the spectrum (optional)
            Default: None.

        thresh : float
            Detect peaks that are greater than minimum peak height.
            Default: 0.0.

        min_sep : int
            Detect peaks that are at least separated by minimum peak distance, in
            number of channels.
            Default : 5.

        edge : str
            One of 'rising', 'falling', or 'both', optional.
            For a flat peak, keep only the rising edge ('rising'), only the
            falling edge ('falling'), both edges ('both').
            Default : 'rising'.

        kpsh : bool
            Keep peaks with same height even if they are closer than `min_sep`,
            optional.
            Default: False.

        Examples
        --------
        .. code-block:: python

           from admit.util.peakfinder.PeakDetect import PeakDetect
           import numpy as np
           x = np.random.randn(100)
           x[60:81] = np.nan
           # detect all peaks
           pd = PeakDetect(x)
           ind = pd.find()
           print(ind)

           x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
           # set minimum peak height = 0 and minimum peak distance = 20
           pd = PeakDetect(x, min_sep=20, thresh=0)
           ind = pd.find()

           x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
           # set minimum peak distance = 2
           pd = PeakDetect(x, min_sep=2)
           ind = pd.find()

           x = [0, 1, 1, 0, 1, 1, 0]
           # detect both edges
           pd = PeakDetect(x, edge='both')
           ind = pd.find()

    """
    # set default values
    min_sep = 5
    thresh = 0.0
    edge = 'rising'
    kpsh = False

    def __init__(self, spec, x=None, **kwarg):
        # set the x axis if it is not given
        if x is None:
            self.x = np.arange(float(spec.shape[0]))
        else:
            if isinstance(x, list):
                self.x = np.array(x, dtype=float)
            else:
                self.x = x.astype(float)
        self.spec = np.atleast_1d(spec).astype('float64')
        # set any other arguments that were given
        for k, v, in kwarg.iteritems():
            # ingore any attributes we don't have
            if hasattr(self, k):
                if type(getattr(self, k)) != type(v):
                    raise Exception("Cannot change the type of a variable in PeakDetect. %s is of type %s, not %s." % (k, type(getattr(self, k)), type(v)))
                setattr(self, k, v)

    def find(self):
        """ Method to locate peaks in an input spectrum

            Parameters
            ----------
            None

            Returns
            -------
            Numpy array containing the located peaks

        """
        # get the positive peaks
        pks = self.detect_peaks(copy.deepcopy(self.spec))
        # get the negative valleys
        pks2 = self.detect_peaks(copy.deepcopy(self.spec), True)

        peaks = []
        # get the x values of the points
        for i in np.concatenate((pks, pks2)):
            peaks.append(self.x[i])

        return np.array(peaks).astype(float)

    def detect_peaks(self, spec, valley=False):
        """ Detects peaks.

            Parameters
            ----------
            spec : 1D array
                The specrum to analyze.

            valley : bool
                Whether to search for peaks (positive) or valleys (negative).
                Default: False

            Returns
            -------
            1D array_like
                indeces of the peaks in `spec`.

            Notes
            -----
            The detection of valleys instead of peaks is performed internally by simply
            negating the data: `ind_valleys = detect_peaks(-x)`
    
            The function can handle NaN's 

            See this IPython Notebook [1]_.

            References
            ----------
            .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

        """
        # can't do any work if there are less than 3 points to work with
        if spec.size < 3:
            return np.array([], dtype=int)
        # if we are looking for valleys, then invert the spectra
        if valley:
            spec = -spec
        # find indexes of all peaks
        dx = spec[1:] - spec[:-1]
        # handle NaN's
        indnan = np.where(np.isnan(spec))[0]
        if indnan.size:
            spec[indnan] = np.inf
            dx[np.where(np.isnan(dx))[0]] = np.inf
        ine, ire, ife = np.array([[], [], []], dtype=int)
        if not self.edge:
            ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
        else:
            if self.edge.lower() in ['rising', 'both']:
                ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
            if self.edge.lower() in ['falling', 'both']:
                ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
        ind = np.unique(np.hstack((ine, ire, ife)))
        # handle NaN's
        if ind.size and indnan.size:
            # NaN's and values close to NaN's cannot be peaks
            ind = ind[np.invert(np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1)))))]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == spec.size-1:
            ind = ind[:-1]
        # remove peaks < minimum peak height
        if ind.size and self.thresh is not None:
            ind = ind[spec[ind] >= self.thresh]
        # detect small peaks closer than minimum peak distance
        if ind.size and self.min_sep > 1:
            ind = ind[np.argsort(spec[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if kpsh is True
                    idel = idel | (ind >= ind[i] - self.min_sep) & (ind <= ind[i] + self.min_sep) \
                        & (spec[ind[i]] > spec[ind] if self.kpsh else True)
                    idel[i] = 0  # Keep current peak
            # remove the small peaks and sort back the indexes by their occurrence
            ind = np.sort(ind[~idel])

        return ind
