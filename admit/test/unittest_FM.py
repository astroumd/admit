#! /usr/bin/env python

# Flow Manager Unit Test
#
# Functions covered: 20
#    __init__
#    add()
#    find()
#    remove()
#    show()
#    replace()
#    __len__
#    __contains__
#    __iter__
#    __getitem__
#    __delitem__
#    __setitem__
#    connectInputs()
#    verify()
#    stale()
#    inFlow()
#    downstream()
#    clone()
#    showsetkey()
#    script()
#
# Functions not covered: 4
#    run()
#    dryrun()
#    __str__()
#    diagram()

# 24

import sys, os
import shutil

import admit
from admit.AT import AT
from admit.bdp.File_BDP import File_BDP as BDP
from admit.Admit import Admit as Project

import unittest
from _ast import Num

class TestFlowManager(unittest.TestCase):

    # Use setUp to do any test initialization.
    # WARNING: this is re-run prior to *every* test method.
    def setUp(self):
        self.verbose = False
        self.testName = "Flow Manager Unit Test"
        self.task = list()
        self.fm = admit.Flow()
        admit.Project = Project('/tmp/FM_%d.admit' % os.getpid())

    # WARNING: this is re-run prior to *every* test method.
    def tearDown(self):
        basedir = admit.Project.baseDir
        del admit.Project
        shutil.rmtree(basedir)

    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName

    # test add() and remove()
    def test_flow(self):
        # Test insertion of tasks (FM method: add(at, stuples, dtuples))
        if (self.verbose) : print "\n------- Test Insertion ------------"

        # connection map diagram: a0->a1->a2->a3
        # structure of an element of the triple-nested dictionary of connmap:
        #     src_taskid: {des_taskid: {des_bdpport: (si,sp, di,dp)}}

        self.correct_connmap = {0: {1: {0: (0, 0, 1, 0)}},
                                1: {2: {0: (1, 0, 2, 0)}},
                                2: {3: {0: (2, 0, 3, 0)}}}

        for i in range(0,4):
            name = "TEST_AT%d" % i;
            if (self.verbose) : print "inserting task %s " % name
            a = AT()
            a._baseDir = admit.Project.baseDir

            # Each AT needs an output BDP
            b = BDP();
            b.type="TEST_BDP%d" % i

            a._bdp_out.append( b )
            self.task.append( a )
            if i == 0:
                taskid = self.fm.add( self.task[i] )
            else:
                taskid = self.fm.add( self.task[i], [(self.task[i-1]._taskid,0)])

        if (self.verbose) : self.fm.show()
        self.assertEqual(self.fm._connmap, self.correct_connmap)
        if (self.verbose) : print "-------- End of Test Insertion ------------"

        # Print the 4-tuples of the connection map
        if (self.verbose) : print "\n------- Print Connection Map ------------"
        cm = self.fm._connmap
        if (self.verbose) : print cm
        for si in cm.keys():
            for di in cm[si].keys():
                for dp in cm[si][di].keys():
                    if (self.verbose) : print cm[si][di][dp]

        if (self.verbose) : print "-------- End of Print ConnMap ------------"

        # Remove a2 and its downstream from a0->a1->a2->a3
        # The result diagram is a0->a1
        if (self.verbose) : print "\n------- Test Remove ------------"
        self.correct_connmap = {0: {1: {0: (0, 0, 1, 0)}}}
        self.fm.remove(2)
        if (self.verbose): self.fm.show()
        self.assertEqual(self.fm._connmap, self.correct_connmap)
        if (self.verbose) : print "-------- End of Test Remove ------------"

    # test add(), find(), replace(),
    #__len__(), __contains()__
    def test_task1(self):
        # add first task
        task = admit.File_AT(touch=True)
        tid1 = self.fm.add(task)

        if (self.verbose):
            print "FM unit test task1 ID:", tid1

        # add another task
        task = admit.Flow11_AT()
        task.setkey("file", "Flow11.dat")
        tid2 = self.fm.add(task, [(tid1,0)])

        if (self.verbose):
            print "FM unit test task2 ID:", tid2

        # now try to find the tasks
        tasks = self.fm.find(lambda at: at.id() < 100)

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

        # test replace()
        task = admit.FlowMN_AT()
        self.fm.replace(tid2, task)

        # to find new tasks
        tasks = self.fm.find(lambda at: at.id() < 100)
 
        if(self.verbose):
            print "Found tasks after replace Flow11 with FlowMN:", tasks
 
        # first task (File_AT)
        type = isinstance(tasks[0], admit.File_AT)
        if(self.verbose):
            print "After replace AT id:", tasks[0].id()
 
        self.assertTrue(type)
 
        # second task (FlowMN_AT)
        type = isinstance(tasks[1], admit.FlowMN_AT)
        if(self.verbose):
            print "After replace AT id:", tasks[1].id()
 
        self.assertTrue(type)

        # the number of tasks
        num = len(self.fm)
        if(self.verbose):
            print "The number of tasks:", num

        self.assertEqual(2, num)

        # Test __contains__()
        contains = 100 in self.fm   # should be false
        self.assertFalse(contains)

        contains = tid1 in self.fm  # should be true
        self.assertTrue(contains)

        # test __iter__
        # we should have two tasks
        counter = 0
        for t in self.fm:
            counter += 1
            if(self.verbose):
                print "Task id:", t

        self.assertEqual(counter, 2)

    # test add(), connectInputs(), verify(), and show()
    #__getitem__(), __delitem__(), __setitem__()
    def test_task2(self):
        # add first task
        task1 = admit.File_AT(touch=True)
        tid1 = self.fm.add(task1)
        bdp = admit.File_BDP()
        task1.addoutput(bdp)

        # add another task
        task2 = admit.Flow11_AT()
        task2.setkey("file", "Flow11.dat")
        tid2 = self.fm.add(task2, [(tid1,0)])

        # test connectInputs
        self.fm.connectInputs()

        num = len(self.fm)  # should be 2
        self.assertTrue(num == 2)

        if (self.verbose):
            print "The number of tasks in flow:", num
            print "The task IDs:", tid1,tid2

        # first task (File_AT)
        t1 = self.fm[tid1]    # call __getitem__
        type = isinstance(t1, admit.File_AT)
        if(self.verbose):
            print "After call __getitem__", t1.id()
 
        self.assertTrue(type)

        # second task (Flow11_AT)
        t2 = self.fm[tid2]    # call __getitem__
        type = isinstance(t2, admit.Flow11_AT)
        if(self.verbose):
            print "After call __getitem__", t2.id()

        self.assertTrue(type)

        # test __setitem__
        newtask = admit.FlowMN_AT()
        newtask.setkey("file", "FlowMN.txt")

        self.fm[tid2] = newtask  # call __setitem__
        if(self.verbose):
            self.fm.show()

        # check to see if task2 got overwritten
        t2 = self.fm[tid2]
        type = isinstance(t2, admit.FlowMN_AT)

        self.assertTrue(type)

        # now restore Flow11_AT
        self.fm[tid2] = task2  # call __setitem__
        if(self.verbose):
            self.fm.show()

        # check it again
        t2 = self.fm[tid2]
        type = isinstance(t2, admit.Flow11_AT)

        self.assertTrue(type)

        # test __delitem__ (delete Flow11)
        at = self.fm[tid2]
        del self.fm[tid2]    # call __delitem__

        num = len(self.fm)  # should be 1 now
        self.assertTrue(num == 1)

        # Add task back.
        self.fm[tid2] = at  # call __setitem__

        # test verify()
        check = self.fm.verify()

        self.assertTrue(check)

    # test inFlow(), downstream(), stale(), clone()
    def test_flow2(self):
        # Construct a flow: File_AT -> Flow11_AT -> Flow1N_AT

        # add first task
        task1 = admit.File_AT(touch=True)
        tid1 = self.fm.add(task1)
        bdp = admit.File_BDP()
        task1.addoutput(bdp)

        # add second task
        task2 = admit.Flow11_AT()
        task2.setkey("file", "Flow11.dat")
        tid2 = self.fm.add(task2, [(tid1,0)])

        # add third task
        task3 = admit.Flow1N_AT()
        task3.setkey("file", "Flow1N.dat")
        tid3 = self.fm.add(task3,[(tid2,0)])

        task4 = admit.FlowMN_AT()

        # test inFlow()
        found = self.fm.inFlow(task1)
        self.assertTrue(found)  # should be true

        # test downstream of tid2 (including tid2)
        dstream = self.fm.downstream(tid2)
        self.assertEquals(dstream, set([tid2, tid3]))

        # test stale()
        for ds in dstream:
            isStale = self.fm._tasks[ds].isstale()  # check before mark
            if isStale:
                self.fm._tasks[ds].markUpToDate()

            isStale = self.fm._tasks[ds].isstale()  # check after mark
            self.assertFalse(isStale)  # should not be stale

        self.fm.stale(tid2)  # call stale()

        # after calling stale()
        for ds in dstream:
            isStale = self.fm._tasks[ds].isstale()
            self.assertTrue(isStale)  # all ATs in downstream should be stale now

        # clone from tid2 (Flow11_AT) in the flow
        cloned = self.fm.clone(tid2)
        if (self.verbose):
            self.fm.show()

    # test showsetkey() and script()
    def test_showsetkey(self):
        # add one task
        task1 = admit.File_AT(touch=True)
        task1.setkey("file", "File.dat")
        tid1 = self.fm.add(task1)

        # add another task
        task2 = admit.Flow11_AT()
        task2.setkey("file", "Flow11.dat")
        tid2 = self.fm.add(task2, [(tid1,0)])

        # test showsetkey()
        name1 = '/tmp/test_FM_showsetkey.%s' % os.getpid()
        self.fm.showsetkey(name1)
        if(self.verbose):
            print "===== Keys ====="
            cmd = "cat %s" % name1
            os.system(cmd)
            print "===== End ====="

        # test script
        name2 = '/tmp/test_FM_script.%s' % os.getpid()
        file = open(name2, mode='w')
        self.fm.script(file)
        file.close()

        if(self.verbose):
            print "===== Script Created ====="
            cmd = "cat %s" % name2
            os.system(cmd)
            print "===== End ====="

        # cleanup
        if os.path.exists(name1):
            os.remove(name1)

        if os.path.exists(name2):
            os.remove(name2)
#----------------------------------------------------------------------
# Below is provided to run the tests on command line
# by either using "python unittest_FM.py" or "./unittest_FM.py"
if __name__ == '__main__':
    unittest.main()
