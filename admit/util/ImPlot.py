#!/usr/bin/env casarun
""" .. _ImPlot-api:

    **ImPlot** --- Simple image plotter.
    ------------------------------------

    This module defines the ImPlot class.
"""
from AbstractPlot import AbstractPlot
import os
import PlotControl
import casautil

class ImPlot(AbstractPlot):
    """
    Basic ADMIT image plotter that uses casa calls to create figures.

    - uses CASA imview
    - plot modes and plot types as in util.PlotControl 
    - keeps track of figure number
    - make thumbnails if requested

    See Also
    --------
    admit.util.AbstractPlot
    admit.util.casautil
    """
    
    def __init__(self,pmode=None,ptype=None,figno=None,abspath=""):
        # @todo figno given here really must be figno-1 since every
        # method increments it.  probably should start static at 1 and
        # increment AFTER plt is made.
        AbstractPlot.__init__(self,pmode,ptype,figno,abspath)

    def plotter(self, figname, rasterfile=None, contourfile=None,
                colorwedge=False, thumbnail=True, zoom=1):
       """Image plotter

          Parameters
          ----------
          figname : str
              Root of output file name.  An extension matching the plot
              type will be appended. For instance, for, figname='fig'
              and plottype=PlotControl.PNG, the output file is 'fig.png'

          rasterfile : str
            Image file to use as raster map.  Optional if contourfile is given.

          contourfile : str
            Image file to use as contour map. Contours will be overlaid on
            rasterfile if both are given.  Optional if rasterfile is given.

          colorwedge  : boolean
            True - show color wedge, False - don't show color wedge

          thumbnail : boolean 
             If True, create a thumbnail when creating an output figure.
             Thumbnails will have '_thumb' appended for file root.
             For instance, if the output file is 'fig.png', the thumbnail
             will be 'fig_thumb.png'.  Note: only PNG format is currently
             supported (matplotlib restriction, Exception raised otherwise).

          zoom : int
            Image zoom ratio.

          Returns
          -------
          None
       """

       self.__class__.figno = self.__class__.figno + 1
       if self._abspath != "":
           figname    = self._abspath + figname
           if rasterfile:  rasterfile  = self._abspath + rasterfile
           if contourfile: contourfile = self._abspath + contourfile

       figname = figname + PlotControl.mkext(self._plot_type,True)
       self._figurefiles[self.__class__.figno] = figname

       if self._plot_mode != PlotControl.NOPLOT:
           #print "%s figno=%d figname=%s rasterfile=%s" % (self.__class__.__name__,self.__class__.figno,figname,rasterfile)
           casautil.implot(rasterfile=rasterfile,figname=figname,contourfile=contourfile,plottype=self._plot_type,plotmode=self._plot_mode,colorwedge=colorwedge,zoom=zoom)

           if thumbnail: self.makeThumbnail(self.__class__.figno)


if __name__ == "__main__":

    import os.path
    import sys
    import PlotControl
    
    rasterfile="implot_test.fits"

    abspath = os.getenv("ADMIT")+os.sep+"data"
    # nb interactive won't show with casarun because --nogui!
    # use casapy -c 
    a1 = ImPlot(pmode=PlotControl.INTERACTIVE,ptype=PlotControl.PNG,figno=10,abspath=abspath)
    
    if os.path.exists(a1._abspath+rasterfile):
        a1.plotter(figname="figone",rasterfile=rasterfile,contourfile="implot_test.fits",thumbnail=True)
        a1.show()
    else:
        print "## Exception: Could not find file: %s" % a1._abspath+rasterfile

