#! /usr/bin/env python
#
# Testing util/stats.py functions
#
# Functions covered by test cases:
#    rejecto1()
#    rejecto2()
#    robust()
#    reducedchisquared()

import admit
import sys, os
import unittest
import numpy as np

class TestStats(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Stats Unit Test"

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test stats.rejecto1() and stats.rejecto2()
    def test_reject(self):
        row = [241.0302, 0.0716, 0.2586, 105.0, 37.0, -0.2861]
        data = np.array(row)
        f = 1.0

        ret1 = admit.stats.rejecto1(data, f)
        l1 = len(ret1)

        if(self.verbose):
            print "\nStats rejecto1:", ret1

        # rejecto1 should remove 241.0302 from the original data set
        t1 = [0.0716, 0.2586, 105.0, 37.0, -0.2861]
        self.assertEqual(l1, 5)
        self.assertEqual(t1, ret1)

        ret2 = admit.stats.rejecto2(data, f)
        l2 = len(ret2)

        if(self.verbose):
            print "\nStats rejecto2:", ret2

        # rejecto2 should remove 241.0302, 105.0, and -0.2861
        t2 = np.array([0.0716, 0.2586, 37.0])
        self.assertEqual(l2, 3)
        self.assertTrue((t2 == ret2).all())

    # test stats.reducedchisquared()
    def test_reducedchisquared(self):
        data = np.array([4.53636592,4.5755861,4.2789703,4.4716104,4.37937843,4.57905511,
                4.40811491, 4.36778876, 4.16284264, 3.97475077, 3.73553099, 4.20574665,
                4.21115653, 3.95044353, 4.22345639, 4.44637076, 4.6424006,  4.39353177,
                4.39433815, 4.15240269, 4.57450134, 4.50496741, 4.03287604, 4.08435447,
                4.49688665, 4.29365314, 4.43879618, 4.37604294, 4.2458898,  4.05097928,
                3.74197024, 3.91985054, 4.17819863, 4.15648265, 3.961444,   3.88149212,
                4.171982,   4.42076355, 4.40572373, 3.98986664, 3.89450797, 3.99845834,
                4.30907563, 4.10298631, 4.1802792,  4.20504231, 3.84852219, 3.92706871])

        sigma = 0.8
        model = []
        for m in data:
            sample = np.random.normal(m, sigma)
            model.append(sample)

            if(self.verbose):
                print m, sample

        ret = admit.stats.reducedchisquared(data, model, 3)
        if(self.verbose):
            print ret

        self.assertGreater(ret, 0.0)
        self.assertLess(ret, 2.0)

    # test stats.robust()
    def test_robust(self):
        data = np.array([241.03, 0.0716, 0.2586, 105.0, 37.0, -0.2861])

        f = 1.0
        ret = admit.stats.robust(data, f)  # [-- 0.0716 0.2586 105.0 37.0 -0.2861]

        l = len(ret)   # 241.03 is the outlier and removed but the length is still 6
        if(self.verbose):
            print ret

        self.assertEqual(l, 6)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_stats.py" 
# or "./unittest_stats.py"
if __name__ == '__main__':
    unittest.main()
