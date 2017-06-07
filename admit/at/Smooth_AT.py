""" .. _Smooth-at-api:

   **Smooth_AT** --- Creates a smoothed version of a cube.
   -------------------------------------------------------

   This module defines the Smooth_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
import admit.util.Image as Image
import admit.util.utils as utils
import admit.util.Line as Line
from admit.bdp.SpwCube_BDP import SpwCube_BDP
from admit.util.AdmitLogging import AdmitLogging as logging

import numpy as np
from copy import deepcopy

try:
  import casa
  import taskinit
except:
  print "WARNING: No CASA; Smooth task cannot function."

class Smooth_AT(AT):
    """Creates a smoothed version of a datacube.

    Because interferometric arrays produce spectral cubes with 
    the frequency varying along the spectral axis, these cubes
    have varying resolutions that are proportional to the wavelength.
    It is often desirable to smooth the resolution of the cube to 
    a uniform one. In this task, we take an input cube, take the 
    beam for each plane, compute the minimum ellipse that contains 
    all the beams, and then smooth uniformly to that resolution.
    Also, we may wish to smooth along the velocity axis so that
    weak lines may come out more clearly in the resulting image. 
    If the user desires, we take the input cube and smooth it 
    to a given velocity resolution. 

    See also :ref:`Smooth-AT-Design` for the design document.

    **Keywords**

        **bmaj**: dictionary
            A dictionary with keys 'unit' giving the unit of the 
            major axis of the desired restoring beam and 'value', 
            giving the value of the major axis of the desired 
            restoring beam.  If 'value' is negative, then the 
            major axis of the restoring beam will be that of the 
            minimum enclosing ellipse for all the beams in the 
            image. Allowed units are "arcsec" and "pixel."
            **Default**: {'value' : -1.0, 'unit': 'arcsec'}.

        **bmin**: dictionary
            A dictionary with keys 'unit' giving the unit of the 
            minor axis of the desired restoring beam and 'value', 
            giving the value of the minor axis of the desired 
            restoring beam.  If 'value' is negative, then the 
            minor axis of the restoring beam will be that of the 
            minimum enclosing ellipse for all the beams in the 
            image. Allowed units are "arcsec" and "pixel."
            **Default**: {'value' : -1.0, 'unit': 'arcsec'}. 

        **bpa**: float
            A float that gives the position angle of the desired 
            restoring beam. If negative, this will be set to the 
            position angle of the minimum enclosing ellipse for 
            all the beams in the image.  
            **Default**: -1.0.

        **velres**: dictionary 
            A dictionary with keys 'unit' giving the unit of the 
            desired velocity resolution of the image cube and 'value', 
            giving the value of the desired velocity resolution of 
            the image cube.  If 'value' is negative, no smoothing 
            in velocity will be done. Allowed units are "m/s", "km/s",
            "Hz", "kHz","MHz", "GHz", and "pixel"
            **Default**: {'value' : -1.0, 'unit': 'km/s'}.
                
    **Input BDPs**

        **SpwCube_BDP**: count: `varies`
          Input cubes; e.g., output from an
          `Ingest_AT <Ingest_AT.html>`_,
          `ContinuumSub_AT <ContinuumSub_AT.html>`_ or
          `LineCube_AT <LineCube_AT.html>`_.

    **Output BDPs**

        **SpwCube_BDP**: count: `varies` (equal to input count)
          Smoothed cubes.

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
           "bmaj"    : {'value': -1.0, 'unit': 'arcsec'},
           "bmin"    : {'value': -1.0, 'unit': 'arcsec'},
           "bpa"     :  -1.0,
           "velres"  : {'value': -1.0, 'unit': 'pixel'},
        }

        AT.__init__(self,keys,keyval)
        self._version = "1.1.0"
        self.set_bdp_in([(SpwCube_BDP,0,bt.REQUIRED)])
        self.set_bdp_out([(SpwCube_BDP,0)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

        Smooth_AT adds the following to ADMIT summary::

           Key      type        Description
         --------  ------       -----------
         smooth    list        Info about smoothing done (e.g., beam parameters, spectral resolution).
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
        dt = utils.Dtime("Smooth")
        dt.tag("start")
        # get the input keys
        bmaj   = self.getkey("bmaj")
        bmin   = self.getkey("bmin")
        bpa    = self.getkey("bpa")
        velres = self.getkey("velres")

        # take care of potential issues in the unit strings
        # @todo  if not provided?
        bmaj['unit'] = bmaj['unit'].lower()
        bmin['unit'] = bmin['unit'].lower()
        velres['unit'] = velres['unit'].lower()
        taskargs = "bmaj=%s bmin=%s bpa=%s velres=%s" % (bmaj,bmin,bpa,velres)

        ia = taskinit.iatool()
        qa = taskinit.qatool()

        bdpnames=[]
        for ibdp in self._bdp_in:
            istem = ibdp.getimagefile(bt.CASA)
            image_in = ibdp.baseDir() + istem

            bdp_name = self.mkext(istem,'sim')
            image_out = self.dir(bdp_name)
          
            ia.open(image_in)        
            h = casa.imhead(image_in, mode='list')
            pix_scale = np.abs(h['cdelt1'] * 206265.0) # pix scale in asec @todo QA ?
            CC = 299792458.0 # speed of light  @todo somewhere else   [utils.c , but in km/s]

            rest_freq = h['crval3']
            # frequency pixel scale in km/s 
            vel_scale = np.abs(CC*h['cdelt3']/rest_freq/1000.0)

            # unit conversion to arcsec (spatial) or km/s 
            # (velocity) or some flavor of Hz.

            if(bmaj['unit'] == 'pixel'):
                bmaj = bmaj['value']*pix_scale
            else:
                bmaj = bmaj['value']
            if(bmin['unit'] == 'pixel'):
                bmin = bmin['value']*pix_scale
            else:
                bmin = bmin['value']

            hertz_input = False
            if velres['unit'] == 'pixel':
                velres['value'] = velres['value']*vel_scale
                velres['unit'] = 'km/s'
            elif velres['unit'] == 'm/s':
                velres['value'] = velres['value']/1000.0
                velres['unit'] = 'km/s'
            elif velres['unit'][-2:] == 'hz':
                hertz_input = True
            elif velres['unit'] == 'km/s':
                pass
            else:
                logging.error("Unknown units in velres=%s" % velres['unit'])

            rdata = bmaj

            # we smooth in velocity first. if smoothing in velocity
            # the cube apparently must be closed afterwards and 
            # then reopened if spatial smoothing is to be done.

            if velres['value'] > 0:
                # handle the different units allowed. CASA doesn't
                # like lowercase for hz units...          
                if not hertz_input:
                    freq_res = str(velres['value']*1000.0/CC *rest_freq )+'Hz'
                else:
                    freq_res = str(velres['value'])
                    # try to convert velres to km/s for debug purposes
                    velres['value'] = velres['value']/rest_freq*CC / 1000.0 
                    if(velres['unit'] == 'khz'):
                        velres['value'] = velres['value']*1000.0
                        velres['unit'] = 'kHz'
                    elif(velres['unit']=='mhz'):
                        velres['value'] = velres['value']*1E6
                        velres['unit'] = 'MHz'
                    elif(velres['unit']=='ghz'):
                        velres['value'] = velres['value']*1E9
                        velres['unit'] = 'GHz'
                    freq_res = freq_res + velres['unit']

                # NB: there is apparently a bug in CASA. only smoothing along the frequency
                # axis does not work. sepconvolve gives a unit error (says axis unit is radian rather 
                # than Hz). MUST smooth in 2+ dimensions if you want this to work.

                if(velres['value'] < vel_scale):
                    raise Exception,"Desired velocity resolution %g less than pixel scale %g" % (velres['value'],vel_scale)
                image_tmp = self.dir('tmp.smooth')
                im2=ia.sepconvolve(outfile=image_tmp,axes=[0,1,2], types=["boxcar","boxcar","gauss"],\
                                              widths=['1pix','1pix',freq_res], overwrite=True)
                im2.done()
                logging.debug("sepconvolve to %s" % image_out)
                # for some reason, doing this in memory does not seem to work, so outfile must be specified.

                logging.info("Smoothing cube to a velocity resolution of %s km/s" % str(velres['value']))
                logging.info("Smoothing cube to a frequency resolution of %s" % freq_res)
                ia.close()
                ia.open(image_tmp)
                dt.tag("sepconvolve")
            else:
                image_tmp = image_out

            # now do the spatial smoothing 

            convolve_to_min_beam = True                     # default is to convolve to a min enclosing beam

            if bmaj > 0 and bmin > 0:
                # form qa objects out of these so that casa can understand
                bmaj = qa.quantity(bmaj,'arcsec')
                bmin = qa.quantity(bmin,'arcsec')
                bpa  = qa.quantity(bpa,'deg')

                target_res={}
                target_res['major'] = bmaj
                target_res['minor'] = bmin
                target_res['positionangle'] = bpa

                # throw an exception if cannot be convolved

                try:
                    # for whatever reason, if you give convolve2d a beam parameter,
                    # it complains ...
                    im2=ia.convolve2d(outfile=image_out,major = bmaj,\
                                             minor = bmin, pa = bpa,\
                                             targetres=True,overwrite=True)
                    im2.done()
                    logging.info("Smoothing cube to a resolution of %s by %s at a PA of %s" %
                                      (str(bmaj['value']), str(bmin['value']), str(bpa['value'])))
                    convolve_to_min_beam = False
                    achieved_res = target_res
                except:
                    # @todo   remind what you need ?
                    logging.error("Warning: Could not convolve to requested resolution of "\
                            +str(bmaj['value']) + " by " + str(bmin['value']) + \
                            " at a PA of "+ str(bpa['value']))
                    raise Exception,"Could not convolve to beam given!"
            dt.tag("convolve2d-1")

            if convolve_to_min_beam:
                restoring_beams = ia.restoringbeam()
                commonbeam = ia.commonbeam()
                # for whatever reason, setrestoringbeam does not use the same set of hashes...
                commonbeam['positionangle']=commonbeam['pa']
                del commonbeam['pa']

                # if there's one beam, apparently the beams keyword does not exist
                if 'beams' in restoring_beams: 
                    print "Smoothing cube to a resolution of "+  \
                         str(commonbeam['major']['value']) +" by "+ \
                         str(commonbeam['minor']['value'])+" at a PA of "\
                        +str(commonbeam['pa']['value'])  
                    target_res = commonbeam
                    im2=ia.convolve2d(outfile=image_out,major=commonbeam['major'],\
                                               minor=commonbeam['minor'],\
                                               pa=commonbeam['positionangle'],\
                                               targetres=True,overwrite=True)
                    im2.done()
                    achieved_res = commonbeam
                    dt.tag("convolve2d-2")
                else:
                    print "One beam for all planes. Smoothing to common beam redundant."
                    achieved_res = commonbeam 
                    if velres['value'] < 0:
                        ia.fromimage(outfile=image_out, infile=image_in)
                    # not really doing anything
                # else, we've already done what we needed to

                ia.setrestoringbeam(beam = achieved_res)
                rdata = achieved_res['major']['value']

            # else do no smoothing and just close the image

            ia.close() 
            dt.tag("close")

            b1 = SpwCube_BDP(bdp_name)
            self.addoutput(b1) 
            # need to update for multiple images.

            b1.setkey("image", Image(images={bt.CASA:bdp_name}))

            bdpnames = bdpnames.append(bdp_name)

            # and clean up the temp image before the next image
            if velres['value'] > 0:
                utils.remove(image_tmp)

        # thes are task arguments not summary entries.
        _bmaj = qa.convert(achieved_res['major'],'rad')['value']
        _bmin = qa.convert(achieved_res['minor'],'rad')['value']
        _bpa = qa.convert(achieved_res['positionangle'],'deg')['value']
        vres = "%.2f %s" % (velres['value'],velres['unit'])

        logging.regression("SMOOTH: %f %f" % (rdata,velres['value']))
       
        self._summary["smooth"] = SummaryEntry([bdp_name,convolve_to_min_beam,_bmaj,_bmin,_bpa,vres],"Smooth_AT",self.id(True),taskargs)
        dt.tag("done")
        dt.end()
