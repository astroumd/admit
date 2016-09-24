"""
  **specutil** --- Module for low-level manipulation of spectral line data.
  -------------------------------------------------------------------------

  This module defines methods used in processing spectral line data.
"""
import numpy as np
import numpy.ma as ma
from Spectrum import Spectrum
import filter.Filter1D as Filter1D
import bdp_types as bt
import utils
from segmentfinder import SegmentFinder
import continuumsubtraction.spectral.ContinuumSubtraction
from admit.util import LineData
import copy

def mergestats(s1, s2, noise):
    """ Method to merge two stats "spectra" into one. Specifically it
        is intended to merge the min and max columns from CubeStats by
        taking the maximum of max and abs(min).
        Giving sensitivity to any absorption lines.

        Parameters
        ----------
        s1 : numpy array
            The "max" array from CubeStats

        s2 : nump array
            The "min" array from CubeStats

        noise : numpy array
            The channel based rms noise

        Returns
        -------
        numpy array containing the merged spectra
    """
    # create the empty spectrum
    fullspec = np.zeros(len(s1))
    # make a sigma spectrum of both inputs
    ts1 = copy.deepcopy(s1) / noise
    # change the negative one to positive
    ts2 = copy.deepcopy(s2) / noise
    # merge the two sigma based spectra
    # prefer s1, but replace it if s2 is larger than s1
    for i in range(len(s1)):
        if ts2[i] > ts1[i]:
            fullspec[i] = s2[i]
        else:
            fullspec[i] = s1[i]
    return fullspec

def getspectrum(bdp, vlsr=0.0, smooth=(), recalc=False, segment={"method": "ADMIT",
                                                                 "minchan":5, "maxgap":3, "numsigma":2.0,
                                                                 "iterate":True, "nomean":True}):
    """ Method to convert an input BDP into a list based spectrum.
        The spectrum will be smoothed if requested by the input
        parameters.

        Parameters
        ----------
        bdp : BDP
            The input BDP, currently either a CubeSpectrum or CubeStats only.

        vlsr : float
            The velocity of the source.
            Default: 0.0

        smooth : tuple
            If smoothing is to be done...

        recalc : bool
            True if the noise is to be recalculted from smoothed spectra
            Default: False

        Returns
        -------
        A series of numpy arrays describing the spectrum.
        (freq, chans, spectrum)
    """
    # if the input bdp is a cubestats then we get both the max and the min
    # value arrays, this make the AT sensitive to both emission and
    # absorption lines
    multi = False
    # PJT: bit awkward, previously we needed just a boolean stat,
    #      now I've used two, but this doesn't scale well. Why not an enumerated type.
    pvcorr = False
    stat = False
    if bdp._type == bt.CUBESTATS_BDP:
        stat = True
        # get the per channel noise
        tempsi = ma.array(bdp.table.getColumnByName("sigma", typ=np.float64), fill_value=0.0)
        # get the peak values
        mspectrum = ma.array(bdp.table.getFullColumnByName("max", typ=np.float64) / tempsi, fill_value=0.0)
        # get the minimum values
        nspectrum = ma.array(abs(bdp.table.getFullColumnByName("min", typ=np.float64)) / tempsi, fill_value=0.0)
        avgnoise = np.average(tempsi)

        # merge the peak/minimum into one spectrum
        #spectrum = mergestats(mspectrum, nspectrum, tempsi)
        mspectrum = ma.masked_equal(mspectrum, 0.0)
        nspectrum = ma.masked_equal(nspectrum, 0.0)

        # get the frequency for each channel
        freq = bdp.table.getColumnByName("frequency", typ=np.float64)
        # get the channel number for each channel
        chans = bdp.table.getColumnByName("channel", typ=np.float64)
        # convert the spectrum to a peak/noise (i.e. sigma) valued spectrum
        #spectrum /= tempsi
        # doppler shift the input spectra, which are in sky frequency, to the proper
        # source rest frame
        freq = utils.undoppler(freq, vlsr)
        if isinstance(mspectrum.mask, bool) or isinstance(mspectrum.mask, np.bool_):
            mspectrum.mask = np.array([mspectrum.mask] * len(mspectrum.data))
        if isinstance(nspectrum.mask, bool) or isinstance(nspectrum.mask, np.bool_):
            nspectrum.mask = np.array([nspectrum.mask] * len(nspectrum.data))
        spec = [Spectrum(mspectrum, copy.deepcopy(freq), copy.deepcopy(chans)),
                Spectrum(nspectrum, copy.deepcopy(freq), copy.deepcopy(chans))]
        for s in spec:
            s.mask_invalid()
            s.fix_invalid(0.0)
            s.mask_equal(0.0)

            segment["spectrum"] = s.spec()
            segment["freq"] = s.freq()
            sfinder = SegmentFinder.SegmentFinder(**segment)
            sep, cut, noise, mean = sfinder.find()
            s.set_noise(noise)

        # smooth the spectrum if requested
        if len(smooth) > 0 and smooth[0] is not None:
            filter = Filter1D.Filter1D(spec[0].spec(), smooth[0], **Filter1D.Filter1D.convertargs(smooth))
            spec[0].set_spec(ma.MaskedArray(filter.run(), mspectrum.mask))
            filter = Filter1D.Filter1D(spec[1].spec(), smooth[0], **Filter1D.Filter1D.convertargs(smooth))
            spec[1].set_spec(ma.MaskedArray(filter.run(), nspectrum.mask))
            if recalc:
                for s in spec:
                    segment["spectrum"] = s.spec()
                    segment["freq"] = s.freq()
                    sfinder = SegmentFinder.SegmentFinder(**segment)
                    sep, cut, noise, mean = sfinder.find()
                    s.set_noise(noise)

    # if the input bdp is a CubseSpectrum then get all of the available
    # spectra
    elif bdp._type == bt.CUBESPECTRUM_BDP:
        spectrum = ma.array(bdp.table.getFullColumnByName("flux", typ=np.float64), fill_value=0.0)

        # get the frequencies of the channels
        freq = bdp.table.getFullColumnByName("frequency", typ=np.float64)
        # get the channel number of each channel
        chans = bdp.table.getFullColumnByName("channel", typ=np.float64)
        # CubeSpectrum can have more than one spectra
        if len(spectrum.shape) == 2:
            multi = True
            for i in range(len(spectrum)):
                spectrum[i] = ma.masked_equal(spectrum[i], 0.0)
        else:
            spectrum = [ma.masked_equal(spectrum, 0.0)]
            freq = [freq]
            chans = [chans]
            # smooth the spectra if requested
        spec = []
        for i in range(len(spectrum)):
            if isinstance(spectrum[i].mask, bool) or isinstance(spectrum[i].mask, np.bool_):
                spectrum[i].mask = np.array([spectrum[i].mask] * len(spectrum[i].data))
        for i in range(len(freq)):
            # source rest frame
            freq[i] = utils.undoppler(freq[i], vlsr)
            tempspec = Spectrum(spectrum[i], freq[i], chans[i])
            tempspec.mask_invalid()
            tempspec.fix_invalid(0.0)
            tempspec.mask_equal(0.0)


            segment["spectrum"] = tempspec.spec()
            segment["freq"] = tempspec.freq()
            sfinder = SegmentFinder.SegmentFinder(**segment)
            sep, cut, noise, mean = sfinder.find()
            tempspec.set_noise(noise)
            spec.append(tempspec)

        if len(smooth) > 0 and smooth[0] is not None:
            for s in spec:
                filter = Filter1D.Filter1D(s.spec(), smooth[0], **Filter1D.Filter1D.convertargs(smooth))
                s.set_spec(ma.MaskedArray(filter.run(), mask=spectrum[i].mask))
                if recalc:
                    segment["spectrum"] = s.spec()
                    segment["freq"] = sfreq()
                    sfinder = SegmentFinder.SegmentFinder(**segment)
                    sep, cut, noise, mean = sfinder.find()
                    s.set_noise(noise)
                    
        # doppler shift the input spectra, which are in sky frequency, to the proper
    elif bdp._type == bt.PVCORR_BDP:
        if len(bdp.table) == 0:
            return None, None, None, None
        pvcorr = True
        chans = bdp.table.getColumnByName("channel", typ=np.float64)
        freq = bdp.table.getColumnByName("frequency", typ=np.float64)
        spectrum = ma.array(bdp.table.getFullColumnByName("pvcorr", typ=np.float64), fill_value=0.0)
        # doppler shift the input spectra, which are in sky frequency, to the proper
        # source rest frame
        freq = utils.undoppler(freq, vlsr)
        spectrum = ma.masked_equal(spectrum, 0.0)
        spec = Spectrum(spectrum, freq, chans)
        spec.mask_invalid()
        spec.fix_invalid(0.0)
        spec.mask_equal(0.0)
    else:
        raise Exception("Data from BDP type %s is not supported." % (bdp._type))
    return spec


def getinfo(segment, spec):
    """ Method to get basic information about a spectral line that was only
        detected by segment detection. Calculates the peak intensity, the
        sigma of the peak, and the very rough FWHM of the line.

        Parameters
        ----------
        segment : list
            List of two points (the start and end of the segement)

        spec : a single admit.util.Spectrum or list of admit.util.Spectrum.
               If a list, the Spectrum with the highest peak (or lowest in case of absorption spectrum) will be used.

        Returns
        -------
        Tuple containing the peak intensity, sigma, and FHWM in km/s of the
        line
    """
    if spec is None: return None,None,None
    peak = 0.0
    ratio = 0.0
    rms = 0.0
    fwhm = 0.0
    end = 0
    start = 0
    if type(spec) is list:
        pkloc = 0
        # find the strongest peak from all input spectra
        for i in range(len(spec)):
            tmp = spec[i].peak(segment)
            if tmp > peak:
                pkloc = i
                peak = tmp
        thespectrum = spec[pkloc]
    else:
        thespectrum = spec

    if len(thespectrum) > 0:
        rms  = thespectrum.rms()
        #print("Specinfo nchan=%d, rms = %f" % (segment[1]-segment[0],rms))
        peak = thespectrum.peak(segment)
        if (rms > 0):
            ratio = peak/rms
        else:
            ratio = 0.0
        fwhm = thespectrum.fwhm(segment)
    else:
        return None, None, None

    return peak, ratio, fwhm

# @todo just use **keyval here?
def findsegments(spectra,method,minchan,maxgap,numsigma,iterate,noise=None):
    """Call Segmentfinder with specific options. Used by LineID_AT
       and LineSegment_AT

       Parameters
       ----------
          spectra : list 
             list of input spectra 

          method  : string
             segment finding method

          maxgap  : int
             maximum channel gap between segments

          numsigma : float
             level cutoff for finding segments, measured in number of 1 sigma rms noise

          iterate  : boolean 

          noise : float 
             noise level to use. Default: None, noise is calculated
     
       Returns
       -------
         list of [(separation,cutoff,noise,mean)] tuples as returned by SegmentFinder.find(), indexed to input spectra

    """
    vals = []
    for i, spec in enumerate(spectra):
        sfinder = SegmentFinder.SegmentFinder(spectrum=spec.spec(),
                                              freq=spec.freq(),
                                              method=method,
                                              minchan=minchan,
                                              maxgap=maxgap,
                                              numsigma=numsigma,
                                              iterate=iterate, 
                                              nomean=True,
                                              noise=noise)

        vals.append(sfinder.find())
    return vals

def contsub(id, spectra, segmentfinder, segargs, algorithm, **keyval):
    """ Do continuum  subtraction with specific arguments.  Used by LineID_AT
        and LineSegment_AT
            Parameters
            ----------
            id : int
                Task id of the AT calling this method

            spectra : list
                List of spectra to run continuum subtraction on

            segmentfinder : str
                The segment finder to use (i.e. ADMIT, ASAP, etc.)

            segargs : dict
                Dictionary containing the arguments for the segmentfinder

            algorithm : str
                The continuum finding algorithm to use (i.e. PolyFit, SplineFit, SVD_Vander, etc.)

            keyval : dict
                Dictionary containing the arguments for the continuum finding algorithm

    """
    for i,spec in enumerate(spectra):
        csub = continuumsubtraction.spectral.ContinuumSubtraction()
        spec.set_contin(csub.run(id, spec.spec(), spec.freq(), segmentfinder, segargs, algorithm, **keyval))



def mergefreq(globalfreq, globalchan, freq, chan):
    """ Method to merge the frequency and channel axes from input spectra into a single global
        set.

        Parameters
        ----------
        globalfreq : array like
            The global set of frequencies, may be empty if first time

        globalchan : array like
            The global set of channels, may be empty if first time

        freq : array like
            The frequency axis to add to the global set

        chan : array like
            The channel axis to add to the global set

        Returns
        -------
        (globalfreq, globalchan) as numpy array tuple
        @todo return it as same type as came in? 

    """
    # if this is the first time, then initialize the array
    if globalfreq is None or globalchan is None or len(globalfreq) == 0 or len(globalchan) == 0:
        return (copy.deepcopy(freq), copy.deepcopy(chan))
    else:
        # otherwise merge in the new frequency axis, extending as needed
        if globalfreq[0] > globalfreq[-1]:
            if freq[0] > globalfreq[0]:
                for i in range(len(freq)):
                    if freq[i] < globalfreq[0]:
                        i -= 1
                        break
                globalfreq = ma.concatenate((freq[0:i], globalfreq))
                globalchan = ma.concatenate((chan[0:i], globalchan))
            if freq[-1] < globalfreq[-1]:
                for i in range(len(freq) - 1, -1, -1):
                    if freq[i] > globalfreq[-1]:
                        i += 1
                        break
                globalfreq = ma.concatenate((globalfreq, freq[i:]))
                globalchan = ma.concatenate((globalchan, chan[i:]))
        else:
            if freq[0] < globalfreq[0]:
                for i in range(len(freq)):
                    if freq[i] > globalfreq[0]:
                        i -= 1
                        break
                globalfreq = ma.concatenate((freq[0:i], globalfreq))
                globalchan = ma.concatenate((chan[0:i], globalchan))
            if freq[-1] > globalfreq[-1]:
                for i in range(len(freq) - 1, -1, -1):
                    if freq[i] < globalfreq[-1]:
                        i += 1
                        break
                globalfreq = ma.concatenate((globalfreq, freq[i:]))
                globalchan = ma.concatenate((globalchan, chan[i:]))

        return (globalfreq, globalchan)
    

def linedatafromsegments(freq,chan,segments,specs,statspec=None):
    """
    Common method used by LineSegment_AT and LineID_AT to construct
    LineData from an input list of segments.

        Parameters
        ----------
        freq : array like
            The global frequency axis of the input segments

        chan : array like
            The global channel axis of the input segments

        segments: array like
            The input segments, as returned from e.g. mergesegments

        specs : Spectrum
            Array of spectra or single spectrum

        statspec : Spectrum
            Optional Cubestats spectrum
    
        Returns
        --------
        List of LineData objects constructed from input segments
    """
    lines = []
    for ch in segments:
        for i in range(len(chan)):
            if chan[i] >= ch[0]:
                break
        mn = i
        for i in range(len(chan) - 1, -1, -1):
            if chan[i] <= ch[1]:
                break
        mx = i
        frq = [min(freq[mn], freq[mx]),
                      max(freq[mn], freq[mx])]
        mid = (frq[0] + frq[1]) / 2.0
        if statspec != None and len(statspec) != 0:
            peak, ratio, fwhm = getinfo(ch, statspec)
        else:
            peak, ratio, fwhm = getinfo(ch, specs)
        lname = "U_%.3f" % mid
        linedata = LineData.LineData(frequency=float(mid), uid=lname, formula="NotIdentified", name="Not Identified", plain="N/A", peakintensity=float(peak), fwhm=float(fwhm), chans=[ch[0], ch[1]], peakrms=float(ratio))
        lines.append(linedata)

    return lines


