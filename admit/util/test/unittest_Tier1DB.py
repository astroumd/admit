#! /usr/bin/env python
#
# Testing util/Tier1DB.py functions
#
# Functions covered by test cases:
#    searchtransitions()
#    add()    -- called by searchtransitions()
#    getone()
#    getall()
#    get()
#    searchhfs()
#    query()
#    close()
#    __init__
#
# Code coverage percentage: 100%

import admit
import sys, os
import unittest

class TestTier1DB(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Tier1DB Class Unit Test"
        self.db = admit.Tier1DB()

    def tearDown(self):
        self.db.close()

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test searchtransitions() and getone()
    def test_transitions(self):

        """ 
        The columns of Transitions table:
        SPECIES(formula),NAME,FREQUENCY,QUANTUM_NUMBERS(transition),
        LINE_STR,LOWER_ENERGY,UPPER_ENERGY,HFS
        
        Expected query result:
           Species = 'CCH',
           Name = 'Ethynyl',
           Frequency = 873.09954,
           Quantum = 'N=10-9,J=19/2-17/2,F=10-9',
           Lins_str = 5.87967014312744140625e+00,
           Lower energy = 1.886183929443359375e+02,
           Upper energy = 2.30520324707031249995e+02,
           HFS = 140
        """

#         f = open("/tmp/db.dump", 'w')
#         for lines in self.db.cursor.iterdump():
#             f.write('%s\n' % lines)

        # query Transitions table
        self.db.searchtransitions(freq=[872.0, 874.0], eu=[2.2e+02, 2.4e+02], 
                                  el=[1.78e+02, 1.89e+02], linestr=[5.7, 5.9],
                                  species='CCH')
        ret = self.db.getone()

        if(self.verbose):
            print "\nTier1 Database Transitions Tbale Query result:"
            for i in range(len(ret)):
                print ret[i]

        engy = ret.getkey('energies')
        self.assertEqual('CCH', ret.getkey('formula'))
        self.assertEqual('Ethynyl', ret.getkey('name'))
        self.assertEqual(873.09954, ret.getkey('frequency'))
        self.assertEqual('N=10-9,J=19/2-17/2,F=10-9', ret.getkey('transition'))
        self.assertAlmostEqual(5.87967014312744140625e+00, ret.getkey('linestrength'))
        self.assertAlmostEqual(1.886183929443359375e+02, engy[0])
        self.assertAlmostEqual(2.30520324707031249995e+02, engy[1])
#        self.assertEqual(140, ret[7]) # LineData does not have HFS key

    # test searchhfs() and getall()
    def test_hfs(self):
 
        """ 
        The columns of HFS table:
        TRANSITION, FREQUENCY, QUANTUM_NUMBERS, LINE_STR, LOWER_ENERGY, UPPER_ENERGY
 
        Expected query result for Transition = 140:
        Row #1
           Frequency = 873.09954
           Quantum = 'N=10-9,J=19/2-17/2,F=9-8'
           Lins_str = 5.291200160980225
           Lower energy = 188.6192626953125
           Upper energy = 230.5211944580078

        Row #2
           Frequency = 873.11769
           Quantum = 'N=10-9,J=19/2-17/2,F=9-9'
           Lins_str = 0.033410001546144485
           Lower energy = 188.61839294433594
           Upper energy = 230.5211944580078

        """
 
        # query HFS table
        self.db.searchhfs(140)
        rows = self.db.getall()

        # row #1
        ret = rows[0]
        if(self.verbose):
            print "\nTier1 Database HFS Table Row 1 Query result:"
            for i in range(len(ret)):
                print ret[i]

        engy = ret.getkey('energies')
        self.assertEqual(873.09954, ret.getkey('frequency'))
        self.assertEqual('N=10-9,J=19/2-17/2,F=9-8', ret.getkey('transition'))
        self.assertAlmostEqual(5.291200160980225, ret.getkey('linestrength'))
        self.assertAlmostEqual(188.6192626953125, engy[0])
        self.assertAlmostEqual(230.5211944580078, engy[1])

        # row #2
        ret = rows[1]
        if(self.verbose):
            print "\nTier1 Database HFS Table Row 2 Query result:"
            for i in range(len(ret)):
                print ret[i]

        engy = ret.getkey('energies')
        self.assertEqual(873.11769, ret.getkey('frequency'))
        self.assertEqual('N=10-9,J=19/2-17/2,F=9-9', ret.getkey('transition'))
        self.assertAlmostEqual(0.033410001546144485, ret.getkey('linestrength'))
        self.assertAlmostEqual(188.61839294433594, engy[0])
        self.assertAlmostEqual(230.5211944580078, engy[1])

    # test query() and get()
    def test_query(self):
        query = "select SPECIES, NAME, FREQUENCY, QUANTUM_NUMBERS, \
                 LINE_STR, LOWER_ENERGY, UPPER_ENERGY, HFS from Transitions \
                 where FREQUENCY between 872.0 and 874.0 and \
                 UPPER_ENERGY between 220.0 and 240.0 and \
                 LOWER_ENERGY between 178.0 and 189.0 \
                 and LINE_STR between 5.70 and 5.90 and \
                 SPECIES like '%CCH%'"
        self.db.query(query)
        rows = self.db.get(2)

        # the list should have only one row
        ret = rows[0]
        if(self.verbose):
            print "\nTier1 Database Query result:"
            for i in range(len(ret)):
                print ret[i]

        self.assertEqual('CCH', ret[0])
        self.assertEqual('Ethynyl', ret[1])
        self.assertEqual(873.09954, ret[2])
        self.assertEqual('N=10-9,J=19/2-17/2,F=10-9', ret[3])
        self.assertAlmostEqual(5.87967014312744140625, ret[4])
        self.assertAlmostEqual(1.886183929443359375e+02, ret[5])
        self.assertAlmostEqual(2.30520324707031249995e+02, ret[6])
        self.assertEqual(140, ret[7])

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Tier1DB.py" 
# or "./unittest_Tier1DB.py"
if __name__ == '__main__':
    unittest.main()
