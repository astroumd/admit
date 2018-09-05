""" .. _Spectrum-api:

    **Spectrum** --- Spectral line data container.
    ----------------------------------------------

    This module defines the Spectrum class.
"""
# system imports
import numpy as np
import numpy.ma as ma
import copy
import math

# ADMIT imports
from admit.util.AdmitLogging import AdmitLogging as logging
import utils

class Spectrum(object):
    """ Class for holding a spectrum. It holds entries for the spectrum,
        frequency axis, channel axis, vlsr, and rest_frequency. A mask
        is also available to mask bad data points. The mask is common to
        all axes.

        A spectrum needs to hold at least 2 channels.

        Parameters
        ----------
        spec : array like
            The spectrum.

        freq : array like
            The frequency axis, one entry per spectral point.

        chans : array like
            The channel axis, one entry per spectral point.

        contin : array like or float
            The continuum for each channel, or for all channels if it is an
            int.

        noise : float
            The rms noise of the spectrum.

        mask : array like or bool
            The mask for the spectrum, one entry per spectral point
            or a single boolean value, Defaults to all good.

    """
    def __init__(self, spec=None, freq=None, chans=None, contin=None, noise=None, mask=[False]):
        domask = True
        self._mask = None
        self._freq = None
        self._chans = None
        self._spec = None
        self._contin = None
        self._noise = None
        self._delta = None
        if spec is not None:
            self.set_spec(spec, mask)
            domask = False

        if freq is not None:
            self.set_freq(freq)

        if noise is not None:
            self._noise = noise

        if chans is not None:
            self.set_chans(chans)

        if contin is not None:
            self.set_contin(contin)

        if domask:
            self.set_mask(mask)

        self.integritycheck()

    def __len__(self):
        return len(self._spec)

    def spec(self, csub=True, masked=True):
        """ Method to get the spectrum, the mask is optionally returned

            Parameters
            ----------
            csub : bool
                If True return the spectrum with the continuum subtracted,
                False will return the pure spectrum
                Default: True

            masked : bool
                If True then return the spectrum as a masked array with
                the current mask applied. False will return a numpy array
                with no masking done.
                Default: True

            Returns
            -------
            Array like object containing the spectrum

        """
        data = copy.deepcopy(self._spec)
        if csub and self._contin is not None and len(self._contin) > 0:
            data -= self._contin
        if masked:
            return ma.masked_array(data, mask=self._mask)
        return data

    def freq(self, masked=True):
        """ Method to get the frequency axis, the mask is optionally returned

            Parameters
            ----------
            masked : bool
                If True then return the frequency axis as a masked array with
                the current mask applied. False will return a numpy array
                with no masking done.

            Returns
            -------
            Array like object containing the frequency axis

        """
        if masked:
            return ma.masked_array(self._freq, mask=self._mask)
        return self._freq

    def contin(self, masked=True):
        """ Method to get the continuum, the mask is optionally returned

            Parameters
            ----------
            masked : bool
                If True then return the continuum as a masked array with
                the current mask applied. False will return a numpy array
                with no masking done.

            Returns
            -------
            Array like object containing the continuum

        """
        if masked:
            return ma.masked_array(self._contin, mask=self._mask)
        return self._contin

    def noise(self):
        """ Method to return the noise of the spectrum.

            Parameters
            ----------
            None

            Returns
            -------
            Float of the rms noise.

        """
        return self._noise

    def rms(self):
        """If the noise has been set, return the noise, otherwise
           compute and return the root-mean-square value of the spectrum.
        """
        if self._noise == None:
           return np.sqrt(np.mean(np.square(self.spec())))
        else:
           return self._noise

    def delta(self):
        if self._delta is None:
            self.calcdelta()
        else:
            return self._delta

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
        if chan > np.max(self._chans):
            return self._freq[self._chans[np.argmax(self._chans)]]
        if chan < np.min(self._chans):
            return self._freq[self._chans[np.argmin(self._chans)]]
        ichan = int(chan)
        ch = np.where(self._chans == ichan)[0][0]

        f1 = self._freq[ch]

        if np.where(self._chans == np.max(self._chans))[0][0] > ch + 1:
            f2 = self._freq[ch + 1]
        else:
            f2 = self._freq[ch - 1]
        frac = chan - float(ichan)
        return f1 + frac * (f2 - f1)

    def getchanindex(self, chan):
        """

        """
        if ma.max(self._chans) >= chan >= ma.min(self._chans):
            return ma.where(self._chans == int(chan))[0][0]
        else:
            return -1

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

        if frq <= np.min(self._freq):
            return int(self._chans[np.where(self._freq == np.min(self._freq))[0][0]])
        if frq >= np.max(self._freq):
            return int(self._chans[np.where(self._freq == np.max(self._freq))[0][0]])
        for i in range(len(self._freq) - 1):
            if self._freq[i] <= frq < self._freq[i + 1] or \
               self._freq[i] >= frq > self._freq[i + 1]:
                return int(self._chans[i])

    def chans(self, masked=True):
        """ Method to get the channel axis, the mask is optionally returned

            Parameters
            ----------
            masked : bool
                If True then return the channel axis as a masked array with
                the current mask applied. False will return a numpy array
                with no masking done.

            Returns
            -------
            Array like object containing the channel axis

        """
        if masked:
            return ma.masked_array(self._chans, mask=self._mask)
        return self._chans

    def mask(self):
        """ Method to return the mask as a numpy array

        Parameters
        ----------
        None

        Returns
        -------
        Array like object containing the mask

        """
        return self._mask

    def mask_equal(self, value, axis="spec"):
        """ Method to mask data equal to the given value.
            Any axis can be used  ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            value : float or int
                The value equal to which all data of the given axis
                will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None


        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = getattr(self, "_" + axis, None) == value
        self._mask = np.logical_or(self._mask, mask)

    def mask_lt(self, limit, axis="spec"):
        """ Method to mask any data less than the given value.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit : float or int
                The value below which all data of the given axis
                will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = getattr(self, "_" + axis, None) < limit
        self._mask = np.logical_or(self._mask, mask)

    def mask_gt(self, limit, axis="spec"):
        """ Method to mask any data greater than the given value.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit : float or int
                The value above which all data of the given axis
                will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = getattr(self, "_" + axis, None) > limit
        self._mask = np.logical_or(self._mask, mask)

    def mask_le(self, limit, axis="spec"):
        """ Method to mask any data less than or erqual to the given value.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit : float or int
                The value which all data, of the given axis,
                less than or equal to, will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = getattr(self, "_" + axis, None) <= limit
        self._mask = np.logical_or(self._mask, mask)

    def mask_ge(self, limit, axis="spec"):
        """ Method to mask any data less than or equal to the given value.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit : float or int
                The value which all data, of the given axis,
                greater than or equal to, will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = getattr(self, "_" + axis, None) >= limit
        self._mask = np.logical_or(self._mask, mask)

    def mask_between(self, limit1, limit2, axis="spec"):
        """ Method to mask any data bewteen the the given values.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit1 : float or int
                The value above which all data of the given axis
                will be masked.

            limit2 : float or int
                The value below which all data of the given axis
                will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask1 = limit1 < getattr(self, "_" + axis, None)
        mask2 = getattr(self, "_" + axis, None) < limit2
        mask = np.logical_and(mask1, mask2)
        self._mask = np.logical_or(self._mask, mask)

    def mask_outside(self, limit1, limit2, axis="spec"):
        """ Method to mask any data less than or greater than the given values.
            Any axis can be used ("spec", "freq", "chans") as
            the basis for the masking.

            Parameters
            ----------
            limit1 : float or int
                The value below which all data of the given axis
                will be masked.

            limit2 : float or int
                The value above which all data of the given axis
                will be masked.

            axis : str
                The axis which is used to determine the flags.
                Default: "spec"

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask1 = getattr(self, "_" + axis, None) < limit1
        mask2 = limit2 < getattr(self, "_" + axis, None)
        mask = np.logical_and(mask1, mask2)
        self._mask = np.logical_or(self._mask, mask)

    def set_noise(self, noise):
        """ Method to set the noise value for the spectrum.

            Parameters
            ----------
            noise : float
                The noise of the spectrum

            Returns
            -------
            None

        """
        self._noise = noise

    def set_mask(self, mask):
        """ Method to set the mask item

            Parameters
            ----------
            mask : array like or bool
                The mask to use, must be equal in dimmension to
                the spectral axis, or a single boolean value which
                is applied to all data.

            Returns
            -------
            None

        """
        tempmask = self._mask
        if isinstance(mask, ma.masked_array):
            if len(self._spec) > len(mask) > 1:
                raise
            elif len(mask) == 1:
                self._mask = np.array([mask.data[0]] * len(self._spec))
            else:
                self._mask = np.array(mask.data)
        elif isinstance(mask, list) or isinstance(mask, np.ndarray):
            if len(self._spec) > len(mask) > 1:
                raise
            elif len(mask) == 1:
                self._mask = np.array([mask[0]] * len(self._spec))
            else:
                self._mask = np.array(mask)
        if self.integritycheck():
            return
        logging.warning("  Mask not applied")
        self._mask = tempmask

    def set_spec(self, spec, mask=None):
        """ Method to set the spectrum, an optionally the mask.

            Parameters
            ----------
            spec : array like
                The spectrum to set

            mask : array like or single bool
                The mask to apply to the spectrum. Default: None (no mask)

            Returns
            -------
            None

        """
        if isinstance(spec, list):
            self._spec = np.array(spec)
            if mask is not None:
                self.set_mask(mask)
            else:
                self.set_mask([False])
        elif isinstance(spec, ma.masked_array):
            self._spec = spec.data
            if isinstance(spec.mask, bool) or isinstance(spec.mask, np.bool_):

                self._mask = np.array([spec.mask] * len(spec.data))
            else:
                self._mask = spec.mask
        elif isinstance(spec, np.ndarray):
            self._spec = spec
            if mask is not None:
                self.set_mask(mask)
            else:
                self.set_mask([False])
        else:
            raise

    def set_freq(self, freq):
        """ Method to set the frequency axis.

            Parameters
            ----------
            freq : array like
                The frequency axis to use

            Returns
            -------
            None

        """
        if isinstance(freq, list):
            self._freq = np.array(freq)
        elif isinstance(freq, ma.masked_array):
            self._freq = freq.data
        elif isinstance(freq, np.ndarray):
            self._freq = freq
        else:
            raise
        self.calcdelta()

    def set_contin(self, contin):
        """ Method to set the continuum.

            Parameters
            ----------
            freq : array like
                The continuum to use

            Returns
            -------
            None

        """
        if isinstance(contin, list):
            self._contin = np.array(contin)
        elif isinstance(contin, float) or isinstance(contin, int):
            self.contin = np.array([contin] * len(self._spec))
        elif isinstance(contin, ma.masked_array):
            self._contin = contin.data
        elif isinstance(contin, np.ndarray):
            self._contin = contin
        else:
            raise

    def set_chans(self, chans):
        """ Method to set the channel axis.

            Parameters
            ----------
            chans : array like
                The channel axis to use

            Returns
            -------
            None

        """
        if isinstance(chans, list):
            self._chans = np.array(chans, dtype=np.int)
        elif isinstance(chans, ma.masked_array):
            self._chans = chans.data.astype(np.int, copy=True)
        elif isinstance(chans, np.ndarray):
            self._chans = chans.astype(np.int, copy=True)
        else:
            raise

    def calcdelta(self):
        if self._freq is None:
            raise Exception("calcdelta: no freq set")
        if len(self._freq) == 1:
            raise Exception("calcdelta: frequency axis 1, continuum?")
        for f in range(len(self._freq) - 1):
            if not self._mask[f] and not self._mask[f + 1]:
                self._delta = abs(self._freq[f] - self._freq[f + 1])
                return
        raise Exception("calcdelta")

    def centerfreq(self):
        cen = int(len(self._freq) / 2)
        for i in range(cen - 1):
            if not self._mask[cen + i]:
                return self._freq[cen + i]
            if not self._mask[cen - i]:
                return self._freq[cen - i]
        raise
        

    def fix_invalid(self, mask_value=0.0):
        """ Method to replace invalid spectral data with a specific value
            and mask it. Invalid values are: NaN, Inf, -Inf

            Parameters
            ----------
            mask_value : float
                The value to replace the invalid data with.
                Default: 0.0

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = np.isfinite(self._spec)
        for i in range(len(mask)):
            if not mask[i]:
                self._spec[i] = mask_value
        self._mask = np.logical_or(self._mask, np.logical_not(mask))

    def mask_invalid(self):
        """ Method to mask all invalid spectral data.
            Invalid values are: NaN, Inf, -Inf

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        if not self.integritycheck():
            logging.warning("  Masking operation not performed.")
            return
        mask = np.isfinite(self._spec)
        self._mask = np.logical_or(self._mask, np.logical_not(mask))

    def integritycheck(self):
        """ Method to check that all axes are the same length. Axes
            that have no data are ignored.

            Parameters
            ----------
            None

            Returns
            -------
            Bool, True if all match, False if there is an inconsistency

        """
        if self._spec is not None:
            ls = len(self._spec)
        else:
            ls = 0
        if self._freq is not None:
            lf = len(self._freq)
        else:
            lf = ls
        if self._chans is not None:
            lc = len(self._chans)
        else:
            lc = ls
        if self._mask is not None:
            lm = len(self._mask)
        else:
            lm = ls
        if self._contin is not None:
            lco = len(self._contin)
        else:
            lco = ls
        if ls == lf == lc == lm == lco:
            return True
        logging.warning("Inconsistent axes: spectrum: %i, freq: %i, chans: %i, mask: %i, contin: %i" % (ls, lf, lc, lm, lco))
        return False

    def _sanitizechanrange(self,chanrange,chupper):
        if chanrange == None:
           chanrange = [ 0, chupper ]
        else:
           if chanrange[0] < 0 or chanrange[0] > chupper or chanrange[1] < 0 or chanrange[1] > chupper:
              msg = "Bad input channel range %s. Available range is [0,%d]" % (chanrange,chupper)
              raise Exception, msg
        return chanrange

    def momenti(self,chanrange=None,p=1):
        """Intensity-weighted moment
           Note this moment does poorly for very narrow line segments where
           some channels may be negative."

           Parameters
           ----------
           chanrange: range of channels over which to compute moment
                      [startchan, endchan]
           p:         the moment to compute (the power of the frequency in the sum)
 
           Returns:
             The computed moment
         """
        # get the masked array
        s = self.spec()
        chupper = len(s)-1
        chanrange = self._sanitizechanrange(chanrange,chupper)
        sum_s = ma.sum(s[chanrange[0]:chanrange[1]+1])
        sum_sf = 0
        mean = 0
        if p > 1:
           mean = self.moment(chanrange,p-1)
        for i in range(chanrange[0],chanrange[1]+1):
           sum_sf += s[i]*math.pow((self._freq[i]-mean),p)
        return sum_sf/sum_s

    def momenta(self,chanrange=None,p=1):
        """abs(intensity)-weighted moment
           Does somewhat better than signed intensity-weighted moment.

           Parameters
           ----------
           chanrange: range of channels over which to compute moment
                      [startchan, endchan]
           p:         the moment to compute (the power of the frequency in the sum)
 
           Returns:
             The computed moment
        """
        # get the masked array
        s = self.spec()
        chupper = len(s)-1
        chanrange = self._sanitizechanrange(chanrange,chupper)
        sum_s = ma.sum(ma.abs(s[chanrange[0]:chanrange[1]+1]))
        sum_sf = 0
        mean = 0
        if p > 1:
           mean = self.moment(chanrange,p-1)
        for i in range(chanrange[0],chanrange[1]+1):
           sum_sf += ma.abs(s[i])*math.pow((self._freq[i]-mean),p)
        return sum_sf/sum_s

    def moment(self,chanrange=None,p=1):
        """Compute the power-weighted moment of a spectrum
           If a mask exists, this function operates on the masked spectrum.

               f_mean = Sum(spec[i]**2*(f[i]-mom{p-1})^p])/Sum(spec[i]**2)

           where spec[i] is the intensity at channel i (spec[i]**2 is he power) 
           and f[i] is the frequency at channel i, p is the moment power,
           and mom{p-1} is the p-1-th moment [for p >1].

           Parameters
           ----------
           chanrange: range of channels over which to compute moment
                      [startchan, endchan]
           p:         the moment to compute (the power of the frequency in the sum)
 
           Returns:
             The computed moment
        """
        # get the masked array
        s = self.spec()
        chupper = len(s)-1
        chanrange = self._sanitizechanrange(chanrange,chupper)
        sum_s = ma.sum(s[chanrange[0]:chanrange[1]+1]*s[chanrange[0]:chanrange[1]+1])
        sum_sf = 0
        mean = 0
        if p > 1:
           mean = self.moment(chanrange,p-1)
        for i in range(chanrange[0],chanrange[1]+1):
           sum_sf += s[i]*s[i]*math.pow((self._freq[i]-mean),p)
        return sum_sf/sum_s
 
    def meanfrequency(self,chanrange=None):
        """Compute the power-weighted mean frequency of this spectrum, 
           aka the first moment.
           If a channel range is given, the mean frequency is computed
           over that channel range, otherwise over the entire spectrum.
           If a mask exists, this function operates on the masked spectrum.

           Parameters
           ----------
           chanrange: range of channels over which to compute frequency
                      [startchan, endchan]

           Returns
           -------
           Power-weighted mean frequency as computed by

               f_mean = Sum(spec[i]**2*f[i]])/Sum(spec[i]**2)

           where spec[i] is the intensity at channel i and f[i] is
           the frequency at channel i.
        """
        return self.moment(chanrange,1)

    def meanvelocity(self,chanrange=None):
        """Compute the power-weighted mean velocity of this spectrum. 
           derived from the mean frequency and channel width:

             mean_v = C * delta()/meanfrequency(chanrange)

        """
        mf = self.meanfrequency(chanrange)
        return self.moment(chanrange,1) * utils.freqtovel(mf,self.delta())


    def freqdispersion(self,chanrange=None):
        """Compute the frequency dispersion of the spectrum in the given
           channel range.
           If a mask exists, this function operates on the masked spectrum.
   
           Parameters
           ----------
           chanrange: range of channels over which to compute dispersion
                      [startchan, endchan]
   
           Returns
           -------
           Power-weighted frequency dispersion df as computed by
   
               df = sqrt(mom2)
   
           where mom2 is the 2nd moment as computed by the moment() method.
        """
        #MWP: I don't understand why I need an extra factor of sqrt(2) here
        # when using power spectrum weighting in moment()!
        return math.sqrt(2*self.moment(chanrange,2))


    def veldispersion(self,chanrange=None):
        """Compute the velocity dispersion (km/s) of the spectrum in the given
           channel range.
           If a mask exists, this function operates on the masked spectrum.
  
           Parameters
           ----------
           chanrange: range of channels over which to compute dispersion
                      [startchan, endchan]
  
           Returns
           -------
           Power-weighted velocity dv as computed by

  
             dv = C * df/mf
  
           where df is the frequency dispersion computered by
           the frequencydispersion() method,
           mf is the mean frequency from the meanfrequency() method, 
           and C is the speed of light.
        """
        mf = self.meanfrequency(chanrange)
        return utils.freqtovel(mf,self.freqdispersion(chanrange))
  
    def fwhm(self,chanrange=None):
        """Compute the full-width at half-maximum velocity (km/s).
           If a mask exists, this function operates on the masked spectrum.
  
           Parameters
           ----------
           chanrange: range of channels over which to compute dispersion
                      [startchan, endchan]
  
           Returns
           -------
           fwhm computed by
  
               fwhm = dv * sqrt(8*ln(2))
  
           where dv is the velocity dispersion computered by
           the veldispersion() method.
        """
        return self.veldispersion(chanrange)*math.sqrt(8*math.log(2))

    def peak(self,chanrange=None):
        """Return the peak intensity in the given channel range
           If a mask exists, this function operates on the masked spectrum.

           Parameters
           ----------
           chanrange: range of channels over which to compute dispersion
                      [startchan, endchan]

           Returns
           ----------
           Maximum of the absolute value of the spectrum in the channel range
                     max(abs(spectrum[startchan:endchan]))
        """
        s = self.spec()
        chupper = len(s)-1
        chanrange = self._sanitizechanrange(chanrange,chupper)

        # Handle one-channel ranges.
        if (chanrange[0] == chanrange[1]):
           return s[chanrange[0]]

        return ma.max(ma.abs(s[chanrange[0]:chanrange[1]]))

    def invert(self):
        """Multiply this spectrum and continuum by -1 

           Parameters
           ----------
           None

           Returns
           ----------
           None
        """
        if self._spec is not None:
            self._spec *= -1.
        if self._contin is not None:
            self._contin *= -1.

