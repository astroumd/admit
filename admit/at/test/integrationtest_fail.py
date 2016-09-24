#!/usr/bin/env python
""" 
Example failing integration test.
"""
import admit

import unittest
import os

class IntegTestFail(unittest.TestCase):

    def setUp(self):
        self.cleanlogs()
        self.root = admit.utils.admit_root()
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"  

    def tearDown(self):
        self.cleanlogs()
        f = open(self.testoutput,"a")
        f.write(self.success + " " + self.__class__.__name__  + "\n")
        f.close()

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
    def runTest(self):
        try:
        # a failure status for this test actually means it ran correctly!
            self.fail("Hooray integration test failed! Check that exit status is 1")
            self.success = "OK"
        except Exception, e:
            m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
            self.success = "FAILED"
            traceback.print_exc()
            self.fail("%s failed with exception %s" % (self.__class__.__name__ , e))

            

###############################################################################
# END CLASS                                                                   #
###############################################################################


#if __name__ == '__main__':
#    print sys.argv
#    sys.argv = [sys.argv[4]]
#    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestFail)
#unittest.TextTestRunner(verbosity=0).run(suite)
