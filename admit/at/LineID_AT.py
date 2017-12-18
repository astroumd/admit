""" .. _Line-at-api:

   **LineID_AT** --- Identifies molecular lines in spectra.
   --------------------------------------------------------

   This module defines the LineID_AT class.
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
import admit.util.filter.Filter1D as Filter1D
from admit.util import APlot
from admit.util.Image import Image
from admit.util.Tier1DB import Tier1DB
from admit.util.AdmitLogging import AdmitLogging as logging
from admit.util import SpectralLineSearch
from admit.util import LineData
from admit.util import Segments


# @todo  this code does not check upon exit that the LineID list is uniq, the U lines,
#        where we only used 3 digits (i.e. 1 MHz accuracy) it would too often find
#        duplicate frequencies to 3 digits. 4 would be better, but despite that these
#        cases have identical channel ranges, U freq still different.
#        Note there were 3 places where %.3f -> %.4f now
#        The real fix is a) not allow same interval (U) lines
#                        b) double check on exit linelist is unique
#        See code around duplicate_lines[] where method b) is applied in 1.0.4.

#(see :ref:`tier-one-lineid`).
class LineID_AT(AT):
    """ Task for detecting and identifying spectral lines from input spectra. All
        input spectra are assumed to be from the same data set.

        See also :ref:`LineID-AT-design` for design documentation.

        The produced LineList_BDP contains a list of all spectral lines,
        possible identifications, and channel ranges, found in the input spectra.
        Additionally a spectral plot with overlayed lines is produced for each input
        spectrum.

        The line identification algorithm first looks for segments of spectral
        line emission. Spectral peaks are then searched for within these regions.
        Once spectral peaks are located, patterns are searched for (specifically
        patterns of rotation, expansion, and collapse). Each peak is then matched
        to ADMIT's *Tier 1* list, which contains the more common molecules and transitions.
        If no match is found then the CASA
        task *slsearch* or the *splatalogue* database is used to generate a potential
        line list based on the peak's frequency and line width. This list is narrowed down
        to a single identification by comparing the transition energies,
        constituent atoms, and line strength.

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
        self.boxcar = True
        AT.__init__(self, keys, keyval)
        self._version = "1.0.5"
        self.set_bdp_in([(CubeSpectrum_BDP, 1, bt.OPTIONAL),
                         (CubeStats_BDP,    1, bt.OPTIONAL),
                         (PVCorr_BDP,       1, bt.OPTIONAL)])
        self.set_bdp_out([(LineList_BDP, 1)])

    def _taskargs(self):
        """ generate a task argument string for the summary taskbar """
        # @todo   duh, why is getkey called again???
        #         shouldn't we have this in self.
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

    def integritycheck(self):
        """ Method to make sure all data have the same frequency axis. This is necessary since
            this AT works in both channel and frequency space, thus it must be ensured that the
            frequency of channel 1 is the same for all input spectra. This method will throw an
            exception if a mismatch is found, as further analysis might be compromised. The
            comparison of the frequencies is done at the 1 part in 10^6 level in case they are
            recorded at differing precisions.

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        # get a list of all good (unmasked) channels in each input spectra
        chans = []
        freqs = []
        for sspec in self.statspec:
            chans.append(ma.nonzero(sspec.spec() > -1)[0])
            freqs.append(sspec.freq())
        for spec in self.specs:
            chans.append(ma.nonzero(spec.spec() > -1)[0])
            freqs.append(spec.freq())
        if self.pvspec is not None:
            chans.append(ma.nonzero(self.pvspec.spec() > -1)[0])
            freqs.append(self.pvspec.freq())
        # if there is only 1 input spectrum, the all is ok by default
        if len(chans) == 1:
            return
        # first check the nearest channel
        for chan in chans[0]:
            found = True
            for i in range(1, len(chans)):
                if not chan in chans[i]:
                    found = False
            if found:
                ref = freqs[0][chan]
                for i in range(1, len(chans)):
                    if not utils.issameinfreq(ref, freqs[i][chan]):
                        raise Exception("Frequency axis are not the same in nearest channel.")
            if found:
                break
        # now check the farthest channel
        for chan in reversed(chans[0]):
            found = True
            for i in range(1, len(chans)):
                if not chan in chans[i]:
                    found = False
            if found:
                ref = freqs[0][chan]
                for i in range(1, len(chans)):
                    if not utils.issameinfreq(ref, freqs[i][chan]):
                        raise Exception("Frequency axis are not the same in farthest channel.")
            if found:
                break

    def removepeaks(self, pks, segments):
        """ Method to remove peak points from a list if they are not inside of
            a segment and merge those that are close to each other

            Parameters
            ----------
            pks : list
                List of peak points, any units

            segments : list
                List of segment end points (two for each segment), must have
                same units as pks

            Returns
            -------
            List of peak points that are inside of the segments
        """
        peaks = []
        tol = self.getkey("minchan")
        for pk in pks:
            for seg in segments:
                # only keep peaks that are inside of a segment
                # also remove any peaks that are in the first or last channel
                # of the spectra, as they are likely false peaks
                if (seg[0] <= pk <= seg[1]) and pk >= 1 and pk < len(self.freq) - 1:
                    peaks.append(pk)
                    break
        npeaks = set()
        peaks.sort()
        if len(peaks) == 1:
            return peaks
        # now go through the remaining peaks and combine any that are within tol of each other
        for i in range(len(peaks)):
            for j in range(i + 1, len(peaks)):
                if j < len(peaks) - 1:
                    if abs(peaks[i] - peaks[j]) < tol \
                       and abs(peaks[j] - peaks[j + 1]) < tol:
                        npeaks.add(peaks[j])
                        break
                    else:
                        npeaks.add(peaks[i])
                        break
                else:
                    if abs(peaks[i] - peaks[j]) < tol:
                        npeaks.add(peaks[j])
                        break
                    else:
                        npeaks.add(peaks[i])
                        break
            if i == len(peaks) - 1:
                if abs(peaks[i] - peaks[i - 1]) > tol:
                    npeaks.add(peaks[i])
        return list(npeaks)

    def findpatterns(self, spec, points, segments):
        """ Method to search for patterns in the peaks. Specifically it is
            looking for pairs of peaks that are the same distance apart (within
            the tolerance). These can be an indicator of rotation/infall/etc.
            Only two patterns are allowed to overlap. See the design documentation
            for specifics

            Parameters
            ----------
            spec : array like
                The spectrum that is currently being worked on.

            points : numpy array
                Listing of peak points

            segments : list
                List of the segments for the current spectrum

            Returns
            -------
            A Peaks class containing the spectra, segments, peaks and patterns
        """
        # initialize the data class
        peaks = Peaks(spec=spec, segments=segments)
        delfrq = utils.veltofreq(650, spec.freq()[len(spec)/2])
        maxsep = delfrq / spec.delta()
        ts = np.zeros(len(spec)).astype(float)
        ts[0] = 1.

        # make a copy of the input points which will be modified as groups are located
        singles = copy.deepcopy(points)
        # create a 2D array to catalog the distances between every peak
        diffs = np.zeros((len(points), len(points)))
        # calculate the distance between every peak
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                diffs[i, j] = abs(points[i] - points[j])
        # look for pairs of peaks that are a common distance apart (within the
        # given tolerance)
        clusters = {}
        for i in range(len(points)):
            for j in range(i + 1, min(len(points), i + 2)):
                # get each distance one at a time and compare it to the rest
                diff = diffs[i, j]
                dlist = []
                # if this is the first time this distance has been found
                first = True
                for k in range(i + 1):
                    for l in range(k + 1, min(len(points), k + 2)):
                        # compare to all other points, skipping itself
                        if (k == i and l == j) or diffs[k, l] < self.tol / 3.0 \
                           or abs(spec.spec()[points[k]]) > 2.0 * abs(spec.spec()[points[l]])\
                           or abs(spec.spec()[points[l]]) > 2.0 * abs(spec.spec()[points[k]]):
                            continue
                        # if the distances from two pairs of points are close enough
                        # add it to the list of clusters
                        if maxsep > diffs[k, l] > 0.0 and (diff - self.tol / 3.0 < diffs[k, l] < diff + self.tol / 3.0):
                            # if this is the first time for this distance then add
                            # both to the list
                            if first:
                                dlist.append([i, j])
                            dlist.append([k, l])
                            # mark the current point as processed (i.e. set to 0.0)
                            diffs[k, l] = 0.0
                            first = False
                # if groups of points were detected then add them to the dictionary
                if len(dlist) > 0:
                    clusters[diff] = dlist
        # get the actual peak points rather then just indexes
        clens = {}
        for k, v in clusters.iteritems():
            tl = []
            for i in v:
                tl.append([points[i[0]], points[i[1]]])
            clusters[k] = tl
            clens[k] = len(tl)
        # sort the list to make it easier to process
        clist = sorted(clens, key=clens.get)
        clist.reverse()

        spoints = []
        for k in clist:
            for i in clusters[k]:
                if not i[0] in spoints:
                    spoints.append(i[0])
                if not i[1] in spoints:
                    spoints.append(i[1])
        # single spectral lines
        # spectral lines that appear to be in a pattern
        for p in spoints:
            l = set()
            for k in clist:
                v = clusters[k]
                # collect those that are very close together
                for i in v:
                    if (p - 0.1 < i[0] < p + 0.1) or (p - 0.1 < i[1] < p + 0.1):
                        l.add(k)
            # reduce each of these to a single instance
            if len(l) > 1:
                for i in clist:
                    if i in l:
                        l.remove(i)
                        break
                for i in l:
                    for j in range(len(clusters[i]) - 1, -1, -1):
                        if (p - 0.1 < clusters[i][j][0] < p + 0.1) or \
                           (p - 0.1 < clusters[i][j][1] < p + 0.1):
                            del clusters[i][j]
                    if len(clusters[i]) < 2:
                        del clusters[i]
                        clist.remove(i)
        # remove any that appear multiple times
        counts = {}
        multi = {}
        for k, v in clusters.iteritems():
            for i in v:
                if i[0] in counts:
                    multi[i[0]].append(i)
                else:
                    counts[i[0]] = 1
                    multi[i[0]] = [i]
                if i[1] in counts:
                    multi[i[1]].append(i)
                else:
                    counts[i[1]] = 1
                    multi[i[1]] = [i]
        for k, v in multi.iteritems():
            ratios = {}
            r = []
            if len(v) > 1:
                for i in v:
                    temp = max(peaks.getspecs()[i[0]], peaks.getspecs()[i[1]]) / \
                           min(peaks.getspecs()[i[0]], peaks.getspecs()[i[1]])
                    r.append(temp)
                    ratios[tuple(i)] = temp
                best = min(r, key=lambda x: abs(x - 1.0))
                for k1, v1 in ratios.iteritems():
                    if best != v1:
                        for k2 in clusters.keys():
                            try:
                                clusters[k2].remove(list(k1))
                            except ValueError:
                                pass
        # only allow the two closest patterns for any given point
        remove = []
        newcounts = {}
        counts = set()
        for k, v in clusters.iteritems():
            counts.add(len(v))
        if len(counts) > 0:
            counts = sorted(counts)
            counts.reverse()
            counts = counts[0:min(2, len(counts))]
        for k, v in clusters.iteritems():
            if not len(v) in counts:
                remove.append(k)
                continue
            else:
                newcounts[k] = len(v)
            for i in v:
                for j in i:
                    try:
                        singles.remove(j)
                    except ValueError:
                        pass

        for i in remove:
            del clusters[i]
        # report the results
        if len(clusters.keys()) > 0:
            if len(clusters.keys()) > 1:
                exp = "s"
                pre = ""
            else:
                exp = ""
                pre = " a"
            msg = "Found %s potential pattern%s with%s separation%s of" % (len(clusters), exp, pre, exp)
            summary = ""
            for k in clusters.keys():
                summary += " %.1f," % (2. * abs(utils.freqtovel(spec.freq()[len(spec)/2], spec.freq()[len(spec)/2] - spec.freq()[len(spec)/2 - k])))
            summary = summary[:-1] + " km/s"
            logging.info(msg + summary)

        peaks.singles = singles
        peaks.pairs = clusters
        peaks.counts = newcounts
        return peaks

    def narrowpossibles(self, possible):
        """ Method to take the possible identifications of a spectral line and
            narrow it down to one possibility. This is done by comparing the
            upper state energies of the transitions, masses, and isotope counts.
            NEED DETAILS

            Parameters
            ----------
            possibles : list
                A list containing all of the possible identifications for the
                line

            Returns
            -------
            The listing of the most likely identification
        """
        # now sort through the contents, find the one with the lowest upper state
        # energy
        # if we have too many non-standard isotopes then we should reconsider
        # for C the standard isotope is 12 and the non-standard ones are 13 and 14
        for j in range(len(possible) - 1, -1, -1):
            # one non-standard iostope is ok for higher mass molecules
            if possible[j].getkey("isocount") > 0 and possible[j].getkey("mass") > 50.0 and len(possible) > 1:
                del possible[j]
            # two non-standard isotopes is ok for middle weight molecules
            elif possible[j].getkey("isocount") > 1 and possible[j].getkey("mass") > 31.0 and len(possible) > 1:
                del possible[j]
            # three or more non-standard isotopes is only ok for the smallest molecules
            elif possible[j].getkey("isocount") > 2 and possible[j].getkey("mass") > 14.0 and len(possible) > 1:
                del possible[j]
        # defaults for searches
        peakmass = 0
        lowmass = 100000000
        lmindx = -1
        lowen = 100000.0
        leindx = -1
        # find out which one(s) have the lowest energy, and highest and lowest mass
        for j in range(len(possible)):
            if possible[j].getupperenergy() < lowen:
                lowen = possible[j].getupperenergy()
                leindx = j
            if possible[j].getkey("mass") > peakmass:
                peakmass = possible[j].getkey("mass")
            if possible[j].getkey("mass") < lowmass:
                lowmass = possible[j].getkey("mass")
                lmindx = j

        # if mass is too big compared to others, then we likely have another candidate
        if (possible[leindx].getkey("mass") > 1.6 * possible[lmindx].getkey("mass"))\
           and (possible[lmindx].getkey("linestrength") > 1.0):
            # ignore ions
            if "+" in possible[lmindx].getkey("formula"):
                pass
            else:
                lowen = possible[lmindx].getupperenergy()
                leindx = lmindx

        # otherwise we just go with lowest energy one
        lname = possible[leindx].getkey("formula")
        qnum = possible[leindx].getkey("transition")
        # loop through all possibilities and eliminate those with much different
        # energy and name (this collects transitions with hyperfine components)
        for k in range(len(possible) - 1, -1, -1):
            if k == leindx:
                continue
            if (not(utils.iscloseinE(lowen, possible[k].getupperenergy()) and possible[k].getkey("formula") == lname)) \
                or (lowen == possible[k].getupperenergy() and possible[k].getkey("formula") == lname and possible[k].getkey("transition") == qnum):
                del possible[k]
        peakls = 0.0
        lsindx = 0
        # of the remaining ones (all from the same molecule), pick the one with
        # the highest line strength
        for j in range(len(possible)):
            if possible[j].getkey("linestrength") > peakls:
                peakls = possible[j].getkey("linestrength")
                lsindx = j
        if len(possible) > 1:
            possible.insert(0, possible[lsindx])
            del possible[lsindx + 1]
            for p in possible:
                p.setkey("blend", self.blendcount)

            self.blendcount += 1
        else:
            possible[0].setkey("blend", 0)

        return possible

    def checkreject(self, lines):
        """ Method to check possible lines against the list of rejected lines. Returns
            an edited version of the input data, removing those that match the reject list.

            Parameters
            ----------
            lines : list or dict
                The line identifications to check for rejects.

            Returns
            -------
            Data in the same form as input, with rejected lines removed

        """
        if isinstance(lines, list):
            results = []
            for res in lines:
                found = False
                for rej in self.reject:
                    if res.name.upper() == rej[0].upper():
                        if rej[1] is None:
                            found = True
                            break
                        if utils.issameinfreq(res.getkey("frequency"), rej[1]):
                            found = True
                            break
                if not found:
                    results.append(res)
        elif isinstance(lines, dict):
            results = {}
            for freq, res in lines.iteritems():
                if isinstance(res, list):
                    tempr = []
                    for r in res:
                        found = False
                        for rej in self.reject:
                            if r.name.upper() == rej[0].upper():
                                if rej[1] is None:
                                    found = True
                                    break
                                if utils.issameinfreq(r.getkey("frequency"), rej[1]):
                                    found = True
                                    break
                        if not found:
                            tempr.append(r)
                    results[freq] = tempr
                else:
                    found = False
                    for rej in self.reject:
                        if res.name.upper() == rej[0].upper():
                            if rej[1] is None:
                                found = True
                                break
                            if utils.issameinfreq(res.getkey("frequency"), rej[1]):
                                found = True
                                break
                    if not found:
                        results[freq] = res
        else:
            raise Exception("Impproper format for input lines, it must be a list or dictionary not a %s." % (type(lines)))
        return results


    def generatepossibles(self, frq):
        """ Method to generate a list of possible molecular identifications
            given a frequency range. The methold calls slsearch and converts
            the output into a list.

            Parameters
            ----------
            frq : list, length 2
                The frequency range to search, it is just passed to slsearch,
                and no error checking is done.

            Returns
            -------
            A list containing the possible identifications. Each item in the
            list is a list itself containing the chemical formula, chemical
            name, rest frequency, transition quantum numbers, line strength,
            lower state energy, and upper state energy, in this order.
        """
        frq = self.checkforcefreqs(frq)
        if frq is None:
            return []
        sls = SpectralLineSearch(self.getkey("online"), self.tier1freq)
        kw = {"exclude" : ["atmospheric", "potential", "probable"],
              "include_only_nrao" : True,
              "line_strengths": ["ls1", "ls2"],
              "energy_levels" : ["el2", "el4"],
              "fel" : True
             }
        results = sls.search(min(frq), max(frq), self.getkey("recomblevel").upper(),
                             self.getkey("allowexotics"), **kw)

        results = self.checkreject(results)
        for r in results:
            print "PJT",r
        return results

    def gettier1(self):
        """ Method to get the Tier 1 transitions that may be in the window.
            These transitions are stored in a small sqlite3 database inside of
            Admit. The molecules in the database are:

            CO      all transitions

            13CO    all transitions

            C18O    all transitions

            C17O    all transitions

            HCO+    all transitions

            H13CO+  all transitions

            DCO+    all transitions

            HDO     all transitions

            CCH     all transitions

            CN      excluding weakest lines

            13CN    excluding weakest lines

            HCN     all transitions

            DCN     all transitions

            H13CN   all transitions

            HN13C   all transitions

            HNC     all transitions

            N2H+    all transitions

            H2CO    excluding weakest lines

            CS      all transitions

            SiO     all transitions

            SO      all transitions

            HC3N    excluding weakest lines


            Parameters
            ----------
            None

            Returns
            -------
            tuple of dictionaries
                The first contains a list of single transitions and the
                strongest component of any lines with hyperfine splitting, the
                second contains a listing of all possible hyperfine components,
                lined with the main components in the first list.
        """
        lines = {}
        hfs = {}
        # connect to the database via the handler class
        # and get all possibilities based on the frequency end points of the window
        t1db = Tier1DB()
        t1db.searchtransitions(freq=[ma.min(self.freq), ma.max(self.freq)])
        results = t1db.getall()
        count = 0
        # go through the main results
        for line in results:
            lines[count] = line
            # if the line has additional hyperfine components then get them from the
            # database and add them to the list
            if line.getkey("hfnum") > 0:
                hfs[count] = []
                t1db.searchhfs(line.getkey("hfnum"))
                hfsresults = t1db.getall()
                for hfr in hfsresults:
                    hline = copy.deepcopy(line)
                    hline.setkey("frequency", hfr.getkey("frequency"))
                    hline.setkey("uid", utils.getplain(line.getkey("formula")) + "_%.5f" % hfr.getkey("frequency"))
                    hline.setkey("linestrength", hfr.getkey("linestrength"))
                    hline.setkey("transition", str(hfr.getkey("transition")))
                    hfs[count].append(hline)
            count += 1
        # close the handle
        t1db.close()
        # return the main components and the associated hyperfine lines

        lines = self.checkreject(lines)
        hfs = self.checkreject(hfs)
        return lines, hfs

    def getpeaks(self, method, args, spec, segments, iterate=False):
        """ Method to get the peaks from the input spectrum. It calls the requested
            peak finder and can iterate over the inputs to find both wider weaker lines as
            well as stronger narrower ones. The iteration is done by conserving the product of
            numsigma * minchan. The first run keeps both values as they were input, subsequent
            runs decrease the minchan by 1 and increase numsigma so that the product is conserved.
            This is repeated as long as minchan > 1. The results of the iterations are merged together
            and a single list of peaks is returned.

            Parameters
            ----------
            method : str
                The peak finding method to use

            args : dict
                The arguments to send to the peak finder

            spec : array like
                The input spectrum which is searched for peaks

            segments : list
                A list of the previously detected segments

            iterate : bool
                If True then iterate over the minchan ans threshold to detect narrow strong lines.
                Default : False

            Returns
            -------
            List of the peak points in channel space

        """
        wdth = []
        pks = []
        area = float(args["min_width"]) * args["thresh"]
        initwidth = args["min_width"]
        initthresh = args["thresh"]
        for i in range(1, 6):
            wdth.append(2*i + 1)
        for s in segments:
            temppks = []
            args["min_width"] = initwidth
            args["thresh"] = initthresh
            last = 0
            curpk = spec[s[0]:s[1]+1].max()
            # only run the boxcar smoothing if the segment is wide enough, this avoids suppressing
            # narrow lines
            if self.boxcar and abs(s[0] - s[1]) > 6:
                for i in range(len(wdth)):
                    fltr = Filter1D.Filter1D(spec, "boxcar", **{"width": wdth[i]})
                    spec3 = fltr.run()
                    spec3 *= math.sqrt(float(wdth[i]))
                    newpk = spec3[s[0]:s[1]+1].max()
                    if newpk > curpk and wdth[i] <= 0.5*(s[1]-s[0]):
                        curpk = newpk
                        last = i
                    else:
                        break
                fltr = Filter1D.Filter1D(spec, "boxcar", **{"width": wdth[last]})
                spec3 = fltr.run()
                args["spec"] = spec3[max(s[0] - 2, 0): min(s[1] + 3, len(spec3) - 1)]
            else:
                args["spec"] = spec[max(s[0] - 2, 0): min(s[1] + 3, len(spec) - 1)]
            while (args["min_width"] > 1 and iterate) or (args["min_width"] > 0 and not iterate):
                pf = utils.getClass("util.peakfinder", method, args)
                pk = pf.find() + float(max(s[0] - 2, 0))
                for p in pk:
                    if s[0] <= p <= s[1]:
                        temppks.append(p)
                if not iterate:
                    break
                args["min_width"] -= 1
                args["thresh"] = area / args["min_width"]
            drop = set()
            for i in range(len(temppks)):
                for j in range(i + 1, len(temppks)):
                    if j not in drop and abs(temppks[i] - temppks[j]) < initwidth:
                        drop.add(j)
            for i in range(len(temppks)):
                if i not in drop:
                    pks.append(temppks[i])
            pks.sort()
        return pks

    def counthfclines(self, chfc, shfc, peak, wiggle, offset, hflines):
        """ Method to count the number of hyperfine lines that match a given offset.
            The offsets are determined by the wings of a cluster. This returns
            the number of hyperfine components that match emission features.

            Parameters
            ----------
            chfc : dict
                Dictionary containing the channel ranges and other line attributes
                of clusters

            shfc : dict
                Dictionary containing the channel ranges and other line attributes
                of single lines

            peak : Peaks instance
                Peaks instance used to calculate channel ranges

            wiggle : float
                The amount of wiggle room to allow for a match in channel space

            offset : float
                The offset to use for the calculations

            hflines : list
                List of all possible hyperfine components

            Returns
            -------
            Int, the number of matches
        """
        count = 0
        for hfl in hflines:
            # get the expected channel range for the hyperfine component for the
            # given wiggle room and offset
            rng = [peak.getchan(hfl.getkey("frequency") - wiggle - offset), peak.getchan(hfl.getkey("frequency") + wiggle - offset)]
            low = min(rng)
            hi = max(rng)
            found = False
            # now look for matches in clusters
            for chan in chfc.values():
                if low <= chan[0][0] <= hi or low <= chan[0][1] <= hi or \
                    chan[0][0] <= low <= chan[0][1]:
                    count += 1
                    found = True
                    break
            # if the current hyperfine component is already located then stop searching
            if found:
                continue
            # now search the single lines
            for chan in shfc.values():
                if low <= chan[0][0] <= hi or low <= chan[0][1] <= hi or \
                    chan[0][0] <= low <= chan[0][1]:
                    count += 1
                    break
            # return the results
        return count

    def taghfclines(self, chfc, shfc, peak, wiggle, offset, hflines):
        """ Method to identify hyperfine components in a given spectrum. If components
            are blended then the strongest line (based on transition line strength)
            is added to the transitions and all others are added to the blended lines.
            All are connected by the blend number.

            Parameters
            ----------
            chfc : dict
                Dictionary containing the channel ranges and other line attributes
                of clusters

            shfc : dict
                Dictionary containing the channel ranges and other line attributes
                of single lines

            peak : Peaks instance
                Peaks instance used to calculate channel ranges

            wiggle : float
                The amount of wiggle room to allow for a match in channel space

            offset : float
                The offset to use for the calculations

            hflines : list
                List of all possible hyperfine components

            Returns
            -------
            Tuple containing the identification(s) and blend(s)
        """
        identifications = {}
        blends = []
        possibleblends = {}
        # combine the input dictionaries
        combhfc = {}
        combhfc.update(chfc)
        combhfc.update(shfc)

        for hfl in hflines:
            # get the channel ranges for the given offset and wiggle room
            rng = [peak.getchan(hfl.getkey("frequency") - wiggle + offset), peak.getchan(hfl.getkey("frequency") + wiggle + offset)]
            low = min(rng)
            hi = max(rng)
            # look to see if any match, if one does add it to the dictionary
            for freq, chan in combhfc.iteritems():
                if low < chan[0][0] <= hi or low <= chan[0][1] <= hi or \
                    chan[0][0] <= low <= chan[0][1]:
                    hfline = copy.deepcopy(hfl)
                    hfline.setfreqs([peak.getfreq(chan[0][0]), peak.getfreq(chan[0][1])])
                    if freq in possibleblends:
                        possibleblends[freq].append(hfline)
                    else:
                        possibleblends[freq] = [hfline]
                    break
        # need to find where main line belongs
        fc = set()
        fs = set()
        for freq, ident in possibleblends.iteritems():
            # if there is only 1 line then just add it to the identifications
            if len(ident) == 1:
                hfline = copy.deepcopy(ident[0])
                hfline.setkey({"velocity" : float(utils.freqtovel(freq, freq - hfline.getkey("frequency")) + self.vlsr),
                               "chans" : [self.chan[self.chan.index(combhfc[freq][0][0])],
                                          self.chan[self.chan.index(combhfc[freq][0][1])]],
                               "freqs" : [self.freq[self.chan.index(combhfc[freq][0][0])],
                                          self.freq[self.chan.index(combhfc[freq][0][1])]],
                               "peakintensity" : float(combhfc[freq][1]),
                               "fwhm" : float(combhfc[freq][2]),
                               "peakrms" : float(combhfc[freq][3]),
                               "peakoffset" : float(utils.freqtovel(freq, freq - hfline.getkey("frequency"))),
                               "blend" : 0})
                identifications[freq] = hfline
            # if there are several then find the strongest and add the rest to the blends
            else:
                maxstr = 0.0
                mindx = -1
                # find the strongest
                for i in range(len(ident)):
                    if ident[i].getkey("linestrength") > maxstr:
                        maxstr = ident[i].getkey("linestrength")
                        mindx = i
                if mindx == -1:
                    mindx = 0
                hfl = copy.deepcopy(ident[mindx])
                poffset = utils.freqtovel(freq, freq - hfl.getkey("frequency"))
                # add the strongest to the identifications, connect it to the other(s) via
                # the blendcount parameter
                hfl.setkey({"velocity" : float(poffset + self.vlsr),
                            "chans" : [self.chan[self.chan.index(combhfc[freq][0][0])],
                                       self.chan[self.chan.index(combhfc[freq][0][1])]],
                            "freqs" : [self.freq[self.chan.index(combhfc[freq][0][0])],
                                       self.freq[self.chan.index(combhfc[freq][0][1])]],
                            "peakintensity" : float(combhfc[freq][1]),
                            "fwhm" : float(combhfc[freq][2]),
                            "peakrms" : float(combhfc[freq][3]),
                            "peakoffset" : float(offset),
                            "blend" : self.blendcount})
                identifications[freq] = hfl
                del ident[mindx]
                # add the others to the blends
                for hfl in ident:
                    hfline = copy.deepcopy(hfl)
                    hfline.setkey({"velocity" : float(utils.freqtovel(freq, freq - hfline.getkey("frequency")) + self.vlsr),
                                   "chans" : [self.chan[self.chan.index(combhfc[freq][0][0])],
                                              self.chan[self.chan.index(combhfc[freq][0][1])]],
                                   "freqs" : [self.freq[self.chan.index(combhfc[freq][0][0])],
                                              self.freq[self.chan.index(combhfc[freq][0][1])]],
                                   "peakintensity" : 0.0,
                                   "fwhm" : 0.0,
                                   "peakrms" : 0.0,
                                   "peakoffset" : float(offset),
                                   "blend" : self.blendcount})
                    blends.append(hfline)
                self.blendcount += 1
            # remove any identified lines from the peaks instance
            for f, v in peak.fcenters.iteritems():
                for idn in ident:
                    if idn.getfstart() <= f <= idn.getfend():
                        fc.add(f)
                    if idn.getfstart() <= v[1][0] <= idn.getfend():
                        v[1][0] = 0.0
                    if idn.getfstart() <= v[1][1] <= idn.getfend():
                        v[1][1] = 0.0
            for f, v in peak.fcenters.iteritems():
                if v[1][0] == 0.0:
                    if v[1][1] != 0.0:
                        peak.fsingles.append(v[1][1])
                    fc.add(f)
                elif v[1][1] == 0.0:
                    peak.fsingles.append(v[1][0])
                    fc.add(f)

            for i in range(len(peak.fsingles)):
                for idn in ident:
                    if idn.getfstart() <= peak.fsingles[i] <= idn.getfend():
                        fs.add(i)
        # remove any already identified clusters and peaks
        for f in fc:
            del peak.fcenters[f]
        for f in fs:
            peak.fsingles[f] = 0.0

        return identifications, blends

    def gettier1line(self, chans):
        """ Method to return a line from the detected tier1 list. The line is found
            by looking for an entry which is between the end points of the input segment.

            Parameters
            ----------
            chans : list
                Two element list of the start and end channels to search over

            Returns
            -------
            A listing of any tier1 line which overlaps with the segment.

        """
        for t1 in self.tier1list:
            if t1.getstart() <= chans[0] <= t1.getend() and t1.getstart() <= chans[1] <= t1.getend():
                return copy.deepcopy(t1)

    def checkforcefreqs(self, frq):
        """ Method to check that detected segments do not overlap with any force segments in
            frequency space

            Parameters
            ----------
            segs : list
                List of the segments (in channel space) to check

            Returns
            -------
            List of segments that do not overlap with force segments

        """
        reverse = self.freq[0] > self.freq[-1]
        for fr in self.forcefreqs:
            if fr[0] <= frq[0] <= fr[1] and fr[0] <= frq[1] <= fr[1]:
                return None
            if fr[0] <= frq[0] <= fr[1]:
                if reverse:
                    frq[0] = min(fr[1] - 0.0001, self.freq[0])
                else:
                    frq[0] = min(fr[1] - 0.0001, self.freq[-1])
            if fr[0] <= frq[1] <= fr[1]:
                if reverse:
                    frq[1] = max(self.freq[-1], fr[0] + 0.0001)
                else:
                    frq[1] = max(self.freq[0], fr[0] + 0.0001)
        return frq

    def checkforcesegs(self, segs):
        """ Method to check that detected segments do not overlap with any force segments in
            channel space

            Parameters
            ----------
            segs : list
                List of the segments (in channel space) to check

            Returns
            -------
            List of Segments objects that do not overlap with force segments

        """
        finalsegs = Segments(nchan=len(self.freq))
        for seg in segs:
            found = False
            for ch in self.forcechans:
                if ch[0] <= seg[0] <= ch[1] and ch[0] < seg[1] < ch[1]:
                    found = True
                    break
                if ch[0] <= seg[0] <= ch[1]:
                    seg[0] = min(ch[1] + 1, self.chan[-1])
                if ch[0] <= seg[1] <= ch[1]:
                    seg[1] = max(0, ch[0] - 1)
            if not found:
                finalsegs.append(seg)
        return finalsegs

    def checkforcechans(self, peaks, chs):
        """ Method to check that no non-force segments overlap with force segments

            Parameters
            ----------
            peaks : Peaks instance
                Instance of the Peaks class containing all of the line peaks

            chs : list
                List containing a pair of entries for the beginning and ending
                channel numbers for the segment.

            Returns
            -------
            List, containing a pair of entries, the start and end channels for the
            segment, modified so that it does not overlap any tier1 segments.

        """
        chans = copy.deepcopy(chs)
        for ch in self.forcechans:
            if ch[0] <= chans[0] <= ch[1] and ch[0] <= chans[1] <= ch[1]:
                return None
            if ch[0] <= chans[0] <= ch[1]:
                chans[0] = min(ch[1] + 1, len(peaks) - 1)
            if ch[0] <= chans[1] <= ch[1]:
                chans[1] = max(0, ch[0] - 1)
        return chans

    def checktier1chans(self, peaks, chs):
        """ Method to check that no non-tier1 segments overlap with tier1 segments
            in the same spectrum.

            Parameters
            ----------
            peaks : Peaks instance
                Instance of the Peaks class containing all of the line peaks

            chs : list
                List containing a pair of entries for the beginning and ending
                channel numbers for the segment.

            Returns
            -------
            List, containing a pair of entries, the start and end channels for the
            segment, modified so that it does not overlap any tier1 segments.

        """
        chans = copy.deepcopy(chs)
        for ch in self.tier1chans:
            if ch[0] <= chans[0] <= ch[1] and ch[0] <= chans[1] <= ch[1]:
                return None
            if ch[0] <= chans[0] <= ch[1]:
                chans[0] = min(ch[1] + 1, len(peaks) - 1)
            if ch[0] <= chans[1] <= ch[1]:
                chans[1] = max(0, ch[0] - 1)
        return chans

    def checkfit(self, peaks, peak, params, freq, segment):
        """ Method to determine if the given Gaussian fit paramters exceed 1.5 times the intensity
            of the peak channel, and are contained within the encompassing segment. Adjustments are
            are made if necessary.

            Parameters
            ----------
            peaks : Peaks instance
                The Peaks instance used to supply the spectrum and segments

            peak : float
                The peak intensity within the segment

            params : array like
                The list of Gaussian parameters from a fit (peak, center (offset from freq), FWHM)

            freq : float
                The central frequency of the fit.

            segment : list
                Segment containing the peak

            Returns
            -------
            Tuple containing the corrected fit parameters

        """
        if abs(params[0]) > 1.5 * abs(peak):
            params[0] = peak
        if not ((peaks.getfreq(segment[0]) < freq + params[1] < peaks.getfreq(segment[1])) or\
           (peaks.getfreq(segment[0]) > freq + params[1] > peaks.getfreq(segment[1]))):
            params[1] = 0.0
        if abs(peaks.getfreq(segment[0]) - peaks.getfreq(segment[1])) < params[2]:
            params[2] = abs(peaks.getfreq(segment[0]) - peaks.getfreq(segment[1]))
        return params

    def identify(self, peaks, noise, tier1, hfs, isstats=False, ispvcorr=False):
        """ Method to identify lines, given their peak locations. This is a
            complex method that works as follows:

            - search for any Tier 1 lines in the spectrum

              + start with any detected patterns
              + then search for individual lines
              + any peak detected within 'tier1width' of the expected rest
                frequency of the Tier 1 line will be marked as being from that
                transition (defaults to 300 km/s for a source vlsr > 150 and 40 km/s
                for a source vlsr <= 150 km/s)
              + if an identified line has hyperfine components, search for them
                before proceeding to the next transition in the Tier 1 list

            - search for any remaining transitions in the spectrum

              + start with any detected patterns
              + then search any remaining single peaks

            - when working with detected (really suspected) patterns both the
              emission/absorption peaks and the central frequency are searched
              for, since the pattern may not be due to rotation, but may be
              due to emission from multiple related transitions (internal molecular
              rotation)
            - any detected lines in a given spectrum will be compared to detected peaks
              of any other spectra. Specifically this helps to identify transitions
              due to source rotation where the CubeStats spectrum see all of the emission
              (both red and blue shifted peaks), but a CubeSpectrum may ony see the red peak,
              this red only peak will be correctly identified because it matches part of the
              pattern from the CubeStats input.


            Parameters
            ----------
            peaks : Peaks instance
                A class containing both the sinlge peaks and those which may be
                grouped by a common offset

            noise : float
                The rms noise of the root spectrum

            tier1 : dict
                Dictionary containing any Tier 1 lines located in the band, rest
                frequency is the key, transition data are the values

            hfs : dict
                Dictionary of hyperfine components that correspond to any lines
                in tier1.

            isstats : bool
                Whether or not a CubeStats based spectrum is being processed.
                Default : False

            ispvcorr : bool
                Whether or not a PVCorr based spectrum is being processed.
                Specifically this disables the use of velocity offsets.
                Default: False

            Returns
            -------
            List of the line identifications
        """
        identifications = {}              # list for all identified lines
        blends = []
        foundcomplex = []
        slen = len(peaks.fsingles)
        fwidth = -1.0
        # do the Tier 1 search first
        if len(tier1) > 0:
            if len(hfs) > 0:
                # first generate channel ranges for all lines and clusters
                chfc = {}
                shfc = {}
                for freq, v in peaks.fcenters.iteritems():
                    parameters = {0: [0, 0, 0, [100000, -1000000]],
                                  1: [0, 0, 0, []],
                                  2: [0, 0, 0, []]}

                    width = abs(v[1][0] - v[1][1]) / 2.0
                    chan = self.getchannels(peaks, noise, cid=peaks.getchan(freq))
                    if chan is None:
                        continue
                    peak = peaks.getspecs()[peaks.getchan(freq)]
                    pkrms = peak / noise
                    if chan[0] is None or chan[1] is None or abs(chan[0] - chan[1]) < 4:
                        popt = [peak, 0.0, abs(peaks.getfreq(chan[0]) - peaks.getfreq(chan[1]))]
                    else:
                        if chan[0]==chan[1]:
                            fwidth = abs(peaks.getfreqs()[chan[0]]-peaks.getfreqs()[chan[0]+1])
                        # get a better number for the FWHM
                        popt, pcov = utils.fitgauss1D(peaks.getfreqs()[chan[0]:chan[1] + 1] - freq,
                                                      peaks.getspecs()[chan[0]:chan[1] + 1],
                                                      par=[peak, 0.0, width],width=fwidth)
                        popt = self.checkfit(peaks, peak, popt, freq, peaks.getsegment(peaks.getchan(freq)))
                    parameters[0] = [peak, popt[1], abs(popt[2]),
                                     peaks.getsegment(peaks.getchan(freq))]
                    if v[0]:
                        mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                  abs(parameters[2][1]))

                        pkrms = mpk
                        if not isstats:
                            pkrms = mpk / noise
                        tfwhm = utils.freqtovel(freq, abs(parameters[0][2]) * 2.355)
                        chfc[freq] = (parameters[0][3], peak, tfwhm, pkrms)
                    for i in [0, 1]:
                        peakw = peaks.getspecs()[peaks.getchan(v[1][i])]
                        seg = peaks.getsegment(peaks.getchan(v[1][i]))
                        if seg is None:
                            parameters[i + 1] = [0, 0, 0, [0, 0]]
                        else:
                            if seg[0] is None or seg[1] is None or abs(seg[0] - seg[1]) < 4:
                                popt = [peakw, 0.0, abs(peaks.getfreq(seg[0]) - peaks.getfreq(seg[1]))]
                            else:
                                [st, en] = seg
                                if st==en:
                                    fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                                
                                popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - v[1][i],
                                                              peaks.getspecs()[st:en + 1],
                                                              par=[peakw, 0.0, width], width=fwidth)
                                popt = self.checkfit(peaks, peakw, popt, v[1][i], peaks.getsegment(peaks.getchan(v[1][i])))
                            parameters[i + 1] = [peakw, popt[1], abs(popt[2]),
                                                 peaks.getsegment(peaks.getchan(v[1][i]))]
                            tfwhm = utils.freqtovel(freq, abs(parameters[i + 1][2]) * 2.355)
                            pkrms = parameters[i + 1][0]
                            if not isstats:
                                pkrms /= noise

                            chfc[parameters[i + 1][1] + v[1][i]] = (parameters[i + 1][3], parameters[i + 1][0], tfwhm, pkrms)
                for freq in peaks.fsingles:
                    chans = self.getchannels(peaks, noise, sid=peaks.getchan(freq))
                    if chans is None:
                        continue
                    st = int(max(0, peaks.getchan(freq) - 10))
                    en = int(min(len(peaks), peaks.getchan(freq) + 10))
                    width = abs(peaks.getfreq(st) - peaks.getfreq(en))
                    peak = peaks.getspecs()[peaks.getchan(freq)]
                    if st==en:
                        fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                        print "PJT1",fwidth

                    popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - freq,
                                                  peaks.getspecs()[st:en + 1], par=[peak, 0.0,
                                                                                    width], width=fwidth)
                    fcenter = freq + popt[1]
                    fwhm = utils.freqtovel(freq, abs(popt[2]))
                    pkrms = peak
                    if not isstats:
                        pkrms = peak / noise
                    shfc[freq] = (peaks.getsegment(peaks.getchan(freq)), peak, fwhm, pkrms)
            # determine what width to use for uncertainty
            if abs(self.vlsr) > 150.0:
                width = 300.0
            else:
                width = 40.0
            if self.getkey("tier1width") != 0.0:
                width = self.getkey("tier1width")
            fwidth = utils.veltofreq(width, peaks.centerfreq())
            # go through each possible transition and see if we have a line that is a possibility
            for trans, t1 in tier1.iteritems():
                todel = set()
                found = False
                # go through all detected clusters
                skip = []
                noskip = {}
                doskip = False
                for k in peaks.fcenters.keys():
                    if t1.getkey("frequency") - fwidth < k < t1.getkey("frequency") + fwidth:
                        doskip = True
                        noskip[abs(k - t1.getkey("frequency"))] = k
                    else:
                        skip.append(k)
                if len(noskip) > 1:
                    minval = noskip[min(noskip.keys())]
                    for i in noskip.values():
                        if i != minval:
                            skip.append(i)
                # search though the clusters first
                for k in peaks.fcenters.keys():
                    if k not in peaks.fcenters or (doskip and k in skip):
                        continue
                    v = peaks.fcenters[k]
                    # center peak
                    centerpeak = v[0]
                    wings = v[1]
                    cent = {"lines": {},
                            "blend": []}
                    left = {"lines": {},
                            "blend": []}
                    right = {"lines": {},
                             "blend": []}
                    ccount = 0
                    lcount = 0
                    rcount = 0

                    # parameters hold the values of line fits and start and end channels
                    # peak intensity, frequency offset, width in GHz, start chan, end chan
                    parameters = {0: [0, 0, 0, [100000, 0]],
                                  1: [0, 0, 0, []],
                                  2: [0, 0, 0, []]}
                    delta = abs(peaks.getfreqs()[peaks.getchan(k)] -
                                peaks.getfreqs()[peaks.getchan(k) - 1])
                    # frequencies of offset lines
                    # rought width
                    twidth = abs(wings[0] - wings[1]) / 2.0
                    width = twidth

                    if centerpeak:
                        # calculate starting and ending channels to extract for the line fitting
                        # cut will will trace the entire line, down to the cutoff level,
                        # keeping in mind the window edges
                        seg = peaks.getsegment(peaks.getchan(k))
                        if seg is None:
                            parameters[0] = [0, 0, 0, [0, 0]]
                            width = 0
                        else:
                            [st, en] = seg
                            peak = peaks.getspecs()[peaks.getchan(k)]
                            hpk = peak / 2.0
                            if st==en:
                                fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                                
                            # get a better number for the FWHM
                            popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - k,
                                                          peaks.getspecs()[st:en + 1],
                                                          par=[peak, 0.0, width], width=fwidth)

                            width = abs(popt[2])
                            parameters[0] = [peak, popt[1], abs(popt[2]),
                                             peaks.getsegment(peaks.getchan(k))]
                    for i in [0, 1]:
                        peakw = peaks.getspecs()[peaks.getchan(wings[i])]
                        seg = peaks.getsegment(peaks.getchan(wings[i]))
                        if seg is None:
                            parameters[i + 1] = [0, 0, 0, [0, 0]]
                        else:
                            [st, en] = seg
                            if st==en:
                                fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                            
                            popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - wings[i],
                                                          peaks.getspecs()[st:en + 1],
                                                          par=[peakw, 0.0, twidth], width = fwidth)
                            parameters[i + 1] = [peakw, popt[1], abs(popt[2]),
                                                 peaks.getsegment(peaks.getchan(wings[i]))]

                    # check the center frequency first
                    closest = -1.
                    distance = 100000.
                    for frq in peaks.fcenters.keys():
                        if t1.getkey("frequency") - fwidth <= frq <= t1.getkey("frequency") + fwidth:
                            if abs(t1.getkey("frequency") - frq) < distance:
                                closest = frq
                                distance = abs(t1.getkey("frequency") - frq)
                    if closest > 0.0:
                        k = closest
                        found = True
                        # if the line has hyperfine components then there is a lot of work to do
                        if trans in hfs:
                            # how much jitter do we allow  ##### should be a parameter of the AT
                            wiggle = 0.01 * fwidth
                            offset = k - t1.getkey("frequency")
                            hflines = sorted(hfs[trans], key=lambda x: x.getkey("frequency"))
                            hflines.reverse()
                            # figure out all the possible main offsets
                            ldiff = wings[0] - t1.getkey("frequency")
                            rdiff = wings[1] - t1.getkey("frequency")
                            poffset = utils.freqtovel(k, k - t1.getkey("frequency"))
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise
                            st = min(parameters[0][3][0], parameters[1][3][0], parameters[2][3][0])
                            en = max(parameters[0][3][1], parameters[1][3][1], parameters[2][3][1])
                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))

                            ccount += 1

                            # see what we get if we assume wing 0 is the main line
                            if t1.getkey("frequency") - fwidth < wings[0] < t1.getkey("frequency") + fwidth:
                                lcount += 1 + self.counthfclines(chfc, shfc, peaks, wiggle, ldiff,
                                                                 hflines)

                            # see what we get if wing 1 is the main line
                            if t1.getkey("frequency") - fwidth < wings[1] < t1.getkey("frequency") + fwidth:
                                rcount += 1 + self.counthfclines(chfc, shfc, peaks, wiggle, rdiff,
                                                                 hflines)

                            # see what we get if the center is the main line
                            # if there is no central peak
                            if not centerpeak:
                                # see who had the best matches
                                if max(lcount, rcount, 1) == 1:
                                    tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                      offset, hflines + [t1])
                                elif lcount == rcount:
                                    if abs(ldiff) < abs(rdiff):
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          ldiff, hflines + [t1])
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          rdiff, hflines + [t1])
                                elif lcount > rcount:
                                    tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                      ldiff, hflines + [t1])
                                else:
                                    tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                      rdiff, hflines + [t1])
                                cent["lines"].update(tempid)
                                if len(tempid) == 0:
                                    continue
                                cent["blend"] += tblend
                            # if there is a center peak
                            else:
                                ccount += self.counthfclines(chfc, shfc, peaks, wiggle, offset,
                                                             hflines)
                                m = max(ccount, lcount, rcount)    # highest number of matches
                                offset = abs(offset)
                                # minimum offset value
                                mo = min(abs(offset), abs(ldiff), abs(rdiff))
                                # if all have only 1 possible, then go with the center
                                if ccount == rcount == lcount == 1:
                                    tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                      offset, hflines + [t1])
                                # if all have the same number of possibles, then go with the one that is closest to
                                # the expected rest frequency
                                elif ccount == rcount == lcount:
                                    if mo == offset:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          offset, hflines + [t1])
                                    elif mo == rdiff:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          rdiff, hflines + [t1])
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          ldiff, hflines + [t1])
                                # if the center has the most possibilities
                                elif m == ccount:
                                    # if it has the same as wing 1 then decide by offset
                                    if ccount == rcount:
                                        if offset < rdiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, offset,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                    # if it has the same as wing 0 then decide by offset
                                    elif ccount == lcount:
                                        if offset < ldiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, offset,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                    # otherwise just go with the center
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          offset, hflines + [t1])
                                # if wing 1 has the most possibles
                                elif m == rcount:
                                    # if it has the same as the center then decide by offset
                                    if ccount == rcount:
                                        if offset < rdiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, offset,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                    # if it has the same as wing 0 then decide by offset
                                    elif rcount == lcount:
                                        if rdiff < ldiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                    # otherwise just go with wing 1
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          rdiff, hflines + [t1])
                                # if wing 0 has the most possibles
                                elif m == lcount:
                                    if lcount == rcount:
                                        if ldiff < rdiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                    elif ccount == lcount:
                                        if offset < ldiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, offset,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          ldiff, hflines + [t1])
                                else:
                                    raise Exception("This should never happen")
                                cent["lines"].update(tempid)
                                if len(tempid) == 0:
                                    continue
                                cent["blend"] += tblend

                        # the easy case of no hyperfine components
                        else:
                            poffset = utils.freqtovel(k, k - t1.getkey("frequency"))
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise
                            st = min(parameters[0][3][0], parameters[1][3][0], parameters[2][3][0])
                            en = max(parameters[0][3][1], parameters[1][3][1], parameters[2][3][1])
                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))
                            line = copy.deepcopy(t1)
                            line.setkey({"velocity" : float(poffset + self.vlsr),
                                         "peakintensity": float(mpk),
                                         "peakoffset" : float(poffset),
                                         "fwhm" : float(tfwhm),
                                         "chans" : [self.chan[self.chan.index(st)],
                                                    self.chan[self.chan.index(en)]],
                                         "freqs" : [self.freq[self.chan.index(st)],
                                                    self.freq[self.chan.index(en)]],
                                         "peakrms" : float(pkrms),
                                         "blend" : 0})
                            identifications[k] = line
                            self.tier1list.append(line)
                            self.tier1chans.append([st, en])
                            frq = [peaks.getfreq(st), peaks.getfreq(en)]
                            self.tier1freq.append([min(frq), max(frq)])
                            todel.add(k)
                    # wing 0
                    closest = -1.0
                    distance = 100000.
                    for frq, val in peaks.fcenters.iteritems():
                        wng = val[1]
                        if t1.getkey("frequency") - fwidth <= wng[0] <= t1.getkey("frequency") + fwidth:
                            if abs(t1.getkey("frequency") - wng[0]) < distance:
                                closest = frq
                                distance = abs(t1.getkey("frequency") - wng[0])
                    if closest > 0.0:
                        k = closest
                        wings = peaks.fcenters[closest][1]
                        found = True
                        # if the line has hyperfine components then there is a lot of work to do
                        if trans in hfs:
                            # how much jitter do we allow  ##### should be a parameter of the AT
                            rlen = 0
                            llen = 0
                            wiggle = 0.01 * fwidth
                            poffset = wings[0] - t1.getkey("frequency")
                            ldiff = wings[0] - t1.getkey("frequency")
                            rdiff = wings[1] - t1.getkey("frequency")
                            hflines = sorted(hfs[trans], key=lambda x: x.getkey("frequency"))
                            hflines.reverse()
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise
                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))

                            # figure out all the possible main offsets
                            rdiff = wings[1] - t1.getkey("frequency")
                            st = parameters[1][3][0]
                            en = parameters[1][3][1]
                            llen += 1 + self.counthfclines(chfc, shfc, peaks, wiggle, ldiff, hflines)
                            # see what we get if wing 1 is the main line
                            tempid = {}
                            if t1.getkey("frequency") - fwidth < wings[1] < t1.getkey("frequency") + fwidth:
                                rlen += 1 + self.counthfclines(chfc, shfc, peaks, wiggle, rdiff,
                                                               hflines)
                            # see what we get if the center is the main line
                            # if there is no central peak
                                m = max(lcount, rcount)    # highest number of matches
                                offset = abs(offset)
                                ldiff = abs(ldiff)
                                # minimum offset value
                                mo = min(abs(ldiff), abs(rdiff))
                                # if all have only 1 possible, then go with the center
                                if rlen == llen == 1:
                                    tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                      rdiff, hflines + [t1])

                                # if all have the same number of possibles, then go with the one that is closest to
                                # the expected rest frequency
                                elif rlen == llen:
                                    if mo == offset:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          rdiff, hflines + [t1])
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          ldiff, hflines + [t1])
                                elif m == rlen:
                                    # if it has the same as the center then decide by offset
                                    if rlen == llen:
                                        if rdiff < ldiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                    # otherwise just go with wing 1
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          rdiff, hflines + [t1])
                                # if wing 0 has the most possibles
                                elif m == llen:
                                    if llen == rlen:
                                        if ldiff < rdiff:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, ldiff,
                                                                              hflines + [t1])
                                        else:
                                            tempid, tblend = self.taghfclines(chfc, shfc, peaks,
                                                                              wiggle, rdiff,
                                                                              hflines + [t1])
                                    else:
                                        tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle,
                                                                          ldiff, hflines + [t1])
                                else:
                                    raise Exception("This should never happen")
                            left["lines"].update(tempid)

                            if len(tempid) == 0:
                                continue
                            left["blend"] += tblend
                        # the easy case of no hyperfine components
                        else:
                            poffset = utils.freqtovel(wings[0], wings[0] - t1.getkey("frequency"))
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise
                            rdiff = wings[1] - t1.getkey("frequency")

                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))
                            line = copy.deepcopy(t1)
                            line.setkey({"velocity" : float(poffset + self.vlsr),
                                         "peakintensity" : float(mpk),
                                         "peakoffset" : float(poffset),
                                         "fwhm" : float(tfwhm),
                                         "chans" : [self.chan[self.chan.index(parameters[1][3][0])],
                                                    self.chan[self.chan.index(parameters[1][3][1])]],
                                         "freqs" : [self.freq[self.chan.index(parameters[1][3][0])],
                                                    self.freq[self.chan.index(parameters[1][3][1])]],
                                         "peakrms" : float(pkrms),
                                         "blend" : 0
                                        })
                            identifications[k] = line
                            self.tier1list.append(line)
                            self.tier1chans.append([parameters[1][3][0], parameters[1][3][1]])
                            frq = [peaks.getfreq(parameters[1][3][0]),
                                   peaks.getfreq(parameters[1][3][1])]
                            self.tier1freq.append([min(frq), max(frq)])

                            todel.add(k)

                    closest = -1.0
                    distance = 100000.
                    for frq, val in peaks.fcenters.iteritems():
                        wng = val[1]
                        if t1.getkey("frequency") - fwidth <= wng[1] <= t1.getkey("frequency") + fwidth:
                            if abs(t1.getkey("frequency") - wng[1]) < distance:
                                closest = frq
                                distance = abs(t1.getkey("frequency") - wng[1])
                    if closest > 0.0:
                        wings = peaks.fcenters[closest][1]

                        found = True
                        # if the line has hyperfine components then there is a lot of work to do
                        if trans in hfs:
                            poffset = wings[1] - t1.getkey("frequency")
                            wings = v[1]
                            # how much jitter do we allow  ##### should be a parameter of the AT
                            wiggle = 0.1 * fwidth
                            offset = wings[1] - t1.getkey("frequency")
                            hflines = sorted(hfs[trans], key=lambda x: x.getkey("frequency"))
                            hflines.reverse()
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise
                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))
                            rdiff = wings[1] - t1.getkey("frequency")
                            tempid, tblend = self.taghfclines(chfc, shfc, peaks, wiggle, rdiff,
                                                              hflines + [t1])
                            right["lines"].update(tempid)
                            if len(tempid) == 0:
                                continue
                            right["blend"] += tblend
                        else:
                            poffset = utils.freqtovel(wings[1], wings[1] - t1.getkey("frequency"))
                            mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                                      abs(parameters[2][1]))
                            pkrms = mpk
                            if not isstats:
                                pkrms = mpk / noise

                            poffset = utils.freqtovel(k, k - t1.getkey("frequency"))
                            tfwhm = utils.freqtovel(k, abs((wings[1] + parameters[2][2]) -
                                                           (wings[0] - parameters[1][2])))
                            line = copy.deepcopy(t1)
                            line.setkey({"velocity" : float(poffset + self.vlsr),
                                         "peakintensity" : float(mpk),
                                         "peakoffset" : float(poffset),
                                         "fwhm" : float(tfwhm),
                                         "chans" : [self.chan[self.chan.index(parameters[2][3][0])],
                                                    self.chan[self.chan.index(parameters[2][3][1])]],
                                         "freqs" : [self.freq[self.chan.index(parameters[2][3][0])],
                                                    self.freq[self.chan.index(parameters[2][3][1])]],
                                         "peakrms" : float(pkrms),
                                         "blend" : 0
                                        })
                            identifications[k] = line
                            self.tier1list.append(line)
                            self.tier1chans.append([parameters[2][3][0], parameters[2][3][1]])
                            frq = [peaks.getfreq(parameters[2][3][0]), peaks.getfreq(parameters[2][3][1])]
                            self.tier1freq.append([min(frq), max(frq)])

                            todel.add(k)
                    if trans in hfs:
                        if len(cent["lines"]) >= len(right["lines"]) and len(cent["lines"]) >= len(left["lines"]):
                            if len(cent["lines"]) != 0:
                                identifications.update(cent["lines"])
                                for val in cent["lines"].values():
                                    self.tier1list.append(val)
                                self.tier1chans.append(cent["lines"].values()[0].getkey("chans"))
                                frq = [peaks.getfreq(cent["lines"].values()[0].getstart()),
                                       peaks.getfreq(cent["lines"].values()[0].getend())]
                                self.tier1freq.append([min(frq), max(frq)])
                                blends += cent["blend"]
                        elif len(left["lines"]) >= len(right["lines"]):
                            identifications.update(left["lines"])
                            for val in left["lines"].values():
                                self.tier1list.append(val)
                            self.tier1chans.append(left["lines"].values()[0].getkey("chans"))
                            frq = [peaks.getfreq(left["lines"].values()[0].getstart()),
                                   peaks.getfreq(left["lines"].values()[0].getend())]
                            self.tier1freq.append([min(frq), max(frq)])
                            blends += left["blend"]
                        else:
                            identifications.update(right["lines"])
                            for val in right["lines"].values():
                                self.tier1list.append(val)
                            self.tier1chans.append(right["lines"].values()[0].getkey("chans"))
                            frq = [peaks.getfreq(right["lines"].values()[0].getstart()),
                                   peaks.getfreq(right["lines"].values()[0].getend())]
                            self.tier1freq.append([min(frq), max(frq)])
                            blends += right["blend"]

                    chanrange = {}
                    freqs = identifications.keys()
                    chans = []
                    for f in freqs:
                        chans.append(peaks.getchan(f))
                    temppeak = Peaks(spec=peaks.spec, fsingles=freqs, singles=chans, segments=peaks.segments)
                    for ident in freqs:
                        temp = self.getchannels(temppeak, noise, sid=peaks.getchan(ident), asfreq=True)
                        if temp is not None:
                            chanrange[ident] = temp
                    for f in freqs:
                        if chanrange[f] is None:
                            continue
                        ch = [peaks.getchan(chanrange[f][0]), peaks.getchan(chanrange[f][1])]
                        identifications[f].setstart(self.chan[self.chan.index(min(identifications[f].getstart(), min(ch)))])
                        identifications[f].setend(self.chan[self.chan.index(max(identifications[f].getend(), max(ch)))])
                        identifications[f].setkey("freqs", [self.freq[self.chan.index(identifications[f].getstart())],
                                                            self.freq[self.chan.index(identifications[f].getend())]])
                    delcent = []
                    for f in peaks.fcenters.keys():
                        for ch, vals in chanrange.iteritems():
                            if vals[0] <= f <= vals[1]:
                                delcent.append(f)
                                break
                    delsingle = []
                    for i in range(len(peaks.fsingles)):
                        if peaks.fsingles[i] in freqs:
                            continue
                        if peaks.fsingles[i] == 0:
                            delsingle.append(i)
                        for ch, vals in chanrange.iteritems():
                            if vals[0] <= peaks.fsingles[i] <= vals[1]:
                                delsingle.append(i)
                    delsingle.reverse()
                    for i in delcent:
                        try:
                            del peaks.fcenters[i]
                        except KeyError:
                            pass
                    for i in delsingle:
                        del peaks.fsingles[i]

                # if no hits then check the wings
                # now do the single peaks
                while len(peaks.fsingles) > 0 and max(peaks.fsingles) > 0.0:
                    closest = -1
                    distance = 1000000.
                    for i in range(len(peaks.fsingles)):
                        seg = peaks.getfsegment(peaks.fsingles[i])
                        if peaks.fsingles[i] == 0.0:# or haveit:
                            continue
                        if t1.getkey("frequency") - fwidth < seg[0] < t1.getkey("frequency") + fwidth or\
                           t1.getkey("frequency") - fwidth < seg[1] < t1.getkey("frequency") + fwidth or\
                           seg[0] < t1.getkey("frequency") < seg[1]:
                            if abs(t1.getkey("frequency") - peaks.fsingles[i]) < distance:
                                distance = abs(t1.getkey("frequency") - peaks.fsingles[i])
                                closest = i
                    if closest >= 0:
                        # get the start and end channels
                        seg = peaks.getsegment(peaks.getchan(peaks.fsingles[closest]))
                        fseg = peaks.getfsegment(peaks.fsingles[closest])

                        if seg is None:
                            continue
                        # cannot just go with first peak, must find closest peak
                        [st, en] = seg

                        if t1.getkey("frequency") - fwidth < fseg[0] < t1.getkey("frequency") + fwidth or\
                           t1.getkey("frequency") - fwidth < fseg[1] < t1.getkey("frequency") + fwidth or\
                           fseg[0] < t1.getkey("frequency") < fseg[1]:
                            found = True
                            if trans in hfs:
                                # allow some uncertainty in the widths
                                wiggle = 0.1 * fwidth
                                hflines = sorted(hfs[trans], key=lambda x: x.getkey("frequency"))
                                hflines.reverse()
                                offset = peaks.fsingles[closest] - t1.getkey("frequency")
                                tempid, tblend = self.taghfclines(chfc, shfc, peaks, 0.0, offset,
                                                                  hflines + [t1])
                                identifications.update(tempid)
                                for val in tempid.values():
                                    self.tier1list.append(val)

                                if len(tempid) == 0:
                                    continue
                                self.tier1chans.append(tempid.values()[0].getkey("chans"))
                                frq = [peaks.getfreq(tempid.values()[0].getstart()),
                                       peaks.getfreq(tempid.values()[0].getend())]
                                self.tier1freq.append([min(frq), max(frq)])
                                peaks.fsingles[closest] = 0.0
                                blends += tblend
                            else:
                                poffset = utils.freqtovel(peaks.fsingles[closest],
                                                          peaks.fsingles[closest] - t1.getkey("frequency"))
                                peak = peaks.getspecs()[peaks.getchan(peaks.fsingles[closest])]
                                maxwidth = width = utils.veltofreq(10.0, peaks.fsingles[closest])
                                breakpoint = 0
                                if i > 0:
                                    delta = abs(peaks.getfreqs()[peaks.singles[closest]]
                                                - peaks.getfreqs()[peaks.singles[closest] - 1])
                                else:
                                    delta = abs(peaks.getfreqs()[peaks.singles[closest]]
                                                - peaks.getfreqs()[peaks.singles[closest] + 1])
                                if st==en:
                                    fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                                    
                                popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - peaks.fsingles[closest],
                                                              peaks.getspecs()[st:en + 1],
                                                              par=[peak, 0.0, width], width=fwidth)
                                if abs(popt[2]) > 0.0:
                                    width = abs(popt[2]) * 1.17741
                                fcenter = peaks.fsingles[closest] + popt[1]
                                fwhm = utils.freqtovel(peaks.fsingles[closest], abs(popt[2])) * 1.17741
                                pkrms = peak
                                if not isstats:
                                    pkrms /= noise
                                delta = utils.freqtovel(peaks.fsingles[closest], delta)
                                line = copy.deepcopy(t1)
                                line.setkey({"velocity" : float(poffset + self.vlsr),
                                             "peakintensity" : float(peak),
                                             "peakoffset" : float(poffset),
                                             "fwhm" : float(fwhm),
                                             "chans" : [self.chan[self.chan.index(st)],
                                                        self.chan[self.chan.index(en)]],
                                             "freqs" : [self.freq[self.chan.index(st)],
                                                        self.freq[self.chan.index(en)]],
                                             "peakrms" : float(pkrms),
                                             "blend" : 0
                                            })
                                identifications[peaks.fsingles[closest]] = line
                                self.tier1list.append(line)
                                self.tier1chans.append([st, en])
                                frq = [peaks.getfreq(st), peaks.getfreq(en)]
                                self.tier1freq.append([min(frq), max(frq)])
                                peaks.fsingles[closest] = 0.0
                        chanrange = {}
                        freqs = identifications.keys()
                        chans = []
                        for f in freqs:
                            chans.append(peaks.getchan(f))
                        temppeak = Peaks(spec=peaks.spec, fsingles=freqs, singles=chans, segments=peaks.segments)
                        for ident in freqs:
                            temp = self.getchannels(temppeak, noise, sid=peaks.getchan(ident), asfreq=True)
                            if temp is not None:
                                chanrange[ident] = temp
                        for f in freqs:
                            if chanrange[f] is None:
                                continue
                            ch = [peaks.getchan(chanrange[f][0]), peaks.getchan(chanrange[f][1])]
                            identifications[f].setstart(self.chan[self.chan.index(min(identifications[f].getstart(), min(ch)))])
                            identifications[f].setend(self.chan[self.chan.index(max(identifications[f].getend(), max(ch)))])
                            identifications[f].setkey("freqs", [self.freq[self.chan.index(identifications[f].getstart())],
                                                                self.freq[self.chan.index(identifications[f].getend())]])
                    else:
                        break
                delcent = []
                freqs = identifications.keys()
                chanrange = {}
                for f in peaks.fcenters.keys():
                    if f in freqs:
                        continue
                    for ch, vals in chanrange.iteritems():
                        if vals[0] <= f <= vals[1]:
                            delcent.append(f)
                            break
                delsingle = []
                for i in range(len(peaks.fsingles)):
                    if peaks.fsingles[i] in freqs:
                        continue
                    if peaks.fsingles[i] == 0:
                        delsingle.append(i)
                    for ch, vals in chanrange.iteritems():
                        if vals[0] <= peaks.fsingles[i] <= vals[1]:
                            delsingle.append(i)
                delsingle.reverse()
                for i in delcent:
                    try:
                        del peaks.fcenters[i]
                    except KeyError:
                        pass
                for i in delsingle:
                    del peaks.fsingles[i]

        slen = len(peaks.fsingles)
        # now process anything that is not Tier 1
        # start with the complex sets
        for freq, v in peaks.fcenters.iteritems():
            # central frequency and channel spacing
            parameters = {0: [0, 0, 0, [10000, 0]],
                          1: [0, 0, 0, []],
                          2: [0, 0, 0, []]}
            centerpeak = v[0]
            delta = abs(peaks.getfreqs()[peaks.getchan(freq)] - peaks.getfreqs()[peaks.getchan(freq) - 1])
            # frequencies of offset lines
            wings = v[1]
            # rought width
            twidth = abs(wings[0] - wings[1]) / 2.0
            width = twidth
            # if there is a central peak in the cluster
            peak = 0.0
            if centerpeak:
                # calculate starting and ending channels to extract for the line fitting
                # cut will will be center +- 3*FWHM, keeping in mind the window edges
                st = max(0, peaks.getchan(freq) - 1.5 * int(twidth / (delta)))
                en = min(len(peaks) - 1, peaks.getchan(freq) + 1.5 * int(twidth / (delta)))
                if st==en:
                    fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                
                peak = peaks.getspecs()[peaks.getchan(freq)]
                hpk = peak / 2.0
                # get a better number for the FWHM
                popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - freq,
                                              peaks.getspecs()[st:en + 1],
                                              par=[peak, 0.0, width], width=fwidth)
                width = abs(popt[2])
                chans = self.getchannels(peaks, noise, cid=peaks.getchan(freq))
                if chans is None:
                    continue
                parameters[0] = [peak, popt[1], abs(popt[2]), chans]

            for i in [0, 1]:
                peakw = peaks.getspecs()[peaks.getchan(wings[i])]
                st = max(0, peaks.getchan(wings[i]) - 1.5 * int(twidth / (delta)))
                en = min(len(peaks) - 1, peaks.getchan(wings[i]) + 1.5 * \
                  int(twidth / (delta)))
                if st==en:
                    fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])

                # get a better number for the FWHM
                popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - wings[i],
                                              peaks.getspecs()[st:en + 1],
                                              par=[peakw, 0.0, twidth],width=fwidth)
                chans = self.getchannels(peaks, noise, cid=peaks.getchan(wings[i]))
                if chans is None:
                    continue
                parameters[i + 1] = [peakw, popt[1], abs(popt[2]), chans]
            clow = min(parameters[0][3][0], parameters[1][3][0], parameters[2][3][0])
            chigh = max(parameters[0][3][1], parameters[1][3][1], parameters[2][3][1])
            possibilities = []
            wpossibles = {}
            # search around the central frequency
            width *= 1.05
            possibilities += self.generatepossibles([freq - width, freq + width])
            # if there is a central peak then search around all possible offsets
            # in case this is not a true cluster but just random coincidence
            if centerpeak:
                for off in peaks.offsets:
                    possibilities += self.generatepossibles([freq - width - off,
                                                             freq + width - off])
                    possibilities += self.generatepossibles([freq - width + off,
                                                             freq + width + off])
            # take care of the wings
            wpeak = []
            wfwhm = []
            wwidth = []
            for i in [0, 1]:
                wpossibles[i] = []
                # calculate starting and ending channels to extract for the line fitting
                # cut will will be center +- 3*FWHM, keeping in mind the window edges
                st = max(0, peaks.getchan(wings[i]) - 3 * int(twidth / (delta)))
                en = min(len(peaks) - 1, peaks.getchan(wings[i]) + 3 * int(twidth / (delta)))
                if en - st < 11:
                    df = (11 - (en - st)) / 2
                    st -= df
                    en += df
                    if st < 0:
                        en += abs(st)
                        st = 0
                    if en > len(peaks) - 1:
                        df = en - len(peaks)
                        st = max(0, st - df)
                        en = len(peaks) - 1
                wpeak.append(peaks.getspecs()[peaks.getchan(wings[i])])
                # get a better value for the FWHM
                if st==en:
                    fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                
                popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - freq,
                                              peaks.getspecs()[st:en + 1], par=[peak, 0.0, width],width=fwidth)

                wwidth.append(width)
                wfwhm.append(utils.freqtovel(wings[i], abs(popt[2])))
                # search around the central frequency of the line
                wpossibles[i] += self.generatepossibles([wings[i] - wwidth[i],
                                                         wings[i] + wwidth[i]])
                # search as if this line is offset in case this is a single line and not a cluster
                if not ispvcorr:
                    for off in peaks.offsets:
                        wpossibles[i] += self.generatepossibles([wings[i] - wwidth[i] - off,
                                                                 wings[i] + wwidth[i] - off])
                        wpossibles[i] += self.generatepossibles([wings[i] - wwidth[i] + off,
                                                                 wings[i] + wwidth[i] + off])

            # if we have no results from all searches then we have U lines
            if len(possibilities) == len(wpossibles[0]) == len(wpossibles[1]) == 0:
                name = "Unknown"
                qn = ""
                linestr = 0.0
                eu = 0.0
                el = 0.0
                vel = 0.0
                if centerpeak:
                    species = "U_%.4f" % (freq)
                    frq = float(freq)
                    winner = LineData(formula=species, name=name, frequency=frq, uid=species,
                                      energies=[el, eu], linestrength=linestr, transition=qn,
                                      plain=species)
                    pkrms = parameters[0][0]
                    if not isstats:
                        pkrms /= noise
                    chans = self.checktier1chans(peak, [parameters[0][3][0], parameters[0][3][1]])
                    if chans is None:
                        identifications[freq] = self.gettier1line([parameters[0][3][0],
                                                                   parameters[0][3][1]])
                        identifications[freq].setkey("chans", [self.chan[self.chan.index(parameters[0][3][0])],
                                                               self.chan[self.chan.index(parameters[0][3][1])]])
                        identifications[freq].setkey("freqs", [self.freq[self.chan.index(parameters[0][3][0])],
                                                               self.freq[self.chan.index(parameters[0][3][1])]])

                    else:
                        winner.setkey({"velocity" : float(vel),
                                       "peakintensity" : float(parameters[0][0]),
                                       "fwhm" :  float(utils.freqtovel(freq, parameters[0][2])),
                                       "chans" : [self.chan[self.chan.index(chans[0])],
                                                  self.chan[self.chan.index(chans[1])]],
                                       "freqs" : [self.freq[self.chan.index(chans[0])],
                                                  self.freq[self.chan.index(chans[1])]],
                                       "peakrms" : float(pkrms),
                                       "blend" : 0
                                      })
                        identifications[freq] = winner
                for i in [0, 1]:
                    species = "U_%.4f" % (wings[i])
                    frq = float(wings[i])
                    wpeak = peaks.getspecs()[peaks.getchan(wings[i])]
                    winner = LineData(formula=species, name=name, frequency=frq, uid=species,
                                      energies=[el, eu], linestrength=linestr, transition=qn,
                                      plain=species)
                    pkrms = parameters[i + 1][0]
                    if not isstats:
                        pkrms /= noise
                    chans = self.checktier1chans(peaks, [parameters[i + 1][3][0], parameters[i + 1][3][1]])
                    if chans is None:
                        identifications[freq] = self.gettier1line([parameters[i + 1][3][0],
                                                                   parameters[i + 1][3][1]])
                        identifications[freq].setkey("chans", [self.chan[self.chan.index(parameters[i + 1][3][0])],
                                                               self.chan[self.chan.index(parameters[i + 1][3][1])]])
                        identifications[freq].setkey("freqs", [self.freq[self.chan.index(parameters[i + 1][3][0])],
                                                               self.freq[self.chan.index(parameters[i + 1][3][1])]])
                    else:
                        winner.setkey({"velocity" : float(vel),
                                       "peakintensity" : float(parameters[i + 1][0]),
                                       "fwhm" :  float(utils.freqtovel(wings[i], parameters[i + 1][2])),
                                       "chans" : [self.chan[self.chan.index(chans[0])],
                                                  self.chan[self.chan.index(chans[1])]],
                                       "freqs" : [self.freq[self.chan.index(chans[0])],
                                                  self.freq[self.chan.index(chans[1])]],
                                       "peakrms" : float(pkrms),
                                       "blend" : 0})
                        identifications[wings[i]] = winner
            # otherwise narrow it down for each one
            else:
                wblends = []
                w1blends = []
                w2blends = []
                if len(possibilities) > 0:
                    # eliminate doubles before proceeding
                    drop = set()
                    for i, poss in enumerate(possibilities):
                        for j in range(i + 1, len(possibilities)):
                            if poss.frequency == possibilities[j].frequency and \
                               poss.transition == possibilities[j].transition and \
                               poss.formula == possibilities[j].formula:
                                drop.add(j)
                    drop = list(drop)
                    drop.sort()
                    drop.reverse()
                    for d in drop:
                        del possibilities[d]
                    temp = self.narrowpossibles(possibilities)
                    winner = temp.pop(0)
                    for b in temp:
                        wblends.append(b)
                else:
                    winner = LineData()
                if len(wpossibles[0]) > 0:
                    drop = set()
                    for i, poss in enumerate(wpossibles[0]):
                        for j in range(i + 1, len(wpossibles[0])):
                            if poss.frequency == wpossibles[0][j].frequency and \
                               poss.transition == wpossibles[0][j].transition and \
                               poss.formula == wpossibles[0][j].formula:
                                drop.add(j)
                    drop = list(drop)
                    drop.sort()
                    drop.reverse()
                    for d in drop:
                        del wpossibles[0][d]

                    temp = self.narrowpossibles(wpossibles[0])
                    w1winner = temp.pop(0)
                    for b in temp:
                        w1blends.append(b)
                else:
                    w1winner = LineData()
                if len(wpossibles[1]) > 0:
                    drop = set()
                    for i, poss in enumerate(wpossibles[1]):
                        for j in range(i + 1, len(wpossibles[1])):
                            if poss.frequency == wpossibles[1][j].frequency and \
                               poss.transition == wpossibles[1][j].transition and \
                               poss.formula == wpossibles[1][j].formula:
                                drop.add(j)
                    drop = list(drop)
                    drop.sort()
                    drop.reverse()
                    for d in drop:
                        del wpossibles[1][d]
                    temp = self.narrowpossibles(wpossibles[1])
                    w2winner = temp.pop(0)
                    for b in temp:
                        w2blends.append(b)
                else:
                    w2winner = LineData()

                if winner.getkey("formula") == "":
                    winner = w2winner  # work around
                if winner.getkey("formula") == w1winner.getkey("formula") == "":
                    winner = w2winner
                if winner.getkey("formula") == w2winner.getkey("formula") == "":
                    winner = w1winner
                # compare species and QN, if they all match then delcare them all as one line
                if (winner.getkey("formula") == w1winner.getkey("formula") == w2winner.getkey("formula") and
                        winner.getkey("transition") == w1winner.getkey("transition") == w2winner.getkey("transition") and \
                   winner.getkey("formula") != "") or \
                   (winner.getkey("formula") == w1winner.getkey("formula") and
                    winner.getkey("transition") == w1winner.getkey("transition")) or\
                   (winner.getkey("formula") == w2winner.getkey("formula") and
                    winner.getkey("transition") == w2winner.getkey("transition")) or\
                   (w1winner.getkey("formula") == w2winner.getkey("formula") and
                    w1winner.getkey("transition") == w2winner.getkey("transition") and
                    w1winner.getkey("formula") != ""):
                    poffset = utils.freqtovel(freq, freq - float(winner.getkey("frequency")))
                    mpk = max(abs(parameters[0][0]), abs(parameters[1][0]),
                              abs(parameters[2][1]))
                    pkrms = mpk
                    if not isstats:
                        pkrms = mpk / noise
                    tfwhm = utils.freqtovel(freq, abs((wings[1] + wwidth[1]) -
                                                      (wings[0] - wwidth[0])))
                    chans = self.checktier1chans(peaks, [clow, chigh])
                    if chans is None:
                        identifications[freq] = self.gettier1line([clow, chigh])
                        identifications[freq].setkey("chans", [self.chan[self.chan.index(clow)],
                                                               self.chan[self.chan.index(chigh)]])
                        identifications[freq].setkey("freqs", [self.freq[self.chan.index(clow)],
                                                               self.freq[self.chan.index(chigh)]])
                    else:
                        line = copy.deepcopy(winner)
                        line.setkey({"velocity" : float(poffset + self.vlsr),
                                     "peakintensity" : float(mpk),
                                     "peakoffset" : float(poffset),
                                     "fwhm" :  float(tfwhm),
                                     "chans" : [self.chan[self.chan.index(chans[0])],
                                                self.chan[self.chan.index(chans[1])]],
                                     "freqs" : [self.freq[self.chan.index(chans[0])],
                                                self.freq[self.chan.index(chans[1])]],
                                     "peakrms" : float(pkrms)
                                    })
                        identifications[freq] = line
                    blends += wblends
                    wings.sort()
                    foundcomplex.append((wings, copy.deepcopy(winner)))
                # otherwise proceed as they are different lines
                else:
                    if centerpeak:
                        poffset = utils.freqtovel(freq, freq - winner.getkey("frequency"))
                        pkrms = parameters[0][0]
                        if not isstats:
                            pkrms /= noise
                        fwhm = utils.freqtovel(freq, parameters[0][2])
                        chans = self.checktier1chans(peaks, [parameters[0][3][0],
                                                             parameters[0][3][1]])
                        if chans is None:
                            identifications[freq] = self.gettier1line([parameters[0][3][0],
                                                                       parameters[0][3][1]])
                            identifications[freq].setkey("chans", [self.chan[self.chan.index(parameters[0][3][0])],
                                                                   self.chan[self.chan.index(parameters[0][3][1])]])
                            identifications[freq].setkey("freqs", [self.freq[self.chan.index(parameters[0][3][0])],
                                                                   self.freq[self.chan.index(parameters[0][3][1])]])
                        else:
                            line = copy.deepcopy(winner)
                            line.setkey({"velocity" : float(poffset + self.vlsr),
                                         "peakintensity" : float(peak),
                                         "peakoffset" : float(poffset),
                                         "fwhm" :  float(tfwhm),
                                         "chans" : [self.chan[self.chan.index(chans[0])],
                                                    self.chan[self.chan.index(chans[1])]],
                                         "freqs" : [self.freq[self.chan.index(chans[0])],
                                                    self.freq[self.chan.index(chans[1])]],
                                         "peakrms" : float(pkrms)
                                        })

                            identifications[freq] = line
                        blends += wblends

                    poffset = utils.freqtovel(wings[0], wings[0] - w1winner.getkey("frequency"))
                    pkrms = parameters[1][0]

                    if not isstats:
                        pkrms /= noise
                    fwhm = utils.freqtovel(freq, parameters[1][2])
                    chans = self.checktier1chans(peaks, [parameters[1][3][0], parameters[1][3][1]])
                    if chans is None:
                        identifications[freq] = self.gettier1line([parameters[1][3][0],
                                                                   parameters[1][3][1]])
                        identifications[freq].setkey("chans", [self.chan[self.chan.index(parameters[1][3][0])],
                                                               self.chan[self.chan.index(parameters[1][3][1])]])
                        identifications[freq].setkey("freqs", [self.freq[self.chan.index(parameters[1][3][0])],
                                                               self.freq[self.chan.index(parameters[1][3][1])]])
                    else:
                        line = copy.deepcopy(w1winner)
                        line.setkey({"velocity" : float(poffset + self.vlsr),
                                     "peakintensity" : float(wpeak[0]),
                                     "peakoffset" : float(poffset),
                                     "fwhm" :  float(fwhm),
                                     "chans" : [self.chan[self.chan.index(chans[0])],
                                                self.chan[self.chan.index(chans[1])]],
                                     "freqs" : [self.freq[self.chan.index(chans[0])],
                                                self.freq[self.chan.index(chans[1])]],
                                     "peakrms" : float(pkrms)
                                    })

                        identifications[wings[0]] = line
                    blends += w1blends
                    poffset = utils.freqtovel(wings[1], wings[1] - w2winner.getkey("frequency"))
                    pkrms = parameters[2][0]

                    if not isstats:
                        pkrms /= noise
                    fwhm = utils.freqtovel(wings[1], parameters[2][2])
                    chans = self.checktier1chans(peaks, [parameters[2][3][0], parameters[2][3][1]])
                    if chans is None:
                        identifications[freq] = self.gettier1line([parameters[2][3][0],
                                                                   parameters[2][3][1]])
                        identifications[freq].setkey("chans", [self.chan[self.chan.index(parameters[2][3][0])],
                                                               self.chan[self.chan.index(parameters[2][3][1])]])
                        identifications[freq].setkey("freqs", [self.freq[self.chan.index(parameters[2][3][0])],
                                                               self.freq[self.chan.index(parameters[2][3][1])]])
                    else:
                        line = copy.deepcopy(w2winner)
                        line.setkey({"velocity" : float(poffset + self.vlsr),
                                     "peakintensity" : float(wpeak[1]),
                                     "peakoffset" : float(poffset),
                                     "fwhm" :  float(fwhm),
                                     "chans" : [self.chan[self.chan.index(chans[0])],
                                                self.chan[self.chan.index(chans[1])]],
                                     "freqs" : [self.freq[self.chan.index(chans[0])],
                                                self.freq[self.chan.index(chans[1])]],
                                     "peakrms" : float(pkrms)
                                    })

                        identifications[wings[1]] = line
                    blends += w2blends
        # now do the single points
        for i in range(slen):
            if peaks.fsingles[i] == 0:
                continue
            found = False
            for fc in foundcomplex:
                wing = fc[0]
                win = fc[1]
                if wing[0] <= peaks.fsingles[i] <= wing[1]:
                    if slen == 1:
                        maxwidth = width = utils.veltofreq(10.0, peaks.fsingles[i])
                        breakpoint = 0
                        if i > 0:
                            delta = abs(peaks.getfreqs()[peaks.singles[i]] -
                                        peaks.getfreqs()[peaks.singles[i] - 1])
                        else:
                            delta = abs(peaks.getfreqs()[peaks.singles[i]] -
                                        peaks.getfreqs()[peaks.singles[i] + 1])
                    elif i > 0 and i < slen - 1:
                        maxwidth = width = min(abs(peaks.fsingles[i] - peaks.fsingles[i - 1]),
                                               abs(peaks.fsingles[i] - peaks.fsingles[i + 1]))
                        breakpoint = int(min(abs(peaks.singles[i] - peaks.singles[i - 1]),
                                             abs(peaks.singles[i] - peaks.singles[i + 1])))
                        delta = abs(peaks.getfreqs()[peaks.singles[i]] -
                                    peaks.getfreqs()[peaks.singles[i] - 1])
                    elif i > 0:
                        maxwidth = width = abs(peaks.fsingles[i] - peaks.fsingles[i - 1])
                        breakpoint = max(int(abs(peaks.singles[i] - peaks.singles[i - 1])), 5)
                        delta = abs(peaks.getfreqs()[peaks.singles[i]] -
                                    peaks.getfreqs()[peaks.singles[i] - 1])
                    else:
                        maxwidth = width = abs(peaks.fsingles[i] - peaks.fsingles[i + 1])
                        breakpoint = max(int(abs(peaks.singles[i] - peaks.singles[i + 1])), 5)
                        delta = abs(peaks.getfreqs()[peaks.singles[i]] -
                                    peaks.getfreqs()[peaks.singles[i] + 1])

                    if slen == 1:
                        st = int(max(0, peaks.singles[i] - 10))
                        en = int(min(len(peaks), peaks.singles[i] + 10))
                    else:
                        st = int(max(0, peaks.singles[i] - max(3 * int(width / (delta)), 3)))
                        en = int(min(len(peaks), peaks.singles[i] + max(3 * int(width / (delta)), 3)))
                    if st==en:
                        fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
                    popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - peaks.fsingles[i],
                                                  peaks.getspecs()[st:en + 1], par=[peak, 0.0, width],width=fwidth)
                    fcenter = peaks.fsingles[i] + popt[1]
                    endpoints = self.getchannels(peaks, noise, sid=peaks.singles[i])
                    if endpoints is None:
                        continue
                    poffset = utils.freqtovel(fcenter, fcenter - win.getkey("frequency"))
                    if abs(popt[2]) > 0.0:
                        width = abs(popt[2])
                    peak = peaks.getspecs()[peaks.singles[i]]
                    hpk = peak / 2.0
                    pkrms = hpk * 2.0
                    if not isstats:
                        pkrms /= noise

                    fwhm = utils.freqtovel(peaks.fsingles[i], abs(popt[2]))
                    chans = self.checktier1chans(peaks, [endpoints[0], endpoints[1]])
                    if chans is None:
                        identifications[peaks.fsingles[i]] = self.gettier1line([endpoints[0], endpoints[1]])
                        identifications[peaks.fsingles[i]].setkey("chans", [self.chan[self.chan.index(endpoints[0])],
                                                                            self.chan[self.chan.index(endpoints[1])]])
                        identifications[peaks.fsingles[i]].setkey("freqs", [self.freq[self.chan.index(endpoints[0])],
                                                                            self.freq[self.chan.index(endpoints[1])]])
                    else:
                        line = copy.deepcopy(win)
                        line.setkey({"velocity" : float(poffset + self.vlsr),
                                     "peakintensity" : float(peak),
                                     "peakoffset" : float(poffset),
                                     "fwhm" :  float(fwhm),
                                     "chans" : [self.chan[self.chan.index(chans[0])],
                                                self.chan[self.chan.index(chans[1])]],
                                     "freqs" : [self.freq[self.chan.index(chans[0])],
                                                self.freq[self.chan.index(chans[1])]],
                                     "peakrms" : float(hpk * 2.0 / pkrms)
                                    })

                        identifications[peaks.fsingles[i]] = line

                    found = True
            if found:
                continue
            # determine rough limits on the width of the lines both in frequency space and channel space
            # calculate the width of each channel
            # also be mindful of the edges of the window
            if slen == 1:
                maxwidth = width = utils.veltofreq(10.0, peaks.fsingles[i])
                breakpoint = 0
                if i > 0:
                    delta = abs(peaks.getfreqs()[peaks.singles[i]] - peaks.getfreqs()[peaks.singles[i] - 1])
                else:
                    delta = abs(peaks.getfreqs()[peaks.singles[i]] - peaks.getfreqs()[peaks.singles[i] + 1])
                st = int(max(0, peaks.singles[i] - 10))
                en = int(min(len(peaks), peaks.singles[i] + 10))
            elif i > 0 and i < slen - 1:
                maxwidth = width = min(abs(peaks.fsingles[i] - peaks.fsingles[i - 1]),
                                       abs(peaks.fsingles[i] - peaks.fsingles[i + 1]))
                breakpoint = int(min(abs(peaks.singles[i] - peaks.singles[i - 1]),
                                     abs(peaks.singles[i] - peaks.singles[i + 1])))
                delta = abs(peaks.getfreqs()[peaks.singles[i]] - peaks.getfreqs()[peaks.singles[i] - 1])
            elif i > 0:
                maxwidth = width = abs(peaks.fsingles[i] - peaks.fsingles[i - 1])
                breakpoint = max(int(abs(peaks.singles[i] - peaks.singles[i - 1])), 5)
                delta = abs(peaks.getfreqs()[peaks.singles[i]] - peaks.getfreqs()[peaks.singles[i] - 1])
            else:
                maxwidth = width = abs(peaks.fsingles[i] - peaks.fsingles[i + 1])
                breakpoint = max(int(abs(peaks.singles[i] - peaks.singles[i + 1])), 5)
                delta = abs(peaks.getfreqs()[peaks.singles[i]] - peaks.getfreqs()[peaks.singles[i] + 1])
            endpoints = self.getchannels(peaks, noise, sid=peaks.getchan(peaks.fsingles[i]))
            if endpoints is None:
                continue
            # get the spectral peak
            peak = peaks.getspecs()[peaks.singles[i]]
            hpk = peak / 2.0
            # calculate a rough FWHM
            for j in range(1, breakpoint):
                if peaks.getspecs()[max(peaks.singles[i] - j, 0)] < hpk or \
                   peaks.getspecs()[min(peaks.singles[i] + j, slen - 1)] < hpk:
                    width = min(2.0 * float(j) * delta, maxwidth)
                    break
            # calculate starting and ending channels to extract for the line fitting
            # cut will will be center +- 3*FWHM, keeping in mind the window edges
            if slen > 1:
                st = int(max(0, peaks.singles[i] - max(3 * int(width / (delta)), 3)))
                en = int(min(len(peaks), peaks.singles[i] + max(3 * int(width / (delta)), 3)))
            if st==en:
                fwidth = abs(peaks.getfreqs()[st]-peaks.getfreqs()[st+1])
            # fit the data with a gaussian
            popt, pcov = utils.fitgauss1D(peaks.getfreqs()[st:en + 1] - peaks.fsingles[i],
                                          peaks.getspecs()[st:en + 1], par=[peak, 0.0, width],width=fwidth)
            width = abs(peaks.getfreq(endpoints[0]) - peaks.getfreq(endpoints[1])) / 2.
            fcenter = peaks.fsingles[i] + popt[1]
            fwhm = utils.freqtovel(peaks.fsingles[i], abs(popt[2]))
            limits = peaks.limitwidth(peaks.fsingles[i], width)
            # look for an identification around the line
            possibilities = []
            possibilities += self.generatepossibles(limits)
            # look for other identifications in case this line is red/blue shifted due to rotation/collapse
            if not ispvcorr:
                for k in peaks.offsets:
                    possibilities += self.generatepossibles([peaks.fsingles[i] - width - k,
                                                             peaks.fsingles[i] + width - k])

                    possibilities += self.generatepossibles([peaks.fsingles[i] - width + k,
                                                             peaks.fsingles[i] + width + k])
            if len(possibilities) == 0:
                # if none were found the set it as a U line
                species = "U_%.4f" % (peaks.fsingles[i])
                name = "Unknown"
                freq = peaks.fsingles[i]
                qn = ""
                linestr = 0.0
                eu = 0.0
                el = 0.0
                poffset = 0.0
                winner = LineData(formula=species, name=name, frequency=float(freq), uid=species,
                                  energies=[el, eu], linestrength=linestr,
                                  mass=utils.getmass(species), transition=qn, plain=species)
            else:
                # narrow down the possibilities
                # eliminate doubles before proceeding
                drop = set()
                for k, poss in enumerate(possibilities):
                    for j in range(k + 1, len(possibilities)):
                        if poss.frequency == possibilities[j].frequency and \
                            poss.transition == possibilities[j].transition and \
                           poss.formula == possibilities[j].formula:
                            drop.add(j)
                drop = list(drop)
                drop.sort()
                drop.reverse()
                for d in drop:
                    del possibilities[d]

                temp = self.narrowpossibles(possibilities)
                winner = temp.pop(0)
                for b in temp:
                    blends.append(b)

                # calculate velocity offset
                poffset = utils.freqtovel(fcenter, fcenter - winner.getkey("frequency"))
            pkrms = hpk * 2.0
            if not isstats:
                pkrms /= noise
            delta = utils.freqtovel(peaks.fsingles[i], delta)
            chans = self.checktier1chans(peaks, [endpoints[0], endpoints[1]])
            if chans is None:
                identifications[peaks.fsingles[i]] = self.gettier1line([endpoints[0], endpoints[1]])
                identifications[peaks.fsingles[i]].setkey("chans", [self.chan[self.chan.index(endpoints[0])],
                                                                    self.chan[self.chan.index(endpoints[1])]])
                identifications[peaks.fsingles[i]].setkey("freqs", [self.freq[self.chan.index(endpoints[0])],
                                                                    self.freq[self.chan.index(endpoints[1])]])
            else:
                line = copy.deepcopy(winner)
                line.setkey({"velocity" : float(poffset + self.vlsr),
                             "peakintensity" : float(peak),
                             "peakoffset" : float(poffset),
                             "fwhm" :  float(fwhm),
                             "chans" : [self.chan[self.chan.index(chans[0])],
                                        self.chan[self.chan.index(chans[1])]],
                             "freqs" : [self.freq[self.chan.index(chans[0])],
                                        self.freq[self.chan.index(chans[1])]],
                             "peakrms" : float(hpk * 2.0 / pkrms)
                            })

                identifications[peaks.fsingles[i]] = line
        badblends = []
        for i, blend in enumerate(blends):
            found = False
            for ident in identifications.values():
                if ident.blend == blend.blend:
                    found = True
            if not found:
                badblends.append(i)
        badblends.reverse()
        for b in badblends:
            del blends[b]

        for b in blends:
            for line in identifications.values():
                if b.blend == line.blend:
                    b.setkey("chans", line.getkey("chans"))
                    b.setkey("freqs", line.getkey("freqs"))
        peaks.linelist.update(identifications)
        peaks.blends += blends

    def getchannels(self, peaks, noise, sid=-1, cid=-1, asfreq=False):
        """ Method to determine the channel ranges for thr given spectral line.
            First uses the segment to get the maximum extent of the line, then
            compares the channel range to all other peaks and makes adjustments
            so that the channel range does not incorporate mote than one peak.

            Parameters
            ----------
            peaks : Peaks instance
                The peaks instance which lists all peaks in the spectrum

            noise : float
                The noise level of the spectrum

            sid : int
                Center channel of the spectrum to find the channel ranges for.
                Default: -1

            cid : int
                Center channel of the cluster to find the channel ranges for.
                Default: -1

            asfreq : bool
                Whether to return the end poitns in frequency units (True) or
                channel numbers (False).
                Defult : False (channel numbers)

            Returns
            -------
            List containing both the start and end channels for the given peak

            Notes
            -----
            Both sid and cid are mutually exclusive.

        """
        if sid == cid == -1:
            raise Exception("An id index must be given, sid or cid")
        if sid > -1 and cid > -1:
            raise Exception("Only one of sid or cid can be given")
        # if we are given a single line to trace
        if sid > -1:
            # get the initial trace
            points = copy.deepcopy(peaks.getsegment(int(sid)))
            # now see if it encompases other peaks, if it does then move the endpoint(s)
            # so that they do not overlap
            if points is None:
                return None
            for spk in peaks.singles:
                if spk == sid:
                    continue
                if points[0] < spk < sid:
                    points[0] = int((sid + spk) / 2)
                elif points[1] > spk > sid:
                    points[1] = int((sid + spk) / 2)
            # do the same for the clusters
            for chan, v in peaks.centers.iteritems():
                if v[0]:
                    if points[0] < chan < sid:
                        points[0] = int((sid + chan) / 2)
                    elif points[1] > chan > sid:
                        points[1] = int((sid + chan) / 2)
                for ch in v[1]:
                    if points[0] < ch < sid:
                        points[0] = int((sid + ch) / 2)
                    elif points[1] > ch > sid:
                        points[1] = int((sid + ch) / 2)
            # if frequency units are requested
            if asfreq:
                t1 = peaks.getfreq(points[0])
                t2 = peaks.getfreq(points[1])
                points[0] = min(t1, t2)
                points[1] = max(t1, t2)
            return points
        # if we are given a cluster to trace
        if cid > -1:
            # get the initial trace
            points = copy.deepcopy(peaks.getsegment(int(cid)))
            # now see if it encompases other peaks, if it does then move the endpoint(s)
            # so that they do not overlap
            if points is None:
                return None
            for spk in peaks.singles:
                if points[0] < spk < cid:
                    points[0] = int((cid + spk) / 2)
                elif points[1] > spk > cid:
                    points[1] = int((cid + spk) / 2)
            # do the same for the clusters
            for chan, v in peaks.centers.iteritems():
                if v[0]:
                    if chan == cid:
                        break
                    if points[0] < chan < cid:
                        points[0] = int((cid + chan) / 2)
                    elif points[1] > chan > cid:
                        points[1] = int((cid + chan) / 2)
                for ch in v[1]:
                    if ch == cid:
                        continue
                    if points[0] < ch < cid:
                        points[0] = int((cid + ch) / 2)
                    elif points[1] > ch > cid:
                        points[1] = int((cid + ch) / 2)
            # if frequency units are requested
            if asfreq:
                t1 = peaks.getfreq(points[0])
                t2 = peaks.getfreq(points[1])
                points[0] = min(t1, t2)
                points[1] = max(t1, t2)
            return points

    def checkcount(self, counts):
        """ Method to determine if there are too many peaks for the pattern finder to be of use. If
            there are too many points then false patterns can be found. The threshold has been
            experimentally determined to be a second order poynolmial based on the number of
            of channels. See the design documentation for specifics and details.

            Parameters
            ----------
            counts : dict
                Dictionary containing the peaks for each input spectrum.

            Returns
            -------
            Bool, True if there are too many peaks for the pattern finder to be of use, False
            otherwise.

        """
        fit = [42.96712785, -777.04366254, 3892.90652112]
        for peaks in counts["stats"]:
            count = len(peaks)
            if count < 10:
                if len(self.freq) < count*48.07692308:
                    logging.info("Too many peaks in CubeStats for pattern finding to be useful, turning it off.")
                    return True
            elif len(self.freq) < fit[0] * count**2 + fit[1] * count + fit[2]:
                logging.info("Too many peaks in CubeStats for pattern finding to be useful, turning it off.")
                return True
        for peaks in counts["specs"]:
            count = len(peaks)
            if count < 10:
                if len(self.freq) < count*48.07692308:
                    logging.info("Too many peaks in CubeSpectrum for pattern finding to be useful, turning it off.")
                    return True
            elif len(self.freq) < fit[0] * count**2 + fit[1] * count + fit[2]:
                logging.info("Too many peaks in CubeSpectrum for pattern finding to be useful, turning it off.")
                return True
        return False

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
        self.dt = utils.Dtime("LineID")
        if not self.boxcar:
            logging.info("Boxcar smoothing turned off.")
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
        for rej in self.reject:
            if rej[1] is None:
                logging.info(" Rejecting all transitions of %s." % (rej[0]))
            else:
                logging.info("Rejecting %s at %f GHz." % (rej[0], rej[1]))

        if self.getkey("minchan") < 1:
            raise Exception("minchan must be a positive integer.")
        elif self.getkey("minchan") == 1 and self.getkey("iterate"):
            logging.info("iterate=True is not allowed for minchan=1, setting iterate to False")
            self.setkey("iterate", False)
        havesomething = False

        for i, ident in enumerate(self.getkey("force")):
            if isinstance(ident, LineData):
                ident.setkey("force", True)
                ident.setkey("uid",isent.getkey("uid") + "F%02i" % i)
                self.force.append(ident)
                logging.info(" Forcing: %s  @  %f GHz  chans[%i, %i]" % (ident.getkey("formula"),
                                                                         ident.getkey("frequency"),
                                                                         ident.getstart(),
                                                                         ident.getend()))
            elif isinstance(ident, tuple) or isinstance(ident, list):
                if len(ident) != 8:
                    raise Exception("Incorrect number of items in force entry. See documentation for correct entries, all are required.")
                self.force.append(LineData(frequency=ident[0], uid=ident[1] + "F%02i" % i, formula=ident[2],
                                           name=ident[3], transition=ident[4],
                                           velocity=float(ident[5]),
                                           chans=[int(ident[6]), int(ident[7])], force=True))
                logging.info(" Forcing: %s  @  %f GHz  chans[%i, %i]" % (ident[2], ident[0],
                                                                         int(ident[6]), int(ident[7])))
            else:
                raise Exception("Improper format for force list. The list must contain tuples, lists or LineData objects, not %s." % (type(ident)))
            self.forcechans.append(self.force[-1].getkey("chans"))
            havesomething = True

        # get the input bdp
        if self._bdp_in[0] is not None:
            specbdp = self._bdp_in[0]
            self.infile = specbdp.xmlFile
        if self._bdp_in[1] is not None:
            statbdp = self._bdp_in[1]
            self.infile = statbdp.xmlFile
        if self._bdp_in[2] is not None:
            pvbdp = self._bdp_in[2]
            self.infile = pvbdp.xmlFile
        # still need to do this check since all are optional inputs
        if specbdp == pvbdp == statbdp is None:
            raise Exception("No input BDP's found.")
        imbase = self.mkext(self.infile, 'll')

        llbdp = LineList_BDP(imbase)

        self.vlsr = self.getkey("vlsr")
        self.identifylines = self.getkey("identifylines")
        if self.vlsr < -999999.0 and self.identifylines:
            try:
                self.vlsr = admit.Project.summaryData.get('vlsr')[0].getValue()[0]
                logging.info("Set vlsr = %.2f for line identification." % self.vlsr)
            except:
                logging.info("No vlsr found in summary data and none given as an argument, switching identifylines to False.")
                self.identifylines = False
            # Ingest_AT could still have written the magic value if RESTFREQ is missing 
            if self.vlsr < -999999.0:
                self.identifylines = False
        if self.identifylines:
            vlsr = self.vlsr
        else:
            vlsr = 0.0
        logging.info("Identifylines = %s" % str(self.identifylines))
        logging.info("Using vlsr = %g" % vlsr)

        # grab any optional references overplotted on the "ll" plots
        line_ref = utils.get_references(self.getkey("references"))

        # Default to SVG output (full-size PNG also produced on-the-fly during
        # thumbnail creation).
        self._plot_type = admit.util.PlotControl.SVG

        # instantiate a plotter for all plots made herein
        myplot = APlot(ptype=self._plot_type, pmode=self._plot_mode, abspath=self.dir())

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
        segargsforcont = {"name":    "Line_ID.%i.asap" % self.id(True),
                     "pmin":    self.getkey("numsigma"),
                     "minchan": self.getkey("minchan"),
                     "maxgap":  self.getkey("maxgap")}

        if specbdp is not None:
            self.specs = specutil.getspectrum(specbdp, vlsr, self.getkey("smooth"),
                                              self.getkey("recalcnoise"), basicsegment)
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

        if statbdp is not None:
            self.statspec = specutil.getspectrum(statbdp, vlsr, self.getkey("smooth"),
                                                 self.getkey("recalcnoise"), basicsegment)
            # remove the continuum
            if self.getkey("csub")[0] is not None:
                order = self.getkey("csub")[0]
                logging.info("Attempting Continuum Subtraction for Input CubeStats Spectra")
                specutil.contsub(self.id(True),self.statspec, self.getkey("segment"), segargsforcont,algorithm="PolyFit",**{"deg" : order})
            else:
                for i, spec in enumerate(self.statspec):
                    spec.set_contin(np.zeros(len(spec)))

            if len(self.statspec) > 0: self.statspec[1].invert()
            for spec in self.statspec:
                self.freq,self.chan = specutil.mergefreq(self.freq,self.chan,spec.freq(False), spec.chans(False))

            self.dt.tag("getspectrum-cubestats")

        if pvbdp is not None:
            self.pvspec = specutil.getspectrum(pvbdp, vlsr, self.getkey("smooth"))
            self.pvsigma = pvbdp.sigma
            if len(self.pvspec.freq(False)) == 0:
                pvbdp = None
            else:
                self.freq,self.chan = specutil.mergefreq(self.freq,self.chan,self.pvspec.freq(False), self.pvspec.chans(False))
                self.pvspec.set_contin(np.zeros(len(self.pvspec)))

        # Add spectra to the output BDPs.
        if specbdp is not None:
            for indx, spec in enumerate(self.specs):
                llbdp.addSpectrum(spec, "CubeSpectrum_%i" % (indx))

        if statbdp is not None:
            for indx, spec in enumerate(self.statspec):
                llbdp.addSpectrum(spec, "CubeStats_%i" % (indx))

        if pvbdp is not None:
            llbdp.addSpectrum(self.pvspec, "PVCorr")

        if isinstance(self.freq, np.ndarray):
            self.freq = self.freq.tolist()
        if isinstance(self.chan, np.ndarray):
            self.chan = self.chan.tolist()
        self.integritycheck()

        for force in self.force:
            rng = [self.freq[force.getstart()], self.freq[force.getend()]]
            force.setkey("freqs", [min(rng), max(rng)])
            self.forcefreqs.append([min(rng), max(rng)])

        # seach for segments of spectral line emission

        method=self.getkey("segment") 
        minchan=self.getkey("minchan")
        maxgap=self.getkey("maxgap") 
        numsigma=self.getkey("numsigma")
        iterate=self.getkey("iterate")

        self.dt.tag("segment finder")
        if specbdp is not None:
            logging.info("Detecting segments in CubeSpectrum based data")
            values = specutil.findsegments(self.specs, method, minchan, maxgap, numsigma, iterate)
            for i, t in enumerate(values):
                self.specseg.append(self.checkforcesegs(t[0]))
                self.specs[i].set_noise(t[2])
                self.speccutoff.append(t[1])

        if statbdp is not None:
            logging.info("Detecting segments in CubeStats based data")
            values = specutil.findsegments(self.statspec, method, minchan, maxgap, numsigma, iterate)
            for i, t in enumerate(values):
                self.statseg.append(self.checkforcesegs(t[0]))
                self.statspec[i].set_noise(t[2])


        if pvbdp is not None:
            logging.info("Detecting segments in PVCorr based data")
            values = specutil.findsegments([self.pvspec], method, minchan, maxgap, numsigma, iterate,noise=self.pvsigma)
            self.pvspec.set_noise(self.pvsigma)  # @TODO: why not values[0][2]?
            for t in values:
                self.pvseg = self.checkforcesegs(t[0])
                self.pvcutoff = t[1]

        # label and captions used immediately below and later in the code.
        label = ["Peak/Noise", "Minimum/Noise"]
        caption = ["Potential lines overlaid on peak intensity plot from CubeStats_BDP.",
                   "Potential lines overlaid on minimum intensity plot from CubeStats_BDP."]

        # if we have no vlsr or just want the segments
        # create the output

        if not self.identifylines:
            segments = utils.mergesegments([self.statseg,self.specseg,self.pvseg],len(self.freq))
            lines = specutil.linedatafromsegments(self.freq,self.chan,segments,self.specs,self.statspec)
            duplicate_lines = []
            for l in lines:
                if l.getkey('uid') in duplicate_lines:
                    logging.log(logging.WARNING, " Skipping-2 duplicate UID: " + l.getkey("uid"))
                    continue
                else:
                    duplicate_lines.append(l.getkey('uid'))
                llbdp.addRow(l)
                logging.regression("LINEID: %s %.5f  %d %d" % ("NotIdentified", l.frequency, l.chans[0], l.chans[1]))

            # @todo  vlsr could now have been taken from Summary, so getkey() is an old value
            if self.getkey("vlsr") > -999998.0:
                t = "Rest"
            else:
                t = "Sky"
            xlabel = "%s Frequency (GHz)" % (t)

            for i, spec in enumerate(self.statspec):
                freqs = []
                for ch in self.statseg[i]:
                    freqs.append([min(spec.freq()[ch[0]], spec.freq()[ch[1]]),
                                  max(spec.freq()[ch[0]], spec.freq()[ch[1]])])
                mult = 1.
                if i == 1:
                    mult = -1.
#                print("MWP plot cutoff[%d] = %f, contin=%f" % (i, (spec.contin() + mult*(spec.noise() * self.getkey("numsigma")))[0], spec.contin()[0] ) )
                myplot.segplotter(x=spec.freq(), y=spec.spec(csub=False),
                                  title="Potential Line Locations", xlab=xlabel,
                                  ylab=label[i], figname=imbase + "_statspec%i" % i, segments=freqs,
                                  cutoff=(spec.contin() + mult * (spec.noise() * self.getkey("numsigma"))),
                                  continuum=spec.contin(), thumbnail=True)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)
                image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                              thumbnailtype=bt.PNG, description=caption[i])
                llbdp.image.addimage(image, "statspec%i" % i)
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname,
                                              thumbnailname, caption[i], self.infile])

            for i, spec in enumerate(self.specs):
                freqs = []
                for ch in self.specseg[i]:
                    freqs.append([min(spec.freq()[ch[0]], spec.freq()[ch[1]]),
                                  max(spec.freq()[ch[0]], spec.freq()[ch[1]])])
                myplot.segplotter(x=spec.freq(), y=spec.spec(csub=False),
                                  title="Potential Line Locations", xlab=xlabel,
                                  ylab="Intensity", figname=imbase + "_spec%03d" % i, segments=freqs,
                                  cutoff=spec.contin() + (spec.noise() * self.getkey("numsigma")),
                                  continuum=spec.contin(), thumbnail=True)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno,
                                                    relative=True)
                _caption = "Potential lines overlaid on input spectrum #%i." % (i)
                image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                              thumbnailtype=bt.PNG, description=_caption)
                llbdp.image.addimage(image, "spec%03d" % i)
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname,
                                              thumbnailname, _caption, self.infile])

            if self.pvspec is not None:
                freqs = []
                for ch in self.pvseg:
                    freqs.append([min(self.pvspec.freq()[ch[0]], self.pvspec.freq()[ch[1]]),
                                  max(self.pvspec.freq()[ch[0]], self.pvspec.freq()[ch[1]])])

                myplot.segplotter(x=self.pvspec.freq(), y=self.pvspec.spec(csub=False),
                                  title="Potential Line Locations", xlab=xlabel,
                                  ylab="Corr. Coef.", figname=imbase + "_pvspec",
                                  segments=freqs, cutoff=self.pvspec.noise() * self.getkey("numsigma"),
                                  thumbnail=True)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno,
                                                    relative=True)
                _caption = "Potential lines overlaid on Correlation plot from PVCorr_BDP."
                image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                              thumbnailtype=bt.PNG, description=_caption)
                llbdp.image.addimage(image, "pvspec")
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel,
                                              imname, thumbnailname, _caption,
                                              self.infile])

            self._summary["linelist"] = SummaryEntry(llbdp.table.serialize(), "LineID_AT",
                                                     self.id(True), taskargs)
            self._summary["spectra"] = [SummaryEntry(self.spec_description, "LineID_AT",
                                                     self.id(True), taskargs)]

            self.addoutput(llbdp)
            self.dt.tag("done")
            self.dt.end()
            return

        tpeaks = {}
        # do the peak finding
        spnoise = []
        # loop over all of the requested methods
        for method, margs in self.getkey("method").iteritems():
            logging.info("Searching for spectral peaks with method: %s" % (method))
            tpeaks[method] = {"stats" : [],
                              "specs" : [],
                              "pvc"   : None}
            # look for peaks in the statspec data
            for i, spec in enumerate(self.statspec):
                logging.debug("Searching for spectral peaks statspec %d" % i)
                args = {"spec"      : spec.spec(),
                        "y"         : spec.freq(),
                        "min_width" : self.getkey("minchan")}
                args.update(margs)
                args["thresh"] = float(spec.noise() * self.getkey("numsigma"))
                pks = self.getpeaks(method, args, spec.spec(), self.statseg[i], iterate=self.getkey("iterate"))
                tpeaks[method]["stats"].append(self.removepeaks(pks, self.statseg[i]))
            # look for peaks in the cubespec data
            for i, spec in enumerate(self.specs):
                logging.debug("Searching for spectral peaks specs %d" % i)
                args = {"spec"      : spec.spec(),
                        "y"         : spec.freq(),
                        "min_width" : self.getkey("minchan")}
                args.update(margs)
                if margs["thresh"] == 0.0:
                    args["thresh"] = float(spec.noise() * self.getkey("numsigma"))
                spnoise.append(args["thresh"])
                pks = self.getpeaks(method, args, spec.spec(), self.specseg[i], iterate=self.getkey("iterate"))
                tpeaks[method]["specs"].append(self.removepeaks(pks, self.specseg[i]))
            # look for peaks in the pvcorr data
            if self.pvspec is not None:
                logging.debug("Searching for spectral peaks pvspec")
                args = {"spec"      : self.pvspec.spec(),
                        "y"         : self.pvspec.freq(),
                        "min_width" : self.getkey("minchan")}
                args.update(margs)
                args["thresh"] = float(self.pvspec.noise() * self.getkey("numsigma"))
                pks = self.getpeaks(method, args, self.pvspec.spec(), self.pvseg, iterate=False)
                tpeaks[method]["pvc"] = self.removepeaks(pks, self.pvseg)

        # now merge it all together into a single dictionary
        allpeaks = {"stats" : [],
                    "specs" : [],
                    "pvc"   : None}
        # must be detected in at least 2 methods or ALL requested methods
        mode = self.getkey("mode").upper()
        logging.debug("merging all peaks for mode=%s" % mode)
        # do the stats first
        for i in range(len(self.statspec)):
            fullstats = set()
            statlist = []
            for v in tpeaks.values():
                statlist.append(v["stats"][i])
            target = 0   # add everything that is unique

            if len(self.getkey("method")) > 1:
                if "ALL" in mode:
                    target = len(statlist)
                elif "TWO" in mode:
                    target = 2
            for j in range(len(statlist)):
                for point in statlist[j]:
                    count = 0
                    for i in range(j + 1, len(statlist)):
                        for stat in statlist[i]:
                            if point - self.tol / 2.0 < stat < point + self.tol / 2.0:
                                count += 1
                                statlist[i].remove(stat)
                                break
                    if count >= target:
                        fullstats.add(point)
            temp = sorted(fullstats)
            allpeaks["stats"].append(temp)
            havesomething = havesomething or len(temp) > 0
        # then the spectra
        if len(self.specs) != 0:
            target = 0
            if "TWO" in mode:
                target = 2
            for row in range(len(self.specs)):
                fullspec = set()
                speclist = []
                for v in tpeaks.values():
                    speclist.append(v["specs"][row])
                if "ALL" in mode:
                    target = len(speclist)
                for j in range(len(speclist)):
                    for point in speclist[j]:
                        count = 0
                        for i in range(j + 1, len(speclist)):
                            for sp in speclist[i]:
                                if point - self.tol / 2.0 < sp < point + self.tol / 2.0:
                                    count += 1
                                    speclist[i].remove(sp)
                                    break
                        if count >= target:
                            fullspec.add(point)
                temp = sorted(fullspec)
                allpeaks["specs"].append(temp)
                havesomething = havesomething or len(temp) > 0

        if self.pvspec is not None:
            fullpvc = set()
            pvclist = []
            for spec, v in tpeaks.iteritems():
                pvclist.append(v["pvc"])
            target = 0   # add everything that is unique

            if len(self.getkey("method")) > 1:
                if "ALL" in mode:
                    target = len(pvclist)
                elif "TWO" in mode:
                    target = 2
            for j in range(len(pvclist)):
                for point in pvclist[j]:
                    count = 0
                    for i in range(j + 1, len(pvclist)):
                        for pv in pvclist[i]:
                            if point - self.tol / 2.0 < pv < point + self.tol / 2.0:
                                count += 1
                                pvclist[i].remove(pv)
                                break
                    if count >= target:
                        fullpvc.add(point)
            allpeaks["pvc"] = sorted(fullpvc)
            havesomething = havesomething or len(allpeaks["pvc"]) > 0

        # if nothing was detected
        if not havesomething:
            logging.warning("No lines detected by LineID.")
            # regression:  name, freq, ch0, ch1
            if self.getkey("vlsr") > -999998.0:
                t = "Rest"
            else:
                t = "Sky"
            xlabel = "%s Frequency (GHz)" % (t)
            # cubestats output
            for i, spec in enumerate(self.statspec):
                mult = 1.
                if i == 1:
                    mult = -1.
                myplot.makespec(x=spec.freq(), y=spec.spec(csub=False), chan=spec.chans(),
                                cutoff=(spec.contin() + mult * (spec.noise() * self.getkey("numsigma"))),
                                figname=imbase +"_statspec%i" % i, title="Line ID (vlsr=%.2f)" % self.vlsr,
                                xlabel=xlabel, lines={}, force=self.force, blends=[],
                                continuum=spec.contin(), ylabel=label[i],
                                thumbnail=True, references=line_ref)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)

                image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                              thumbnailtype=bt.PNG, description=caption[i])
                llbdp.image.addimage(image, "statspec%i" % i)
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname,
                                              thumbnailname, caption[i], self.infile])
            # cubespec output (1 for each input spectra, there could be many from a single BDP)
            for i, spec in enumerate(self.specs):
                myplot.makespec(x=spec.freq(), y=spec.spec(csub=False), chan=spec.chans(),
                                cutoff=spec.contin() + spnoise[i],
                                figname=imbase +"_spec%03d" % i,
                                title="Line ID (vlsr=%.2f)" % self.vlsr, xlabel=xlabel,
                                lines={}, force=self.force, blends=[],
                                continuum=spec.contin(), thumbnail=True,
                                references=line_ref)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno,
                                                    relative=True)
                _caption = "Identified lines overlaid on input spectrum #%i." % (i)
                image = Image(images={bt.SVG: imname},
                              thumbnail=thumbnailname, thumbnailtype=bt.PNG,
                              description=_caption)
                llbdp.image.addimage(image, "spec%03d" % i)
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname,
                                              thumbnailname, _caption, self.infile])

            if self.pvspec is not None:
                myplot.makespec(x=self.pvspec.freq(), y=self.pvspec.spec(csub=False), chan=self.pvspec.chans(),
                                cutoff=self.pvcutoff,
                                figname=imbase + "_pvspec", title="Line ID (vlsr=%.2f)" % self.vlsr,
                                xlabel=xlabel, lines={}, force=self.force, blends=[],
                                continuum=[0.0] * len(self.pvspec), ylabel="Corr. Coeff.",
                                thumbnail=True, references=line_ref)
                imname = myplot.getFigure(figno=myplot.figno, relative=True)
                thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)

                _caption = "Identified lines overlaid on Correlation Coefficient plot from PVCorr_BDP."
                image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                              thumbnailtype=bt.PNG, description=_caption)
                llbdp.image.addimage(image, "pvspec")
                self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname,
                                              thumbnailname, _caption, self.infile])

            self._summary["linelist"] = SummaryEntry(llbdp.table.serialize(), "LineID_AT",
                                                     self.id(True), taskargs)
            self._summary["spectra"] = [SummaryEntry(self.spec_description, "LineID_AT",
                                                     self.id(True), taskargs)]
            self.addoutput(llbdp)
            self.dt.tag("nolines")
            self.dt.end()
            Peaks.reset()
            # no lines detected
            return

        # do pattern matching
        peaks = {"stats" : [],
                 "specs" : [],
                 "pvc"   : None}
        toomanypeaks = self.checkcount(allpeaks)
        for i, spec in enumerate(self.statspec):
            self.current = "CubeStat %i" % (i)
            if self.pattern == "ON" or (self.pattern == "AUTO" and not toomanypeaks):
                peaks["stats"].append(self.findpatterns(spec, allpeaks["stats"][i], self.statseg[i]))
            else:
                stpeaks = Peaks(spec=spec)
                stpeaks.singles = allpeaks["stats"][i]
                stpeaks.pairs = {}
                stpeaks.segments = self.statseg[i]
                peaks["stats"].append(stpeaks)
        for i, spec in enumerate(self.specs):
            self.current = "CubeSpec %i" % (i)
            if self.pattern == "ON" or (self.pattern == "AUTO" and not toomanypeaks):
                peaks["specs"].append(self.findpatterns(spec, allpeaks["specs"][i],
                                                        self.specseg[i]))
            else:
                sppeaks = Peaks(spec=spec)
                sppeaks.singles = allpeaks["specs"][i]
                sppeaks.pairs = {}
                sppeaks.segments = self.specseg[i]
                peaks["specs"].append(sppeaks)
        if self.pvspec is not None:
            pvpeaks = Peaks(spec=self.pvspec)
            pvpeaks.singles = allpeaks["pvc"]
            pvpeaks.segments = self.pvseg
            pvpeaks.pairs = {}
            peaks["pvc"] = pvpeaks
        # now flatten the pattern to remove noise
        mpattern = []
        for i in range(len(self.statspec)):
            mpattern += peaks["stats"][i].flatten(self.tol)
            peaks["stats"][i].sort()
        for i in range(len(self.specs)):
            mpattern += peaks["specs"][i].flatten(self.tol)
            peaks["specs"][i].sort()
        if self.pvspec is not None:
            mpattern += peaks["pvc"].flatten(self.tol)
            peaks["pvc"].sort()

        # initialize the output bdp
        llist = []
        foundsomething = False
        # for each detected line search for an identity
        if self.getkey("vlsr") > -999998.0:
            t = "Rest"
        else:
            t = "Sky"
        tier1, hfs = self.gettier1()

        for i in range(len(self.statspec)):
            peaks["stats"][i].converttofreq()
        for i in range(len(peaks["specs"])):
            peaks["specs"][i].converttofreq()
        if self.pvspec is not None:
            peaks["pvc"].converttofreq()

        # start with the statspec
        for i in range(len(self.statspec)):
            drop = []

            self.identify(peaks["stats"][i], self.statspec[i].noise(), tier1, hfs, isstats=True)

            # if at least 1 line was found, apply the results to the other spectra
            if len(peaks["stats"][i].linelist) > 0:
                foundsomething = True
            for k, v in peaks["stats"][i].linelist.iteritems():
                if v.getstart() <= self.getkey("minchan")/2 and k < peaks["stats"][i].getfreq(v.getstart()):
                    drop.append(k)
                elif v.getend() >= (len(peaks["stats"][i].spec) - self.getkey("minchan")/2) and \
                   k > peaks["stats"][i].getfreq(v.getend()):
                    drop.append(k)
            for d in drop:
                del peaks["stats"][i].linelist[d]
            peaks["stats"][i].validatelinesegments()

        for i in range(len(peaks["specs"])):
            self.identify(peaks["specs"][i], self.specs[i].noise(), tier1, hfs)

            if len(peaks["specs"][i].linelist) > 0 and foundsomething is False:
                foundsomething = True
            drop = []

            for k, v in peaks["specs"][i].linelist.iteritems():
                if v.getstart() <= self.getkey("minchan") / 4 and \
                   k < min(peaks["specs"][i].getfreq(v.getstart()),
                           peaks["specs"][i].getfreq(v.getend())):
                    drop.append(k)
                elif v.getend() >= (len(peaks["specs"][i].spec) - self.getkey("minchan") / 4) \
                   and k > max(peaks["specs"][i].getfreq(v.getstart()),
                               peaks["specs"][i].getfreq(v.getend())):
                    drop.append(k)
            for d in drop:
                del peaks["specs"][i].linelist[d]

            peaks["specs"][i].validatelinesegments()

        if self.pvspec is not None:
            self.identify(peaks["pvc"], self.pvspec.noise(), tier1, hfs, ispvcorr=True)
            peaks["pvc"].validatelinesegments()

        # check through all lines:
        #  1. Unidentified lines cannot overlap with identified lines
        #  2. One line cannot be fully indside of another line, unless forced
        done = False
        loopcount = 0
        while not done and loopcount < 3:
            done = True
            for i, spec in enumerate(peaks["specs"]):
                for line in spec.linelist.values():
                    for j in range(i + 1, len(peaks["specs"])):
                        for sline in peaks["specs"][j].linelist.values():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines cannot overlap with identified lines
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "transition" : sline.getkey("transition"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                line.setkey(data)
                            elif ("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula"))):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "transition" : line.getkey("transition"),
                                        "uid"  : line.getkey("uid"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                sline.setkey(data)

                    for stat in peaks["stats"]:
                        for ll, sline in stat.linelist.iteritems():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines cannot overlap with identified lines
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "transition" : sline.getkey("transition"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                line.setkey(data)
                            elif ("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula"))):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "transition" : line.getkey("transition"),
                                        "uid"  : line.getkey("uid"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                sline.setkey(data)
                    if peaks["pvc"] is not None:
                        for sline in peaks["pvc"].linelist.values():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines can overlap
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro) and not line.getkey("force"):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "transition" : sline.getkey("transition"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                line.setkey(data)
                            elif (("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula")))) and not sline.getkey("force"):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "uid"  : line.getkey("uid"),
                                        "transition" : line.getkey("transition"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                sline.setkey(data)
            for spec in peaks["stats"]:
                for line in spec.linelist.values():
                    for j in range(i + 1, len(peaks["specs"])):
                        for sline in peaks["specs"][j].linelist.values():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines cannot overlap with identified lines
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "transition" : sline.getkey("transition"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                line.setkey(data)
                            elif ("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env  and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula"))):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "transition" : line.getkey("transition"),
                                        "uid"  : line.getkey("uid"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                sline.setkey(data)

                    for stat in peaks["specs"]:
                        for sline in stat.linelist.values():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines cannot overlap with identified lines
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "transition" : sline.getkey("transition"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                line.setkey(data)
                            elif ("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env  and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula"))):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "transition" : line.getkey("transition"),
                                        "uid"  : line.getkey("uid"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                                sline.setkey(data)

                    if peaks["pvc"] is not None:
                        for sline in peaks["pvc"].linelist.values():
                            lo = False
                            ro = False
                            env = False
                            if sline.getstart() <= line.getstart() <= sline.getend():
                                lo = True
                            if sline.getstart() <= line.getend() <= sline.getend():
                                ro = True
                            if line.getstart() <= sline.getstart() <= line.getend() and\
                               line.getstart() <= sline.getend() <= line.getend():
                                env = True
                            # Ulines can overlap
                            if "Ukn" in line.getkey("name") and "Ukn" not in sline.getkey("name") and (lo or ro) and not line.getkey("force"):
                                done = False
                                poffset = utils.freqtovel(sline.getkey("frequency"), line.getkey("frequency") - sline.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : sline.getkey("name"),
                                        "uid"  : sline.getkey("uid"),
                                        "formula" : sline.getkey("formula"),
                                        "energies" : sline.getkey("energies"),
                                        "linestrength" : sline.getkey("linestrength"),
                                        "frequency" : sline.getkey("frequency"),
                                        "mass" : sline.getkey("mass"),
                                        "plain" : sline.getkey("plain"),
                                        "isocount" : sline.getkey("isocount"),
                                        "hfnum" : sline.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
                            elif (("Ukn" in sline.getkey("name") and "Ukn" not in line.getkey("name") and (lo or ro)) or (env  and (sline.getkey("transition") != line.getkey("transition") or sline.getkey("formula") != line.getkey("formula")))) and not sline.getkey("force"):
                                done = False
                                poffset = utils.freqtovel(line.getkey("frequency"), sline.getkey("frequency") - line.getkey("frequency"))
                                vel = poffset + self.vlsr
                                data = {"name" : line.getkey("name"),
                                        "uid"  : line.getkey("uid"),
                                        "formula" : line.getkey("formula"),
                                        "energies" : line.getkey("energies"),
                                        "linestrength" : line.getkey("linestrength"),
                                        "frequency" : line.getkey("frequency"),
                                        "mass" : line.getkey("mass"),
                                        "plain" : line.getkey("plain"),
                                        "isocount" : line.getkey("isocount"),
                                        "hfnum" : line.getkey("hfnum"),
                                        "peakoffset" : poffset,
                                        "velocity" : vel
                                       }
            loopcount += 1
        for i in range(len(self.statspec)):
            ulist = []
            mlist = []

            for v in peaks["stats"][i].linelist.values():
                v.setkey("peakrms", float(np.max(self.statspec[i].spec()[v.getstart():v.getend() + 1])))
                v.setkey("peakintensity", float(v.getkey("peakrms") * self.statspec[i].noise()))
                if "Ukn" in v.getkey("name"):
                    ulist.append(copy.deepcopy(v))
                else:
                    mlist.append(copy.deepcopy(v))
            # eliminate very close u lines
            for k in range(len(ulist) - 1, -1, -1):
                frq = ulist[k][1]
                tol = abs(self.tol * (self.statspec[k].freq()[ulist[k].getstart()] -
                                      self.statspec[k].freq()[ulist[k].getstart() + 1]))
                for j in range(k - 1, -1, -1):
                    if ulist[j].getkey("frequency") - tol < frq < ulist[j].getkey("frequency") + tol:
                        ulist[j].setkey("chans", [self.chan[self.chan.index(min(ulist[j].getstart(), ulist[k].getstart()))],
                                                  self.chan[self.chan.index(max(ulist[j].getend(), ulist[k].getend()))]])
                        ulist[j].setkey("freqs", [self.freq[self.chan.index(ulist[j].getstart())],
                                                  self.freq[self.chan.index(ulist[j].getend())]])
                        del ulist[i]
                        break
            # eliminate doubles
            for k in range(len(mlist) - 1, -1, -1):
                uid = mlist[k].getkey("uid")
                qn = mlist[k].getkey("transition")
                for j in range(k - 1, -1, -1):
                    if uid == mlist[j].getkey("uid") and qn == mlist[j].getkey("transition"):
                        mlist[j].setkey("chans", [self.chan[self.chan.index(min(mlist[j].getstart(), mlist[k].getstart()))],
                                                  self.chan[self.chan.index(max(mlist[j].getend(), mlist[k].getend()))]])
                        mlist[j].setkey("freqs", [self.freq[self.chan.index(mlist[j].getstart())],
                                                  self.freq[self.chan.index(mlist[j].getend())]])
                        del mlist[k]
                        break
            mlist += ulist

            xlabel = "%s Frequency (GHz)" % (t)
            mult = 1.
            if i == 1:
                mult = -1.
            myplot.makespec(x=self.statspec[i].freq(), y=self.statspec[i].spec(csub=False),
                            chan=self.statspec[i].chans(),
                            cutoff=(self.statspec[i].contin() + mult * (self.statspec[i].noise() *
                                                                        self.getkey("numsigma"))),
                            figname=imbase + "_statspec%i" % i, title="Line ID (vlsr=%.2f)" % self.vlsr,
                            xlabel=xlabel, lines=mlist, force=self.force,
                            blends=peaks["stats"][i].blends, continuum=self.statspec[i].contin(),
                            ylabel=label[i], thumbnail=True, references=line_ref)
            imname = myplot.getFigure(figno=myplot.figno, relative=True)

            thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)

            image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                          thumbnailtype=bt.PNG, description=caption[i])
            llbdp.image.addimage(image, "statspec%i" % i)
            self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname, thumbnailname,
                                          caption[i], self.infile])

        for i in range(len(peaks["specs"])):
            ulist = []
            mlist = []

            for v in peaks["specs"][i].linelist.values():
                v.setkey("peakintensity", float(np.max(self.specs[i].spec()[v.getstart():v.getend() + 1])))
                v.setkey("peakrms", float(v.getkey("peakintensity") / self.specs[i].noise()))

                if "Ukn" in v.getkey("name"):
                    ulist.append(copy.deepcopy(v))
                else:
                    mlist.append(copy.deepcopy(v))
            # eliminate very close u lines
            for i in range(len(ulist) - 1, -1, -1):
                frq = ulist[i][1]
                tol = abs(self.tol * (self.specs[i].freq()[ulist[i].getstart()] -
                                      self.specs[i].freq()[ulist[i].getstart() + 1]))
                for j in range(i - 1, -1, -1):
                    if ulist[j].getkey("frequency") - tol < frq < ulist[j].getkey("frequency") + tol:
                        ulist[j].setkey("chans", [min(ulist[j].getstart(), ulist[i].getstart()),
                                                  max(ulist[j].getend(), ulist[i].getend())])
                        ulist[j].setkey("freqs", [self.freq[self.chan.index(ulist[j].getstart())],
                                                  self.freq[self.chan.index(ulist[j].getend())]])
                        del ulist[i]
                        break
            # eliminate doubles
            for k in range(len(mlist) - 1, -1, -1):
                uid = mlist[k].getkey("uid")
                qn = mlist[k].getkey("transition")
                for j in range(k - 1, -1, -1):
                    if uid == mlist[j].getkey("uid") and qn == mlist[j].getkey("transition"):
                        mlist[j].setkey("chans", [min(mlist[j].getstart(), mlist[k].getstart()),
                                                  max(mlist[j].getend(), mlist[k].getend())])
                        mlist[j].setkey("freqs", [self.freq[self.chan.index(mlist[j].getstart())],
                                                  self.freq[self.chan.index(mlist[j].getend())]])
                        del mlist[k]
                        break

            mlist += ulist
            xlabel = "%s Frequency (GHz)" % (t)
            myplot.makespec(x=self.specs[i].freq(), y=self.specs[i].spec(csub=False),
                            chan=self.specs[i].chans(),
                            cutoff=self.specs[i].contin() + (self.specs[i].noise() *
                                                             self.getkey("numsigma")),
                            figname=imbase + "_spec%03d" % i,
                            title="Line ID (vlsr=%.2f)" % self.vlsr, xlabel=xlabel, lines=mlist,
                            force=self.force, blends=peaks["specs"][i].blends,
                            continuum=self.specs[i].contin(), thumbnail=True, references=line_ref)
            imname = myplot.getFigure(figno=myplot.figno, relative=True)
            thumbnailname = myplot.getThumbnail(figno=myplot.figno,
                                                relative=True)
            _caption = "Identified lines overlaid on input spectrum #%i." % (i)

            image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                          thumbnailtype=bt.PNG, description=_caption)
            llbdp.image.addimage(image, "spec%03d" % i)
            self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname, thumbnailname,
                                          _caption, self.infile])

        if self.pvspec is not None:
            ulist = []
            mlist = []
            for v in peaks["pvc"].linelist.values():
                v.setkey("peakintensity", float(np.max(self.pvspec.spec()[v.getstart():v.getend()+1])))
                v.setkey("peakrms", float(v.getkey("peakintensity") / self.pvspec.noise()))
                if "Ukn" in v.getkey("name"):
                    ulist.append(copy.deepcopy(v))
                else:
                    mlist.append(copy.deepcopy(v))
            # eliminate very close u lines
            for i in range(len(ulist) - 1, -1, -1):
                frq = ulist[i].getkey("frequency")
                tol = abs(self.tol * (self.pvspec.freq()[ulist[i].getstart()] -
                                      self.pvspec.freq()[ulist[i].getstart() + 1]))
                for j in range(i - 1, -1, -1):
                    if ulist[j].getkey("frequency") - tol < frq < ulist[j].getkey("frequency") + tol:
                        ulist[j].setkey("chans", [min(ulist[j].getstart(), ulist[i].getstart()),
                                                  max(ulist[j].getend(), ulist[i].getend())])
                        ulist[j].setkey("freqs", [self.freq[self.chan.index(ulist[j].getstart())],
                                                  self.freq[self.chan.index(ulist[j].getend())]])
                        del ulist[i]
                        break
            # eliminate doubles
            for i in range(len(mlist) - 1, -1, -1):
                uid = mlist[i].getkey("uid")
                qn = mlist[i].getkey("transition")
                for j in range(i - 1, -1, -1):
                    if uid == mlist[j].getkey("uid") and qn == mlist[j].getkey("transition"):
                        mlist[j].setkey("chans", [min(mlist[j].getstart(), mlist[i].getstart()),
                                                  max(mlist[j].getend(), mlist[i].getend())])
                        mlist[j].setkey("freqs", [self.freq[self.chan.index(mlist[j].getstart())],
                                                  self.freq[self.chan.index(mlist[j].getend())]])
                        del mlist[i]
                        break
            mlist += ulist


            xlabel = "%s Frequency (GHz)" % (t)
            myplot.makespec(x=self.pvspec.freq(), y=self.pvspec.spec(csub=False), chan=self.pvspec.chans(),
                            cutoff=self.pvspec.noise() * self.getkey("numsigma"),
                            figname=imbase + "_pvspec", title="Line ID (vlsr=%.2f)" % self.vlsr,
                            xlabel=xlabel, lines=mlist, force=self.force, blends=peaks["pvc"].blends,
                            continuum=[0.0] * len(self.pvspec), ylabel="Correlation",
                            thumbnail=True, references=line_ref)
            imname = myplot.getFigure(figno=myplot.figno, relative=True)
            thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)
            _caption = "Identified lines overlaid on correlation coefficient plot from PVCorr_BDP."

            image = Image(images={bt.SVG: imname}, thumbnail=thumbnailname,
                          thumbnailtype=bt.PNG, description=_caption)
            llbdp.image.addimage(image, "pvspec")
            self.spec_description.append([llbdp.ra, llbdp.dec, "", xlabel, imname, thumbnailname,
                                          _caption, self.infile])

        llist = []
        # merge the results into a single list
        for s in range(len(self.statspec)):
            keylist = peaks["stats"][s].linelist.keys()
            keylist.sort()
            for key in keylist:

                found = False
                for i in range(len(llist)):
                    if llist[i].getkey("frequency") == peaks["stats"][s].linelist[key].getkey("frequency") and \
                       llist[i].getkey("transition") == peaks["stats"][s].linelist[key].getkey("transition"):
                        tt = [llist[i].getstart(), llist[i].getend(),
                              peaks["stats"][s].linelist[key].getstart(),
                              peaks["stats"][s].linelist[key].getend()]
                        llist[i].setkey("chans", [self.chan[self.chan.index(min(tt))],
                                                  self.chan[self.chan.index(max(tt))]])
                        llist[i].setkey("freqs", [self.freq[self.chan.index(min(tt))],
                                                  self.freq[self.chan.index(max(tt))]])
                        found = True
                    elif (i != 0 and llist[i - 1].getkey("frequency") < peaks["stats"][s].linelist[key].getkey("frequency") < llist[i].getkey("frequency")) or \
                       (i == 0 and peaks["stats"][s].linelist[key].getkey("frequency") < llist[i].getkey("frequency")):
                        llist.insert(i, peaks["stats"][s].linelist[key])
                        found = True

                if not found:
                    llist.append(peaks["stats"][s].linelist[key])

            for item in peaks["stats"][s].blends:
                place = False
                for i in range(len(llist)):
                    if (i != 0 and llist[i-1].getkey("frequency") < item.getkey("frequency") < llist[i].getkey("frequency")) or \
                       (i == 0 and item.getkey("frequency") < llist[i].getkey("frequency")):

                        place = True
                        break
                if not place:
                    llist.append(item)
        for ps in peaks["specs"]:
            blendcheck = {}
            for freq, v in ps.linelist.iteritems():
                place = False
                for i in range(len(llist)):
                    if (v.getkey("frequency") == llist[i].getkey("frequency") and \
                        v.getkey("transition") == llist[i].getkey("transition")) or \
                       ("U" in v.getkey("uid") and v.getkey("uid") == llist[i].getkey("uid")):
                        place = True
                        llist[i].setkey("chans", [self.chan[self.chan.index(min(llist[i].getstart(), v.getstart()))],
                                                  self.chan[self.chan.index(max(llist[i].getend(), v.getend()))]])
                        llist[i].setkey("freqs", [self.freq[self.chan.index(llist[i].getstart())],
                                                  self.freq[self.chan.index(llist[i].getend())]])

                        if v.getkey("blend") > 0 and llist[i].getkey("blend") > 0:
                            blendcheck[v.getkey("blend")] = llist[i].getkey("blend")
                        elif v.getkey("blend") > 0:
                            llist[i].setkey("blend", v.getkey("blend"))

                    elif (i != 0 and llist[i - 1].getkey("frequency") < v.getkey("frequency") < llist[i].getkey("frequency")) or \
                       (i == 0 and v.getkey("frequency") < llist[i].getkey("frequency")):
                        llist.insert(i, v)
                        place = True
                if not place:
                    llist.append(v)
            # do the same for the blends, keep in mind the blendcheck
            for blend in ps.blends:
                place = False
                for i in range(len(llist)):
                    if (i != 0 and llist[i - 1].getkey("frequency") < blend.getkey("frequency") < llist[i].getkey("frequency")) or \
                         (i == 0 and blend.getkey("frequency") < llist[i].getkey("frequency")):
                        if blend.getkey("blend") in blendcheck:
                            blend.setkey("blend", blendcheck[blend.getkey("blend")])
                        llist.insert(i, blend)
                        place = True
                    # if it is already there then just drop it
                        break
                    if blend.getkey("frequency") == llist[i].getkey("frequency") and \
                       blend.getkey("transition") == llist[i].getkey("transition"):
                        if llist[i].getkey("blend") == 0:
                            mindx = -1
                            bqn = ""
                            frq = 0.0
                            bls = blend.getkey("linestrength")
                            for j in ps.linelist.keys():
                                if ps.linelist[j].getkey("blend") == blend.getkey("blend") and \
                                   ps.linelist[j].getkey("linestrength") > bls:
                                    bqn = ps.linelist[j].getkey("transition")
                                    frq = ps.linelist[j].getkey("frequency")
                                    bls = ps.linelist[j].getkey("linestrength")
                            for j in range(len(llist)):
                                if llist[j].getkey("transition") == bqn:# and llist[j].getkey("frequency") == frq:
                                    mindx = j
                                    break

                            if mindx >= 0:
                                if llist[i].getend() > 0:
                                    llist[mindx].setstart(self.chan[self.chan.index(min(llist[i].getstart(),
                                                                                        llist[mindx].getstart(),
                                                                                        blend.getstart()))])
                                    llist[mindx].setend(self.chan[self.chan.index(max(llist[i].getend(),
                                                                                      llist[mindx].getend(),
                                                                                      blend.getend()))])
                                    llist[mindx].setkey("freqs", [self.freq[self.chan.index(llist[mindx].getstart())],
                                                                  self.freq[self.chan.index(llist[mindx].getend())]])
                                llist[i].setkey("blend", llist[mindx].getkey("blend"))

                                temp = {"blend" : llist[mindx].getkey("blend"),
                                        "velocity" : 0.0,
                                        "peakintensity" : 0.0,
                                        "peakoffset" : 0.0,
                                        "fwhm" : 0.0,
                                        "peakrms" : 0.0}

                                llist[i].setkey(temp)
                        else:
                            mindx = -1
                            bqn = ""
                            bls = blend.getkey("linestrength")
                            # get the strongest one in the blend
                            for j in ps.linelist.keys():
                                if ps.linelist[j].getkey("blend") == blend.getkey("blend") and \
                                   ps.linelist[j].getkey("linestrength") > bls:
                                    bqn = ps.linelist[j].getkey("transition")
                                    bls = ps.linelist[j].getkey("linestrength")
                            for j in range(len(llist)):
                                if llist[j].getkey("transition") == bqn:
                                    mindx = j
                                    break
                            if mindx >= 0:
                                if llist[i].getend() > 0:
                                    llist[mindx].setstart(self.chan[self.chan.index(min(llist[i].getstart(),
                                                                                        llist[mindx].getstart()))])
                                    llist[mindx].setend(self.chan[self.chan.index(max(llist[i].getend(),
                                                                                      llist[mindx].getend()))])
                                    llist[mindx].setkey("freqs", [self.freq[self.chan.index(llist[mindx].getstart())],
                                                                  self.freq[self.chan.index(llist[mindx].getend())]])

                        place = True
                        break
                if not place:
                    if blend.getkey("blend") in blendcheck:
                        blend.setkey("blend", blendcheck[blend.getkey("blend")])

                    llist.append(blend)
        if peaks["pvc"] is not None:
            blendcheck = {}
            for freq, v in peaks["pvc"].linelist.iteritems():
                place = False
                for i in range(len(llist)):
                    if (v.getkey("frequency") == llist[i].getkey("frequency") and \
                        v.getkey("transition") == llist[i].getkey("transition")) or \
                       ("U" in v.getkey("uid") and v.getkey("uid") == llist[i].getkey("uid")):
                        place = True
                        llist[i].setkey("chans", [self.chan[self.chan.index(min(llist[i].getstart(), v.getstart()))],
                                                  self.chan[self.chan.index(max(llist[i].getend(), v.getend()))]])
                        llist[i].setkey("freqs", [self.freq[self.chan.index(llist[i].getstart())],
                                                  self.freq[self.chan.index(llist[i].getend())]])

                        if v.getkey("blend") > 0 and llist[i].getkey("blend") > 0:
                            blendcheck[v.getkey("blend")] = llist[i].getkey("blend")
                        elif v.getkey("blend") > 0:
                            llist[i].setkey("blend", v.getkey("blend"))
                    elif (i != 0 and llist[i-1].getkey("frequency") < v.getkey("frequency") < llist[i].getkey("frequency")) or \
                       (i == 0 and v.getkey("frequency") < llist[i].getkey("frequency")):
                        llist.insert(i, v)

                        place = True
                if not place:
                    llist.append(v)

            # do the same for the blends, keep in mind the blendcheck

            for blend in peaks["pvc"].blends:
                place = False
                for i in range(len(llist)):
                    if (i != 0 and llist[i - 1].getkey("frequency") < blend.getkey("frequency") < llist[i].getkey("frequency")) or \
                       (i == 0 and blend.getkey("frequency") < llist[i].getkey("frequency")):
                        if blend.getkey("blend") in blendcheck:
                            blend.setkey("blend", blendcheck[blend.getkey("blend")])
                        llist.insert(i, blend)

                        place = True
                    # if it is already there then just modify it if necessary
                    if blend.getkey("frequency") == llist[i].getkey("frequency") and \
                       blend.getkey("transition") == llist[i].getkey("transition"):
                        if llist[i].getkey("blend") == 0:
                            mindx = -1
                            bqn = ""
                            bls = blend.getkey("linestrength")
                            # get the strongest one in the blend
                            for j in peaks["pvc"].linelist.keys():
                                if peaks["pvc"].linelist[j].getkey("blend") == blend.getkey("blend") and \
                                   peaks["pvc"].linelist[j].getkey("linestrength") > bls:
                                    bqn = peaks["pvc"].linelist[j].getkey("transition")
                                    bls = peaks["pvc"].linelist[j].getkey("linestrength")
                            for j in range(len(llist)):
                                if llist[j].getkey("transition") == bqn:
                                    mindx = j
                                    break
                            if mindx >= 0:
                                if llist[i].getend() > 0:
                                    llist[mindx].setstart(self.chan[self.chan.index(min(llist[i].getstart(),
                                                                                        llist[mindx].getstart(),
                                                                                        blend.getstart()))])
                                    llist[mindx].setend(self.chan[self.chan.index(max(llist[i].getend(),
                                                                                      llist[mindx].getend(),
                                                                                      blend.getend()))])
                                    llist[mindx].setkey("freqs", [self.freq[self.chan.index(llist[mindx].getstart())],
                                                                  self.freq[self.chan.index(llist[mindx].getend())]])
                                llist[i].setkey("blend", llist[mindx].getkey("blend"))

                                temp = {"velocity" : 0.0,
                                        "peakintensity" : 0.0,
                                        "peakoffset" : 0.0,
                                        "fwhm" : 0.0,
                                        "peakrms" : 0.0}
                                temp["blend"] = llist[mindx].getkey("blend")
                                llist[i].setkey(temp)
                        else:
                            mindx = -1
                            bqn = ""
                            bls = blend.getkey("linestrength")
                            # get the strongest one in the blend
                            for j in peaks["pvc"].linelist.keys():
                                if peaks["pvc"].linelist[j].getkey("blend") == blend.getkey("blend") and \
                                   peaks["pvc"].linelist[j].getkey("linestrength") > bls:
                                    bqn = peaks["pvc"].linelist[j].getkey("transition")
                                    bls = peaks["pvc"].linelist[j].getkey("linestrength")
                            for j in range(len(llist)):
                                if llist[j].getkey("transition") == bqn:
                                    mindx = j
                                    break
                            if mindx >= 0:
                                if llist[i].getend() > 0:
                                    llist[mindx].setstart(self.chan[self.chan.index(min(llist[i].getstart(),
                                                                                        llist[mindx].getstart()))])
                                    llist[mindx].setend(self.chan[self.chan.index(max(llist[i].getend(),
                                                                                      llist[mindx].getend()))])
                                    llist[mindx].setkey("freqs", [self.freq[self.chan.index(llist[mindx].getstart())],
                                                                  self.freq[self.chan.index(llist[mindx].getend())]])
                                temp = {"velocity" : 0.0,
                                        "peakintensity" : 0.0,
                                        "peakoffset" : 0.0,
                                        "fwhm" : 0.0,
                                        "peakrms" : 0.0}
                                temp["blend"] = llist[mindx].getkey("blend")
                                llist[i].setkey(temp)

                        place = True

                if not place:
                    if blend.getkey("blend") in blendcheck:
                        blend.setkey("blend", blendcheck[blend.getkey("blend")])
                    llist.append(blend)
        ulist = []
        mlist = []
        for l in llist:
            if "Ukn" in l.getkey("name"):
                ulist.append(l)
            else:
                mlist.append(l)
        # eliminate very close u lines
        for i in range(len(ulist) - 1, -1, -1):
            frq = ulist[i].getkey("frequency")
            tol = abs(self.tol * (self.freq[ulist[i].getstart()] - self.freq[ulist[i].getstart() + 1]))
            for j in range(i - 1, -1, -1):
                if ulist[j].getkey("frequency") - tol < frq < ulist[j].getkey("frequency") + tol:
                    del ulist[i]
                    break

        mlist += ulist
        for frc in self.force:
            mlist.append(frc)
        #mlist[0]
        mlist.sort(key=lambda x: float(x.getkey("frequency")))
        duplicate_lines = []
        for m in mlist:
            addon = ""
            logging.log(logging.INFO, " Found line: " + m.getkey("formula") + " " + m.getkey("transition") +
                        " @ " + str(m.getkey("frequency")) + "GHz, channels " + str(m.getstart()) +
                        " - " + str(m.getend()) + addon)
            if m.getkey('uid') in duplicate_lines:
                logging.log(logging.WARNING, " Skipping duplicate UID: " + m.getkey("uid"))
                continue
            else:
                duplicate_lines.append(m.getkey('uid'))
            llbdp.addRow(m)
            logging.regression("LINEID: %s %.5f  %d %d" % (m.getkey("formula"), m.getkey("frequency"),
                                                           m.getstart(), m.getend()))
        # Need to adjust plot DPI = 72 for SVG; stick to PNG for now...
        myplot._plot_type = admit.util.PlotControl.PNG
        myplot._plot_mode = admit.util.PlotControl.NONE
        myplot.summaryspec(self.statspec, self.specs, self.pvspec, imbase + "_summary", llist, force=self.force)
        imname = myplot.getFigure(figno=myplot.figno, relative=True)
        thumbnailname = myplot.getThumbnail(figno=myplot.figno, relative=True)
        _caption = "Identified lines overlaid on Signal/Noise plot of all spectra."

        image = Image(images={bt.PNG: imname}, thumbnail=thumbnailname,
                      thumbnailtype=bt.PNG, description=_caption)

        llbdp.image.addimage(image, "summary")
        self.spec_description.append([llbdp.ra, llbdp.dec, "", "Signal/Noise", imname,
                                      thumbnailname, _caption, self.infile])

        # The plain ascii list may still be useful for regression testing

        self._summary["linelist"] = SummaryEntry(llbdp.table.serialize(), "LineID_AT",
                                                 self.id(True), taskargs)

        self._summary["spectra"] = [SummaryEntry(self.spec_description, "LineID_AT",
                                                 self.id(True), taskargs)]
        self.addoutput(llbdp)
        Peaks.reset()
        self.dt.tag("done")
        self.dt.end()

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           LineID_AT adds the following to ADMIT summary:

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


class Peaks(object):
    """ Lightweight class for working with the peaks found by one or more peak
        finding algorithms.

        Parameters
        ----------
        kwargs : dict
            A dictionary of keyword/value pairs of the parameters. Can contain
            any attribute. See Attributes below for a full listing of possible
            keywords and value types.

        Attributes
        ----------
        centers : dict

        fcenters : dict

        singles : list

        fsingles : list

        pairs : dict

        x : list
            Listing of the x axis (frequency) for the given peaks

        y : list
            Listing of the y axis (intensity) for the given peaks

        offsets : set
            Listing of all possible offset values, shared among all instances
            of Peaks.

        offsetdone : boolean
            Whether or not the offsets have been converted to frequency.
            Internal use only should not be set manually.
    """
    __slots__ = ["centers", "offsets", "singles", "pairs", "spec",
                 "offsetdone", "fcenters", "fsingles", "linelist",
                 "blends", "segments", "fsegments", "counts"]
    offsets = set()
    offsetdone = False

    def __init__(self, **kwargs):
        self.centers = {}
        self.fcenters = {}
        self.singles = []
        self.fsingles = []
        self.pairs = {}
        self.counts = {}
        self.linelist = {}
        self.blends = []
        self.spec = None
        #self.x = []
        #self.y = []
        self.segments = []
        self.fsegments = []
        #self.chans = []
        for kw, arg in kwargs.iteritems():
            setattr(self, kw, arg)

    def __str__(self):
        print "CENTERS", self.centers
        print "FCENTERS", self.fcenters
        print "SINGLES", self.singles
        print "FSINGLES", self.fsingles
        print "PAIRS", self.pairs
        print "LINELIST", self.linelist
        print "OFFSETS", self.offsets
        print "SEGMENTS", self.segments
        print "FSEGMENTS", self.fsegments
        return ""

    @staticmethod
    def reset():
        """ Method to reset the Peaks static member variables so that LineID
            can be re-run without polluting the results with items from previous
            runs.

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        Peaks.offsets = set()
        Peaks.offsetdone = False

    def __len__(self):
        if self.spec is None:
            return 0
        return len(self.spec)

    def removeidentified(self, data, tol):
        """ Method to remove already identified peaks.

            Parameters
            ----------
            data : Peaks instance
                A Peaks instance to use as the base for removal

            tol : float
                The tolerance to allow (in GHz) for comparable lines

            Returns
            -------
            None

        """
        remove = set()
        for center in self.fcenters:
            for freq, v in data.linelist.iteritems():
                if center - tol / 2.0 < freq < center + tol / 2.0:
                    remove.add(center)
                    self.linelist[center] = v
        for rem in remove:
            del self.fcenters[rem]
        remove = set()
        for single in self.fsingles:
            for freq, v in data.linelist.iteritems():
                if single - tol / 2.0 < freq < single + tol / 2.0:
                    remove.add(single)
                    self.linelist[single] = v
        for rem in remove:
            self.fsingles.remove(rem)

    def flatten(self, tol):
        """ Method to collapse pair peaks that are close together into single
            pair

            Parameters
            ----------
            tol : float
                The tolerance (minimum distance between points)

            Returns
            -------
            List containing the consolidated points

        """
        mpattern = []

        p1 = copy.deepcopy(self.pairs)
        for o in self.pairs.keys():
            isnew = True
            for pattern in mpattern:
                if pattern - tol / 2.0 < o < pattern + tol / 2.0:
                    isnew = False
                    p1[pattern] += p1.pop(o)
            if isnew:
                mpattern.append(o)
        self.pairs = p1
        return mpattern

    def getchan(self, frq):
        """ Method to get the channel number given the frequency

            Parameters
            ----------
            frq : float
                The frequency whose channel number is to be found

            Returns
            -------
            int containing the channel number, will be 0 or len(self.x)-1 if
            the frequency is outside of the frequency range in the class

        """
        return self.spec.getchan(frq)

    def getchans(self, masked=True):
        """ Method to get the entire channel axis

            Parameters
            ----------
            masked : bool
                If True return a masked array with "bad" channels masked,
                else return a numpy array

            Returns
            -------
            array like containing the channel axis

        """
        return self.spec.chans(masked)

    def getspecs(self, masked=True):
        """ Method to get the entire spectral axis

            Parameters
            ----------
            masked : bool
                If True return a masked array with "bad" channels masked,
                else return a numpy array

            Returns
            -------
            array like containing the spectral axis

        """
        return self.spec.spec(masked)

    def getfreqs(self, masked=True):
        """ Method to get the entire frequency axis

            Parameters
            ----------
            masked : bool
                If True return a masked array with "bad" channels masked,
                else return a numpy array

            Returns
            -------
            array like containing the frequency axis

        """
        return self.spec.freq(masked)

    def getsegment(self, chan):
        """ Method to get the segment that contains the given channel

            Parameters
            ----------
            chan : int
                The channel number to find the segment for

            Returns
            -------
            Two element List containing the starting and ending channels
            for the segment containing the given channel
        """
        for seg in self.segments:
            if seg[0] <= chan <= seg[1]:
                return seg
        return [None, None]

    def getfsegment(self, freq):
        """ Method to return the segment which contains the given frequency.

            Parameters
            ----------
            freq : float
                The frequency for which the segment is requested

            Returns
            -------
            List containing the segment end points, or [None, None] if the frequency is not in a
            segment.

        """
        seg = self.getsegment(self.getchan(freq))
        fseg = [self.getfreq(seg[0]), self.getfreq(seg[1])]
        fseg.sort()
        return fseg

    def sort(self):
        """ Method to sort through all pairs and organize them into dictionary
            entries indexed by their common separation

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        listing = sorted(self.pairs)
        for diff in listing:
            points = self.pairsort(self.pairs[diff])
            for indx, item in enumerate(points):
                p1, p2 = item
                # search for p2 as a p1 in any other set
                # ignore p1 as it will have been caught in an earlier iteration
                found = False
                for indx2, item2 in enumerate(points, start=indx):
                    if p2 == item2[0] and not p2 in self.centers:
                        found = True
                        self.centers[p2] = (True, [p1, item2[1]])
                        Peaks.offsets.add(diff)
                        break
                if not found and not p2 in self.centers:
                    self.centers[(p2 + p1) / 2.0] = (False, [p1, p2])
                    Peaks.offsets.add(diff / 2.0)

    def pairsort(self, pairs):
        """ Method to sort a list of pairs into ascending order

            Parameters
            ----------
            pairs : list
                List of pairs (as lists) to be sorted

            Returns
            -------
            A list of the sorted pairs

        """
        for p in pairs:
            p.sort()
        pairs.sort()
        return pairs

    def patternsort(self, pattern):
        """ Method to sort a detected patterns into sorted lists

            Parameters
            ----------
            pattern : dict
                Dictionary of the patterns to sort

            Returns
            -------
            Dictionary of sorted patterns

        """
        retpattern = {"stats" : {},
                      "specs" : {}}
        stat = pattern["stats"]
        for freq, wings in stat.iteritems():
            stat[freq] = self.pairsort(wings)
        retpattern["stats"] = stat
        spec = pattern["specs"]
        for freq, wings in spec.iteritems():
            spec[freq] = self.pairsort(wings)
        retpattern["specs"] = spec
        return retpattern

    def getfreq(self, chan):
        """ Method to get the frequency of the given channel, the channel can
            contain a fraction of a channel (e.g. 1.45)

            Parameters
            ----------
            chan : float
                The channel to convert

            Returns
            -------
            Float of the frequency corresponding to the channel

        """
        return self.spec.getfreq(chan)

    def converttofreq(self):
        """ Method to convert the peak and pattern locations from channel to
            frequency indexing

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        if not Peaks.offsetdone:
            tf1 = self.spec.freq()[1:]
            tf2 = self.spec.freq()[:-1]
            avgdif = np.mean(tf1 - tf2)
            ts = set()
            for offset in Peaks.offsets:
                ts.add(offset * avgdif)
            Peaks.offsets = ts
            Peaks.offsetdone = True
        if len(self.fsegments) == 0:
            for seg in self.segments:
                fseg = [self.getfreq(seg[0]), self.getfreq(seg[1])]
                self.fsegments.append([min(fseg), max(fseg)])
        for single in self.singles:
            self.fsingles.append(self.getfreq(single))

        for wings in self.centers.values():
            v1 = [self.getfreq(wings[1][0]), self.getfreq(wings[1][1])]
            v1.sort()
            self.fcenters[self.getfreq(abs(wings[1][0] + wings[1][1]) / 2.0)] = \
                (wings[0], v1)

    def validatelinesegments(self):
        """ Method to ensure that all line channel ranges do not go past the
            bounds of the original segments.

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        drop = []
        for f, line in self.linelist.iteritems():
            low = line.getstart()
            hi = line.getend()
            flow = False
            fhigh = False
            for seg in self.segments:
                if not flow and seg[0] <= low <= seg[1]:
                    flow = True
                if not fhigh and seg[0] <= hi <= seg[1]:
                    fhigh = True
            if fhigh and flow:
                continue
            if not fhigh and not flow:
                found = False
                for seg in self.segments:
                    if low <= seg[0] <= hi:
                        found = True
                        break
                if not found:
                    drop.append(f)
                    continue
            if not fhigh:
                distance = 1000000.
                current = -1
                # find the closest that is less than
                for i in range(len(self.segments)):
                    dist = hi - self.segments[i][1]
                    if 0 < dist < distance:
                        distance = dist
                        current = i
                if current >= 0:
                    self.linelist[f].setend(self.spec.chans()[self.spec.getchanindex(self.segments[current][1])])
                    self.linelist[f].setfend(max(self.spec.getfreq(self.linelist[f].getend()),
                                                 self.spec.getfreq(self.linelist[f].getstart())))
            if not flow:
                distance = 1000000.
                current = -1
                # find the closest that is less than
                for i in range(len(self.segments)):
                    dist = self.segments[i][0] - low
                    if 0 < dist < distance:
                        distance = dist
                        current = i
                if current >= 0:
                    self.linelist[f].setstart(self.spec.chans()[self.spec.getchanindex(self.segments[current][0])])
                    self.linelist[f].setfstart(min(self.spec.getfreq(self.linelist[f].getend()),
                                                   self.spec.getfreq(self.linelist[f].getstart())))

        for f in drop:
            del self.linelist[f]

    def centerfreq(self):
        """ Method to get the center frequency of the spectrum

            Parameters
            ----------
            None

            Returns
            -------
            Float containing the center frequency of the spectrum

        """
        return self.spec.centerfreq()

    def limitwidth(self, center, width):
        """ Method to ensure that the given peak and line width fit within its segment

            Parameters
            ----------
            center : float
                The center frequency in GHz

            width : float
                The half width of the line in GHz

            Returns
            -------
            Two element List containing the start and end frequencies, limited by the
            segment boundaries

        """
        for seg in self.fsegments:
            if seg[0] <= center <= seg[1]:
                return [max(seg[0], center - width), min(seg[1], center + width)]
