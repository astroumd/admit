""" .. _PVCorr-at-api:

   **PVCorr_AT** --- Determines position-velocity correlations in a map.
   ---------------------------------------------------------------------

   Defines the PVCorr_AT class.
"""
import sys, os, logging

from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.util.Image import Image
from admit.util.Table import Table
import admit.util.utils as utils
import admit.util.casautil as casautil
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.PVCorr_BDP import PVCorr_BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.util import APlot
from admit.util import stats
from admit.util.AdmitLogging import AdmitLogging as logging

import numpy as np
import numpy.ma as ma
try:
    import scipy
    import scipy.signal
except:
    print "WARNING: No scipy; PVCorr task cannot function."
try:
    import casa
except:
    print "WARNING: No CASA; PVCorr task cannot function."

#
# Some discussion/code on https://github.com/keflavich/image_registration
# about sub-pixel registration, although we probably don't need this 
# accuracy in PVCorr.

class PVCorr_AT(AT):
    """PV correllation in a PVSlice map.

       PVCorr_AT computes a cross-correlation of a feature in a PVSlice with the 
       whole PVSlice, looking for repeated patterns to detect spectral lines. Much
       like the output from CubeStats_AT and CubeSpectrum_AT, this table can then be
       given to LineID_AT to attempt a line identification.

       See also :ref:`PVCorr-AT-Design` for the design document.

       **Keywords**

          **numsigma**: float 
            Minimum intensity, in terms of sigma, above which a selected portion
            of the spectrum will be used for cross-correlation.
            Default: 3.0.

          **range**: integer list
            If given, it has to be a list with 2 channel numbers, the first and last channel
            (0-based channels) of the range which to use for the cross-correlation.
            Default: [].

          **nchan**: integer
            The number of channels (in case range= was not used) that defines the line.
            The line is centers on the strongest point in the input PV-map.
            If 0 is given, it will watershed down from the strongest line.
            Default: 0.

       **Input BDPs**

          **PVSlice_BDP**: count: 1
            Input PV slice, normally from a `PVSlice_AT <PVSlice_AT.html>`_.

          **CubeStats_BDP**: count: 1
            Input cube statistics from which the RMS is taken, received from a
            `CubeStats_AT <CubeStats_AT.html>`_.

       **Output BDPs**

          **PVCorr_BDP**: count: 1
            Output table.
       

    """

    def __init__(self,**keyval):
        keys = {"numsigma" : 3.0,    # N-sigma
                "range"    : [],     # optional channel range
                "nchan"    : 0,      # number of channels around the channel where the peak is
               }
        AT.__init__(self,keys,keyval)
        self._version = "1.1.0"
        self.set_bdp_in([(Image_BDP,1,bt.REQUIRED),
                         # @todo optional 2nd PVSlice can be used to draw the template from
                         (CubeStats_BDP,1,bt.REQUIRED)])
        self.set_bdp_out([(PVCorr_BDP,1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

           PVCorr_AT adds the following to ADMIT summary:

           .. table::
              :class: borderless

              +----------+----------+-----------------------------------+
              |   Key    | type     |    Description                    |
              +==========+==========+===================================+
              | pvcorr   | list     |   correlation diagram             |
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
        dt = utils.Dtime("PVCorr")
        self._summary = {}

        numsigma = self.getkey("numsigma")
        mode = 1                                            # PV corr mode (1,2,3)
        normalize = True
        # normalize = False

        b1 = self._bdp_in[0]                                # PVSlice_BDP
        fin = b1.getimagefile(bt.CASA)                      # CASA image
        data = casautil.getdata_raw(self.dir(fin))          # grab the data as a numpy array
        self.myplot = APlot(ptype=self._plot_type,pmode=self._plot_mode,abspath=self.dir())
        #print 'DATA[0,0]:',data[0,0]
        #print 'pv shape: ',data.shape
        npos = data.shape[0]
        nvel = data.shape[1]
        dt.tag("getdata")

        b2 = self._bdp_in[1]                                # CubeStats_BDP
        sigma = b2.sigma                                    # global sigma in the cube
        cutoff = numsigma * sigma
        freq =  b2.table.getColumnByName("frequency")

        chans = self.getkey("range")                        # range of channels, if used
        if len(chans) > 0:
            if len(chans) != 2:
                logging.fatal("range=%s" % chans)
                raise Exception,"range= needs two values, left and right (inclusive) channel"
            ch0 = chans[0]
            ch1 = chans[1]
        else:
            nchan = self.getkey("nchan")
            imstat0 = casa.imstat(self.dir(fin))         # @todo   can use data[] now
            xmaxpos = imstat0['maxpos'][0]
            ymaxpos = imstat0['maxpos'][1]
            logging.info("MAXPOS-VEL %s %g" % (str(imstat0['maxpos']),imstat0['max'][0]))
            if nchan > 0:
                # expand around it, later ch0,ch1 will be checked for running off the edge
                ch0 = ymaxpos - nchan/2
                ch1 = ymaxpos + nchan/2
            else:
                # watershed down to find ch0 and ch1 ?
                # this doesn't work well in crowded areas
                ch0 = ymaxpos
                ch1 = ymaxpos
                spmax = data.max(axis=0)
                k = spmax.argmax()
                n = len(spmax)
                logging.debug('spmax %s %d %g' % (str(spmax.shape),k,spmax[k]))
                # find lower cutoff
                for i in range(n):
                    ch0 = ymaxpos - i
                    if ch0<0: break
                    if spmax[ch0] < cutoff: break
                ch0 = ch0 + 1
                # find higher cutoff
                for i in range(n):
                    ch1 = ymaxpos + i
                    if ch1==n: break
                    if spmax[ch1] < cutoff: break
                ch1 = ch1 - 1
            dt.tag("imstat")

        
        bdp_name = self.mkext(fin,"pvc")                    # output PVCorr_BDP
        b3 = PVCorr_BDP(bdp_name)
        self.addoutput(b3)

        if ch0<0 or ch1>=nvel:
            # this probably only happens to small cubes (problematic for PVCorr)
            # or when the strongest line is really close to the edge of the band
            # (which is probably ok)
            if ch0<0 and ch1>=nvel:
                logging.warning("Serious issues with the size of this cube")
            if ch0<0: 
                logging.warning("Resetting ch0 edge to 0")
                ch0=0
            if ch1>=nvel: 
                ch1=nvel-1
                logging.warning("Resetting ch1 edge to the maximum")

        if ch0 > ch1:
            logging.warning("Sanity swapping ch0,1 due to likely noisy data")
            ch0,ch1 = ch1,ch0

        if mode == 1:
            out,rms = mode1(data, ch0, ch1, cutoff, normalize)
            corr = out
        elif mode == 2:
            out,rms = mode2(data, ch0, ch1, cutoff)             # slower 2D version
            corr = out[npos/2,:]                                # center cut, but could also try feature detection
        elif mode == 3:
            out,rms = self.mode3(data, ch0, ch1, cutoff)        # Doug's faster 2D version
            # get the peak of each column
            corr = np.amax(out,axis=0)
        # print "PVCORR SHAPE ",corr.shape," mode", mode
        if len(corr) > 0:
            # print "SHAPE out:",out.shape,corr.shape,npos/2
            ch  = range(len(corr))
            if len(corr) != len(freq):
                logging.fatal("ch (%d) and freq (%d) do not have same size" % (len(corr),len(freq)))
                raise Exception,"ch and freq do not have same dimension"
            dt.tag("mode")
            labels = ["channel",   "frequency",  "pvcorr"]
            units  = ["number",    "GHz",        "N/A"]
            data   = (ch,          freq,         corr)
            table = Table(columns=labels,units=units,data=np.column_stack(data))
        else:
            # still construct a table, but with no rows
            labels = ["channel",   "frequency",  "pvcorr"]
            units  = ["number",    "GHz",        "N/A"]
            table = Table(columns=labels,units=units)
        b3.setkey("table",table)
        b3.setkey("sigma",float(rms))
        dt.tag("table")
        if len(corr) > 0:
            table.exportTable(self.dir("testPVCorr.tab"),cols=['frequency','pvcorr'])
            test_single(ch,freq,corr)

            logging.regression("PVC: %f %f" % (corr.min(),corr.max()))

            title = 'PVCorr mode=%d [%d,%d] %g' % (mode,ch0,ch1,cutoff)
            x = ch
            xlab = 'Channel'
            y = [corr]
            ylab = 'PV Correlation'
            p1 = "%s_%d" % (bdp_name,0)
            segp = []
            segp.append( [0,len(ch),0.0,0.0] )
            segp.append( [0,len(ch),3.0*rms, 3.0*rms] )
            # @todo:   in principle we know with given noise and  size of box, what the sigma in pvcorr should be
            self.myplot.plotter(x,y,title,figname=p1,xlab=xlab,ylab=ylab,segments=segp, thumbnail=True)

            #out1 = np.rot90 (data.reshape((nvel,npos)) )
            if mode > 1:
                self.myplot.map1(data=out,title="testing PVCorr_AT:  mode%d"%mode,figname='testPVCorr', thumbnail=True)

            taskargs = "numsigma=%.1f range=[%d,%d]" % (numsigma,ch0,ch1)
            caption = "Position-velocity correlation plot"
            thumbname = self.myplot.getThumbnail(figno=self.myplot.figno,relative=True)
            figname   = self.myplot.getFigure(figno=self.myplot.figno,relative=True)
            image = Image(images={bt.PNG: figname}, thumbnail=thumbname, thumbnailtype=bt.PNG,
                description=caption)
            b3.image.addimage(image, "pvcorr")

            self._summary["pvcorr"] = SummaryEntry([figname,thumbname,caption,fin],"PVCorr_AT",self.id(True),taskargs)
        else:
            self._summary["pvcorr"] = None
            logging.warning("No summary")
            logging.regression("PVC: -1")

        dt.tag("done")
        dt.end()

    def mode3(self, data, v0, v1, dmin=0.0):
        """ v0..v1 (both inclusive) are channel selections
            threshold on dmin
            @todo the frequency axis is not properly calibrated here
            @todo a full 2D is slow, we only need the 1D version
        """
        print "PVCorr mode3: v0,1=",v0,v1
        smin = data.min()
        #s = data[v0:v1+1,:]
        s = data[:,v0:v1+1]
        if dmin==0.0:
            logging.warning("Using all data in crosscorr")
            f = s
        else:
            f = np.where(s>dmin,s,0)
        # find out where the zeros are
        temp = np.amax(f,axis=1)
        nz = np.nonzero(temp)
        # trim the kernel in the y direction, removing rows that are all 0.0
        f = f[nz[0][0]:nz[0][-1],:]
        f0 = np.where(s>smin,1,0)
        f1 = np.where(s>dmin,1,0)
        fmax = f.max()
        print "PVCorr mode3:",f1.sum(),'/',f0.sum(),'min/max',smin,fmax
        out =  scipy.signal.correlate2d(data,f,mode='same')
        self.myplot.map1(data=f,title="PVCorr 2D Kernel",figname='PVCorrKernel', thumbnail=True)

        print 'PVCorr min/max:',out.min(),out.max()
        n1,m1,s1,n2,m2,s2 = stats.mystats(out.flatten())
        print "PVCorr stats", n1,m1,s1,n2,m2,s2
        rms_est = s2/np.sqrt(f1.sum())
        return out,rms_est

def test_single(x1,x2,y,cutoff=None):
    """ test as if there is only one line via a simple moment analysis
    """
    ymax = y.max()
    if cutoff == None:
        cutoff = 0.10 * ymax
    ym = ma.masked_less(y,cutoff)
    y1 = ym * x1
    y2 = ym * x2
    logging.info("Average: %d %d %d %d" % (ym.count(), y1.count(), y2.count(), len(y)))
    logging.info("Average intensity weighted channel: %g %g %g %g" % (y1.sum()/ym.sum(),y2.sum()/ym.sum(),cutoff,ymax))

def mode1(data,v0,v1, dmin=0.0,  normalize=False):
    """ faster 1D version of mode2
        This works by forcing mode='valid' and making the X (position)
        dimension of the template the same as the PV diagram.  We then
        pad the ends of the PV with zero's. Introduces some complexity
        how to return the correct shape
        v0..v1 (both inclusive) are channel selections
        threshold on dmin
        @todo the frequency axis may not be properly calibrated here

        @todo plot the template for debug, like in mode3
    """
    logging.info("PVCorr mode1: v0,1= %d %d  dmin= %g  normalize=%s " % (v0,v0,dmin,str(normalize)))
    smin = data.min()
    nx = data.shape[0]
    ny = data.shape[1]
    nv = v1-v0+1
    pad = np.zeros(nx*nv).reshape(nx,nv)                # ValueError: negative dimensions are not allowed (EGNoG)
    pdata = np.concatenate((pad,data,pad),axis=1)
    s = data[:,v0:v1+1]                                 # the stencil where the line is
    if dmin==0.0:
        logging.warning("Using all data in crosscorr")
        f = s
    else:
        f = np.where(s>dmin,s,0.0)
    if normalize:
        f = np.where(f != 0.0, 1.0, 0.0)
    f0 = np.where(s>smin,1,0)
    f1 = np.where(s>dmin,1,0)
    if s.max() < dmin:
        logging.warning("Datamax=%g, no data above dmin=%g; data too noisy?" % (s.max(),dmin))
        return np.arange(0),0.0
    fmax = f.max()
    fsum = f.sum()
    ssum = s.sum()
    fssum = (f*s).sum()
    ffsum = (f*f).sum()
    logging.info("PVCorr mode1: %d/%d  min/max  %g %g   sums: %g %g %g %g" % (f1.sum(),f0.sum(),smin,fmax,fsum,ssum,ffsum,fssum))
    if normalize:
      out =  scipy.signal.correlate2d(pdata,f,mode='valid')/fssum
    else:
      out =  scipy.signal.correlate2d(pdata,f,mode='valid')/ffsum
    logging.info('PVCorr min/max: %g %g' % (out.min(),out.max()))
    n1,m1,s1,n2,m2,s2 = stats.mystats(out.flatten())
    logging.info("PVCorr stats %d %g %g  %d %g %g" % (n1,m1,s1,n2,m2,s2))
    rms_est = s2
    logging.info("RMS est: %g" % rms_est)
    # CAVEAT:
    # cutting it this way will agree with peaks in mode2,
    # but between ny=odd or even there is a half channel freq offset
    # alternatively for one of them an interpolation is needed.
    # the idea is that half channel should not influence LineID.
    corr = out[0,nv/2+1:nv/2+ny+1]
    return corr,rms_est

    
def mode2(data,v0,v1, dmin=0.0):
    """ v0..v1 (both inclusive) are channel selections
        threshold on dmin
        for odd number of channels, center line in mode2 will be same as mode1
        @todo the frequency axis is not properly calibrated here
        @todo a full 2D is slow, we only need the 1D version
    """
    print "PVCorr mode2: v0,1=",v0,v1,"dmin=",dmin
    smin = data.min()
    s = data[:,v0:v1+1]
    if dmin==0.0:
        logging.warning("Using all data in crosscorr")
        f = s
    else:
        f = np.where(s>dmin,s,0)
    print "PVCorr dmin:",dmin
    f0 = np.where(s>smin,1,0)
    f1 = np.where(s>dmin,1,0)
    fmax = f.max()
    ffsum = (f*f).sum()
    print "PVCorr mode2:",f1.sum(),'/',f0.sum(),'min/max',smin,fmax
    out =  scipy.signal.correlate2d(data,f,mode='same')/ffsum
    print 'PVCorr min/max:',out.min(),out.max()
    n1,m1,s1,n2,m2,s2 = stats.mystats(out.flatten())
    print "PVCorr stats", n1,m1,s1,n2,m2,s2
    rms_est = s2/np.sqrt(f1.sum())
    return out,rms_est
