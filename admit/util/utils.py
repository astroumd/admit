""" **utils** --- Generic (CASA-independent) utilities module.
    ----------------------------------------------------------

    This module contains utility functions that do NOT rely on CASA.
"""
import shutil
import os
import time
import tempfile
import fnmatch
import matplotlib
import numpy as np
import importlib
import math
import subprocess
from admit.util.Segments import Segments 

from admit.util.AdmitLogging import AdmitLogging as logging
import admit.version as version

# Sphinx crashes on scipy even when listed in autodoc_mock_imports.
try:
    from scipy.optimize import curve_fit
    import scipy
except:
    print "WARNING: No scipy; some utilities will not function."

ndarray = np.array(0)
# speed of light in km/s
c = 299792.458

ostype = None

# atomic weights (just an integer) for calculations in line finding
wts = {"He" : 4,
       "Li" : 6,
       "Be" : 9,
       "Ne" : 20,
       "Na" : 23,
       "Mg" : 24,
       "Al" : 27,
       "Si" : 28,
       "Cl" : 35,
       "Ar" : 40,
       "Ca" : 40,
       "Sc" : 45,
       "Ti" : 48,
       "Cr" : 52,
       "Mn" : 55,
       "Fe" : 56,
       "Co" : 59,
       "Ni" : 59,
       "Cu" : 63,
       "Zn" : 65,
       "H"  : 1,
       "D"  : 2,
       "B"  : 11,
       "C"  : 12,
       "N"  : 14,
       "O"  : 16,
       "F"  : 19,
       "P"  : 31,
       "S"  : 32,
       "K"  : 39,
       "V"  : 51
       }

# A common location for the linelist column headers and units.
# This is used by LineList_BDP and LineSegment_BDP, which we do not
# want to get out of sync!  LineSegment_BDP may in the future
# add columns, but it will always have at least these.

linelist_columns =  [
    "frequency", "uid", "formula", "name", "transition", 
    "velocity", "El", "Eu", "linestrength", "peakintensity", 
    "peakoffset", "fwhm", "startchan", "endchan", "peakrms", 
    "blend", "force"
]


linelist_units = [
    "GHz", "", "", "", "", 
    "km/s", "K", "K", "D^2", "Jy/beam", 
    "km/s", "km/s", "", "", "", 
    "",""
]

_admit_root = None

def admit_root(path = None):
    """ Return the root directory of the ADMIT environment

        Typically in ADMIT/etc there are files needed by certain functions
        and other TBD locations.
        For now we are using getenv(), but in deployment this may not
        be the case.

        Parameters
        ----------
        path : string
           Optional path appended to the ADMIT root

        Returns
        -------
        String containing the absolute address of the admit root directory,
        with the optional path appended
    """
    global _admit_root
    if _admit_root != None:  return _admit_root

    # try the old style developer environment first
    _admit_root = os.getenv("ADMIT")
    if _admit_root == None:
        # try the dumb generic way;  is that safe to reference from __file__ ???
        _admit_root = version.__file__.rsplit('/',2)[0]
        if _admit_root[0] != '/':
            logging.warning("ADMIT_ROOT is a relative address")
            # @tdodo shouldn't that be a fatal error
    # 
    print "_ADMIT_ROOT=",_admit_root
    if path == None:
        return _admit_root
    return _admit_root + '/' + path

def admit_dir(file, out=None):
    """ create the admit directory name from a filename

    This filename can be a FITS file (usually with a .fits extension
    or a directory, which would be assumed to be a CASA image or
    a MIRIAD image.

    If out is set and non-blank, this (+.admit) will be the output name, overriding
    file

    It can be an absolute or relative address

    x.fits    -> x.admit
    x.fits.gz -> x.admit
    x.admit   -> x.admit (+warning)
    x         -> x.admit
    """
    if out != None and len(out)>0:
        return out
    loc = file.rfind('.')
    ext = '.admit'
    if loc < 0:
        return file + ext
    else:
        if file[loc:] == ext:
            print "Warning: assuming a re-run on existing ",file
            return file
        if file[loc:] == '.gz':
            loc = file[:loc].rfind('.')
            if loc < 0:
                print "Warning: ill format short filename ",file
                return file
        return file[:loc] + ext

def assert_files(files):
    """Assert that files exist, if not, throw an exception

        Parameters
        ----------
        files : list
            Files to be checked

        Returns
        -------
        None
    """
    for f in files:
        if len(f) == 0: continue
        if not os.path.exists(f):
            raise Exception,"File %s does not exist" % f

#@TODO why do we have a wrapper for a one-line python library call?
# because the default is to fail if there are errors, we want to supress
# these, hence the convenience wrapper that automatically adds the
# error supression
def rmdir(dir):
    """ Remove a directory. Calls shutil.rmtree and errors are supressed

        Parameters
        ----------
        dir : str
            Directory to be deleted

        Returns
        -------
        None
    """
    shutil.rmtree(dir, ignore_errors=True)

def rm(file):
    """ Remove a file

        Parameters
        ----------
        file : str
            File to be deleted

        Returns
        -------
        None
    """
    try:
        os.remove(file)
    # if the file doesn't exist don't worry about it
    except OSError:
        pass

def remove(item):
    """ Remove a file or directory.

        The method determines if it is a file or directory and removes it
        appropriately.

        Parameters
        ----------
        item : str
            Item to be deleted

        Returns
        -------
        None
    """
    # if it is a file
    if(os.path.isfile(item)):
        rm(item)
    # if it is a directory
    elif(os.path.isdir(item)):
        rmdir(item)


def rename(item1, item2):
    """ Rename a file or directory, but ensuring the destination is removed first

        Parameters
        ----------
        item1 : string
            Source file/directory name
        item2 : string
            Destination file/directory name

        Returns
        -------
        None
    """
    # make sure the destination does not exist
    remove(item2)
    # rename the item
    shutil.move(item1, item2)

def getClass(typ, name, init=None):
    """ Get an instance of an ADMIT class

        Parameters
        ----------
        typ : str
            package name, e.g. 'at' or 'bdp', 'admit.' wil be prepended to this.

        name : str
            The name of the class to retrieve, must have proper capitalization

        init : dict
            Initialization parameters. Default: None

        Returns
        -------
        An instance of the requested class
    """
    # prepend admit to the name
    path  = "admit." + typ
    # import the module
    module = importlib.import_module(path)
    # Normally, "import admit" has brought the class names
    # up to the top level...
    #print "##getClass(%s,%s) got module %s" % (typ,name,module)
    if hasattr(module,name):
        if init is None:
            return getattr(module, name)()

    # ...However, when running dtdGenerator, new __init__.py files
    # are created and imported, but not yet promoted to the top
    # level, so we must check the original "unpromoted" class path.
    else:
       path  = "admit." + typ + "." + name
       #print "##trying getClass(%s)"
       module = importlib.import_module(path)
       if init is None:
    # get the class with default parameters
           return getattr(module, name)()

    # if init != None in both cases
    # get the class with the given parameters
    return getattr(module, name)(**init)

def add_new_bdp():
    """ Method to add a new BDP to the ADMIT infrastructure.
        Alternatively, the command line tool dtdGenerator can be used.

        Parameters
        ----------
        None

        Returns
        -------
        None
    """
    # import and run the dtdGenerator, it takes care of everything
    import admit.xmlio.dtdGenerator as dtd
    dtd.generate()

def add_new_at():
    """ Method to add a new AT to the ADMIT infrastructure.
        Alternatively, the command line tool dtdGenerator can be used.

        Parameters
        ----------
        None

        Returns
        -------
        None
    """
    # import and run the dtdGenerator, it takes care of everything
    import admit.xmlio.dtdGenerator as dtd
    dtd.generate()


def find_files(directory, pattern):
    """ Find files with a given pattern down a directory tree.  This is a
        generator function.

        Parameters
        ----------
        directory : str
            Root directory to start search
        pattern : str
            Pattern to match

        Returns
        --------
        list of file names

        Examples
        --------
        find_files(\'/tmp/a\', \'\*.fits\')


        See Also
        --------
        Admit.find_files() which works exclusively within the current admit tree

    """
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

def tmp_file(prefix, tmpdir='/tmp'):
    """ Create a temporary file in /tmp.

        Parameters
        ----------
        prefix : str
           starting name of the filename in <tmpdir>/<pattern>

        tmpdir

        Returns
        -------
        Unique filename
    """
    fd = tempfile.NamedTemporaryFile(prefix=prefix,dir=tmpdir,delete='false')
    name = fd.name
    fd.close()
    return name

def on_error_retry(exception, callback, timeout=2, timedelta=.1):
    """ A generic method for doing retries with timeout.

        Parameters
        ----------
        exception : Exception
            An Exception class to handle exceptions from the callback.
        callback : function
            The callback method to invoke
        timeout : float
            timeout in seconds before giving up. default: 2
        timedelta : float
            number of seconds to sleep before retries.  default: 0.1

        Examples
        --------
        >>> for retry in on_error_retry(SomeSpecificException, do_stuff):
        >>>     retry()

        @todo: a better reference should be given, per our discussion in mid Sepetember
        stolen from stackoverflow.
    """
    end_time = time.time() + timeout
    while True:
        try:
            yield callback
            break
        except exception:
            if time.time() > end_time:
                raise
            elif timedelta > 0:
                time.sleep(timedelta)


def freqtovel(freq, delta):
    """ Method to convert between offset frequency and offset velocity

        Parameters
        ----------
        freq : float
            The base frequency

        delta : float
            The change in frequency

        Returns
        -------
        The offset velocity (in km/s) corresponding to the frequency shift.

    """
    global c
    return c * (delta / freq)


def veltofreq(vel, freq):
    """ Method to convert between offset velocity and offset frequency

        Parameters
        ----------
        vel : float
            The offset velocity

        freq : float
            The base frequency

        Returns
        -------
        The offset frequency corresponding to the velocity shift.

    """
    global c
    return freq * (vel / c)


def undoppler(sky, vel):
    """ Method to convert from sky frequency to source rest frequency

        Parameters
        ----------
        sky : float, list, or numpy array
            The sky frequency

        vel : float
            The source vlsr in km/s

        Returns
        -------
        The input value converted to rest frequency, in the same form that the input
        was given.  If the the absolute value of the input velocity is less 
        than 1E-8 km/s (0.01 cm/s), it is assumed to be zero and 'sky' is 
        returned.
    """

    if abs(vel) < 1E-8: return sky

    global c
    # if it is a float or numpy array we can just do the math
    if isinstance(sky, float) or isinstance(sky, np.ndarray):
        return sky / (1.0 - (vel / c))
    # if it is a list then it has to be done entry by entry
    elif isinstance(sky, list):
        for f in range(len(sky)):
            sky[f] = undoppler(sky[f], vel)
        return sky
    else:
        raise Exception("Invalid type given for input data to undopper, must be of type float, list, or numpy array, %s was given." % (str(type(sky))))

def ztovrad(z):
    """ Convert (optical) z to the linear radio convention recession
        velocity
    """
    global c
    return c * z / (1.0+z)


def interpolatespectrum(spec, left=0.0, right=0.0):
    """ Method to interpolate over bad points in a spectrum. Bad points generally
        come from masked pixels in an image. On read in these show up as exactly 0.0
        or +/-inf, or nan in the spectrum. Edge channels that are bad are just
        converted to 0.0.

        Parameters
        ----------
        spec : numpy array
            The input spectrum to process

        left : float
            The value to assign bad edge channels to on the left side of the
            spectrum.
            Defualt: 0.0

        right : float
            The value to assign bad edge channels to on the right side of the
            spectrum.
            Defualt: 0.0

        Returns
        -------
        A numpy array with the same length as the input with nan values converted to
        iterpolated values between good points, and bad edge values.

    """
    # set all 0.0 values to NaN's
    spec[spec == 0.0] = np.nan
    # find out which ones are not NaN's
    not_nan = np.logical_not(np.isnan(spec))
    indices = np.arange(len(spec))
    # do the interpolation, ignoring all those that are NaN's
    return np.interp(indices, indices[not_nan], spec[not_nan], left=left, right=right)


def iscloseinE(v1, v2):
    """ Method to determine if two spectral lines are very close in energy

        Parameters
        ----------
        v1 : float
            Energy of first transition.

        v2 : float
            Energy of second transition

        Returns
        -------
        True/False whether or not the energies are very close

    """
    return (abs(v2 - v1) < 1.0) and (abs(((v2 + 0.0001) / (v1 + 0.0001)) - 1) < 0.01)

# deprecate this one in favor of 'equal'
def issameinfreq(f1, f2, relerror=0.000001):
    return equal(f1,f2,relerror)

def equal(f1, f2, relerror=0.000001):
    """ Determine if two numbers are identical within a relative margin

        Parameters
        ----------
        f1 : float
            first number

        f2 : float
            second number

        relerror : float
            The relative error to allow between the two numbers

        Returns
        -------
        True if the two numbers are near enough identical, False otherwise

    """
    if f1 == f2:
        return True
    if f2 != 0.0:
        df = abs((f1 - f2) / f2)
    elif f1 != 0.0:
        df = abs((f1 - f2) / f1)
    else:
        # f1==f2==0.0 should have been caught before
        print f1,f2
        raise Exception,"Can never happen.... really"
    
    if df <= relerror:
        return True
    return False


def rreplace(s, old, new, occurrence=1):
    """ Replace portion of a string (from the right side). Handy utility to
        change a filename extension, e.g. rreplace('a/b/c.fits', 'fits', 'im') -> 'a/b/c.im'

        Parameters
        ----------
        s : str
            The string to process

        old : str
            The substring to replace

        new : str
            Whet to replace the 'old' substring with

        occurrence : int
            The number of occurrences to replace
            Default: 1
    """
    li = s.rsplit(old, occurrence)
    return new.join(li)


def getplain(formula):
    """ Method to make a chemical formula more readable for embedding in filenames
        Examples:

        CH3COOHv=0     -> CH3COOH

        g-CH3CH2OH     -> CH3CH2OH

        (CH3)2COv=0    -> (CH3)2CO

        cis-CH2OHCHOv= -> CH2OHCHO

        g'Ga-(CH2OH)2  -> (CH2OH)2

        Parameters
        ----------
        formula : str
            The chemical formula to process

        Returns
        -------
        String of the more readable formula
    """
    pos = formula.find("-")
    if pos != -1:
        if not(-1 < formula.find("C") < pos or -1 < formula.find("N") < pos \
           or -1 < formula.find("O") < pos or -1 < formula.find("H") < pos):
            formula = formula[pos + 1:]
    pos = formula.find("v")
    if pos != -1:
        formula = formula[:pos]
    pos = formula.find("&Sigma")
    if pos != -1:
        return formula[:pos]
    formula = formula.replace(";","")
    return formula.replace("&","-")


def format_chem(form):
    """ Method to format a chemical formula for display, specifically adding
        subscripts and superscripts

        Parameters
        ----------
        formula : str
            The chemical formula, usually obtained from splatalogue

        Returns
        -------
        string containing the formatted formula

    """
    # the isotopes and their formatted form (latex-like)
    isotopes = {"13C":  "$^{13}$C",
                "12C":  "C",
                "16O":  "O",
                "17O":  "$^{17}$O",
                "18O":  "$^{18}$O",
                "14N":  "N",
                "15N":  "$^{15}$N",
                "6Li":  "$^6$Li",
                "7Li":  "$^7$Li",
                "28Si": "Si",
                "29Si": "$^{29}$Si",
                "30Si": "$^{30}$Si",
                "32S":  "S",
                "33S":  "$^{33}$S",
                "34S":  "$^{34}$S",
                "46Ti": "$^{46}$Ti",
                "47Ti": "$^{47}$Ti",
                "48Ti": "Ti",
                "49Ti": "$^{49}$Ti",
                "50Ti": "$^{50}$Ti",
                "54Fe": "$^{54}$Fe",
                "56Fe": "Fe",
                "57Fe": "$^{57}$Fe",
                "58Fe": "$^{58}$Fe",
                "24Mg": "Mg",
                "25Mg": "$^{25}$Mg",
                "26Mg": "$^{26}$Mg"
                }

    # look for any ')' and append any subscripts to it
    for i in range(len(form) - 1, -1):
        if form[i] == ")":
            factor = form[i + 1]
            form = form[:i] + "$_%s$" % (factor) + form[i + 1:]

    # look for isomers and format them
    # start with the back and loop over, that way we should catch all
    for k, v in isotopes.iteritems():
        form = form.replace(k, v)
    # there should be only single digit numbers now, multipliers for atoms
    inf = False
    for i in range(len(form) - 1, -1, -1):
        if form[i] == "$":
            if inf:
                inf = False
            else:
                inf = True
        if str.isdigit(form[i]) and not inf:
            pos = i
            form = form[:pos] + "$_%s$" % (form[i]) + form[pos + 1:]
    form = form.replace(";","")
    return form.replace("&","-")


def isotopecount(formula):
    """ Method to count the number of isotopes in a molecule

        Parameters
        ----------
        formula : str
            The chemical formula to analyze

        Returns
        -------
        An integer of the number of less common isotopes found
    """
    # less common isotopes
    isotopes = ["D",   # heavy H
               "13C",
               "17O",
               "18O",
               "15N",
               "6Li",
               "7Li",
               "29Si",
               "30Si",
               "33S",
               "34S",
               "46Ti",
               "47Ti",
               "49Ti",
               "50Ti",
               "54Fe",
               "57Fe",
               "58Fe",
               "25Mg",
               "26Mg"]

    # get rid of extra stuff
    form = formula.replace(" ", "")
    form = form.replace("{", "")
    form = form.replace("}", "")
    form = form.replace("^", "")
    form = form.replace("_", "")
    form = form.replace("(TopModel)", "")

    pos = form.find("-")
    if pos != -1:
        if not(-1 < form.find("C") < pos or -1 < form.find("N") < pos \
           or -1 < form.find("O") < pos or -1 < form.find("H") < pos):
            form = form[pos + 1:]
    pos = form.find("v")
    if pos != -1:
        form = form[:pos]

    # look for any "(" and ")" and add any additional atoms as needed
    pos = form.find("(")
    while pos != -1:
        epos = form.find(")")
        substr = form[pos + 1:epos]
        factor = form[epos + 1]
        if factor.isdigit():
            factor = form[epos + 1: epos + 3]
            if not factor.isdigit():
                factor = form[epos + 1]
        else:
            pos = form.find("(", pos + 1)
            continue
        factor = int(factor) - 1
        newstr = substr * factor
        form = form.replace("(", "", 1)
        form = form.replace(")%i" % (factor + 1), "", 1)
        form += newstr
        pos = form.find("(")
    # now look for any less common isotopes
    count = 0
    for i in isotopes:
        count += form.count(i)
    return count


def getmass(formula):
    """ Method to calculate the rough mass of a molecule

        Parameters
        ----------
        formula : str
            The chemical formula, usually obtained from splatalogue

        Returns
        -------
        int of the rough mass

    """
    mass = 0
    isotopes = {"13C":  13,
                "12C":  12,
                "16O":  16,
                "17O":  17,
                "18O":  18,
                "14N":  14,
                "15N":  15,
                "6Li":   6,
                "7Li":   7,
                "28Si": 28,
                "29Si": 29,
                "30Si": 30,
                "32S":  32,
                "33S":  33,
                "34S":  34,
                "46Ti": 46,
                "47Ti": 47,
                "48Ti": 48,
                "49Ti": 49,
                "50Ti": 50,
                "54Fe": 54,
                "56Fe": 56,
                "57Fe": 57,
                "58Fe": 58,
                "24Mg": 24,
                "25Mg": 25,
                "26Mg": 26
                }
    # get rid of extraneous characters
    form = formula.replace(" ", "")
    form = form.replace("{", "")
    form = form.replace("}", "")
    form = form.replace("^", "")
    form = form.replace("_", "")
    form = form.replace("(TopModel)", "")
    global wts
    pos = form.find("-")
    if pos != -1:
        if not(-1 < form.find("C") < pos or -1 < form.find("N") < pos \
           or -1 < form.find("O") < pos or -1 < form.find("H") < pos):
            form = form[pos + 1:]
    pos = form.find("v")
    if pos != -1:
        form = form[:pos]

    # look for any "(" and ")" and add any additional atoms as needed
    pos = form.find("(")
    while pos != -1:
        epos = form.find(")")
        substr = form[pos + 1:epos]
        factor = form[epos + 1]
        if factor.isdigit():
            factor = form[epos + 1: epos + 3]
            if not factor.isdigit():
                factor = form[epos + 1]
        else:
            pos = form.find("(", pos + 1)
            continue
        factor = int(factor) - 1
        newstr = substr * factor
        form = form.replace("(", "", 1)
        form = form.replace(")%i" % (factor + 1), "", 1)
        form += newstr
        pos = form.find("(")
    # look for isomers and remove them
    # start with the back and loop over, that way we should catch all
    while True:
        loc = -1
        key = None
        for k, v in isotopes.iteritems():
            l = form.rfind(k)
            if l > loc:
                loc = l
                key = k
        if loc < 0:
            break

        form = rreplace(form, key, "", 1)
        mass += isotopes[key]
    # there should be only single digit numbers now, multipliers for atoms
    for i in range(len(form)):
        pos = -1
        if str.isdigit(form[i]):
            pos = i
            factor = int(form[i])
            if form[i - 1].islower():
                substr = form[i - 2:i]
            else:
                substr = form[i - 1]
            form.replace(form[i], "", 1)
            form += substr * (factor - 1)
    for k, v in wts.iteritems():
        count = form.count(k)
        mass += count * v
        form = form.replace(k, "")
    return mass

def isexotic(species):
    """ Method to determine if a molecule contains an "exotic" atom. In
        this case an exotic atom is one that is uncommon, but possible to
        be detected in the right environment.

        Parameters
        ----------
        species : str
            The chemical formula for the molecule

        Returns
        -------
        True if the molecule contains an "exotic" element, False otherwise.

    """
    exotics = ["Al", "Cl", "Mg", "Mn", "F", "Li", "Na", "K", "Ti"]
    for i in exotics:
        if i in species:
            return True
    return False

def gaussian1D(x, intensity, center, fwhm):
    """ Method for generating a 1D gaussian, primarily by the line fitting routine

        Parameters
        ----------
        x : array like
            list of points to generate the gaussian for

        intensity : float
            intensity of the gaussian, arbitrary units

        center : float
            The center position (peak) of the gaussian in the same units as x

        fwhm : float
            FWHM of the gaussian in the same units as x.
            Recall FMWHM = 2*sqrt(2*ln(2)) sigma ~ 2.355 sigma for a gaussian
            with variance sigma.

        Returns
        -------
        a list of intensities for the gaussian, one for each entry in x
    """
    val = intensity * scipy.exp(-((x - center) ** 2) / (2 * ((fwhm / (2 * scipy.sqrt(2 * scipy.log(2)))) ** 2)))
    return val

def fitgauss1D(x, y, par=None, width=-1.0):
    """ Method for fitting a 1D gaussian to a spectral line

        Parameters
        ----------
        x: array like
            The x co-ordinates of the spectrum, note the center of
            the spectral line should be near 0.0 if possible

        y: array like
            The y co-ordinates (intensity) of the spectrum

        par: array like
            The initial guesses for the fit parameters, the fitter works best
            if the center parameter is near 0.0
            3 parameters:  PeakY, CenterX, FWHM.

        width: float 
            If positive, this is the assumed width (or step) in the x array,
            which is needed if only 1 point is given. Otherwise ignored.

        Returns
        -------
        A tuple containing the best fit parameters (as a list) and the covariance
        of the parameters (also as a list)
    """
    if len(x) == 3:
        logging.info("Gaussian fit attempted with only three points, look at the covariance for goodness of fit.")
    # if there are too few points to fit then just conserve the are of the channels to calculate the
    # parameters
    if len(x) < 3:
        logging.info("Gaussian fit attempted with fewer than three points (%d). Using conservation of area method to determine parameters." % len(x))
        params = fitgauss1Dm(x,y,dx=width)
        covar = [1000.] * len(params)
    else:
        try:
            params, covar = curve_fit(gaussian1D, x, y, p0=par)
        # if the covariance cannot be determined, just return the initial values
        except RuntimeError, e:
            if "Optimal" in str(e):
                params = par
                covar = [0] * len(par)
            # otherwise re-raise the exception
            else:
                raise
        # return the results
    return params, covar

def fitgauss1Dm(xdat, ydat, usePeak = False, dx = -1.0):
    """ gaussfit helper function
        this will get a reasonable gauss even if you only have 2 points
        assumes evenly spaced data in xdat, so it can extract a width.
        It can be used like fitgauss1D(), but uses the first three moments
        of the distribution to "match" that of a gauss. area preserving
        if you wish.
        If you set usePeak, it will pick the highest value in your data.
        Warning:   if you must fit negative profiles, be sure to rescale
        before you come into this routine.
    """
    if len(xdat) == 1:
        # special case, it will need dx
        if dx < 0.0:
            logging.critical("Cannot determine gaussian of delta function if width not given")
            raise
        return (ydat[0], xdat[0], dx)
    
    sum0 = sum1 = sum2 = peak = 0.0
    # the mean is given as the weighted mean of x
    for x,y in zip(xdat,ydat):
        if y>peak: peak = y
        sum0 = sum0 + y
        sum1 = sum1 + y*x
    xmean = sum1/sum0
    # re-center the data for a moment-2 calculation
    # @todo pos/neg
    xdat0 = xdat - xmean
    for x,y in zip(xdat0,ydat):
        sum2 = sum2 + y*x*x
    sigma = math.sqrt(abs(sum2/sum0))
    # equate the area under the histogram with the area under a gauss
    # to get the peak of the "matched" gauss
    dx = abs(xdat[1]-xdat[0])     # @todo   use optional "dx=None" ?
    if not usePeak:
        # pick the area preserving one, vs. the "real" peak
        # The area preserving one seems to be about 18% higher
        # but with a tight correllation
        peak = (sum0 * dx) / math.sqrt(2*sigma*math.pi)
    fwhm = 2.35482 * sigma

    return (peak, xmean, fwhm)

def setkey(obj, key, val):
    """ Method to set the key of an arbitrary class. The class must
        have an attribute named 'keys'. The existence and data type
        of the given key are checked and if it does not exist, or
        changes data type then an exception is raised.

        Parameters
        ----------
        obj : class instance
            The class whose key is being set

        key : str
            The name of the item to change

        val : varies
            The value to change key to

        Returns
        -------
        None

    """
    try:
        a = obj.keys[key]
    except:
        raise
    if type(obj.keys[key]) != type(val):
        raise Exception("Cannot change the type of a keyword. %s is a %s, not a %s"
                        % (key, str(type(obj.keys[key])), str(type(val))))
    obj.keys[key] = val

#
# needed for some casarun style scripts,
#
def casa_argv(argv):
    """ Processes casarun arguments into C-style argv list.

        Modifies the argv from a casarun script to a classic argv list
        such that the returned argv[0] is the casarun scriptname.

        Parameters
        ----------
        argv : list of str
            Argument list.

        Returns
        -------
        sargv
            Script name plus optional arguments

        Notes
        -----
        Does not depend on CASA being present.
    """
    if False:
        lines = os.popen("casarun -c","r").readlines()
        n = int(lines[len(lines)-1].strip())
    else:
        n = argv.index('-c') + 1
    return argv[n:]


#  For some variations on this theme, e.g.  time.time vs. time.clock, see
#  http://stackoverflow.com/questions/7370801/measure-time-elapsed-in-python
#
class Dtime(object):
    """ Class to help measuring the wall clock time between tagged events
        Typical usage:
        dt = Dtime()
        ...
        dt.tag('a')
        ...
        dt.tag('b')
    """
    def __init__(self, label=".", report=True):
        self.start = self.time()
        self.init = self.start
        self.label = label
        self.report = report
        self.dtimes = []
        dt = self.init - self.init
        if self.report:
            logging.timing("%s ADMIT " % self.label + str(self.start))
            logging.timing("%s BEGIN " % self.label + str(dt))

    def reset(self, report=True):
        self.start = self.time()
        self.report = report
        self.dtimes = []

    def tag(self, mytag):

        t0 = self.start
        t1 = self.time()
        dt = t1 - t0

        # get memory usage (Virtual and Resident) info
        mem = self.get_mem()
        if mem.size != 0 :
            dt = np.append(dt, mem)

        self.dtimes.append((mytag, dt))
        self.start = t1
        if self.report:
            logging.timing("%s " % self.label + mytag + "  " + str(dt))
        return dt

    def show(self):
        if self.report:
            for r in self.dtimes:
                logging.timing("%s " % self.label + str(r[0]) + "  " + str(r[1]))
        return self.dtimes

    def end(self):
        t0 = self.init
        t1 = self.time()
        dt = t1 - t0
        if self.report:
            logging.timing("%s END " % self.label + str(dt))
        return dt

    def time(self):
        """ pick the actual OS routine that returns some kind of timer
        time.time   :    wall clock time (include I/O and multitasking overhead)
        time.clock  :    cpu clock time
        """
        return np.array([time.clock(), time.time()])

    def get_mem(self):
        """ Read memory usage info from /proc/pid/status
            Return Virtual and Resident memory size in MBytes.
        """
        global ostype
        
        if ostype == None:
            ostype = os.uname()[0].lower()
            logging.info("OSTYPE: %s" % ostype)
            
        scale = {'MB': 1024.0}
        lines = []
        try:
            if ostype == 'linux':
                proc_status = '/proc/%d/status' % os.getpid()          # linux only
                # open pseudo file  /proc/<pid>/status
                t = open(proc_status)
                # get value from line e.g. 'VmRSS:  9999  kB\n'
                for it in t.readlines():
                    if 'VmSize' in it or 'VmRSS' in it :
                        lines.append(it)
                t.close()
            else:
                proc = subprocess.Popen(['ps','-o', 'rss', '-o', 'vsz', '-o','pid', '-p',str(os.getpid())],stdout=subprocess.PIPE)
                proc_output = proc.communicate()[0].split('\n') 
                proc_output_memory = proc_output[1]
                proc_output_memory = proc_output_memory.split()
                
                phys_mem = int(proc_output_memory[0])/1204 # to MB 
                virtual_mem = int(proc_output_memory[1])/1024 
                
        except (IOError, OSError):
            if self.report:
                logging.timing(self.label + " Error: cannot read memory usage information.")

            return np.array([])

        # parse the two lines
    
        mem = {}
        if(ostype != 'darwin'):
            for line in lines:
                words = line.strip().split()
            #print words[0], '===', words[1], '===', words[2]
                
            # get rid of the tailing ':'
                key = words[0][:-1]

            # convert from KB to MB
                scaled = float(words[1]) / scale['MB']
                mem[key] = scaled
        else:
            mem['VmSize'] = virtual_mem
            mem['VmRSS']  = phys_mem


        return np.array([mem['VmSize'], mem['VmRSS']])

def get_references(filename):
    """
    Read a *references* file , which contain two columns,
    one with frequencies (or any float), one with line (references),
    a string. They are returned as a dictionary {   freq:line, ... }
    to be used for plotting references in e.g. APlot.makespec()

    Lines starting with the usual comment symbol '#' are skipped
    Blank lines are skipped
    Duplicate entries are skipped

    Used by e.g. LineID_AT and passed to APlot.makespec()

    It is recommended that the filename is relative to $ADMIT,
    e.g. "etc/co_lines.tab", as for an absolute filename reference
    the ADMIT product is not formally portable.
    """
    ref = {}
    if filename == "": return ref
    if filename[0] == os.sep:
        lines = open(filename,"r").readlines()
    else:
        lines = open(admit_root()+os.sep+filename,"r").readlines()
        
    for line in lines:
        if line[0] == '#': continue
        w = line.strip().split()
        if len(w) > 1:
            f = float(w[0])
            if ref.has_key(f):
                print "Warning: duplicate key at reference ",f
                continue
            ref[f] = w[1]
    return ref

def merge(a, b):
    """Merge two overlapping segments together. Segments are given
       as a two item list of the end points.
       **There is no actually check that the input segments overlap or are continguous.**

        Parameters
       ----------
       a : two item list
            One of the segments to merge

        b : two item list
           The second segment to merge

       Returns
        -------
       list
          A list of the merged segment end points
    """
    # There is no check that the input segments overlap or are continguous.
    # make sure the segment indices are [min, max]
    a = [min(a[0], a[1]), max(a[0], a[1])]
    b = [min(b[0], b[1]), max(b[0], b[1])]
    # merge them together
    return [min(a[0], b[0]), max(a[1], b[1])]

def getBDP(file):
    """ Convenience method to convert a bdp file into a BDP object. It calls the BDPReader class to
        do the work.

        Parameters
        ----------
        file : str
            File name (including any relative or absolute path) of the bdp file to be parsed and 
            converted to a BDP object.

        Returns
        -------
        BDP object of appropriate type based on the given input file.
    """
    # only need to import the class for this method, so do it here rather than at the top of the
    # module
    import admit.xmlio.BDPReader as bdpr
    reader = bdpr.BDPReader(file)
    return reader.read()

def specingest(chan=None, freq=None, velocity=None, spec=None, file=None, separator=None, 
               restfreq=None, vlsr=None):
    """ Convenience method  to convert input data (either files or arrays) into a CubeSpectrum_BDP. 
        If files
        are used then then the columns containing the frequency and the intensity must be given
        (channel numbers are optional). Any number of files can be given, but all spectra must
        have the same length as they are assumed to come from the same data source. Blank lines
        and lines starting with a comment '#' will be skipped, additionally any line with too
        few columns will be skipped. If arrays are used an input then both the frequency and
        intensity must be specified (the channel numbers are optional). Both lists and numpy
        arrays are accepted as inputs. Multidimmensional arrays are supported with the following
        parameters:

        + A single frequency list can be given to cover all input spectra, otherwise the shape
          of the frequency array must match that of the spectra
        + A single channel list can be given to cover all input spectra, otherwise the shape
            of the channel array must match that of the spectra
        + All spectra must have the same length

        If a channel array is not specified then one will be constructed with the following
        parameters:

        + The channel numbers will start at 0 (casa convention)
        + The first entry in the spectrum will be considered the first channel, regardless of
          whether the frequency array increases or decreases.

        Additionally, if there is velocity axis, but no frequency axis, a frequency axis can
        be constructed by specifying a rest frequency (restfreq), and vlsr.

        The convert method will return a single CubeSpectrum_BDP instance holding all input spectra
        along with an image of each.

        Parameters
        ----------
        chan : array or int
            An array holding the channel numbers for the data, multidimmensional arrays are
            supported. If an integer is specified then it is the number of the column
            in the file which contains the channel numbers, column numbers are 1 based.
            Default: None

        freq : array
            An array holding the frequencies for the data, multidimmensional arrays are
            supported. If an integer is specified then it is the number of the column
            in the file which contains the frequencies, column numbers are 1 based.
            Default: None

        velocity : array
            An array holding the velocity for the data, multidimmensional arrays are
            supported. If an integer is specified then it is the number of the column
            in the file which contains the velcoties, column numbers are 1 based. If this
            parameter is specified then restfreq and vlsr must also be specified.
            Default: None

        spec : array
            An array holding the intesities of the data, multidimmensional arrays are supported.
            If an integer is specified then it is the number of the column in the file which
            contains the intensities, column numbers are 1 based.
            Default: None

        file : list or str
            A single file name or a list of file names to be read in for spectra.
            Default: None

        separator : str
            The column separator for reading in the data files.
            Default: None (any whitespace)

        restfreq : float
            The rest frequency to use to convert the spectra from velocity to frequency units.
            The rest frequency is in GHz.
            Default: None (no conversion done)

        vlsr : float
            The reference velocity for converting a velocity axis to frequency. The units are
            km/s. If this is not set then it is assumed that the vlsr is 0.0.
            Default: None

        Returns
        -------
        CubeSpectrum_BDP instance containing all of the inpur spectra.

    """
    # only need to import the class for this method, so do it here rather than at the top of the
    # module
    import admit.util.SpectrumIngest as si
    a = si.SpectrumIngest()
    return a.convert(chan, freq, velocity, spec, file, separator, restfreq, vlsr)

def parseversion(version):
    """ Method to parse a version string from an AT or a BDP to turn it into ints so it can
        be easily compared.

        Parameters
        ----------
        version : str
            The string to parse

        Returns
        -------
            Tuple containing the major, minor, and sub version numbers (all ints)

    """
    # split the string into the components
    parse = version.split(".")
    # if all three components are present
    if len(parse) == 3:
        major = int(parse[0])
        minor = int(parse[1])
        sub   = int(parse[2])
    # if only two are present
    elif len(parse) == 2:
        major = int(parse[0])
        minor = int(parse[1])
        sub   = 0
    # if only one is present
    elif len(parse) == 1:
        major = int(parse[0])
        minor = 0
        sub   = 0
    else:
        raise Exception("Improperly formatted version string, it must conatin 1, 2, or 3 ints.")

    return (major, minor, sub)

def compareversions(version1, version2):
    """ Method to compare two version numbers or strings. The comparison is first done on the major
        version number, if they are the same then the minor version numbers are compared, if these
        are the same then the sub version numbers are compared. Returns 1 if version1 > version2,
        0 if version1 == version2, and -1 if version1 < version2.

        Parameters
        ----------
        version1 : str or tuple
            The first version to compare. If it is a string then it is converted to a tuple of ints
            before comparison.

        version2 : str or tuple
            The first version to compare. If it is a string then it is converted to a tuple of ints
            before comparison.

        Returns
        -------
        Int, 1 if version1 > version2, 0 if version1 == version2, and -1 if version1 < version2.

    """
    # check the type and convert if needed from a string to tuple
    if isinstance(version1, str):
        v1 = parseversion(version1)
    elif isinstance(version1, tuple):
        if len(version1) == 3:
            v1 = version1
        elif len(version1) == 2:
            v1 = (version1[0], version1[1], 0)
        elif len(version1) == 1:
            v1 = (version1[0], 0, 0)
        else:
            raise Exception("Version must have 1, 2, or 3 elements.")
    else:
        raise Exception("Improper format for the version number, it must be a tuple or a string")

    # check the type and convert if needed from a string to tuple
    if isinstance(version2, str):
        v2 = parseversion(version2)
    elif isinstance(version2, tuple):
        if len(version2) == 3:
            v2 = version2
        elif len(version2) == 2:
            v2 = (version2[0], version2[1], 0)
        elif len(version2) == 1:
            v2 = (version2[0], 0, 0)
        else:
            raise Exception("Version must have 1, 2, or 3 elements.")
    else:
        raise Exception("Improper format for the version number, it must be a tuple or a string")
    
    if v1[0] > v2[0]:
        return 1
    if v1[0] < v2[0]:
        return -1
    if v1[1] > v2[1]:
        return 1
    if v1[1] < v2[1]:
        return -1
    if v1[2] > v2[2]:
        return 1
    if v1[2] < v2[2]:
        return -1
    return 0

def getFiles(basedir):
    """ Generates a list of all BDP files that are in the baseDir and any
        subdirectories

        Parameters
        ----------
        None

        Returns
        -------
        List
            List of BDP files that need to be read in from disk
    """
    files = []
    for root, dirnames, filenames in os.walk(basedir):
        for f in filenames:
            if f.endswith(".bdp"):
                files.append(os.path.join(root, f))
    return files

def getButton(buttonid,onclick,label):
    """Generates HTML for a button that will call a javascript method with
       the id as its argument.   The button class will be *livedisplay*
       (see admit.css) so it only is visible in pages viewed with http.  

       Parameters
       ----------
       buttonid: str 
           String for the button *id* tag
       onclick: str 
           Name of the javascript method to be called via the *onclick* tag
       label: str 
           Label for button that will be displayed to user

       Returns
       -------
       str
           HTML button element 
    """
    return '<button class="livedisplay btn btn-primary" id="%s" onclick="%s(this.id)">%s</button>' % (buttonid, onclick, label)

def mergesegments(segs,nchan):
    """ Method to merge all input segments into a single list. Any
        overlaping segments are merged into one that encompases all 
        the channels.

        Parameters
        ----------
        segs : list
           list of Segments tuples in channel space

        nchan: int
           number of channels in parent spectrum

        Returns
        ------- 
        merged list of segments
    """
    segments = Segments(nchan=nchan)
    for seg in segs:
        # Segment + operator is overloaded to 
        # allow RHS to be a list of tuples or 
        # single tuple
        if type(seg) == list:
            for s in seg:
                segments += s  
        else:
            segments += seg
    segments.merge()
    return segments.getsegments()
