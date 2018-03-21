""" .. _LineCube-at-api:

   **LineCube_AT** --- Cuts a cube into one or more line-oriented cubes.
   ---------------------------------------------------------------------

   This module defines the LineCube_AT class.
"""
# ADMIT imports
from admit.AT import AT
from admit.Summary import SummaryEntry
import admit.util.bdp_types as bt
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.LineList_BDP import LineList_BDP
from admit.bdp.LineCube_BDP import LineCube_BDP
from admit.util.Line import Line
from admit.util.Image import Image
import admit.util.Table
import admit.util.utils as utils
from admit.util.AdmitLogging import AdmitLogging as logging


# CASA imports
try:
    from imsubimage import imsubimage
    from imrebin import imrebin
    from casa import imhead
except:
    print "WARNING: No CASA; LineCube task cannot function."

# system imports
import os
import math

# @todo
# - use CoordSys tool and setrestfrequency to set the restfreq per linecube
# - the current code cannot make cubes with equal velocity gridding
#   the cheat is that as long as bandwidth not too wide, it's about right
#   but to compare between bands, this will not work anymore, or even USB/LSB?


class LineCube_AT(AT):
    """ AT for generating a subcube of s specific spectral line.

        See also :ref:`LineCube-AT-design` for design documentation.

        The produced LineCube_BDP(s) holds a spectral cube for each of the 
        specified spectral lines.

        **Keywords**
          **pad**: int
            Extra channels added on either side of a line (as given by
            the LineList).  If a negative number is given, its
            positive value will be the number of channels of each
            linecube.  This keyword has no meaning when gridding in
            velocity space is done.
            Default: 5 (add 5 channels to both sides of the line).

          **fpad**: float
            An optional way to control the padding would be to specify the
            fraction of the current line segment that is going to be added
            on either side of the segment. This would override the pad=
            keyword. 
            Default: -1 (meaning not used)

          **equalize**: bool
            Whether or not to create equal size cubes (based on widest line
            in input LineList_BDP).
            These cubes will be padded based on the value of pad.
            Default: False.

        **Input BDPs**

          **Image_BDP**: count: 1
            Spectral cube from which the line cube is sliced, as from an
            `Ingest_AT <Ingest_AT.html>`_ or 
            `ContinuumSub_AT <ContinuumSub_AT.html>`_.

          **LineList_BDP**: count: 1
            List of spectral lines to cut (including the channel ranges),
            typically the output of a `LineID_AT <LineID_AT.html>`_.

        **Output BDPs**

          **LineCube_BDP**: count: `varies`
            The image slices of each spectral line (one for each).

        Parameters
        ----------
        keyval : dictionary of keyword:value pairs, optional
          Keyword values.

        Attributes
        ----------
        _version : string
          Version information.

    """
    def __init__(self, **keyval):
        keys = {"equalize" : False,  # default to no equalization and no regridding
                "pad"      : 5,      # default to 5 channels on either side
                "fpad"     : -1.0,   # optional fractional linesegment width padding
                }
        AT.__init__(self, keys, keyval)
        self._version = "1.0.3"
        self.set_bdp_in([(Image_BDP,     1, bt.REQUIRED),
                         (LineList_BDP,  1, bt.REQUIRED)])
        self.set_bdp_out([(LineCube_BDP, 0)])

    def summary(self):
        """Returns the summary dictionary for LineCube_AT".
        """
        if hasattr(self, "_summary"):
            return self._summary
        else:
            return {}

    def run(self):
        """ The run method, creates the slices, regrids if requested, and 
            creates the BDP(s)

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        dt = utils.Dtime("LineCube")
        self._summary = {}
        # look for an input noise level, either through keyword or input 
        # CubeStats BDP or calculate it if needed
        pad  = self.getkey("pad")
        fpad = self.getkey("fpad")
        equalize = self.getkey("equalize")
        minchan = 0

        linelist = self._bdp_in[1]
        if linelist == None or len(linelist) == 0:
            logging.info("No lines found in input LineList_BDP, exiting.")
            return

        spw = self._bdp_in[0]
        # get the columns from the table
        cols = linelist.table.getHeader()
        # get the casa image
        imagename = spw.getimagefile(bt.CASA)
        imh = imhead(self.dir(imagename), mode='list')
        # set the overall parameters for imsubimage
        args = {"imagename" : self.dir(imagename),
                "overwrite" : True}

        dt.tag("start")

        if pad != 0 or fpad > 0:
            nchan = imh['shape'][2]
            dt.tag("pad") 

        # if equal size cubes are requested, this will honor the requested pad
        if equalize:
            start = linelist.table.getColumnByName("startchan")
            end = linelist.table.getColumnByName("endchan")
            # look for the widest line
            for i in range(len(start)):
                diff = end[i] - start[i] + 1
                if fpad > 0:
                    minchan = max(minchan , diff * int(1+ 2*fpad))
                else:
                    minchan = max(minchan , diff + (2*pad))
            dt.tag("equalize")

        # get all of the rows in the table
        rows = linelist.getall()
        delrow = set()
        procblend = [0]
        # search through looking for blended lines, leave only the strongest from each blend
        # in the list
        for i, row in enumerate(rows):
            if row.blend in procblend:
                continue
            strongest = -100.
            index = -1
            indexes = []
            blend = row.blend
            for j in range(i, len(rows)):
                if rows[j].blend != blend:
                    continue
                indexes.append(j)
                if rows[j].linestrength > strongest:
                    strongest = rows[j].linestrength
                    index = j
            indexes.remove(index)
            delrow = delrow | set(indexes)
            procblend.append(blend)
        dr = list(delrow)
        dr.sort()
        dr.reverse()
        for row in dr:
            del rows[row]

        # check on duplicate UID's, since those are the directory names here
        uid1 = []
        for row in rows:
            uid1.append(row.getkey("uid"))
        uid2 = set(uid1)
        if len(uid1) != len(uid2):
            print "LineList:",uid1
            logging.warning("There are duplicate names in the LineList")
            #raise Exception,"There are duplicate names in the LineList"

        # Create Summary table
        lc_description = admit.util.Table()
        lc_description.columns = ["Line Name","Start Channel","End Channel","Output Cube"]
        lc_description.units   = ["","int","int",""]
        lc_description.description = "Parameters of Line Cubes"
        # loop over all entries in the line list
        rdata = []
        for row in rows:
            uid = row.getkey("uid")
            cdir = self.mkext(imagename,uid)
            self.mkdir(cdir)
            basefl = uid
            lcd = [basefl]
            outfl = cdir + os.sep + "lc.im"
            args["outfile"] = self.dir(outfl)
            start = row.getkey("startchan")
            end = row.getkey("endchan")
            diff = end - start + 1
            startch = 0
            if diff < minchan:
                add = int(math.ceil(float(minchan - diff) / 2.0))
                start -= add
                end += add
                startch += add
                if start < 0:
                    logging.info("%s is too close to the edge to encompass with the "
                          + "requested channels, start=%d resetting to 0" % 
                          (uid, start))
                    startch += abs(start)
                    start = 0
                if end >= nchan:
                    logging.info("%s is too close to the edge to encompass with the "
                          + "requested channels, end=%d resetting to %d" % 
                          (uid, end, nchan - 1))
                    end = nchan - 1
                #print "\n\nDIFF ",startch,"\n\n"
            if not equalize:
                if fpad > 0:
                    diff   = end - start + 1
                    start -= int(fpad*diff)
                    end   += int(fpad*diff)
                    if start < 0:
                        logging.warning("fpad=%d too large, start=%d resetting to 0"
                              % (int(fpad*diff), start))
                        startch += abs(start)
                        start = 0
                    else:
                        startch += int(fpad*diff)
                    if end >= nchan:
                        logging.warning("fpad=%d too large, end=%d resetting to %d"
                              % (int(fpad*diff), end, nchan - 1))
                        end = nchan - 1
                elif pad > 0:
                    start -= pad
                    end += pad
                    if start < 0:
                        logging.warning("pad=%d too large, start=%d resetting to 0"
                              % (pad, start))
                        startch += abs(start)
                        start = 0
                    else:
                        startch += pad
                    if end >= nchan:
                        logging.warning("pad=%d too large, end=%d resetting to %d"
                              % (pad, end, nchan - 1))
                        end = nchan - 1
                elif pad < 0:
                    mid = (start + end) / 2
                    start = mid + pad / 2
                    end = mid - pad / 2 - 1
                    if start < 0:
                        logging.warning("pad=%d too large, start=%d resetting to 0"
                              % (pad, start))
                        startch += abs(start)
                        start = 0
                    else:
                        startch += abs(start)
                    if end >= nchan:
                        logging.warning("pad=%d too large, end=%d resetting to %d"
                              % (pad, end, nchan - 1))
                        end = nchan - 1
            endch = startch + diff
            args["chans"] = "%i~%i" % (start, end)
            rdata.append(start)
            rdata.append(end)
            # for the summmary, which will be a table of
            # Line name, start channel, end channel, output image
            lc_description.addRow([basefl, start, end, outfl])

            # create the slices
            imsubimage(**args)

            line = row.converttoline()
            # set the restfrequency ouf the output cube
            imhead(imagename=args["outfile"], mode="put", hdkey="restfreq", 
                   hdvalue="%fGHz" % (row.getkey("frequency")))
            # set up the output BDP
            images = {bt.CASA : outfl}
            casaimage = Image(images=images)
            # note that Summary.getLineFluxes() implicitly relies on the BDP out order
            # being the same order as in the line list table.  If this is ever not
            # true, then Summary.getLineFluxes mismatch BDPs and flux values.
            #self.addoutput(LineCube_BDP(xmlFile=cdir + os.sep + basefl + ".lc",
            self.addoutput(LineCube_BDP(xmlFile=outfl,
                           image=casaimage, line=line, linechans="%i~%i" % (startch, endch)))
            dt.tag("trans-%s" % cdir)

        logging.regression("LC: %s" % str(rdata))

        taskargs = "pad=%s fpad=%g equalize=%s" % (pad, fpad, equalize)

        self._summary["linecube"] = SummaryEntry(lc_description.serialize(), "LineCube_AT",
                                                 self.id(True), taskargs)
        dt.tag("done")
        dt.end()
