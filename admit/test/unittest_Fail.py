#! /usr/bin/env python
#
# Q: Does a failing unit test cause buildbot to go red?
# A: Yes, it does!


import sys, os
import unittest

class TestFail(unittest.TestCase):

    def setUp(self):
        self.testName = "Failing Unit Test"

    def test_AAAwhoami(self):
        print "==== %s ====" % self.testName

# Uncomment to make this unit test fail and turn buildbot red
#    def test_fail(self):
#        self.assertEqual(True,False)


#----------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
