"""
    An example of how to inherit from the Image_BDP
"""
from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

class Image_inherit_BDP(Image_BDP):    
    def __init__(self,xmlFile=None):
        Image_BDP.__init__(self,xmlFile)
        self.item1 = ["a","b"]
        self.item2 = 0.0

    def testset(self):
        self.set("taskid",5)
        # add a fits image
        #self.image.addimage(ID("test.fits",bt.FITS,bt.DATA))
        # add a thumbnail
        #self.image.addimage(ID("thumb.png",bt.PNG,bt.THUMB))
        # add a caption/description
        self.image.description = "Testing the images"
        self._version= "0.1.0"
