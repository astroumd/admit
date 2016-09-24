#! /usr/bin/env casarun
#
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
""" Run this test using integrationtest_helloworld.csh

This test does the following:
    creates an admit class
    creates a helloworld AT
    sets some parameters
    adds the helloworld AT to the admit class
    runs admit (which in turn runs the needed AT's)
    writes the results out to disk
    reads them into a new admit instance
    prints out one of the BDP xml file names

"""
import os
import admit
import admit.xmlio.dtdGenerator as dtd
import unittest

class IntegTestHelloWorldAT(unittest.TestCase):

    def setUp(self):
        self.root = admit.utils.admit_root()
        self.admitdir   = self.root + "/admit/at/test/helloworld.admit"
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"
        self.cleanup()

    def tearDown(self):
        self.cleanup()
        f = open(self.testoutput,"a")
        f.write(self.success + " " + self.__class__.__name__  + "\n")
        f.close()

    def cleanup(self):
        try:
            cmd = "/bin/rm -rf %s*" % self.admitdir
            os.system( cmd )
            os.system("/bin/rm -rf ipython*.log casapy*.log")
        except:
            pass

    # Call the main method runTest() for automatic running.
    #
    def runTest(self):
        try:
            # instantiate the class
            a = admit.Project(self.admitdir)

            # instantiate hello world at
            h = admit.HelloWorld_AT(yourname="Bob")

            task1id = a.addtask(h)

            # check the fm
            a.fm.verify()

            # run admit and save to disk
            a.run()

            a2 = admit.Project(self.admitdir)   # read in the admit.xml and bdp files
            self.assertEqual(len(a.fm),len(a2.fm))
            for atask in a.fm:
                self.assertEqual(len(a.fm[atask]._bdp_out),
                                 len(a2.fm[atask]._bdp_out))
                if(len(a.fm[atask]._bdp_in) != 0 and len(a2.fm[atask]._bdp_in) != 0):
                    self.assertEqual( a.fm[atask]._bdp_in[0]._taskid,
                                      a2.fm[atask]._bdp_in[0]._taskid)


            self.assertEqual(a.fm._connmap,a2.fm._connmap)

            for at in a.fm:
                for i in range(len(a.fm[at]._bdp_out)) :
                    print "%d %d %d %s %s\n" % (i ,
                             a.fm[at]._bdp_out[i]._taskid,
                            a2.fm[at]._bdp_out[i]._taskid,
                             a.fm[at]._bdp_out[i].xmlFile,
                            a2.fm[at]._bdp_out[i].xmlFile )
            self.success = "OK"
        except Exception, e:
            m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
            self.success = "FAILED"
            traceback.print_exc()
            self.fail("%s failed with: %s" % (self.__class__.__name__ , m))


###############################################################################
# END CLASS                                                                   #
###############################################################################

if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestHelloWorldAT)
    unittest.TextTestRunner(verbosity=0).run(suite)

