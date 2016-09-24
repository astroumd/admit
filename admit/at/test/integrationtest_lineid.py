#! /usr/bin/env casarun
# 
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
""" LineID_AT Integration test.
"""
import matplotlib as mpl
import matplotlib.pyplot as pl

import admit
import numpy as np

import unittest
import os

class IntegTestLineIDAT(unittest.TestCase):

    def setUp(self):
        self.root = admit.utils.admit_root()
        self.specfile = self.root + "/admit/at/test/lineID.spec"
        self.admitdir = self.root + "/admit/at/test/lineID.admit"
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"
        self.cleanup()

    def tearDown(self):
        self.cleanup()
        self.cleanlogs()
        f = open(self.testoutput,"a")
        f.write(self.success + " " + self.__class__.__name__  + "\n")
        f.close()
            

    def cleanup(self):
        try:
            cmd = "/bin/rm -rf %s*" % self.admitdir
            os.system(cmd)
        except Exception :
            print "failed to remove admit dir %s :" % self.admitdir

    def cleanlogs(self):
        print "Cleaning up...\n"
        try:
            os.system("/bin/rm -rf ipython*.log")
        except:
            print "failed to remove ipython logs"

        try:
            os.system("/bin/rm -rf casapy*.log")
        except:
            print "failed to remove casapy logs"


    # Call the main method runTest() for automatic running.
    #
    # NB: don't use "run()" - it conflicts unittest.TestCase run() 
    # method and you get side effects, e.g. fileName = 
    # <unittest.runner.TextTestResult run=0 errors=0 failures=0>
    #
    def runTest(self):
        try:
            # instantiate the class

            a = admit.Project(self.admitdir)

            #use a GenerateSpectrum_AT that reads in a spectrum 
            gs1 = a.addtask(admit.GenerateSpectrum_AT(file=self.specfile,freq=124.470, seed=-1))
            gstab1 = (gs1,0)

            # instantiate a LineID AT and set parameters
            l = admit.LineID_AT(vlsr=0.0)
            task1id = a.addtask(l,[gstab1])

            # check the fm 
            a.fm.verify()

            #mpl.rcParams['backend'] = 'Agg'

            # run admit 
            a.run()

            a2 = admit.Project(self.admitdir)   # read in the admit.xml and bdp files
            self.success = "OK"
        except Exception, e:
            m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
            self.success = "FAILED"
            traceback.print_exc()
            self.fail("%s failed with: %s" % (self.__class__.__name__ , m))

###############################################################################
# END CLASS                                                                   #
###############################################################################

suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestLineIDAT)
unittest.TextTestRunner(verbosity=0).run(suite)
