""".. _Template-AT-api:

   **Template_AT** --- Cube manipulation template.
   -----------------------------------------------

   This module defines the Template_AT class.
"""
import sys, os
import numpy as np

import admit
import admit.util.bdp_types as bt

class Template_AT(admit.Task):
    """
    Image cube manipulation sample template.

    This task demonstrates several ways of manipulating a generic
    position-position-frequency (or velocity) data cube.  It can be used as a
    template by users developing their own cube analysis routines. This
    template demonstrates the following transformations:

    - scale the intensity at all points in the cube by a specified value
    - extract a 2-D position-position image from the (scaled) cube at a 
      specified frequency (channel number)
    - extract a 1-D spectrum from the (scaled) cube at the specified spatial
      position (pixel coordinates)

    Each of these operations is controlled by keywords.

    **Keywords**

      **cubescale**: float
        The value by which to scale the cube intensity; default: 2.0.

      **imgslice**: int
        Frequency (pixel index) of the 2-D image plane to extract from the
        cube; default: 0 (the first spectral channel).

      **specpos**: 2-tuple of int
        The 2-D (spatial) pixel position from which to extract the 1-D cube
        spectrum; default: (0,0).

    **Input BDPs**

      **SpwCube_BDP**: count: 1
        Input 3-D data cube; e.g., as output from an
        `Ingest_AT <Ingest_AT.html>`_,
        `ContinuumSub_AT <ContinuumSub_AT.html>`_ or
        `LineCube_AT <LineCube_AT.html>`_.

    **Output BDPs**

      **SpwCube_BDP**: count: 1
        Output scaled 3-D data cube.

      **Image_BDP**: count: 1
        Output 2-D image sliced from the cube.

      **Table_BDP**: count: 1
        Output 1-D spectrum extracted from the cube.


    Parameters
    ----------
    keyval : dict, optional
      Dictionary of keyword:value pairs.

    Attributes
    ----------
    _version : str
      Version ID string.

    Notes
    -----
    Whenever the expected type or number of keywords or input/output BDPs
    changes, the __init__ method must be updated accordingly.
    """
    def __init__(self, **keyval):
        keys = {"cubescale" : 2.0, "imgslice" : 0, "specpos" : (0,0)}   
        admit.Task.__init__(self, keys, keyval)
        self._version   = "1.0.0"
        self.set_bdp_in ([(admit.SpwCube_BDP, 1, bt.REQUIRED)])
        self.set_bdp_out([(admit.SpwCube_BDP, 1), (admit.Image_BDP, 1),
                          (admit.Table_BDP, 1)])

    def summary(self):
        """
        Summary data dictionary.

        Template_AT adds the following to ADMIT summary:

        .. table::
           :class: borderless

           +----------+----------+-----------------------------------+
           |   Key    | type     |    Description                    |
           +==========+==========+===================================+
           | spectra  | list     | Plots of cube slice and spectrum. |
           +----------+----------+-----------------------------------+
           | template | table    | Template data product statistics. |
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

    def userdata(self):
        """
        User data dictionary.

        Parameters
        ----------
        None
        
        Returns
        -------
        dict
            The user data dictionary from the AT, for merging into the ADMIT
            user data object.  
        """
        if hasattr(self,"_userdata"):
            return self._userdata
        else:
            return {}

    def run(self):
        """
        Task run method.

        Outputs three sample data products from a single input data cube:

        1. A cube scaled by the value of *cubescale*.
        2. An image sliced from the cube at frequency *imgfreq*.
        3. A spectrum extracted from the cube at position *specpos*.

        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self._summary = {}

        # BDP output uses the alias name if provided, else a flow-unique name.
        stem = self._alias
        if not stem: stem = "template%d" % (self.id())

        # The input data cube BDP.
        ibdp = self._bdp_in[0]

        # The data cube is a CASA image on disk.
        # Get its file name, read it in and convert to a NumPy array.
        # The entire cube is read into memory (large cubes may exceed RAM!)
        # Any masked pixels are converted to zero.
        istem = ibdp.getimagefile(bt.CASA)
        ifile = ibdp.baseDir() + istem
        icube = admit.casautil.getdata(ifile, zeromask=True).data
        assert len(icube.shape) == 3, "Only 3-D data cubes supported"
        admit.logging.info((istem + " dimensions: (%d, %d, %d)") % icube.shape)


        # ===================================================================
        # 1. Scale the entire cube by 'cubescale'.
        # ===================================================================
        cubescale = self.getkey('cubescale')
        ocube = icube * cubescale
        ocubestem = "%s_cube" % stem
        ocubefile = self.baseDir() + ocubestem
        #
        # Create a CASA ouput image (no mask information).
        admit.casautil.putdata_raw(ocubefile+".im", ocube, ifile)
        # 
        # Output the result as a new SpwCube.
        image = admit.Image(description="Template 3-D Cube")
        image.addimage(admit.imagedescriptor(ocubefile+".im", format=bt.CASA))
        obdp1 = admit.SpwCube_BDP(ocubestem)
        obdp1.addimage(image)
        self.addoutput(obdp1)


        # ===================================================================
        # 2. Slice a 2-D image from the cube at frequency 'imgslice'.
        # ===================================================================
        #
        # The frequency axis is the third array index.
        # Clip slice to be in range.
        imgslice = max(0, min(ocube.shape[2]-1, self.getkey('imgslice')))
        oimg = ocube[:, :, imgslice]
        oimgstem = "%s_img" % stem
        oimgfile = self.baseDir() + oimgstem
        #
        # Create a CASA format ouput image.
        # @TODO Does not work for 3-D -> 2-D output.
        #admit.casautil.putdata_raw(oimgfile+".im", oimg, ifile)
        #
        # Create a PNG format output image.
        # Image data must be rotated to match matplotlib axis order.
        oimgtitle="Template Image Slice @ channel %d" % imgslice
        aplot = admit.APlot(figno=1, abspath=self.baseDir(),
                            pmode=admit.PlotControl.BATCH,
                            ptype=admit.PlotControl.PNG)
        aplot.map1(np.rot90(oimg),
                   xlab="R.A. (pixels)", ylab="Dec (pixels)",
                   title=oimgtitle, figname=oimgstem)
        aplot.final()
        #
        # Output data product referencing both image formats.
        image = admit.Image(description="Template 2-D Image")
        image.addimage(admit.imagedescriptor(oimgfile+".im",  format=bt.CASA))
        image.addimage(admit.imagedescriptor(oimgstem+".png", format=bt.PNG))
        obdp2 = admit.Image_BDP(oimgstem)
        obdp2.addimage(image)
        self.addoutput(obdp2)


        # ===================================================================
        # 3. Extract a 1-D spectrum from the cube at position 'specpos'.
        # ===================================================================
        #
        # Clip position to be in range.
        specpos = self.getkey('specpos')
        specpos = (max(0, min(ocube.shape[0]-1, specpos[0])),
                   max(0, min(ocube.shape[1]-1, specpos[1])))
        ospec = ocube[specpos[0], specpos[1], :]
        ochan = np.arange(ospec.shape[0])
        ospecstem = "%s_spec" % stem
        #
        # Create a PNG plot (standalone).
        ospectitle = "Template Spectrum @ position %s" % str(specpos)
        aplot = admit.APlot(figno=2, abspath=self.baseDir(),
                            pmode=admit.PlotControl.BATCH,
                            ptype=admit.PlotControl.PNG)
        aplot.plotter(x=ochan, y=[ospec],
                      xlab="Channel", ylab="Intensity",
                      title=ospectitle, figname=ospecstem)
        aplot.final()
        #
        # Output data product (spectrum table).
        obdp3 = admit.Table_BDP(ospecstem)
	obdp3.table.description = "Template 1-D Spectrum"
	obdp3.table.columns = ["Channel", "Spectrum @ (%d, %d)" % specpos]
	obdp3.table.setData(np.transpose(np.vstack([ochan, ospec])))
        self.addoutput(obdp3)


        # ===================================================================
        # Populate example summary object.
        # ===================================================================
        #
        # NOTE: Summary.py, etc., must be updated to recognize this and
        #       for Template_AT to appear in the HTML summary.
        stats = admit.Table()
        stats.description = "Template Data Product Statistics"
        stats.columns = ["Statistic", "InCube", "OutCube", "Image", "Spectrum"]
        stats.setData(
        np.array([
         ["Min", np.amin(icube), np.amin(ocube), np.amin(oimg), np.amin(ospec)],
         ["Max", np.amax(icube), np.amax(ocube), np.amax(oimg), np.amax(ospec)]
        ]))
        #
        # Data product statistics table.
        keys = "cubescale=%s imgslice=%d specpos=%s" % \
            (str(cubescale), imgslice, str(specpos))
        self._summary["template"] = admit.SummaryEntry([stats.serialize()],
                                                       "Template_AT",
                                                       self.id(True), keys)
        #
        # Plots for the image and spectrum.
        ocubeim = ocubestem+".im"
        spec_description = [
          [0, 0, "", "",
           oimgstem+".png", oimgstem+"_thumb.png", oimgtitle, ocubeim],
          [specpos[0], specpos[1], "", "Channel",
           ospecstem+".png", ospecstem+"_thumb.png", ospectitle, ocubeim]]
        self._summary["spectra"] = admit.SummaryEntry(spec_description,
                                                      "Template_AT",
                                                      self.id(True), keys)
