#! /usr/bin/env python
#
# Testing util/Line.py functions
#

import admit
import sys, os
import unittest

class TestLine(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Line Class Unit Test"
        self.line = admit.Line()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test Line.setupperenergy() and line.getupperenergy()
    def test_upperenergy(self):

        # test with an integer
        self.line.setupperenergy(12)
        ret = self.line.getupperenergy()
        if(self.verbose):
            print "\nUpper Energy:", ret

        self.assertEqual(12.0, ret)

        # test set with float number
        self.line.setupperenergy(13.5)
        ret = self.line.getupperenergy()
        if(self.verbose):
            print "\nUpper Energy:", ret

        self.assertEqual(13.5, ret)

    # test Line.setlowererenergy() and line.getlowerenergy()
    def test_lowerenergy(self):

        # test with an integer
        self.line.setlowerenergy(2)
        ret = self.line.getlowerenergy()
        if(self.verbose):
            print "\nLower Energy:", ret

        self.assertEqual(2.0, ret)

        # test set with float number
        self.line.setlowerenergy(3.8)
        ret = self.line.getlowerenergy()
        if(self.verbose):
            print "\nLower Energy:", ret

        self.assertEqual(3.8, ret)

    # test Line.setkey()
    def test_setkey(self):
        keys = {'name' : 'Carbon monoxide', 'uid' : 'CO-115.271', 'formula' : 'CO'}
        self.line.setkey(keys)

        ret = self.line.name
        str = 'Carbon monoxide'
        if(self.verbose):
            print "\nLine name:", ret

        self.assertEqual(str, ret)

        ret = self.line.uid
        str = 'CO-115.271'
        if(self.verbose):
            print "\nLine uid:", ret

        self.assertEqual(str, ret)

        ret = self.line.formula
        str = 'CO'
        if(self.verbose):
            print "\nLine Formula:", ret

        self.assertEqual(str, ret)

    # test Line.isequal()
    def test_isequal(self):

        keys = {'name' : 'Isocyanic Acid', 'uid' : 'DNCO_101.9628', 'formula' : 'DNCO'}
        line = admit.Line(**keys)
        
        ret = self.line.isequal(line)

        if(self.verbose):
            print "\nIs this line equal:", ret

        self.assertEqual(ret, False)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Line.py" 
# or "./unittest_Line.py"
if __name__ == '__main__':
    unittest.main()
