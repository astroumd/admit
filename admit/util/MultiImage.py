""" .. _MultiImage-api:

    **MultiImage** --- Multiple image container base.
    -------------------------------------------------

    This module defines the MultiImage class for multiple Image instances.
"""

# system imports
import xml.etree.cElementTree as et
import ast
import os

# ADMIT imports
import bdp_types as bt
from Image import Image
from UtilBase import UtilBase


class MultiImage(UtilBase):
    """ Class tha allows multiple image instances to be stored as one Image
        instance. There can be 0 to N different images (no limit) and the
        number does not need to be specified as they are allocated and removed
        dynamically.

        Parameters
        ----------
        None

        Attributes
        ----------
        mimages : dict
            A dictionary for holding the Image instances. Each Image instance
            must have a unique name (the key).

    """
    def __init__(self):
        self.mimages = {}
        UtilBase.__init__(self, **{})

    def __str__(self):
        for k, v in self.mimages.iteritems():
            print "\n" + str(v)
        return ""

    def addimage(self, image, name=""):
        """ Method to add a new image to the dictionary. The image key must not
            already exist.

            Parameters
            ----------
            image : Image
                The image instance to add

            name : str
                The unique name to use for the image
                Default : ""

            Returns
            -------
            None
        """
        if not isinstance(image, Image):
            raise Exception("Only an image can be added to MultiImage")
        if name in self.mimages:
            raise Exception("An image named %s already exists, use replaceimage to replace it" % (name))
        image.setkey("name", name)
        self.mimages[name] = image

    def replaceimage(self, image, name=""):
        """ Method to replace an image in the dictionary. This will no throw an
            error if the image does not already exist.

            Parameters
            ----------
            image : Image
                The image instance to insert

            name : str
                The name of the image to replace

            Returns
            -------
            None

        """
        if not isinstance(image, Image):
            raise Exception("Only an image can be added to MultiImage")
        self.mimage[name] = image

    def removeimage(self, name):
        """ Method to remove an image from the dictionary

            Parameters
            ----------
            name : str
                The name of the image to remove

            Returns
            -------
            None

        """
        if name in self.images:
            #self.mimages[name].delete(BASEDIR)
            del self.mimages[name]

    def getimage(self, typ, name=""):
        """ Method to get the requested image from the named instance as an
            imagedescriptor.

            Parameters
            ----------
            typ : string
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
            ImageDescriptor
                An imagedescriptor of the requested image or None if the image
                does not exist in the class.

        """
        return self.mimages[name].getimage(typ)

    def getimageclass(self, name):
        """ Method to return the requested Image instance

            Parameters
            ----------
            name : str
                The name of the Image instance to get

            Returns
            -------
            Image class instance of the requested image
        """
        if name in self.mimages:
            return self.mimages[name]
        return None

    def delete(self, basedir, delfiles=True):
        """ Method to delete all of the Images

            Parameters
            ----------
            basedir : str
                The base directory where the image(s) are

            delfiles : bool
                Whether or not to delete the actual image files
                Default : True

            Returns
            -------
            None

        """
        for k, v in self.mimages.iteritems():
            v.delete(basedir, delfiles)

    def serialize(self):
        imlist = dict()
        for k,v in self.mimages.iteritems():
            imlist[k] = v.serialize()
        return str(imlist)

    def deserialize(self,serial):
        imlist = ast.literal_eval(serial)
        for k,v in imlist.iteritems():
            #print "deserializing: %s" % k
            image = Image()
            image.deserialize(v)
            #print image
            self.addimage(image, k)

    def __str__(self):
        retstr = ""
        for k in self.mimages:
           retstr = retstr + str(self.mimages[k]) + os.linesep
        return retstr

    def __eq__(self,other):
        try:
            for k in self.mimages:
                if not self.mimages[k] == other.mimages[k]:
                    return False
        except Exception, e:
             return False
        return True

