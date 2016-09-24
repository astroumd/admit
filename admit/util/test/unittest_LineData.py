#! /usr/bin/env python
#
# Testing util/LineData.py functions
#
# Functions covered by test cases: 12/12
#    __init__()
#    setstart()
#    getstart()
#    setend()
#    getend()
#    setchans()
#    setfstart()
#    getfstart()
#    setfend()
#    getfend()
#    setfreqs()
#    getkey()


import admit
import sys, os
import unittest

class TestLineData(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "LineData Class Unit Test"

        data = {"frequency":115.271, "uid":"CO","formula":"CO-115.271",
                    "name":"Carbon Monoxide", "transition":"1-0",
                    "velocity":0.0,
                    "linestrength":0.01, "peakintensity":1.3,
                    "peakoffset":0.0, "fwhm":5.0,
                    "peakrms":5.2, "blend":0}

        self.linedata = admit.LineData()
        self.linedata.setkey(name=data)

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test setstart() and getstart()
    def test_start_chan(self):
        chan = self.linedata.getstart()
        if(self.verbose):
            print "\nStarting channel:", chan

        self.assertEqual(0, chan)  # should be 0, the default value

        self.linedata.setstart(123)
        chan = self.linedata.getstart()
        if(self.verbose):
            print "\nStarting channel after:", chan

        self.assertEqual(123, chan)  # should be 123 now

    # test setend() and getend()
    def test_end_chan(self):
        chan = self.linedata.getend()
        if(self.verbose):
            print "\nEnding channel:", chan

        self.assertEqual(0, chan)  # should be 0, the default value

        self.linedata.setend(234)
        chan = self.linedata.getend()
        if(self.verbose):
            print "\nEnding channel after:", chan

        self.assertEqual(234, chan)  # should be 234 now

    # test setchans()
    def test_set_chans(self):
        chan = self.linedata.getstart()
        if(self.verbose):
            print "\nStarting channel:", chan

        self.assertEqual(0, chan)  # should be 0, the default value

        chan = self.linedata.getend()
        if(self.verbose):
            print "\nEnding channel:", chan

        self.assertEqual(0, chan)  # should be 0

        # now set the channels
        self.linedata.setchans([11, 22])
        chan = self.linedata.getstart()
        if(self.verbose):
            print "\nStarting channel after:", chan

        self.assertEqual(11, chan)  # should be 11

        chan = self.linedata.getend()
        if(self.verbose):
            print "\nEnding channel after:", chan

        self.assertEqual(22, chan)  # should be 22

    # test setfstart() and getfstart()
    def test_start_frequency(self):
        freq = self.linedata.getfstart()
        if(self.verbose):
            print "\nStarting frequency:", freq

        self.assertEqual(0.0, freq)  # should be 0.0

        self.linedata.setfstart(100.123)
        freq = self.linedata.getfstart()
        if(self.verbose):
            print "\nStarting frequency after:", freq

        self.assertEqual(100.123, freq)  # should be 100.123 now

    # test setfend() and getfend()
    def test_end_frequency(self):
        freq = self.linedata.getfend()
        if(self.verbose):
            print "\nEnding frequency:", freq

        self.assertEqual(0.0, freq)  # should be 0.0

        self.linedata.setfend(200.456)
        freq = self.linedata.getfend()
        if(self.verbose):
            print "\nEnding frequency after:", freq

        self.assertEqual(200.456, freq)  # should be 200.456 now

    # test setfreqs()
    def test_set_freqs(self):
        freq = self.linedata.getfstart()
        if(self.verbose):
            print "\nStarting frequency:", freq

        self.assertEqual(0, freq)  # should be 0, the default value

        freq = self.linedata.getfend()
        if(self.verbose):
            print "\nEnding frequency:", freq

        self.assertEqual(0, freq)  # should be 0

        # now set the frequency range
        self.linedata.setfreqs([100.123, 200.456])
        freq = self.linedata.getfstart()
        if(self.verbose):
            print "\nStarting frequency after:", freq

        self.assertEqual(100.123, freq)  # should be 100.123

        freq = self.linedata.getfend()
        if(self.verbose):
            print "\nEnding frequency after:", freq

        self.assertEqual(200.456, freq)  # should be 200.456

    # test getkey() and setkey()
    def test_getkey(self):
        """ 
        === LineData init values:
        self.mass = 0
        self.plain = ""
        self.isocount = 0
        self.chans = [0, 0]
        self.freqs = [0.0, 0.0]
        self.peakintensity = 0.0
        self.peakrms = 0.0
        self.fwhm = 0.0
        self.noise = 0.0
        self.hfnum = 0
        self.velocity = 0.0
        self.peakoffset = 0.0
        self.force = False

        === Setup valules:
        data = {"frequency":115.271, "uid":"CO","formula":"CO-115.271",
                    "name":"Carbon Monoxide", "transition":"1-0",
                    "velocity":0.0,
                    "linestrength":0.01, "peakintensity":1.3,
                    "peakoffset":0.0, "fwhm":5.0,
                    "peakrms":5.2, "blend":0}
        """

        # ==== mass ====
        val = self.linedata.getkey("mass")
        if(self.verbose):
            print "\nLineData mass:", val

        self.assertEqual(0, val)  # should be 0.0

        self.linedata.setkey(name = "mass", value=111)

        val = self.linedata.getkey("mass")
        if(self.verbose):
            print "\nLineData mass after:", val

        self.assertEqual(111, val)  # should be 0.0

        # ==== plain ====
        val = self.linedata.getkey("plain")
        if(self.verbose):
            print "\nLineData plain:", val

        self.assertEqual("", val)

        self.linedata.setkey(name = "plain", value='TEST')

        val = self.linedata.getkey("plain")
        if(self.verbose):
            print "\nLineData plain after:", val

        self.assertEqual('TEST', val)  # should be 'TEST'

        # ==== isocount ====
        val = self.linedata.getkey("isocount")
        if(self.verbose):
            print "\nLineData isocount:", val

        self.assertEqual(0, val) # should be 0

        self.linedata.setkey(name = "isocount", value=333)

        val = self.linedata.getkey("isocount")
        if(self.verbose):
            print "\nLineData isocount after:", val

        self.assertEqual(333, val)  # should be 333

        # ==== peakintensity ====
        val = self.linedata.getkey("peakintensity")
        if(self.verbose):
            print "\nLineData peakintensity:", val

        self.assertEqual(1.3, val) # should be 1.3

        self.linedata.setkey(name = "peakintensity", value=10.2)

        val = self.linedata.getkey("peakintensity")
        if(self.verbose):
            print "\nLineData peakintensity after:", val

        self.assertEqual(10.2, val)

        # ==== peakrms ====
        val = self.linedata.getkey("peakrms")
        if(self.verbose):
            print "\nLineData peakrms:", val

        self.assertEqual(5.2, val) # should be 5.2

        self.linedata.setkey(name = "peakrms", value=8.2)

        val = self.linedata.getkey("peakrms")
        if(self.verbose):
            print "\nLineData peakrms after:", val

        self.assertEqual(8.2, val)

        # ==== fwhm ====
        val = self.linedata.getkey("fwhm")
        if(self.verbose):
            print "\nLineData fwhm:", val

        self.assertEqual(5.0, val) # should be 5.0

        self.linedata.setkey(name = "fwhm", value=9.5)

        val = self.linedata.getkey("fwhm")
        if(self.verbose):
            print "\nLineData fwhm after:", val

        self.assertEqual(9.5, val)

        # ==== force ====
        val = self.linedata.getkey("force")
        if(self.verbose):
            print "\nLineData force:", val

        self.assertEqual(False, val) # should be False

        self.linedata.setkey(name = "force", value=True)

        val = self.linedata.getkey("force")
        if(self.verbose):
            print "\nLineData force after:", val

        self.assertTrue(val)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_LineData.py" 
# or "./unittest_LineData.py"
if __name__ == '__main__':
    unittest.main()
