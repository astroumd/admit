#! /usr/bin/env python
"""
  **APlot** --- Standardized plot generator.
  ------------------------------------------

  This module defines the APlot class.
"""

from AbstractPlot import AbstractPlot
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from   matplotlib.widgets import RadioButtons
import PlotControl
import numpy.ma as ma
import utils
from admit.util.AdmitLogging import AdmitLogging as logging
# import mpld3      # needs matplotlib 1.3

class APlot(AbstractPlot):
    """
    Basic ADMIT plotter that uses matplotlib calls to create figures.

    - simple parser of extra layout commands on top of general style
    - plotter, scatter or histogram

    line x0 y0 x1 y1 ...
    point x0 y0 ...

    See Also
    --------
    admit.util.AbstractPlot
    """

    def __init__(self,pmode=None,ptype=None,figno=None,abspath=""):
        # @todo figno given here really must be figno-1 since every
        # method increments it.  probably should start static at 1 and
        # increment AFTER plt is made.
        self.version = "28-mar-2016"
        AbstractPlot.__init__(self,pmode,ptype,figno,abspath)

    def parse(self,lines):
        """APlot parser to pass along some matplotlib commands
           lines : list

               A list of matplotlib commands to be added to the current figure.
               Currently supported:

               grid
                  display a grid on the plot

               axis equal
                  ensure axis scales to be the same, if you want squares and
                  circles to come out as such.
        """
        for line in lines:
            if line=='grid':
                plt.grid()
            elif line=='axis equal':
                plt.axis('equal')
            else:
                print "Skipping unknown APlot command: %s" % line

    #@todo how is this actually used?  a plot instance must know when
    # to call final() ?!?
    def final(self):
        """final signoff from APlot

           This would be needed for plotmode=PlotControl.SHOW_AT_END, but
           this does not seem to work (anymore)
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        if self._plot_mode == PlotControl.SHOW_AT_END:
            plt.ioff()
            plt.show()

    def scatter(self,x,y,title=None,figname=None,xlab=None,ylab=None,color=None,size=None,cmds=None,thumbnail=True, xrange=None, yrange=None):
        """Scatter plot of multiple columns against one column

           Parameters
           ----------
           x : numpy array
               X axis (abscissa) values

           y : numpy array
               Y axis (ordinate) values

           title : str
               Title string for plot

           figname : str
               Root of output file name.  An extension matching the plot
               type will be appended. For instance, for, figname='fig'
               and plottype=PlotControl.PNG, the output file is 'fig.png'

           xlab : str
              X axis label

           ylab : str
              Y axis label

           color : str
              Color as defined in matplotlib.Axes.scatter() argument 'c'.

           size : numpy array or scalar
              Point size as defined matplotlib.Axes.scatter() argument,
              It is a size in points^2.  It is a scalar
              or an array of the same length as x and y.

           cmds :
              add matplot lib commands. See parse()

           thumbnail : boolean
              If True, create a thumbnail when creating an output figure.
              Thumbnails will have '_thumb' appended for file root.
              For instance, if the output file is 'fig.jpg', the thumbnail
              will be 'fig_thumb.jpg'

           xrange : tuple
              X axis range (xmin,xmax). Default:None meaning show full range of data

           yrange: tuple
              Y axis range, (ymin,ymax). Default:None meaning show full range of data


           Returns
           -------
           None

        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        if color==None and size==None:
            ax1.scatter(x,y)
        elif color==None:
            ax1.scatter(x,y,s=size)
        elif size==None:
            ax1.scatter(x,y,c=color)
        else:
            ax1.scatter(x,y,c=color,s=size)
        if title:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        if ylab:     ax1.set_ylabel(ylab)
        if xrange != None:
            ax1.set_xlim(xrange)
        if yrange != None:
            ax1.set_ylim(yrange)
        if cmds != None:
              self.parse(cmds)
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)


        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        # mpld3.save_html(fig, "mpld3.html")

        plt.close()

    def plotter(self,x,y,title=None,figname=None,xlab=None,ylab=None,xrange=None,yrange=None,segments=None,labels=[],histo=False,thumbnail=True,x2range=None,y2range=None,x2lab=None,y2lab=None):
        """Simple plotter of multiple columns against one column, optionally in histogram style

           Parameters
           ----------
           x : numpy array
               X axis (abscissa) values

           y : list of numpy array
               Y axis (ordinate) values

           title : str
               Title string for plot

           figname : str
               Root of output file name.  An extension matching the plot
               type will be appended. For instance, for, figname='fig'
               and plottype=PlotControl.PNG, the output file is 'fig.png'

           xlab : str
              X axis label

           ylab : str
              Y axis label

           xrange : tuple
              X axis range (xmin,xmax). Default:None meaning show full range of data

           yrange: tuple
              Y axis range, (ymin,ymax). Default:None meaning show full range of data

           segments : list
              list of segment end points pairs for overlaying horizontal
              segment lines.  e.g. [[0,2],[5,6.3],[10.1,14.27]]

           labels : list
              labels for the plot traces. In general, there should be one per plot trace.

           histo : boolean
              Histogram style?  not implemented yet

           thumbnail : boolean
              If True, create a thumbnail when creating an output figure.
              Thumbnails will have '_thumb' appended for file root.
              For instance, if the output file is 'fig.jpg', the thumbnail
              will be 'fig_thumb.jpg'

           x2range: tuple
              If given and non-empty, label the upper x axis with a second
              range. Useful for, e.g. plotting frequency and velocity on
              the same plot.  Default: None, no second x axis

           y2range: tuple
              If given and non-empty, label the right y axis with a second
              range. Default: None, no second y axis

           x2lab : str
              second X axis label

           y2lab : str
              second Y axis label


           Returns
           -------
           None

        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # if filename: plt.ion()
        #plt.ion()
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        if len(labels) > 0:
            for (yi,li) in zip(y,labels):
                ax1.plot(x,yi,label=li)
            # @todo    try loc='lower center'
            # smaller font
            ax1.legend(loc='best',prop={'size':8})
        else:
            for yi in y:
                ax1.plot(x,yi)
        ylim = ax1.get_ylim()[1]/3.0
        if segments:
            for s in segments:
                #print "SEGMENTS",s
                #ax1.plot([s[0],s[1]],[s[2],s[3]])
                if len(s) == 2:
                    #print "plotting ",[s[0],s[1]],[0.01,0.01]
                    ax1.plot([s[0],s[1]],[ylim,ylim],'k-')
                else:
                    #print "plotting",[s[0],s[1]],[s[2],s[3]]
                    ax1.plot([s[0],s[1]],[s[2],s[3]],'k-')
        if title and not x2range:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        if ylab:     ax1.set_ylabel(ylab)
        if xrange:   ax1.set_xlim(xrange)
        if yrange:   ax1.set_ylim(yrange)
        if x2range:  
           ax2 = ax1.twiny()
           ax2.set_xlim(x2range)
           if x2lab: ax2.set_xlabel(x2lab)
           # if 2nd x-axis specified, then title will be
           # placed interior to plot
           if title: ax1.text(.5,.92,title, horizontalalignment='center', transform=ax1.transAxes)
        if y2range:  
           ax3 = ax1.twinx()
           ax3.set_ylim(y2range)
           if y2lab: ax3.set_ylabel(y2lab)
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()

    def multiplotter(self,x,y,title=None,figname=None,xlab=None,ylab=None,xrange=None,yrange=None,labels=[],thumbnail=True,x2range=None,y2range=None,x2lab=None,y2lab=None):
        """Plotter of multiple x against multiple y as traces on same plot. 

           Parameters
           ----------
           x : list of numpy array
               X axis (abscissa) values

           y : list of numpy array
               Y axis (ordinate) values

           title : str
               Title string for plot

           figname : str
               Root of output file name.  An extension matching the plot
               type will be appended. For instance, for, figname='fig'
               and plottype=PlotControl.PNG, the output file is 'fig.png'

           xlab : str
              X axis label

           ylab : str
              Y axis label

           xrange : tuple
              X axis range (xmin,xmax). Default:None meaning show full range of data

           yrange: tuple
              Y axis range, (ymin,ymax). Default:None meaning show full range of data

           labels : list
              labels for the plot traces. In general, there should be one per plot trace.

           thumbnail : boolean
              If True, create a thumbnail when creating an output figure.
              Thumbnails will have '_thumb' appended for file root.
              For instance, if the output file is 'fig.jpg', the thumbnail
              will be 'fig_thumb.jpg'

           x2range: tuple
              If given and non-empty, label the upper x axis with a second
              range. Useful for, e.g. plotting frequency and velocity on
              the same plot.  Default: None, no second x axis

           y2range: tuple
              If given and non-empty, label the right y axis with a second
              range. Default: None, no second y axis

           x2lab : str
              second X axis label

           y2lab : str
              second Y axis label

           Returns
           -------
           None

        """
        if self._plot_mode == PlotControl.NOPLOT:
            return

        if len(x) != len(y):
           raise Exception("Input x and y arrays are not the same length [%d,%d]"%(len(x),len(y)))

        # if filename: plt.ion()
        #plt.ion()
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        if len(labels) > 0:
            for (xi,yi,li) in zip(x,y,labels):
                ax1.plot(xi,yi,label=li)
            # @todo    try loc='lower center'
            # smaller font
            ax1.legend(loc='best',prop={'size':8})
        else:
            for i in len(y):
                ax1.plot(x[i],y[i])
        ylim = ax1.get_ylim()[1]/3.0
        if title and not x2range:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        if ylab:     ax1.set_ylabel(ylab)
        if xrange:   ax1.set_xlim(xrange)
        if yrange:   ax1.set_ylim(yrange)
        if x2range:  
           ax2 = ax1.twiny()
           ax2.set_xlim(x2range)
           if x2lab: ax2.set_xlabel(x2lab)
           # if 2nd x-axis specified, then title will be
           # placed interior to plot
           if title: ax1.text(.5,.92,title, horizontalalignment='center', transform=ax1.transAxes)
        if y2range:  
           ax3 = ax1.twinx()
           ax3.set_ylim(y2range)
           if y2lab: ax3.set_ylabel(y2lab)


        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()

    def segplotter(self,x,y,title="",figname="",xlab="",ylab="",segments=[],cutoff=0.0, continuum=None, thumbnail=True):
        """Plotter for spectral line segments. Based on plotter, but extended to create a legend.

           Parameters
           ----------
           x : numpy array
               X axis (abscissa) values

           y : numpy array
               Y axis (ordinate) values

           title : str
               Title string for plot

           figname : str
               Root of output file name.  An extension matching the plot
               type will be appended. For instance, for, figname='fig'
               and plottype=PlotControl.PNG, the output file is 'fig.png'

           xlab : str
              X axis label

           ylab : str
              Y axis label

           segments : list
              list of segment end points pairs for overlaying horizontal segment lines.
              e.g. [[0,2],[5,6.3],[10.1,14.27]]

           cutoff : float or list of floats
              y-axis value(s) at which to draw the cutoff-level indicator (horizontal line)

           continuum : float or list of floats
              y-axis value(s) at which to draw the continuum "Mean/Baseline" indicator (horizontal line)

           thumbnail : boolean
              If True, create a thumbnail when creating an output figure.
              Thumbnails will have '_thumb' appended for file root.
              For instance, if the output file is 'fig.jpg', the thumbnail
              will be 'fig_thumb.jpg'


           Returns
           -------
           None
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        # reverse the numpy arrays
        x = x[::-1].copy()
        y = y[::-1].copy()
        if continuum is not None:
            c = continuum[::-1].copy()
        fig = plt.figure(APlot.figno, figsize=(18,12), dpi=80)
        ax1 = fig.add_subplot(1,1,1)
        ax1.set_xlim([ma.min(x) - 0.0001,ma.max(x) + 0.0001])
        ax1.plot(x,y,'k-')
        # @todo  temporary: turn on red plusses for debug
        ax1.plot(x,y,'r+')
        #ax1.plot([x[0],x[-1]],[0.0,0.0],'b-')
        first = True
        neg = False
        if np.max(y) < 0.:
            neg = True
        if isinstance(cutoff, list) or isinstance(cutoff, np.ndarray) or isinstance(cutoff, ma.masked_array):
            ax1.plot(x,cutoff[::-1].copy(),'g-',label='Cutoff level')
        else:
            ax1.plot([x[0],x[-1]],[cutoff,cutoff],'g-',label='Cutoff level')
        ylim = ax1.get_ylim()[1]/3.0
        if neg:
            ylim = ax1.get_ylim()[0]/2.
        yseg = ylim/15.0
        ncol = 0
        if continuum is not None:
            ax1.plot(x, c, 'b-', label='Mean/Baseline')
            ncol = 1
        else:
            ax1.plot([x[0],x[-1]],[0.0,0.0],'b-')

        if segments:
            for s in segments:
                if first:
                    ax1.plot([s[0],s[1]],[ylim,ylim],'r-',label="Potential Line")
                    first = False
                else:
                    ax1.plot([s[0],s[1]],[ylim,ylim],'r-')
                ax1.plot([s[0],s[0]],[ylim-yseg,ylim+yseg],'r-')
                ax1.plot([s[1],s[1]],[ylim-yseg,ylim+yseg],'r-')

        ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))

        ax1.set_title(title)
        ax1.set_xlabel(xlab)
        ax1.set_ylabel(ylab)
        ax1.legend(loc="lower center",ncol=2+ncol)
        if figname != "":
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()


    def histogram(self,columns,title=None,figname=None,xlab=None,xrange=None,ylab="#",bins=80,thumbnail=True):
        """Simple histogram of one or more columns

           Parameters
           ----------
           columns : numpy array or list of numpy arrays
               X axis (abscissa) values

           title : str
               Title string for plot

           figname : str
               Root of output file name.  An extension matching the plot
               type will be appended. For instance, for, figname='fig'
               and plottype=PlotControl.PNG, the output file is 'fig.png'

           xlab : str
              X axis label

           xrange: tuple
              X axis range, (xmin,xmax)

           ylab : str
              Y axis label

           bins: int
              Number of histogram bins. Default:80

           thumbnail : boolean
              If True, create a thumbnail when creating an output figure.
              Thumbnails will have '_thumb' appended for file root.
              For instance, if the output file is 'fig.jpg', the thumbnail
              will be 'fig_thumb.jpg'

           Returns
           -------
           None
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # if filename: plt.ion()
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        if isinstance(columns,list):
            for xi in columns:
                ax1.hist(xi,bins=bins,range=xrange)
        # handle the case of just putting in a single nparray
        # (old behavior of mkhisto.)
        else:
            if len(columns) == 0:
                # PJT debug: handle if no data, fake it
                ax1.hist(np.array([0,1,2,3]),bins=bins)
            else:
                ax1.hist(columns,bins=bins,range=xrange)

        if title:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        ax1.set_ylabel(ylab)

        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()

    def hisplot(self,x,title=None,figname=None,xlab=None,range=None,bins=80,gauss=None,thumbnail=True):
        """simple histogram of one column with optional overlayed gaussfit
           This plot could be merged with histogram()

           Returns
           -------
           None
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # if filename: plt.ion()
        # better example: http://matplotlib.org/examples/statistics/histogram_demo_features.html
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        if range == None:
            h=ax1.hist(x,bins=bins,range=range)

        if title:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        ax1.set_ylabel("#")
        if gauss != None:                                  # overplot a gaussian
            if len(gauss) == 3:
                m = gauss[0]    # mean
                s = gauss[1]    # std
                a = gauss[2]    # amp
            elif len(gauss) == 2:
                m = gauss[0]    # mean
                s = gauss[1]    # std
                a = max(h[0])   # match peak value in histogram
            else:
                print "bad gauss estimator"
                s = -1.0
            #print "PJT: GaussPlot(%g,%g,%g)" % (m,s,a)
            d = s/10.0
            if d > 0.0:
                if range == None:
                    xmin = x.min()
                    xmax = x.max()
                else:
                    xmin = range[0]
                    xmax = range[1]
                #print "PJT: GaussRange(%g,%g,%g)" % (xmin,xmax,d)
                nx = int((xmax-xmin)/d)
                if nx > 0 and nx < 10000:
                    # don't plot the gauss if it's too narrow 
                    gx = np.arange(xmin,xmax,d)
                    arg = (gx-m)/s
                    gy = a * np.exp(-0.5*arg*arg)
                    ax1.plot(gx,gy)
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()

    def map1(self,data,title=None,figname=None,xlab=None,ylab=None,range=None,
             contours=None,cmap='hot',segments=None,circles=None,
             thumbnail=True,zoom=1,star=None):
        """
        display map; horrible hack, the caller should call np.flipud(np.rot90()) since
        casa and numpy do not have their axes in the same order.
        We cannot call casa here, since APlot needs to stay casa agnostic.
        To be resolved.
        
        data:    a classic numpy array, i.e. data[ny][nx] where we want data[0][0]
                 in the lower left corner
        
        segments    [x0,x1,y0,y1]
        star        [x,y]
        
        See also casa.viewer() calls in e.g. Moment_AT
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)

        # Zoom calculation.  (n= X direction; m= Y direction)
        # @todo   for zoom>1 star and circles not plotted right
        m, n = data.shape
        m2 = m/2
        n2 = n/2
        m0 = m2-m2/zoom    # Y direction
        m1 = m2+m2/zoom
        n0 = n2-n2/zoom    # X direction
        n1 = n2+n2/zoom
        #logging.info("type(data) %s m,n,m0,n0,m1,n1 %g %g %g %g %g %g" % (type(data),m,n,m0,n0,m1,n1))

        if segments:
            for s in segments:
                ax1.plot([s[0]-n0,s[1]-n0],[s[2]-m0,s[3]-m0],c='skyblue')
                # ax1.plot([s[0],s[1]],[s[2],s[3]],c='skyblue')                
        if star:
                ax1.plot(star[0],star[1],'*',c='white')
        if circles:
            # @todo awkward, these are closes circles, we want open
            for c in circles:
                circ = plt.Circle((c[0]-m0,c[1]-n0),radius=c[2], color='green')
                ax1.add_patch(circ)
                # plt.plot([c[0]], [c[1]], 'g.', markersize=c[2])
        if title:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        if ylab:     ax1.set_ylabel(ylab)

        ax1.tick_params(axis='both',color='white',width=1)
#   Note this (inadvertently) can change the axis order if m0>m1 or n0>n1!
        zoom = data[m0:m1,n0:n1]
#        logging.info("data[0,0] %g data[m1,n1] %g zoom[0,0] %g zoom[m1,n1] %g" % (data[0,0],data[m1-1,n1-1],zoom[0,0],zoom[m1-1,n1-1]))
#        print("Zoom==data? %s " % np.array_equal(zoom,data) )
#        zoom = data
        if range == None:
            alplot = ax1.imshow(zoom, origin='lower')
        elif len(range) == 1:
            alplot = ax1.imshow(zoom, origin='lower', vmin = range[0])
        elif len(range) == 2:
            alplot = ax1.imshow(zoom, origin='lower', vmin = range[0], vmax = range[1])
        alplot.set_cmap(cmap)
        if contours != None:
            ax1.contour(zoom, contours, colors='g')
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()

    def summaryspec(self, stat, spec, pvc, figname, lines=[], thumbnail=True, force=[]):
        """ Method to plot a summary of all spectra with overlayed id's. All spectra
            are in S/N units.

            Parameters
            ----------
            stat : list
                List of Spectrum class holding the CubeStats based spectrum

            spec : list
                List of Spectrum classes, each holding the CubeSpectrum based
                spectrum

            pvc : Spectrum instance
                Instance of Spectrum class holding the PVCorr based spectrum

            figname : str
                The name of the output figure

            lines : list
                List of LineData objects, one for each detected transition or segment

            thumbnail : bool
                If True then generate a thumbnail of the image. Default: True

            force : list
                List of LineData objects, one for each forced line id.
                Default: []

            Returns
            -------
            None

        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # get the peak value
        #pk = max(y)
        #pm = min(y)
        # do the plot and set the labels
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname
        fig = plt.figure(APlot.figno, figsize=(12,12), dpi=80)
        ax1 = fig.add_subplot(1,1,1)
        #ax1.plot(x,y,"-")
        offset = 0
        pm = 0
        pk = 0
        fm = 0.0
        fx = 0.0
        delta = 0
        offset = 0.0
        #
        # Determines frequency delta in the presence of masked values.
        def findDelta(freq):
          for i in range(len(freq)-1):
            if not freq.mask[i] and not freq.mask[i+1]:
              return freq.mask[i+1]-freq.mask[i]

          return 0.0
        #
        for i in range(len(stat)):
            mult = 1.
            addon = " Max"
            if i == 1:
                mult = -1.
                addon = " Min"
            ax1.plot(stat[i].freq(), offset + (mult * stat[i].spec()), '-', label="CubeStat" + addon)
            pm = ma.min(stat[i].spec())
            pk = ma.max(stat[i].spec())
            fm = ma.min(stat[i].freq())
            fx = ma.max(stat[i].freq())
            delta = abs(findDelta(stat[i].freq()))
            ax1.plot([fm, fx], [offset, offset], 'k-')
            offset += max(ma.max(stat[i].spec()) + 1., 4.0)
        for i in range(len(spec)):
            sp = (spec[i].spec()/spec[i].noise())
            ax1.plot(spec[i].freq(), sp + offset, '-', label="CubeSpec%i" % (i))
            pm = min(pm, min(sp) + offset)
            pk = max(pk, max(sp) + offset)
            fm = max(fm, ma.min(spec[i].freq()))
            fx = max(fx, ma.max(spec[i].freq()))
            ax1.plot([fm, fx], [offset, offset], 'k-')
            offset += max(ma.max(sp) + 1., 4.0)
            delta = abs(findDelta(spec[i].freq()))
        if pvc is not None:
            sp = (pvc.spec()/pvc.noise())
            pm = min(pm, min(sp) + offset)
            pk = max(pk, max(sp) + offset)
            fm = max(fm, ma.min(pvc.freq()))
            fx = max(fx, ma.max(pvc.freq()))
            delta = abs(findDelta(pvc.freq()))
            ax1.plot(pvc.freq(), sp + offset, '-', label="PVCorr")
            ax1.plot([fm, fx], [offset, offset], 'k-')

        ax1.set_ylabel("Signal/Noise")
        ax1.set_xlabel("Frequency (GHz)")
        ax1.set_title("Summary Plot")
        # reset the plot y axis to be a bit taller
        #ax1.set_ylim(ymax=pk*1.2)
        # make sure we can read the frequencies
        ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))
        # label each line

        step = (pk-pm)/20.0
        place = pm + (pk-pm)/5.0
        first = True
        ylim = ax1.get_ylim()[1]
        ax1.set_ylim([pm - 1.0, ylim * 1.2])
        ax1.set_xlim([fm - (2.0 * delta), fx + (2.0 * delta)])
        size = fig.get_size_inches()*fig.dpi
        ylim = ax1.get_ylim()
        first = True
        for l in lines:
            extra = ""
            # label
            if l.getkey("blend") != 0:
                extra += "*"
                frqs = [l.getkey("frequency")]
                ax1.plot([min(frqs), max(frqs)], [pk*.92, pk*.92], 'k-')
                ax1.plot([min(frqs), max(frqs)], [place-step/2.0,place-step/2.0], 'k-')

            ax1.text(l.getkey("frequency"),0.0,l.getkey("uid") + extra,withdash=True,rotation='vertical',dashdirection=1,dashlength=size[1]*0.7,dashrotation=90)
            if l.getfstart() != 0 and l.getfend() != 0:
                if first:
                    ax1.add_patch(patches.Rectangle((l.getfstart(), ylim[0]), l.getfend() - l.getfstart(), ylim[1] - ylim[0], alpha=0.1, ec='none', fc='blue', label="Channel Range"))
                    first = False
                else:
                    ax1.add_patch(patches.Rectangle((l.getfstart(), ylim[0]), l.getfend() - l.getfstart(), ylim[1] - ylim[0], alpha=0.1, ec='none', fc='blue'))
        first = True
        for l in force:
            ax1.text(l.getkey("frequency"),0.0,l.getkey("uid"),withdash=True,rotation='vertical',dashdirection=1,dashlength=size[1]*0.7,dashrotation=90,color='green')
            if l.getfstart() != 0 and l.getfend() != 0:
                if first:
                    ax1.add_patch(patches.Rectangle((l.getfstart(), ylim[0]), l.getfend() - l.getfstart(), ylim[1] - ylim[0], alpha=0.1, ec='none', fc='green', label="Forced Channel Range"))
                    first = False
                else:
                    ax1.add_patch(patches.Rectangle((l.getfstart(), ylim[0]), l.getfend() - l.getfstart(), ylim[1] - ylim[0], alpha=0.1, ec='none', fc='green'))

        ncol = 2
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
                  fancybox=True, shadow=True, ncol=ncol)
        #ax1.legend(loc="lower center",ncol=3)

        # finally, if a reference line was given, label the top axis in km/s as well
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            #print self._figurefiles[APlot.figno]
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()


    def makespec(self, x, y, cutoff, figname, title="", xlabel="", lines=[],
                 force=[], blends=[], continuum=None, ylabel=None,
                 thumbnail=True, references={}, refline=None, chan=None):
        """ Plots a spectrum, overlaying known spectral and reference lines.

            Parameters
            ----------
            x : list
                The x data to plot (usually freq or velocity).

            y : list
                The spectrum to plot.

            cutoff  : float or numpy array
                A horizontal line at this level will be plotted

            figname : str
                Root of output file name.  An extension matching the plot
                type will be appended. For instance, for, figname='fig'
                and plottype=PlotControl.PNG, the output file is 'fig.png'

            title : str
                The title to put at the top.
                Default: ""

            xlabel : str
                Label along the X axis

            lines : list
                A list of LineData objects, one for each detected transition.
                The labels and channel ranges are plotted from this
                information.

            force : list
                A list of LineData objects for forced lines. The labels and
                channel ranges are plotted from this information.

            blends : list
                A list of LineData objects for blended lines. The labels and
                channel ranges are plotted from this information.

            references : dictionary
                A dictionary of frequencies and reference line names to be
                overplotted. This can be useful if you want to plot some well
                known, but possibly not detected, lines.
                Default: empty

            continuum : list or numpy array?
                Matching to the size of the input spectrum, this is
                the continuum of the spectrum.
                Default: None

            ylabel : str
                Label along the Y axis.
                Default: None (no label)

            thumbnail : boolean
               If True, create a thumbnail when creating an output figure.
               Thumbnails will have '_thumb' appended for file root.
               For instance, if the output file is 'fig.jpg', the thumbnail
               will be 'fig_thumb.jpg'

            references : dict
                Dictionary of reference lines to plot. The keys are the
                frequencies and the values are the labels to place. Default: {}

            refline : float
                If given, this is the reference frequency for which VLSR = 0.0,
                the top axis will then be labeled in KM/S. Otherwise the middle
                of the plot is chosen to be VLSR = 0.0.
                Default: None (use the center of the spectrum)        

            chan : list of int, optional
                Channel numbers corresponding to `x`
                (default: if `None`, use index number).

            Returns
            -------
            None
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # get the peak value
        pk = ma.max(y)
        pm = ma.min(y)
        # do the plot and set the labels
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname
        fig = plt.figure(APlot.figno, figsize=(21,14), dpi=72)

        # X-axis frequency limits.
        # We have to step through the masked arrays manually to make sure
        # the channel and frequency axes remain properly aligned.
        axpad = 0.04
        for i in range(len(x)):
         if not x.mask[i]:
           xmin = x[i]
           cmin = chan[i]
           break
        #
        for i in range(len(x)-1,0,-1):
         if not x.mask[i]:
           xmax = x[i]
           cmax = chan[i]
           break
        #
        if xmin > xmax:
          xmin, xmax = xmax, xmin
          cmin, cmax = cmax, cmin
        #
        fmin = xmin-axpad*(xmax-xmin)
        fmax = xmax+axpad*(xmax-xmin)

        # Make ax1 the "twin" so that the tracker displays its coordinates.
        ax2 = fig.add_subplot(1,1,1)
        ax1 = ax2.twiny()
        ax1.xaxis.tick_bottom()
        ax1.xaxis.set_label_position('bottom')
        ax1.yaxis.set_visible(True)
        ax2.xaxis.tick_top()
        ax2.xaxis.set_label_position('top')
        ax2.yaxis.set_visible(False)
        plt.subplots_adjust(bottom=0.15)

        # Configure minor ticks to display channel number.
        # Display every channel up to 1000 channels; subsample after that.
        # Labels are subsampled sooner to avoid excessive clutter.
        maxloc = 1000
        maxlab = 500
        tickcolor = 'g'
        if chan is None:
          chan = range(len(x))
          tickcolor = 'r'
        locstride = (len(chan)+maxloc-1)/maxloc
        labstride = (locstride*maxloc)/maxlab
        matplotlib.ticker.Locator.MAXTICKS = 2*(maxloc+1)

        # Preliminary tick formatting.
        minorLabels = []
        minorLocations = []
        for i in range(0,len(chan),locstride):
          minorLabels.append('' if i%labstride else str("%.0f" % chan[i]))
          minorLocations.append(x[i])
        #
        minorFormatter = matplotlib.ticker.FixedFormatter(minorLabels)
        ax1.xaxis.set_minor_formatter(minorFormatter)
        #
        minorLocator = matplotlib.ticker.FixedLocator(minorLocations)
        #
        majstride = 5
        majorLocator = matplotlib.ticker.MaxNLocator(10*majstride)
        ax1.xaxis.set_major_locator(majorLocator)
        ax1.xaxis.set_minor_locator(minorLocator)

        ax1.set_xlim(fmin, fmax)
        #print "plotting\n\n",x,"\n\n"
        axlines = ax1.plot(x,y,"-", zorder=4)
        # @todo  temporary: turn on red plusses for debug for spectra < 1000 points
        axlines += ax1.plot(x,y,"r+")

        # Cutoff line. Force a list for use with minor tick guide lines.
        if not hasattr(cutoff, "__len__"): cutoff = [cutoff for xi in x]
        axlines += ax1.plot(x,cutoff,label='Cutoff level')
        #df = cutoff - continuum
        #ax1.plot(x,continuum-df)

        # Finalize minor tick formatting.
        ax1.xaxis.set_tick_params(which='minor', colors=tickcolor,
                                  labelsize=1, pad=1, width=0.25)
        minors = ax1.xaxis.get_minor_ticks()
        msize = minors[0].tick1line.get_markersize()
        ymin  = ax1.get_ylim()[0]
        guides = []
        for i in range(len(minors)):
          minors[i].tick2On = False
          if i%(labstride/locstride):
            # Shorten unlabeled minor ticks.
            minors[i].tick1line.set_markersize(msize/2)
        for i in range(0,len(x),labstride):
          # Draw guide lines from labeled minor ticks.
          guides += ax1.plot([x[i], x[i]], [ymin, cutoff[i]],
                             color='0.7', ls='-', lw=0.05, zorder=0)
        for label in ax1.xaxis.get_ticklabels(minor=True):
          label.set_rotation(90)

        # Finalize major tick formatting.
        majTicks = ax1.xaxis.get_major_ticks()
        majSize  = majTicks[0].tick1line.get_markersize()
        for i in range(len(majTicks)):
          if i%majstride:
            majTicks[i].label1On = False
            majTicks[i].tick1line.set_markersize(0.8*majSize)
          else:
            majTicks[i].tick1line.set_markersize(1.2*majSize)

        ncol = 2
        if continuum is not None:
            axlines += ax1.plot(x,continuum,'c-',label='Mean/Baseline')
            ncol += 1
        ax1.set_xlabel(xlabel)
        if ylabel == None:
            ax1.set_ylabel("Intensity")
        else:
            ax1.set_ylabel(ylabel)
        plt.title(title, y=1.04)

        # Set Y-axis limits (leave room for line IDs, include zero if close).
        ymin = pm-axpad*(pk-pm) if pm < 0 or pm-2*axpad*(pk-pm) > 0 else 0.0
        ax1.set_ylim(ymin=ymin, ymax=pk+0.20*(pk-pm))

        # make sure we can read the frequencies
        ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))

        # label each line
        step = (pk-pm)/20.0
        place = pm + (pk-pm)/5.0
        first = True
        seglines = []
        axtexts = []
        if isinstance(lines,dict): lines = lines.values()
        for l in lines:
            extra = ""
            # label
            if l.getkey("blend") != 0:
                extra += "*"
                frqs = [l.getkey("frequency")]
                for b in blends:
                    if b.getkey("blend") == l.getkey("blend"):
                        frqs.append(b.getkey("frequency"))
                        axtexts.append(ax1.text(b.getkey("frequency"),pk*.85,"",withdash=True,rotation='vertical',dashdirection=1,dashlength=50,dashrotation=90))
                        seglines += ax1.plot([b.getkey("frequency"),b.getkey("frequency")],[place-step/2.0,place+step/2.0],'k-')
                seglines += ax1.plot([min(frqs), max(frqs)], [pk*.92, pk*.92], 'k-')
                seglines += ax1.plot([min(frqs), max(frqs)], [place-step/2.0,place-step/2.0], 'k-')

            axtexts.append(ax1.text(l.getkey("frequency"),pk*.85,l.getkey("uid")+extra,withdash=True,rotation='vertical',dashdirection=1,dashlength=50,dashrotation=90))
            # black tickmark
            seglines += ax1.plot([l.getkey("frequency"),l.getkey("frequency")],[place-step/2.0,place+step/2.0],'k-')
            # red segment
            if first:
                seglines += ax1.plot([l.getfstart(),l.getfend()],[place,place],'r-',label="Chan. Ranges")
                first = False
            else:
                seglines += ax1.plot([l.getfstart(),l.getfend()],[place,place],'r-')
            seglines += ax1.plot([l.getfstart(),l.getfstart()],[place-step,place+step],'r-')
            seglines += ax1.plot([l.getfend(),l.getfend()],[place-step,place+step],'r-')

        first = True
        for l in force:
            axtexts.append(ax1.text(l.getkey("frequency"),pk*.85,l.getkey("uid"),withdash=True,rotation='vertical',dashdirection=1,dashlength=50,dashrotation=90,color='green'))
            # green tickmark
            seglines += ax1.plot([l.getkey("frequency"),l.getkey("frequency")],[place-step/2.0,place+step/2.0],'g-')
            # green segment
            if first:
                seglines += ax1.plot([l.getfstart(),l.getfend()],[place,place],'g-',label="Forced Transition")
                first = False
            else:
                seglines += ax1.plot([l.getfstart(),l.getfend()],[place,place],'g-')
            seglines += ax1.plot([l.getfstart(),l.getfstart()],[place-step,place+step],'g-')
            seglines += ax1.plot([l.getfend(),l.getfend()],[place-step,place+step],'g-')

            # done

        # Add references
        for f in references.keys():
            if f<fmin or f>fmax: continue
            r = references[f]
            seglines += ax1.plot([f,f],[2.0*place-step,2.0*place+step],'k-')
            axtexts.append(ax1.text(f,2.0*place+step,r,withdash=True,rotation='vertical',dashdirection=1,dashlength=50,dashrotation=45))

        # Put a legend below current axis.
        ax1.legend(loc="lower center", bbox_to_anchor=(0.5,-0.14),
                   fancybox=True, shadow=True, ncol=ncol)

        # Label the top axis in km/s vlsr offset from reference (or mid-band).
        if refline is None:
            # @todo   for now cheat, and always take the middle of the band
            refline = 0.5 * (ma.min(x) + ma.max(x))
        ax2.set_xlabel('VLSR Offset (km/s) from %g' % refline, color='r')
        # use the radio definition 
        vmin = (1-fmin/refline)*utils.c
        vmax = (1-fmax/refline)*utils.c
        #print "REFERENCE LINE @ ",refline," VEL RANGE",vmin,vmax
        ax2.set_xlim(xmin=vmin, xmax=vmax)
        ax2.xaxis.labelpad = 3
        ax2.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        for t1 in ax2.get_xticklabels():
            t1.set_color('r')
        ax2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        for tick in ax2.yaxis.get_minor_ticks():
          tick.tick1On = True
          tick.tick2On = True

        if figname and self._plot_mode != PlotControl.INTERACTIVE:
          self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
          #print self._figurefiles[APlot.figno]
          fig.savefig(self._figurefiles[APlot.figno], dpi=fig.get_dpi())
          if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            # Remove channel-based ticks and guides for interactive mode.
            ax1.xaxis.cla()
            ax1.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(10))
            ax1.xaxis.set_major_formatter(
                matplotlib.ticker.ScalarFormatter(useOffset=False)
            )
            ax1.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
            ax1.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax1.set_xlabel(xlabel)
            #
            for line in guides: line.remove()

            # Make room for radio buttons and legend.
            plt.subplots_adjust(left=0.17)

            # Convert frequency to channel (assumed uniform).
            def freq_to_chan(f):
                return cmin+(cmax-cmin)*(f-xmin)/(xmax-xmin)

            # Convert channel to frequency (assumed uniform).
            def chan_to_freq(c):
                return xmin+(xmax-xmin)*(c-cmin)/(cmax-cmin)

            # Radio buttons.
            rcolor = 'lightgoldenrodyellow'
            rlabels = (xlabel, 'Channel Number')
            rax = plt.axes([0.02, 0.02, 0.14, 0.10], axisbg=rcolor)
            radio = RadioButtons(rax, rlabels)

            # X-axis callback, plot frequency or channels.
            def xcall(label):
                if (label == rlabels[0]) == (ax1.get_xlabel() == xlabel):
                  # User re-selected the currently displayed view.
                  return

                # Translate X-axis data.
                xl, xr = ax1.get_xlim()
                if label == rlabels[0]:
                  z = x
                  zlabel = rlabels[0]
                  xl = chan_to_freq(xl)
                  xr = chan_to_freq(xr)
                  for line in seglines:
                    cdata = line.get_xdata()
                    fdata = []
                    for c in cdata: fdata.append(chan_to_freq(c))
                    line.set_xdata(fdata)
                  for text in axtexts:
                    pos = text.get_position()
                    text.set_position((chan_to_freq(pos[0]), pos[1]))
                else:
                  z = chan
                  zlabel = rlabels[1]
                  xl = freq_to_chan(xl)
                  xr = freq_to_chan(xr)
                  for line in seglines:
                    fdata = line.get_xdata()
                    cdata = []
                    for f in fdata: cdata.append(freq_to_chan(f))
                    line.set_xdata(cdata)
                  for text in axtexts:
                    pos = text.get_position()
                    text.set_position((freq_to_chan(pos[0]), pos[1]))

                for line in axlines: line.set_xdata(z)
                ax1.set_xlim(xl, xr)
                ax1.set_xlabel(zlabel)
                plt.draw()

            radio.on_clicked(xcall)
            plt.show()

        plt.close()

    def makeUlines(self,x,y,noise=0.0,title=None,figname=None,xlab=None,ylab=None,segments=None,tags=None, thumbnail=True):
        """simple plotter of multiple columns against one column
           stolen from atable, allowing some extra bars in the plot
           for line_id
           This code should be merged with plotter()
        """
        if self._plot_mode == PlotControl.NOPLOT:
            return
        # if filename: plt.ion()
        #plt.ion()
        plt.ioff()
        APlot.figno = APlot.figno + 1
        if self._abspath != "" and figname:
            figname = self._abspath + figname

        fig = plt.figure(APlot.figno)
        ax1 = fig.add_subplot(1,1,1)
        xlim = ax1.get_xlim()
        ylim = ax1.get_ylim()
        for yi in y:
            ax1.plot(x,yi)
        ax1.plot([xlim[0],xlim[1]],[noise,noise],'-')
        height = abs(ylim[0]-ylim[1])/2.0
        inc = height/20.
        if segments:
            for s in segments:
                ax1.plot([s[0],s[1]],[height,height])
        if tags:
            for t in tags:
                ax1.plot([t,t],[height-inc,height+inc])
        if title:    ax1.set_title(title)
        if xlab:     ax1.set_xlabel(xlab)
        if ylab:     ax1.set_ylabel(ylab)
        if figname:
            self._figurefiles[APlot.figno] = figname + PlotControl.mkext(self._plot_type,True)
            fig.savefig(self._figurefiles[APlot.figno])
            if thumbnail: self.makeThumbnail(APlot.figno, fig=fig)

        if self._plot_mode==PlotControl.INTERACTIVE:
            plt.show()

        plt.close()


if __name__ == "__main__":
    import PlotControl
    x = np.arange(0,1,0.1)
    psize = x*200 # vary the point size for scatter plot
    y = x*x
    z = y-x

    print "a1"
    a1 = APlot(pmode=PlotControl.INTERACTIVE,ptype=PlotControl.PNG,figno=10,abspath="/tmp")
    #a1.backend('agg')
    a1.plotter(x,[y],figname="figone")
    a1.plotter(x,[z])
    a1.plotter(x,[y,z])
    a1.show()

    print "a2"
    a2 = APlot(pmode=PlotControl.INTERACTIVE,ptype=PlotControl.PNG,figno=20)
    a2.backend('agg')
    #a2.histogram([x,y])
    #a2.show()
    a2.plotter(x,[y],labels=['Example label','DEF','ZYZ']) # last two labels unused.
    a2.show()
    a2.scatter(y,x,figname="scatter",color='red',size=psize, cmds=['grid'])
    a2.show()

    print "a3"
    a3 = APlot(pmode=PlotControl.BATCH,ptype=PlotControl.PNG,figno=29)
    a3.histogram([x,y],figname="histo")
    a3.plotter(x,[y],figname="plot")
    a3.show()
    print "A3 plotmode: %d" % a3.plotmode
    print "Abs,AP figno %d,%d" % (AbstractPlot.figno, APlot.figno)
    if a3.plotmode == PlotControl.BATCH:
       print "BATCH"
