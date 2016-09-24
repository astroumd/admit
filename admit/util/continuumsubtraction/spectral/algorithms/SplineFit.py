""" .. _splinecontinuum:

    SplineFit --- Continuum subtraction using a spline fit.
    -------------------------------------------------------

    Module for doing spline fitting to the continuum of a 1D spectrum.

"""
import numpy as np

from admit.util.AdmitLogging import AdmitLogging as logging

try:
    from scipy.interpolate import UnivariateSpline
except:
    print "WARNING: No scipy; SplineFit fitter cannot function."


class SplineFit(object):
    """ Class which calculates the continuum of a 1D spectrum by
        fitting a spline to the continuum channels. The algorithm
        can be controlled by arguments to the run() method.

        Parameters
        ----------
        x : numpy array
            An array containing the x coordinates.

        y : masked array
            A masked array containing the y coordinates with any
            strong emission masked.

        Attributes
        ----------
        None
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def run(self,**keyval):
        """ Method to calculate the continuum from the given masked spectrum.
            If search=True is given as an argument then the algorithm will
            iterate through the different order splines to find the best fit,
            based on noise level.

            Parameters
            ----------
            keyval : dictionary
                Dictionary containing the keyword value pair arguments

            Returns
            -------
            numpy array containing the best fit continuum

            Notes
            -----
            Arguments for the run method:

            - search : bool, whether or not to search for the best fit. Default: False
            - bbox : array_like, 2-sequence specifying the boundary of the approximation
              interval. If None (default), ``bbox=[x[0], x[-1]]``.
            - k : int 1 < k <= 5, the degree of spline smoothing to use, Defualt: 3
            - s : float or None
              Positive smoothing factor used to choose the number of knots.  Number
              of knots will be increased until the smoothing condition is satisfied::
 
                sum((w[i] * (y[i]-spl(x[i])))**2, axis=0) <= s
 
              If None (default), ``s = len(w)`` which should be a good value if
              ``1/w[i]`` is an estimate of the standard deviation of ``y[i]``.
              If 0, spline will interpolate through all data points.
            - ext : int or str
              Controls the extrapolation mode for elements
              not in the interval defined by the knot sequence.
  
                * if ext=0 or 'extrapolate', return the extrapolated value.
                * if ext=1 or 'zeros', return 0
                * if ext=2 or 'raise', raise a ValueError
                * if ext=3 of 'const', return the boundary value.
   
              The default value is 0.
            - check_finite : bool
              Whether to check that the input arrays contain only finite numbers.
              Disabling may give a performance gain, but may result in problems
              (crashes, non-termination or non-sensical results) if the inputs
              do contain infinities or NaNs.
              Default is False.

        """
        # set up the data elements
        args = {"x": self.x,
                "y" : self.y.data,
                # reverse the weights since a masked array uses True for good values
                # and UnivariateSpline needs a number. The reversal translates the
                # True values to False, which are then interpreted as 0.0 
                "w" : -self.y.mask}

        # get the given arguments
        search = False
        noise = None
        if "search" in keyval:
            search = keyval["search"]
        if "noise" in keyval:
            noise = keyval["noise"]
        if "chisq" in keyval:
            maxchisq = keyval["chisq"]
        for arg in ["bbox","k","s","ext","check_finite"]:
            if arg in keyval:
                args[arg] = keyval[arg]
        # if searching for the best fit
        # limited to 3rd order as 4th and 5th order could fit weak wide lines 
        if search:
            chisq = {1:1000.,
                     2:1000.,
                     3:1000.}
            # iterate over each possible order
            for k in chisq:
                args["k"] = k
                spl = UnivariateSpline(**args)
                fit = spl(self.x)
                chisq[k] = stats.reducedchisquared(self.y, fit, k + 1, noise)
            # find the best fit, if chisq values are close (<20%), then prefer the lowest order
            mv = 1000.
            order = 0
            for k in chisq:
                if chisq[k] < mv and (mv - chisq[k]) / mv > 0.2:
                    mv = chisq[k]
                    order = k
            # if we have a really poor fit then just give up
            if mv > maxchisq:
                logging.warning("No good fit for continuum found")
                return None
            args["k"] = order
            logging.info("Using fit of order %i with chi^2 of %f" % (order, mv))
            # do the final fit
            spl = UnivariateSpline(**args)
            fit = spl(self.x)
        else:
            # do the fit with the given parameters
            spl = UnivariateSpline(**args)
            fit = spl(self.x)
        return fit
