#! /usr/bin/env casarun

#  This is a barebones example of how to set up and run an integration
#  test using the unittest module via casarun.  One cannot use 
#  unittest.main() because the command line arguments to casapy
#  are interpreted by unittest and the script barfs.   Therefore, the
#  alternate method of unittest.TestLoader is used.

import unittest
import admit

class IntegTestExample(unittest.TestCase):
   def setUp(self):
        print "hello, world"
        self.root = admit.utils.admit_root()
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"


   def tearDown(self):
   # NOTE: You must write self.success to  file so that 
   # $ADMIT/bin/runIntegrationTests.csh
   # can grep it.  This is a workaround for the fact that
   # casapy always returns 0 status regardless of exceptions.
        f = open(self.testoutput,"a")
        f.write(self.success + " " + self.__class__.__name__  + "\n")
        f.close()
        print "goodbye, everybody"

   # Call the main method runTest() for automatic invocation.
   # Alternatively, ff runTest() does not exist, every method 
   # with name beginning "test_" will be run.
   # NOTE: If test_ methods exist, then runTest will NOT be run!
   def runTest(self):
        try:
           print "runtest"
           self.success = "OK"
        except Exception, e:
           m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
           self.success = "FAILED"
           traceback.print_exc()
           self.fail("%s failed with: %s" % (self.__class__.__name__ , m))


########################################################################
# Below here is what is run on invocation either from shell or casapy  #
########################################################################


#   NOPE. This won't work.
#    unittest.main()
suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestExample)
unittest.TextTestRunner(verbosity=0).run(suite)


