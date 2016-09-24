""" .. _Tier1DB-api:

    **Tier1DB** --- Tier 1 molecular line database services.
    --------------------------------------------------------

    This module is used to interact with the Tier 1 database.
"""

import logging
import sqlite3 as sql
import os
from admit.util import LineData
from admit.util import utils

class Tier1DB(object):
    """ Class for interacting with the Tier 1 database. Methods are supplied to
        query the database and get restults of the query. See the DOCUMENTATION
        on the Tier 1 database for specifics.

        Parameters
        ----------
        None

        Attributes
        ----------
        conn : sql connection
            The main sql database connection.

        cursor : sql cursor
            The cursor used to interact with the database.

    """
    def __init__(self):
        # open up the database
        self.conn = sql.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             "..", "..", "etc", "transitions.db"))
        # get a cursor
        self.cursor = self.conn.cursor()
        self.ishfs = False

    def close(self):
        """ Method to cleanly close the database connection

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        self.conn.close()

    def add(self, string):
        """ Method to append to the query string, automatically adding where/and if
            necessary.

            Parameters
            ----------
            string : str
                The string to add to the query

            Returns
            -------
            None

        """
        # if this is the first one the add where
        if self.first:
            self.query += " where"
            self.first = False
        # otherwise add an and
        else:
            self.query += " and"
        self.query += string

    def searchtransitions(self, freq=[], eu=[], el=[], linestr=[], species=None):
        """ Method to construct the query and send it to the database.

            Parameters
            ----------
            freq : list or float
                The frequency range to search over. If a list is given it is treated
                as [min,max]. If a single float is given then it is treated as a maximum
                allowable frequency. The units are GHz.

            eu : list or float
                The upper energy range to search over. If a list is given it is treated
                as [min,max]. If a single float is given then it is treated as a maximum
                allowable upper state energy.

            el : list or float
                The lower energy range to search over. If a list is given it is treated
                as [min,max]. If a single float is given then it is treated as a maximum
                allowable lower state energy.

            linestr : list or float
                The line strength range to search over. If a list is given it is treated
                as [min,max]. If a single float is given then it is treated as a maximum
                allowable line strength.

            species : str
                The species to restrict the search to. It is executed as an sql "like"
                statement, and thus an exact match is not required.

        """
        # set up the query
        self.ishfs = False
        self.first = True
        self.query = "select SPECIES, NAME, FREQUENCY, QUANTUM_NUMBERS, LINE_STR, LOWER_ENERGY, UPPER_ENERGY, HFS from Transitions"

        # add any frequency restrictions
        if isinstance(freq, list):
            if len(freq) == 2:
                self.add(" FREQUENCY between %f and %f" % (min(freq[0], freq[1]), max(freq[0], freq[1])))
            elif len(freq) == 1:
                self.add(" FREQUENCY <= %f" % (freq[0]))
            elif len(freq) == 0:
                pass
            else:
                raise Exception("Invalid number of freq components given, bust be 0, 1, or 2")
        elif isinstance(freq, float) or isinstance(freq, int):
            self.add(" FREQUENCY <= %f" % (float(freq)))
        else:
            raise Exception("Invalid data type given for freq, must be a list or float")

        # add any upper energy restrictions
        if isinstance(eu, list):
            if len(eu) == 2:
                self.add(" UPPER_ENERGY between %f and %f" % (min(eu[0], eu[1]), max(eu[0], eu[1])))
            elif len(eu) == 1:
                self.add(" UPPER_ENERGY <= %f" % (eu[0]))
            elif len(eu) == 0:
                pass
            else:
                raise Exception("Invalid number of eu components given, bust be 0, 1, or 2")
        elif isinstance(eu, float) or isinstance(eu, int):
            self.add(" UPPER_ENERGY <= %f" % (float(eu)))
        else:
            raise Exception("Invalid data type given for eu, must be a list or float")

        # add any lower energy restrictions
        if isinstance(el, list):
            if len(el) == 2:
                self.add(" LOWER_ENERGY between %f and %f" % (min(el[0], el[1]), max(el[0], el[1])))
            elif len(el) == 1:
                self.add(" LOWER_ENERGY <= %f" % (el[0]))
            elif len(el) == 0:
                pass
            else:
                raise Exception("Invalid number of el components given, bust be 0, 1, or 2")
        elif isinstance(el, float) or isinstance(el, int):
            self.add(" LOWER_ENERGY <= %f" % (float(el)))
        else:
            raise Exception("Invalid data type given for el, must be a list or float")

        # add and line strength restrictions
        if isinstance(linestr, list):
            if len(linestr) == 2:
                self.add(" LINE_STR between %f and %f" % (min(linestr[0], linestr[1]), max(linestr[0], linestr[1])))
            elif len(linestr) == 1:
                self.add(" LINE_STR <= %f" % (linestr[0]))
            elif len(linestr) == 0:
                pass
            else:
                raise Exception("Invalid number of linestr components given, bust be 0, 1, or 2")
        elif isinstance(linestr, float) or isinstance(linestr, int):
            self.add(" LINE_STR <= %f" % (float(linestr)))
        else:
            raise Exception("Invalid data type given for linestr, must be a list or float")

        # add any species restrictions
        if species:
            self.add(" SPECIES like '%%%s%%'" % (species))
        self.cursor.execute(self.query)

    def searchhfs(self, hfsid):
        """ Method to search the HFS table for the requested transitions

            Parameters
            ----------
            hfsid : int
                The id of the HFS line to get

            Returns
            -------
            None

        """
        self.ishfs = True
        self.cursor.execute("select FREQUENCY, QUANTUM_NUMBERS, LINE_STR, LOWER_ENERGY, UPPER_ENERGY from HFS where TRANSITION=%i" % (hfsid))

    def getall(self):
        """ Method to get all results from the query

            Parameters
            ----------
            None

            Returns
            -------
            List of LineData objects, one for each transition

        """
        results = self.cursor.fetchall()
        output = []
        if self.ishfs:
            for res in results:
                output.append(LineData(frequency=res[0], transition=str(res[1]), linestrength=res[2],
                                       energies=[res[3], res[4]]))
        else:
            for res in results:
                formula = str(res[0])
                output.append(LineData(formula=formula, name=str(res[1]), frequency=res[2], uid=utils.getplain(formula) + "_%.5f" % res[2],
                                       energies=[res[5], res[6]], linestrength=res[4], mass=utils.getmass(formula), transition=str(res[3]),
                                       plain=utils.getplain(formula), isocount=utils.isotopecount(formula),
                                       hfnum=res[7]))
        return output

    def getone(self):
        """ Method to get the next result from the query

            Parameters
            ----------
            None

            Returns
            -------
            LineData object containing the transition data
        """
        res = self.cursor.fetchone()

        if self.ishfs:
            return LineData(frequency=res[0], transition=res[1], linestrength=res[2],
                            energies=[res[3], res[4]])
        formula = str(res[0])
        return LineData(formula=formula, name=str(res[1]), frequency=res[2], uid=utils.getplain(formula) + "_%.5f" % res[2],
                        energies=[res[5], res[6]], linestrength=res[4], mass=utils.getmass(formula), transition=str(res[3]),
                        plain=utils.getplain(formula), isocount=utils.isotopecount(formula), hfnum=res[7])

    def get(self, num):
        """ Method to get many results from the query

            Parameters
            ----------
            num : int
                The number of results to get

            Returns
            -------
            A tuple containing the requested results as a list

        """
        return self.cursor.fetchmany(num)

    def query(self, querystring):
        """ Method to execute the requested query against the transitions database

            Parameters
            ----------
            query : str
                The query to perform, no error checking is done

            Returns
            -------
            None

        """
        self.cursor.execute(querystring)
