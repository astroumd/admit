"""**File_BDP** --- Test data product representing a disk file.
   ------------------------------------------------------------
   
   This module defines the File_BDP class.
"""
import os
from BDP import BDP

class File_BDP(BDP):
    """
    This is the file BDP, just for testing.

    But there really isn't much to this, other than containing
    a file reference. See File_AT how to make one.

    Parameters
    ----------
    xmlFile : str
        Output XML file name.
    """
    def __init__(self,xmlFile=None):
        BDP.__init__(self,xmlFile)
        self.filename = ""
        self._version= "0.1.0"

    def show(self):
        """ 
        testing Overriding the baseclass SHOW
        """
        print "File_BDP.show() ran..."

    def getfiles(self):
	""" returns a list of file names. 

        For File_BDP only one filename is currently allowed
	"""
	return [self.filename]

    def checkfiles(self):
        """
        Determines whether the associated disk file exists.

        Raises an exception if the file is absent.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        fname = self.baseDir() + self.filename
        if not os.path.exists(fname):
            raise Exception,'File_BDP: file %s does not exist' % fname
        else:
            print "File_BDP: file %s exists" % fname

    def touch(self):
        """
        Touches the associated disk file.

        The implementation uses native Python OS bindings for speed.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        fname = self.baseDir() + self.filename
        print "File_BDP: touching", fname

        if os.path.exists(fname):
            os.utime(fname,None)
        else:
            open(fname,'a').close()
