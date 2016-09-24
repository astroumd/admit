""" .. _Image-api:

    **Image** --- Image data base.
    ------------------------------

    This module defines the Image class for IMAGE entries in BDPs as well as
    the imagedescriptor container class.
"""

# system imports
import xml.etree.cElementTree as et
import utils
import ast
import os

# ADMIT imports
import bdp_types as bt
from UtilBase import UtilBase


class Image(UtilBase):
    """ Defines the basic Image structure used in ADMIT.

        The class can store multiple types of the same image (e.g. png, jpg,
        CASA),  however no check is made that they are the same image, this
        must be ensured by the AT using the class. A thumbnail, caption, and
        auxiliary file (for e.g. a histogram) are also included.

        Parameters
        ----------
        keyvals : dictionary of new values for  the keywords, optional.
          These keyword value pairs can be fed in form the command line
          instantiation of the class.

        Attributes
        ----------
        images : dictionary
            Dictionary containing the image data, one entry per format type.

        thumbnail : string
            File name of the thumbnail image.

        thumbnailtype : string
            The format of the thumbnail, see bt for a list of available
            formats.

        auxiliary : string
            The name of the auxiliary file.

        auxtype : string
            The format of the auxiliary file, see bt for a list of
            available formats.

        description : string
            A description or caption for the image.
    """
    def __init__(self, **keyval):
        self.images = {}                # dictionary of images {Format:filename}
        self.thumbnail = ""             # thumbnail of image
        self.thumbnailtype = ""         # format of thumbnail
        self.auxiliary = ""             # auxiliary file (typically a histogram)
        self.auxtype = ""               # format of auxiliary file
        self.description = ""           # image description/caption
        self.name = ""
        UtilBase.__init__(self, **keyval)

    def __str__(self):
        retstr = bt.format.BOLD + bt.color.GREEN + "Image :" + bt.format.END + os.linesep
        for i, j in self.__dict__.iteritems():
            retstr = retstr + bt.format.BOLD + i + ": " + bt.format.END + str(j) + os.linesep
        return retstr

    def serialize(self):
        """Create a string representation of the Image that can
           be converted to native Python structures with ast.literal_eval
           or back to a Table with deserialize().
           Intended for the summary but can be used wherever.

           Parameters
           ----------
           None

           Returns
           -------
           A string representation of the Image that can be converted back
           to a Image with deserialize().
        """
        return str(self.__dict__)

    def deserialize(self,serial):
        """Create an Image from serialized data created by serialize().

           Parameters
           ----------
           serial : The string representation of an Image in the format from
           deserialize().

           Returns
           -------
           None
        """
        # Do not convert directly to self.__dict__ because
        # the Image structure may change between versions, e.g.
        # an attribute may be added or deleted.
        # So we can only safely convert attributes which are valid
        # for this Image instance.
        x = ast.literal_eval(serial)
        for i in self.__dict__:
           if i in x:
               self.__dict__[i] = x[i]

    def setkey(self, name="", value=""):
        """
            set keys, two styles are possible:

            1. name = {key:val}            e.g. **setkey({"a":1})**

            2. name = "key", value = val     e.g. **setkey("a", 1)**

            This method checks the type of the keyword value, as it must
            remain the same. Also new keywords cannot be added.

            Parameters
            ----------

            name : dictionary or string
                Dictionary of keyword value pais to set or a string with the
                name of a single key

            value : any
                The value to change the keyword to

            Returns
            -------
            None
        """
        if isinstance(name, dict):
            for k, v in name.iteritems():
                if k == "images" and isinstance(v, dict):
                    for k1, v1 in v.iteritems():
                        if k1 == bt.THUMB or k1 == bt.AUX:
                            raise Exception("Thumnails and auxiliary files cannot be added as part of the images item, they must be added under the thumbnail or auxiliary item.")
                if hasattr(self, k):
                    if type(v) == type(getattr(self, k)):
                        setattr(self, k, v)
                    else:
                        raise Exception("Cannot change data type for %s, expected %s but got %s" % (k, str(type(getattr(self, k))), str(type(v))))
                else:
                    raise Exception("Invalid key given to Image class: %s" % (k))
        elif not name == "":
            if name == "images" and isinstance(value, dict):
                for k, v in value.iteritems():
                    if k == bt.THUMB or k == bt.AUX:
                        raise Exception("Thumnails and auxiliary files cannot be added as part of the images item, they must be added under the thumbnail or auxiliary item.")
            if hasattr(self, name):
                if type(getattr(self, name)) == type(value):
                    setattr(self, name, value)
                else:
                    raise Exception("Cannot change data type for %s, expected %s but got %s"
                                    % (name, str(type(getattr(self, name))), str(type(value))))
            else:
                raise Exception("Invalid key given to Image class: %s" % (name))
        else:
            raise Exception("Invalid name parameter given, it must be a string or a dictionary of keys:values.")

    def addimage(self, image):
        """ Method to add an image to the class

            Parameters
            ----------
            image : List/ImageDescriptor
                Can be either a list of imagedescriptors or just an individual
                imagedescriptor. If the image type already exists in the class
                then it is replaced and the original removed. Any images
                labeled DATA will be added to the dictionary (overwriting any
                previous instances of the format)

            Returns
            -------
            None
        """
        if isinstance(image, list):
            for t in image:
                if(not t.format in bt.image_types):
                    raise Exception("%s is not a valid image type, accepted types are: %s"
                                    % (t, str(bt.image_types)))
                if(not isinstance(t, imagedescriptor)) :
                    raise Exception("Input image is not of imagedescriptor type or an imagedescriptor list")
                self.addfile(t)
            return
        elif(not isinstance(image, imagedescriptor)):
            raise Exception("Input image is not of imagedescriptor type or an imagedescriptor list")

        if(not image.type in bt.image_types + bt.imagedescriptor_types):
            raise Exception("%s is not a valid image type, accepted types are: %s"
                         % (image.type, str(bt.image_types + bt.imagedescriptor_types)))
        self.addfile(image)

    def addfile(self, image):
        """ Method to add a file to the class, it should not be called directly,
            instead addimage should be called

            Parameters
            ----------
            image : ImageDescriptor
                An imagedescriptor of the image to be added. Removes any file
                that is being replaced

            Returns
            -------
            None
        """
        if(image.type == bt.DATA) :
            if(image.format in self.images):
                self.removeimage(image.format)
            self.images[image.format] = image.file
        elif(image.type == bt.THUMB):
            if(self.thumbnail is not None):
                self.removeimage(bt.THUMB)
            self.thumbnail = image.file
            self.thumbnailtype = image.format
        elif(image.type == bt.AUX):
            if(self.auxiliary is not None):
                self.removeimage(bt.AUX)
            self.auxiliary = image.file
            self.auxtype = image.format

    def getimage(self, type):
        """ Method which returns the requested image from the class as an
            imagedescriptor.

            Parameters
            ----------
            type : string
                Can be any of the following: bt.AUX to retrieve the
                auxiliary file, bt.THUMB to retrieve the thumbnail,
                or a file format (e.g. bt.FITS) to retrieve the
                requested format of the main image. If the requested image
                does not exist then None is returned.

            Returns
            -------
            ImageDescriptor
                An imagedescriptor of the requested image or None if the image
                does not exist in the class.
        """
        if(type == bt.AUX):
            if(self.auxiliary != ""):
                return imagedescriptor(self.auxiliary, self.auxtype, bt.AUX)
            return None
        if(type == bt.THUMB):
            if(self.thumbnail != ""):
                return imagedescriptor(self.thumbnail, self.thumbnailtype, bt.THUMB)
            return None
        try:
            if(type in self.images):
                return imagedescriptor(self.images[type], type, bt.DATA)
        except:
            print "NOT FOUND"
            return None
        return None

    def getimagefile(self, imtype):
        """ Method to get the name of a file for the given image type

            Parameters
            ----------
            imtype : str
                Can be any of the following: bt.AUX to retrieve the
                auxiliary file, bt.THUMB to retrieve the thumbnail,
                or a file format (e.g. bt.FITS) to retrieve the
                requested format of the main image. If the requested image
                does not exist then None is returned.

            Returns
            -------
            String containing the image name, or None if the image does not
            exist

        """
        temp = self.getimage(imtype)
        if temp is None:
            return None
        return temp.file

    def removeimage(self, typ, basedir="", delete=True):
        """ Method to remove a specific image from the class, including from
            disk if requested.

            Parameters
            ----------
            type : string
                The type of the image to be removed. Can be any of the
                following: bt.AUX to remove the auxiliary file,
                bt.THUMB to remove the thumbnail, or a file format
                (e.g. bt.FITS) to remove the requested format from
                the main image dictionary.

            delete : Boolean
                Whether to delete the actual image from disk (default is True)

            Returns
            -------
            None
        """
        # go through each image component and delete the file and instance
        if(typ == bt.THUMB):
            if(delete):
                utils.remove(basedir + os.sep + self.thumbnail)
            self.thumbnail = ""
            self.thumbnailtype = ""
        elif(typ == bt.AUX):
            if(delete):
                utils.remove(basedir + os.sep+ self.auxiliary)
            self.auxiliary = ""
            self.auxtype = ""
        elif(typ in bt.image_types and typ in self.images):
            if(delete):
                utils.remove(basedir + os.sep + self.images[typ])
        elif(typ in self.images.values()):
            k = None
            for key, val in self.images.iteritems():
                if(typ == val):
                    k = key
            if(delete) :
                utils.remove(basedir + os.sep + k)
            self.images.pop(k, None)
        else:
            pass

    def delete(self, basedir="", delfile=True):
        """ Method to delete everything

            Parameters
            ----------
            delfile : Boolean
                Whether or not do delete the underlying files
                (default is True)

            Returns
            -------
            None
        """
        for f, v in self.images.iteritems():
            self.removeimage(f, basedir, delfile)
        self.images = {}
        if(self.thumbnail != ""):
            self.removeimage(bt.THUMB, basedir, delfile)
        if(self.auxiliary != ""):
            self.removeimage(bt.AUX, basedir, delfile)

    def getthumbnail(self):
        """ Method to get the thumbnail image file name

            Parameters
            ----------
            None

            Returns
            -------
            string
                The file name of the thumbnail image, relative to the encasing
                BDP
        """
        return self.getimage(bt.THUMB)

    def getaux(self):
        """ Method to get the auxiliary file name

            Returns
            -------
            string
                The name of the auxiliry file, relative to the encasing BDP
        """
        return self.getimage(bt.AUX)

    def __eq__(self, img):
        """ Method to determine if two images are equivalent

            Parameters
            ----------
            img : Image
                The image to compare to this one

            Returns
            -------
            Boolean
                Whether or not the two image classes are equivalent

            Notes
            -----
            Useful for testing purposes, still experimental
        """
        try:
            for i in self.__dict__:
                if cmp(getattr(self, i), getattr(img, i)) != 0:
                    return False
        except Exception, e:
            return False
        return True


class imagedescriptor(object):
    """ A lightweight class for transporting an image, its format and type.
        This class has three and only three data members, and no added methods.
        The members are file for the image file name on disk, format for the
        image format (e.g. bt.FITS), and type (one of bt.THUMB,
        bt.AUX, or bt.DATA) specifying what type of image this
        is.

        Parameters
        ----------
        file : string
            The name of the file containing the image
            No default

        format : string
            The format the image is in (see bt for a list of formats)
            No default

        type : string
            The data type this image is filling in the class auxiliary,
            thumbnail or data (where most images go). Use: bt.AUX, bt.THUMB, or
            bt.DATA
            Default : bt.DATA)

        Attributes
        ----------
        Same as parameters.
    """
    __slots__ = ["file", "format", "type"]

    def __init__(self, file, format, type=bt.DATA) :
        if(not type in bt.imagedescriptor_types) :
            raise Exception("type %s is not a valid value. Valid values are %s"
                            % (type, str(bt.imagedescriptor_types)))
        if(not format in bt.image_types):
            raise Exception("Format %s is not an acceptable format type" % (format))
        self.file = file
        self.format = format
        self.type = type
