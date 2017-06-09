""" .. _Regrid-at-api:

   **Regrid_AT** --- Regrids multiple cubes to a common resolution.
   ----------------------------------------------------------------

   This module defines the Regrid_AT class.
"""
import admit as admit 
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
import admit.util.Table
import admit.util.utils as utils
from admit.bdp.SpwCube_BDP import SpwCube_BDP
import numpy as np
import os as os
from copy import deepcopy

try:
  import casa
  import taskinit
except:
  print "WARNING: No CASA; Regrid task cannot function."

class Regrid_AT(AT):
    """Creates a regridded version of multiple datacubes. Capable of 
    regridding in both spatial and spectral dimensions. Default 
    behavior is to take a set of N cubes and (a) regrid the pixel size 
    to the minimum pixel size of all the images and (b) to remap the images
    so that they all fit on the minimum-area square patch of sky that
    encloses each image. User may specify an alterative pixel size. User
    may also specify spectral regridding. If spectral regridding is desired,
    the default behavior is to regrid so a common set of frequencies with 
    mininum/maximum frequency those of the collection of cubes and channel width
    the minimum channel width in the collection of cubes. Alternatively, 
    user may specify a desired channel width in Hz.

    See also :ref:`Regrid-AT-Design` for the design document.

    **Keywords**
        **do_spatial_regrid**: bool
           Whether or not to do spatial regridding. The default is to do 
           spatial regridding. If set to true (or left default), the pix_scale 
           keyword will be used to determine the appropriate pixel size 
           to regrid the images to.            

        **pix_scale**: double
           The pixel size on which to regrid all the images. If negative, then 
           the default is the minimum pixel scale for all images. Unit is arcsec.
           **Default**: -1.0.

        **do_freq_regrid**: bool
           Whether or not to do frequency regridding. The default is to only do 
           spatial regridding. If set to true, the chan_width keyword will be used
           to determine the appropriate channel width to regrid the images to.            
        **chan_width**: double
           The channel width with which to regrid the images. If negative, then 
           the default is the minimum such channel width. Unit is Hz.
           **Default**: -1.0.

    **Input BDPs**

        **SpwCube_BDP**: count: `varies` (minimum 2)
           Input cubes, as from
           `Ingest_AT <Ingest_AT.html>`_,
           `ContinuumSub_AT <ContinuumSub_AT.html>`_ or
           `LineCube_AT <LineCube_AT.html>`_.

    **Output BDPs**

        **SpwCube_BDP**: count: `varies` (equal to input count)
          Regridded cubes.

    Parameters
    ----------
        keyval : dict, optional
            Dictionary of keyword:value pairs.

    Attributes
    ----------
        _version : string
            Version ID string.
    """

    def __init__(self, **keyval):
        keys = {
           "do_spatial_regrid": True,
           "pix_scale"    : -1.0,     
           "do_freq_regrid": False,
           "chan_width"    : -1.0          
        }

        AT.__init__(self,keys,keyval)
        self._version = "1.1.0"
        self.set_bdp_in([(SpwCube_BDP,0,bt.REQUIRED)])
        self.set_bdp_out([(SpwCube_BDP,0)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

        Regrid_AT adds the following to ADMIT summary::

           Key      type        Description
         --------  ------       -----------
         regrid    list        Info about smoothing done 
        """
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """ The run method creates the BDP

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        self._summary = {}
        dt = utils.Dtime("Regrid")
        dt.tag("start")

        do_spatial_regrid = self.getkey("do_spatial_regrid")
        pix_scale   = self.getkey("pix_scale")
        do_freq_regrid=self.getkey("do_freq_regrid")
        chan_width  = self.getkey("chan_width")

        pix_size=[]
        chan_size=[]
        im_size =[]
        pix_wc_x = []
        pix_wc_y = []
        pix_wc_nu=[]
        src_dec = []
        
        RADPERARCSEC = 4.848137E-6

        ia = taskinit.iatool()

        for ibdp in self._bdp_in:
          # Convert input CASA images to numpy arrays.
          istem = ibdp.getimagefile(bt.CASA)
          ifile = ibdp.baseDir() + istem
          
          h = casa.imhead(ifile, mode='list')
          pix_size.append(np.abs(h['cdelt1'])) # pix scale in asec @todo QA ?                                    
          chan_size.append(np.abs(h['cdelt3']))
          # grab the pixels 
          pix_x = h['shape'][0]
          pix_y = h['shape'][1]          
          pix_nu= h['shape'][2]
          
          ia.open(ifile)
          mycs = ia.coordsys(axes=[0,1,2])
#           getting all four corners handles the case of images where
#           x-y axis not aligned with RA-dec
          for xpix in [0,pix_x]:
            for ypix in [0,pix_y]:
              x = mycs.toworld([xpix,ypix])['numeric'][0] 
              y = mycs.toworld([xpix,ypix])['numeric'][1]
              pix_wc_x.append(x)
              pix_wc_y.append(y)
              
          nu= mycs.toworld([pix_x,pix_y,0])['numeric'][2]
          pix_wc_nu.append(nu)
          nu= mycs.toworld([pix_x,pix_y,pix_nu])['numeric'][2]
          pix_wc_nu.append(nu)
          ia.close()
 
        min_ra = np.min(pix_wc_x)
        max_ra = np.max(pix_wc_x)
        min_dec = np.min(pix_wc_y)
        max_dec = np.max(pix_wc_y)        
        mean_ra  = 0.5*(min_ra + max_ra)
        mean_dec  = 0.5*(min_dec + max_dec)

        if(pix_scale < 0):
          pix_scale = np.min(pix_size)
        else:
          pix_scale = pix_scale * RADPERARCSEC
        
          
        npix_ra = int((max_ra - min_ra) / pix_scale * np.cos(mean_dec))
        npix_dec = (max_dec - min_dec) / pix_scale
        npix_dec = (int(npix_dec) if npix_dec == int(npix_dec) else int(npix_dec) + 1) 
        min_nu  = np.min(pix_wc_nu)
        max_nu  = np.max(pix_wc_nu)
        mean_nu   = 0.5*(min_nu + max_nu)
        if(chan_width < 0):
          chan_width = np.min(chan_size)
        npix_nu  =int((max_nu - min_nu)/chan_width)+1

        # now regrid everything
        innames =[]
        outnames = []
        incdelt = []
        outcdelt = []

        #=========================================================
        #@todo - check if bdp_ins refer to same input file.
        # If so, the current code will fail because the output
        # file name is fixed to $INPUT_regrid.  A valid use case
        # is "regrid the same input file different ways" -- which
        # is not supported in the current code but should be
        #=========================================================
        for ibdp in self._bdp_in:      
          istem = ibdp.getimagefile(bt.CASA)
          ifile = ibdp.baseDir() + istem          
          ostem = "%s_regrid/" % (istem)
          ofile = self.baseDir() + ostem
          # save the input/output file names
          innames.append(istem)
          outnames.append(ostem)
          
          header=casa.imregrid(imagename=ifile,template='get')
          # save the input cdelt1,2,3 for summary table
          incdelt.append((header['csys']['direction0']['cdelt'][0]/RADPERARCSEC,header['csys']['direction0']['cdelt'][1]/RADPERARCSEC,utils.freqtovel(mean_nu,header['csys']['spectral2']['wcs']['cdelt'])))
          
          if(do_spatial_regrid):
            header['csys']['direction0']['cdelt'] = [ -1*pix_scale,pix_scale] 
            header['csys']['direction0']['crval'] = [ mean_ra,mean_dec] 
            header['shap'][0] = npix_ra 
            header['shap'][1] = npix_dec 
            header['csys']['direction0']['crpix'] = [npix_ra/2,npix_dec/2] 
            
          if(do_freq_regrid):
              header['csys']['spectral2']['wcs']['crval']=min_nu
              header['shap'][2] = npix_nu
              chan_size = np.abs(header['csys']['spectral2']['wcs']['cdelt'])
              header['csys']['spectral2']['wcs']['cdelt'] = chan_width
              flux_correction = chan_width/chan_size             

          casa.imregrid(imagename=ifile,output=ofile,template=header)
          # save the output cdelt1,2,3 for summary table
          newhead = casa.imregrid(imagename=ofile,template='get')
          outcdelt.append((newhead['csys']['direction0']['cdelt'][0]/RADPERARCSEC,newhead['csys']['direction0']['cdelt'][1]/RADPERARCSEC,utils.freqtovel(mean_nu,newhead['csys']['spectral2']['wcs']['cdelt'])))

          if(do_freq_regrid):
            ia.open(ofile)
            print flux_correction
            ia.calc(pixels=ofile.replace(r"/",r"\/")+'*'+str(flux_correction))
            ia.done()
          obdp = admit.SpwCube_BDP(ostem)
          self.addoutput(obdp)

        # make a table for summary
        atable = admit.util.Table()
        atable.columns = ["Input Image","cdelt1", "cdelt2", "cdelt3", "Regridded Image","cdelt1","cdelt2","cdelt3"]
        atable.units = ["","arcsec", "arcsec", "km/s", "","arcsec","arcsec","km/s"]
        for i in range(len(innames)):
            atable.addRow([ innames[i],incdelt[i][0],incdelt[i][1],incdelt[i][2], outnames[i],outcdelt[i][0],outcdelt[i][1],outcdelt[i][2] ])


        #keys = "pixsize=%.4g naxis1=%d naxis2=%d mean_ra=%0.4f mean_dec=%0.4f reffreq=%g chan_width=%g" % (pix_scale/(4.848137E-6), npix_ra, npix_dec, mean_ra,mean_dec,min_nu,chan_width)
        taskargs = "pix_scale = " + str(self.getkey("pix_scale")) + " chan_width = "+str(self.getkey("chan_width"))
        self._summary["regrid"] = SummaryEntry(atable.serialize(),"Regrid_AT",self.id(True),taskargs)
        dt.tag("done")
        dt.end()
