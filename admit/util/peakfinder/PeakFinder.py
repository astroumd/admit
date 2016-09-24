""" .. _peakfinder:

    PeakFinder --- Peak finding with derivatives.
    ---------------------------------------------

    This module defines a peak finding utility using the derivative of
    the spectral line profile.

"""
import numpy as np


class PeakFinder(object):
    """ PeakFinder searches for spectral peaks by taking the first derivative of the
        spectrum and looks for zero crossings. Noise spikes are eliminated by
        a noise cutoff, minimum separation of points, and minimum width of lines.

        Parameters
        ----------
        spec : List or numpy array
            The spectrum to be analyzed.

        x : List or numpy array, optional
            The x co-ordinates for the spectrum.
            Default: None.

        kwarg : Dict
            Any additional arguments, see the Attributes list for a complete
            listing.

        Attributes
        ----------
        spec : numpy array
            The spectrum to be analyzed.

        x : numpy array
            The x co-ordinates of the spectrum.

        thresh : float, optional
            The cutoff used to determine if a peak is above the noise. The absolute
            value of the spectrum is compared to this so that absorption lines are
            also detected.
            Default: 0.0.

        min_sep : int
            The minimum separation between peaks in channels.
            Default: 5.

        min_width : int
            The minimum width of a line to consider, in channels.
            Default: 5.

    """
    thresh = 0.0
    min_sep = 5
    min_width = 5

    def __init__(self, spec, x=None, **kwarg):
        if isinstance(spec, list):
            self.spec = np.array(abs(spec), dtype=float)
        else:
            self.spec = abs(spec.astype(float))
        if x is None:
            self.x = np.arange(float(spec.shape[0]))
        else:
            if isinstance(x, list):
                self.x = np.array(x, dtype=float)
            else:
                self.x = x.astype(float)
        for k, v, in kwarg.iteritems():
            # ingore any attributes we don't have
            if hasattr(self, k):
                if type(getattr(self, k)) != type(v):
                    raise Exception("Cannot change the type of a variable in PeakUtils. %s is of type %s, not %s." % (k, type(getattr(self, k)), type(v)))
                setattr(self, k, v)

    def wideenough(self, pk, mult=1):
        """ Method to determine whether a line is wide enough, based on the given 
            parameters.

            Parameters
            ----------
            pk : int
                The peak to examine (in channel units)

            mult : int
                A mulitpiler to use for the noise level cutoff
                Default: 1

            Returns
            -------
            True of the line meets the minimum width criteria in self.min_width, False
            otherwise

        """
        for i in range(2 * self.min_width):
            if self.spec[min(max(0, pk - self.min_width + i), len(self.spec) - 2):
                         max(1, min(pk + i, len(self.spec) - 1))].min() > mult * self.thresh:
                return True
        # check if there is a single low channel
        start = max(0, pk - self.min_width)
        end = min(len(self.spec) - self.min_width, pk + self.min_width)
        for i in range(start, end + 1):
            if np.sort(self.spec[i: i + self.min_width])[1] > mult * self.thresh :
                return True

        return False

    def find(self):
        """ Method to locate peaks in an input spectrum

            Parameters
            ----------
            None

            Returns
            -------
            Numpy array containing the located peaks

        """
        self.min_width += int(self.min_width) % 2
        hw = int(self.min_width / 2)
        minpeaks = []
        maxpeaks = []
        # determine which points are above the cutoff and set flags appropriately
        flag = np.ones(len(self.spec), dtype=bool)
        flag[abs(self.spec) < self.thresh] = False
        #print self.spec
        #print flag,"\n"

        dx = np.diff(self.spec).tolist()

        # get the initial peaks
        for i in range(1,len(dx) - 1):
            if flag[i]:
                if self.spec[i] <= -1 * self.thresh:
                    if dx[i] < 0.0 < dx[i + 1]:
                        minpeaks.append(i + 1)
                    elif dx[i] > 0.0 > dx[i - 1]:
                        minpeaks.append(i)
                elif self.spec[i] >= self.thresh:
                    if dx[i] < 0.0 < dx[i - 1]:
                        maxpeaks.append(i)
                    elif dx[i] > 0.0 > dx[i + 1]:
                        maxpeaks.append(i + 1)

        # refine
        # 1. remove "false" peaks
        # 2. remove peaks that are too close together, favor the one with highest flux
        # do gaussian fit to get proper peak
        for i in range(len(maxpeaks) - 1, -1, -1):
            pk = maxpeaks[i]
            if self.spec[max(0, pk - hw):min(pk + hw, len(self.spec) - 1)].argmax() != hw \
               or not self.wideenough(pk):
                del maxpeaks[i]
        for i in range(len(minpeaks) - 1, -1, -1):
            pk = minpeaks[i]
            if self.spec[max(0, pk - hw):min(pk + hw, len(self.spec) - 1)].argmax() != hw:
                del minpeaks[i]

        for i in range(len(maxpeaks) - 1):
            if abs(maxpeaks[i] - maxpeaks[i + 1]) < self.min_sep:
                if self.spec[maxpeaks[i]] > self.spec[maxpeaks[i + 1]]:
                    maxpeaks[i + 1] = -10
                else:
                    maxpeaks[i] = -10
        maxpeaks[:] = [x for x in maxpeaks if x >= 0]
        for i in range(len(minpeaks) - 1):
            if abs(maxpeaks[i] - maxpeaks[i + 1]) < self.min_sep:
                minpeaks[minpeaks.index(self.spec.index(min(self.spec[minpeaks[i]],
                                                            self.spec[minpeaks[i + 1]])))] = 0
        minpeaks[:] = [x for x in minpeaks if x >= 0]
        peaks = []
        # now eliminate any peaks that do not have at least a cutoff's worth of dip between them
        remove = set()
        for i in range(len(maxpeaks) - 1):
            for j in range(i + 1, len(maxpeaks)):
                mn = min(self.spec[maxpeaks[i]:maxpeaks[j] + 1])
                if max(self.spec[maxpeaks[i]], self.spec[maxpeaks[j]]) - mn < self.thresh:
                    if self.spec[maxpeaks[i]] < self.spec[maxpeaks[j]]:
                        remove.add(maxpeaks[i])
                    else:
                        remove.add(maxpeaks[j])
        for r in remove:
            maxpeaks.remove(r)
        remove = set()
        for i in range(len(minpeaks) - 1):
            for j in range(i + 1, len(minpeaks)):
                mx = max(self.spec[minpeaks[i]:minpeaks[j] + 1])
                if abs(min(self.spec[minpeaks[i]], self.spec[minpeaks[j]]) - mn) < self.thresh:
                    if self.spec[maxpeaks[i]] > self.spec[maxpeaks[j]]:
                        remove.add(maxpeaks[i])
                    else:
                        remove.add(maxpeaks[j])
        for r in remove:
            minpeaks.remove(r)

        for i in maxpeaks + minpeaks:
            peaks.append(self.x[i])
        return np.array(peaks).astype(float)
