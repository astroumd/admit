#! /usr/bin/env python
#
# Testing util/Table.py functions
#
# Functions covered (22) by test cases:
#    addColumn()
#    addRow()
#    getRow()
#    exportTable()
#    serialize()
#    deserialize()
#    html()
#    addPlane()
#    getPlane()
#    shape()
#    setData()
#    getColumnByName()
#    getFullColumnByName()
#    getColumn()
#    getHeader()
#    getUnits()
#    next()
#    rewind()
#    __init__
#    __str__
#    __len__
#    __eq__
#
# coverage: 92%
#

import admit

import sys, os
import unittest
import numpy as np

class TestTable(unittest.TestCase):
    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Table Class Unit Test"
        self.table = admit.Table()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    # test Table.setkey() and Table.exportTable()
    def test_case1(self):
        cols = ['channel', 'frequency', 'mean', 'sigma', 'max', 'maxposx', 'maxposy', 'min']
        rows = [[0.0, 241.0302, -0.0011, 0.0716, 0.2586, 105.0, 37.0, -0.2861], 
                [1.0, 241.0301, 0.00174, 0.0696, 0.3038, 141.0, 43.0, -0.3391]]

        data = np.array(rows)

        # setkey() - this method is now moved to UtilBase class
        self.table.setkey(name='columns', value=cols)
        self.table.setkey(name='data', value=data)

        # exportTable()
        file = '/tmp/table_exp_%s.txt' % os.getpid()
        self.table.exportTable(file)

        # now check the exported table (data)
        i = 0
        r = open(file, 'r')
        for row in r.readlines():
            if row[0] == '#' :
                continue
            else:
                row = row.rstrip()    # remove \n
                l = row.split('\t')

                # convert strings to float
                new = []
                for item in l :
                    new.append(float(item))

                if(self.verbose):
                    print "\nRow:", i, new

                self.assertEqual(new, rows[i])

                i = i+1

        # cleanup
        r.close()
        if os.path.exists(file):
            os.unlink(file)

    # test Table.addColumn()
    def test_addColumn(self):
        # setup the base table
        self.table.columns = ['test1', 'test2']
        self.table.data = np.array([[0.0, 0.0], [1.0, 1.0]])

        # now add a column
        col = ['test3']
        rows = np.array([[2.0, 2.0]])

        self.table.addColumn(rows, col)

        # new value
        new_cols = ['test1', 'test2', ['test3']]
        new_data = np.array([[0.0, 0.0, 2.0], [1.0, 1.0, 2.0]])

        if(self.verbose):
            print self.table.columns
            print self.table.data

        equal = (new_data == self.table.data).all()
        self.assertTrue(equal)
        self.assertEqual(new_cols, self.table.columns)

    # test Table.addRow() and Table.getRow()
    def test_addRow(self):
        # setup the base table
        self.table.columns = ['test1', 'test2']
        self.table.data = np.array([[0.0, 0.0], [1.0, 1.0]])

        # addRow()
        row = np.array([[2.0, 2.0]])
        self.table.addRow(row)

        new_data = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])

        if(self.verbose):
            print self.table.data

        self.assertTrue((new_data == self.table.data).all())

        # getRow()
        row2 = self.table.getRow(2)
        if(self.verbose):
            print row2

        self.assertTrue((row2 == row).all())

    # test addPlane(), getPlane(), and shape()
    def test_Plane(self):
        # setup plane 1
        plane1 = np.array([[0.0, 0.0], [1.0, 1.0]])
        self.table.data = plane1
        self.table.planes = ['plane1']

        # add plane 2
        plane2 = np.array([[2.0, 2.0], [3.0, 3.0]])
        self.table.addPlane(data=plane2, plane="plane2")

        new_data = np.array([[[0.0, 2.0], [0.0, 2.0]], [[1.0, 3.0], [1.0, 3.0]]])
        shape = (2,2,2)

        # get shape
        ret1 = self.table.shape()

        ret2 = self.table.getPlane(0)
        ret3 = self.table.getPlane(1)
        
        if(self.verbose):
            print self.table.planes
            print "Plane1\n", ret2
            print "Plane2\n", ret3

        self.assertEqual(ret1, shape)
        self.assertTrue((ret2 == plane1).all())
        self.assertTrue((ret3 == plane2).all())
        self.assertTrue((new_data == self.table.data).all())

    # test setData(), getColumnByName(), getFullColumnByName(), 
    # getColumn(), getHeader(), getUnits(), next(), rewind()
    def test_Data(self):
        cols = ['channel', 'frequency', 'mean', 'sigma', 'max', 'maxposx', 'maxposy', 'min']
        unit = ['','GHz','Jy/bm','Jy/bm','Jy/bm','arcsec','arcsec','Jy/bm']
        rows = [[0.0, 241.03, -0.0011, 0.07, 0.26, 105.0, 37.0, -0.29], 
                [1.0, 266.03, 0.00174, 0.08, 0.30, 141.0, 43.0, -0.33]]

        self.table.columns = cols
        self.table.units = unit

        # test setData()
        data = np.array(rows)
        self.table.setData(data)

        self.assertTrue((data == self.table.data).all())

        # test getColumn()
        column = self.table.getColumn(0)
        if(self.verbose):
            print "getColumn", column

        self.assertTrue((column == np.array([0.0, 1.0])).all())

        # test getColumnByName()
        ret1 = self.table.getColumnByName(name='sigma')
        ret2 = self.table.getColumnByName(name='test')
        if(self.verbose):
            print "getColumnByName", ret1
            print "getColumnByName", ret2

        self.assertTrue((ret1 == np.array([0.07, 0.08])).all())
        self.assertTrue(ret2 == None)

        # test getFullColumnByName()
        fc = self.table.getFullColumnByName('channel')
        if(self.verbose):
            print "getFullColumnByName", fc

        self.assertTrue((fc == np.array([0.0, 1.0])).all())

        # test getHeader()
        header = self.table.getHeader()
        if(self.verbose):
            print "getHeader", header

        self.assertEqual(header, cols)

        # test getUnits()
        u = self.table.getUnits()
        if(self.verbose):
            print "getUnits", u

        self.assertEqual(u, unit)

        # test next()
        row1 = self.table.next()
        row2 = self.table.next()
        if(self.verbose):
            print "getNext", row1
            print "getNext", row2

        self.assertTrue((row1 == np.array(rows[0])).all())
        self.assertTrue((row2 == np.array(rows[1])).all())

        # test rewind()
        self.table.rewind()
        row = self.table.next()
        self.assertTrue((row == np.array(rows[0])).all())

    # test Table.serialize() and Table.deserialize()
    def testSerialization(self):
        self.table.description = "This is a table for serialization unit test"
        self.table.columns = ['channel', 'frequency', 'mean', 'sigma', 'max', 'maxposx', 'maxposy', 'min']
        self.table.units = ['','GHz','Jy/bm','Jy/bm','Jy/bm','arcsec','arcsec','Jy/bm']
        self.planes = []
        rows1 = [['a',0.0, 241.32, -0.0011, 0.0716, 0.2586, 105.0, 37.0, -0.2861], 
                 ['b',1.0, 241.31, 0.00174, 0.0696, 0.3038, 141.0, 43.0, -0.3391],
                 ['c',2.0, 241.30, 0.00104, 0.0606, 0.3008, 101.0, 40.0, -0.3091],
                 ['d',3.0, 231.29, 0.30104, 0.3606, 0.3308, 131.0, 30.0, -0.3391]]
        self.table.data = np.array(rows1)
        out = self.table.serialize()
        myTable = admit.Table()
        myTable.deserialize(out)
        if(self.verbose):
            print myTable.html('class="table table-bordered table-striped"')
        self.assertEqual(self.table,myTable)
        self.planes = ['plane1','plane2','plane3']
        plane1 = [[0.0, 241.320, -0.0011, 0.0716, 0.2586, 105.0, 37.0, -0.2861], 
                [1.0, 241.31, 0.00174, 0.0696, 0.3038, 141.0, 43.0, -0.3391],
                [2.0, 241.30, 0.00104, 0.0606, 0.3008, 101.0, 40.0, -0.3091],
                [3.0, 231.29, 0.30104, 0.3606, 0.3308, 131.0, 30.0, -0.3391]]
        plane2 = [[0.0, 241.28, -0.0011, 0.0716, 0.2586, 105.0, 37.0, -0.2861], 
                [1.0, 241.27, 0.00174, 0.0696, 0.3038, 141.0, 43.0, -0.3391],
                [2.0, 241.26, 0.00104, 0.0606, 0.3008, 101.0, 40.0, -0.3091],
                [3.0, 231.25, 0.30104, 0.3606, 0.3308, 131.0, 30.0, -0.3391]]
        plane3 = [[0.0, 241.24, -0.0011, 0.0716, 0.2586, 105.0, 37.0, -0.2861], 
                [1.0, 241.23, 0.00174, 0.0696, 0.3038, 141.0, 43.0, -0.3391],
                [2.0, 241.21, 0.00104, 0.0606, 0.3008, 101.0, 40.0, -0.3091],
                [3.0, 231.20, 0.30104, 0.3606, 0.3308, 131.0, 30.0, -0.3391]]
        rows = [plane1,plane2,plane3]
        self.table.data = np.array(rows)
        out = self.table.serialize()
        self.assertNotEqual(self.table,myTable)
        myTable.deserialize(out)
        self.assertEqual(self.table,myTable)
        self.assertEqual(len(myTable),len(plane1))
        if(self.verbose):
            print myTable.html()
        x = self.table.getRowAsDict(0).keys()
        x.sort()
        self.assertEqual(['channel', 'frequency', 'mean', 'sigma'], x)
        print self.table.getRowAsDict(0)

        # 2D table test (4x9)
        myTable2 = admit.Table()
        for row in rows1:
            myTable2.addRow(row)
        self.assertEqual(len(myTable2),len(rows1))

        # test __len__ and also that an empty Table has zero size
        xTable = admit.Table()
        self.assertEqual(len(xTable),0)
        # empty column header list should raise exception
        self.assertRaises(Exception, xTable.getRowAsDict,0)
        # duplicate string column headers should raise exception
        xTable.columns.append("foo")
        xTable.columns.append("foo")
        self.assertRaises(Exception, xTable.getRowAsDict,0)
        # empty string column headers should raise exception
        myTable.columns[0] = ""
        self.assertRaises(Exception, myTable.getRowAsDict,0)

#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Table.py" 
# or "./unittest_Table.py"
if __name__ == '__main__':
    unittest.main()
