#! /usr/bin/env casarun
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

class IntegTestLineCubeAT(unittest.TestCase):

    def setUp(self):
        self.root = admit.utils.admit_root()
        self.inputFile = self.root + "/admit/at/test/mom_integ_test_input.fits"
        self.admitDir  = self.root + "/admit/at/test/lcube_integ_test.admit"
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"
        self.cleanup()

    def tearDown(self):
        self.cleanup()
        f = open(self.testoutput,"a")
        f.write(self.success+ " "+self.__class__.__name__  + "\n")
        f.close()
            

    def cleanup(self):
        try:
            cmd = "/bin/rm -rf %s" % self.admitDir
            os.system( cmd )
            os.system("/bin/rm -rf ipython*.log casapy*.log immoments.last exportfits.last admit.xml")
        except:
            pass

    # Call the main method runTest() for automatic running.
    #
    # NB: don't use "run()" - it conflicts unittest.TestCase run() 
    # method and you get side effects, e.g. fileName = 
    # <unittest.runner.TextTestResult run=0 errors=0 failures=0>
    #
    def runTest(self):
        try:
            # instantiate the class
            a = admit.Project(self.admitDir)
            a.plotparams(admit.PlotControl.BATCH,admit.PlotControl.PNG)

            fitsin = admit.Ingest_AT(file=self.inputFile)
            task0id = a.addtask(fitsin)

            l = admit.LineID_AT()
            task2id = a.addtask(l)
            l._needToSave = True
            ll = admit.LineList_BDP()

#             ll.addRow([115.271,"CO","CO-115.271","Carbon Monoxide","1-0",0.0,0.0,3.2,0.01,1.3,0.0,5.0,15,20,5.2])
#             ll.addRow([115.832,"U", "U-115.832", "", "",0.0,0.0,0.0,0.0,0.0,0.0,0.0,25,35,2.4])

            # keys (column names of LineList_BDP)
            # "frequency", "uid", "formula", "name", "transition", "velocity", 
            # "El", "Eu", "linestrength", "peakintensity", "peakoffset", "fwhm", 
            # "startchan", "endchan", "peakrms", "blend"
            keys = {"frequency":115.271, "uid":"CO","formula":"CO-115.271",
                    "name":"Carbon Monoxide", "transition":"1-0",
                    "velocity":0.0,
                    "linestrength":0.01, "peakintensity":1.3,
                    "peakoffset":0.0, "fwhm":5.0,
                    "peakrms":5.2, "blend":0}

            data = admit.LineData()
            data.setkey(name=keys)
            ll.addRow(data)

            keys = {"frequency":115.832, "uid":"U","formula":"U-115.832",
                    "name":"", "transition":"",
                    "velocity":0.0,
                    "linestrength":0.0, "peakintensity":0.0,
                    "peakoffset":0.0, "fwhm":0.0,
                    "peakrms":2.4, "blend":0}

            data.setkey(name=keys)
            ll.addRow(data)

            l.addoutput(ll)
            l.markUpToDate()

            # instantiate a linecube_AT
            lcube = admit.LineCube_AT()
            task1id = a.addtask(lcube,[(task0id,0),(task2id,0)])

            # check the fm 
            a.fm.verify()

            # run admit 
            a.run()
            a.write()
            # read in the admit.xml and bdp files
            a2 = admit.Project(self.admitDir)

            self.assertEqual(len(a.fm),len(a2.fm))
            for atask in a.fm:
                self.assertEqual(len(a.fm[atask]._bdp_out),
                                 len(a2.fm[atask]._bdp_out))
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

suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestLineCubeAT)
unittest.TextTestRunner(verbosity=0).run(suite)
