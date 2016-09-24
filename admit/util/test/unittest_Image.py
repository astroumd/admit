#! /usr/bin/env python
#
# Testing util/Image.py functions
#
# Functions covered by test cases:
#    serialize()
#    deserialize()
import admit

import sys, os
import unittest

class TestImage(unittest.TestCase):

    # initialization
    def setUp(self):
        self.verbose = False
        self.testName = "Utility Image Class Unit Test"
        self.image = admit.Image()

    def tearDown(self):
        pass

    def test_AAAwhoami(self):
        print "\n==== %s ====" % self.testName

    def testSerialization(self):
        self.image.images = {admit.bdp_types.FITS:"myimage.fits",admit.bdp_types.CASA:"myimage.casa"}
        self.image.thumbnail = "myimage_thumb.png"
        self.image.thumbnailtype = admit.bdp_types.PNG
        self.image.auxiliary = "myaux.jpg"
        self.image.auxtype = admit.bdp_types.JPG
        self.image.description = "This is a image for serialization unit test"
        self.image.name = "My name is legion"
        out = self.image.serialize()
        myImage = admit.Image()
        myImage.deserialize(out)
        self.assertEqual(self.image,myImage)
        self.image.description = "Bad wolf"
        self.assertNotEqual(self.image,myImage)

        myImage2 = admit.Image()
        myImage2.deserialize(out)
        multi_image = admit.MultiImage()
        myImage.description = "First image"
        multi_image.addimage(myImage,"first")
        myImage2.description = "Second image"
        multi_image.addimage(myImage2,"second")
        out = multi_image.serialize()
        multi_image2 = admit.MultiImage()
        multi_image2.deserialize(out)
        out2 = multi_image2.serialize()
        self.assertEqual(out,out2)
        self.assertEqual(multi_image,multi_image2)
#----------------------------------------------------------------------
# To run on commandline, using either "python unittest_Image.py" 
# or "./unittest_Image.py"
if __name__ == '__main__':
    unittest.main()
