"""**FlowN1_AT** --- Test task consuming N File_BDPs and creating one.
   -------------------------------------------------------------------
   
   This module defines the FlowN1_AT class.
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


class FlowN1_AT(AT):
    """
    Change a series of BDPs into another BDP.

    **Keywords**

      **file**: string
          Output filename created, from which the BDP is named as well
          as "<file>.bdp".  The BDP is always created. The file itself
          will depend on the touch= keyword.
          If the filename is blank, it will generate an output filename
          by appending _11 to the input filename.

      **touch**: bool
          Create a 0-length file that the output BDP will point to [False].

      **exist**: bool
          Files belonging to the input BDPs must exist to pass [True].

    **Input BDPs**

      **File_BDP**: count: `varies`
          Test inputs.

    **Output BDPs**

      **File_BDP**: count: 1
          Test output.

    """
    # keys = ['debug','touch','exist','file']
    def __init__(self,**keyval):
        keys = {"file"  : "",      
                "touch" : False,   
                "exist" : True}         
        AT.__init__(self,keys,keyval)
        self._version = "1.0.0"
        self.set_bdp_in ([(File_BDP,0,bt.REQUIRED)])
        self.set_bdp_out([(File_BDP,1)])

    def run(self):
        n = len(self._bdp_in)
        print "FlowN1_AT.run():  Found %d input bdps with the following filenames:" % n

        exist = self.getkey('exist')
        for i in range(n):
            print "bdp_in[%d]: %s" % (i,self._bdp_in[i].filename)
            if exist: self._bdp_in[i].checkfiles()
                                      
        # grab essential parameters
        filename = self.getkey('file')
        if not filename:
          alias = self._alias
          filename = self._bdp_in[0].filename + ('-'+alias if alias else '_N1')

        # create the output BDP
        bdp1 = File_BDP(filename)
        bdp1.filename = filename
        self.clearoutput()
        self.addoutput(bdp1)

        if self.getkey('touch'): bdp1.touch()

        # this FlowN1 is actually not doing anything with the input BDP.
