""" .. _File-at-api:

   **File_AT** --- Test task representing an arbitrary disk file.
   --------------------------------------------------------------
   
   This module defines the File_AT class.
"""
import sys, os

from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.File_BDP import File_BDP
from admit.util.AdmitLogging import AdmitLogging as logging

# reminder: need matching $ADMIT/doc/sphinx/module/admit.at/File_AT.rst
#           .. automodule:: admit.at.File_AT

class File_AT(AT):
    """Hold a file reference.

    See also :ref:`File-AT-Design` for the design document.

    The resulting File_BDP holds a reference to a file, useful for
    bootstrapping your flow if you don't strictly need something
    complex such as Ingest_AT.  Used primarily by the Flow*_AT family
    for testing.

    Other realistic examples, besides Ingest_AT, are
    BDPIngest_AT and GenerateSpectrum_AT.py.

    **Keywords**

      **file**: string
            The name of the file. See below for controlling parameters
            if the file needs to exist or if it can be created.
            File has to be a file within the admit project, absolute
            paths are not allowed.
            No default.
    
      **touch**: bool
            If True, the "touch" system command is
            used on the file, which will then either create a zero
            length file, or else update the timestamp of an existing
            file. Probably only useful for testing.
            **Default**: False.

      **exist**: bool
            If True,  the input file is checked for existence before it could
            even be touched. An exception is thrown if the file does not exist
            and should exist.
            **Default**: True.
    
    **Input BDPs**
      None

    **Output BDPs**

      **File_BDP**: count: 1 


    Parameters
    ----------
    keyval : dictionary, optional
      Keyword-value pairs, directly passed to the contructor for ease of
      assignment.


    """

    def __init__(self,**keyval):
        keys = {"file"  : "",  
                "exist" : True,
                "touch" : False}  
        AT.__init__(self,keys,keyval)
        self._version = "1.0.0"
        self.set_bdp_in()
        self.set_bdp_out([(File_BDP,1)])

    def run(self):
        """ running the File_AT task
        """
        
        # grab and check essential keywords
        filename = self.getkey('file')
        logging.info("file=%s" % filename)
        if len(filename) == 0:
            raise Exception,'File_AT: no file= given'

        exist = self.getkey('exist')
        if exist:
            #
            logging.warning("no checking now")
            # self._bdp_in[0].checkfiles()

        # create the BDP
        bdp1 = File_BDP(filename)
        bdp1.filename = filename
        self.addoutput(bdp1)

        # touch the file if desired
        if self.getkey('touch'): bdp1.touch()

        # all done.
