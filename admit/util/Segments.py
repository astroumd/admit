""" .. _Segments-api:

    **Segments** --- Manages groups of line segments.
    -------------------------------------------------

    This module defines the Segments class.
"""
# system imports
import numpy as np
import copy

# ADMIT imports
from admit.util.AdmitLogging import AdmitLogging as logging


class Segments(object):
    """ Class to hold segments and convert them between different types.

        Segments are defined by a beginning and ending channel (both
        inclusive). ADMIT gives special meaning to a segment, for example a
        line can be found within that segment, or a continuum has to be fitted
        in that segment (or group of segments).

        Parameters
        ----------
        st : array like
            Array like object containing either the full segment list (array of
            two element arrays containing the start and end channel numbers for
            each segment), or an array of starting channel numbers.
            Default: None.

        en : array like
            An array of the ending channel number corresponding to the starting
            channel numbers given in st. Leave as None if st contains the full
            listing.
            Default: None.

        nchan : int
            The number of channels in the spectrum that the segments refer to.
            This is used to construct the bit mask for tracking all segments.
            If left as None, no bitmask will be made.
            Default: None.

        startchan : int
            The starting channel number of the spectrum that the segments refer
            to. Must be >= 0.
            Default: 0.

    """
    def __init__(self, st=None, en=None, nchan=None, startchan=0):
        # initialize everything
        self._segments = []
        self._nchan = nchan
        # error chack the starting channel number
        self._startchan = int(startchan)
        if self._startchan < 0:
            raise Exception("Start channel must be 0 or greater.")
        # if nchan was specified create the bitmask
        if nchan:
            self._chans = np.array([0] * nchan)
            # determine the maxchan
            self._maxchan = nchan - 1 + self._startchan
        else:
            self._chans = None
            self._maxchan = 0
        if st is None:
            return
        if type(st) != type(en) and en is not None:
            raise Exception("Channel start and end points must be the same type.")
        # build the list of segments
        # if en is not given
        peak = 0
        if en is None:
            # st must be array like
            if not hasattr(st, '__iter__'):
                raise Exception("A list must be given for parameter st.")
            for seg in st:
                # each one must have length of 2
                if len(seg) != 2:
                    raise Exception("Each segment must have a size of 2.")
                # make sure they are in the right order
                tempseg = [int(seg[0]), int(seg[1])]
                tempseg.sort()
                peak = max(peak, tempseg[1])
                self._segments.append(tempseg)
        else:
            # if both en and st are given and are ints
            if not hasattr(st, '__iter__'):
                tempseg = [int(st), int(en)]
                tempseg.sort()
                peak = max(peak, tempseg[1])
                self._segments.append(tempseg)
            else:
                # if both en ans st are given and both array like
                # create iterators
                stit = iter(st)
                enit = iter(en)
                if len(st) != len(en):
                    logging.warning("Starting and ending channel ranges do not have the same length, truncating the longer.")
                # iterate through the lists
                while True:
                    try:
                        tempseg = [int(stit.next()), int(enit.next())]
                        tempseg.sort()
                        peak = max(peak, tempseg[1])
                        self._segments.append(tempseg)
                    except StopIteration:
                        break
        if self._chans is None:
            self._chans = np.array([0] * (peak + 1))
            # determine the maxchan
            self._maxchan = peak + self._startchan

        # build the bit mask
        for seg in self._segments:
            if seg[1] > self._maxchan or seg[0] < self._startchan:
                raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                                (seg, self._startchan, self._maxchan))
            self._chans[seg[0] - self._startchan: seg[1] - self._startchan + 1] = 1

    def __len__(self):
        """ Returns the number of segments

            Parameters
            ----------
            None

            Returns
            -------
            int containing the number of segments in the class

        """
        return len(self._segments)

    def __iter__(self):
        """ Rurns an iterator to the list of segments

            Parameters
            ----------
            None

            Returns
            -------
            Iterator to the list of segments

        """
        return iter(self._segments)

    def __getitem__(self, index):
        """ Returns the segment at the given index

            Parameters
            ----------
            index : int
                The index of the segment to return

            Returns
            -------
            Two element list (segment) of the starting and ending channel numbers

        """
        if index >= len(self._segments):
            raise Exception("Index %i is beyond the range of indices (%i)" % (index, len(self._segments)))
        return self._segments[index]

    def __add__(self, other):
        """ Method to add two Segments classes together, without merging he semgents. The bitmask
            is recalculated.

            Parameters
            ----------
            other : Segments class instance or array like
                If a Segments instance is given then the internal segments are added to the current
                segment list. If an array is given then the items of the array are added to the
                current segment list.

            Returns
            -------
            The instance of this class with the new segments incorporated
        """
        new = copy.deepcopy(self)
        if type(other) == type(new):
            if new._startchan != other._startchan:
                raise Exception("Starting channels do not match.")
            if len(new._chans) != len(other._chans):
                raise Exception("Number of channels do not match.")
            for seg in other:
                new._segments.append(seg)
            new.recalcmask()
        elif hasattr(other, "__iter__"):
            for seg in other:
                tempseg = [int(seg[0]), int(seg[1])]
                if tempseg[1] > new._maxchan or tempseg[0] < new._startchan:
                    raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                                    (seg, self._startchan, self._maxchan))
                new._segments.append(tempseg)
            new.recalcmask()
        return new

    def __setitem__(self, index, item):
        """ Method to set the segment at index to a new value

            Parameters
            ----------

            index : int
                The location in the segment array to replace

            item : two element array
                The new segment to replace the indicated one with

            Returns
            -------
            None
        """
        if not hasattr(item, "__iter__"):
            raise Exception("Segments must be ginven as an iteratable object (list, np.array, etc.")
        if len(item) != 2:
            raise Exception("Segments must have length 2.")
        tempseg = [int(item[0]), int(item[1])]
        tempseg.sort()
        if tempseg[1] > self._maxchan or tempseg[0] < self._startchan:
            raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                            (tempseg, self._startchan, self._maxchan))
        self._segments[index] = tempseg
        self._chans[tempseg[0] - self._startchan: tempseg[1] - self._startchan + 1] = 1

    def __contains__(self, chan):
        """ Method to determine if a given channel is in a segment. This requires the bit mask to
            be available

            Parameters
            ----------
            chan : int
                The channel number to test

            Returns
            -------
            bool, True if the channel is in a segment, False otherwise

        """
        if self._chans is None:
            raise Exception("No bitmask has been built, call setnchan to build it.")
        return bool(self._chans[chan - self._startchan])

    def append(self, item):
        """ Method to append a new segment to the current list

            Parameters
            ----------
            item : two element array
                The new segment to append to the list

            Returns
            -------
            None

        """
        if not hasattr(item, '__iter__'):
            raise Exception("Segments must be ginven as an iteratable object (list, np.array, etc.")
        else:
            if len(item) != 2:
                raise Exception("Segments must have length 2.")
            tempseg = [int(item[0]), int(item[1])]
            tempseg.sort()
            if tempseg[0] < self._startchan or tempseg[1] > self._maxchan:
                raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                                (tempseg, self._startchan, self._maxchan))
            self._segments.append(tempseg)
            self._chans[tempseg[0] - self._startchan: tempseg[1] - self._startchan + 1] = 1

    def getmask(self):
        """ Method to return the current bitmask

            Parameters
            ----------
            None

            Returns
            -------
            Array like object containing the bit current bit mask, 1 = in segment, 0 = not in segment

        """
        return self._chans

    def getchannels(self, invert=False):
        """ Method to return the current list of channel numbers in the bitmask

            Parameters
            ----------
            invert : boolean
                Return the list of channels outside the bitmask instead

            Returns
            -------
            Array like object containing the (zero based) channel numbers that are in the segments

        """
        if invert:
            return (np.where(self._chans == 0)[0] + self._startchan).tolist()
        else:
            return (np.where(self._chans == 1)[0] + self._startchan).tolist()

    def remove(self, index):
        """ Method to remove a segment from the segment list

            Parameters
            ----------
            index : int
                The location of the segment to remove

            Returns
            -------
            None

        """
        del self._segments[index]
        self.recalcmask()

    def pop(self):
        """ Method to pop, or remove and return, the last segment in the list

            Parameters
            ----------
            None

            Returns
            -------
            Array like 2 element list of the segment starting and ending channels of the last
            segment in the list

        """
        seg = self._segments.pop()
        self.recalcmask()
        return seg

    def limits(self):
        """ Method to return the channel range of the internal channel bit mask

            Parameters
            ----------
            None

            Returns
            -------
            Array like 2 element list of the segment starting and ending channels
        """
        return [self._startchan, self._maxchan]

    def recalcmask(self, test=False):
        """ Method to recalculate the bit mask based on the current segment list. 1 = in segment
            0 = not in segment

            Parameters
            ----------
            test : bool
                If True then test each segment to be sure it is in the current allowed channel range.
                If False the do not test.

            Returns
            -------
            None
        """
        self._chans = np.array([0] * (self._maxchan + 1 - self._startchan))
        for seg in self._segments:
            if test and (seg[0] < self._startchan or seg[1] >= self._maxchan):
                raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                                (seg, self._startchan, self._maxchan))
            self._chans[seg[0] - self._startchan: seg[1] - self._startchan + 1] = 1

    def setnchan(self, nchan):
        """ Method to set the number of channels in the internal channel bit mask

            Parameters
            ----------
            nchan : int
                The number of channels in the bit mask

            Returns
            -------
            None

        """
        if nchan - 1 == self._nchan:
            return
        self._nchan = nchan
        self._maxchan = self._startchan + nchan - 1
        self.recalcmask(True)

    def getnchan(self):
        """ Method to return the number of channels in the current bit mask

            Parameters
            ----------
            None

            Returns
            -------
            int giving the number of channels

        """
        return self._maxchan - self._startchan + 1

    def setstartchan(self, chan):
        """ Method to set the starting channels number for the internal bit mask

            Parameters
            ----------
            chan : int
                The starting channel number

            Returns
            -------
            None

        """
        if chan == self._startchan:
            return
        self._startchan = chan
        self._maxchan = self._startchan + self._nchan - 1
        self.recalcmask(True)

    def getstartchan(self):
        """ Method to get the starting channel number of the current bit mask

            Parameters
            ----------
            None

            Returns
            -------
            int containing the starting channel number

        """
        return self._startchan

    def chans(self, invert=False):
        """ Method to convert the bit mask into a string of channel ranges in CASA format. e.g.
            [3,10],[25,50] => "3~10;25~50"

            Parameters
            ----------
            None

            Returns
            -------
            string containing the formatted channel ranges

        """
        output = ""
        if invert:
            basechan = np.append(1-self._chans, 0)
            shiftchan = np.insert(1-self._chans, 0, 0)
        else:
            basechan = np.append(self._chans, 0)
            shiftchan = np.insert(self._chans, 0, 0)
        diff = basechan - shiftchan
        st = np.where(diff == 1)[0]
        en = np.where(diff == -1)[0]
        first = True
        for seg in zip(st, en):
            if not first:
                output += ";"
            else:
                first = False
            output += str(seg[0] + self._startchan) + "~" + str(seg[1] - 1 + self._startchan)
        return output

    def merge(self, other=None):
        """ Method to merge overlapping segments into one segment. This operates on the current
            instance or takes a second instance or list of segments as input.

            Parameters
            ----------
            other : Segments instance or list of segments
                If given then these segments are added to the current list and then merged, to give
                a single list of non-overlapping segments.

            Returns
            -------
            None

        """
        if other is None:
            basechan = np.append(self._chans, 0)
            shiftchan = np.insert(self._chans, 0, 0)
            diff = basechan - shiftchan
            st = np.where(diff == 1)[0]
            en = np.where(diff == -1)[0]
            tempchans = []
            for seg in zip(st, en):
                tempchans.append([seg[0], seg[1]])
            self._segments = tempchans
            self.recalcmask()
        elif type(other) == type(self):
            if self._startchan != other._startchan:
                raise "Starting channel numbers do not match."
            if len(self._chans) != len(other._chans):
                raise "Number of channels do not match."
            for seg in other:
                self._segments.append(seg)
                self.recalcmask()
                self.merge()
        elif hasattr(other, "__iter__"):
            for seg in other:
                tempseg = [int(seg[0]), int(seg[1])]
                if tempseg[1] > self._maxchan or tempseg[0] < self._startchan:
                    raise Exception("All or part of a segment is beyond the given spectrum. Segment: %s, bounds: [%i, %i]" %
                                    (seg, self._startchan, self._maxchan))
                self._segments.append(tempseg)
            self.recalcmask()
            self.merge()
        else:
            raise Exception("Improper data type given as input. It must be an iteratable (list, np.array, etc.) or Segments object.")

    def getsegments(self):
        """ Method to get the list of segments

            Parameters
            ----------
            None

            Returns
            -------
            list of the segment end points [start, end]

        """
        return self._segments

    def getsegmentsaslists(self):
        """ Method to get the list of segments

            Parameters
            ----------
            None

            Returns
            -------
            list of the segment end points [start, end]

        """
        return self._segments

    def getsegmentsastuples(self):
        """ Method to get the list of segments as tuples

            Parameters
            ----------
            None

            Returns
            -------
            list of the segment end points as tuples (start, end)

        """
        out = []
        for seg in self._segments:
            out.append(tuple(seg))
        return out
