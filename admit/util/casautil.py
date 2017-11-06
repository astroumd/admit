""" **casautil** --- CASA-dependent utilities module.
    -------------------------------------------------

    This module contains utility functions that rely on CASA.
"""
# Non-CASA utility functions must be put in util.py!!

import os
import numpy
import numpy.ma as ma


try:
  import casa
  import taskinit
except:
  print "WARNING: No CASA; casautil can't function"

# imview was left out of the casa namespace in CASA5
from imview import imview as casa_imview

import PlotControl

def iscasa(file):
    """is a file a casa image

       Returns
       -------
       boolean
    """
    # @todo   caution: this also catches a MIRIAD file.... or check for 'file/header' and/or 'file/table.info'
    return os.path.isdir(file)
    

def implot(rasterfile, figname, contourfile=None, plottype=PlotControl.PNG,
           plotmode=PlotControl.BATCH, colorwedge=False, zoom=1):
    """Wrapper for CASA's imview, that will also create thumbnails.

       Parameters
       ----------
       rasterfile : str
         Fully-qualified image file to use as raster map.  Optional if
         contourfile is given.

       figname : str
           Fully-qualified output file name.

       contourflie : str
         Fully-qualified image file to use as contour map. Contours
         will be overlaid on rasterfile if both are given.  Optional if
         rasterfile is given.

       plottype : int
         Plotting format, one of util.PlotControl plot type (e.g., PlotControl.PNG). Default: PlotControl.PNG

       plotmode : int
         Plot mode, one of util.PlotControl plot mode (e.g., PlotControl.INTERACTIVE). Default: PlotControl.BATCH

       colorwedge  : boolean
         True - show color wedge, False - don't show color wedge

       zoom : int
         Image zoom ratio.

       Returns
       -------
       None

    """

    # axes dictionary is ignored by imview!
    #xlab=NONE,ylab=NONE 

    #can't support this until imview out= is fixed! (see below)
    #orientation=PlotControl.LANDSCAPE 


    if plotmode == PlotControl.NOPLOT:  return

    if contourfile==None and rasterfile==None:
       raise Exception, "You must provide rasterfile and/or contourfile"

    if not PlotControl.isSupportedType(plottype):
       raise Exception, "Unrecognized plot type %d. See util.PlotControl" % plottype
    if plottype == PlotControl.SVG or plottype == PlotControl.GIF:
       raise Exception, "CASA viewer does not support SVG and GIF format :-("

    if plottype == PlotControl.JPG:
       raise Exception, "CASA viewer claims to support JPG but doens't :-("

    if plottype != PlotControl.PNG:
       raise Exception, "Thumbnails not supported (by matplotlib) for types other than PNG"


    DEFAULT_SCALING = -1  # scaling power cycles.

    # Grmph. axes dictionary ignored in imview.
    #    axes={'y':ylab, 'x':xlab}

    contour = {}
    if contourfile: contour={'file':contourfile}

    raster  = {}
    if rasterfile:
        raster={'file'       : rasterfile,  
                'colorwedge' : colorwedge, 
                'scaling'    : DEFAULT_SCALING}

    # Grmph. Giving an 'out' dictionary to imview causes SEVERE error.
    #out={'file'   : figname,
    #     'format' : PlotControl.mkext(plottype,False),
    #     'scale'  : 2.0,
    #     'dpi'    : 1.0,
    #     'orient' : orientation}
         #dpi/scale - DPI used for PS/EPS, scale for others. Perhaps 
         #            we will enable these options later

    # These are completely ignored, but imview throws an exception
    # axes is not provided!
    axes = {'x':'x','y':'y','z':'z'}

    # work around this axis labeling problem?
    ia = taskinit.iatool()
    ia.open(rasterfile)
    h = ia.summary()
    ia.close()
    #print "PJT: implot axisnames:",h['axisnames'][0],h['axisnames'][1]
    if h['axisnames'][1]=='Frequency':
        axes['y'] = 'Frequency'

    # this complained about 'dimensions of axes must be strings (x is not)'
    # axes = { 'x' : h['axisnames'][0],  'y' : h['axisnames'][1] , 'z' : 'z' }

    
    casa_imview(raster=raster, contour=contour, out=figname, axes=axes,
                zoom=zoom)

    #of = PlotControl.mkext(plottype,dot=False)
    #casa.viewer(outfile=outfile, infile=imagename, gui=False, plottype=of)
    if plotmode == PlotControl.INTERACTIVE or plotmode==PlotControl.SHOW_AT_END:
        casa_imview(raster=raster, contour=contour,axes=axes)

# Moment_AT, and now CubeSum_AT too
def getdata(imgname, chans=[], zeromask=False):
    """Return all good data from a CASA image as a masked numpy array.

       The tb.open() access method, although faster, didn't seem to carry
       the mask (or at least in an easy way).  ma.masked_invalid(data)
       still returned all pixels ok.

       NOTE:  since this routine grabs all data in a single numpy
       array, this routine should only be used for 2D images
       or small 3D cubes, things with little impact on memory

       Parameters
       ----------
       imagename : str 
           The (absolute) CASA image filename 

       Returns
       -------
       array 
           data in a masked numpy array
    """
    ia = taskinit.iatool()    
    ia.open(imgname)
    if len(chans) == 0:
        d = ia.getchunk(blc=[0,0,0,0],trc=[-1,-1,-1,0],getmask=False).squeeze()
        m = ia.getchunk(blc=[0,0,0,0],trc=[-1,-1,-1,0],getmask=True).squeeze()
    else:
        d = ia.getchunk(blc=[0,0,chans[0],0],trc=[-1,-1,chans[1],0],getmask=False).squeeze()
        m = ia.getchunk(blc=[0,0,chans[0],0],trc=[-1,-1,chans[1],0],getmask=True).squeeze()
    ia.close()
    # note CASA and MA have their mask logic reversed
    # casa: true means a good point
    #   ma: true means a masked/bad point
    if zeromask:
        shape = d.shape
        ndim = len(d.shape)
        if ndim == 2:
            (x,y) = ma.where(~m)
            d[x,y] = 0.0
        elif ndim == 3:
            (x,y,z) = ma.where(~m)
            d[x,y,z] = 0.0
        else:
            raise Exception,"getdata: cannot handle data of dimension %d" % ndim
    dm = ma.masked_array(d,mask=~m)
    return dm

# CubeSum - see getdata2()
def getdata1(imgname):
    """Return all good data from a CASA image as a compressed 1D numpy array.
 
       The tb.open() access method, although faster, didn't seem to carry
       the mask (or at least in an easy way).  ma.masked_invalid(data)
       still returned all pixels ok.
  
       NOTE:  since this routine grabs all data in a single numpy
       array, this routine should only be used for 2D images
       or small 3D cubes.
  
       Parameters
       ----------
       imagename : str 
           The (absolute) CASA image filename 
  
       Returns
       -------
       array 
          data in a 1D numpy array
    """
    ia = taskinit.iatool()
    ia.open(imgname)
    d = ia.getchunk(blc=[0,0,0,0],trc=[-1,-1,0,0],getmask=False)
    m = ia.getchunk(blc=[0,0,0,0],trc=[-1,-1,0,0],getmask=True)
    ia.close()
    # note CASA and MA have their mask logic reversed
    # casa: true means a good point
    #   ma: true means a masked/bad point
    dm = ma.masked_array(d,mask=~m)
    return dm.compressed()

# PVCorr
def getdata_raw(imgname):
    """Return data as a 2D numpy array
       For more detailed access to cubes, don't use this method, 
       as it will use all the memory. instead use ia.open()
       and getslice/putslice() to cycle through the cube.
       Note we're not getting the mask this way.... see Moment_AT for
       a version that return a numpy.ma array with masking

       See putdata(imgname,data) for the reverse operation, but you
       will need to create a clone of the image to ensure the header.

       Parameters
       ----------
       imagename : str 
           The (absolute) CASA image filename 
  
       Returns
       -------
       array 
           data in a 2D numpy array
    """
    tb = taskinit.tbtool()
    tb.open(imgname)
    data=tb.getcol('map')
    tb.close()
    shp=data.shape
    nx = shp[0]
    ny = shp[1]
    d = data.reshape(nx,ny)
    return d

def putdata_raw(imgname, data, clone=None):
    """Store (overwrite) data in an existing CASA image.
       See getdata_raw(imgname) for the reverse operation.

       Parameters
       ----------
       imagename : str
           The (absolute) CASA image filename.  It should exist
           already, unless **clone** was given.

       data : 2D numpy array or a list of 2D numpy arrays
           The data...

       clone : str, optional
           An optional filename from which to clone the image
           for output. It needs to be an absolute filename.
  
    """
    ia = taskinit.iatool()    
    if clone != None:
        ia.fromimage(infile=clone,outfile=imgname,overwrite=True) 
        ia.close()
    # @todo this seems circumvent to have to borrow the odd dimensions (nx,ny,1,1,1) shape was seen
    if type(data) == type([]):
        # @todo since this needs to extend the axes, the single plane clone and replace data doesn't work here
        raise Exception,"Not Implemented Yet"
        bigim = ia.imageconcat(outfile=imgname, infiles=infiles, axis=2, relax=T, tempclose=F, overwrite=T)
        bigim.close()
    else:
        tb = taskinit.tbtool()
        tb.open(imgname,nomodify=False)
        d = tb.getcol('map')
        pdata = ma.getdata(data).reshape(d.shape)
        tb.putcol('map',pdata)
        tb.flush()
        tb.close()
    return
  
def mapdim(imgname, dim=None):
     """Return the dimensionality of the map, or if dim is given.
     
     Returns True if the dimensionality matches this value, or
     False if not.

     Warning: opens and closes the map via ia.open()

     Parameters
     ----------
     imagename : str (a filename)

     dim : integer (or None)

     """
     ia = taskinit.iatool()     
     ia.open(imgname)
     s = ia.summary()
     shape = s['shape']
     ia.close()
     #
     rdim = -1
     for d in range(len(shape)):
         if shape[d] == 0 or shape[d] == 1:
             rdim = d 
             break
     if rdim < 0:
       rdim = len(shape)
     #print "MAPDIM",imgname,shape,rdim
     #
     if dim == None:
         return rdim
     if dim == rdim:
         return True
     else:
         return False


def parse_robust(robust):
      """parse a compound robust=['algorithm',optional_parameters...]

      Within ADMIT we use robust=[]
      Within CASA  we use a varargs type algorithm=,fence=,...  

      Parameters  
      ----------
      robust :  list of robust parameters, method specific. See e.g. casa::imstat

      Returns
      -------
      dict
          A dictionary ready for \*\*args inclusion in a CASA command.
          If none found, returns an empty dictionary.
      """
      rkey = {}
      nr = len(robust)
      if nr==0:  
          return rkey

      a = robust[0]                                   # algorithm:

      if a[:2]=='cl':                                 # classic
          rkey['algorithm'] = 'classic'
          if nr>1:
              rkey['clmethod'] = robust[1]
      elif a[:2]=='ch':                               # chauvenet
          rkey['algorithm'] = 'chauvenet'
          if nr>1:
              rkey['zscore'] = robust[1]
              if nr>2:
                  rkey['maxiter'] = robust[2]
      elif a[:1]=='f':                                # fit-half
          rkey['algorithm'] = 'fit-half'
          if nr>1:
              rkey['center'] = robust[1]
              if nr>2:
                  rkey['lside'] = robust[2]
      elif a[:1]=='h':                                # hinges-fences
          rkey['algorithm'] = 'hinges-fences'
          if nr>1:
              rkey['fence'] = robust[1]
      else:
          raise Exception("Unknown algorithm in robust=%s" % robust)
      print "ROBUST:",rkey
      return rkey

