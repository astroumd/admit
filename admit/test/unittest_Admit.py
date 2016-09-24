#!/usr/bin/env python
#
# Admit class Unit Test 
#

# Functions covered by test cases: 24
#    __init__()
#    __str__()
#    __len__()
#    __del__()
#    setlogginglevel()
#    getlogginglevel()
#    mkdir()
#    addTask()
#    __getitem__()
#    getFlow()
#    getManager()
#    findtask()
#    dir()
#    userdata()
#    get()
#    script()
#    showsetkey()
#    set()
#    has()
#    find_bdp()
#    find_files()
#    setdir()
#    tesdir()
#    _markstalefrom()

# Functions Not covered: 18
#    plotparams()
#    show()
#    exit()
#    run()
#    print_all()
#    print_summary()
#    print_methods()
#    print_attributes()
#    updateHTML
#    atToHTML
#    logToHTML
#    write()
#    writeXML()
#    export()
#    startDataServer()
#    _onpost()
#    _dotdiagram()
#    _serveforever()

# 42 total

# Other (not implemented) 3
#    check()
#    discover()
#    read()


import sys, os, unittest

import admit
from admit.util.AdmitLogging import AdmitLogging as logging

class TestAdmit(unittest.TestCase):

    # test initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Admit Unit Test"

        # sometimes CWD is set to self.outputDir that is deleted by
        # tearDown() function, then we need to change back to the parent dir
        try:
            os.getcwd()

        except OSError:
            os.chdir('..')

        self.outputDir = "AdmitUnitTest"
        self.p = admit.Project(self.outputDir)

    # clean up
    def tearDown(self):
        if os.path.exists(self.outputDir):
            cmd = "rm -rf %s" % self.outputDir
            os.system(cmd)

    # print unit test name
    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName

    # test __str__, __len__
    def test_case1(self):
        self.p.__str__()

        # to get the number of tasks
        ret = self.p.__len__()  # should be 0
        if(self.verbose):
            print "The number of tasks:", ret

        self.assertEqual(ret, 0)

    # test setlogginglevel(), getlogginglevel(), and __del__
    def test_logging(self):

        self.p.setlogginglevel(logging.ERROR)
        ret = self.p.getlogginglevel()  # logging.ERROR value is 40
        if(self.verbose):
            print ret

        # logging shutdown
        self.p.__del__()

        self.assertEqual(ret, logging.ERROR)

    # test mkdir
    def test_mkdir(self):
        # temp directory name
        dir = '/tmp/admit_unit_test_%s' % os.getpid()

        before = os.path.exists(dir)  # should be false
        self.p.mkdir(dir)
        after = os.path.exists(dir)
        if(self.verbose):
            print "\nDirectory exists:", before
            print "After mkdir:", after

        self.assertEqual(before, False)
        self.assertEqual(after, True)

        # change back to preset current dir
        self.p.tesdir()

        # cleanup
        if os.path.exists(dir):
            os.rmdir(dir)

    # test addtask(), __getitem__()
    def test_addtask(self):

        # add first task
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid1 = self.p.addtask(task)

        # add another task
        task = admit.Flow11_AT(alias="at" + self.p.baseDir[-2]) # at1 or at2
        task.setkey("file", "Flow11.dat")
        tid2 = self.p.addtask(task, [(tid1,0)])

        # to get the AT with task_id = 0
        at = self.p.__getitem__(0)
        if(self.verbose):
            print at

        # check class type - should be the first task (File_AT)
        type = isinstance(at, admit.File_AT)

        self.assertTrue(type)

        # to get the AT with task_id = 1
        at = self.p.__getitem__(1)
        if(self.verbose):
            print at

        # check class type - should be the second task (Flow11_AT)
        type = isinstance(at, admit.Flow11_AT)

        self.assertTrue(type)

    # test getFlow(), getManager()
    def test_getFM(self):
        fm = self.p.getFlow()
        type = isinstance(fm, admit.Flow)

        if(self.verbose):
            print "getFlow() returned FM:", type

        self.assertTrue(type)

        mg = self.p.getManager()

        if(self.verbose):
            print "getManager() returned Manager:", type

        type = isinstance(mg, admit.Manager)

        self.assertTrue(type)

    # test findtask()
    def test_findtask(self):
        # add first task
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid1 = self.p.addtask(task)

        # add another task
        task = admit.Flow11_AT()
        task.setkey("file", "Flow11.dat")
        tid2 = self.p.addtask(task, [(tid1,0)])

        tasks = self.p.findtask(lambda at: at.id() < 100)
        if(self.verbose):
            print "Found tasks:", tasks

        # check class type of the first task (File_AT)
        type = isinstance(tasks[0], admit.File_AT)
        if(self.verbose):
            print "AT id:", tasks[0].id()

        self.assertTrue(type)

        # check class type of second task (Flow11_AT)
        type = isinstance(tasks[1], admit.Flow11_AT)
        if(self.verbose):
            print "AT id:", tasks[1].id()

        self.assertTrue(type)

    # test dir()
    def test_dir(self):
        currentDir = os.getcwd()
        baseDir = currentDir + os.sep + self.outputDir + os.sep

        ret = self.p.dir()
        if(self.verbose):
            print "Base Directory:", ret

        self.assertEqual(baseDir, ret)

    # test userdata() and get()
    def test_userdata(self):

        key = 'admit_unit_test'
        val = ['test1', 1, 'admit']

        task = admit.Flow11_AT()
        task._userdata = {}
        task._userdata[key] = val

        self.p.addtask(task)
        self.p.userdata()
        ret = self.p.get('admit_unit_test')
        if(self.verbose):
            print "User Data:", ret

        self.assertEqual(ret, val)

    # test script()
    def test_script(self):
        # add one task
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid1 = self.p.addtask(task)

        # add another task
        task = admit.Flow11_AT()
        task.setkey("file", "Flow11.dat")
        tid2 = self.p.addtask(task, [(tid1,0)])

        name = '/tmp/test_script.%s' % os.getpid()
        self.p.script(name)
        if(self.verbose):
            print "===== Script Created ====="
            cmd = "cat %s" % name
            os.system(cmd)
            print "===== End ====="

        # cleanup
        if os.path.exists(name):
            os.remove(name)

    # test showsetkey()
    def test_showsetkey(self):
        # add one task
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid1 = self.p.addtask(task)

        # add another task
        task = admit.Flow11_AT()
        task.setkey("file", "Flow11.dat")
        tid2 = self.p.addtask(task, [(tid1,0)])
 
        name = '/tmp/test_showsetkeys.%s' % os.getpid()
        self.p.showsetkey(name)
        if(self.verbose):
            print "===== Keys ====="
            cmd = "cat %s" % name
            os.system(cmd)
            print "===== End ====="

        # cleanup
        if os.path.exists(name):
            os.remove(name)

    # test set(), get(), and has() on userData
    def test_set(self):
        # add one task
        task = admit.File_AT(touch=True)
        name = "File.dat"
        task.setkey("file", name)
        self.p.addtask(task)

        # try to get the value of 'file' - should be None because it is not in user data
        ret = self.p.get('file')
        if(self.verbose):
            print "User Data:", ret

        self.assertEqual(ret, None)

        # set the key
        key = 'admit_unit_test'
        val = ['test2', 2, 'admit']

        userdata = {}
        userdata[key] = val

        # set()
        self.p.set(**userdata)
        ret = self.p.get('admit_unit_test')
        if(self.verbose):
            print "User Data:", ret

        self.assertEqual(ret, val)

        # has()
        ret = self.p.has('admit_unit_test')
        if(self.verbose):
            print "User Data:", ret

        self.assertTrue(ret)

    # test find_bdp()
    def test_find_bdp(self):
        project = admit.Project()

        # add one task
        task = admit.File_AT(touch=True)
        name = "File.dat"
        task.setkey("file", name)

        project.addtask(task)  # add task

        # now add an output bdp
        obdp = admit.File_BDP('Test')
        task.addoutput(obdp)

        self.p.addtask(task)

        # find_bdp() will search Admit output data directory for *.bdp files
        # should return an empty list since no *.bdp file created by this test
        ret = self.p.find_bdp()
        outdir = self.p.dir()
        if(self.verbose):
            if len(ret):
                print "Found BDPs in", outdir
            else:
                print "No BDPs Found in", outdir

        self.assertTrue(len(ret) == 0)

    # test find_files()
    def test_find_files(self):

        # find_files() will search Admit data directory for files with a given pattern
        ret = self.p.find_files(pattern="*.log")
        outdir = self.p.dir()
        if(self.verbose):
            if len(ret):
                print "Found files in", outdir, ret
            else:
                print "No file Found in", outdir

        self.assertTrue(len(ret) >= 0)

    # test setdir()
    def test_setdir(self):
        # temp directory name
        dir = '/tmp/test_setdir_%s' % os.getpid()
  
        before = os.path.exists(dir)  # should be false
        self.p.setdir(dir)
        after = os.path.exists(dir)
        if(self.verbose):
            print "\nDirectory exists:", before
            print "After setdir:", after

        self.assertEqual(before, False)
        self.assertEqual(after, True)

        # change back to preset current dir
        self.p.tesdir()

        # cleanup
        if os.path.exists(dir):
            os.rmdir(dir)

    # test tesdir()
    def test_tesdir(self):

        self.p.tesdir()
        cwd1 = ''
        try:
            cwd1 = os.getcwd()

        except OSError:
            if(self.verbose):
                print "\nCannot get current work directory."

        if(self.verbose):
            print "\nCurrent Directory:", cwd1

        cwd2 = self.p.currDir
        self.assertEqual(cwd1, cwd2)

    # test _markstalefrom()
    def test_markstalefrom(self):
        # add one task
        task1 = admit.File_AT(touch=True)
        task1.setkey("file", "File.dat")
        task1._stale = False
        tid1 = self.p.addtask(task1)
        if(self.verbose):
            print "Task1 state:", task1._stale

        # add another task
        task2 = admit.Flow11_AT()
        task2.setkey("file", "Flow11.dat")
        task2._stale = False
        tid2 = self.p.addtask(task2, [(tid1,0)])
        if(self.verbose):
            print "Task2 state:",task2._stale

        # mark - only the second task state will be changed
        self.p._markstalefrom(tid1)

        if(self.verbose):
            print "===== Task Ids =====", tid1, tid2

        if(self.verbose):
            print "Task1 state after marking:", task1._stale
            print "Task2 state after marking:", task2._stale

        self.assertEqual(task1._stale, False)
        self.assertEqual(task2._stale, True)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Admit.py" 
# or "./unittest_Admit.py"
if __name__ == '__main__':
    unittest.main()
