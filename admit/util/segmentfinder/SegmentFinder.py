""" .. _segmentfinder:

    SegmentFinder --- Top-level spectral emission segment finder.
    -------------------------------------------------------------

    This module defines base segment finder for ADMIT. It calls the requested segment finder.

"""
# system imports
import math
import copy

# ADMIT imports
from admit.util import utils

class SegmentFinder(object):
    """ This class is used to find segments of emission in spectra. It calls the requested
        segment finder and can iterate over the inputs to find both wider weaker segments as
        well as stronger narrower ones. The iteration is done by conserving the product of
        numsigma * minchan. The first run keeps both values as they were input, subsequent
        runs decrease the minchan by 1 and increase numsigma so that the product is conserved.
        This is repeated as long as minchan > 1. The results of the iterations are merged together
        and a single list of channel ranges is returned.

        Parameters
        ----------
        spectrum : array like
            The input spectrum from which the segments are detected.

        freq : array like
            The frequency axis of the spectrum, must have the same length as
            spectrum.

        method : str
            The segment finding method to use (e.g. "ADMIT", "ASAP").

        minchan : int
            The minimum number of channels that a segment must span.

        maxgap : int
            The maximum number of channels below the cutoff, to allow in the middle
            of a segment. Gaps larger than this will start a new segment.

        numsigma : float
            The minimum number of sigma a channel must be in order to consider it part
            of a segment.

        iterate : bool
            If True then iterate over the minchan and numsigma to detect stronger, but
            narrower lines.
            Default: False.

        Attributes
        ----------
        spectrum : array like
            The input spectrum from which the segments are detected.

        freq : array like
            The frequency axis of the spectrum, must have the same length as
            spectrum.

        method : str
            The segment finding method to use (e.g. "ADMIT", "ASAP").

        minchan : int
            The minimum number of channels that a segment must span.

        maxgap : int
            The maximum number of channels below the cutoff, to allow in the middle
            of a segment. Gaps larger than this will start a new segment.

        numsigma : float
            The minimum number of sigma a channel must be in order to consider it part
            of a segment.

        iterate : bool
            If True then iterate over the minchan and numsigma to detect stronger, but
            narrower lines.

        area : float
            The area (numsigma * minchan) which is conserved while iterating.

    """
    def __init__(self, spectrum, freq, method, minchan, maxgap, numsigma, iterate=False,
                 noise=None, nomean=False):
        self.spectrum = spectrum
        self.freq = freq
        self.method = method
        self.minchan = minchan
        self.numsigma = numsigma
        self.maxgap = maxgap
        self.iterate = iterate
        self.noise = noise
        self.nomean = nomean
        self.area = self.numsigma * float(self.minchan)

    def find(self):
        """ Method to find segments in the input spectrum, using the given method.
            If iterate is set to True then the segment finder is called multiple
            times, each run decreasing the minchan by one and increasing numsigma
            (while conserving the product of the two), until minchan = 1, then the
            cycle is stopped (single channel spikes, no matter how strong, will
            not be detected).

            Parameters
            ----------
            None

            Returns
            -------
            Four items: list of the segment start and end points, the cutoff, the noise
            of the spectrum, and the mean of the spectrum.

        """
        results = []        # list to hold the results of each iteration
        cutoff = []         # list to hold the cutoff from each iteration
        noise = []          # list to hold the noise from each iteration
        mean = []           # list to hold the mean from each iteration

        # keep iterating as long as minchan is greater than 1
        while (self.minchan > 1 and self.iterate) or (self.minchan > 0 and not self.iterate):
            # find the segments with the current parameters
            sfinder = utils.getClass("util.segmentfinder",
                                     self.method + "SegmentFinder",
                                     {"name":    "Line_ID.%i.asap" % 100,
                                      "spec":    self.spectrum,
                                      "pmin":    self.numsigma,
                                      "minchan": self.minchan,
                                      "maxgap":  self.maxgap,
                                      "freq":    self.freq,
                                      "noise":   self.noise,
                                      "nomean":  self.nomean})
            sfinder.set_options(threshold=math.sqrt(float(self.numsigma)),
                                min_nchan=self.minchan, box_size=0.1,
                                average_limit=1, noise_box="box")
            # find the segments
            seg, cut, noi, mn = sfinder.find()
            del sfinder
            # append the results
            if not self.iterate:
                # if not iterating then just return the results
                return seg, cut, noi, mn
            results.append(seg)
            cutoff.append(cut)
            noise.append(noi)
            mean.append(mn)
            # decrease minchan and recompute numsigma (conserving the area)
            self.minchan -= 1
            self.numsigma = self.area / float(self.minchan)
        # put the first results on top
        results.reverse()

        # get the first results as they will be the widest
        segments = results.pop()
        # for each of the remaining runs merge the results
        for tempsegs in results:
            for seg in tempsegs:
                found = False
                for m in range(len(segments)):
                    # fully contained segment
                    if seg[0] >= segments[m][0] and seg[1] <= segments[m][1]:
                        found = True
                        break
                    # partial overlap of segments, then merge them
                    if (seg[0] > segments[m][0] and seg[0] < segments[m][1]
                        and (seg[1] > segments[m][1] or seg[1] < segments[m][0]))\
                       or (seg[1] > segments[m][0] and seg[1] < segments[m][1]
                        and (seg[0] > segments[m][1] or seg[0] < segments[m][0])):
                        seg = utils.merge(segments[m], seg)
                        segments[m] = copy.deepcopy(seg)
                        found = True
                        break
                if not found:
                    # just add it if there is no overlap
                    segments.append([min(seg[0], seg[1]), max(seg[0], seg[1])])
        # find the run with the lowest noise
        indx = noise.index(min(noise))
        # return the results
        return segments, cutoff[indx], noise[indx], mean[indx]
