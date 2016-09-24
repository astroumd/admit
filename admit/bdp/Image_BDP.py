"""
   .. _Image-bdp-api:

   **Image_BDP** --- Image data base.
   ----------------------------------

   This module defines the Image_BDP class.
"""

# get the main BDP base class
from BDP import BDP

# get the multiimage base class
from admit.util.MultiImage import MultiImage
from admit.util.Image import Image
import admit.util.bdp_types as bt


# set up the inheritance
class Image_BDP(BDP):
    """ MultiImage Basic Data Product

        Image base class for use in BDP's. BDP's that contain images
        should inherit from this class. In the instance where more than
        one image is needed then the class should instantiate instances
        of the Image class directly.

        Parameters
        ----------
        xmlFile : string
            Output XML file name.

        keyval : dictionary
            Dictionary of keyword value pairs.

        Attributes
        ----------
        image : Image
            An Image class to hold the data.

    """
    def __init__(self, xmlFile=None, **keyval):
        BDP.__init__(self, xmlFile)
        # instantiate an image as a data member
        self.image = MultiImage()
        self.setkey(keyval)
        self._version= "0.1.0"

    def addimage(self, image, name=""):
        """ Method to add an image to the class

            Parameters
            ----------
            image : Image
                The image instance to add

            name : str
                The name of the image, must be unique within the BDP instance
                Default: ""

            Returns
            -------
            None

        """
        if not isinstance(image, Image):
            raise Exception("Only Image classes can be added with addimage.")
        self.image.addimage(image, name)

    def getimage(self, imtype=None, name=""):
        """ Method to get a specific image type from the class

            Parameters
            ----------
            image : string
                The name of the image to get

            Returns
            -------
            The requested Image or None if it does not exist

        """
        if imtype is None:
            return self.image.getimageclass(name)
        return self.image.getimage(imtype, name)

    def getimagefile(self, imtype=bt.CASA, name=""):
        """ Method to get the requested image file name from the named instance

            Parameters
            ----------
            imtyp : string
                Can be any of the following: bdp_types.AUX to retrieve the
                auxiliary file, bdp_types.THUMB to retrieve the thumbnail, 
                or a file format (e.g. bdp_types.FITS) to retrieve the
                requested format of the main image. If the requested image
                does not exist then None is returned.

            name : str
                The name if the image instance to get.
                Default : ""

            Returns
            -------
            String containing the image name, or None if it does not exist

        """
        return self.image.getimage(imtype, name).file
