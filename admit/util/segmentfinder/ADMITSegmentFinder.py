""" .. _admitsegment:

    ADMITSegmentFinder --- Finds segments of emission within a spectrum.
    --------------------------------------------------------------------

    This module defines the class for spectral line segment detection.
"""
# system imports
import math
import numpy as np
import numpy.ma as ma

# ADMIT imports
from admit.util import stats
from admit.util import utils
from admit.util import Segments
from admit.util.AdmitLogging import AdmitLogging as logging


class ADMITSegmentFinder(object):
    """Define segments of 'line' emission where segments from data appear to be
    above a threshold. This routine comes out of ASTUTE, some parameters below
    are hardcoded.

    Parameters
    ----------
    freq : float array
        Frequencies, GHz.

    spec : float array
        The y component of the spectrum (arbitrary units, could be linear,
        could be log).

    f : float
        Robustness parameter [1.5].

    pmin : float
        Signal above cuttoff,   rmean+pmin*rstd.

    minchan :  int
        Minimum number of channels needed for a line.

    maxgap : int
        Allowed channels with signal below cutoff [0].

    nomean : bool
        Remove the mean from any noise and cutoff calculations. This is useful
        if PVCorr based spectra are being processed to get a correct noise level.
        Default: False.

    Returns
    -------
    4-tuple
        channel_segments[], cutoff, noise, mean
    """
    ###
    ### @todo   symmetrize the attributes with the vals[]list ?   ->   spec and nsigma not set
    ###         
    def __init__(self, **keyval):
        self.peak     = None     ##
        self.f        = 1.5      ## standard robust
        self.hanning  = False    #  @todo not in vals[]
        self.bottom   = True     ##
        self.abs      = False    ##
        self.loglevel = 20       # @todo why it's own loglevel?  do we still need this
        self.pvc      = False    ##
        self.freq     = []       ##
        # self.spec   = []       ##
        self.maxgap   = 0        ## 0 the default ?
        self.minchan  = 3        ## 
        self.pmin     = 0.0      ## 0.0 the default ?
        self.nomean   = False    ## this is the csub parameter in e.g. LineID, another beautiful double negative here
        self.noise    = None     ##
        # self.nsigma            ## is this pmin?  shouldn't nsigma be gone from the vals[] list?

        self.vals = ["freq", "spec", "pmin", "peak", "f", "nsigma",\
                     "minchan", "maxgap", "abs", "pvc", "bottom", "nomean",\
                     "noise"]
        self.set_options(**keyval)

    def line_segments(self, spec, cutoff):
        """ Method to find segments that where lines are located
        [ [start1,end1], [start2,end2], ....]

        This function assumes you've subtracted a possible continuum (see the nomean
        parameter), and applied the absolute value, because this routine only
        segments above the cutoff.

        Need some explanation on the use of abs here. 

        Parameters
        ----------
        spec : numpy array (with a mask)
            The spectrum to analyze

        cutoff : float
            The cutoff to use (line segments must be higher than this value)

        Returns
        -------
        List of segment start and end channels, e.g.  [[10,20],[30,40]]

        """
        def index(w, start, value):
            """ Method to find the index of a specific value, starting at
                a specified index

                w : list
                    The list to search for the value

                start : int
                    Index to start searching at

                value :
                    The value to search for

                Returns
                -------
                Int containing the matching index, or -1 if not found.

            """
#@todo 
# how about something cleaner:
#  try:
#     return w[start:].index(value)+start
#  except ValueError:
#     return -1
            n = len(w)
            i = start
            while i < n:
                if w[i] == value:
                    return i
                i = i + 1
            return -1

        def setval(w, start, end, value):
            """ Method to set a range of indices to a specific value

                Parameters
                ----------
                w : list
                    The list to modify

                start : int
                    The index to start at

                end : int
                    The index to end at

                value : varies
                    The value to insert into to specified indicies

                Returns
                -------
                None

            """
            for i in range(start, end):
                w[i] = value

        #       -- start of line_segment --
        #print "PJT line_segment: ",spec.min(),spec.max(),cutoff,self.minchan,self.maxgap,self.abs
        s = []            # accumulate segments
        n = len(spec)
        w = range(n)      # @todo   use masking operations, so no loops are needed. this now should work though.
        if True:
            # here's the old one
            w1 = [-1] * n
            for i in range(n):
                if not self.abs and abs(spec[i]) < cutoff:
                    w1[i] = 0
                elif self.abs and spec[i] < cutoff:
                    w1[i] = 0
                else:
                    if spec.mask[i]:
                        w1[i] = 0
                    else:
                        w1[i] = 1
            #print "PJTW1:",w1
        if False:
            # here's the new one
            w2 = [-1] * n        
            if self.abs:
                for i in range(n):
                    if spec.mask[i]:
                        w2[i] = 0
                        continue
                    if abs(spec[i]) < cutoff:
                        w2[i] = 0
                    else:
                        w2[i] = 1
            else:
                for i in range(n):
                    if spec.mask[i]:
                        w2[i] = 0
                        continue
                    if spec[i] < cutoff:
                        w2[i] = 0
                    else:
                        w2[i] = 1
            sum0 = abs(np.array(w2)-np.array(w1)).sum()
            #print "PJTW2:",w2,sum0
        # pick your method (w1 = original, w2 = peter's )
        w = w1
        #
        i0 = 0
        while i0 >= 0:
            i1 = index(w, i0, 1)
            if i1 < 0:
                break
            t = index(w, i1 + 1, 1)
            if t - i1 > 1:
                i0 = i1 + 1
                continue
            i2 = index(w, i1, 0)
            if i2 < 0:
                break
            i3 = index(w, i2, 1)
            if i3 < 0:
                il = i2 - i1
                if il >= self.minchan:
                    s.append([i1, i2 - 1])
                break
            i4 = index(w, i3, 0)
            if i4 < 0:
                i4 = n - 1
            #
            ig = i3 - i2
            if (ig <= self.maxgap and i4 - i3 > self.minchan) or ig <= 1:
                # fill the gap, it's small
                setval(w, i2, i3, 1)
                i0 = i1
                continue
            else:
                il = i2 - i1
                if il >= self.minchan:
                    s.append([i1, i2 - 1])
                i0 = i2
                continue
        return s

    def set_options(self, **keyval):
        """ Set the options for the line finding algorithm.

            Parameters
            ----------
            freq : float array
                Frequencies, GHz.

            spec : float array
                The y component of the spectrum (arbitrary units, could
                be linear, could be log)

            f : float
                Robustness parameter [1.5]

            pmin : float
                Signal above cuttoff,   rmean+pmin*rstd

            minchan :  int
                Minimum number of channels needed for a line

            maxgap : int
                Allowed channels with signal below cutoff [0]

        """
        for v in self.vals:
            try:
                setattr(self, v, keyval[v])
            except KeyError:
                pass


    def find(self):
        """ Method that does the segment finding

            Parameters
            ----------
            None

            Returns
            -------
            Tuple containing a list of the segments, the cutoff used, the
            noise level, and a mean baseline.

        """
        if self.abs:
            self.spec = abs(self.spec)
        temp = np.zeros(len(self.spec))
        #self.see = ma.masked_array(temp, mask=self.spec.mask)
        # parameters (some now from the function argument)
        logging.debug("MIN/MAX " + str(self.spec.min()) + " / " +\
            str(self.spec.max()))
        n = len(self.spec)      # data and freq assumed to be same size
        if self.hanning:
            h = np.hanning(5) / 2         # normalize the convolution array
            h = np.array([0.25, 0.5, 0.25])
            data2 = np.convolve(self.spec, h, 'same')
        else:
            data2 = self.spec
        if len(data2) != len(self.freq):
            raise Exception("ulines: data2 and freq not same array")

        # do the work
        dr = stats.robust(data2, self.f)
        noise = dr.std()
        logging.debug("ROBUST: (mean/median/noise) " + \
            str(dr.mean()) + " / " + str(ma.median(dr)) + " / " + str(noise))
        #print "\n\nD2",data2,"\n"
        data3 = ma.masked_invalid(data2)
        #print "\n\nD3\n",data3,"\n"
        ddiff = data3[1:n] - data3[0:n-1]
        logging.debug("DIFF: (mean/stdev) " + str(ddiff.mean()) +\
            " / " + str(ddiff.std()))
        #print "\n\n",ddiff,"\n",self.f,"\n"
        ddr = stats.robust(ddiff, self.f)
        logging.debug("RDIFF: (mean/median/stdev) " + \
            str(ddr.mean()) + " / " + str(ma.median(ddr)) + " / " + \
            str(ddr.std()))
        #plt.show()
        if self.bottom:
            # first remind the classic
            dmean1 = dr.mean()
            dstd1 = dr.std()
            logging.debug("CLASSIC MEAN/SIGMA: " + str(dmean1) + \
                " / " + str(dstd1))
            # see if we can find a better one?
            # k should really depend on nchan, (like an nsigma), 2-3 should be ok for most.
            k = 2.5
            dmin = dr.min()
            dmax = dr.min() + 2 * k * ddr.std() / 1.414214
            logging.debug("DMIN/DMAX: " + str(dmin) + " / " + \
                str(dmax))
            dm = ma.masked_outside(dr, dmin, dmax)
            dmean = max(0.0, dm.mean()) # ensure that the mean is positive or 0.0
            dstd = dm.std()
            if self.noise is not None:
                cutoff = self.pmin * self.noise
            elif self.nomean:
                cutoff = self.pmin * dstd
            else:
                cutoff = dmean + self.pmin * dstd

            logging.debug("BETTER MEAN/SIGMA: " + str(dmean) + \
                " / " + str(dstd))
        else:
            # classic simple, but fails when robust didn't kill off (enough of) the signal
            # sigma will be too high, cutoff too high and you could have no lines if there
            # is one strong lines
            dmean = dr.mean()
            dstd = dr.std()
            if self.noise is not None:
                cutoff = self.pmin * self.noise
            elif self.nomean:
                cutoff = self.pmin * dstd
            else:
                cutoff = dmean + self.pmin * dstd
            logging.debug("CLASSIC MEAN/SIGMA: " + str(dmean) + \
                " / " + str(dstd))
        logging.debug("SEGMENTS: f=%g pmin=%g maxgap=%d minchan=%d" % \
                   (self.f, self.pmin, self.maxgap, self.minchan))
        #print "\nDATA\n\n",data2,"\n\n"
        segments = self.line_segments(data2, cutoff)
        #print "SEGMENTS",segments
        nlines = len(segments)
        logging.debug("Found %d segments above cutoff %f" % \
            (nlines, cutoff))
        segp = []
        rmax = data2.max() + 0.1 #  + 0.05*(data2.max()-data2.min())
        segp.append([self.freq[0], self.freq[n - 1], cutoff, cutoff])
        segp.append([self.freq[0], self.freq[n - 1], dmean, dmean])
        for (l, s) in zip(range(nlines), segments):
            ch0 = s[0]
            ch1 = s[1]
            sum0 = sum(data2[ch0:ch1+1])
            sum1 = sum(self.freq[ch0:ch1+1] * data2[ch0:ch1+1])
            sum2 = sum(self.freq[ch0:ch1+1] * self.freq[ch0:ch1+1] * data2[ch0:ch1+1])
            lmean = sum1 / sum0
            # this fails for weaker lines, so wrapped it in a abs
            lsigma = math.sqrt(abs(sum2 / sum0 - lmean * lmean))
            lmax = max(data2[ch0:ch1+1])
            if self.peak != None:
                lpeak = 1000*max(self.peak[ch0:ch1+1])
            else:
                lpeak = max(self.spec[ch0:ch1+1])
            # @todo if we ever allow minchan=1 lsigma would be 0.0.... should we adopt channel width?
            lfwhm = 2.355 * lsigma / lmean * utils.c
            logging.debug(
                "Line in %2d channels %4d - %4d @ %.4f GHz +/- %.4f GHz log(S/N) = %.2f FWHM %5.1f km/s  %.2f" % \
                (ch1 - ch0 + 1, ch0, ch1, lmean, lsigma, lmax, lfwhm, lpeak))
            segp.append([self.freq[ch0], self.freq[ch1], rmax, rmax])
            segp.append([lmean, lmean, rmax - 0.1, rmax + 0.05])
        return Segments.Segments(segments, nchan=len(self.spec)), cutoff, dstd, dmean
