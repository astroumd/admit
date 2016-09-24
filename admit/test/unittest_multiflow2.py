#!/usr/bin/env python
#
# Multiflow (type 2) test script.
#
import sys, os, unittest

import admit
from admit.Admit import Admit as Project

class TestClone(unittest.TestCase):
    """
    The FlowManager clone() method allows sub-flows emanating from a single
    root to be grafted onto an independent flow. Functionally this is
    equivalent to a type 2 multiflow, but avoids the need to explicitly create
    a multiflow. It is also not necessary to run/update either flow prior to
    cloning.

    Test sequence:
    1. Create two projects, a File+Flow11 flow and a File+FlowN1+Flow11 flow.
    2. Clone the latter flow into the former by identifying FlowN1 with Flow11.
    4. Attempt to clone an undeclared non-autonomous flow (should fail).
    5. Attempt to clone a    declared non-autonomous flow (should work).
    6. Execute the resulting flow.
    """
    def test_AAAwhoami(self):
        print "\n==== Clone Unit Test ====\n"

    def setUp(self):
        self.outputDir = "mflowclonetest"
        cmd = "rm -rf %s" % self.outputDir
        os.system(cmd)

    def tearDown(self):
        #cmd = "rm -rf %s" % self.outputDir
        #os.system(cmd)
        pass

    def test_clone(self):
        admit.Project = Project()
        p1 = Project(self.outputDir+"/clone-p1")
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid1 = p1.addtask(task)
        #
        task = admit.Flow11_AT(alias="at1")
        task.setkey("file", "Flow11-at1.dat")
        tid2 = p1.addtask(task, [(tid1,0)])

        p2 = Project(self.outputDir+"/clone-p2")
        task = admit.File_AT(touch=True)
        task.setkey("file", "File.dat")
        tid3 = p2.addtask(task)
        #
        # The following 2-to-1 flow simply inputs the same File BDP twice.
        # This is to exercise cloning a sub-root task with multiple inputs 
        # (which is ok since the *sub-flow* stems from only one AT, FlowN1).
        task = admit.FlowN1_AT(alias="at2")
        task.setkey("file", "FlowN1-at2.dat")
        tid4 = p2.addtask(task, [(tid3,0), (tid3, 0)])
        #
        task = admit.Flow11_AT(alias="at3a")
        task.setkey("file", "Flow11-at3a.dat")
        tid5 = p2.addtask(task, [(tid4,0)])

        p1.fm.clone(tid2, (p2.fm, tid4))

        # Task to be re-cloned; avoid filename clashes.
        p2[tid5].setkey("file", "Flow11-at3b.dat")
        p2[tid5].setAlias(({'at3b': 0},0), "at3bb")

        # We should *not* be able to clone a sub-flow containing ATs 
        # receiving inputs beyond the sub-root without an explicit dependency
        # map. Here we append a FlowN1 to p2 to make it depend on the root 
        # File AT, outside the sub-flow.
        task = admit.FlowN1_AT(alias="at4")
        task.setkey("file", "FlowN1-at4.dat")
        tid6 = p2.addtask(task, [(tid5,0), (tid3, 0)])
        try:
          p1.fm.clone(tid2, (p2.fm, tid4))
        except:
          # Clean up aborted clone() (since we're ignoring the failure here).
          # This is highly volatile code users should never imitate!
          p1.fm.remove(p1.fm._tasklevs.keys()[-1])
        else:
          raise Exception, "Non-autonomous clone() unexpectedly succeeded"

        # Non-autonomous sub-flows are ok if all dependencies are explicit.
        try:
          p1.fm.clone(tid2, (p2.fm, tid4), {tid3:tid1})
        except:
          raise Exception, "Non-autonomous clone() unexpectedly failed"

        assert len(p1) == 5

        # This should produce output in clone-p1/ only, not clone-p2/.
        p1.fm.show()
        p1.run()
        p1.write()

        del admit.Project

class TestMultiflow2(unittest.TestCase):
    """
    Multiflow type 2 test case.

    Test sequence:
    1. Create a template (type 2) multiflow.
    2. Create two identical projects and bring them up to date.
    3. Add the two projects to the multiflow's project manager. 
    4. Clone the template multiflow onto each project and run them.

    This test is a use-case experiment. In the end, the multiflow is not
    particularly helpful and is treated like an ordinary flow. Adding the
    individual projects to its manager is gratuitous overhead---we must still
    loop over all projects manually to set up the problem, so cloning can
    be performed on the projects directly.
    """
    def test_AAAwhoami(self):
        print "\n==== Multiflow (Type 2) Unit Test ====\n"

    def setUp(self):
        self.outputDir = "mflow2test"
        cmd = "rm -rf %s" % self.outputDir
        os.system(cmd)

    def test_multiflow2(self):
        admit.Project = Project()

        # Template multiflow is Flow11+FlowN1+Flow11 with two File inputs.
        mflow = Project(self.outputDir+"/mflow")
        tid1 = mflow.addtask(admit.File_AT())
        tid2 = mflow.addtask(admit.File_AT())
        tid3 = mflow.addtask(admit.Flow11_AT(), [(tid2, 0)])
        tid4 = mflow.addtask(admit.FlowN1_AT(touch=True), [(tid2, 0), (tid3, 0)])
        tid5 = mflow.addtask(admit.Flow11_AT(), [(tid4, 0)])
        mflow[tid3].setkey("file", "Flow11a.dat")
        mflow[tid3].setAlias(({'alias1': 0},0),"alias11")
        mflow[tid4].setkey("file", "FlowN1a.dat")
        mflow[tid4].setAlias(({'alias2': 0},0),"alias22")
        mflow[tid5].setkey("file", "Flow11b.dat")
        mflow[tid5].setAlias(({'alias3': 0},0),"alias33")
        mflow[tid5].enabled(False)
        pm = mflow.pm

        for d in [self.outputDir+"/p1", self.outputDir+"/p2"]:
          p = Project(d)
          for f in ["File1.dat", "File2.dat"]:
            p.addtask(admit.File_AT(touch=True, file=f, alias=f[:-4]))
          p.run()
          p.write()
          pid0 = pm.addProject(d)
          assert pid0 != -1

          # Clone template flow onto current project.
          pid = pm.getProjectId(d)
          assert pid == pid0
          at1 = pm.findTaskAlias(pid, "File1")
          at2 = pm.findTaskAlias(pid, "File2")
          assert len(at1) == 1
          assert len(at2) == 1
          id1 = at1[0].id(True)
          id2 = at2[0].id(True)
          mflow.fm.show()
          pm[pid].show()
          pm[pid].fm.clone(id1, (mflow.fm, tid2), {tid1:id2})
          pm[pid].show()
          pm[pid].run()
          pm[pid].write()

          # Dot output test.
          pm[pid][id1].markChanged()
          pm[pid].fm.diagram("%s/flow.dot" % d)
          try:
            os.system("dot -Tpng %s/flow.dot -o %s/flow.png" % (d, d))
          except:
            pass

        del admit.Project

if __name__ == '__main__':
    unittest.main()
