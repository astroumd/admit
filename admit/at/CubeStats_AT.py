""" .. _CubeStats-at-api:

   **CubeStats_AT** --- Calculates cube statistics.
   ------------------------------------------------

   This module defines the CubeStats_AT class.
"""

from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.Image_BDP import Image_BDP

from admit.util.Table import Table
from admit.util.Image import Image
from admit.util import APlot
from admit.util import utils
from admit.util import stats
from admit.util.segmentfinder import ADMITSegmentFinder
from admit.Summary import SummaryEntry
import admit.util.casautil as casautil
from admit.util.AdmitLogging import AdmitLogging as logging

from copy import deepcopy
import numpy as np
import numpy.ma as ma
import math
import os

try:
    import scipy.stats
    import casa
    import taskinit
except:
    print "WARNING: No CASA; CubeStats task cannot function."

class CubeStats_AT(AT):
    """Compute image-plane based statistics for a cube.

    CubeStats_AT will compute per-channel statistics, as well as a global
    statistics per cube. It computes minimum and maximum values, as well
    as an attempt to get a signal-free ("robust") estimate of the noise,
    with some control how robust statistics this is done.

    Plane based statistics records the channel number, frequency (in GHz),
    mean, sigma, min and max.   If PeakPointPlot (ppp, see below) 
    is selected, it also stores the minpos and maxpos (in pixels). See
    also **CASA::imstat** for more details on the meaning of these
    columns.

    See also :ref:`CubeStats-AT-Design` for the design document.

    **Keywords**
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

      **ppp**: boolean
        Add columns to create a PeakPointPlot. Currently this is somewhat expensive.
        Default: False.

      **maxvrms**: float
        Clip the RMS if it varies by more than this number. This is to avoid creating
        artificial lines when large variations occur due to for example missing short
        spacings.   Use -1 to skip this clipping.
        Default: 2.0

      **psample** : integer
        The spatial sample rate used to examine every peak. This is an expensive option
        and is only used for peakstats.

    **Input BDPs**

      **Image_BDP**: count: 1
        Spectral cube (or map) for which statistics are computed; for example,
        the output of an `Ingest_AT <Ingest_AT.html>`_,
        `SFind2D_AT <SFind2D_AT.html>`_ or `Moment_AT <Moment_AT.html>`_.


    **Output BDPs** 

      **CubeStats_BDP**: count: 1
        The CubeStats_BDP table containing various columns with statistics. Each row
        represents a slice (channel) from the image.
        Extension:   cst.

    Parameters
    ----------
    keyval : dictionary, optional

    Attributes
    ----------
    _version : string

    """

    def __init__(self,**keyval):
        keys = {"robust"  : [],         # signal rejection parameters
                "ppp"     : False,      # PeakPointPlot
                "maxvrms" : 2.0,        # clip varying RMS (-1 to skip)
                "psample" : -1,         # if > 0, spatial sampling rate for PeakStats
        }
        AT.__init__(self,keys,keyval)
        self._version       = "1.1.0"
        self.set_bdp_in([(Image_BDP,      1, bt.REQUIRED)])
        self.set_bdp_out([(CubeStats_BDP, 1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           CubeStats_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +---------+--------+---------------------------------------------+
              |   Key   | type   |    Description                              |
              +=========+========+=============================================+
              | datamean| float  | mean data value float                       |
              +---------+--------+---------------------------------------------+
              | dynrange| float  | dynamic range, equal to datamax/chanrms     |
              +---------+--------+---------------------------------------------+
              | chanrms | float  | one-sigma noise in cube                     |
              +---------+--------+---------------------------------------------+
              | rmsmethd| list   | method and parameters used to compute RMS   |
              +---------+--------+---------------------------------------------+
              | spectra | list   | the spectral plot of signal, noise, and S/N |
              +---------+--------+---------------------------------------------+

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
        """Runs the task.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """

        self._summary = {}
        dt = utils.Dtime("CubeStats")

        #maxvrms = 2.0      # maximum variation in rms allowed (hardcoded for now)
        #maxvrms = -1.0     # turn maximum variation in rms allowed off
        maxvrms = self.getkey("maxvrms")

        psample = -1
        psample = self.getkey("psample")        

        # BDP's used :
        #   b1 = input BDP
        #   b2 = output BDP

        b1 = self._bdp_in[0]
        fin = b1.getimagefile(bt.CASA)

        bdp_name = self.mkext(fin,'cst')
        b2 = CubeStats_BDP(bdp_name)
        self.addoutput(b2)

        # PeakPointPlot 
        use_ppp = self.getkey("ppp")

        # peakstats: not enabled for mortal users yet
        # peakstats = (psample=1, numsigma=4, minchan=3, maxgap=2, peakfit=False)
        pnumsigma = 4
        minchan   = 3
        maxgap    = 2
        peakfit   = False             # True will enable a true gaussian fit
        
        # numsigma:  adding all signal > numsigma ; not user enabled;   for peaksum.
        numsigma = -1.0
        numsigma = 3.0

        # tools we need
        ia = taskinit.iatool()

        # grab the new robust statistics. If this is used, 'rms' will be the RMS,
        # else we will use RMS = 1.4826*MAD (MAD does a decent job on outliers as well)
        # and was the only method available before CASA 4.4 when robust was implemented
        robust = self.getkey("robust")
        rargs = casautil.parse_robust(robust)
        nrargs = len(rargs)

        if nrargs == 0:
           sumrargs = "medabsdevmed"      # for the summary, indicate the default robust
        else:
           sumrargs = str(rargs)

        self._summary["rmsmethd"] = SummaryEntry([sumrargs,fin],"CubeStats_AT",self.id(True))
        #@todo think about using this instead of putting 'fin' in all the SummaryEntry
        #self._summary["casaimage"] = SummaryEntry(fin,"CubeStats_AT",self.id(True))

        # extra CASA call to get the freq's in GHz, as these are not in imstat1{}
        # @todo what if the coordinates are not in FREQ ?
        # Note: CAS-7648 bug on 3D cubes
        if False:
            # csys method
            ia.open(self.dir(fin))
            csys = ia.coordsys() 
            spec_axis = csys.findaxisbyname("spectral") 
            # ieck, we need a valid position, or else it will come back and "Exception: All selected pixels are masked"
            #freqs = ia.getprofile(spec_axis, region=rg.box([0,0],[0,0]))['coords']/1e9
            #freqs = ia.getprofile(spec_axis)['coords']/1e9
            freqs = ia.getprofile(spec_axis,unit="GHz")['coords']
            dt.tag("getprofile")
        else:
            # old imval method 
            #imval0 = casa.imval(self.dir(fin),box='0,0,0,0')     # this fails on 3D
            imval0 = casa.imval(self.dir(fin))
            freqs = imval0['coords'].transpose()[2]/1e9
            dt.tag("imval")
        nchan = len(freqs)
        chans = np.arange(nchan)

        # call CASA to get what we want
        # imstat0 is the whole cube, imstat1 the plane based statistics
        # warning: certain robust stats (**rargs) on the whole cube are going to be very slow
        dt.tag("start")
        imstat0 = casa.imstat(self.dir(fin),           logfile=self.dir('imstat0.logfile'),append=False,**rargs)
        dt.tag("imstat0")
        imstat1 = casa.imstat(self.dir(fin),axes=[0,1],logfile=self.dir('imstat1.logfile'),append=False,**rargs)
        dt.tag("imstat1")
        # imm = casa.immoments(self.dir(fin),axis='spec', moments=8, outfile=self.dir('ppp.im'))
        if nrargs > 0:
            # need to get the peaks without rubust
            imstat10 = casa.imstat(self.dir(fin),           logfile=self.dir('imstat0.logfile'),append=True)
            dt.tag("imstat10")
            imstat11 = casa.imstat(self.dir(fin),axes=[0,1],logfile=self.dir('imstat1.logfile'),append=True)
            dt.tag("imstat11")

        # grab the relevant plane-based things from imstat1
        if nrargs == 0:
            mean    = imstat1["mean"]
            sigma   = imstat1["medabsdevmed"]*1.4826     # see also: astropy.stats.median_absolute_deviation()
            peakval = imstat1["max"]
            minval  = imstat1["min"]
        else:
            mean    = imstat1["mean"]
            sigma   = imstat1["rms"]
            peakval = imstat11["max"]
            minval  = imstat11["min"]

        if True:
            # work around a bug in imstat(axes=[0,1]) for last channel [CAS-7697]
            for i in range(len(sigma)):
                if sigma[i] == 0.0:
                    minval[i] = peakval[i] = 0.0

        # too many variations in the RMS ?
        sigma_pos = sigma[np.where(sigma>0)]
        smin = sigma_pos.min()
        smax = sigma_pos.max()
        logging.info("sigma varies from %f to %f; %d/%d channels ok" % (smin,smax,len(sigma_pos),len(sigma)))
        if maxvrms > 0:
            if smax/smin > maxvrms:
                cliprms = smin * maxvrms
                logging.warning("sigma varies too much, going to clip to %g (%g > %g)" % (cliprms, smax/smin, maxvrms))
                sigma = np.where(sigma < cliprms, sigma, cliprms)

        nzeros = len(np.where(sigma<=0.0)[0])
        if nzeros > 0:
            zeroch = np.where(sigma<=0.0)[0]
            logging.warning("There are %d fully masked channels (%s)" % (nzeros,str(zeroch)))
            
        # @todo   (and check again) for foobar.fits all sigma's became 0 when robust was selected
        #         was this with mask=True/False?

        # PeakPointPlot (can be expensive, hence the option)
        if use_ppp:
            logging.info("Computing MaxPos for PeakPointPlot")
            xpos    = np.zeros(nchan)
            ypos    = np.zeros(nchan)
            peaksum = np.zeros(nchan)

            ia.open(self.dir(fin))
            for i in range(nchan):
                if sigma[i] > 0.0:
                    plane = ia.getchunk(blc=[0,0,i,-1],trc=[-1,-1,i,-1],dropdeg=True)
                    v = ma.masked_invalid(plane)
                    v_abs = np.absolute(v)
                    max = np.unravel_index(v_abs.argmax(), v_abs.shape)
                    xpos[i] = max[0]
                    ypos[i] = max[1]
                    if numsigma > 0.0:
                        peaksum[i] = ma.masked_less(v,numsigma * sigma[i]).sum()
            peaksum = np.nan_to_num(peaksum)    # put 0's where nan's are found
            ia.close()
            dt.tag("ppp")

        # construct the admit Table for CubeStats_BDP
        # note data needs to be a tuple, later to be column_stack'd
        if use_ppp:
            labels = ["channel" ,"frequency" ,"mean"    ,"sigma"   ,"max"     ,"maxposx" ,"maxposy" ,"min",     "peaksum"]
            units  = ["number"  ,"GHz"       ,"Jy/beam" ,"Jy/beam" ,"Jy/beam" ,"number"  ,"number"  ,"Jy/beam", "Jy"]
            data   = (chans     ,freqs       ,mean      ,sigma     ,peakval   ,xpos      ,ypos      ,minval,    peaksum)

        else:
            labels = ["channel" ,"frequency" ,"mean"    ,"sigma"   ,"max"     ,"min"]
            units  = ["number"  ,"GHz"       ,"Jy/beam" ,"Jy/beam" ,"Jy/beam" ,"Jy/beam"]
            data   = (chans     ,freqs       ,mean      ,sigma     ,peakval   ,minval)

        table = Table(columns=labels,units=units,data=np.column_stack(data))
        b2.setkey("table",table)

        # get the full cube statistics, it depends if robust was pre-selected
        if nrargs == 0:
            mean0  = imstat0["mean"][0]
            sigma0 = imstat0["medabsdevmed"][0]*1.4826
            peak0  = imstat0["max"][0]
            b2.setkey("mean" , float(mean0))
            b2.setkey("sigma", float(sigma0))
            b2.setkey("minval",float(imstat0["min"][0]))
            b2.setkey("maxval",float(imstat0["max"][0]))
            b2.setkey("minpos",imstat0["minpos"][:3].tolist())     #? [] or array(..dtype=int32) ??
            b2.setkey("maxpos",imstat0["maxpos"][:3].tolist())     #? [] or array(..dtype=int32) ??
            logging.info("CubeMax: %f @ %s" % (imstat0["max"][0],str(imstat0["maxpos"])))
            logging.info("CubeMin: %f @ %s" % (imstat0["min"][0],str(imstat0["minpos"])))
            logging.info("CubeRMS: %f" % sigma0)
        else:
            mean0  = imstat0["mean"][0]
            sigma0 = imstat0["rms"][0]
            peak0  = imstat10["max"][0]
            b2.setkey("mean" , float(mean0))
            b2.setkey("sigma", float(sigma0))
            b2.setkey("minval",float(imstat10["min"][0]))
            b2.setkey("maxval",float(imstat10["max"][0]))
            b2.setkey("minpos",imstat10["minpos"][:3].tolist())     #? [] or array(..dtype=int32) ??
            b2.setkey("maxpos",imstat10["maxpos"][:3].tolist())     #? [] or array(..dtype=int32) ??
            logging.info("CubeMax: %f @ %s" % (imstat10["max"][0],str(imstat10["maxpos"])))
            logging.info("CubeMin: %f @ %s" % (imstat10["min"][0],str(imstat10["minpos"])))
            logging.info("CubeRMS: %f" % sigma0)
        b2.setkey("robust",robust)
        rms_ratio = imstat0["rms"][0]/sigma0
        logging.info("RMS Sanity check %f" % rms_ratio)
        if rms_ratio > 1.5:
            logging.warning("RMS sanity check = %f.  Either bad sidelobes, lotsa signal, or both" % rms_ratio)
        logging.regression("CST: %f %f" % (sigma0, rms_ratio))

        # plots: no plots need to be made when nchan=1 for continuum
        # however we could make a histogram, overlaying the "best" gauss so 
        # signal deviations are clear?

        logging.info('mean,rms,S/N=%f %f %f' % (mean0,sigma0,peak0/sigma0))

        if nchan == 1:
            # for a continuum/1-channel we only need to stuff some numbers into the _summary
            self._summary["chanrms"] = SummaryEntry([float(sigma0), fin], "CubeStats_AT", self.id(True))
            self._summary["dynrange"] = SummaryEntry([float(peak0)/float(sigma0), fin], "CubeStats_AT", self.id(True))
            self._summary["datamean"] = SummaryEntry([float(mean0), fin], "CubeStats_AT", self.id(True))
        else:
            y1 = np.log10(ma.masked_invalid(peakval))
            y2 = np.log10(ma.masked_invalid(sigma))
            y3 = y1-y2

            # Note: log10(-minval) will fail with a runtime domain error if all values
            # in minval are positive , so do a check here and only call log10 if there
            # is at least one negative value in minval.
            # RuntimeWarning: invalid value encountered in log10
            if (minval <= 0).all(): 
                y4 = np.log10(ma.masked_invalid(-minval))
            else:
                y4 = np.zeros(len(minval))
            y5 = y1-y4
            y = [y1,y2,y3,y4]
            title = 'CubeStats: ' + bdp_name+'_0'
            xlab  = 'Channel'
            ylab  = 'log(Peak,Noise,Peak/Noise)'
            labels = ['log(peak)','log(rms noise)','log(peak/noise)','log(|minval|)']
            myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())
            segp = [[chans[0],chans[nchan-1],math.log10(sigma0),math.log10(sigma0)]]
            myplot.plotter(chans,y,title,bdp_name+"_0",xlab=xlab,ylab=ylab,segments=segp,labels=labels,thumbnail=True)
            imfile = myplot.getFigure(figno=myplot.figno,relative=True)
            thumbfile = myplot.getThumbnail(figno=myplot.figno,relative=True)

            image0 = Image(images={bt.PNG:imfile},thumbnail=thumbfile,thumbnailtype=bt.PNG,description="CubeStats_0")
            b2.addimage(image0,"im0")

            if use_ppp:
                # new trial for Lee
                title = 'PeakSum: (numsigma=%.1f)' % (numsigma)
                ylab = 'Jy*N_ppb'
                myplot.plotter(chans,[peaksum],title,bdp_name+"_00",xlab=xlab,ylab=ylab,thumbnail=False)

            if True:
                # hack ascii table
                y30 = np.where(sigma > 0, np.log10(peakval/sigma), 0.0)
                table2 = Table(columns=["freq","log(P/N)"],data=np.column_stack((freqs,y30)))
                table2.exportTable(self.dir("testCubeStats.tab"))
                del table2

            # the "box" for the "spectrum" is all pixels.  Don't know how to 
            # get this except via shape.
            ia.open(self.dir(fin))
            s = ia.summary()
            ia.close()
            if 'shape' in s:
                specbox = (0,0,s['shape'][0],s['shape'][1])
            else:
                specbox = ()

            caption = "Emission characteristics as a function of channel, as derived by CubeStats_AT "
            caption += "(cyan: global rms,"
            caption += " green: noise per channel,"
            caption += " blue: peak value per channel,"
            caption += " red: peak/noise per channel)."
            self._summary["spectra"] = SummaryEntry([0, 0, str(specbox), 'Channel', imfile, thumbfile , caption, fin], "CubeStats_AT", self.id(True))
            self._summary["chanrms"] = SummaryEntry([float(sigma0), fin], "CubeStats_AT", self.id(True))

            # @todo Will imstat["max"][0] always be equal to s['datamax']?  If not, why not?
            if 'datamax' in s:
                self._summary["dynrange"] = SummaryEntry([float(s['datamax']/sigma0), fin], "CubeStats_AT", self.id(True))
            else:
                self._summary["dynrange"] = SummaryEntry([float(imstat0["max"][0]/sigma0), fin], "CubeStats_AT", self.id(True))
            self._summary["datamean"] = SummaryEntry([imstat0["mean"][0], fin], "CubeStats_AT", self.id(True))

            title = bdp_name + "_1"
            xlab =  'log(Peak,Noise,P/N)'
            myplot.histogram([y1,y2,y3],title,bdp_name+"_1",xlab=xlab,thumbnail=True)

            imfile = myplot.getFigure(figno=myplot.figno,relative=True)
            thumbfile = myplot.getThumbnail(figno=myplot.figno,relative=True)
            image1 = Image(images={bt.PNG:imfile},thumbnail=thumbfile,thumbnailtype=bt.PNG,description="CubeStats_1")
            b2.addimage(image1,"im1")

            # note that the 'y2' can have been clipped, which can throw off stats.robust()
            # @todo  should set a mask for those.

            title = bdp_name + "_2"
            xlab = 'log(Noise))'
            n = len(y2)
            ry2 = stats.robust(y2)
            y2_mean = ry2.mean()
            y2_std  = ry2.std()
            if n>9: logging.debug("NORMALTEST2: %s" % str(scipy.stats.normaltest(ry2)))
            myplot.hisplot(y2,title,bdp_name+"_2",xlab=xlab,gauss=[y2_mean,y2_std],thumbnail=True)

            title = bdp_name + "_3"
            xlab = 'log(diff[Noise])'
            n = len(y2)
            # dy2 = y2[0:-2] - y2[1:-1]
            dy2 = ma.masked_equal(y2[0:-2] - y2[1:-1],0.0).compressed()
            rdy2 = stats.robust(dy2)
            dy2_mean = rdy2.mean()
            dy2_std  = rdy2.std()
            if n>9: logging.debug("NORMALTEST3: %s" % str(scipy.stats.normaltest(rdy2)))
            myplot.hisplot(dy2,title,bdp_name+"_3",xlab=xlab,gauss=[dy2_mean,dy2_std],thumbnail=True)


            title = bdp_name + "_4"
            xlab = 'log(Signal/Noise))'
            n = len(y3)
            ry3 = stats.robust(y3)
            y3_mean = ry3.mean()
            y3_std  = ry3.std()
            if n>9: logging.debug("NORMALTEST4: %s" % str(scipy.stats.normaltest(ry3)))
            myplot.hisplot(y3,title,bdp_name+"_4",xlab=xlab,gauss=[y3_mean,y3_std],thumbnail=True)

            title = bdp_name + "_5"
            xlab = 'log(diff[Signal/Noise)])'
            n = len(y3)
            dy3 = y3[0:-2] - y3[1:-1]
            rdy3 = stats.robust(dy3)
            dy3_mean = rdy3.mean()
            dy3_std  = rdy3.std()
            if n>9: logging.debug("NORMALTEST5: %s" % str(scipy.stats.normaltest(rdy3)))
            myplot.hisplot(dy3,title,bdp_name+"_5",xlab=xlab,gauss=[dy3_mean,dy3_std],thumbnail=True)


            title = bdp_name + "_6"
            xlab = 'log(Peak+Min)'
            n = len(y1)
            ry5 = stats.robust(y5)
            y5_mean = ry5.mean()
            y5_std  = ry5.std()
            if n>9: logging.debug("NORMALTEST6: %s" % str(scipy.stats.normaltest(ry5)))
            myplot.hisplot(y5,title,bdp_name+"_6",xlab=xlab,gauss=[y5_mean,y5_std],thumbnail=True)

            logging.debug("LogPeak: m,s= %f %f min/max %f %f" % (y1.mean(),y1.std(),y1.min(),y1.max()))
            logging.debug("LogNoise: m,s= %f %f %f %f min/max %f %f" % (y2.mean(),y2.std(),y2_mean,y2_std,y2.min(),y2.max()))
            logging.debug("LogDeltaNoise: RMS/sqrt(2)= %f %f " % (dy2.std()/math.sqrt(2),dy2_std/math.sqrt(2)))
            logging.debug("LogDeltaP/N:   RMS/sqrt(2)= %f %f" % (dy3.std()/math.sqrt(2),dy3_std/math.sqrt(2)))
            logging.debug("LogPeak+Min: robust m,s= %f %f" % (y5_mean,y5_std))

            # compute two ratios that should both be near 1.0 if noise is 'normal'
            ratio  = y2.std()/(dy2.std()/math.sqrt(2))
            ratio2 = y2_std/(dy2_std/math.sqrt(2))
            logging.info("RMS BAD VARIATION RATIO: %f %f" % (ratio,ratio2))

        # making PPP plot
        if nchan > 1 and use_ppp:
            smax = 10
            gamma = 0.75

            z0 = peakval/peakval.max()
            # point sizes
            s = np.pi * ( smax * (z0**gamma) )**2
            cmds = ["grid", "axis equal"]
            title = "Peak Points per channel"
            pppimage = bdp_name + '_ppp'
            myplot.scatter(xpos,ypos,title=title,figname=pppimage,size=s,color=chans,cmds=cmds,thumbnail=True)
            pppimage     = myplot.getFigure(figno=myplot.figno,relative=True)
            pppthumbnail = myplot.getThumbnail(figno=myplot.figno,relative=True)
            caption = "Peak point plot: Locations of per-channel peaks in the image cube " + fin
            self._summary["peakpnt"] = SummaryEntry([pppimage, pppthumbnail, caption, fin], "CubeStats_AT", self.id(True))
        dt.tag("plotting")

        # making PeakStats plot
        if nchan > 1 and psample > 0:
            logging.info("Computing peakstats")
            # grab peak,mean and width values for all peaks
            (pval,mval,wval) = peakstats(self.dir(fin),freqs,sigma0,pnumsigma,minchan,maxgap,psample,peakfit)
            title = "PeakStats: cutoff = %g" % (sigma0*pnumsigma)
            xlab = 'Peak value'
            ylab = 'FWHM (channels)'
            pppimage = bdp_name + '_peakstats'
            cval = mval
            myplot.scatter(pval,wval,title=title,xlab=xlab,ylab=ylab,color=cval,figname=pppimage,thumbnail=False)
            dt.tag("peakstats")
            

        # myplot.final()    # pjt debug 
        # all done!
        dt.tag("done")

        taskargs = "robust=" + sumrargs 
        if use_ppp: 
            taskargs = taskargs + " ppp=True"
        else: 
            taskargs = taskargs + " ppp=False"
        for v in self._summary:
            self._summary[v].setTaskArgs(taskargs)

        ia.done()     # is that a good habit?
        dt.tag("summary")
        dt.end()

#
# @todo NEMO::ccdpeakstats does test0 in << 1", admit takes 85-90" with sample=4 -> 6000"
# Calling line_segments() speeding up to 5" for psample=1 even
        
def peakstats(image, freq, sigma, nsigma, minchan, maxgap, psample, peakfit = False):
    """ Go through a cube and find peaks in the spectral dimension

    It will gather a table of <peak>,<freq>,<sigma> which can be
    optionally used for plotting
    """
    if psample < 0: return
    cutoff = nsigma * sigma
    madata = casautil.getdata(image)
    data   = madata.data
    shape  = data.shape
    logging.debug("peakstats: shape=%s cutoff=%g" % (str(shape),cutoff))
    #print "DATA SHAPE:",shape
    #print "cutoff=",cutoff
    nx = shape[0]
    ny = shape[1]
    nz = shape[2]
    chan = np.arange(nz)
    # prepare the segment finder
    # we now have an array data[nx,ny,nz]
    sum = 0.0
    pval = []
    mval = []
    wval = []
    for x in range(0,nx,psample):
        for y in range(0,ny,psample):
            s0    = data[x,y,:]
            spec  = ma.masked_invalid(s0)
            sum += spec.sum()
            # using abs=True is a bit counter intuitive, but a patch to deal with the confusion in
            # ADMITSegmentFinder w.r.t abs usage
            asf = ADMITSegmentFinder(pmin=nsigma, minchan=minchan, maxgap=maxgap, freq=freq, spec=spec, abs=True)
            #asf = ADMITSegmentFinder(pmin=nsigma, minchan=minchan, maxgap=maxgap, freq=freq, spec=spec, abs=False)
            f = asf.line_segments(spec, nsigma*sigma)
            for s in f:
                if False:
                    for i in range(s[0],s[1]+1):
                        print "# ",x,y,i,spec[i]
                ## area preserving and peak are correlated, 18% difference
                ## fitgauss1Dm was about 5"
                ## with fitgauss1D was about 30", and still bad fits
                par      = utils.fitgauss1Dm(chan[s[0]:s[1]+1], spec[s[0]:s[1]+1], True)           # peak from max
                #par      = utils.fitgauss1Dm(chan[s[0]:s[1]+1], spec[s[0]:s[1]+1], False)       # peak from area preserving
                if peakfit:
                    (par,cov) = utils.fitgauss1D (chan[s[0]:s[1]+1], spec[s[0]:s[1]+1],par)
                #print "FIND:  ",x,y,s,cutoff,0.0,0.0,par[0],par[1],par[2],s[1]-s[0]+1
                pval.append(par[0])
                mval.append(par[1])
                wval.append(par[2])
    #print "SUM:",sum
    return (np.array(pval),np.array(mval),np.array(wval))

