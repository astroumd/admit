"""**FlowMN_AT** --- Test task consuming M File_BDPs and creating N.
   -----------------------------------------------------------------
   
   This module defines the FlowMN_AT class.
"""
#! /usr/bin/env python

import sys, os
from copy import deepcopy

from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.File_BDP import File_BDP
import admit.Admit as admit
from admit.at.File_AT import File_AT



#  this is a collection of Flow_AT's, with the sole purpose 
#  to connect with one or more File_BDP (in/out) to test
#  flow's of arbitrary scale.
#  It is the most simple of ADMIT, without the need for
#  any external package (such as CASA) or serious computation
#  inside of the flow.  Hence the '#! /usr/bin/env python' first line.


class FlowMN_AT(AT):
    """
    Change one or more BDPs into many other BDPs.

    **Keywords**

      **touch**: bool
	Touch the output files [False].

      **exist**: bool
        Files belonging to the input BDPs must exist to pass [False].

      **m**: int
	Number of input BDPs; note this is a shadow keyword
        (attribute) that cannot be accessed after construction.

      **n**: int, optional
	Number of output bdp's (but this number should
	not be used afterwards, instead scan bdp_out after the run.
        Default: 2.

      **file**: str, optional
	Optional basename of output file. If not given
	the filename from the input BDP is used as 
	basename, and basename.# is created.

    **Input BDPs**

      **File_BDP**: count: **m** (keyword value)
          Test inputs.

    **Output BDPs**

      **File_BDP**: count: **n** (keyword value)
          Test outputs.
    """

    def __init__(self,**keyval):
        keys = {"file"  : "",      
                "m"     :  0,
                "n"     :  2,
                "touch" : False,   
                "exist" : False} 
        AT.__init__(self,keys,keyval)
        self._version   = "1.0.0"
        self.set_bdp_in ([(File_BDP,self._keys.pop('m'),bt.REQUIRED)])
        self.set_bdp_out([(File_BDP,1), (File_BDP,0)])

    def run(self):
        exist = self.getkey('exist')
        m = len(self._bdp_in)
        print "FlowMN_AT.run():  Found %d input bdps with the following filenames:" % m
        for b in self._bdp_in:
            print "MN_in: ",b.filename        # this works because we know it's a File_BDP, getfiles() otherwise
            if exist: b.checkfiles()

        filename = self.getkey('file')
        if not filename:
          alias = self._alias
          filename = self._bdp_in[0].filename + ('-'+alias if alias else '_MN')

        if self.haskey('junk'):
            print "Impossible"

        # Although for practical purposes 'n' is defined here, other
        # AT's computed what 'n' should be (e.g. LineID/LineCube
        n = self.getkey('n')

        # special case: if n<0 use a random number generator
        # that creates between 0 and n BDP outs

        # bdps will be the list of BDPs in the loop below
        bdps = range(n)

        # create the output BDPs
        self.clearoutput()
        for i in range(n):
            bfilename = "%s.%d" % (filename,i)
            bdps[i] = File_BDP(bfilename)
            bdps[i].filename = bfilename
            self.addoutput(bdps[i])
            if self.getkey('touch'): bdps[i].touch()
