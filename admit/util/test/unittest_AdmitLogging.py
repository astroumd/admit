#! /usr/bin/env python
#
# Testing util/AdmitLogging.py functions
#
# Functions covered by test cases:
#    init()
#    critical()
#    debug()
#    error()
#    info()
#    log()
#    warning()
#    setLevel()
#    timing()
#    regression()
#    heading()
#    subheading()
#    reportKeyword()
#    addLevelName()
#    getEffectiveLevel()
#    findLogger()    <-- called by multiple functions
#    basicConfig()
#    StreamHandler()
#    shutdown()
#
# Code coverage percentage: 90%

import admit
import sys, os
import unittest
import logging
from admit.util.AdmitLogging import AdmitLogging as Alogging

class TestAdmitLogging(unittest.TestCase):
    setup = False

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility AdmitLogging Class Unit Test"
        self.logfile = '/tmp/logging_unit_test_%s.log' % os.getpid()
        self.level = 1

        # only need to initialize the logger once since it is a static class
        if not TestAdmitLogging.setup:
            Alogging.init(name="test", logfile=self.logfile, level=Alogging.DEBUG)
            Alogging.addLevelName(15, "TIMING")
            Alogging.addLevelName(16, "REGRSSION")
            Alogging.setLevel(self.level)
            TestAdmitLogging.setup = True

    # test shutdown()
    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

## commented out because basicConfig() is currently not working.
## It should call logging.basicConfig() instead of logger.basicConfig()
#
#     def test_basicConfig(self):
#         FORMAT = '%(asctime)-15s -8s %(message)s'
#         Alogging.basicConfig(**{"format":FORMAT})

    # test StreamHandler()
    def test_handler(self):
        h = Alogging.StreamHandler()
        self.assertTrue(type(h) is logging.StreamHandler)

    # test critical()
    def test_critical(self):
        msg = "unit_test_critical_message"
        Alogging.critical(msg)

        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", line
                found = True
                r.close()
                break

        self.assertTrue(found)

    # test debug()
    def test_debug(self):
        msg = "unit_test_debug_message"
        Alogging.debug(msg)
 
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", line
                found = True
                r.close()
                break
 
        self.assertTrue(found)
 
    # test error()
    def test_error(self):
        msg = "unit_test_error_message"
        Alogging.error(msg)
 
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", line
                found = True
                r.close()
                break
 
        self.assertTrue(found)
 
    # test info()
    def test_info(self):
        msg = "unit_test_info_message"
        Alogging.info(msg)
  
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test log()
    def test_log(self):
        msg = "unit_test_log_message"
        Alogging.log(Alogging.INFO, msg)
  
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test timing()
    def test_timing(self):
        msg = "unit_test_timing_message"
        Alogging.timing(msg)
 
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message > ", found
  
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test regression()
    def test_regression(self):
        msg = "unit_test_regression_message"
        Alogging.regression(msg)
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test heading()
    def test_heading(self):
        msg = "unit_test_heading_message"
        Alogging.heading(msg)
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test subheading()
    def test_subheading(self):
        msg = "unit_test_subheading_message"
        Alogging.subheading(msg)
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test reportKeywords()
    def test_reportKeywords(self):
        kw = {"input": "helloWorld",
              "list" : [1,2,3,4]}
        Alogging.reportKeywords(kw)
        found = []
        r = open(self.logfile, 'r')
        for line in r.readlines():
            for k, v in kw.iteritems():
                if k in line and str(v) in line:
                    if(self.verbose):
                        print "\nFound message >", line
 
                    found.append(True)
        r.close()
  
        self.assertTrue(len(found) == 2)
 
    # test setlevel() and getEffectiveLevel()
    def test_effectiveLevel(self):
        msg = "unit_test_levels_message"
 
        # check that the logging level is what is expected
        level = Alogging.getEffectiveLevel()
        self.assertTrue(level == self.level)
 
        # set the level to a new value and check again
        Alogging.setLevel(50)
        level = Alogging.getEffectiveLevel()
        self.assertTrue(level == 50)
 
        # log an info message which is below the logging level, this message should not appear
        # in the logs
        Alogging.info(msg)
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                break
        r.close()
        self.assertFalse(found)
 
        Alogging.setLevel(self.level)
        # reset the logging level
        msg += "2"
        # log an info message, which is now above the logging level, this message should appear
        # in the logs
        Alogging.info(msg)
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                r.close()
                break
  
        self.assertTrue(found)
 
    # test warning() and shutdown()
    def test_warning(self):
        msg = "unit_test_warning_message"
        Alogging.warning(msg)
  
        found = False
        r = open(self.logfile, 'r')
        for line in r.readlines():
            if msg in line:
                if(self.verbose):
                    print "\nFound message >", line
 
                found = True
                r.close()
                break
 
        # since this is the last test case, we now close off the logging
        Alogging.shutdown()

        try:
            if os.path.exists(self.logfile):
                os.remove(self.logfile)

        except RuntimeError:
            pass
 
        self.assertTrue(found)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_AdmitLogging.py" 
# or "./unittest_AdmitLogging.py"
if __name__ == '__main__':
    unittest.main()
