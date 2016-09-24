#! /usr/bin/env python
#
# Testing CubeSum AT
#

from admit.at.CubeSum_AT import CubeSum_AT

import sys, os
import unittest

class TestCubeSum_AT(unittest.TestCase):

    # initialization.
    def setUp(self):
        self.verbose = False
        self.testName = "CubeSum AT Unit Test"
        self.at = CubeSum_AT()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName
    
    def test_keys(self):
        if (self.verbose):
            print "\n--- Default Keys ---"
            print "numsigma:", self.at.getkey("numsigma")
            print "sigma:   ", self.at.getkey("sigma")
            print "--------------------"

    def test_input(self):
        bdpin = len(self.at._bdp_in)
        if (self.verbose):
            print "\nCubeSum_AT: number of BDP in:", bdpin

    def test_output(self):
        if(self.verbose):
            print "\nCubeSum_AT: number of BDP out:", len(self.at)

    def test_version(self):
        if(self.verbose):
            print "\nCubeSum_AT version:", self.at._version

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_CusbSum.py" 
# or "./unittest_CubeSum.py"
if __name__ == '__main__':
    unittest.main()
