""" .. _polycontinuum:

    PolyFit --- Continuum subtraction using a polynomial fit.
    ---------------------------------------------------------

    Module for doing polynomial fitting to the continuum of a
    1D spectrum.

"""

import numpy as np
import numpy.ma as ma

from admit.util import stats
from admit.util.AdmitLogging import AdmitLogging as logging


class PolyFit(object):
    """ Class which calculates the continuum of a 1D spectrum by
        fitting a polynomial to the continuum channels. The algorithm
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
            - deg : int, the degree of polynomial to use, Defualt: 1
        """
        # set up the data elements
        args = {"x": self.x,
                "y" : ma.fix_invalid(self.y,fill_value=0.0),
                # reverse the weights since a masked array uses True for good values
                # and UnivariateSpline needs a number. The reversal translates the
                # True values to False, which are then interpreted as 0.0 
                "w" : -self.y.mask}

        # get the given arguments
        search = False
        noise = None
        chisq = 3.0
        if "search" in keyval:
            search = keyval["search"]
        if "noise" in keyval:
            noise = keyval["noise"]
        if "chisq" in keyval:
            maxchisq = keyval["chisq"]
        for arg in ["deg"]:
            if arg in keyval:
                args[arg] = keyval[arg]
        # if searching for the best fit
        # limited to 3rd order as 4th and 5th order could fit weak wide lines 
        if search:
            chisq = {0:1000.,
                     1:1000.,
                     2:1000.,
                     3:1000.}
            # iterate over each possible order
            for order in chisq:
                args["deg"] = order
                
                pfit = np.polyfit(**args)
                if len(pfit) == 1:
                    numpar = 1
                else:
                    # find the number of free parameters
                    # note that if a coefficient is << the max coefficient
                    # it is not considered a free parameter as it has very little affect on the fit
                    numpar = 0
                    mxpar = max(abs(pfit))
                    for i in range(len(pfit)):
                        if abs(mxpar/pfit[i]) < 1000.:
                            numpar += 1
                fit = np.polyval(pfit,self.x)
                chisq[order] = (stats.reducedchisquared(self.y, fit, numpar, noise), numpar)
            # find the base fit, based on number of free parameters and chisq
            mv = 1000.
            order = 0
            for k in chisq:
                if chisq[k][0] < mv and (mv - chisq[k][0]) / mv > 0.2:
                    mv = chisq[k][0]
                    order = k
            if mv > maxchisq:
                logging.warning("No good fit for continuum found")
                return None
            args["deg"] = mv
            logging.info("Using polynomial fit of order %i with chi^2 of %f" % (order, mv))
            # do the final fit
            pfit = np.polyfit(**args)
            fit = np.polyval(pfit,self.x)
        else:
            # do the fit with the given parameters
            pfit = ma.polyfit(**args)
            fit = np.polyval(pfit,self.x)

        return fit
