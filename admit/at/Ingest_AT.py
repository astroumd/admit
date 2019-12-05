""" .. _Ingest-at-api:

   **Ingest_AT** --- Ingests a (FITS) data cube.
   ---------------------------------------------

   This module defines the Ingest_AT class.
"""
import os, sys

import admit
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.util.Image import Image
import admit.util.utils as utils
import admit.util.casautil as casautil
import admit.util.ImPlot  as ImPlot
from admit.bdp.SpwCube_BDP import SpwCube_BDP
from admit.bdp.Image_BDP   import Image_BDP
from admit.util.AdmitLogging import AdmitLogging as logging

import numpy as np
import math
try:
    import taskinit
    import casa
    from specsmooth import specsmooth
    from impbcor import impbcor
    from imtrans import imtrans
except:
    print "WARNING: No CASA; Ingest task cannot function."

import random

# @todo 
# - rel path should be to ../basename.fits
# = edge/box are the keywords to cut a cube
#   len(box) = 0       edge allowed
#              2       no edge allowed, they are z1,z2
#              4       edge allowed, they are blc,trc
#              6       no edge allowed
# - vlsr needs to be stored, in a veldef?   For this we need access to ASDM/Source.xml
#   and will need a small tool in util.py to parse the xml and return what we need
# - resolve the confusion between symlink= and copy=
# - allow LineCube instead of the default SpwCube
# - autobox?
# - if not a fits file, there is no smoothing
#   (obviously if it remains a symlink, of course we cannot change the data)
# - check if spectral reference is LSRK (e.g. some ALMA is TOPO, that's bad)
#   although some may not have it, e.g. test6503
#   SPECSYS = 'TOPO' or 'TOPOCENT' (casa 3.3.0)
#             'BARY'  (helio)
#   imhead->['reffreqtype']
#  - smooth and decimate option?
#  - vlsr=0.0 cannot be given technically?


class Ingest_AT(AT):
    """Ingest an image (cube) into ADMIT, normally to bootstrap a flow.

    See also :ref:`Ingest-AT-Design` for the design document.

    Ingest an image cube (usually FITS, but a CASA image or MIRIAD
    image are also natively supported by CASA) into CASA.  Expect I/O
    penalties if you use FITS or MIRIAD because CASA images are tiled.

    A number of selections and corrections to the cube can be made, as
    specified by the keywords. Notably, a sub-cube can be taken out of
    the cube by trimming off spatial and spectral edges, a primary beam
    correction can be made as well.

    Internally ADMIT will store images as 4D CASA images, with any missing
    3rd or 4th axis created redundantly (FREQ as axis 3, and POL as axis 4)

    **Keywords**

      **file**: string
               Input filename.

               Usually 'basename.fits' where 'basename' can be long, and can
               involve a directory hierarchy.  The admit directory will be
               'basename.admit', which will include the whole directory path
               if one was given.

               A symbolic link within ADMIT will then be used to resolve
               this as a local file.
    
               An absolute address is advised to be used if your working directory
               can change in a flow.

               If a CASA image is given, a symlink is used when no modifications
               (e.g. box=) are used, but this will cause uncertain integrity of the
               input BDP, as other clients could be modifying it.  A MIRIAD image
               can also be given, but I/O (like with FITS) will be slower.

               [no default]

      **basename**: string
               New short basename (like an alias) of the output file.
    
               This is meant to override a possibly long basename in the input
               file. The **alias** keyword in the baseclass can still be used
               to create **basename-alias** type filenames.
               Warning: if you use a dash in your basename, there is a good risk
               this will be confused with the alias separator in the basename
               in a flow, as these are "basename-alias.extension".
               Default: empty string, basename inherited from the input file name.

      **pb**:  string
               If given, this is the filename of the Primary Beam by which the
               input file needs to be multiplied to get a noise flat image for
               processing the ADMIT flow.
               The ALMA pipeline product of the Primary Beam should be in
               'longname.pb.fits' where the flux flat cube is
               'longname.pbcor.fits'  Note: PB correction is slow.
               Default:  empty string, no PB correction is done.

      **usepb**: boolean
               If True, the PB is actually used in an assumed flux flat input file to
               create a noise flat input BDP.  If False, it is assumed the user has
               given a noise flat file, and the PB can be used downstream to compute
               proper PB corrected fluxes.  Note that the PB is always stored as an 2D image,
               not as a cube.
               Default: True

      **box**:  blc,tlc (a list of 2, 4 or 6 integers)
               Select a box region from the cube.
               For example box=[xmin,ymin,xmax,ymax], which takes all channels, or
               [xmin,ymin,zmin,xmax,ymax,zmax], which also selects a range in channels.
               You can also select just some channels, with box=[zmin,zmax].
               As always, pixels and channels are 0 based in CASA.
               Arbitrary CASA regions are not implemented here, we only support
               a box/edge selection.

      **edge**:  Z_start,Z_end (a list of 1 or 2 integers)
               You can use edge= to remove edge channels, e.g. if box= was not specified,
               or when only an XY box was given. If box contains 2 or 6 numbers, any edge
               specification would be ignored. If one number is given, the edge rejection
               is the same at the upper and lower end. Default: not used.

      **smooth**: [nx,ny,[nz]] (a list of 2 or 3 integers)
               You can convolve your cube spatially, and optionally spectrally as well,
               by supplying the number of pixels by which it is convolved. Spatially the
               FWHM is used. 
               If nz is 1, a Hanning smooth is applied, else a boxcar of size nz is used.
               See also :ref:`Smooth-AT-api`, where a common beam can be computed or supplied.
               A future version should contain a decimation option.
               By default no smoothing is applied.
    
      **mask**: boolean
               If True, a mask needs to be created where the
               cube has 0's. This option is automatically bypassed if the input
               CASA image had a mask. 
               [False]

      **vlsr**: float (km/s)
               VLSR of the source (km/s).  If not set, the frequency at the center of the
               band is compared with the rest frequency from the header, which we call VLSRc.
               If the input file is not FITS, or header items are missing if the input
               file is CASA or MIRIAD already, unexpected things may happen.
               This VLSR (or VLSRc) is added to the ADMIT summary, which will be used
               downstream in the flow by other AT's (e.g. LineID)
               Default: -999999.99 (not set).

      **restfreq**: float (GHz)
               An alternative method providing the source VLSR would be to specify the true
               restfreq (f0) where the fits header has a 'fake' restfreq (f). This technique
               is sometimes used by the PI to avoid complex high-z doppler calculations and
               supply the redshifted line directly.
               In this case VLSR = c * (1-f/f0), in the radio definition, with z in the optical
               convention of course. We call this VLSRf.
               NOTE: clarify/check if the "1+z" velocity scale of the high-z object is correct.
               Default: -1.0 (method not used). Units must be GHz!
      

    **Input BDPs**
      None. The input is specific via the file= keyword.

    **Output BDPs**

      **SpwCube**: count: 1
        The output spectral window cube. The convention is that the name of the BDP
        inherits from the basename of the input fits cube,and adding an extension
        "im". Each AT has a hidden keyword called alias=, use this keyword if
        you want to modify the cube name to "alias.im", and hence the BDP to
        "alias.im.bdp".   Note this is an exception from the usual rule, where
        alias= is used to create a dashed-prefix to an extension, e.g. "x.alias-y".

      **Image_BDP**: 1
        Output PB Map. If the input PB is a cube, the central channel (being representative
        for the avarage PB across the spectrum window) is used.
        New extension will be ".pb"

    Parameters
    ----------

    keyval : dictionary, optional
      Keyword-value pairs, directly passed to the contructor for ease of
      assignment.

    Attributes
    ----------

    _version : string
        Version ID for some future TBD use.  Also should not be documented here,
        as underscore attributes are for internal usage only.

    """

    #### DEPRECATED KEYWORDS BUT STILL ACTIVE IN CODE BY THEIR DEFAULT
    """

          **symlink** : True/False:
               If True, A symlink is kept to the input file without
               any conversion (if that was needed) This is used in
               those cases where your whole flow can work with the
               fits file, without need to convert to a CASA image
               Setting to True, also disabled all other processing
               (mask/region/pbcor) Use with caution!  [False]
               DEPRECATION

    """

    def __init__(self,**keyval):
        keys = {
            'file'    : "",        # fitsfile cube or map (or casa/miriad)
            'basename': "",        # override basename (useful for shorter names)
            'pb'      : "",        # PB cube or map
            'usepb'   : True,      # use PB, or was it just given for downstream
            'mask'    : True,      # define a mask where data==0.0 if no mask present
            'box'     : [],        # [] or z1,z2 or x1,y1,x2,y2  or x1,y1,z1,x2,y2,z2 
            'edge'    : [],        # [] or zl,zr - number of edge channels
            'smooth'  : [],        # pixel smoothing size applied to data (can be slow) - see also Smooth_AT
            'variflow': False,     # requires manual sub-flow management for now
            'vlsr'    : -999999.99, # force a VLSR (see also LineID)
            'restfreq': -1.0,      # alternate VLSRf specification
            # 'symlink' : False,   # 
            # 'autobox' : False,   # automatically cut away spatial and spectral slices that are masked
            # 'cbeam'   : 0.5,     # channel beam variation allowed in terms of pixel size to use median beam
        }
        AT.__init__(self,keys,keyval)
        self._version = "1.1.5"
        self.set_bdp_in()                            # no input BDP
        self.set_bdp_out([(SpwCube_BDP, 1),          # one or two output BDPs
                          (Image_BDP,   0),          # optional PB if there was an pb= input
                        ])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.

        Ingest_AT adds the following to ADMIT summary::

           Key      type        Description
         --------  ------       -----------
         fitsname  string      Pathless filename of FITS cube
         casaname  string      Pathless filename of CASA cube
         object    string      Object (or field) name
         naxis     integer     Number of axes
         naxisn    integer     size of axis n (n=1 to naxis0)
         crpix1    float       Reference pixel axis 1 (n=1 to naxis)
         crvaln    float       axis value at CRPIX1 (n=1 to naxis)
         ctypen    string      axis type 1 (n=1 to naxis0
         cdeltn    float       axis increment 1 (n=1 to naxis)
         cunitn    string      axis unit 1 (n=1 to naxis)
         equinox   string      equinox
         restfreq  float       rest frequency, Hz
         bmaj      float       beam major axis, radians
         bmin      float       beam minor axis, radians
         bpa       float       beam position angle, deg
         bunit     string      units of pixel values
         telescop  string      telescope name
         observer  string      observer name
         date-obs  string      date of observation
         datamax   float       maximum data value
         datamin   float       minimum data value
         badpixel  float       fraction of invalid pixels in the cube (a number between 0 and 1)
         vlsr      float       Object line-of-sight velocity (km/s)
        """
        # @todo the master list is in $ADMIT/admit/summary_defs.tab
        #       1) we duplicate that here....
        #       2) should it be with code?  or in $ADMIT/etc ?
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        # 
        self._summary = {}                  # prepare to make a summary here
        dt = utils.Dtime("Ingest")          # timer for debugging

        do_cbeam = True                     # enforce a common beam
        #
        pb = self.getkey('pb')
        do_pb = len(pb) > 0
        use_pb = self.getkey("usepb")
        # 
        create_mask = self.getkey('mask')   # create a new mask ?
        box   = self.getkey("box")          # corners in Z, XY or XYZ
        edge  = self.getkey("edge")         # number of edge channels to remove
        restfreq = self.getkey("restfreq")  # < 0 means not activated
        ckms  = utils.c                     # 299792.458 km/s

        # smooth=  could become deprecated, and/or include a decimation option to make it useful
        #          again, Smooth_AT() does this also , at the cost of an extra cube to store
        smooth = self.getkey("smooth")      # 
        #
        vlsr = self.getkey("vlsr")          # see also LineID, where this could be given again

        # first place a fits file in the admit project directory (symlink)
        # this is a bit involved, depending on if an absolute or relative path was
        # give to Ingest_AT(file=)
        fitsfile = self.getkey('file')
        if fitsfile[0] != os.sep:
            fitsfile = os.path.abspath(os.getcwd() + os.sep + fitsfile)
        logging.debug('FILE=%s' % fitsfile)
        if fitsfile[0] != os.sep:
            raise Exception,"Bad file=%s, expected absolute name",fitsfile

        # now determine if it could have been a CASA (or MIRIAD) image already 
        # which we'll assume if it's a directory; this is natively supported by CASA
        # but there are tools where if you pass it a FITS or MIRIAD
        # MIRIAD is not recommended for serious work, especially big files, since there
        # is a performance penalty due to tiling.
        file_is_casa = casautil.iscasa(fitsfile)

        loc = fitsfile.rfind(os.sep)               # find the '/'
        ffile0 = fitsfile[loc+1:]                  # basename.fits
        basename = self.getkey('basename')         # (new) basename allowed (allow no dots?)
        if len(basename) == 0:
            basename = ffile0[:ffile0.rfind('.')]  # basename
        logging.info("basename=%s" % basename)
        target = self.dir(ffile0)

        if not os.path.exists(target) :
            cmd = 'ln -s "%s" "%s"' % (fitsfile, target)
            logging.debug("CMD: %s" % cmd)
            os.system(cmd)

        readonly = False
        if file_is_casa:
            logging.debug("Assuming input %s is a CASA (or MIRIAD) image" % ffile0)
            bdpfile = self.mkext(basename,"im")
            if bdpfile == ffile0:
                logging.warning("No selections allowed on CASA image, since no alias was given")
                readonly = True
            b1  = SpwCube_BDP(bdpfile)
            self.addoutput(b1)
            b1.setkey("image", Image(images={bt.CASA:bdpfile}))
            # @todo b2 and PB?
        else:
            # construct the output name and construct the BDP based on the CASA image name
            # this also takes care of the behind the scenes alias= substitution
            bdpfile = self.mkext(basename,"im")
            if bdpfile == basename:
                raise Exception,"basename and bdpfile are the same, Ingest_AT needs a fix for this"
            b1  = SpwCube_BDP(bdpfile)
            self.addoutput(b1)
            if do_pb:
                print "doing the PB"
                bdpfile2 = self.mkext(basename,"pb")
                b2 = Image_BDP(bdpfile2)
                self.addoutput(b2)

        # @todo    we should also set readonly=True if no box, no mask etc. and still an alias
        #          that way it will speed up and not make a copy of the image ?

        # fni and fno are full (abspath) filenames, ready for CASA
        # fni is the same as fitsfile
        fni = self.dir(ffile0)
        fno = self.dir(bdpfile)
        if do_pb: fno2 = self.dir(bdpfile2)
        dt.tag("start")

        ia = taskinit.iatool()
        rg = taskinit.rgtool()
        
        if file_is_casa:
            ia.open(fni)
        else:
            if do_pb and use_pb:
                # @todo   this needs a fix for the path for pb, only works if abs path is given
                # impbcor(im.fits,pb.fits,out.im,overwrite=True,mode='m')
                if False:
                    # this may seem like a nice shortcut, to have the fits->casa conversion be done
                    # internally in impbcor, but it's a terrible performance for big cubes. (tiling?)
                    # we keep this code here, perhaps at some future time (mpi?) this performs better
                    # @todo fno2
                    impbcor(fni,pb,fno,overwrite=True,mode='m')
                    dt.tag("impbcor-1")
                else:
                    # the better way is to convert FITS->CASA and then call impbcor()
                    # the CPU savings are big, but I/O overhead can still be substantial
                    _pbcor = utils.tmp_file('_pbcor_','.')
                    _pb    = utils.tmp_file('_pb_',   '.')
                    ia.fromfits(_pbcor,fni,overwrite=True)
                    ia.fromfits(_pb,   pb, overwrite=True)
                    dt.tag("impbcor-1f")
                    if False:
                        impbcor(_pbcor,_pb,fno,overwrite=True,mode='m')
                        # @todo fno2
                        utils.remove(_pbcor)
                        utils.remove(_pb)
                        dt.tag("impbcor-2")
                    else:
                        # immath appears to be even faster (2x in CPU)
                        # https://bugs.nrao.edu/browse/CAS-8299
                        # @todo  this needs to be confirmed that impbcor is now good to go (r36078)
                        casa.immath([_pbcor,_pb],'evalexpr',fno,'IM0*IM1')
                        dt.tag("immath")
                        if True:
                            # use the mean of all channels... faster may be to use the middle plane
                            # barf; edge channels can be with fewer subfields in a mosaic 
                            ia.open(_pb)
                            s=ia.summary()
                            #ia1=taskinit.ia.moments(moments=[-1],drop=True,outfile=fno2)    # fails for cont maps
                            ia1=ia.collapse(outfile=fno2, function='mean', axes=2)  # @todo ensure 2=freq axis
                            ia1.done()
                            ia.close()
                            dt.tag("moments")
                        utils.remove(_pbcor)
                        utils.remove(_pb)
                        dt.tag("impbcor-3")
            elif do_pb and not use_pb:
                # cheat case: PB was given, but not meant to be used
                # not implemented yet
                print "cheat case dummy PB not implemented yet"
            else:
                # no PB given
                if False:
                    # re-running this was more consistently faster in wall clock time
                    # note that zeroblanks=True will still keep the mask
                    logging.debug("casa::ia.fromfits(%s) -> %s" % (fni,bdpfile))
                    ia.fromfits(fno,fni,overwrite=True)

                    #taskinit.ia.fromfits(fno,fni,overwrite=True,zeroblanks=True)
                    dt.tag("fromfits")
                else:
                    # not working to extend 3D yet, but this would solve the impv() 3D problem
                    logging.debug("casa::importfits(%s) -> %s" % (fni,bdpfile))
                    #casa.importfits(fni,fno,defaultaxes=True,defaultaxesvalues=[None,None,None,'I'])
                    # possible bug: zeroblanks=True has no effect?
                    casa.importfits(fni,fno,zeroblanks=True,overwrite=True)
                    dt.tag("importfits")
            ia.close()
            ia.open(fno)
            if len(smooth) > 0:
                # smooth here, but Smooth_AT is another option
                # here we only allow pixel smoothing
                # spatial: gauss
                # spectral: boxcar/hanning (check for flux conservation)
                #     is the boxcar wrong, not centered, but edged?
                # @todo CASA BUG:  this will loose the object name (and maybe more?) from header, so VLSR lookup fails
                fnos = fno + '.smooth'
                ia.convolve2d(outfile=fnos, overwrite=True, pa='0deg',
                                       major='%gpix' % smooth[0], minor='%gpix' % smooth[1], type='gaussian')
                ia.close()
                srcname = casa.imhead(fno,mode="get",hdkey="object")          # work around CASA bug
                #@todo use safer ia.rename() here.
                # https://casa.nrao.edu/docs/CasaRef/image.rename.html
                utils.rename(fnos,fno)
                casa.imhead(fno,mode="put",hdkey="object",hdvalue=srcname)    # work around CASA bug
                dt.tag("convolve2d")
                if len(smooth) > 2 and smooth[2] > 0:
                    if smooth[2] == 1:
                        # @todo only 1 channel option
                        specsmooth(fno,fnos,axis=2,function='hanning',dmethod="")
                    else:
                        # @todo may have the wrong center
                        specsmooth(fno,fnos,axis=2,function='boxcar',dmethod="",width=smooth[2])
                    #@todo use safer ia.rename() here.
                    # https://casa.nrao.edu/docs/CasaRef/image.rename.html
                    utils.rename(fnos,fno)
                    dt.tag("specsmooth")
                ia.open(fno)

            s = ia.summary()
            if len(s['shape']) != 4:
                logging.warning("Adding dummy STOKES-I axis")
                fnot = fno + '_4'
                ia2=ia.adddegaxes(stokes='I',outfile=fnot)
                ia.close()
                ia2.close()
                #@todo use safer ia.rename() here.
                # https://casa.nrao.edu/docs/CasaRef/image.rename.html
                utils.rename(fnot,fno)
                ia.open(fno)
                dt.tag("adddegaxes")
            else:
                logging.info("SHAPE: %s" % str(s['shape']))
        s = ia.summary()
        dt.tag("summary-0")
        if s['hasmask'] and create_mask:
            logging.warning("no extra mask created because input image already had one")
            create_mask = False

        # if a box= or edge= was given, only a subset of the cube needs to be ingested
        # this however complicates PB correction later on
        if len(box) > 0 or len(edge) > 0:
            if readonly:
                raise Exception,"Cannot use box= or edge=, data is read-only, or use an basename/alias"
            if len(edge) == 1:  edge.append(edge[0])

            nx = s['shape'][0]
            ny = s['shape'][1]
            nz = s['shape'][2]
            logging.info("box=%s edge=%s processing with SHAPE: %s" % (str(box),str(edge),str(s['shape'])))
                                                                                                 
            if len(box) == 2:
                # select zrange
                if len(edge)>0:
                    raise Exception,"Cannot use edge= when box=[z1,z2] is used"
                r1 = rg.box([0,0,box[0]] , [nx-1,ny-1,box[1]])
            elif len(box) == 4:
                if len(edge) == 0:
                    # select just an XY box
                    r1 = rg.box([box[0],box[1]] , [box[2],box[3]])
                elif len(edge) == 2:
                    # select an XY box, but remove some edge channels
                    r1 = rg.box([box[0],box[1],edge[0]] , [box[2],box[3],nz-edge[1]-1])
                else:
                    raise Exception,"Bad edge= for len(box)=4"
            elif len(box) == 6:
                # select an XYZ box
                r1 = rg.box([box[0],box[1],box[2]] , [box[3],box[4],box[5]])
            elif len(edge) == 2:
                # remove some edge channels, but keep the whole XY box
                r1 = rg.box([0,0,edge[0]] , [nx-1,ny-1,nz-edge[1]-1])
            else:
                raise Exception,"box=%s illegal" % box
            logging.debug("BOX/EDGE selection: %s %s" % (str(r1['blc']),str(r1['trc']))) 
            #if taskinit.ia.isopen(): taskinit.ia.close()

            logging.info("SUBIMAGE")
            subimage = ia.subimage(region=r1,outfile=fno+'.box',overwrite=True)
            ia.close()
            ia.done()
            subimage.rename(fno,overwrite=True)
            subimage.close()
            subimage.done()
            ia.open(fno)
            dt.tag("subimage-1")
        else:
            # the whole cube is passed onto ADMIT
            if readonly and create_mask:
                raise Exception,"Cannot use mask=True, data read-only, or use an alias"
            if file_is_casa and not readonly:
                # @todo a miriad file - which should be read only - will also create a useless copy here if no alias used
                ia.subimage(overwrite=True,outfile=fno)
                ia.close()
                ia.open(fno)
                dt.tag("subimage-0")

        if create_mask:
            if readonly:
                raise Exception,"Cannot create mask, data read-only, or use an alias"
            # also check out the 'fromfits::zeroblanks = False'
            # calcmask() will overwrite any previous pixelmask
            #taskinit.ia.calcmask('mask("%s") && "%s" != 0.0' % (fno,fno))
            ia.calcmask('"%s" != 0.0' % fno)
            dt.tag("mask")

        s = ia.summary()
        dt.tag("summary-1")

        # do a fast statistics (no median or robust)
        s0 = ia.statistics()
        dt.tag("statistics")
        if len(s0['npts']) == 0:
            raise Exception,"No statistics possible, are there valid data in this cube?"
        # There may be multiple beams per plane so we can't
        # rely on the BEAM's 'major', 'minor', 'positionangle' being present.
        # ia.commonbeam() is guaranteed to return beam parameters
        # if present
        if do_cbeam and 'perplanebeams' in s:
            # report on the beam extremities, need to loop over all, 
            # first and last don't need to be extremes....
            n = s['perplanebeams']['nChannels']
            ab0 = '*0'
            bb0 = s['perplanebeams']['beams'][ab0]['*0']
            bmaj0 = bb0['major']['value']
            bmin0 = bb0['minor']['value']
            beamd = 0.0
            for i in range(n):
                ab1 = '*%d' % i
                bb1 = s['perplanebeams']['beams'][ab1]['*0']
                bmaj1 = bb1['major']['value']
                bmin1 = bb1['minor']['value']
                beamd = max(beamd,abs(bmaj0-bmaj1),abs(bmin0-bmin1))
            logging.warning("MAX-BEAMSPREAD %f" % (beamd))
            #
            if True:
                logging.info("Applying a commonbeam from the median beam accross the band")
                # imhead is a bit slow; alternatively use ia.summary() at the half point for setrestoringbeam()
                h = casa.imhead(fno,mode='list')
                b = h['perplanebeams']['median area beam']
                ia.setrestoringbeam(remove=True)
                ia.setrestoringbeam(beam=b)
                commonbeam = ia.commonbeam()

            else:
                # @todo : this will be VERY slow - code not finished, needs renaming etc.
                #         this is however formally the better solution
                logging.warning("commmonbeam code not finished")
                cb = ia.commonbeam()
                ia.convolve2d(outfile='junk-common.im', major=cb['major'], minor=cb['minor'], pa=cb['pa'], 
                                       targetres=True, overwrite=True)
                dt.tag('convolve2d')
                commonbeam = {}
        else:
            try:
                commonbeam = ia.commonbeam()
            except:
                nppb = 4.0
                logging.warning("No synthesized beam found, faking one to prevent downstream problems: nppb=%f" % nppb)
                s = ia.summary()
                cdelt2 = abs(s['incr'][0]) * 180.0/math.pi*3600.0
                bmaj = nppb * cdelt2      # use a nominal 4 points per (round) beam 
                bmin = nppb * cdelt2
                bpa  = 0.0
                ia.setrestoringbeam(major='%farcsec' % bmaj, minor='%farcsec' % bmin, pa='%fdeg' % bpa)
                commonbeam = {}
        logging.info("COMMONBEAM[%d] %s" % (len(commonbeam),str(commonbeam)))

        first_point = ia.getchunk(blc=[0,0,0,0],trc=[0,0,0,0],dropdeg=True)
        logging.debug("DATA0*: %s" % str(first_point))

        ia.close()
        logging.info('BASICS: [shape] npts min max: %s %d %f %f' % (s['shape'],s0['npts'][0],s0['min'][0],s0['max'][0]))
        logging.info('S/N (all data): %f' % (s0['max'][0]/s0['rms'][0]))
        npix = 1
        nx = s['shape'][0]
        ny = s['shape'][1]
        nz = s['shape'][2]
        for n in s['shape']:
            npix = npix * n
        ngood = int(s0['npts'][0])
        fgood = (1.0*ngood)/npix
        logging.info('GOOD PIXELS: %d/%d (%f%% good or %f%% bad)' % (ngood,npix,100.0*fgood,100.0*(1 - fgood)))
        if s['hasmask']:
            logging.warning('MASKS: %s' % (str(s['masks'])))

        if not file_is_casa:
            b1.setkey("image", Image(images={bt.CASA:bdpfile}))
            if do_pb:
                b2.setkey("image", Image(images={bt.CASA:bdpfile2}))            

        # cube sanity: needs to be either 4D or 2D. But p-p-v cube
        # alternative: ia.subimage(dropdeg = True)
        # see also: https://bugs.nrao.edu/browse/CAS-5406
        shape = s['shape']
        if len(shape)>3:
            if shape[3]>1:
                # @todo this happens when you ingest a fits or casa image which is ra-dec-pol-freq
                if nz > 1:
                    msg = 'Ingest_AT: cannot deal with real 4D cubes yet'
                    logging.critical(msg)
                    raise Exception,msg
                else:
                    # @todo this is not working yet when the input was a casa image, but ok when fits. go figure.
                    fnot = fno + ".trans"
                    if True:
                        # this works
            #@todo use safer ia.rename() here.
            # https://casa.nrao.edu/docs/CasaRef/image.rename.html
                        utils.rename(fno,fnot)
                        imtrans(fnot,fno,"0132")
                        utils.remove(fnot)
                    else:
                        # this does not work, what the heck
                        imtrans(fno,fnot,"0132")
            #@todo use safer ia.rename() here.
            # https://casa.nrao.edu/docs/CasaRef/image.rename.html
                        utils.rename(fnot,fno)
                    nz = s['shape'][3]
                    # get a new summary 's'
                    ia.open(fno)
                    s = ia.summary()
                    ia.close()
                    logging.warning("Using imtrans, with nz=%d, to fix axis ordering" % nz)
                    dt.tag("imtrans4")
            # @todo  ensure first two axes are position, followed by frequency
        elif len(shape)==3:
            # the current importfits() can do defaultaxes=True,defaultaxesvalues=['', '', '', 'I']
            # but then appears to return a ra-dec-pol-freq cube
            # this branch probably never happens, since ia.fromfits() will 
            # properly convert a 3D cube to 4D now !!
            # NO: when NAXIS=3 but various AXIS4's are present, that works. But not if it's pure 3D
            # @todo  box=
            logging.warning("patching up a 3D to 4D cube")
            raise Exception,"SHOULD NEVER GET HERE"
            fnot = fno + ".trans"
            casa.importfits(fni,fnot,defaultaxes=True,defaultaxesvalues=['', '', '', 'I'])
            utils.remove(fno)        # ieck
            imtrans(fnot,fno,"0132")
            utils.remove(fnot)
            dt.tag("imtrans3")

        logging.regression('CUBE: %g %g %g  %d %d %d  %f' % (s0['min'],s0['max'],s0['rms'],nx,ny,nz,100.0*(1 - fgood)))

        # if the cube has only 1 plane (e.g. continuum) , create a visual (png or so)
        # for 3D cubes, rely on something like CubeSum
        if nz == 1:
            implot = ImPlot(pmode=self._plot_mode,ptype=self._plot_type,abspath=self.dir())
            implot.plotter(rasterfile=bdpfile,figname=bdpfile)
            # @todo needs to be registered for the BDP, right now we only have the plot

        # ia.summary() doesn't have this easily available, so run the more expensive imhead()
        h = casa.imhead(fno,mode='list')
        telescope = h['telescope']
        # work around CASA's PIPELINE bug/feature?   if 'OBJECT' is blank, try 'FIELD'
        srcname = h['object']
        if srcname == ' ':
            logging.warning('FIELD used for OBJECT')
            srcname = casa.imhead(fno,mode='get',hdkey='field')
            if srcname == False:
                # if no FIELD either, we're doomed.  yes, this did happen.
                srcname = 'Unknown'
            casa.imhead(fno,mode="put",hdkey="object",hdvalue=srcname)
            h['object'] = srcname
        logging.info('TELESCOPE: %s' % telescope)
        if telescope == 'UNKNOWN':
            msg = 'Ingest_AT: warning, an UNKNOWN telescope often results in ADMIT failing'
            logging.warning(msg)
        logging.info('OBJECT: %s' % srcname)
        logging.info('REFFREQTYPE: %s' % h['reffreqtype'])
        if h['reffreqtype'].find('TOPO')>=0:
            msg = 'Ingest_AT: cannot deal with cubes with TOPOCENTRIC frequencies yet - winging it'
            logging.warning(msg)
            #raise Exception,msg
        # Ensure beam parameters are available if there are multiple beams
        # If there is just one beam, then we are just overwriting the header
        # variables with their identical values.
        if len(commonbeam) != 0:
            h['beammajor'] = commonbeam['major']
            h['beamminor'] = commonbeam['minor']
            h['beampa']    = commonbeam['pa']
        # cheat add some things that need to be passed to summary....
        h['badpixel'] = 1.0-fgood
        if vlsr < -999998.0:
            vlsr          = admit.VLSR().vlsr(h['object'].upper())
            if vlsr == 0.0:
                vlsr = -999999.99
        h['vlsr']     = vlsr
        logging.info("VLSR = %f (from source catalog)" % vlsr)
        
        taskargs = "file=" + fitsfile
        if create_mask == True:
            taskargs = taskargs + " mask=True" 
        if len(box) > 0:
            taskargs = taskargs + " " + str(box)
        if len(edge) > 0:
            taskargs = taskargs + " " + str(edge)
        r2d = 57.29577951308232
        logging.info("RA   Axis 1: %f %f %f" % (h['crval1']*r2d,h['cdelt1']*r2d*3600.0,h['crpix1']))
        logging.info("DEC  Axis 2: %f %f %f" % (h['crval2']*r2d,h['cdelt2']*r2d*3600.0,h['crpix2']))
        if nz > 1:
            # @todo check if this is really a freq axis (for ALMA it is, but...)
            t3 = h['ctype3']
            df = h['cdelt3']
            fc = h['crval3'] + (0.5*(float(shape[2])-1)-h['crpix3'])*df        # center freq; 0 based pixels
            if 'restfreq' in h:
                fr = float(h['restfreq'][0])           # casa cheats, it may put 0 in here if FITS is missing it
                if fr == 0.0:
                    fr = fc
                else:
                    if vlsr < -999998.0:
                        vlsr = (1-fc/fr)*ckms
                        h['vlsr'] = vlsr
            else:
                fr = fc
            fw = df*float(shape[2])
            print "PJT:",fr/1e9,fc/1e9,fw/1e9
            dv = -df/fr*ckms
                
            logging.info("Freq Axis 3: %g %g %g" % (h['crval3']/1e9,h['cdelt3']/1e9,h['crpix3']))
            logging.info("Cube Axis 3: type=%s  velocity increment=%f km/s @ fc=%f fw=%f GHz" % (t3,dv,fc/1e9,fw/1e9))
        # @todo sort out this restfreq/vlsr
        # report 'reffreqtype', 'restfreq' 'telescope'
        # if the fits file has ALTRVAL/ALTRPIX, this is lost in CASA?
        # but if you do fits->casa->fits , it's back in fits (with some obvious single precision loss of digits)
        # @todo ZSOURCE is the proposed VLSR slot in the fits header, but this has frame issues (it's also optical)
        #
        # Another method to get the vlsr is to override the restfreq (f0) with an AT keyword
        # and the 'restfreq' from the header (f) is then used to compute the vlsr:   v = c (1 - f/f0)
        #
        if shape[2] > 1 and 'restfreq' in h:
            logging.info("RESTFREQ: %g %g %g" % (fr/1e9,h['restfreq'][0]/1e9,restfreq))
            if shape[2] > 1:
                # v_radio of the center of the window w.r.t. restfreq
                vlsrc = ckms*(1-fc/fr)     # @todo rel frame?
                vlsrw = dv*float(shape[2])
                if restfreq > 0:
                    vlsrf = ckms*(1-fr/restfreq/1e9)
                    h['vlsr'] = vlsrf
                else:
                    vlsrf = 0.0
                logging.info("VLSRc = %f  VLSRw = %f  VLSRf = %f VLSR = %f" % (vlsrc, vlsrw, vlsrf, vlsr))
                if h['vlsr'] == 0.0: # @todo! This fails if vlsr actually is zero. Need another magic number
                    h['vlsr'] = vlsrc
                    logging.warning("Warning: No VLSR found, substituting VLSRc = %f" % vlsrc)
        else:
            msg = 'Ingest_AT: missing RESTFREQ'
            print msg
        # @todo   LINTRN  is the ALMA keyword that designates the expected line transition in a spw

        self._summarize(fitsfile, bdpfile, h, shape, taskargs)

        dt.tag("done")
        dt.end()

    def _summarize(self, fitsname, casaname, header, shape, taskargs):
        """Convenience function to populate dictionary for
           items to add to the ADMIT Summary. The contract
           function is self.summary(), called by AT()

        """

        self._summary = {}
        self._summary['fitsname'] = SummaryEntry(fitsname)
        self._summary['casaname'] = SummaryEntry(casaname)

        # these are one-to-one match keywords 
        easy = [ 'object'  , 'equinox', 
                 'observer', 'date-obs',   'datamax', 
                 'datamin' , 'badpixel',   'vlsr',
               ]

        naxis = len(shape)
        self._summary['naxis'] = SummaryEntry(naxis)
        for i in range(naxis):
            j = i+1
            jay = str(j)
            easy.append('crpix'+jay)
            easy.append('ctype'+jay)
            easy.append('crval'+jay)
            easy.append('cdelt'+jay)
            easy.append('cunit'+jay)
            self._summary['naxis'+jay] = SummaryEntry(int(shape[i]))

        # FITS is only 8 chars.
        if 'telescope' in header:
            self._summary['telescop'] = SummaryEntry(header['telescope'])

        if 'imtype' in header:
            self._summary['bunit'] = SummaryEntry(header['bunit'])

        for k in easy:
            if k in header:
                self._summary[k] = SummaryEntry(header[k])

        if 'restfreq' in header:
            self._summary['restfreq']  = SummaryEntry(header['restfreq'][0])
            
        # These are in imhead returned as dictionaries {'unit','value'} 
        # so we have to munge them

        # convert beam parameters
        qa = taskinit.qatool()
        if 'beampa' in header:
            self._summary['bpa']  = SummaryEntry(qa.convert(header['beampa'],'deg')['value'])
        if 'beammajor' in header:
            self._summary['bmaj'] = SummaryEntry(qa.convert(header['beammajor'],'rad')['value'])
        if 'beamminor' in header:
            self._summary['bmin'] = SummaryEntry(qa.convert(header['beamminor'],'rad')['value'])
        
        # Now tag all summary items with task name and task ID.

        for k in self._summary:
            self._summary[k].setTaskname("Ingest_AT")
            self._summary[k].setTaskID(self.id(True))
            self._summary[k].setTaskArgs(taskargs)
