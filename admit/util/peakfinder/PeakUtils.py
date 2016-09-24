""" .. _peakutils:

    PeakUtils --- A peak finding algorithm.
    ---------------------------------------

    A version of the PyPi PeakUtils, converted from Python3.4 to Python2.7.
"""

# The MIT License (MIT)
#
# Copyright (c) 2014 Lucas Hermann Negri
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from __future__ import division
from __future__ import absolute_import
import numpy as np
import math
import types
import matplotlib.pyplot as plt
try:
  from scipy import optimize
  import scipy.linalg as LA
except:
  print "WARNING: No scipy; PeakUtils utility cannot function."



class PeakUtils(object):
    """ PeakUtils peak finding algorithm

        Parameters
        ----------
        spec : List or numpy array
            The spectrum to be analyzed.

        x : List or numpy array, optional
            The x co-ordinates for the spectrum.
            Default = None.

        kwarg : Dict
            Any additional arguments, see the Attributes list for a complete
            listing.

        Attributes
        ----------
        spec : numpy array
            The spectrum to be analyzed.

        x : numpy array
            The x co-ordinates of the spectrum.

        thres : float
            Threshold for detecting a peak/valley. The absolute value of the intensity
            must be above this value. Default: 0.0.

        min_dist : int
            The minimum distance between peaks in channels.
            Deafult: 5.

        profile : str
            The spectral line profile to use when refining the fits. Choices are
            "gaussian" and "lorentzian".
            Default: "gaussian".

        width : int
            The number of channels on either side of a peak to use when refining
            the fit.
            Default: 10.

        basedeg : int
            Degree of the polynomial that will estimate the data baseline.
            Default: 3.

        baseiter : int
            The maximum number of iterations to perform when trying to fit the
            baseline.
            Default: 100.

        basetol : float
            Tolerance to use when comparing the difference between the current
            fit coefficient and the ones from the last iteration.
            Default: 1e-3.

        dobase : boolean
            Whether or not to do baseline/continuum subtraction.
            Default: False.
    """
    thres = 0.0
    min_dist = 1
    profile = "gaussian"
    width = 10
    basedeg = 3
    baseiter = 100
    basetol = 1e-3
    dobase = False
    def __init__(self,spec,x = None,**kwarg):
        if type(spec) == types.ListType:
            self.spec = np.array(spec,dtype=float)
        else:
            self.spec = spec.astype(float)
        if x == None:
            self.x = np.arange(float(spec.shape[0]))
        else:
            if type(x) == types.ListType:
                self.x = np.array(x,dtype=float)
            else:
                self.x = x.astype(float)
        for k,v, in kwarg.iteritems():
            # ingore any attributes we don't have
            if hasattr(self,k):
                if type(getattr(self,k)) != type(v):
                    raise Exception,"Cannot change the type of a variable in PeakUtils. %s is of type %s, not %s." % (k,type(getattr(self,k)),type(v))
                setattr(self,k,v)
        #print self.min_dist

    def find(self):
        """ Method to find any peaks in the spectrum. A baseline will be subtracted first if requested.

            Parameters
            ----------
            None

            Returns
            -------
            numpy array of floats
                containing the locations of the peaks
        """
        # subtract a baseline if needed
        #fig = plt.figure(20)
        #x = np.arange(len(self.spec))
        #ax1 = fig.add_subplot(1,1,1)
        #ax1.set_title("BEFORE")
        #ax1.plot(x,self.spec,"-")
        #plt.show()

        if self.dobase:
            self.baseline(self.basedeg,self.baseiter,self.basetol)
        #fig2 = plt.figure(21)
        #x = np.arange(len(self.spec))
        #ax2 = fig2.add_subplot(1,1,1)
        #ax2.set_title("AFTER")
        #ax2.plot(x,self.spec,"-")
        #plt.show()

        # do an initial cut
        ind = self.indexes(self.thres,self.min_dist)
        # now refine the peaks
        if "gauss" in self.profile:
            fit = "gaussian_fit"
        else:
            fit = "lorentzian_fit"
        refined = self.interpolate(ind,self.width,fit)
        return refined

    def indexes(self,thres=0.0, min_dist=5):
        """Peak detection routine.

            Finds the peaks in *y* by taking its first order difference. By using
            *thres* and *min_dist* parameters, it is possible to reduce the number of
            detected peaks.

            Parameters
            ----------
            thres : float
                Threshold for detecting a peak/valley. The absolute value of the intensity
                must be above this value. Default: 0.0

            min_dist : int
                Minimum distance between each detected peak. The peak with the highest
                amplitude is preferred to satisfy this constraint.

            Returns
            -------
            ndarray
                Array containing the indexes of the peaks that were detected
        """
        #thres *= np.max(self.spec) - np.min(self.spec)

        # find the peaks by using the first order difference
        dy = np.diff(self.spec)
        peaks = np.where((np.hstack([dy, 0.]) < 0.)
                         & (np.hstack([0., dy]) > 0.)
                         & (np.absolute(self.spec) > thres))[0]
        #print "\n\n",peaks,peaks.size,"\n\n"
        if peaks.size > 1 and min_dist > 1:
            highest = peaks[np.argsort(self.spec[peaks])][::-1]
            rem = np.ones(self.spec.size, dtype=bool)
            rem[peaks] = False

            for peak in highest:
                if not rem[peak]:
                    sl = slice(max(0, peak-min_dist), peak+min_dist+1)
                    rem[sl] = True
                    rem[peak] = False

            peaks = np.arange(self.spec.size)[~rem]

        #print "\n\n",peaks,peaks.size,"\n\n"

        return peaks


    def centroid(self,chans=[0,-1]):
        """ Computes the centroid for the specified data.

            Parameters
            ----------
            chans : list
                The indexes to start and end at.
                Default: [0,-1]

            Returns
            -------
            float
                Centroid of the data.
        """
        ydata = self.spec[chans[0]:chans[1]+1]
        xdata = self.x[chans[0]:chans[1]+1]
        return np.sum(xdata*ydata)/np.sum(ydata)


    def gaussian(self,x, ampl, center, dev):
        """Computes the Gaussian function.

            Parameters
            ----------
            x : float
                Point to evaluate the Gaussian for.

            ampl : float
                Amplitude.

            center : float
                Center.

            dev : float
                Width.

            Returns
            -------
            float
                Value of the specified Gaussian at *x*
        """
        return ampl * np.exp(-(x-center)**2 / (2*dev**2))


    def gaussian_fit(self,chans=[0,-1]):
        """ Performs a Gaussian fitting of the specified data.

            Parameters
            ----------
            chans : list
                The indexes to start and end at.
                Default: [0,-1]

            Returns
            -------
            ndarray
                Parameters of the Gaussian that fits the specified data
        """
        ydata = self.spec[chans[0]:chans[1]+1]
        xdata = self.x[chans[0]:chans[1]+1]
        initial = [np.max(ydata), xdata[0], (xdata[1]-xdata[0])*5]
        _3to2list = list(optimize.curve_fit(self.gaussian, xdata, ydata, initial))
        params, _, = _3to2list[:1] + [_3to2list[1:]]
        return params[1]

    def lorentzian(self,x, ampl, center, width):
        """Computes the Lorentzian function.

            Parameters
            ----------
            x : float
                Point to evaluate the Gaussian for.

            ampl : float
                Amplitude.

            center : float
                Center.

            width : float
                Width.

            Returns
            -------
            float
                Value of the specified Gaussian at *x*
        """
        return (ampl/math.pi) * (width/2.0)/(math.pow(x-center,2) + math.pow(width/2.0,2))


    def laurentzian_fit(self,chans=[0,-1]):
        """ Performs a Lorentzian fitting of the specified data.

            Parameters
            ----------
            chans : list
                The indexes to start and end at.
                Default: [0,-1]

            Returns
            -------
            ndarray
                Parameters of the Lorentzian that fits the specified data
        """
        ydata = self.spec[chans[0]:chans[1]+1]
        xdata = self.x[chans[0]:chans[1]+1]
        initial = [np.max(ydata), xdata[0], (xdata[1]-xdata[0])*5]
        _3to2list = list(optimize.curve_fit(self.lorentzian, xdata, ydata, initial))
        params, _, = _3to2list[:1] + [_3to2list[1:]]
        return params[1]

    def interpolate(self, ind=None, width=10, func="gaussian_fit"):
        """ Tries to enhance the resolution of the peak detection by using
            Gaussian fitting, centroid computation or an arbitrary function on the
            neighborhood of each previously detected peak index.

            Parameters
            ----------
            ind : ndarray
                Indexes of the previously detected peaks. If None, indexes() will be
                called with the default parameters.

            width : int
                Number of points (before and after) each peak index to pass to *func*
                in order to increase the resolution in *x*.

            func : function(x,y)
                Function that will be called to detect an unique peak in the x,y data.

            Returns
            -------
            ndarray :
                Array with the adjusted peak positions (in *x*)
        """
        if ind is None:
            ind = indexes(self.spec)

        out = []
        for i in ind:
            try:
                fit = getattr(self,func)([i-width,i+width+1])
                out.append(fit)
            except:
                pass

        return np.array(out)

    def baseline(self,deg=3, max_it=100, tol=1e-3):
        """ Computes the baseline of a given data.

            Iteratively performs a polynomial fitting in the data to detect its
            baseline. At every iteration, the fitting weights on the regions with
            peaks is reduced to identify the baseline only.

            Parameters
            ----------
            deg : int
                Degree of the polynomial that will estimate the data baseline. A low
                degree may fail to detect all the baseline present, while a high
                degree may make the data too oscillatory, especially at the edges.

            max_it : int
                Maximum number of iterations to perform.

            tol : float
                Tolerance to use when comparing the difference between the current
                fit coefficient and the ones from the last iteration. The iteration
                procedure will stop when the difference between them is lower than
                *tol*.

            Returns
            -------
            ndarray
                Array with the baseline amplitude for every original point in *y*
        """
        order = deg+1
        coeffs = np.ones(order)

        # try to avoid numerical issues
        cond = math.pow(self.spec.max(), 1./order)
        x = np.linspace(0., cond, self.spec.size)
        base = self.spec.copy()

        vander = np.vander(x, order)
        vander_pinv = LA.pinv2(vander)

        for _ in xrange(max_it):
            coeffs_new = np.dot(vander_pinv, self.spec)

            if LA.norm(coeffs_new-coeffs) / LA.norm(coeffs) < tol:
                break

            coeffs = coeffs_new
            base = np.dot(vander, coeffs)
            self.spec = np.minimum(self.spec, base)

        return base

    def scale(self,x, new_range=(0., 1.), eps=1e-9):
        """ Changes the scale of an array

            Parameters
            ----------
            x : ndarray
                1D array to change the scale (remains unchanged)

            new_range : tuple (float, float)
                Desired range of the array

            eps: float
                Numerical precision, to detect degenerate cases (for example, when
                every value of *x* is equal)

            Returns
            -------
            ndarray
                Scaled array
            tuple (float, float)
                Previous data range, allowing a rescale to the old range
        """
        assert new_range[1] >= new_range[0]
        range_ = (x.min(), x.max())

        if (range_[1] - range_[0]) < eps:
            mean = (new_range[0] + new_range[1]) / 2.0
            xp = np.full(x.shape, mean)
        else:
            xp = (x - range_[0])
            xp *= (new_range[1] - new_range[0]) / (range_[1] - range_[0])
            xp += new_range[0]

        return xp, range_
