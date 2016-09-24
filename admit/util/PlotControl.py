""" .. _PlotControl-api:

    **PlotControl** --- Defines plot mode, type and orientation.
    ------------------------------------------------------------

    Singleton class to encapsulate plot types and plot modes as enums, as well a
    convention for file extension strings.  All plot types may not be supported
    by individual plotting tools.  For instance, matplotlib only supports
    PNG for thumbnail creation.

    Plot types are: 

    - PlotControl.GIF  (@todo should we get rid of this?)
    - PlotControl.JPG
    - PlotControl.PDF 
    - PlotControl.PNG
    - PlotControl.PS
    - PlotControl.SVG

    Plot modes are: 

    - PlotControl.NOPLOT 
    - PlotControl.BATCH 
    - PlotControl.INTERACTIVE 
    - PlotControl.SHOW_AT_END 

    Plot Orientations are:

    - PlotControl.LANDSCAPE
    - PlotControl.PORTRAIT
"""
class __PlotControl:

     _NUM_SUPPORTED_TYPES = 8
     PLOTTYPE_NONE, PLOTTYPE_EPS, PLOTTYPE_GIF, PLOTTYPE_JPG, PLOTTYPE_PDF, PLOTTYPE_PNG, PLOTTYPE_PS, PLOTTYPE_SVG = range(_NUM_SUPPORTED_TYPES)

     # xbm, xpm, ppm?  - imview supports these. what about matlab?
     PLOTMODE_NOPLOT         =  -1 
     PLOTMODE_BATCH          =  32
     PLOTMODE_INTERACTIVE    =  33
     PLOTMODE_SHOW_AT_END    =  34
     PLOTORIENTATION_LANDSCAPE = 'landscape'
     PLOTORIENTATION_PORTRAIT  = 'portrait'

     #@staticmethod
     def mkext(self,plottype,with_dot):
         """ Return a standard file extension, with or without dot, for a given 
             plot type.

             Parameters
             ----------
             plottype : plot type, one of the supported enumerations
             with_dot : True or False to prepend '.' to the extension.

             Returns
             -------
             str
                 file extension

         """
         if plottype == self.PLOTTYPE_NONE:
             raise Exception, "PlotControl.NONE has no file extension!"
         if plottype == self.PLOTTYPE_GIF:
             ext = "gif"
         elif plottype == self.PLOTTYPE_JPG:
             ext = "jpg"
         elif plottype == self.PLOTTYPE_PDF:
             ext = "pdf"
         elif plottype == self.PLOTTYPE_PNG:
             ext = "png"
         elif plottype == self.PLOTTYPE_PS:
             ext = "ps"
         elif plottype == self.PLOTTYPE_SVG:
             ext = "svg"
         else:
            raise Exception, "Unrecognized input plot type: %s. Expecting PlotControl enumeration" % str(plottype)

         if with_dot == True:
            return "." + ext
         else:
            return ext

     #@staticmethod
     def plottype(self,plottype):
         """ Return a string representation of the plot type.

             Parameters
             ----------
             plottype : int 
                 Plot type, one of the supported enumerations

             Returns
             -------
             str
                 String representation of plot type

         """
         if plottype == self.PLOTTYPE_NONE:
             return "PLOTTYPE_NONE"
         elif plottype == self.PLOTTYPE_EPS:
             return "PLOTTYPE_EPS"
         if plottype == self.PLOTTYPE_GIF:
             return "PLOTTYPE_GIF"
         elif plottype == self.PLOTTYPE_JPG:
             return "PLOTTYPE_JPG"
         elif plottype == self.PLOTTYPE_PDF:
             return "PLOTTYPE_PDF"
         elif plottype == self.PLOTTYPE_PNG:
             return "PLOTTYPE_PNG"
         elif plottype == self.PLOTTYPE_PS:
             return "PLOTTYPE_PS"
         elif plottype == self.PLOTTYPE_SVG:
             return "PLOTTYPE_SVG"
         else:
             return "UNKNOWN PLOT TYPE %d" % plottype

     #@staticmethod
     def isSupportedType(self,plottype):
          """Test if the input plot type is supported.  Supported
             means that either CASA imview or matplotlib supports
             the type, but not necessarily both!

             Parameters
             ----------
             plottype : int 
                 An integer plot type

             Returns 
             ----------
             boolean
                 True if supported, False if unsupported
          """
          return plottype in range(self._NUM_SUPPORTED_TYPES)

     #@staticmethod
     def plotmode(self,plotmode):
         """ Return a string representation of the plot mode.

             Parameters
             ----------
             plotmode : int 
                 Plot mode, one of the supported enumerations

             Returns
             -------
             string  
                 String representation of plot mode

         """
         if plotmode == self.PLOTMODE_NOPLOT:
             return "PLOTMODE_NOPLOT"
         if plotmode == self.PLOTMODE_BATCH:
             return "PLOTMODE_BATCH"
         elif plotmode == self.PLOTMODE_INTERACTIVE:
             return "PLOTMODE_INTERACTIVE"
         elif plotmode == self.PLOTMODE_SHOW_AT_END:
             return "PLOTMODE_SHOW_AT_END"
         else:
             return "UNKNOWN PLOT MODE (%d)" % plotmode


#-------------------------------
# This is a singleton    
#-------------------------------
_inst = __PlotControl()

#-------------------------------
# shortcuts for the enumerations
#-------------------------------

#Plot types
NONE  = _inst.PLOTTYPE_NONE
EPS   = _inst.PLOTTYPE_EPS
GIF   = _inst.PLOTTYPE_GIF # do we really support GIF?
JPG   = _inst.PLOTTYPE_JPG
PDF   = _inst.PLOTTYPE_PDF
PNG   = _inst.PLOTTYPE_PNG
PS    = _inst.PLOTTYPE_PS
SVG   = _inst.PLOTTYPE_SVG

#Plot modes
NOPLOT         = _inst.PLOTMODE_NOPLOT
BATCH          = _inst.PLOTMODE_BATCH
INTERACTIVE    = _inst.PLOTMODE_INTERACTIVE
SHOW_AT_END    = _inst.PLOTMODE_SHOW_AT_END
LANDSCAPE      = _inst.PLOTORIENTATION_LANDSCAPE
PORTRAIT       = _inst.PLOTORIENTATION_PORTRAIT

#-------------------------------
# shortcuts for the methods
#-------------------------------
mkext    = _inst.mkext
plottype = _inst.plottype
plotmode = _inst.plotmode
isSupportedType = _inst.isSupportedType
