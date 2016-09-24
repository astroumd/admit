#! /usr/bin/env casarun
#
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
""" Right now you need to run this test inside of casapy

This test does the following:
    creates an admit class
    creates a moment AT
    sets some moment parameters
    adds the moment AT to the admit class
    runs admit (which in turn runs the needed AT's)
    writes the results out to disk
    reads them into a new admit instance
    prints out one of the BDP xml file names

    to run this test do the following:
        import admit.at.test.test_moment as tm
        tm.run(<filename>)    <filename> is the name of the image file to be processed (note for the time being you need to be in the directory containing the image file
"""
import admit

import unittest
import os

class IntegTestMomentAT(unittest.TestCase):

    def setUp(self):
        self.root = admit.utils.admit_root()
        self.inputFile  = self.root + "/admit/at/test/mom_integ_test_input.fits"
        self.admitdir   = self.root + "/admit/at/test/mom_integ_test_input.admit"
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"
        self.cleanup()

    def tearDown(self):
        self.cleanup()
        self.cleanlogs()
        f = open(self.testoutput,"a")
        f.write(self.success+ " "+self.__class__.__name__  + "\n")
        f.close()

    def cleanup(self):
        try:
            cmd = "/bin/rm -rf %s*" % self.admitdir
            os.system( cmd )
        except Exception as ex :
            print "failed to remove admit dir %s :" % self.admit_dir
            print ex

    # cleanlogs is separate because we don't want to remove logs we might
    # be writing to.
    def cleanlogs(self):
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
            # instantiate the Admit class
            a = admit.Project(self.admitdir)

            # set up to write out figure files
            a.plotparams(admit.PlotControl.BATCH,admit.PlotControl.PNG)

            fitsin = admit.Ingest_AT(file=self.inputFile)
            task0id = a.addtask(fitsin)

            # instantiate a moment AT and set some moment parameters
            m = admit.Moment_AT()
            m.setkey('moments',[0,1,2])
            m.setkey('sigma',0.005) 
            m.setkey('numsigma',[3.0]) 
            task1id = a.addtask(m,[(task0id,0)])

            # check the fm
            a.fm.verify()

            # run admit
            a.run()
            # save it out to disk.
            a.write()

            a2 = admit.Project(self.admitdir)   # read in the admit.xml and bdp files
            self.assertEqual(len(a.fm),len(a2.fm))
            for atask in a.fm:
                self.assertEqual(len(a.fm[atask]._bdp_out),
                                 len(a2.fm[atask]._bdp_out))
                # Note: we don't check bdp_in because they are connected
                # "just in time" so will be set None up read-in.

            self.assertEqual(a.fm._connmap,a2.fm._connmap)

            for at in a.fm:
                for i in range(len(a.fm[at]._bdp_out)) :
                    self.assertEqual( a.fm[at]._bdp_out[i]._taskid,
                                     a2.fm[at]._bdp_out[i]._taskid)
                    self.assertEqual( a.fm[at]._bdp_out[i].xmlFile,
                                     a2.fm[at]._bdp_out[i].xmlFile)
            self.success = "OK"
        except Exception, e:
            m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
            self.success = "FAILED"
            traceback.print_exc()
            self.fail("%s failed with: %s" % (self.__class__.__name__ , m))

            

###############################################################################
# END CLASS                                                                   #
###############################################################################

suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestMomentAT)
unittest.TextTestRunner(verbosity=0).run(suite)
