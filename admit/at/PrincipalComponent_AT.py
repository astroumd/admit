"""**PrincipalComponent_AT** --- Calculates principal components of maps.
   ----------------------------------------------------------------------

   This module defines the PrincipalComponent_AT class.
"""
import sys, os
import numpy as np
import matplotlib.mlab as mlab

import admit
import admit.util.bdp_types as bt

class PrincipalComponent_AT(admit.Task):
    """
    Calculates the principal components of a set of input maps.

    Given **N** single-plane (i.e., 2-D) images, principal component analysis
    solves the **N**-dimensional eigenvalue problem determining the principal
    directions in **N**-space of the image data, ranked according to their
    contribution to the total variance of the sample points (each sample point
    being the **N**-vector of image values corresponding to a single pixel
    position).  This decomposition can be used to reduce the dimensionality of
    the data by identifying components contributing little independent
    information to the data set. This task also calculates the covariance
    matrix for input images.

    Mathematically, a principal component analysis can be applied to an
    arbitrary set of images. In practice, the input images should be related in
    some way; otherwise, the eigenvalues will be of similar magnitude and (as
    expected) no reduction in dataset dimensionality possible. For astronomical
    images, the inputs will typically be maps of the same source (at the same
    pixel scale) in different wavelength bands. In ADMIT, the inputs will often
    be moment maps produced by `Moment_AT <Moment_AT.html>`_.

    **Keywords**

      **clipvals**: list of float
        List of threshold values below which each input map value will be
        clipped (set to zero). The length of **clipvals** must match
        the number of input maps; the default empty list implies all zeroes.

      **covarmin**: float
	Minimum pairwise covariance for summary output (only); default: 0.90.

    **Input BDPs**

      **Image_BDP**: count: `varies`
        Input images for principal component analysis; e.g., moment maps
        produced by `Moment_AT <Moment_AT.html>`_ or
        `CubeSum_AT <CubeSum_AT.html>`_.

    **Output BDPs**

      **Table_BDP**: count: 3
	First table contains the input mean and standard deviation plus output
        eigenimage filename and variance fractions. Second table is the
        calculated projection matrix transforming (mean-subtracted and
        variance-normalized) input data to principal component space. Third
        table is the covariance matrix of the input images.

      **Image_BDP**: count: `varies` (equal to input count)
        Calculated principal component images (in order of eigenvalue size).

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
    All input maps must have the same dimensions. Currently only 2-D maps are
    supported.
    """

    def __init__(self, **keyval):
        keys = {"clipvals" : [], "covarmin" : 0.90}   
        admit.Task.__init__(self, keys, keyval)
        self._version   = "1.0.1"
        self.set_bdp_in ([(admit.Image_BDP, 0, bt.REQUIRED)])
        self.set_bdp_out([(admit.Table_BDP, 3), (admit.Image_BDP, 0)])

    def summary(self):
        """
        Summary data dictionary.

        PrincipalComponent_AT adds the following to ADMIT summary:

        .. table::
           :class: borderless

           +----------+----------+-----------------------------------+
           |   Key    | type     |    Description                    |
           +==========+==========+===================================+
           | pca      | table    |  Statistics and covariance data.  |
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

        Computes the principal component decomposition of the input images and
        populates the output eigenimages and projection matrix.

        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
	self._summary = {}

	# BDP output uses the alias name if provided, else a flow-unique one.
	stem = self._alias
	if not stem: stem = "pca%d" % (self.id())

	inum = 0
	data = []
	icols = []
        for ibdp in self._bdp_in:
	  # Convert input CASA images to numpy arrays.
	  istem = ibdp.getimagefile(bt.CASA)
	  ifile = ibdp.baseDir() + istem
	  icols.append(os.path.splitext(istem)[0])
	  if os.path.dirname(icols[-1]):
	    icols[-1] = os.path.dirname(icols[-1])  # Typical line cube case.
	  img = admit.casautil.getdata(ifile, zeromask=True).data
	  data.append(img)
	  admit.logging.info("%s shape=%s min=%g max=%g" % 
              (icols[-1], str(img.shape), np.amin(img), np.amax(img)))
	  assert len(data[0].shape) == 2, "Only 2-D input images supported"
	  assert data[0].shape == data[inum].shape, "Input shapes must match"
	  inum += 1

	# At least two inputs required for meaningful PCA!
	assert inum >= 2, "At least two input images required"

	# Each 2-D input image is a plane in a single multi-color image.
	# Each color multiplet (one per pixel) is an observation.
	# For PCA we collate the input images into a vector of observations.
	shape = data[0].shape
	npix = shape[0] * shape[1]
	clip = self.getkey('clipvals')
	if not clip: clip = [0 for i in range(inum)]
	assert len(clip) >= inum, "Too few clipvals provided"

	# Clip input values and stack into a vector of observations.
	pca_data = []
        for i in range(inum):
          nd = data[i]
	  nd[nd < clip[i]] = 0.0
	  pca_data.append(np.reshape(nd, (npix,1)))
	pca_in = np.hstack(pca_data)
	pca = mlab.PCA(pca_in)

	# Input statistics and output variance fractions.
	#print "fracs:", pca.fracs
	#print "mean:", pca.mu
	#print "sdev:", pca.sigma
	obdp = admit.Table_BDP(stem+"_stats")
	obdp.table.setData(np.vstack([pca.mu, pca.sigma,pca.fracs]).T)
	obdp.table.columns = ["Input mean", "Input deviation",
			      "Eigenimage variance fraction"]
	obdp.table.description = "PCA Image Statistics"
	self.addoutput(obdp)

	# Pre-format columns for summary output.
	# This is required when mixing strings and numbers in a table.
	# (NumPy will output the array as all strings.)
	table1 = admit.Table()
	table1.setData(np.vstack([[i for i in range(inum)],
                                  icols,
	                          ["%.3e" % x for x in pca.mu],
	                          ["%.3e" % x for x in pca.sigma],
	                          ["%s_eigen/%d.im" % (stem, i) 
                                      for i in range(inum)],
				  ["%.4f" % x for x in pca.fracs]]).T)
	table1.columns = ["Index", "Input", "Input mean",
			  "Input deviation",
                          "Eigenimage",
			  "Eigenimage variance fraction"]
	table1.description = "PCA Image Statistics"

	# Projection matrix (eigenvectors).
	#print "projection:", pca.Wt
	obdp = admit.Table_BDP(stem + "_proj")
	obdp.table.setData(pca.Wt)
	obdp.table.columns = icols
	obdp.table.description = \
	    "PCA Projection Matrix (normalized input to output)"
	self.addoutput(obdp)

	# Covariance matrix.
	covar = np.cov(pca.a, rowvar=0, bias=1)
	#print "covariance:", covar
	obdp = admit.Table_BDP(stem + "_covar")
	obdp.table.setData(covar)
	obdp.table.columns = icols
	obdp.table.description = "PCA Covariance Matrix"
	self.addoutput(obdp)

	# Collate projected observations into eigenimages and save output.
	os.mkdir(self.baseDir()+stem+"_eigen")
	pca_out = np.hsplit(pca.Y, inum)
	odata = []
        for i in range(inum):
	  ofile = "%s_eigen/%d" % (stem, i)
	  img = np.reshape(pca_out[i], shape)
          odata.append(img)
	  #print ofile, "shape, min, max:", img.shape, np.amin(img), np.amax(img)

	  aplot = admit.util.APlot(figno=inum, abspath=self.baseDir(),
                                   ptype=admit.util.PlotControl.PNG)
	  aplot.map1(np.rot90(img), title=ofile, figname=ofile)
	  aplot.final()

	  # Currently the output eigenimages are stored as PNG files only.
	  admit.casautil.putdata_raw(self.baseDir()+ofile+".im", img, ifile)
	  oimg = admit.Image()
	  oimg.addimage(admit.imagedescriptor(ofile+".im",  format=bt.CASA))
	  oimg.addimage(admit.imagedescriptor(ofile+".png", format=bt.PNG))
          obdp = admit.Image_BDP(ofile)
	  obdp.addimage(oimg)
	  self.addoutput(obdp)

	# As a cross-check, reconstruct input images and compute differences.
        for k in range(inum):
	  ximg = pca.Wt[0][k]*odata[0]
	  for l in range(1,inum):
	    ximg += pca.Wt[l][k]*odata[l]

	  ximg = pca.mu[k] + pca.sigma[k]*ximg
          admit.logging.regression("PCA: %s residual: " % icols[k] +
                                   str(np.linalg.norm(ximg - data[k])))

	# Collect large covariance values for summary.
	cvmin = self.getkey('covarmin')
	cvsum = []
        cvmax = 0.0
	for i in range(inum):
	  for j in range(i+1, inum):
            if abs(covar[i][j]) >= cvmax:
              cvmax = abs(covar[i][j])
	    if abs(covar[i][j]) >= cvmin:
	      cvsum.append([icols[i], icols[j], "%.4f" % (covar[i][j])])
        admit.logging.regression("PCA: Covariances > %.4f: %s (max: %.4f)" % (cvmin,str(cvsum),cvmax))

	table2 = admit.Table()
	table2.columns = ["Input1", "Input2", "Covariance"]
	table2.setData(cvsum)
	table2.description = "PCA High Covariance Summary"

	keys = "covarmin=%.4f clipvals=%s" % (cvmin, str(clip))
        self._summary["pca"] = admit.SummaryEntry([table1.serialize(),
						   table2.serialize()
						  ],
						  "PrincipalComponent_AT",
						  self.id(True), keys)
