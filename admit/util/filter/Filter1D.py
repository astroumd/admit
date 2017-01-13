""" .. _filter1D:

    Filter1D --- 1-dimensional spectral filtering.
    ----------------------------------------------

    This module defines the 1D filter methods.
"""

import numpy as np
import math
from copy import deepcopy
from collections import OrderedDict


class Filter1D(object):
    """ This class defines and runs 1D spectral filters. The currently available
        filters are Gaussian, Hanning, Triangle, Welch, Boxcar, and Savitzky 
        Golay. The output spectrum will be of the same length as the input 
        spectrum, however some edge channels may be zeroed by some methods, 
        depending on the input paramters.

        Parameters
        ----------
        spec : numpy array
            1D numpy array of the input spectrum (just the amplitudes).

        method : str
            The smoothing filter to apply: boxcar, gaussian, welch, hanning, 
            triangle, or savgol. 
            No default. Minimum matching is enabled with a minimum of 3 
            characters, i.e. box = boxcar.

        keyval : various
            Any keyword value pairs for the specific method chosen, see the 
            notes for specific keywords.

        Attributes
        ----------
        spec : numpy array
            The spectrum.

        len : int
            The length of the spectrum.

        methods : list
            A list of the available filters.

        [method]_args : dict
            A dictionary for each method giving its keywords and defaults 
            (e.g. boxcar_args).

        method : str
            The method being used.

        Notes
        -----
        Details of the different filter keywords and defaults:

        .. tabularcolumns:: |p{1.5cm}|p{2cm}|p{0.5cm}|p{8cm}|

        +------------+---------------+------+----------------------------------------------+
        | Filter     | Keyword       | Def. | Description                                  |
        +============+===============+======+==============================================+
        | "boxcar"   | "width"       | 3    | Number of channels to average together       |
        +------------+---------------+------+----------------------------------------------+
        | "gaussian" | "width"       | 7    | Number of channels to span with the gaussian |
        +------------+---------------+------+----------------------------------------------+
        | "hanning"  | "width"       | 5    | Number of channels to include in the cos     |
        +------------+---------------+------+----------------------------------------------+
        | "triangle" | "width"       | 5    | Number of channels to span with the triangle |
        +------------+---------------+------+----------------------------------------------+
        | "welch"    | "width"       | 5    | Number of channels to use in the function    |
        +------------+---------------+------+----------------------------------------------+
        | "savgol"   | "window_size" | 7    | Number of channels to use in the calculation |
        +------------+---------------+------+----------------------------------------------+
        |            | "order"       | 3    | Order of the poynomial fit (must be odd)     |
        +------------+---------------+------+----------------------------------------------+
        |            | "deriv"       | 0    | The number of the derivative to compute      |
        |            |               |      | (0 = just smooth)                            |
        +------------+---------------+------+----------------------------------------------+

    """
    boxcar_args =   OrderedDict([("width", 3)])
    gaussian_args = OrderedDict([("width", 7)])
    welch_args =    OrderedDict([("width", 5)])
    hanning_args =  OrderedDict([("width", 5)])
    triangle_args = OrderedDict([("width", 5)])
    savgol_args =   OrderedDict([("window_size", 7), 
                                 ("order"      , 3), 
                                 ("deriv"      , 0), 
                                 ("rate"       , 1)])

    methods = ["boxcar", 
               "gaussian", 
               "welch", 
               "hanning", 
               "triangle", 
               "savgol"]

    def __init__(self, spec, method, **keyval):
        if len(spec.shape) > 1:
            raise Exception("Spectrum is not 1D but you are trying to use a 1D filter.")
        self.spec = spec
        self.len = self.spec.shape[0]
        # keywords for the different algorithms
        self.method = self.checkmethod(method)
        for k, v in keyval.iteritems():
            try:
                a = getattr(self, method + "_args")[k]
            except:
                raise Exception("Unknown input %s for smoothing." % (k))
            if type(a) != type(v):
                raise Exception("Cannot change the type of an attribute. %s must be a %s not a %s." % (k, type(a), type(v)))
            getattr(self, method + "_args")[k] = v

    def isodd(self, value):
        """ Method to determine if a number is odd

            Parameters
            ----------
            value : int
                The number to check

            Returns
            -------
            bool, True if the number is odd, False if it is even

        """
        return value%2 == 1

    def checkmethod(self, method):
        """ Method to interpret the input method and determine the full method 
            name

            Parameters
            ----------
            method : str
                The method to use, minimal matching is possible, with a minimum
                of 3 characters (e.g. "box" will be interpreted to be "boxcar")

            Returns
            -------
            None
        """
        if len(method) < 3:
            raise Exception("Minimum of 3 characters are needed for minimal matching of strings.")
        for m in self.methods:
            if m.startswith(method):
                return m
        raise Exception("Unknown method %s given for smoothing. Available methods are: %s" % (method, str(self.methods)))

    def buffer(self, nchan):
        """ Method to buffer/pad an array so that filters can work all the way
            to the edge. Uses np.pad with mode='reflect'

            Parameters
            ----------
            nchan : int
                The number of channels to add to each end of the array

            Returns
            -------
            Numpy array containing the buffered input array
        """
        return np.pad(self.spec, (nchan, ), mode='reflect')

    def boxcar(self, width):
        r""" Method to apply a boxcar filter to a spectrum. The filter for point
            x[i] is defined as:

            .. math::

                x[i] = \frac{1}{N} \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}]

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The width of the box to use in channels, must be odd

            Returns
            -------
            numpy array
                The smoothed spectrum, (width - 1)/2 edge channels will be 
                zeroed
        """
        if not self.isodd(width):
            raise Exception("Boxcar width must be an odd number.")
        side = (width - 1) / 2
        kernel = np.array([1.0] * width)
        kernel /= kernel.sum()
        return np.convolve(self.buffer(side), kernel, mode="valid")

    def gaussian(self, width):
        r""" Method to apply a Gaussian filter to a spectrum. The filter for 
            point x[i] is defined as:

            .. math::

                x[i] = \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] e^{-\frac{1}{2}\left(\frac{n-(N-1)/2}{\sigma(N-1)/2}\right)^2}

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the gaussian for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed spectrum, (width - 1)/2 edge channels will be zeroed
        """
        if not self.isodd(width):
            raise Exception("Gaussian width must be an odd number.")
        side = (width - 1) / 2
        kernel = np.zeros(width)
        for j in range(width):
            kernel[j] = math.exp(-0.5 * pow(((float(j) - ((float(width) - 1.0) /
                                 2.0)) / (0.2 * (float(width) - 1.0) / 2.0)), 2))
        kernel /= kernel.sum()
        return np.convolve(self.buffer(side), kernel, mode="valid")

    def welch(self, width):
        r""" Method to apply a Welch filter to a spectrum. The filter for point x[i]
            is defined as:

            .. math::

                x[i] = \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] \left(1 - \left(\frac{n - \frac{N-1}{2}}{\frac{N-1}{2}}\right)^2\right)

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the function for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed spectrum, (width - 1)/2 edge channels will be zeroed
        """
        if not self.isodd(width):
            raise Exception("Welch width must be an odd number.")
        width += 2    # must add 2 to get the proper width
        side = (width - 1) / 2
        kernel = np.zeros(width)
        for j in range(width):
            kernel[j] = (1 - math.pow((j - (float(width - 1) / 2.0)) / 
                         (float(width - 1) / 2.0), 2))
        kernel /= kernel.sum()
        return np.convolve(self.buffer(side), kernel, mode="valid")

    def hanning(self, width):
        r""" Method to apply a Hanning filter to a spectrum. The filter for 
            point x[i] is defined as:

            .. math::

                x[i] = \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] 0.5 \left(1 - \cos\left(\frac{2\pi n}{N-1}\right)\right)

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the function for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed spectrum, (width - 1)/2 edge channels will be zeroed
        """
        if not self.isodd(width):
            raise Exception("Hanning width must be an odd number.")

        width += 2    # must add 2 to get the proper width
        side = (width - 1) / 2
        kernel = np.zeros(width)
        for j in range(width):
            kernel[j] = 0.5 * (1.0 - math.cos((2.0 * math.pi * j) / float(width - 1)))
        kernel /= kernel.sum()
        return np.convolve(self.buffer(side), kernel, mode="valid")

    def triangle(self, width):
        r""" Method to apply a Triangular filter to a spectrum. The filter for 
            point x[i] is defined as:

            .. math::

                x[i] =  \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] \left(1 - \left|\frac{n-\frac{N-1}{2}}{\frac{N}{2}}\right|\right)

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the function for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed spectrum, (width - 1)/2 edge channels will be zeroed
        """
        if not self.isodd(width):
            raise Exception("Triangle width must be an odd number.")
        side = (width - 1) / 2
        kernel = np.zeros(width)
        for j in range(width):
            kernel[j] = (1 - abs((j - (float(width - 1) / 2.0)) / 
                         (float(width) / 2.0)))
        kernel /= kernel.sum()
        return np.convolve(self.buffer(side), kernel, mode="valid")

    def savgol(self, window_size, order, deriv=0, rate=1):
        """ Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
            The Savitzky-Golay filter removes high frequency noise from data.
            It has the advantage of preserving the original shape and
            features of the signal better than other types of filtering
            approaches, such as moving averages techniques. Adapted from
            http://wiki.scipy.org/Cookbook/SavitzkyGolay

            Parameters
            ----------
            window_size : int
                the length of the window. Must be an odd integer number.

            order : int
                the order of the polynomial used in the filtering.
                Must be less then `window_size` - 1.

            deriv: int
                the order of the derivative to compute (default = 0 means only 
                smoothing)

            Returns
            -------
            ndarray
                the smoothed signal (or it's n-th derivative).

            Notes
            -----

            The Savitzky-Golay is a type of low-pass filter, particularly
            suited for smoothing noisy data. The main idea behind this
            approach is to make for each point a least-square fit with a
            polynomial of high order over a odd-sized window centered at
            the point.

            References
            ----------
            .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
               Data by Simplified Least Squares Procedures. Analytical
               Chemistry, 1964, 36 (8), pp 1627-1639.
            .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
               W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
               Cambridge University Press ISBN-13: 9780521880688
        """
        if not self.isodd(width):
            raise Exception("Savgol window_size must be an odd number.")
        y = deepcopy(self.spec)
        try:
            window_size = np.abs(np.int(window_size))
            order = np.abs(np.int(order))
        except ValueError:
            raise ValueError("window_size and order have to be of type int")
        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        order_range = range(order + 1)
        half_window = (window_size - 1) // 2
        # precompute coefficients
        b = np.mat([[k ** i for i in order_range] for k in range(-half_window,
                                                                 half_window + 1)])
        m = np.linalg.pinv(b).A[deriv] * rate ** deriv * math.factorial(deriv)
        # pad the signal at the extremes with
        # values taken from the signal itself
        firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
        lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        return np.convolve(m[::-1], y, mode='valid')

    @staticmethod
    def convertargs(args):
        """ Method to convert a tuple of arguments into a dictionary of arguments for the specified
            method. The first item of the tuple must be the method name. The remaining items are the
            arguments to the method in the order the method lists. To see which arguments a method
            takes call getargs(method) or getargs() to list the arguments for all methods.

            Parameters
            ----------
            args : tuple
                Tuple containing the method as the first item and any arguments for that method in
                the order specified by the method.

            Returns
            -------
            Dictionary containing the converted arguments.

        """
        if len(args) == 0:
            raise Exception("Smoothing method must be given.")
        if args[0] not in Filter1D.methods:
            raise Exception("The smoothing method %s is not known, it must be one of: %s" % 
                            (args[0], str(Filter1D.methods)))
        keyval = deepcopy(getattr(Filter1D, args[0] + "_args"))
        keys = keyval.keys()
        for i, arg in enumerate(args):
            if i == 0:
                continue
            keyval[keys[i - 1]] = arg
        return dict(keyval)

    def run(self):
        """ Method to run the selected filter on the data

            Parameters
            ----------
            None

            Returns
            -------
            The smoothed spectrum
        """
        return getattr(self, self.method)(**getattr(self, self.method + "_args"))

def getargs(method=None):
    """ Method to report the keywords and default values for smoothing algorithms

        Parameters
        ----------
        method : str
            The name of the method to report the keywords and default values for. If no method is
            given then all methods are reported on.
            Default: None

        Returns
        -------
        None

    """
    if method is None:
        print "     arg           Default"
        for m in Filter1D.methods:
            print m
            for k, v in getattr(Filter1D, m + "_args").iteritems():
                print "    %s   %s" % (k.ljust(14), str(v))
        return
    if method in Filter1D.methods:
        print "     arg           Default"
        for k, v in getattr(Filter1D, method + "_args").iteritems():
            print "     %s   %s" % (k.ljust(14), str(v))
        return
    print "Method %s is not known. Available methods are: %s" % (method, Filter1D.methods)


