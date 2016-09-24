#! /usr/bin/env python
#
# Testing util/Spectrum.py functions
#

import admit

import sys, os
import unittest
import numpy as np
import admit.util.utils as utils

class TestSpectrum(unittest.TestCase):
    # initialization
    def setUp(self):
        #utils.specingest() ?????
        self.verbose = False
        self.testName = "Utility Spectrum Class Unit Test"
        maxchan = 257
        self.fwhm_in = 2.355 # ghz (so that dispersion is 1.0)
        self.delta_in = 0.05 # ghz
        self.peak_in = 1.0
        chans = np.ma.array(range(maxchan))
        self.freq = np.ma.array([110.0+(x * self.delta_in) for x in chans])
        self.mid = self.freq[maxchan/2+1]
        self.intensity = np.ma.array(utils.gaussian1D(self.freq,self.peak_in,self.mid,self.fwhm_in))
        self.spectrum = admit.Spectrum(spec=self.intensity,freq=self.freq,chans=chans)

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    def test_moments(self):
        print "m0(P)=%f,m0(I)=%f,m0(A)=%f"% ( self.spectrum.moment(p=0),self.spectrum.momenti(p=0),self.spectrum.momenta(p=0))
        print "m1(P)=%f,m1(I)=%f,m1(A)=%f" % (self.spectrum.moment(p=1),self.spectrum.momenti(p=1),self.spectrum.momenta(p=1))
        print "m2(P)=%f,m2(I)=%f,m2(A)=%f" % (self.spectrum.moment(p=2),self.spectrum.momenti(p=2),self.spectrum.momenta(p=2))
        print "m3(P)=%f,m3(I)=%f,m3(A)=%f" % (self.spectrum.moment(p=3),self.spectrum.momenti(p=3),self.spectrum.momenta(p=3))
        print "mf=%f,df=%f,delta=%f,dv=%f,fwhm=%f\n"% (self.spectrum.meanfrequency(),self.spectrum.freqdispersion(),self.spectrum.delta(),self.spectrum.veldispersion(),self.spectrum.fwhm())
        self.assertEqual(round(self.spectrum.meanfrequency(),2),self.mid)
        self.assertEqual(self.spectrum.peak(),self.peak_in)
        self.assertEqual(round(self.spectrum.freqdispersion(),3),self.fwhm_in/2.355)
        self.assertEqual(round(self.spectrum.fwhm(),2),
                         round(utils.freqtovel(self.spectrum.meanfrequency(),self.fwhm_in),2))
        self.assertEqual(round(self.spectrum.delta(),2),self.delta_in)

    def see_plot(self):
        import matplotlib.pyplot as plt
        plt.plot(self.freq,self.intensity,c='g')
        intensityout = utils.gaussian1D(self.freq,self.peak_in,self.spectrum.meanfrequency(),self.spectrum.freqdispersion()*2.355)
    
        plt.plot(self.freq,intensityout,c='b')
        plt.show()

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Spectrum.py" 
# or "./unittest_Spectrum.py"
if __name__ == '__main__':
    unittest.main()
