#!/usr/bin/env python
#
# Multiflow (type 1) test script.
#
# (1) Create two new projects, each containing a simple File+Flow11 flow.
# (2) Add alias names to the final ATs ("at1" and "at2").
# (3) Run the flows to bring them up to date.
# (4) Create a new project (the multiflow).
# (5) Add the other two projects to it.
# (6) Find ATs (by alias) and add them to the multiflow.
# (7) Extend the multiflow with a FlowN1 AT (N = 2) and run it.
# (8) Change keyword on one of the root ATs and re-run the flow.

import sys, os, unittest

import admit

class TestMultiflow1(unittest.TestCase):

    # Use setUp to do any test initialization.
    def setUp(self):
        self.verbose = False
        self.testName = "Multiflow (Type 1) Unit Test"
        self.outputDir = "mflow1test"

    def tearDown(self):
        cmd = "rm -rf %s" % self.outputDir
        os.system(cmd)

    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName

    def test_multiflow(self):

        # Parent projects.
        p1 = admit.Project(self.outputDir+"/p1")
        p2 = admit.Project(self.outputDir+"/p2")
        for p in [p1, p2]:
          task = admit.File_AT(touch=True)
          task.setkey("file", "File.dat")
          tid1 = p.addtask(task)

          task = admit.Flow11_AT(alias="at" + p.baseDir[-2]) # at1 or at2
          task.setkey("file", "Flow11.dat")
          tid2 = p.addtask(task, [(tid1,0)])

          p.run()

        # Multiflow project.
        mflow = admit.Project(self.outputDir+"/mflow")

        # Add parent projects to the multiflow.
        # Note they must be completely up-to-date for this to succeed.
        pid1 = mflow.pm.addProject(self.outputDir+"/p1")
        pid2 = mflow.pm.addProject(self.outputDir+"/p2")
        print "Parent project p1 ID = ", pid1
        print "Parent project p2 ID = ", pid2

        # Find some ATs to link into the multiflow.
        # Here searching is done by alias name.
        stuples = []
        for pid in [pid1, pid2]:
            alias = "at" + mflow.pm[pid].baseDir[-2]
            print "Looking for alias", alias, "..."
            ats = mflow.pm.findTaskAlias(pid, alias)
            print "Result:", ats
            self.assertEqual(len(ats), 1, "Found wrong number of matches")
            self.assertEqual(ats[0]._alias, alias, "Alias mismatch")
            self.assertNotEqual(ats[0].getProject(), 0, "Null project ID")
            print alias, "belongs to project ", \
                  mflow.pm.getProjectDir(ats[0].getProject())

            # Add task to the multiflow (must be a root task---no stuples).
            tid = mflow.addtask(ats[0])
            print "tid=%d stale=%s" % (tid, mflow[tid].isstale())
            self.assertNotEqual(tid, -1, "mflow.addtask(" + alias + ") failed")
            stuples.append((tid, 0))

        # Combine output from the two newly linked tasks.
        print "stuples =", stuples
        tid = mflow.addtask(admit.FlowN1_AT(file="FlowN1.dat", touch=True), stuples)
        self.assertNotEqual(tid, -1, "mflow.addtask(FlowN1) failed")

        mflow.show()
        # Run the multiflow.
        mflow.run()

        # Make at2 out of date, then re-run the multiflow to update everything.
        at2 = mflow.findtask(lambda at: at._alias == "at2")
        self.assertEqual(len(at2), 1, "Found wrong number of matches for at2")
        self.assertEqual(at2[0]._alias, "at2", "Alias mismatch for at2")
        at2[0].setkey("file", "Flow11-at2.dat")
        mflow.show()
        mflow.run()


if __name__ == '__main__':
    unittest.main()
