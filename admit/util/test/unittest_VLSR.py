#! /usr/bin/env python
#
# Testing util/VLSR.py functions
#
# Functions covered by test cases:
#    vlsr()
#    vlsr2()
#    read_vlsr()

import admit
import sys, os
import unittest

class TestVLSR(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility VLSR Class Unit Test"
        self.vq = admit.VLSR()    # read_vlsr() is called in __init__()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test VLSR.vlsr() and VLSR.vlsr2()
    def test_VLSR(self):
        # test vlsr()
        ret = self.vq.vlsr('M83') # should return 514.0
        if(self.verbose):
            print "\nVLSR for M83:", ret
        self.assertEqual(514.0, ret)

        
        ret = self.vq.vlsr("NGC6503")    # should return 25.0
        if(self.verbose):
            print "\nVLSR for NGC6503:", ret
        self.assertEqual(25.0, ret)

        ret = self.vq.vlsr("ngc6503")    # should return 25.0
        if(self.verbose):
            print "\nVLSR for ngc6503:", ret
        self.assertEqual(25.0, ret)

        ret = self.vq.vlsr("test")     # should return 0.0
        if(self.verbose):
            print "\nVLSR for testing:", ret
        self.assertEqual(0.0, ret)

        ret = self.vq.vlsr("L1551 NE")   # should return 7.0 
        if(self.verbose):
            print "\nVLSR for L1551 NE:", ret
        self.assertEqual(7.0, ret)

        # test vlsr2()
        ret = self.vq.vlsr2('B1S')
        if(self.verbose):
            print "\nVLSR for B1S:", ret

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_VLSR.py" 
# or "./unittest_VLSR.py"
if __name__ == '__main__':
    unittest.main()
