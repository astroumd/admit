""" .. _AbstractPlot-base-api:

    **AbstractPlot** --- Plotting base class.
    -----------------------------------------

    This module defines the base class for ADMIT plotters (APlot, ImPlot):

    - keeps track of figure numbers
    - plotmodes as in util.PlotControl 
    - thumbnail generation built-in
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import PlotControl
import utils
import sys

class AbstractPlot(object):
    """
    Base class of ADMIT plotters.

    Attributes
    ----------

    figno : int
      Figure number (1 and up). This is a static class variable.

    _figurefiles : dict
      Dictionary of figure file names with key equal to figno.

    _thumbnailfiles : dict
      Dictionary of thumbnail file names with key equal to figno.

    _plot_mode : int
      Plot mode, one of util.PlotControl plot mode (e.g.,
      PlotControl.INTERACTIVE). Default: PlotControl.NOPLOT .

    _plot_type : int
      Plotting format, one of util.PlotControl plot type (e.g.,
      PlotControl.PNG). Default: PlotControl.NONE.

    _abspath : str
      Fully-qualified path where images will be written.  Default: empty string,      meaning write in current working directory or the path will be given
      in the figname argument to plot methods.

    """
    # Figure number is a static member
    figno = 0
    
    def __init__(self,pmode=None,ptype=None,figno=None,abspath=""):

        self._plot_mode = PlotControl.NOPLOT
        self._plot_type = PlotControl.NONE

        if pmode!=None: self._plot_mode = pmode
        if ptype!=None: self._plot_type= ptype
        if figno!=None: self.__class__.figno = figno

        self._abspath      = abspath
        if len(self._abspath) > 0:
            if self._abspath[len(self._abspath)-1] != os.sep:
                 self._abspath = self._abspath + os.sep

        self._figurefiles   = {}
        self._thumbnailfiles = {}
#        self.backend("Agg")
#        self.backend("TkAgg")

    def show(self):
        """show internals for debugging 
        """
        print "%s:  plotmode=%s plottype=%s current figno=%d" % ( self.__class__.__name__, PlotControl.plotmode(self._plot_mode), PlotControl.plottype(self._plot_type), self.figno)
        print "abspath = %s " % self._abspath
        print "Figure files created by this Aplot: "    + str(self._figurefiles)
        print "Thumbnail files created by this Aplot: " + str(self._thumbnailfiles)

    @property
    def plotmode(self):
        """Get the plotting mode

           Returns
           -------
           int 
               Plotting mode. 

           See Also
           --------
           util.PlotControl plot modes.
        """
        return self._plot_mode

    @plotmode.setter
    def plotmode(self,plotmode):
        """Set the plot mode

           Parameters
           ----------
           plotmode : int
               Plotting mode. 

           See Also
           --------
           util.PlotControl plot modes.
        """
        self._plotmode = plotmode

    @property
    def plottype(self):
        """Get the plot type

           Returns
           ----------
           int
               Plot format type. 

           See Also
           --------
           util.PlotControl plot types.
        """
        return self._plot_type

    @plottype.setter
    def plottype(self,plottype):
        """Set the plot type

           Parameters
           ----------
           plottype : int  
               Plot format type. 

           See Also
           --------
           util.PlotControl plot types.
        """
        self._plot_type = plottype

    def getThumbnail(self,figno,relative):
        """Get the name of the thumbnail file for given figure number

           Parameters
           ----------
           figno : int  
               Figure number to look up

           relative : boolean
               Whether to return with relative path or absolute path.  If True,
               plot _abspath will be removed from retured string.

           Returns
           -------
           str
              Thumbnail file name
        """
        try:
            if relative:
                return self._thumbnailfiles[figno].replace(self._abspath,"")
            else:
                return self._thumbnailfiles[figno]
        except KeyError:
            raise Exception, "Thumbnail for figure %d was not created by this %s ." % (figno,self.__class__.__name__)

    def getFigure(self,figno,relative):
        """Get the name of the figure file for given figure number

           Parameters
           ----------
           figno : int  
               Figure number to look up

           relative : boolean
               Whether to return with relative path or absolute path.  If True,
               plot _abspath will be removed from retured string.

           Returns
           -------
           str
               Figure file name
        """
        try:
            if relative:
                return self._figurefiles[figno].replace(self._abspath,"")
            else:
                return self._figurefiles[figno]
        except KeyError:
            raise Exception, "Figure %d was not created by this %s." % (figno, self.__class__.__name__ )

    def figure(self,figno=1):
        """set the figure number. 
        This should normally not be needed, unless you want to alternate drawing in different figures.
        This option has not been tested at all.
        """
        self.__class__.figno = figno-1

    def makeThumbnail(self,figno=None, scale=0.33, fig=None):
        """Create a thumbnail for a given figure number. The output
           file will be root of input plus '_thumb' plus plot type extension.
           For instance, if the input were "myimage.png", the output
           would be "myimage_thumb.png".   Note: only PNG format is currently
           supported (matplotlib restriction, Exception raised otherwise).

           Parameters
           ----------
           figno: int
               figure number for a plot that has been created by this Plot 
               instance.  

           scale: float
               multiplier to scale input image, e.g. for 50% scaling, 
               scale = 0.5.  Default: 0.33

           fig : figure, optional
               Populated matplotlib.figure.Figure instance
               (if `None`, input plot type must be PNG).

           Returns
           ----------
           None

        """
        if figno:
           fno = figno
        else:
           # not safe if static member has been changed between
           # method invocation and here!
           fno = self.__class__.figno

        pngfile = self._figurefiles[fno]
        filename, file_extension = os.path.splitext(pngfile)
        if self._plot_type != PlotControl.PNG:
           if fig is None:
             raise Exception, "Thumbnails for plot types other than PNG require specifying fig="
           else:
             pngfile = filename + ".png"
             fig.savefig(pngfile, format='png', dpi=fig.get_dpi())

        try:
            # strip the file extension so that the base name can be appended to
            # make sure the file to be processed exists and is readable
            if os.path.isfile(pngfile) and os.access(pngfile, os.R_OK):
                outfile = filename + "_thumb.png"
                # generate the thumbnail
                fig = matplotlib.image.thumbnail(pngfile, outfile, scale)
            else:
                raise Exception("File not found or not readable: %s " % file)
            # set the class variable to the name
            self._thumbnailfiles[fno] = outfile
        except KeyError:
            raise Exception("Figure %d was not created by this %s." % (fno, self.__class__.__name__))

    """Set a particular backend for matplotlib

       Parameters
       ----------
       thebackend: str
           backend string, e.g. 'agg'
   
       Returns
       ----------
       None
    """
    def backend(self,thebackend):
        #try:
        global plt
        print "started with %s" % plt.get_backend()
        plt.switch_backend(thebackend)
    #except Exception, e:
        print "changing matplotlib backend the hard way"
        # See http://stackoverflow.com/questions/3285193/how-to-switch-backends-in-matplotlib-python

        modules = []
        for module in sys.modules:
            if module.startswith('matplotlib'):
                modules.append(module)

        for module in modules:
            sys.modules.pop(module)

        import matplotlib
        matplotlib.use(thebackend)
        import matplotlib.pyplot as plt

        print "ended with %s" % plt.get_backend()

