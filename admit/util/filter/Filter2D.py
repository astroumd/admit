""" Filter2D --- 2-dimensional spectral filtering.
    ----------------------------------------------

    This module defines the 2D filter methods.
"""

import numpy as np
import math
try:
  import scipy.signal
except:
  print "WARNING: No scipy; Filter2D utility cannot function."

class Filter2D(object):
    """ This class defines and runs 2D spectral filters. The currently available
        filters are Gaussian, Hanning, Triangle, Welch, Boxcar, and Savitzky 
        Golay. The output spectrum will be of the same length as the input 
        spectrum, however some edge channels may be zeroed by some methods, 
        depending on the input parameters.

        Parameters
        ----------
        spec : numpy array
            2D numpy array of the input spectrum (just the amplitudes).

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
    def __init__(self, data, method, **keyval):
        if len(data.shape) != 2:
            raise Exception("Spectrum is not 2D but you are trying to use a 2D filter.")
        self.data = data
        #self.len = self.spec.shape[0]
        self.methods = ["boxcar", 
                        "gaussian", 
                        "welch", 
                        "hanning", 
                        "triangle", 
                        "savgol"]
        # keywords for the different algorithms
        self.boxcar_args =   {"width" : 5}
        self.gaussian_args = {"width" : 9}
        self.welch_args =    {"width" : 7}
        self.hanning_args =  {"width" : 7}
        self.triangle_args = {"width" : 7}
        self.savgol_args =   {"window_size" : 11, 
                              "order"       : 3, 
                              "deriv"       : None}
        self.method = self.checkmethod(method)

        for k, v in keyval.iteritems():
            try:
                a = getattr(self, method + "_args")[k]
            except:
                raise Exception("Unknown input %s for smoothing." % (k))
            if type(a) != type(v):
                raise Exception("Cannot change the type of an attribute. %s must be a %s not a %s." % (k, type(a), type(v)))
            getattr(self, method + "_args")[k] = v

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

    def radius(self, x , y, width):
        """ Method to calculate the radius of a point in the kernel

            Parameters
            ----------
            x : float
                The x coordinate

            y : float
                The y coordinate

            width : int
                The width of the Gaussian being used

            Returns
            -------
            Float containing the radius to the point

        """
        return math.sqrt(math.pow(x - width / 2.0, 2) + math.pow(y - width / 2.0, 2))

    def boxcar(self, width):
        r""" Method to apply a boxcar filter to a spectrum. The filter for point x[i]
            is defined as:

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
                The smoothed image, (width - 1)/2 edge channels will be zeroed
        """
        kernel = np.zeros((width, width))
        for x in range(width):
            for y in range(width):
                kernel[y][x] = 1.0
        kernel /= kernel.sum()
        return scipy.signal.convolve2d(self.data, kernel, boundary="symm")

    def gaussian(self, width):
        r""" Method to apply a Gaussian filter to a spectrum. The filter for 
            point x[i] is defined as:

            .. math::

                x[i] = \frac{3}{N} \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] e^{-\frac{1}{2}\left(\frac{n-(N-1)/2}{\sigma(N-1)/2}\right)^2}

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the gaussian for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed image, (width - 1)/2 edge channels will be zeroed
        """
        kernel = np.zeros((width, width))
        for x in range(width):
            for y in range(width):
                kernel[y][x] = math.exp(-0.5 * pow(((self.radius(float(x), 
                                        float(y), float(width)) - ((float(width) - 1.0) /
                                        2.0)) / (0.2 * (float(width) - 1.0) / 2.0)), 2))
        kernel /= kernel.sum()
        return scipy.signal.convolve2d(self.data, kernel, boundary="symm")

    def welch(self, width):
        r""" Method to apply a Welch filter to a spectrum. The filter for point x[i]
            is defined as:

            .. math::

                x[i] = \frac{3}{2(N-1)} \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] \left(1 - \left(\frac{n - \frac{N-1}{2}}{\frac{N-1}{2}}\right)^2\right)

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the function for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed image, (width - 1)/2 edge channels will be zeroed
        """
        width += 2    # must add 2 to get the proper width
        kernel = np.zeros((width, width))
        for x in range(width):
            for y in range(width):
                kernel[y][x] = (1 - pow((self.radius(float(y), float(x), 
                                float(width)) - (float(width - 1) / 2.0)) / (float(width - 1) / 2.0), 2))
        kernel /= kernel.sum()
        return scipy.signal.convolve2d(self.data, kernel, boundary="symm")

    def hanning(self, width):
        r""" Method to apply a Hanning filter to a spectrum. The filter for 
            point x[i] is defined as:

            .. math::

                x[i] = \frac{2}{N-1} \sum_{n=0}^{N} x[i + n - \frac{N - 1}{2}] 0.5 \left(1 - \cos\left(\frac{2\pi n}{N-1}\right)\right)

            where N is the width of the filter.

            Parameters
            ----------
            width : int
                The number of channels to span with the function for each 
                iteration, must be odd

            Returns
            -------
            numpy array
                The smoothed image, (width - 1)/2 edge channels will be zeroed
        """
        width += 2    # must add 2 to get the proper width
        kernel = np.zeros((width, width))
        for x in range(width):
            for y in range(width):
                kernel[y][x] = 0.5 * (1.0 - math.cos((2.0 * math.pi * 
                                      self.radius(float(y), float(x), 
                                                  float(width))) / float(width - 1)))
        kernel /= kernel.sum()
        return scipy.signal.convolve2d(self.data, kernel, boundary="symm")

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
                The smoothed image, (width - 1)/2 edge channels will be zeroed
        """
        kernel = np.zeros((width, width))
        for x in range(width):
            for y in range(width):
                kernel[y][x] = (1.0 - abs((self.radius(float(y), float(x),
                                float(width)) - (float(width - 1) / 2.0)) / (float(width) / 2.0)))
        kernel /= kernel.sum()
        return scipy.signal.convolve2d(self.data, kernel, boundary="symm")

    def savgol(self, window_size, order, deriv=None):
        """ Method to apply a Savitzky-Golay filter to a 2D image.

            Parameters
            ----------
            window_size : int
                the size of the window. Must be an odd integer number.

            order : int
                the order of the polynomial used in the filtering.
                Must be less then `window_size` - 1.

            deriv: int
                the order of the derivative to compute (default = None means only 
                smoothing)

            Returns
            -------
            numpy array
                The smoothed image, (width - 1)/2 edge channels will be zeroed

        """
        # number of terms in the polynomial expression
        n_terms = (order + 1) * (order + 2) / 2.0

        if window_size % 2 == 0:
            raise ValueError('window_size must be odd')

        if window_size ** 2 < n_terms:
            raise ValueError('order is too high for the window size')

        half_size = window_size // 2

        # exponents of the polynomial.
        # p(x, y) = a0 + a1*x + a2*y + a3*x^2 + a4*y^2 + a5*x*y + ...
        # this line gives a list of two item tuple. Each tuple contains
        # the exponents of the k-th term. First element of tuple is for x
        # second element for y.
        # Ex. exps = [(0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2), ...]
        exps = [(k - n, n) for k in range(order + 1) for n in range(k + 1)]

        # coordinates of points
        ind = np.arange(-half_size, half_size + 1, dtype=np.float64)
        dx = np.repeat(ind, window_size)
        dy = np.tile(ind, [window_size, 1]).reshape(window_size ** 2,)

        # build matrix of system of equation
        A = np.empty((window_size ** 2, len(exps)))
        for i, exp in enumerate(exps):
            A[:, i] = (dx ** exp[0]) * (dy ** exp[1])

        # pad input array with appropriate values at the four borders
        new_shape = self.data.shape[0] + 2 * half_size, self.data.shape[1] + 2 * half_size
        Z = np.zeros((new_shape))
        # top band
        band = self.data[0, :]
        Z[:half_size, half_size:-half_size] = \
            band - np.abs(np.flipud(self.data[1:half_size + 1, :]) - band)
        # bottom band
        band = self.data[-1, :]
        Z[-half_size:, half_size:-half_size] = \
            band + np.abs(np.flipud(self.data[-half_size - 1:-1, :]) - band)
        # left band
        band = np.tile(self.data[:, 0].reshape(-1, 1), [1, half_size])
        Z[half_size:-half_size, :half_size] = \
            band - np.abs(np.fliplr(self.data[:, 1:half_size + 1]) - band)
        # right band
        band = np.tile(self.data[:, -1].reshape(-1, 1), [1, half_size])
        Z[half_size:-half_size, -half_size:] =  \
            band + np.abs(np.fliplr(self.data[:, -half_size - 1:-1]) - band)
        # central band
        Z[half_size:-half_size, half_size:-half_size] = self.data

        # top left corner
        band = self.data[0, 0]
        Z[:half_size, :half_size] = \
            band - np.abs(np.flipud(np.fliplr(self.data[1:half_size + 1,
                                                        1:half_size + 1])) - band)
        # bottom right corner
        band = self.data[-1, -1]
        Z[-half_size:, -half_size:] = \
            band + np.abs(np.flipud(np.fliplr(self.data[-half_size - 1:-1,
                                                        -half_size - 1:-1])) - band)

        # top right corner
        band = Z[half_size, -half_size:]
        Z[:half_size, -half_size:] = \
            band - np.abs(np.flipud(Z[half_size + 1:2 * half_size + 1,
                                      -half_size:]) - band)
        # bottom left corner
        band = Z[-half_size:, half_size].reshape(-1, 1)
        Z[-half_size:, :half_size] = \
            band - np.abs(np.fliplr(Z[-half_size:, half_size + 1:2 * half_size + 1]) - band)

        # solve system and convolve
        if deriv is None:
            m = np.linalg.pinv(A)[0].reshape((window_size, -1))
            return scipy.signal.fftconvolve(Z, m, mode='valid')
        elif deriv == 'col':
            c = np.linalg.pinv(A)[1].reshape((window_size, -1))
            return scipy.signal.fftconvolve(Z, -c, mode='valid')
        elif deriv == 'row':
            r = np.linalg.pinv(A)[2].reshape((window_size, -1))
            return scipy.signal.fftconvolve(Z, -r, mode='valid')
        elif deriv == 'both':
            c = np.linalg.pinv(A)[1].reshape((window_size, -1))
            r = np.linalg.pinv(A)[2].reshape((window_size, -1))
            return scipy.signal.fftconvolve(Z, -r, mode='valid'), scipy.signal.fftconvolve(Z, -c, mode='valid')

    def run(self):
        """ Method to run the selected filter on the data

            Parameters
            ----------
            None

            Returns
            -------
            The smoothed image
        """
        return getattr(self, self.method)(**getattr(self, self.method + "_args"))
