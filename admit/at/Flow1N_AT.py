"""**Flow1N_AT** --- Test task consuming one File_BDP and creating N.
   ------------------------------------------------------------------
   
   This module defines the Flow1N_AT class.
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


class Flow1N_AT(AT):
    """
    Change one BDP into many other BDPs.

    **Keywords**

      **touch**: bool
	Touch the output file [False].

      **exist**: bool
        Input file that belongs to a BDP must exist to pass [False].

      **n**: int
	Number of output bdp's (but this number should
        not be used afterwards, instead use len(bdp_out)
        after the run.

      **file**: str
	Optional basename of output file. If not given
	the filename from the input BDP is used as 
	basename, and basename.# is created
	If no filename given, it will auto-name the input
	BDP filename with _1N.

      **subdir**: str
	If true, it will create the output BDP's in a 
	subdirectory "subdir_X", where X is an index
	counting up from 1..n.

    **Input BDPs**

      **File_BDP**: count: 1
          Test input.

    **Output BDPs**

      **File_BDP**: count: **n** (keyword value)
          Test outputs.
    """

    def __init__(self,**keyval):
        keys = {"file"   : "",      
                "n"      :  2,
                "subdir" : False,
                "touch"  : False,   
                "exist"  : False} 
        AT.__init__(self,keys,keyval)
        self._version   = "1.0.0"
        self.set_bdp_in ([(File_BDP,1,bt.REQUIRED)])
        self.set_bdp_out([(File_BDP,1), (File_BDP,0)])

    def run(self):
        filename = self._bdp_in[0].filename
        print "Flow1N_AT.run():  Input: ",filename

        if len(self._bdp_in) > 1:
            print "Warning: Flow1N found %d input BDP's" % len(self._bdp_in)

        exist = self.getkey('exist')
        if exist:
            for b in self._bdp_in: b.checkfiles()

        filename = self.getkey('file')
        if len(filename) == 0:
          alias = self._alias
          filename = self._bdp_in[0].filename + ('-'+alias if alias else '_1N')


        # Although for practical purposes 'n' is defined here, other
        # AT's computed what 'n' should be (e.g. LineID/LineCube)
        n = self.getkey('n')

        # special case: if n<0 use a random number generator
        # that creates between 0 and n BDP outs

        # bdps will be the list of BDPs in the loop below
        bdps = range(n)

        subdir = self.getkey('subdir')

        # create the output BDPs, notice that the loop index here is
        # either in the subdir name or the filename (if subdir not set)
        self.clearoutput()
        for i in range(n):
            if subdir:
                sdir = 'subdir_%d/' % (i+1)
                self.mkdir(sdir)
                bfilename = "%s/%s" % (sdir,filename)
            else:
                bfilename = "%s.%d" % (filename,i)
            bdps[i] = File_BDP(bfilename)
            bdps[i].filename = bfilename
            self.addoutput(bdps[i])
            if self.getkey('touch'): bdps[i].touch()
