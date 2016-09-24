import admit.util.Spectrum as Spectrum
import admit.util.utils as utils
import os
import numpy as np
import random
from admit.util.segmentfinder import SegmentFinder
import math
import admit.util.filter.Filter1D as Filter1D
import copy
import matplotlib.pyplot as plt
import matplotlib
import time

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
                    p1[pattern] = p1.pop(o)
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
                        #print "DIFF ", diff
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
            #print "TF ", tf1, tf2
            ts = set()
            for offset in Peaks.offsets:
                #print "VEL ", utils.freqtovel(tf1[0], avgdif*offset)
                ts.add(offset * avgdif)
            Peaks.offsets = ts
            Peaks.offsetdone = True
        if len(self.fsegments) == 0:
            for seg in self.segments:
                fseg = [self.getfreq(seg[0]), self.getfreq(seg[1])]
                self.fsegments.append([min(fseg), max(fseg)])
        for single in self.singles:
            #print "\n\nSINGLE",single,self.getfreq(single),"\n\n"
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


def getpeaks(method, args, spec, segments, iterate=False):
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
        if abs(s[0] - s[1]) > 6:
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
        while (args["min_width"] >= 1 and iterate) or (args["min_width"] > 0 and not iterate):
            pf = utils.getClass("util.peakfinder", method, args)
            pk = pf.find() + float(max(s[0] - 2, 0))
            for p in pk:
                if s[0] <= p <= s[1]:
                    temppks.append(p)
            if not iterate:
                break
            args["min_width"] -= 1
            if args["min_width"] == 0:
                break
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


def findpatterns(spec, points, segments):
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
    #self.dt.tag("START PATTERN")
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
    #self.dt.tag("P0")

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            diffs[i, j] = abs(points[i] - points[j])
    #self.dt.tag("P1")
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
                    #print i, j, k, l
                    # compare to all other points, skipping itself
                    if (k == i and l == j) or diffs[k, l] < 3.0 / 3.0 \
                       or abs(spec.spec()[points[k]]) > 2.0 * abs(spec.spec()[points[l]])\
                       or abs(spec.spec()[points[l]]) > 2.0 * abs(spec.spec()[points[k]]):
                        continue
                    # if the distances from two pairs of points are close enough
                    # add it to the list of clusters
                    if maxsep > diffs[k, l] > 0.0 and (diff - 3.0 / 3.0 < diffs[k, l] < diff + 3.0 / 3.0):
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
    #self.dt.tag("P2")
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
    remove = []
    newcounts = {}
    counts = set()
    for k, v in clusters.iteritems():
        #newcounts[k] = len(v)
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

    peaks.singles = singles
    peaks.pairs = clusters
    peaks.counts = newcounts
    return peaks

def plot(x, res, nruns):
    f = plt.figure(figsize=(21,14))

    ax = f.add_subplot(111)
    keys = res.keys()
    keys.sort()
    for k in keys:
        ax.plot(x,res[k],label='%s chans' % (str(k)),linewidth=2)
        ax.scatter(x,res[k],s=15)

    ax.set_ylim([-1, nruns + 1])
    ax.set_xlim([0,110])
    for i in x:
        ax.plot([i,i],[0,100], 'r-')
    ax.set_xlabel("Number of Lines")
    ax.grid(True)
    ax.set_ylabel("Number of False Patterns (per %i runs)" % (nruns))
    matplotlib.rcParams.update({'font.size': 22})
    gridlines = ax.get_ygridlines()

    for i in gridlines:
        i.set_linestyle('--')
    gridlines = ax.get_xgridlines()

    for i in gridlines:
        i.set_linestyle('')
    ax.legend(loc="lower right")
    plt.show()

def run(nchan, lwidth, inten):
    """ Method to generate spectra and inject Gaussians

        Parameters
        ----------
        nchan : int
            Number of channels in the generated spectrum

        lwidth : float
            Width of the generated Gaussians in km/s

        inten : float
            The nominal peak intensity of the Gaussians
    """
    # set up the dict to collect the results, key is the number of Gaussians to inject
    pats = {5: None, 10: None, 15:None, 20:None, 25:None, 30:None, 40:None, 50:None, 60:None, 70:None, 80:None, 90:None, 100:None}
    nl = pats.keys()
    nl.sort()
    # for each of the number of Gaussians
    for nlines in nl:
        print "    ",nlines
        # generate frequency axis
        rms = 1.0
        freq = np.arange(nchan, dtype=np.float64)
        center = int(nchan/2)
        for i in range(nchan):
            freq[i] = 100.0 + (float((i - nchan/2)) * 0.0001)
        # generate spectral and channel axes
        spec = np.zeros(nchan)
        chans = np.arange(nchan)
        # generate noise
        spec += np.random.normal(0.0, rms, nchan)
        # inject Gaussians
        for i in range(nlines):
            # randomly determine the peak position in channel space
            peak = int(random.random() * nchan)
            spec += utils.gaussian1D(freq, inten, freq[peak] + (random.random()/20), utils.veltofreq(lwidth, freq[peak]))
        # convert to Spectrum object
        spectrum = Spectrum(spec, freq, chans)
        # find the segments
        sfinder = SegmentFinder.SegmentFinder(spectrum=spectrum.spec(),
                                              freq=spectrum.freq(),
                                              method="ADMIT",
                                              minchan=3,
                                              maxgap=3,
                                              numsigma=4.0,
                                              iterate=True, nomean=True)

        seg, cut, noi, mean = sfinder.find()
        spectrum.set_noise(noi)
        # find the peaks
        args = {"spec"      : spectrum.spec(),
                "y"         : spectrum.freq(),
                "min_width" : 3}
        args["thresh"] = float(spectrum.noise() * 4.0)
        pks = getpeaks("PeakFinder", args, spectrum.spec(), seg, iterate=True)
        # find any patterns
        pats[nlines] = findpatterns(spectrum, pks, seg)
    return pats

def generate(lwidth=1.5, peak=8.0, seed=45, seed2=65, nruns=100):
    """ Main method to run the simulations

        Parameters
        ----------
        lwidth : float
            Width of the lines in km/s
            Default: 1.5

        peak : float
            Nominal peak intensity of the lines in sigma units
            Default: 8.0

        seed : int
            Seed for random number generator
            Default: 45

        seed2 : int
            Seed for numpy random number generator
            Default: 65

        nruns : int
            Number of runs to perform for each channel range
            Default: 100

    """
    random.seed(seed)
    np.random.seed(seed2)
    # dict to store the results, key is the number of channels in the spectra
    chans = {500: None, 1000: None, 2000: None, 4000: None, 8000: None}
    ch = chans.keys()
    ch.sort()
    # loop over each number of channels
    for nchan in ch:
        print "Running %i channels" % nchan
        res = {5: 0, 10: 0, 15:0, 20:0, 25:0, 30:0, 40:0, 50:0, 60:0, 70:0, 80:0, 90:0, 100:0}
        # loop over for the number of requested runs
        for i in range(nruns):
            print "  Run: ",i
            p = run(nchan, lwidth, peak)
            # if at least one pattern was found the increment the counter
            for n in res.keys():
                if len(p[n].pairs) > 0:
                    res[n] += 1
        ke = res.keys()
        ke.sort()
        y = []
        for i in ke:
            y.append(res[i])

        chans[nchan] = y
    # plot the results
    plot(ke, chans, nruns)
