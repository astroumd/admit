#! /usr/bin/env python
#
# Testing utility functions
#
# Functions covered by test cases:
#    admitroot()
#    freqtovel()
#    veltofreq()
#    undoppler()
#    rmdir()
#    rm()
#    remove()
#    rename()
#    find_files()
#    fitgauss1D()
#    interpolatespectrum()
#    iscloseinE()
#    rrplace()
#    getplain()
#    format_chem()
#    isotopecount()
#    getmass()
#    fitgauss1D()
#    casa_argv()

import admit
import sys, os
import unittest
import numpy as np
import tempfile

# speed of light in km/s
speed = 299792.458

class TestUtils(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utils Unit Test"

    def tearDown(self):
        #self.cleanup()
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test getting admit-root directory with utils.admitroot
    def test_admitroot(self):
        root1 = os.getenv("ADMIT")
        root2 = admit.utils.admit_root()
        if(self.verbose):
            print "\nAdmit Root:", root1

        self.assertEqual(root1, root2)

    # test frequency to velocity
    def test_freqtovel(self):
        global speed
        v = admit.utils.freqtovel(103.22, 3.69)
        if(self.verbose):
            print "\nVelocity:", v

        self.assertAlmostEqual(v, 10717.2463672)

    # test velocity to frequency
    def test_veltofreq(self):
        global speed
        f = admit.utils.veltofreq(10717.0, 103.22)
        if(self.verbose):
            print "\nFrequency:", f

        self.assertAlmostEqual(f, 3.68991517)

    # test converting sky frequency to source rest frequency
    def test_undoppler(self):
        global speed
        f = admit.utils.undoppler(103.22,10717.0)
        if(self.verbose):
            print "\nSource Rest Frequency:", f

        self.assertAlmostEqual(f, 107.04671274)

    # test removing a directory with utils.rmdir()
    def test_rmdir(self):
        dir = tempfile.mkdtemp()
        before = os.path.exists(dir)

        admit.utils.rmdir(dir)
        after = os.path.exists(dir)
        if(self.verbose):
            print "\nDirectory exists:", before
            print "After utils.rmdir", after

        self.assertEqual(before, True)
        self.assertEqual(after, False)

    # test removing a file with utils.rm()
    def test_rm(self):

#       mkstemp returns a tuple containing an OS-level handle to an open file (as would
#       be returned by os.open()) and the absolute pathname of that file, in that order.
        temp = tempfile.mkstemp(prefix='util_', 
                                suffix='_test_file1', 
                                dir='/tmp')

        fname = temp[1]   # example tuple = (3, '/tmp/util_B5l4xj_test_file')
        test = os.path.exists(fname)

        if test:
            admit.utils.rm(fname)

        after = os.path.exists(fname)
        if(self.verbose):
            print "\nFile exists:", test
            print "After utils.rm", after

        self.assertEqual(test, True)
        self.assertEqual(after, False)

    # test utils.remove()
    def test_remove(self):
        file = tempfile.mkstemp(prefix='util_', 
                                suffix='_test_file2', 
                                dir='/tmp')

        name = file[1]
        test = os.path.exists(name)
        if test:
            admit.utils.remove(name)

        after = os.path.exists(name) and os.path.isfile(name)
        if(self.verbose):
            print "\nutils.remove: file exists:", test
            print "After utils.remove", after

        self.assertEqual(test, True)
        self.assertEqual(after, False)

        dir = tempfile.mkdtemp()

        test = os.path.exists(dir)
        if test:
            admit.utils.remove(dir)

        after = os.path.exists(dir) and os.path.isdir(dir)
        if(self.verbose):
            print "utils.remove: directory exists:", test
            print "After utils.remove", after

        self.assertEqual(test, True)
        self.assertEqual(after, False)

    # test rename a file
    def test_rename(self):

        tfile = tempfile.mkstemp(suffix='_test_file', dir='/tmp')
        tmp1 = tfile[1]
        tmp2 = tmp1.replace('test_file', 'replaced')

        if(self.verbose):
            print tmp1, tmp2

        test1 = os.path.exists(tmp1)
        test2 = os.path.exists(tmp2)

        admit.utils.rename(tmp1, tmp2)

        after1 = os.path.exists(tmp1)
        after2 = os.path.exists(tmp2)

        self.assertEqual(test1, True)
        self.assertEqual(test2, False)
        self.assertEqual(after1, False)
        self.assertEqual(after2, True)

        # cleanup
        if os.path.exists(tmp2):
            os.remove(tmp2)

    # test finding files in a directory
    def test_find_files(self):
        tmp1 = tempfile.NamedTemporaryFile(suffix='_test_test_test', dir='/tmp')
        tmp2 = tempfile.NamedTemporaryFile(suffix='_test_test_test', dir='/tmp')

        if(self.verbose):
                print "temp files", tmp1.name, tmp2.name
        names = []
        flist = admit.utils.find_files('/tmp', '*test_test_test*')
        for file in flist:
            if(self.verbose):
                print "\nFound:", file
 
            if file == tmp1.name or file == tmp2.name :
                names.append(file)

        size = len(names)
        test1 = tmp1.name in names
        test2 = tmp2.name in names
        self.assertEqual(size, 2)
        self.assertTrue(test1)
        self.assertTrue(test2)

        # cleanup
        tmp1.close()
        tmp2.close()

    def test_interpolatespectrum(self):
        spec = np.array([0.0, 4.5755861,4.2789703,4.37937843, np.nan, 4.57905511,
                         4.4081149,4.3677887,4.1628426,3.9747507, 0.0, np.nan])

        ret = admit.utils.interpolatespectrum(spec, 1.0, 1.0)

        if(self.verbose):
            print "\n1:", ret[0]
            print "\n5:", ret[4]
            print "\n11:", ret[10]
            print "\n12:", ret[11]

        self.assertEqual(ret[0], 1.0)
        self.assertEqual(ret[11], 1.0)
        self.assertGreater(ret[4], 0.0)
        self.assertGreater(ret[10], 0.0)

    # test if two lines are very close in energy
    def test_iscloseinE(self):
        case1 = admit.utils.iscloseinE(5.0089, 5.0099)
        case2 = admit.utils.iscloseinE(5.0089, 7.0019)

        self.assertTrue(case1)
        self.assertFalse(case2)

    # test replacing the suffix of a filename
    def test_rreplace(self):
        before = "a/b/c/file.x"
        after = "a/b/c/file.y"
        ret = admit.utils.rreplace(before, 'x', 'y')

        self.assertEquals(after, ret)

    # test get_plain()
    def test_getplain(self):

        str = "CH3COOHv=0"
        form1 = "CH3COOH"
        ret1 = admit.utils.getplain(str)

        str = "g-CH3CH2OH"
        form2 = "CH3CH2OH"
        ret2 = admit.utils.getplain(str)

        str = "SO&Sigma"
        form3 = "SO"
        ret3 = admit.utils.getplain(str)

        self.assertEquals(form1, ret1)
        self.assertEquals(form2, ret2)
        self.assertEquals(form3, ret3)

    # test formatting a chemical formula for display
    def test_format_chem(self):
        str1 = "C4H5Cl"
        exp1 = "C$_4$H$_5$Cl"
        out1 = admit.utils.format_chem(str1)
        if(self.verbose):
            print "\nformatted formula:", out1

        str2 = "H13CO+"
        exp2 = "H$^{13}$CO+"
        out2 = admit.utils.format_chem(str2)
        if(self.verbose):
            print "\nformatted formula:", out2

        self.assertEquals(exp1, out1)
        self.assertEquals(exp2, out2)

    # test isotopecount in a molecule
    def test_isotopecount(self):
        str1 = "C4H5Cl"
        num1 = 0
        out1 = admit.utils.isotopecount(str1)
        if(self.verbose):
            print "\nFormatted formula:", out1

        str2 = "H13CO+"
        num2 = 1
        out2 = admit.utils.isotopecount(str2)

        if(self.verbose):
            print "\nFormatted formula:", out2

        self.assertEquals(num1, out1)
        self.assertEquals(num2, out2)

    # test getmass (the rough mass of a molecule)
    def test_getmass(self):
        str1 = "CO"
        mass1 = 28
        out1 = admit.utils.getmass(str1)
        if(self.verbose):
            print "\nMolecule Mass:", out1

        self.assertEquals(mass1, out1)

#         str2 = "SiO"
#         mass2 = 44
#         out2 = admit.utils.getmass(str2)  # returned 48. should be 44?
#                                           # a bug in getmass() to be fixed
#         if(not self.verbose):
#             print "\nMolecule Mass:", out2
#
#         self.assertEquals(mass2, out2)

    # test gaussian1D() and fitgauss1D()
    def test_fitgauss1D(self):
        xdata = np.linspace(0,4,20)
        intensity = 2.5
        center = 1.3
        sigma = 0.5
        y = admit.utils.gaussian1D(xdata, intensity, center, sigma)
        ydata = y + 0.2 * np.random.normal(size=len(xdata))
        oprt, cov = admit.utils.fitgauss1D(xdata, ydata)

    # test casa_argv which removes the input argv up to '-c'
    # then returns the rest of the argv
    def test_casa_argv(self):
        arg = ['casapy.py', 
                '--quiet', '--nogui', '-c', 
                'admit1.py', 
                'data.fits', 'x']
        str = ['admit1.py', 'data.fits', 'x']
        ret = admit.utils.casa_argv(arg)
        if(self.verbose):
            print "\nArguments:", str

        self.assertEquals(str, ret)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_utils.py" 
# or "./unittest_utils.py"
if __name__ == '__main__':
    unittest.main()
