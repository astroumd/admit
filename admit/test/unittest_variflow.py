#!/usr/bin/env python
#
# Variadic flow test script.
#

import sys, os, unittest
import admit

class TestVariflow(unittest.TestCase):
    """
    Variadic flow tests.

    The instantiated flow exercises several special cases:

    (1) sub-flows connected to fixed and/or variadic ports on the same AT
    (2) sub-flows connected to fixed and/or variadic ports on multiple ATs
    (3) sub-flows containing another variadic task
    (4) ATs directly connected to multiple variadic tasks

    It is highly instructive to examine the flow diagram to better understand
    the flow topology.
    """

    # Use setUp to do any test initialization.
    def setUp(self):
        self.verbose = False
        self.testName = "Variflow Unit Test"
        self.outputDir = "vflow"

    def tearDown(self):
        cmd = "rm -rf %s" % self.outputDir
        os.system(cmd)

    def test_AAAwhoami(self):
        print "==== %s ====\n" % self.testName

    def test_variflow(self):
        p = admit.Project(self.outputDir)
        p.setlogginglevel(50)
        p.addtask(admit.File_AT(alias='root', file='root', touch=True))
        p.addtask(admit.Flow11_AT(alias='flow1'), ['root'])
        p.addtask(admit.Flow1N_AT(alias='flow1N',n=2, touch=True, exist=True),
                  ['root'])
        p.addtask(admit.Flow11_AT(alias='sub1Nf'), ['flow1N'])
        p.addtask(admit.Flow11_AT(alias='sub1Nv'), [('flow1N', 1)])
        p.addtask(admit.FlowMN_AT(alias='flowMN',n=2, touch=True, exist=True),
                  ['flow1', 'root', ('flow1N', 1)])
        p.addtask(admit.Flow11_AT(alias='subMNf'), ['flowMN'])
        p.addtask(admit.FlowN1_AT(alias='subMNv', touch=True),
                  [('flowMN',0), ('flowMN',2)])
        p.addtask(admit.FlowN1_AT(alias='flowN1', touch=True),
                  ['flow1N', ('flowMN', 1)])
        p.addtask(admit.Flow11_AT(alias='subN1'), ['flowN1'])

        p.show()
        for n in [2, 3, 1, 2]:
          if(p.fm.find(lambda at: at._alias == 'flow1N')):
             p['flow1N'].setkey('n', n)
          if(p.fm.find(lambda at: at._alias == 'flowMN')):
              p['flowMN'].setkey('n', n+1)

          p.run()
          p.show()

        self.assertLessEqual(len(p), 20, "Incorrect task count")


if __name__ == '__main__':
    unittest.main()
