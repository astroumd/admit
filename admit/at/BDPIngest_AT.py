""" .. _BDPIngest-at-api:

    **BDPIngest_AT** --- Ingests an arbitrary BDP disk file.
    --------------------------------------------------------

    This module defines the BDPIngest_AT class.
"""

# ADMIT imports
from admit.AT import AT
from admit.bdp import BDP
import admit.util.utils as utils
from admit.util.Table import Table
from admit.Summary import SummaryEntry


class BDPIngest_AT(AT):
    """ This AT takes a ``.bdp`` file and converts it into the appropriate BDP
        type. This AT is useful for ingesting a raw BDP to start a new flow.

        **Keywords**

          **file**: str
            The name of the bdp file to ingest.
            No default.

        **Input BDPs**
          None

        **Output BDPs**
          **Various**: count: 1
            Output BDP type will depend on the input file.
    """
    def __init__(self, **keyval):
        keys = {"file": ""}
        AT.__init__(self, keys, keyval)
        self._version = "1.0.0"
        self.set_bdp_in()
        self.set_bdp_out([(BDP, 1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           BDPIngest_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | sources  | table    |   table of source parameters      |
              +----------+----------+-----------------------------------+

           
           Parameters
           ----------
           None

           Returns
           -------
           dict
               Dictionary of SummaryEntry
        """
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """ Method to read in a .bdp file and convert it to a BDP object.

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        self._summary = {}
        if not self.getkey("file"):
            raise Exception("Input file name is empty, one must be given.")
        bdp = utils.getBDP(self.getkey("file"))
        self.addoutput(bdp)

        # Make a table of some basic BDP info for Summary.  
        # Why in god's name do BDPs not store the name of the task that 
        # created them?!?!  The task ID attrbute is useless if the BDP came 
        # from another flow -- which is why this task was created in 
        # the first place!
        table = Table()
        if bdp.project != "":
            table.addRow(["Project",bdp.project])
        if bdp.sous!= "":
            table.addRow(["SOUS",bdp.sous])
        if bdp.gous!= "":
            table.addRow(["GOUS",bdp.gous])
        if bdp.mous!= "":
            table.addRow(["MOUS",bdp.mous])
        table.addRow(["BDP Type",bdp._type])
        table.addRow(["Base directory",bdp._baseDir])
        table.addRow(["XML file",bdp.xmlFile])
        if bdp._date != "":
            table.addRow(["Time stamp",bdp._date])
        files = bdp.getfiles()
        for f in files:
            table.addRow(["Associated File",f])
        table.description = "Information about the ingested BDP"
        taskargs = "file=%s" % self.getkey('file')
        self._summary["bdpingest"] = SummaryEntry(table.serialize(),"BDPIngest_AT",self.id(True),taskargs)
