#! /usr/bin/env python
#
# Testing AT base class
#

# total functions 67
#
# Functions Covered: 39
#    __init__
#    __len__
#    __contains__
#    __iter__
#    __setitem__
#    __getitem__
#    len2()
#    setlogginglevel()
#    getlogginglevel()
#    seteffectivelevel()
#    geteffectivelevel()
#    baseDir()
#    dir()
#    mkext()
#    enabled()
#    isstale()
#    markUpToDate()
#    markChanged()
#    setProject()
#    getProject()
#    id()
#    mkdir()
#    setkey()
#    getkey()
#    haskey()
#    set_bdp_in()
#    addinput()
#    clearinput()
#    set_bdp_out()
#    addoutput()
#    clearoutput()
#    setloggername()
#    getloggername()
#    isAutoAlias()
#    get()
#    set()
#    setAlias()
#    releaseAlias()
#    checktype()

# Functions Not covered: 10
#    __str__
#    run()
#    dryrun()
#    show()
#    summary()
#    html()
#    reset()
#    userdata()
#    link()
#    unlink()

import admit
from admit.AT import AT
from admit.bdp.BDP import BDP
from admit.bdp.File_BDP import File_BDP
import admit.util.bdp_types as bt

import sys, os
import unittest

class TestAT(unittest.TestCase):

    # initialization.
    def setUp(self):
        self.verbose = False
        self.testName = "AT Base Class Unit Test"
        self.project = admit.Project("UnitTest")

#     def tearDown(self):
#         print "Done"

    def test_AAAwhoami(self):
        print "==== %s ====" % self.testName

    # test input bdp
    def test_input(self):
        at = AT({'alias': 'a'})
        bdpin = len(at._bdp_in)
        if(self.verbose):
            print "\nAT Class number of BDP in:", bdpin

        self.assertEqual(bdpin, 0)  ## should have no input bdp

    # test __len__()
    def test_output(self):
        at = AT({'alias': 'b'})
        bdpout = len(at)
        if(self.verbose):
            print "\nAT Class number of BDP out:", bdpout
 
        self.assertEqual(bdpout, 0)  ## should have no output bdp
 
    # test len2()
    def test_len2(self):
        at = AT({'alias': 'c'})
        tuple = at.len2() # bdp_in and bdp_out tuple
        if(self.verbose):
            print "\nAT Class (bdp_in, bdp_out):", tuple
 
        self.assertEqual(tuple, (0,0))  ## should be (0,0)
 
    def test_version(self):
        at = AT({'alias': 'd'})
        print "\nAT Class Version:", at._version
 
    # test setlogginglevel and getlogginglevel methods
    def test_logginglevel(self):
        """
            CRITICAL    50
            ERROR       40
            WARNING     30
            INFO        20
            DEBUG       10
            NOTSET      0
        """
        at = AT({'alias': 'e'})
        at.setlogginglevel(50)
        level = at.getlogginglevel()
 
        if(self.verbose):
            print "\nAT Class logging level", level
 
        self.assertEqual(level, 50)
 
    # test seteffectivelevel and geteffectivelevel methods
    def test_effectivelevel(self):
        at = AT({'alias': 'f'})
        at.seteffectivelevel(40)
        level = at.geteffectivelevel()
        if(self.verbose):
            print "\nAT Class effective logging level", level
 
        self.assertEqual(level, 40)

    def test_loggername(self):
        at = AT({'alias': 'log'})
        name = "admit_logger"
        at.setloggername(name)
        ret = at.getloggername()
        if(self.verbose):
            print "\nAT Class Logger Name:", name

        self.assertEqual(ret, name)

    def test_baseDir(self):
        at = AT({'alias': 'g'})
        basedir = at.baseDir("/tmp/")
        if(self.verbose):
            print "\nAT Class base directory", basedir
 
        self.assertEqual(basedir, "/tmp/")
 
    def test_dir(self):
        at = AT({'alias': 'h'})
        basedir = at.baseDir("/tmp/")
        fullpath = at.dir("test.test")
        if(self.verbose):
            print "\nAT Fullpath:", fullpath
 
        self.assertEqual(fullpath, "/tmp/test.test")
 
    def test_mkext(self):
        at = AT({'alias': 'k'})
        t1 = at.mkext("x","z")         # return 'x-k.z'
        t2 = at.mkext("x.y","z")       # return 'x-k.z'
        t3 = at.mkext("x.y","z", "a")  # return 'x-a.z'

        self.assertEqual(t1, "x-k.z")
        self.assertEqual(t2, "x-k.z")
        self.assertEqual(t3, "x-a.z")
 
    def test_enabled(self):
        at = AT({'alias': 'm'})
        at.enabled(False)
        after = at._enabled
        if(self.verbose):
            print "\nAT Class state _enabled", after
 
        self.assertEqual(after, False)

    # test isstale() and markUpToDate()
    def test_markUpToDate(self):
        at = AT({'alias': 'n'})
        state = at.isstale()
        if(self.verbose):
            print "\nAT Class state", state
 
        self.assertTrue(state)  # should be True

        at.markUpToDate()
        state = at.isstale()
        if(self.verbose):
            print "\nAT Class state", state  # should be False
 
        self.assertFalse(state)
 
    def test_markChanged(self):
        at = AT({'alias': 'p'})
        at.markChanged()
        state = at._stale
        if(self.verbose):
            print "\nAT Class state _stale", state
 
        self.assertEqual(state, True)
 
    # test setProject(), getProject(), and id() of AT class
    def test_projectID(self):
        at = AT({'alias': 'q'})
        self.project.addtask(at)

        # get the taskid before adding project id
        tid = at._taskid
        if(self.verbose):
            print "\nAT Class taskid (before):", at._taskid
 
        # now set the project id
        pid = 2
        at.setProject(pid)
        pid = at.getProject()
        if(self.verbose):
            print "\nAT Class project", pid
 
        self.assertEqual(pid, 2)
 
        # now strip out the project id from _taskid
        taskid = at.id(True)
        if(self.verbose):
            print "\nAT Class taskid (after):", taskid
 
        self.assertEqual(taskid, tid)
 
    def test_mkdir(self):
        at = AT({'alias': 's'})
        # test with full path
        tmpdir = "/tmp/test1_%d" % os.getpid()
        at.mkdir(tmpdir)
        t1 = os.path.exists(tmpdir)
 
        self.assertEqual(t1, True)
        os.rmdir(tmpdir)
 
        # test with relative path
        basedir = at.baseDir("/tmp/")        # set base dir to /tmp/
        tail = "test2_%d" % os.getpid()
        tmpdir = "/tmp/" + tail
        at.mkdir(tail)
        t1 = os.path.exists(tmpdir)

        self.assertEqual(t1, True)
        os.rmdir(tmpdir)
 
    # test setkey(), getkey(), and haskey()
    def test_key(self):
        at = AT({'alias': 't', 'test_key': 'at_test'})
        key = "test_key"
        val = "TEST"

        t1 = at.haskey("testtesttest")  # invalid key
        self.assertEqual(t1, False)

        # test haskey()
        t1 = at.haskey(key)  # AT should have the key set at init
        self.assertTrue(t1)

        # test setkey()
        at.setkey(name=key, value=val, isinit=True)

        # test getkey()
        ret = at.getkey(key)
        if(self.verbose):
            print "\n test key:", ret

        self.assertEqual(ret, "TEST")
 
        # test {key:val} way of setting a key
        at.setkey(name={key:"TEST2"})
 
        ret = at.getkey(key)
        if(self.verbose):
            print "\n alias key:", ret
 
        self.assertEqual(ret, "TEST2")

    # test isAutoAlias()
    def test_isAutoAlias(self):
        at = AT()
        ret = at.isAutoAlias()
        self.assertTrue(ret)  # should be true

        at = AT({'alias': 'alias_test', 'test_key': 'at_test'})
        ret = at.isAutoAlias(withEmpty=False)
        self.assertFalse(ret)  # should be false

    # test get(), set() attributes
    # test setAlias(), releaseAlias()
    def test_get_set(self):
        at = AT({'alias': 'test'})
        ret = at.get('_alias')
        self.assertTrue(ret == 'test')

        at.set('_alias', 'alias_test')
        ret = at.get('_alias')
        self.assertEqual(ret, 'alias_test')

        at.setAlias(({'w':0},0), 'alias_test_2')
        ret = at.get('_alias')
        self.assertEqual(ret, 'alias_test_2')

#         at.releaseAlias()
#         ret = at.get('alias')
#         self.assertEqual(ret, None)  # after release it, the alias should be none now

    def test_checktype(self):
        at = AT()
        bdp = BDP()
        ret = at.checktype(bdp)
    
        self.assertEquals(ret, None) # should be None without raising an exception
    
    # test set_bdp_in, addinput, clearinput, set_bdp_out
    # addoutput, clearoutput, __contains__, __iter__, __getitem__
    def test_bdp(self):
        at = AT({'alias': 'w'})
        self.project.addtask(at)

        # input bdp
        at.set_bdp_in([(BDP,1, bt.REQUIRED)])
        bdpin = len(at._bdp_in)
        if(self.verbose):
            print "\nAT Class number of BDP input:", bdpin

        self.assertEqual(bdpin, 1)  ## should have one input bdp
 
        at.clearinput()
        bdpin = at._bdp_in[0]
        if(self.verbose):
            print "\nAT Class BDP input:", bdpin
 
        self.assertEqual(bdpin, None)
 
        at.addinput(BDP())
        bdpin= at._bdp_in[0]
         
        self.assertFalse(bdpin is None)
 
        # output bdp
        at.set_bdp_out([(BDP,1)])  # set_bdp_out
        bdpout = len(at._bdp_out)
        if(self.verbose):
            print "\nAT Class number of BDP output:", bdpout
 
        self.assertEqual(bdpout, 1)  ## should have one output bdp

        # test clearoutput
        at.clearoutput()
        bdpout = at._bdp_out[0]
        if(self.verbose):
            print "\nAT Class BDP output:", bdpout
 
        self.assertEqual(bdpout, None)

        output1 = BDP()
        at.addoutput(output1)

        isIn = output1 in at   # call __contains__
        self.assertTrue(isIn)

        #at.set_bdp_out([(File_BDP,2)])
        output2 = File_BDP({'file': 'test.file'})

        at[0] = output2   # call __setitem__

        isIn = output2 in at   # call __contains__ again
        self.assertTrue(isIn)

        # test __iter__
        counter = 0
        for b in at._bdp_out:
            counter += 1
            if(self.verbose):
                print "Output BDP:", b

        self.assertEqual(counter, 1)

        item1 = at[0]  # call __getitem__ at index = 0
        type = isinstance(item1, admit.File_BDP)
        self.assertTrue(type)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_AT.py"
# or "./unittest_AT.py"
if __name__ == '__main__':
    unittest.main()
