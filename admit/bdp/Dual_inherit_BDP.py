"""
    An example of how to inherit from both Image_BDP and Table_BDP
"""

from Table_BDP import Table_BDP
from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

class Dual_inherit_BDP(Table_BDP,Image_BDP):    
    def __init__(self,xmlFile=None):
        Table_BDP.__init__(self,xmlFile)
        Image_BDP.__init__(self,xmlFile)
        self.item1 = ["a","b"]
        self.item2 = 0.0
        self._version= "0.1.0"

    def testset(self):
        self.set("taskid",5)
        # set the column labels and units
        self.table.columns = ["Frequency","Peak Intensity","FWHM"]
        self.table.units = ["GHz","Jy/bm","km/s"]
        # populate the table with some data
        self.table.setData([[93.2,1.5,8.6],
                            [92.35,0.6,4.5],
                            [93.7,8.2,6.7]])
        # add a row
        self.table.addRow([92.6,1.04,7.3])
        self.table.description = "Table of spectral lines"

        # add a fits image
        #self.image.addimage(ID("test.fits",bt.FITS,bt.DATA))
        # add a thumbnail
        #self.image.addimage(ID("thumb.png",bt.PNG,bt.THUMB))
        # add a caption/description
        self.image.description = "Testing the images"
