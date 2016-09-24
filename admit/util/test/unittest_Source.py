#! /usr/bin/env python
#
# Testing util/Source.py functions
#
# Functions covered by test cases:
#    isequal()
#    __str__
#    __init__
#
# Code coverage percentage: 100%

import sys, os
import unittest
from admit.util.Source import Source

class TestSource(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Source Class Unit Test"
        self.s1 = Source()
        self.s2 = Source()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test isequal() and __str__()
    def test_isequal(self):

        ret = self.s1.isequal(self.s2)
        if(self.verbose):
            print "\nSource is equal:", ret

        # s1 and s2 are the same
        self.assertTrue(ret)

        self.s2.major = 4.5
        self.s2.name = "Test"

        self.s2.__str__()

        ret = self.s1.isequal(self.s2)
        if(self.verbose):
            print "\nSource is equal:", ret

        # s1 is not equal to s2
        self.assertFalse(ret)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Source.py" 
# or "./unittest_Source.py"
if __name__ == '__main__':
    unittest.main()
