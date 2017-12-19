""" .. _SFind2D-at-api:

   **SFind2D_AT** --- Finds sources in a 2D map.
   ---------------------------------------------

   This module defines the SFind2D_AT class.
"""
from admit.AT import AT
from admit.Summary import SummaryEntry
from admit.util import APlot
import admit.util.bdp_types as bt
from admit.bdp.SourceList_BDP import SourceList_BDP
import admit.util.casautil as casautil
import admit.util.Image as Image
import admit.util.Line as Line
import admit.util.ImPlot as ImPlot
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
import admit.util.utils as utils
from admit.util.AdmitLogging import AdmitLogging as logging

import numpy as np
import numpy.ma as ma
from copy import deepcopy

import types
try:
    import casa
    import taskinit
except:
    print "WARNING: No CASA; SFind2D task cannot function."

class SFind2D_AT(AT):
    """
    Find sources in a 2-D map -- Sources are found based on peak flux density
    (Jy/beam) and fitted with a Gaussian to determine source parameters. The
    AT uses the CASA findsources task. The key words allow the cutoff level
    for source discovery to be limited either by N times the RMS noise or by
    a dynamic range. The latter is important when a strong source in the image
    increases noise local to that source. SFind2d_AT can be used on continuum
    maps, moment maps, or other 2-D images. It is likely to give poor fits
    for sources that extend over many beams.


    **Keywords**

        **sigma**: float
            The noise level to be used for calculating the cutoff value. 
            Negative value: the RMS is obtained from the CubeStats_BDP, if provided;
            otherwise it is calculated via call to imstat using the region parameter.
            Positive value: override **CubeStats**, the user provided value is utilized.
            Default: -1.0.

        **numsigma**: float
            The lower cutoff level for source finder in terms of **sigma**.
            Default: 6.0.

        **robust**: list
            A compound list keyword describing how robust statistics is used. By default
            all data are used, with CASA's "medabsdevmed" (MAD) statistic as the robust noise
            estimator. For normal (gaussian) noise, RMS = 1.4826 * MAD.

            For more flexible noise statistics see **CASA::imstat** for a detailed background,
            but the current valid algorithms and their optional additional arguments are:

               'classic',clmethod{'auto','tiled','framework'}

               'chauvenet',zscore[-1],maxiter[-1]

               'fit-half',center{'mean','median','zero'},lside{True,False}

               'hinges-fences',fence[-1]

            Examples:    

                robust=['classic','auto']

                robust=['fit-half','zero']

                robust=['hin',1.5]

    
            Used only if **sigma** is negative and there is no CubeStats_BDP given.

        **snmax**: float
            Maximum dynamic range between strongest source in map and **sigma** computed or provided.
            Used to calculate a new **sigma** if the previously computed **sigma** implies a larger
            dynamic range [(map max)/"sigma"] than requested here. 
            Negative  -- use the (nsgima * sigma) value for limiting flux density
            Default: 35

            Example:

               snmax= 35.0  

            Limits search to 1/35th brightness of max source in map -- good default
            for pipeline ALMA images which have not been selfcaled.

        **nmax**: int
            Maximum sources that will be searched for in the map.
            Default: 30

        **region**: string
            Region to search for sources. Format is CASA region specification.
            Default: entire image.

            Example:

               region='box[[10pix,10pix],[200pix,200pix]]'

               region='circle[[19h58m52.7s,+40d42m06.04s ],30.0arcsec]'

        **zoom**: int
          Image zoom ratio applied to the source map plot. This does not
          affect the base (CASA) image itself. Default: 1.

    **Input BDPs**

        **SpwCube_BDP**: count: 1
            Input 2-D map, typically from `Moment_AT <Moment_AT.html>`_.
            Needs to be a noise-flat map. `Ingest_AT <Ingest_AT.html>`_
            has the option for creating a noise-flat map from a primary beam
            corrected map and a primary beam.

        **CubeStats_BDP**: count: 1 (optional)
            Output from `CubeStats_AT <CubeStats_AT.html>`_ executed on the
            input image cube.  Optional, see description of **sigma** keyword.

    **Output BDPs**

        **SourceList_BDP**: count: 1
            An image and table with source information, ordered by peak flux
            density. Can be input to `CubeStats_AT <CubeStats_AT.html>`_
            to produce spectra at each source position.

    Parameters
    ----------
        keyval : dictionary, optional

    Attributes
    ----------
        _version : string
    """

    def __init__(self, **keyval):
        keys = {"numsigma" : 6.0,          # default to 5 sigma
                "sigma"    : -1.0,         # default to grab sigma from CubeStats BDP
                "region"   : "",           # default to entire map
                "robust"   : ['hin',1.5],  # default to classic MAD
                "snmax"    : 35.0,         # default to limit dynamic range to 100
                "nmax"     : 30,           # default to limit max number of sources to 30
                "zoom"     : 1,            # default map plot zoom ratio
               }

        AT.__init__(self,keys,keyval)
        self._version = "1.1.1"
        self.set_bdp_in([(Image_BDP,2,bt.OPTIONAL),
                         (CubeStats_BDP,1,bt.OPTIONAL)])
        self.set_bdp_out([(SourceList_BDP, 1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           SFind2D_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | sources  | table    |   table of source parameters      |
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

    def run(self):
        """ The run method creates the BDP

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        dt = utils.Dtime("SFind2D")               # tagging time
        self._summary = {}
        # get key words that user input
        nsigma = self.getkey("numsigma")
        sigma  = self.getkey("sigma")
        region = self.getkey("region")
        robust = self.getkey("robust")
        snmax  = self.getkey("snmax")
        nmax   = self.getkey("nmax")
        ds9 = True                                     # writes a "ds9.reg" file
        mpl = True                                     # aplot.map1() plot
        dynlog = 20.0                                  # above this value of dyn range finder chart is log I-scaled
        bpatch = True                                  # patch units to Jy/beam for ia.findsources()
        
        # get the input casa image from bdp[0]
        bdpin = self._bdp_in[0]
        infile = bdpin.getimagefile(bt.CASA)
        if mpl:
            data = np.flipud(np.rot90(casautil.getdata(self.dir(infile)).data))

        # check if there is a 2nd image (which will be a PB)
        for i in range(len(self._bdp_in)):
            print 'BDP',i,type(self._bdp_in[i])

        if self._bdp_in[2] != None:
            bdpin_pb  = self._bdp_in[1]            
            bdpin_cst = self._bdp_in[2]
            print "Need to process PB"
        else:
            bdpin_pb  = None
            bdpin_cst = self._bdp_in[1]
            print "No PB given"
            

        # get the output bdp basename
        slbase = self.mkext(infile,'sl')

        # make sure it's a 2D map
        if not casautil.mapdim(self.dir(infile),2):
            raise Exception,"Input map dimension not 2: %s" % infile

        # arguments for imstat call if required
        args = {"imagename" : self.dir(infile)}
        if region != "":
            args["region"] = region
        dt.tag("start")

        # The following code sets the sigma level for searching for sources using
        # the sigma and snmax keyword as appropriate
        # if no CubeStats BDP was given and no sigma was specified:
        # find a noise level via casa.imstat()
        # if a CubeStat_BDP is given get it from there.
        if bdpin_cst == None:
            # get statistics from input image with imstat because no CubeStat_BDP
            stat  = casa.imstat(**args)
            dmin  = float(stat["min"][0])                 # these would be wrong if robust were used already
            dmax  = float(stat["max"][0])
            args.update(casautil.parse_robust(robust))    # only now add robust keywords for the sigma
            stat  = casa.imstat(**args)            
            if sigma <= 0.0 :
                sigma = float(stat["sigma"][0])
            dt.tag("imstat")
        else:
            # get statistics from CubeStat_BDP 
            sigma = bdpin_cst.get("sigma")
            dmin  = bdpin_cst.get("minval")
            dmax  = bdpin_cst.get("maxval")

        self.setkey("sigma",sigma)
        # calculate cutoff based either on RMS or dynamic range limitation
        drange = dmax/(nsigma*sigma)
        if snmax < 0.0 :
            snmax = drange
        if drange > snmax :
            cutoff = 1.0/snmax
        else:
            cutoff = 1.0/drange
        logging.info("sigma, dmin, dmax, snmax, cutoff %g %g %g %g %g" % (sigma, dmin, dmax, snmax, cutoff))
        # define arguments for call to findsources
        args2 = {"cutoff" : cutoff}
        args2["nmax"] = nmax
        if region != "" :
            args2["region"] = region
        #args2["mask"] = ""
        args2["point"] = False
        args2["width"] = 5
        args2["negfind"] = False
        # set-up for SourceList_BDP
        slbdp = SourceList_BDP(slbase)

        # connect to casa image and call casa ia.findsources tool
        ia = taskinit.iatool()
        ia.open(self.dir(infile))

        # findsources() cannot deal with  'Jy/beam.km/s' ???
        # so for the duration of findsources() we patch it
        bunit = ia.brightnessunit()
        if bpatch and bunit != 'Jy/beam':
            logging.warning("Temporarely patching your %s units to Jy/beam for ia.findsources()" % bunit) 
            ia.setbrightnessunit('Jy/beam')
        else:
            bpatch = False
        atab = ia.findsources(**args2)
        if bpatch:
            ia.setbrightnessunit(bunit)
        
        taskargs = "nsigma=%4.1f sigma=%g region=%s robust=%s snmax=%5.1f nmax=%d" % (nsigma,sigma,str(region),str(robust),snmax,nmax)
        dt.tag("findsources")
        nsources = atab["nelements"] 
        xtab = []
        ytab = []
        logscale = False
        sumflux = 0.0
        if nsources > 0:
            # @TODO: Why are Xpix, YPix not stored in the table?
            #        -> PJT: I left them out since they are connected to an image which may not be available here
            #                but we should store the frequency of the observation here for later bandmerging
            logging.debug("%s" % str(atab['component0']['shape']))
            logging.info("Right Ascen.  Declination   X(pix)   Y(pix)      Peak       Flux    Major   Minor    PA    SNR")
            funits = atab['component0']['flux']['unit']
            if atab['component0']['shape'].has_key('majoraxis'):
                sunits = atab['component0']['shape']['majoraxis']['unit']
                aunits = atab['component0']['shape']['positionangle']['unit']
            else:
                sunits = "n/a"
                aunits = "n/a"
            punits = ia.summary()['unit']
            logging.info("                                               %s       %s    %s   %s   %s" % (punits,funits,sunits,sunits,aunits))
            #
            # @todo future improvement is to look at image coordinates and control output appropriately
            #
            if ds9:
                # @todo variable name
                regname = self.mkext(infile,'ds9.reg')
                fp9 = open(self.dir(regname),"w!")
            sn0 = -1.0
            for i in range(nsources):
                c = "component%d" % i
                name = "%d" % (i+1)
                r = atab[c]['shape']['direction']['m0']['value']
                d = atab[c]['shape']['direction']['m1']['value']
                pixel = ia.topixel([r,d])
                xpos = pixel['numeric'][0]
                ypos = pixel['numeric'][1]
                rd = ia.toworld([xpos,ypos],'s')
                ra = rd['string'][0][:12]
                dec = rd['string'][1][:12]
                flux = atab[c]['flux']['value'][0]
                sumflux = sumflux + flux
                if atab[c]['shape'].has_key('majoraxis'):
                    smajor = atab[c]['shape']['majoraxis']['value']
                    sminor = atab[c]['shape']['minoraxis']['value']
                    sangle = atab[c]['shape']['positionangle']['value']
                else:
                    smajor = 0.0
                    sminor = 0.0
                    sangle = 0.0
                peakstr = ia.pixelvalue([xpos,ypos,0,0])
                if len(peakstr) == 0:
                    logging.warning("Problem with source %d @ %d,%d" % (i,xpos,ypos))
                    continue
                peakf = peakstr['value']['value']
                snr = peakf/sigma
                if snr > dynlog:
                    logscale = True
                if snr > sn0:
                    sn0 = snr
                logging.info("%s %s %8.2f %8.2f %10.3g %10.3g %7.3f %7.3f %6.1f %6.1f" % (ra,dec,xpos,ypos,peakf,flux,smajor,sminor,sangle,snr))
                
                xtab.append(xpos)
                ytab.append(ypos)
                slbdp.addRow([name,ra,dec,flux,peakf,smajor,sminor,sangle])
                if ds9:
                    ras = ra
                    des = dec.replace('.',':',2)
                    msg = 'ellipse(%s,%s,%g",%g",%g) # text={%s}' % (ras,des,smajor,sminor,sangle+90.0,i+1)
                    fp9.write("%s\n" % msg)
            if ds9:
                fp9.close()
                logging.info("Wrote ds9.reg")
            dt.tag("table")
        logging.regression("CONTFLUX: %d %g" % (nsources,sumflux))
        

        summary = ia.summary()
        beammaj = summary['restoringbeam']['major']['value']
        beammin = summary['restoringbeam']['minor']['value']
        beamunit = summary['restoringbeam']['minor']['unit']
        beamang = summary['restoringbeam']['positionangle']['value']
        angunit = summary['restoringbeam']['positionangle']['unit']
        # @todo add to table comments?
        logging.info(" Fitted Gaussian size; NOT deconvolved source size.")
        logging.info(" Restoring Beam: Major axis: %10.3g %s , Minor axis: %10.3g %s , PA: %5.1f %s" % (beammaj, beamunit, beammin, beamunit, beamang, angunit))
        # form into a xml table
        
        # output is a table_bdp
        self.addoutput(slbdp)

        # instantiate a plotter for all plots made herein
        myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())

        # make output png with circles marking sources found
        if mpl:
            circles=[]
            nx = data.shape[1]             # data[] array was already flipud(rot90)'d
            ny = data.shape[0]             # 
            for (x,y) in zip(xtab,ytab):
                circles.append([x,y,1])
            # @todo variable name
            if logscale:
                logging.warning("LogScaling applied")
                data = data/sigma
                data = np.where(data<0,-np.log10(1-data),+np.log10(1+data))
            if nsources == 0:
                title = "SFind2D: 0 sources above S/N=%.1f" % (nsigma)
            elif nsources == 1:
                title = "SFind2D: 1 source (%.1f < S/N < %.1f)" % (nsigma,sn0)
            else:
                title = "SFind2D: %d sources (%.1f < S/N < %.1f)" % (nsources,nsigma,sn0)
            myplot.map1(data,title,slbase,thumbnail=True,circles=circles,
                        zoom=self.getkey("zoom"))

        #---------------------------------------------------------
        # Get the figure and thumbmail names and create a caption
        #---------------------------------------------------------
        imname = myplot.getFigure(figno=myplot.figno,relative=True)
        thumbnailname = myplot.getThumbnail(figno=myplot.figno,relative=True)
        caption = "Image of input map with sources found by SFind2D overlayed in green."
        slbdp.table.description="Table of source locations and sizes (not deconvolved)"
 
        #---------------------------------------------------------
        # Add finder image to the BDP
        #---------------------------------------------------------
        image = Image(images={bt.PNG: imname}, 
                      thumbnail=thumbnailname, 
                      thumbnailtype=bt.PNG, description=caption)
        slbdp.image.addimage(image, "finderimage")

        #-------------------------------------------------------------
        # Create the summary entry for the table and image
        #-------------------------------------------------------------
        self._summary["sources"] = SummaryEntry([slbdp.table.serialize(),
                                                 slbdp.image.serialize()],
                                                "SFind2D_AT", 
                                                self.id(True), taskargs)
        
        dt.tag("done")
        dt.end()
