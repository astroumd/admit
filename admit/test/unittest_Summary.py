#! /usr/bin/env python
#
# Testing Summary
#

import sys, os, unittest
import admit

class TestSummary(unittest.TestCase):

    # Use setUp to do any test initialization.
    # WARNING: this is re-run prior to *every* test method.
    def setUp(self):
        self.verbose = False
        self.testName = "Summary Unit Test"

    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName

    def test_summary(self):
        # Test insertion of tasks (FM method: add(at, stuples, dtuples))
        if (self.verbose) : 
            print "\n------- Test Insertion ------------"
        s = admit.Summary()
        self.assertEqual(s._test(),True)

#----------------------------------------------------------------------
# Below is provided to run the tests on command line
if __name__ == '__main__':
    unittest.main()
