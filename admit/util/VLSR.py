#! /usr/bin/env python
#! /usr/bin/env casarun
"""
  **VLSR** --- Simple VLSR catalog and calculator.
  ------------------------------------------------

  This module defines the VLSR class.
"""


import sys, os
import numpy as np

from admit.util.AdmitLogging import AdmitLogging as logging

try:
    import utils
    have_ADMIT = True
except:
    have_ADMIT = False

try:
    from astroquery.simbad import Simbad
    have_SB = True
except:
    have_SB = False

try:
    from astroquery.ned import Ned
    have_NED = True
except:
    have_NED = False

class VLSR(object):
    """
    Simple VLSR catalog and calculator.

    Possible extensions:

    - merge in multiple tables, now hardcoded to a single
      table in $ADMIT/etc/vlsr.tab
    - allow astroquery from NED and/or SIMBAD
      (this may need to run in pure-python, outside of ADMIT/CASA)
    - name matching is now done in upper case by default

    Attributes
    ----------
    None
    """

    def __init__(self, upper=True):
        self.version = "27-apr-2016"
        if have_ADMIT:
            self.table = utils.admit_root() + "/etc/vlsr.tab"
            self.cat = read_vlsr(self.table,upper)
            logging.debug("VLSR: %s, found %d entries" % (self.table,len(self.cat)))
        else:
            logging.warning("VLSR: Warning, no ADMIT, empty catalogue")
            self.cat = {}

    def vlsr(self, name, upper=True):
        """ return VLSR from requested object
            name matching is done in upper case by default
            If no match is found, 0.0 is returned.
        """
        # print "VLSR debug",name,self.cat
        if len(name) == 0:  return 0.0
        src = name.upper()
        quote1 = "'"
        quote2 = '"'
        if src[0] == quote1:
            src = src.strip(quote1)
        if src[0] == quote2:
            src = src.strip(quote2)
        if self.cat.has_key(src):
            return self.cat[src]
        else:
            return 0.0

    def vlsr2(self, name):
        """ experimental Simbad/NED
        """
        if have_SB:
            print "Trying SIMBAD..."
            try:
                t1 = Simbad.query_object(name)
                print t1.colnames
                print t1
            except:
                pass
        else:
            print "No SIMBAD"
        if have_NED:
            print "Trying NED..."
            try:
                t2 = Ned.query_object(name)
                print t2.colnames
                print t2
                print 'VLSR=',t2['Velocity'].item()
            except:
                pass
        else:
            print "No NED"

    def try_SB(self,name):
        return 0.0

    def try_NED(self,name):
        return 0.0

def read_vlsr(filename, upper=True):
    """ read the ADMIT vlsr.cat table

    This table is peculiar in allowing spaces in source names,
    but then requires the name to be single (or double) quotes.
    The source name is stored without these quotes.
    The 2nd column is VLSR in km/s
    Anything beyond is ignored, so comments are allowed 
    Also note we are taking the source names "as is", so 
    it is suggested they are in upper case.

    """
    fp = open(filename)
    lines = fp.readlines()
    #print 'Found %d lines in %s' % (len(lines),filename)
    cat = {}
    quote1 = "'"
    quote2 = '"'
    for line in lines:
        w = line.split()
        if len(w) < 2: 
            continue
        elif line[0] == '#':
            continue
        elif line[0] == quote1:
            loc = line[1:].find(quote1) + 1
            if loc==0: 
                print "VLSR: Skipping bad line",line.strip()," in ",filename
                continue
            src = line[1:loc]       # sourcename without the quotes
            if upper:
                src = src.upper()
            cat[src] = float(line[loc+1:].split()[0])
        elif line[0] == quote2:
            loc = line[1:].find(quote2) + 1
            if loc==0: 
                print "VLSR: Skipping bad line",line.strip()," in ",filename
                continue
            src = line[1:loc]       # sourcename without the quotes
            if upper:
                src = src.upper()
            cat[src] = float(line[loc+1:].split()[0])
        else:
            src = w[0]
            if upper:
                src = src.upper()
            cat[src] = float(w[1])
    return cat

if __name__ == "__main__":

    vq = VLSR()
    print vq.vlsr("NGC6503")    # should print 25.0
    print vq.vlsr("ngc6503")    # should print 25.0
    print vq.vlsr("foobar")     # should print 0.0
    print vq.vlsr("L1551 NE")   # should print 7.0
    print vq.vlsr("'L1551 NE'") # should print 7.0 
    vq.vlsr2("NGC6503")
    
