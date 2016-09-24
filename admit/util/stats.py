""" **stats** --- Statistics functions module.
    ------------------------------------------

    This module contains utility functions used for statistics in ADMIT.
"""

import numpy as np
import numpy.ma as ma


def rejecto1(data, f=1.5):
    """ reject outliers from a distribution
    using a hinges-fences style rejection,
    using a mean.
    
    Parameters
    ----------
    data : array

    f : float
        The factor f, such that only data is retained
        between mean - f*std and mean + f*std

    Returns
    -------
    returns: an array with only data between
    mean - f*std and mean + f*std
        
    """
    u = np.mean(data)
    s = np.std(data)
    newdata = [e for e in data if (u - f * s < e < u + f * s)]
    return newdata

def rejecto2(data, f=1.5):
    """ reject outliers from a distribution
        using a hinges-fences style rejection,
        using a median.

    Parameters
    ----------
    data : array

    f : float
        The factor f, such that only data is retained
        between median - f*std and median + f*std

    Returns
    -------
    returns: an array with only data between
    median - f*std and median + f*std
    """
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else 0.
    return data[s<f]

def mystats(data):
    """ return raw and robust statistics for a distribution

        Parameters
        ----------
        data : array 
            The data array for which the statistics is returned.

        Returns
        -------
        returns:   N, mean, std for the raw and robust resp.
    """
    m1 = data.mean()
    s1 = data.std()
    n1 = len(data)
    d = rejecto2(data)
    m2 = d.mean()
    s2 = d.std()
    n2 = len(d)
    return (n1,m1,s1,n2,m2,s2)
    
def robust(data,f=1.5):
    """return a subset of the data with outliers robustly removed
    data - can be masked
    """
    if type(data) == np.ndarray:
        d = np.sort(data)
    else:
        d = np.sort(data).compressed()
    n= len(d)
    n1 = n/4
    n2 = n/2
    n3 = (3*n)/4
    q1 = d[n1]
    q2 = d[n2]
    q3 = d[n3]
    d = q3-q1
    f1 = q1-f*d
    f3 = q3+f*d
    # median = np.median(d)
    # print "robust: Median: ", median
    # print "robust: n,Q1,2,3:",n,q1,q2,q3
    # print "robust: f1,f3:",f1,f3
    dm = ma.masked_outside(data,f1,f3)
    return dm

def reducedchisquared(data, model, numpar, noise=None):
    """ Method to compute the reduced chi squared of a fit to data.

        Parameters
        ----------
        data : array like
            The raw data the fit is based on, acceptable data types
            are numpy array, masked array, and list

        model : array like
            The fit to the data, acceptable data types are numpy array,
            masked array, and list. Must be of the same length as data,
            no error checking is done

        dof : int
            Number of free parameters (degrees of freedom) in the model

        noise : float
            The noise/uncertainty of the data

        Returns
        -------
        Float containing the reduced chi squared value, the closer to 1.0
        the better

    """
    if noise is None:
        chisq = np.sum((data - model) ** 2)
    else:
        chisq = np.sum(((data - model)/noise)**2)
    if isinstance(data, ma.masked_array):
        nu = data.count() - numpar
    elif isinstance(data, np.ndarray):
        nu = data.shape[0] - numpar
    else:
        nu = len(data) - numpar
    return chisq / nu


if __name__ == "__main__":
    np.random.seed(123)
    np.random.seed()
    n = 1000
    f = 1.5
    if False:
        a = np.random.normal(0.0,1.0,n)     # gaussian
        print "normal(0.0,1.0,%d)" % n
    else:
        a = np.random.random(n)             # uniform
        print "random(%d)" % n
    a1 = rejecto1(a,f)
    print "rejecto1: ",len(a1)
    a2 = rejecto2(a,f)
    print "rejecto2: ",len(a2)
    print "mystats:",mystats(a)
    ar = robust(a,f)
    #print "robust: ",len(ar),ar
    print "robust: len=",len(ar)
