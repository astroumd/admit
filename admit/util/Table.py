""" .. _Table-api:

    **Table** --- Raw tabular data base.
    ------------------------------------

    This module defines the Table class for TABLE entries in BDPs.
"""

#system imports
import numpy as np
import xml.etree.cElementTree as et
import copy
import textwrap
import ast

# ADMIT imports
from UtilBase import UtilBase
import bdp_types as bt


class Table(UtilBase):
    """ Defines the basic table structure used in ADMIT.

        The Table class is a container for holding data in tabular format. The
        table can hold data in column-row format and also in plane-column-row
        format. Data can be added in instantiation, by columns, by rows, or by
        entire planes.

        Parameters
        ----------
        keyval : dict
          Any valid attributes can be specified to the constructor.

        Attributes
        ----------
        columns : List containing the column headers, optional
           (defaults to an empty list)

        units : List containing the units of each column, optional
           (defaults to an empty list)

        planes : List containing labels for each plane, optional
           (defaults to an empty list)

        data : A numpy array containing the data, can be 1D, 2D, or 3D, optional
           (defaults to an empty array)

        description : A string for a description/caption of the table, optional
           (defaults to an empty string)

    """
    def __init__(self, **keyval):
        """Constructor
        """
        self.columns = []            # column labels
        self.units = []              # units of columns
        self.planes = []             # label for planes
        self.data = np.array([])     # 1d, 2d, 3d
        self.description = ""
        UtilBase.__init__(self, **keyval)

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + "Table :" + bt.format.END
        if len(self.data.shape) < 3:
            self.exportTable("/dev/stdout")
        else:
            for plane in range(self.data.shape[2]):
                print bt.format.BOLD + "Plane : " + str(plane) + bt.format.END
                self.exportTable("/dev/stdout", plane=plane)
                print "\n"
        return "\n"

    def _jsondict(self,prefix=False):
        """prepare as json formatted. note simply using json.dump()
           will not work because numpy arrays are not JSON serializable.
           Furthermore json.dump(self.data.tolist()) is not useful because
           it spits out a bare list, when what we need is a dict.
           2D TABLES ONLY!
        """
        # have to replace ' with " for javascript to interpret
        # kooky two-step process needed
        # http://stackoverflow.com/questions/13409559/
        s = str(self.columns)
        colstr = s.replace("\\'", 'REPLACEME').replace("'", '"').replace('REPLACEME', "\\'")
        s = str(self.units)
        unitsstr = s.replace("\\'", 'REPLACEME').replace("'", '"').replace('REPLACEME', "\\'")
        if prefix:
            outstr = '"linetable":'+ '{\n"columns":' + colstr +',\n"units":'+unitsstr+',\n'
        else:
            outstr = '{\n"columns":' + colstr +',\n"units":'+unitsstr+',\n'
        datastr = '"lines":['
        datalist = self.data.tolist()
        j =0
        for line in datalist:
           linestr = '{'
           for i in range(len(line)):
               linestr = linestr+'"'+self.columns[i]+'":"'+line[i]+'"'
               if i != len(line)-1:
                  linestr = linestr + ','
           linestr = linestr + '} '
           if j != len(datalist)-1:
               linestr = linestr + ',\n'
           j+=1
           datastr = datastr+linestr

        outstr = outstr+datastr+']\n}\n'
        return outstr

    def html(self,css=None) :
        """Create an HTML representation of the table

           Parameters
           ----------
           css : str
               A string that may refer to a CSS or style parameter. This can be used for special
               formatting of the table, e.g. striping. Default: No extra formatting.


           Returns
           -------
           string
               HTML <table> representation.
        """
        if css:
            tablestr = '<h3>%s</h3>\n<table %s><thead><tr>' % (self.description,css)
        else:
            tablestr = '<h3>%s</h3>\n<table><thead><tr>' % self.description

        for h in self.columns:
            tablestr = tablestr + '<th>%s</th>' % h
        tablestr = tablestr + '</tr>\n'
        for u in self.units:
            tablestr = tablestr + '<th>[%s]</th>' % u
        tablestr = tablestr + '</tr></thead>\n<tbody>'
        np.set_string_function(None)
        np.set_printoptions(
              threshold = None,
              nanstr = 'NaN',
              infstr = 'Inf',
              formatter={'float' : '<td>{:.3E}</td>'.format,
                         #'str_kind'   : '<td>{}</td>'.format
                         'str_kind'   : lambda x: self._formatcell(x)
                        })
        for row in self.data:
            #strip beginning and ending [,] from string.
            rowstr = str(row)[1:-1]
            tablestr = tablestr + '<tr>'+rowstr+'</tr>\n'
        tablestr = tablestr + '</tbody></table>\n'
        np.set_printoptions(formatter=None)
        return tablestr

    def _formatcell(self,str_value):
        """Format a cell for an HTML table. This method is needed to
           deal with numpy array's unfortunate feature of
           converting all numbers to strings in an array if
           any cell in the array is string.

           Parameters:
           ----------
           str_value: str
                The string from a cell of a numpy array.

           Returns
           -------
           HTML-formatted cell: <td>value</td>.  If the input value can
           be converted to a float, return it in scientific notation %.3E,
           otherwise return the string
        """
        try:
           # if float conversion works, then the string is really a
           # number and we can use scientific notation
           q = float(str_value)
           return '<td>{:.3E}</td>'.format(q)
        except:
           return '<td>{}</td>'.format(str_value)

    def exportTable(self, fileName, plane=0, cols=[], fixcols=[]):
        """ Method to export a table to ascii text

            Note only one plane at the time can be written.  Alternatively
            one could allow multiple planes, and use another keyword for the fixcols=[],
            i.e. the columns that do not change per plane. This has not been implemented.

            Parameters
            ----------
            fileName : str
                The name of the file to write the table to

            plane : int or list, optional
                What plane to export, defaults to the first plane (0).
                A list can be given if multiple planes need to be written.

            cols  : if given, a subset of these named columns will be written
                Columns are written in the order they were listed originally,
                not the order in this given list.
                For multi-plane tables, these should be the columns that vary.

            fixcols : if given, these are the named columns that are common for
                all planes.

            Returns
            -------
            None
        """
        # @todo implement multiple planes using a fixcols=
        # @todo csv=True/False option?
        #
        # if cols was not given, use all columns from the table for output
        if len(cols) == 0:
            cols = self.columns
        f = open(fileName, 'w')

        # Determine if the data are 2D or 3D and act appropriately
        if len(self.data.shape) == 2:
            # header first
            line = "#|"
            for i in cols :
                line += i + "\t|"
            f.write(line + "\n")

            x, y = self.data.shape
            for i in range(0, x) :
                line = ""
                for j in range(0, y) :
                    if self.columns[j] not in cols:
                        continue
                    line += str(self.data[i][j]) + "\t"
                f.write(line + "\n")

        elif len(self.data.shape) == 3 and type(plane) == type([]):

            line = "#|"
            for i in cols:
                line += i + "\t|"
            f.write(line + "\n")
            x, y, z = self.data.shape
            if(plane > z) :
                raise Exception("Requested plane does not exist in table")
            for i in range(0, x) :
                line = ""
                for j in range(0, y) :
                    if self.columns[j] not in cols:
                        continue
                    line += str(self.data[i][j][plane]) + "\t"
                f.write(line + "\n")
        elif len(self.data.shape) == 3:
            line = "#|"
            for i in cols:
                line += i + "\t|"
            f.write(line + "\n")
            x, y, z = self.data.shape
            if(plane > z) :
                raise Exception("Requested plane does not exist in table")
            for i in range(0, x) :
                line = ""
                for j in range(0, y) :
                    if self.columns[j] not in cols:
                        continue
                    line += str(self.data[i][j][plane]) + "\t"
                f.write(line + "\n")
        else:
            print "Cannot write out this table at this time. len(data.shape) = %d" % len(self.data.shape)
        f.close()

    # these methods allow for the addition of columns, rows, and planes to existing tables
    def addColumn(self, data, col=""):
        """ Add a column to the table

            Adds the given column to the table and recomputes the minimum and maximum.
            The column must have the same length as the other columns or numpy will throw
            an exception.

            Parameters
            ----------
            data : list or numpy array
                The data of the column to be added

            col : str, optional
                The name of the column

            Returns
            -------
            None
        """
        # add the data to the array, converting as necessary
        if isinstance(data, list):
            data = np.array([data])
        self.data = np.concatenate((self.data, data.T), axis=1)
        # add the column name to the list
        self.columns.append(col)

    def addRow(self, row):
        """ Add a row to the table

            Adds the given row to the table and recomputes the minimum and
            maximum.

            Parameters
            ----------
            row : list or numpy array
                The data of the row to be added

            Returns
            -------
            None
        """
        # add the row, converting as necessary
        if isinstance(row, list):
            row = np.array([row], dtype=object)
        #print row.shape
        #print self.data.shape
        if len(self.data.shape) == 1 and self.data.shape[0] == 0:
            self.data = copy.deepcopy(row)
        else:
            self.data = np.concatenate((self.data, row), axis=0)
        #print self.data.shape, "XX"

    def addPlane(self, data, plane=""):
        """ Add a plane to the table

            Adds the given plane to the table and recomputes the minimum and
            maximum. The plane must have the same dimensions as the other planes
            or numpy will throw an exception.

            Parameters
            ----------
            data : list or numpy array
                The data of the plane to be added

            plane : str, optional
                The name of the plane. See getPlane() how to access a plane

            Returns
            -------
            None
        """
        # add the plane, converting as necessary
        if isinstance(data, list):
            data = np.array([data])
        sh = self.data.shape
        if len(sh) == 1:
            if sh[0] != 0:
                raise Exception("Data in this table are only 1D, you cannot add a plane. Try using addRow.")
            else:
                self.data = data
        elif len(sh) == 2:
            self.data = np.dstack([self.data, data])
        else:
            if len(data.shape) == 2:
                self.data = np.concatenate((self.data, np.expand_dims(data, axis=2)), axis=2)
            else:
                self.data = np.concatenate((self.data, data), axis=2)
        # add the name to the planes
        self.planes.append(plane)

    def setData(self, data):
        """ Set the data of the table all at once

            Parameters
            ----------
            data : list or numpy array
                The actual data to insert into the table

            Returns
            -------
            None
        """
        # set the data, converting as necessary
        if isinstance(data, list) :
            data = np.array(data)
        self.data = data

    def getColumnByName(self, name, plane=0, typ=None):
        """ Get a column by its name

            Parameters
            ----------
            name : str
                The name of the column to retrieve

            plane : int
                The plane to retrieve it from if the table is 3D

            typ : various
                The data type to convert the returning data to.
                Default: None (no conversion)

            Returns
            -------
            The data from the column as a numpy array, or None if the column name
            does not exist.
        """
        if len(self.data.shape) == 3:
            try:
                i = self.columns.index(name)
                temp = self.data.T[plane]
                if typ is None:
                    return temp[i]
                else:
                    return temp[i].astype(typ)
            except:
                return None

        try :
            i = self.columns.index(name)
            if typ is None:
                return self.data.T[i]
            else:
                return self.data.T[i].astype(typ)
        except :
            return None

    def getFullColumnByName(self, name, typ=None):
        """ Method to get a full column (single column from all planes) by name

            Parameters
            ----------
            name : str
                The name of the column to get

            typ : various
                The data type to convert the returning data to.
                Default: None (no conversion)

            Returns
            -------
            Numpy array containing the data of the full column.

        """
        try:
            temp = np.array([self.getColumnByName(name, 0)])
            if len(self.data.shape) < 3:
                if len(temp.shape) == 2:
                    if temp.shape[0] == 1 and temp.shape[1] == 1:
                        if typ is None:
                            return np.reshape(temp, -1)
                        else :
                            return np.reshape(temp, -1).astype(typ)
                if typ is None:
                    return np.squeeze(temp)
                else:
                    return np.squeeze(temp).astype(typ)
            for i in range(1, self.data.shape[2]):
                col = np.array([self.getColumnByName(name, i)])
                temp = np.concatenate((temp, col), axis=0)
            if typ is None:
                return temp
            else:
                return temp.astype(typ)
        except:
            raise

    def getColumn(self, col, plane=0, typ=None):
        """ Get a single column by its index

            Parameters
            ----------
            col : int
                The index of the column to retrieve

            plane : int
                The plane to retrieve it from if the table is 3D

            typ : various
                The data type to convert the data to.
                Default: None

            Returns
            -------
            The data from the column as a numpy array, or None if the column index
            does not exist.
        """
        if len(self.data.shape) == 3:
            try:
                temp = self.data.T[plane]
                if typ is None:
                    return temp[col]
                else:
                    return temp[col].astype(typ)
            except:
                return None

        try:
            if typ is None:
                return self.data.T[col]
            else:
                return self.data.T[col].astype(typ)
        except:
            return None

    def getHeader(self):
        """ Get the header information

            Parameters
            ----------
            None

            Returns
            -------
            list of the column headers

        """
        return self.columns

    def getUnits(self):
        """ Get the units information

            Parameters
            ----------
            None

            Returns
            -------
            list of the units headers

        """
        return self.units

    def getRow(self, row):
        """ Get data from a specific row

            Parameters
            ----------
            row : int
                The row to get

            Returns
            -------
            a numpy array of the data of the specified row, or None if the
            row does not exist
        """
        try:
            return self.data[row]
        except:
            return None

    def getRowAsDict(self, row):
        """ Get data from a specific row in dictionary format with the column headings as keys.
            If there are no column headings or two column headings are identical or column header
            has an empty string an exception is thrown.   Note: this is not terribly useful for multi-plane Tables.

            Parameters
            ----------
            row : int
                The row to get

            Returns
            -------
            A dictionary of the data of the specified row, or None if the
            row does not exist
        """
        # check for empty column header list
        if not self.columns:
           errmsg = "Can't make a dictionary -- Table has no column headers defined"
           raise Exception, errmsg

        # check for duplicates
        if len(self.columns) != len(set(self.columns)):
           errmsg = "Can't make a dictionary -- Table has duplicate column headers"
           raise Exception, errmsg

        try:
            x = dict()
            for i in range(len(self.data[row])):
                 #check first for empty column header
                 if not self.columns[i]:
                     errmsg = "Can't make a dictionary -- Table has empty column header %d" % i
                     raise Exception, errmsg
                 x[self.columns[i]] = self.data[row][i]
            return x
        except IndexError:
            return None

    def clear(self, full=False):
        """ Method to clear out the data from the table

            Parameters
            ----------
            full : bool
                If True then clear header and other meta data also
                Default: False

            Returns
            -------
            None

        """
        del self.data
        self.data = np.array([])     # 1d, 2d, 3d
        self.planes = []             # label for planes
        if full:
            self.columns = []            # column labels
            self.units = []              # units of columns
            self.description = ""

    def getPlane(self, pln):
        """ Method to get a single plane from the table

            Parameters
            ----------
            pln : int
                The plane number to get (0 based)
                No Default.

            Returns
            -------
            Numpy array containing the requested plane

        """
        if len(self.shape()) < 3:
            return copy.deepcopy(self.data)
        return copy.deepcopy(self.data.T[pln].T)

    def next(self):
        """ Method to get the next row from a table

            Parameters
            ----------
            None

            Returns
            -------
            List of the next row, None if there are no more.
        """
        if not hasattr(self, "lastrow"):
            self.lastrow = 0
            return self.getRow(0)
        self.lastrow += 1
        return self.getRow(self.lastrow)

    def rewind(self):
        """ Reset the "next" counter to the beginning

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        del self.lastrow

    def shape(self):
        return self.data.shape


    def serialize(self):
        """Create a string representation of the table that can
           be converted to native Python structures with ast.literal_eval
           or back to a Table with deserialize().
           Intended for the summary but can be used wherever.

           Parameters
           ----------
           None

           Returns
           -------
           A string representation of the Table that can be converted back
           to a Table with deserialize().
        """
        x = dict(self.__dict__)
        # convert the numpy array to a Python list
        # so we can write it as a string.
        x["data"] = x["data"].tolist()
        return str(x)

    def deserialize(self,serial):
        """Create a Table from serialized data created by serialize().

           Parameters
           ----------
           serial : The string representation of a Table in the format from
           deserialize().

           Returns
           -------
           None
        """
        # Do not convert directly to self.__dict__ because
        # the Table structure may change between versions, e.g.
        # an attribute may be added or deleted.
        # So we can only safely convert attributes which are valid
        # for this Table instance.
        x = ast.literal_eval(serial)
        # convert from Python list to numpy array
        x["data"] = np.array(x["data"])
        for i in self.__dict__:
           if i in x:
               self.__dict__[i] = x[i]

    def __eq__(self, table):
        """Define equivalency for two Tables

            Parameters
            ----------
            table : Table
                The Table to compare to this one.

            Returns
            -------
            Boolean
                Whether or not the two Tables are identical

        """
        if(not isinstance(table,self.__class__)):
            return False
        try:
            for i in self.__dict__:
                if i == "data":
                    #np.allclose is only for numeric types!
                    #if not np.allclose(self.data, table.data):
                    # ideally we want np.array_equal(self.data,table.date),
                    # but for numpy version <1.8, np.array_equal can't
                    # compare strings.  So for now, use np.all(x==y).
                    if not np.all(self.data == table.data):
                        return False
                    continue
                if cmp(getattr(self, i), getattr(table, i)) != 0:
                    return False
        except:
            return False
        return True

    def __len__(self):
        """The Table length is defined as the number of rows in the table
        not including the column header and units, i.e. the number of
        data rows.

        Returns
        -------
        int
           number of data rows in the table.
        """
        # The shape tuple is (planes,rows,columns) for 3D
        # but (rows,columns) for 2D
        # If the data array is empty then the tuple value is
        # (0,) -- so we must check shape[0] to see if the Table is
        # empty
        if self.data.shape[0] == 0:
           return 0
        #
        if len(self.data.shape) == 2:
            return self.data.shape[0]
        elif len(self.data.shape) == 3:
            return self.data.shape[1]
        else:
            return 0
