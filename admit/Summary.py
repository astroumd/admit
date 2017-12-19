#!/usr/bin/env python
""".. _Summary-api:

   **Summary** --- Project summary metadata.
   -----------------------------------------

   This module defines the Summary class.
"""

import os
import admit.xmlio.XmlWriter as XmlWriter
import xml.etree.cElementTree as et
import admit.util.bdp_types as bt
import admit.util.utils as utils
import admit.util.Table
import datetime
import math
import json
import uuid
from admit.util.AdmitLogging import AdmitLogging as logging

class Summary():
    """ 
        Defines and manages the summary metadata for the ADMIT object,
        which is ingested by ALMA Archive  and also used by data browser.


        The Summary is metadata provided by the various tasks.  and written
        to the ADMIT object and admit.xml.  It is used as project information
        for the ALMA archive to ingest and for the data browser to display.
        There will be one summary object per FITS cube, which means that
        for flows with multiple Ingests there can be multiple Summaries.
        Each entry in the Summary will be a dictionary of 

        `{ key, [ SummaryEntry ]  }` 

        where the value is a list of zero or more SummaryEntry.  The summaryEntry
        contains the actual data value, the taskname string, the taskid integer,
        and string task arguments to be displayed in the web page.
        Each key also has a value type and description which is the same for
        every entry in the list.  These are retrieved using getType(key)
        and getDescription(key).  In the case where different tasks
        or different instances of the same task write to the same key,
        the new value will be appended:

        `{ key, [SummaryEntry task1, SummaryEntry task2,...]}`

        Because they are needed by the ALMA archive, the keys, value types,
        and description will be strictly defined ahead of time.  Individual ATs
        will be responsible for providing the actual value data through their
        summary() method as a dictionary of {key, [value, taskname, taskid]}.
        ADMIT Summary keywords that map directly to standard FITS keywords
        shall have their values copied directly from the FITS header (by
        Ingest_AT).  Below is a draft list, necessarily incomplete until we
        have all ATs implemented.  Keywords ending in `n` indicate multiple
        keywords 1 to NAXIS (as in FITS).  The table below summarizes the keys.

        .. table::
           :class: borderless
           
           +---------+----------------------------+----------------+---------------------+
           | Key     |   Description              |      Type      |  Typically          |
           |         |                            |                |  Provided by        |
           +=========+============================+================+=====================+
           |FITSNAME | Pathless filename of       |                |                     | 
           |         | FITS cube                  |      string    |  Ingest_AT          |
           +---------+----------------------------+----------------+---------------------+
           |OBJECT   | Object name                |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |NAXIS    | Number of Axes             |      integer   |  Ingest_AT/FITS     | 
           +---------+----------------------------+----------------+---------------------+
           |NAXISn   | size of axis n             |      integer   |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |CRPIXn   | Reference pixel axis n     |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |CRVALn   | axis value at CRPIXn       |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |CTYPEn   | axis type                  |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |CDELTn   | axis increment             |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |CUNITn   | axis unit                  |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |RESTFREQ | rest frequency, Hz         |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |BMAJ     | beam major axis, radians   |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |BMIN     | beam minor axis, radians   |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |BPA      | beam position angle, deg   |      float     |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |BUNIT    | units of pixel values      |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |TELESCOP | telescope name             |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |OBSERVER | observer name              |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |DATE-OBS | date of observation        |      string    |  Ingest_AT/FITS     |
           +---------+----------------------------+----------------+---------------------+
           |DATAMAX  | maximum data value         |      float     | Ingest_AT or        |
           |         |                            |                | CubeStats_AT        |
           +---------+----------------------------+----------------+---------------------+
           |DATAMIN  | minimum data value         |      float     | Ingest_AT or        |
           |         |                            |                | CubeStats_AT        |
           +---------+----------------------------+----------------+---------------------+
           |DATAMEAN | mean data value            |      float     |  CubeStats_AT       |
           +---------+----------------------------+----------------+---------------------+
           |DYNRANGE | dynamic range, equal to    |      float     |  CubeStats_AT       |
           |         | DATAMAX/CHANRMS            |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |CHANRMS  | one-sigma noise in cube    |      float     |  CubeStats_AT       |
           +---------+----------------------------+----------------+---------------------+
           |RMSMETHD | method and parameters used |      list      |  CubeStats_AT       |
           |         | to compute RMS             |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |SPECTRA  | Spectra extracted by       |     list       | CubeSpectrum_AT     |
           |         | any method                 |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |LINELIST | Table of parameters of     |admit.util.Table| LineID_AT           |
           |         | identified spectral lines. |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |LINECUBE | Info about any LineCubes   |   list         |  LineCube_AT        |
           |         | produced (name, channel    |                |                     |
           |         | range, image name).        |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |CUBESUM  | Info about any CubeSum     |   list         |  CubeSum_AT         |
           |         | produced                   |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |MOMENTS  | Table of moments computed  |admit.util.Table| Moment_AT           |
           |         | from the original cube.    |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |PVSLICES |Table of position-velocity  |   list         | PVSlice_AT          |
           |         |slices computed from        |                |                     |
           |         |original cube.              |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |PVCORR   |List of PV correlation      |   list         | PVCorr_AT           |
           |         |diagrams computed from input|                |                     |
           |         |cube.                       |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |SEGMENTS | List of segments found by  |   list         | LineSegment_AT      |
           |         | segment-finding algorithm  |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |SOURCES  | Table of sources found by a|admit.util.Table| SFind2D_AT          |
           |         | feature-finding algorithm  |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |SMOOTH   | Info about any smoothing   |   list         | Smooth_AT           |
           |         | done to cube.              |                |                     |
           +---------+----------------------------+----------------+---------------------+
           |OVERLAP  | Overlap integral input and |   list         | OverlapIntegral_AT  |
           |         | output images information  |                |                     |
           +---------+----------------------------+----------------+---------------------+
           | PCA     |Principal component analysis|list of         |PrincipalComponent_AT| 
           |         |information.                |admit.util.Table|                     |
           +---------+----------------------------+----------------+---------------------+
           | PEAKPNT |Peak Point Plot optionally  |   list         | CubeStats_AT        |
           |         |produced by CubeStats_AT    |                |                     |
           +---------+----------------------------+----------------+---------------------+
           | VELDEF  |User or ASDM/source.xml     |   list         | Ingest_AT?          |
           |         |derived source velocity     |                |                     |
           |         |information (value,         |                |                     |
           |         |reference frame, etc)       |                |                     |
           +---------+----------------------------+----------------+---------------------+

        *@TODO:* the following entries are in the summary_defs.tab file, but not documented here:
         

        *Note:* Keys are stored in all lower case.  All key access will change argument to lower case before
        accessing.

        casaname, equinox, badpixel, vlsr, continuumsub, template, regrid, bdpingest

        .. table::
           :class: borderless

           +----------------------------------------------------------------------------------------------------+
           | FORMATS AND EXAMPLES OF COMPLICATED SUMMARIES                                                      |
           +====================================================================================================+
           | RMSMETHD: `[[method type, method args], input cube]`                                               |
           |                                                                                                    |
           | Examples::                                                                                         |
           |                                                                                                    |
           |   [['metabdevmed'], foobar.im]                                                                     |
           |   [['robust', 'chauvenet', 21.3, 123], foobar.im]                                                  |
           |   [['robust', 'classic', 'auto'], foobar.im]                                                       |
           +----------------------------------------------------------------------------------------------------+
           | SPECTRA: `[x,y, box, axis type, display image, thumbnail image, caption, input cube]`              |
           |                                                                                                    |
           | Example::                                                                                          |
           |                                                                                                    |
           |  [[ '00h47m33.159s','-25d17m17.41s',(10,-10,-20,22),'frequency','spect1.svg','spect1_thumb.svg',   |
           |     "Spectrum at Emission Peak", foobar.im],                                                       |
           |  [ +10,-20,(),'velocity','spect.svg','spect2_thumb.svg', "Pencil beam spectrum", foobar.im]]       |
           +----------------------------------------------------------------------------------------------------+
           | LINELIST:  [Format same as output from LineList_AT]                                                |
           |                                                                                                    |
           | Example::                                                                                          |
           |                                                                                                    |
           | [['H2CS_103.0405',  103.04055,'H2CS', ...],                                                        |
           | ['NH2CHO_102.0643',102.06427, 'NH2CHO', ...]]                                                      |
           +----------------------------------------------------------------------------------------------------+
           | MOMENTS:  [table of moment data ]                                                                  |
           |                                                                                                    |
           | Columns: `[Line UID, Moment value, display image, thumbnail image, caption,  casa image].`         |
           |                                                                                                    |
           | If thumbnail image is not present, an empty string is given.                                       |
           |                                                                                                    |
           | Example::                                                                                          |
           |                                                                                                    |
           | [['H2CS_103.0405', 0, 'foo_mom0.png', 'foo_mom0_thumb.png', 'Moment 0 of H2CS', ''],               |
           | ['H2CS_103.0405', 1, 'foo_mom1.svg', '', 'Moment 1 of H2CS clipped at 3 sigma', 'foobar_mom1.im']] |
           +----------------------------------------------------------------------------------------------------+
           | PVSLICES:                                                                                          |
           | `[pvslice type, pvslice args, display image, thumbnail image, caption, input cube, output image].` |
           |                                                                                                    |
           | Example::                                                                                          |
           |                                                                                                    |
           |  [['slice', start, end, width, 'slice1.png', 'slice1_thumb.png','pvslice of h2co','foobar.im',     | 
           |     'slice.im'],                                                                                   |
           |  ['slit', center, length, pa, width, 'slit1.png', 'slit1_thumb.png', 'pvslit of h2co','foobar.im', |
           |     'slit.im']]                                                                                    |
           +----------------------------------------------------------------------------------------------------+
           | PVCORR:                                                                                            |
           | `[display image, thumbnail image, caption, input cube, output image].`                             |
           |                                                                                                    |
           +----------------------------------------------------------------------------------------------------+


        Attributes
        ----------
        _metadata : dictionary of lists {key, [SummaryEntry]}.  
        _datatype : dictionary of {key, valuetype} where the keys are the as in _metadata and valuetype is defined in $ADMIT/etc/summary_defs.tab
        _description : dictionary of {key, description} where the keys are the as in _metadata and description string is defined in $ADMIT/etc/summary_defs.tab

    """
    def __init__(self):
       self._metadata = {}
       self._datatype = {}
       self._description = {}
       self._startup()
       self._type = bt.SUMMARY

    def getFull(self, key):
        """Get the full entry [[value(s)], valuetype, description] for 
           the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.
        """
        retval = [self._metadata[key.lower()]]
        retval.append(self.getType(key))
        retval.append(self.getDescription(key))
        return retval

    def get(self,key):
        """Get the value for the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

        """
        return self._metadata.get(key.lower(),None)


    def getTaskname(self,key):
        """Get the name of the task that produced the data 
           for the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

           Returns
           -------
           List of zero or more string task names that produced data for the
           input key.  If no tasks did, the list is empty.
        """
        val = self.get(key)
        tasknames = []
        for x in val:
            tasknames.append(x.taskname)
        return tasknames
            

    def getAllTaskIDs(self):
        """Get a list of all integer task IDs that have written to this Summary
           for the input key.
        
           Parameters
           ----------
           None

           Returns
           ----------
           Sorted list of zero or more integer task ids that produced data for the Summary.  
           If no tasks ids, the list is empty because you have empty Summary!
        """
        taskids = []
        for k in self._metadata:
           taskids.extend(self.getTaskID(k))

        # sorted might not be necessary for a set of integers,
        # but I think there is no guarantee that set is in sort order
        return sorted(list(set(taskids)))

    def getTasknameForTaskID(self,taskid):
        """Get the task name matching the input taskid.
           
           Parameters
           ----------
           taskid : int
              Task ID to look up

           Returns 
           -------
           String task name or empty string if no match
        """
        for k in self._metadata:
            for p in self._metadata[k]:
               if p.taskid == taskid:
                  return p.taskname

        return ""

    def getTaskIDsforTaskname(self,taskname):
        """Get the task ID(s) matching the input taskname.
           
           Parameters
           ----------
           taskname : str
              Task name to look up

           Returns 
           -------
           List of taskids matching the taskname. Empty list if none.
        """
        taskids = []
        for k in self._metadata:
            for p in self._metadata[k]:
               if p.taskname == taskname:
                  taskids.append(p.taskid)

        return taskids

    def getTaskID(self,key):
        """Get the integer task ID number that produced the data 
           for the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

           Returns
           ----------
           List of zero or more integer taskids that produced data for the
           input key.  If no tasks did, the list is empty.

        """
        val = self.get(key)
        taskids = []
        for x in val:
            # don't include unset keys
            if x.unset(): continue
            taskids.append(x.taskid)
        return taskids

    def getItemsByTaskname(self,taskname):
        """Return all Summary items that were produced 
           by the given task, as dict of SummaryEntrys
           
           Parameters
           ----------
           taskname : str
              Task name to look up, case-insensitive

           Returns 
           -------
           Return a dictionary of all SummaryEntrys that were produced 
           by the given task, with keys as in Summary or an empty
           dictionary if there is no match for the input taskid.

           Notes
           -----
           The values in the returned dictionary may be single SummaryEntry
           instances or a list of entries; in general, caller code needs to
           check this explicitly for every key...
        """
        matched = {}
        tnlower = taskname.lower()
        for k in self._metadata:
            for p in self._metadata[k]:
               if p.taskname.lower() == tnlower:
                   if k in matched: 
                       if type(matched[k]) == list:
                           matched[k].append(p)
                       else:
                           matched[k] = [matched[k], p]
                   else:
                       # should this be [p]??
                       matched[k] = p

        return matched

    def getItemsByTaskID(self,taskid):
        """Return all Summary items that were produced 
           by the given taskid, as dict of SummaryEntrys
           
           Parameters
           ----------
           taskid : int
              Task ID to look up

           Returns 
           -------
           Return a dictionary of all SummaryEntrys that were produced 
           by the given task, with keys as in Summary or an empty
           dictionary if there is no match for the input taskid.

           Notes
           -----
           The values in the returned dictionary may be single SummaryEntry
           instances or a list of entries; in general, caller code needs to
           check this explicitly for every key...
        """
        matched = {}
        for k in self._metadata:
            for p in self._metadata[k]:
               if p.taskid == taskid:
                   if k in matched: 
                       if type(matched[k]) == list:
                           matched[k].append(p)
                       else:
                           matched[k] = [matched[k], p]
                   else:
                       matched[k] = p

        return matched

    def delItemsByTaskID(self,taskid):
        """Deletes all summary entries belonging to task #`taskid`.
           
           Parameters
           ----------
           taskid : int
              ID of task for which to delete summary information.

           Returns 
           -------
           None
        """
        delkeys = []
        for key in self._metadata:
            keep = []
            for p in self._metadata[key]:
                if p.taskid != taskid: keep.append(p)
            if keep:
                self._metadata[key] = keep
            else:
                delkeys.append(key)

        for key in delkeys:
            del self._metadata[key]
            del self._datatype[key]
            del self._description[key]


    def getDescription(self,key):
        """Get the description for the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

           Returns 
           -------
           String description for the key
        """
        return self._description[key.lower()]

    def getType(self,key):
        """Get the value type for the input key. 
           
           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

           Returns 
           -------
           String indicating underlying data type, e.g., 'float', 'table'
        """
        return self._datatype[key.lower()]

    def set(self, key, value):
        """Set the SummaryEntry value for an existing input key
           
           Parameters
           ----------
           key : str
              Key to set, case insensitive.  Key must already exist.
           value : SummaryEntry or list of SummaryEntry
              Entry to set

           Returns 
           -------
           None
        """
        k = key.lower()
        if isinstance(value,list):
            self._checklist(value)
#            print "setting " + k + "/" + str(value[0]._taskid) + "/" + str(value) + "/" + str(len(self._metadata[k]))
            try:
                self._metadata[k] = value
            except KeyError:
                raise Exception,"Key %s does not exist" % k 
        else:
            if isinstance(value, SummaryEntry):
#                print "setting " + k + "/" + str(value._taskid) + "/" + str(value) + "/" + str(len(self._metadata[k]))
                try:
                    self._metadata[k] = [value]
                except KeyError:
                    raise Exception,"Key %s does not exist" % k 
            else:
                raise Exception, "Input value is not an instance of SummaryEntry"

    def isTable(self,key):
        """ Return True if this key corresponds to an item that is
            natively an ADMIT table.

           Parameters
           ----------
           key : str
              Key to set, case insensitive.  Key must already exist.

           Returns
           -------
           boolean
              True if this key corresponds to an item that is
              natively an ADMIT table, False otherwise
        """
        return self._datatype[key.lower()] == "table"

    def insert(self,key,value):
        """Set, replace, or append the SummaryEntry value to the list for an existing input key
           If the key is not yet set, it will be set with the value.
           If the key is set, the taskid(s) will be checked and the value will replace
           the existing value(s) if the keys match.  If the taskids do not match the input
           value(s) will be appended to the existing value.  
           
           Parameters
           ----------
           key : str
              Key to insert, case insensitive.  Key must already exist.
           value : SummaryEntry or list of SummaryEntry
              Entry to insert

           Returns
           ----------
           None
        """
        k = key.lower()
        # if key is not yet set, just set and return
        if self.unset(k): 
           self.set(k,value)
           return

        if isinstance(value,list):
            self._checklist(value)
            # check if a taskid in value matches one in _metadata[key]
            # replace/extend _metadata[key] appropriately
            # This is done by creating a set of the current
            # entries for the key, then comparing them with
            # the input list.  The comparison is done soley
            # based on the taskid.   SummaryEntry has comparators
            # __eq__ and __hash__() to facilitate this. 
            # This works because design, a single task can only write one
            # entry to a given key.
            currentset = set(self.get(k))
            for j in value:
                currentset.discard(j)
                currentset.add(j)
            try:
                self._metadata[k] = list(currentset)
                return
            except KeyError:
                raise Exception,"Key %s does not exist" % k 
        else:
            if isinstance(value, SummaryEntry):
                currentset = set(self.get(k))
                currentset.discard(value)
                currentset.add(value)
                self._metadata[k] = list(currentset)
                
               # for i in range(len(self._metadata[k])):
               #      if self._metadata[k][i]._taskid == value._taskid:
#              #           print "replacing " + k + "/" + str(value._taskid) + "/" + str(value) + "/" + str(len(self._metadata[k]))
               #          self._metadata[k][i] = value
               #          return
#              #  print "appending " + k + "/" + str(value._taskid) + "/" + str(value) + "/" + str(len(self._metadata[k]))
               # self._metadata[k].append(value)
            else:
                raise Exception, "Input value does not contain instance of SummaryEntry"
            
    def show(self, showunset=False):
        """Display the all entries [key, values, description].

           Parameters
           ----------
            showunset : boolean
              If True, show unset values in addition to set values. Default: False

           Returns
           ----------
           None
        """
        for key in self._metadata:
            for v in self._metadata[key]:
                if self.unset(key) and not showunset:
                    continue
                else:
                    print "key = %s entry = [%s] desc=%s" % (key, v, self.getDescription(key))
                #print "key = %s entry = [%s] LEN=%d" % (key, v, len(self._metadata[key]) )

    def unset(self,key):
       """Determine if the key has any data.

           Parameters
           ----------
           key : str
              Key to retrieve, case insensitive.

           Returns 
           -------
           boolean
               True if the value for the key has not been set, False otherwise.
       """
       # if the value is the startup value, then the key is not set.
       # If the first entry is unset, assume there are not additional entries
       # that might not be unset!
       #if self.get(key)[0].unset():
       #    print "####UNSET() key = %s val=%s" % (key, str(self.get(key)[0]))
       #    return True
       return self.get(key)[0].unset()

    def getLineTable(self, index=0):
        """Get the table of spectral lines found

           Parameters
           ----------
           None

           Returns
           --------
           An admit.Table with spectral line entries or empty Table if
           no lines were found
        """
        atable = admit.util.Table()
        if self.unset("linelist"): 
            return atable
        else:
            # SummaryEntry data for linelist are
            # a line list admit.Table of form
            # [frequency1, name1, ...]
            # [frequency1, name2, ...]
            summaryentry = self.get("linelist")[index]
            atable.deserialize(summaryentry.getValue()[0])
            return atable

    def getLinelist(self,index=0):
        """Get the list of spectral lines found

           Parameters
           ----------
           None

           Returns
           --------
           A Python list with spectral line entries or empty list if
           no lines were found
        """
        return self.getLineTable(index).data.tolist()

    def getLinenames(self,index=0):
        """Get the names of spectral lines found

           Parameters
           ----------
           None

           Returns
           --------
           A list of string spectral line names or empty list if
           no lines were found
        """
        if self.unset("linelist"): 
            return []
        else:
            # SummaryEntry data for linelist are
            # a line list table of form
            # [
            # [frequency1, name1, ...]
            # [frequency1, name2, ...]
            # ]
            # want the slice through "name"
            lines = self.getLinelist(index)
            names = [n[1] for n in lines]
            return names

    def getLinefluxes(self,index=0):
        """Get an estimate of the line fluxes from the line list
           by multiplying Peak * Linewidth.

           Parameters
           ----------
           None

           Returns
           --------
           A dictionary of 'image filename':flux for all non-blended spectral lines in the line list,
           or an empty dictionary if no line list is available or linecubes were not created.
        """
        linelist = self.getLineTable(index)
        # note test order matters as len(None) is an error.
        if linelist == None or len(linelist) == 0: 
           return {}
        fluxes = []
        peak = linelist.getColumnByName("peakintensity")
        fwhm = linelist.getColumnByName("fwhm")
        startchan = linelist.getColumnByName("startchan")
        endchan = linelist.getColumnByName("endchan")
        for i in range(len(linelist)):
          # Magic numbers! If these startchan and endchan
          # then the line is blended and a separate line cube
          # was not created!
          # Compare as strings because numpy converts all list members to 
          # strings if any member is a string.
          if startchan[i] == '0' and endchan[i] == '0':
             continue
          # peak == l[9], fwhm == l[11]
          fluxes.append(float(peak[i])*float(fwhm[i]))
 
        # assume only one SummaryEntry, what happens if we have run linecube
        # multiple times??
        linecube = self.get("linecube")[0]
        if linecube == None:
           # a line list was made but no linecubes, so we can't get filenames
           return {}
        atable = admit.util.Table()
        atable.deserialize(linecube.getValue()[0])
        #[[basefile1,startchan1,endchan1,outfile2],...[basefileN,startchanN,endchanN,outfileN]]
        files = atable.getColumnByName("Output Cube")
        flux_dict = {}
        for x,y in zip(files,fluxes):
           flux_dict[x] = y
 
        return flux_dict

    def write(self,root):
        """ Method to write out the summary data to XML

            Parameters
            ----------
            root : cElementTree node to attach to

            Returns
            -------
            None

        """
        snode = et.SubElement(root,"summaryData")
        snode.set("type",bt.SUMMARY)
        for k,v in self._metadata.iteritems():
            mnode = et.SubElement(snode,"metadata")
            mnode.set("type",bt.METADATA)
            mnode.set("name",k)
            for item in v:
                item.write(mnode)
        writer = XmlWriter.XmlWriter(self,["_datatype","_description"],{"_datatype":bt.DICT,"_description":bt.DICT},snode,None)

    # not terribly useful since columns aren't labelled.
    #def _linelistToJSON(self,outdir):
    #    """Write the linelist to a JSON formatted file, so the
    #       lineID editor can read it.
    #    """
    #    #@todo what if there is more than one linelist?
    #    outfile = outdir + "ll.json"
    #    f = open(outfile,"w")
    #    linelist = self.getLinelist()
    #    json.dump(linelist,f)
    #    f.close()

    def _linetableToJSON(self,outdir):
        """Write the linelist table to a JSON formatted file, so the
           lineID editor can read it.
        """
        # a.run() can be called anytime in a script. don't
        # attempt write out lineid editor data if LineID_AT has not been called
        linelists = self.get("linelist")

        # naxis3 is stored as numpy.int32, which is not json serializable
        # so convert to python int.
        # Q: Should this be done at storage time or a read time?
        # @TODO CubeSpectrum, GenerateSpectrum, PVSlice should write this 
        # to summary? 
        n3 = self.get("naxis3")
        if n3 == None or n3[0].unset():
            naxis3 = -1
        else:
            naxis3 = int(n3[0].getValue()[0])

        filelist = []
        #debug
        #f.write(self.getLineTable()._jsondict())
        numlists = len(linelists)
        for i in range(numlists):
            summaryentry = linelists[i]
            if summaryentry.unset():
               continue;
            tid = str(summaryentry.getTaskID())
            outbase = "lltable."+tid+".json"
            outfile = outdir + outbase
            filelist.append(outbase)
            f = open(outfile,"w")

            tabstr = self.getLineTable(i)._jsondict(True)
            x = '{"taskid":' + str(summaryentry.getTaskID()) +', "naxis3":' + str(naxis3) + ',\n'
            tabstr = x+tabstr+'\n}'
            f.write(tabstr)
            f.close()


        #f.close()
        #outfile = outdir + "lltask.json"
        #x = {"taskid": summaryentry.getTaskID(), "naxis3" : naxis3}

        f = open(outdir+"llfiles.json","w")
        f.write(json.dumps(filelist))
        f.close()

    def _writeuuid(self,outdir,uid=None):
        """Write out a uuid to with the data.  This is an attempt
           to allow caching of data in browser between page revisits.
           Since our form-based pages are fetched with POST, they are not 
           cached by normal browser mechanism.
        """
        outfile = outdir + "uuid.json"
        f = open(outfile,"w")
        if uid==None:  
           uid == str(uuid.uuid4())
        else: 
            x = {"uuid": uid}
        f.write(json.dumps(x))
        f.close()

    def html(self,outdir,flowmanager,dotdiagram="",editor=True):
        admitloc = utils.admit_root()
        admitetc = admitloc + os.sep + "etc"
        admit_headfile = admitetc+os.sep+"index_head.html"
        admit_flowfile = admitetc+os.sep+"flowdiagram.html"
        admit_flowdiagram = dotdiagram
        admit_tailfile = admitetc+os.sep+"index_tail.html"
        admit_lineIDedithead= admitetc+os.sep+"lineIDedit_head.html"
        admit_lineIDeditfile = admitetc+os.sep+"lineIDedit_template.html"
        # outdir has trailing slash, need to strip it or
        # basename() returns ''
        # python basename() behavior different from Unix!!
        basedir = os.path.basename(outdir.rstrip(os.sep))

        # Spit out the boiler plate that is the same for
        # all index.html files.
        with open(admit_headfile,"r") as h:
            header = h.read() % (basedir,basedir)
        if ( outdir[len(outdir)-1] != os.sep ):
           outfile = outdir + os.sep + "index.html"
        else:
           outfile = outdir + "index.html"
        f = open(outfile,"w")
        f.write(header)

        # If a flow diagram was created, write out the
        # HTML to display it.
        if os.path.isfile(admit_flowdiagram):
            with open(admit_flowfile,"r") as h:
                f.write(h.read() % basedir)

        # Now process each task summary output in ID (flow) order
        #------------------------------------------------------------------
        # this is no longer workable because it won't include failed tasks
        # so use the flowmanager list instead
        #taskids = self.getAllTaskIDs()  
        #------------------------------------------------------------------
        taskids = flowmanager._tasks.keys()
        for tid in taskids:
            #tname = self.getTasknameForTaskID(tid) # see above
            tname = flowmanager[tid].__class__.__name__
            titems = self.getItemsByTaskID(tid)
            f.write(self._process(tname,tid,titems,flowmanager[tid], outdir))

        # finally, spit out the standard file ending HTML.
        with open(admit_tailfile,"r") as h:
            tail = h.read() % datetime.datetime.now() 
        f.write(tail) 
        f.close()

        self._linetableToJSON(outdir)
        #self._writeuuid(outdir,uid)

        if editor==True:
            with open(admit_lineIDedithead,"r") as h:
                header = h.read() % (basedir,basedir)
            if ( outdir[len(outdir)-1] != os.sep ):
               outfile = outdir + os.sep + "lineIDedit.html"
            else:
               outfile = outdir + "lineIDedit.html"
            f = open(outfile,"w")
            f.write(header)

            # now process data needed for lineID editor file.
            # since we have defined __cmp__ this will sort by taskid
            linelists = sorted(self.get("linelist"))
            numlists = len(linelists)

            #===============================================================
            # ugh, don't like that this is cut'n'paste from _process.
            if linelists == None or numlists == 0 : 
                llstr="<br><h4>LineID_AT identified no spectral lines in the input cube(s)</h4>"
            else:
                for i in range(numlists):
                    llstr = ''
                    summaryentry = linelists[i]
                    if summaryentry.unset():
                       continue;
                    tid = summaryentry.getTaskID()
                    taskargs = summaryentry.getTaskArgs()
                    f.write("<!-- #################### BEGIN LINEID_AT %d #################### -->\n" % tid)

                    atable = self.getLineTable(i)
                    if len(atable) == 0:
                           llstr="<br><h4>LineID_AT identified no spectral lines in this cube</h4>"

                    # Even if no lines are identified, spectra still written out.
                    tname = summaryentry.getTaskname();
                    thetask = flowmanager[tid]
                    # crashed, stale and disabled tasks will have a different color bars.
                    # If a task reports it is running outside of task.execute(), then it must have crashd.
                    if thetask.running():  
                      taskclass = "crashed-admittask" 
                    elif thetask.enabled():
                      taskclass = "stale-admittask" if thetask.isstale() else "label-admittask"
                    else:
                      taskclass = "disabled-admittask" 
                    titems = self.getItemsByTaskID(tid)
                    spectra = titems.get('spectra',None)
                    #print "SPECTRA %s" % spectra
                    if spectra != None:
                       MAX_THUMBNAILS_PER_ROW = 3  
                       SPANSVGVAL = '<div class="span4"><div class="thumbnail"> <a href="%s.html" target="_blank"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div></div><!-- thumbnail -->\n</div><!-- span4 -->'
                       SPAN4VAL = '<div class="span4"><div class="thumbnail"> <a href="%s" class="fancybox"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div><!--caption--></div><!-- thumbnail -->\n</div><!-- span4 -->'
                       # SPAN4VAL with 2 added buttons
                       # Note because of the path problem, we currently hide the
                       # Export To Fits button with <span style="display:none">
                       SPAN4VALB = '<div class="span4"><div class="thumbnail"> <a href="%s" class="fancybox"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div><!--caption-->\n%s <span style="display:none">%s</span></div><!-- thumbnail -->\n</div><!-- span4 -->'
                       SPANXVAL = '<div class="span%s">%s</div><!-- spanx -->'
                       ENDROW = '</div><!-- row-fluid --> \n'
                       STARTROW ='<div class="row-fluid">'
                       allspecs = ''
                       count = 0

                       # @todo this is a godforsaken kludge because running multiple lineIDs creates
                       # multiple spectra so that titems["spectra"] = [SummaryEntry,SummaryEntry,...]
                       # rather than SummaryEntry.  This is a problem with getItemsByTaskName--previously 
                       # each run inserts another level of [].  I have patched it, but I think it is still not
                       # correct.
                       # Why hasn't this failed when there are spectra by both CubeSpect_AT and LineID_AT, which
                       # uses getItemsByTaskID which has similar code matched[k] = [matched[k],p]
                       if type(spectra) == list:
                          mylist = spectra[0].value
                       else:
                          mylist = spectra.value
                       
                       for val in mylist:
                           #print "type(val) = %s" % type(val)
                           if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                              specval = ENDROW + STARTROW
                           else: 
                              specval = ""
                           
                           position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
                           box = str(val[2])
                           xlabel = val[3]
                           image = val[4]
                           thumb = val[5]
                           caption = val[6]
                           top   = val[7]

                           if self._imageIsSVG(image):
                               specval = specval + (SPANSVGVAL % ( image, thumb, caption, caption, caption))
                               self.makesvghtml(image,caption,outdir)
                           else:
                               specval = specval + (SPAN4VAL % ( image, thumb, caption, caption, caption))
                           allspecs = allspecs + "\n" + specval
                           count = count + 1

                    llstr = llstr + STARTROW + allspecs + ENDROW
                    with open(admit_lineIDeditfile,"r") as h:
                        #                        %s     %d      %s                 %s    %d     %s                      %d   %d   %d   %s    %d   %d  %d  %d  %d  %d  %d  %d  %d  %d  %d %d
                        header = h.read() % (taskclass,tid,thetask.statusicons(), tname,tid, summaryentry.getTaskArgs(),tid, tid,tid, llstr, tid, tid,tid,tid,tid,tid,tid,tid,tid,tid,tid,tid)
                    f.write(header)
                    f.write("<!-- #################### END LINEID_AT %d #################### -->\n" % tid)

            with open(admit_tailfile,"r") as h:
                tail = h.read() % datetime.datetime.now() 
            f.write(tail)
            f.close()

    def _imageIsSVG(self,image):
        if image[len(image)-3:len(image)+1] == 'svg': 
            return True
        else:
            return False

    def makesvghtml(self,image,caption,outdir):

        # filter out non-svg images
        if not self._imageIsSVG(image): return

        admitloc = utils.admit_root()
        admitetc = admitloc + os.sep + "etc"
        admit_svgfile = admitetc+os.sep+"svg_template.html"
        # outdir has trailing slash, need to strip it or
        # basename() returns ''
        # python basename() behavior different from Unix!!
        basedir = os.path.basename(outdir.rstrip(os.sep))

        with open(admit_svgfile,"r") as h:
            body = h.read() % (basedir,image,caption,image,datetime.datetime.now())
        if ( outdir[len(outdir)-1] != os.sep ):
           outfile = outdir + os.sep + image + ".html"
        else:
           outfile = outdir + image + ".html"
        f = open(outfile,"w")
        f.write(body)
        f.close()

    def _process(self,taskname,tid,titems,thetask,outdir):
        """Parse the SummaryEntrys for individual tasks and return formatted HTML to represent the summary data"""

        # ------ constants used in this method --------
        # Because there are 12 slots per row in Bootstrap CSS, and
        # we are using 4 slots ("span4") per thumbnail, then max thumbnails per row is 3.
        MAX_THUMBNAILS_PER_ROW = 3  
        SPANSVGVAL = '<div class="span4"><div class="thumbnail"> <a href="%s.html" target="_blank"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div></div><!-- thumbnail -->\n</div><!-- span4 -->'
        SPAN4VAL = '<div class="span4"><div class="thumbnail"> <a href="%s" class="fancybox"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div></div><!-- thumbnail -->\n</div><!-- span4 -->'
        # Export To Fits button with <span style="display:none">
        # Note because of the path problem, we currently hide the
        SPAN4VALB = '<div class="span4"><div class="thumbnail"> <a href="%s" class="fancybox"><img src="%s" alt="%s" title="%s"/></a><div class="caption"><h5>%s</h5></div><!--caption-->\n%s <span style="display:none">%s</span></div><!-- thumbnail -->\n</div><!-- span4 -->'
        SPANXVAL = '<div class="span%s">%s</div><!-- spanx -->'
        ENDROW = '</div><!-- row-fluid --> \n'
        STARTROW ='<div class="row-fluid">'
        #----------------------------------------------------
        tlower = taskname.lower()
        tupper = taskname.upper()
        admitloc = utils.admit_root()
        admitetc = admitloc + os.sep + "etc"
        admitfile = admitetc + os.sep + tlower + ".html"
        admitfail= admitetc + os.sep + "failed_at.html"
        try:
            with open(admitfile,"r") as h:
                    header = h.read() 
            with open(admitfail,"r") as h:
                    failedheader = h.read() 
        except:
            return "<!-- ***** failed to open %s ***** -->" % admitfile

        topval = "<!-- ############### BEGIN %s ###############-->\n" % tupper
        retval = "<br><b>%s: TBD by if tlower==%s below!</b><br>" % (tupper,tlower)    # see below
        botval = "\n<!-- ############### END %s ###############-->\n" % tupper

        # crashed, stale and disabled tasks will have a different color bars.
        # If a task reports it is running outside of task.execute(), then it must have crashd.
        taskargs=''
        if thetask.running():  
          taskclass = "crashed-admittask" 
          retval = failedheader % (taskclass, tid,thetask.statusicons(),taskname,tid,tid,tid)
          return topval + retval + botval
        elif thetask.enabled():
          taskclass = "stale-admittask" if thetask.isstale() else "label-admittask"
        else:
          taskclass = "disabled-admittask" 

        # If the task before this one crashed, then this one will have no summary data.
        # So just return.   Ideally, we might want each task to write a little bit of summary
        # data when it starts, rather than all at the end.  But for now, short-circuit.
        if len(titems) == 0:
           return topval + botval

        if tlower == "ingest_at":
            fitsfile = 'unknown'
            if 'fitsname' in titems:
                fitsfile = titems['fitsname'].value[0]
                taskargs = titems['fitsname'].taskargs
            casaimage = 'unknown'
            if 'casaname' in titems:
                casaimage = titems['casaname'].value[0]
                taskargs = titems['casaname'].taskargs
            source = 'unknown'
            if 'object' in titems:
                source = titems['object'].value[0]
            beam = 'unknown'
            if 'bmaj' in titems and 'bmin' in titems and 'bpa' in titems:
               bmaj = titems['bmaj'].value[0] * 180.0*3600.0/math.pi
               bmin = titems['bmin'].value[0] * 180.0*3600.0/math.pi
               bpa  = titems['bpa'].value[0]
               beam = "%5.2f\" x %5.2f\" PA @ %5.2f deg" % (bmaj,bmin,bpa)
            nx1 = 'unknown'
            nx2 = 'unknown'
            if 'naxis1' in titems:
                nx1 = str(titems['naxis1'].value[0])
            if 'naxis2' in titems:
                nx2 = str(titems['naxis2'].value[0])
            nx3 = ""
            if 'naxis3' in titems:
               nx3 = " x " + str(titems['naxis3'].value[0])
            imsize = "%s x %s%s" % (nx1,nx2,nx3)
            dmin = 'unknown'
            dmax = 'unknown'
            bunit = 'unknown'
            telescope = 'unknown'
            badpixel = 'unknown'
            restfreq = 'unknown'
            vlsr = 'unknown'
            if 'datamin' in titems:
               dmin = '%.3E' % titems['datamin'].value[0]
            if 'datamax' in titems:
               dmax = '%.3E' % titems['datamax'].value[0]
            if 'bunit' in titems:
               bunit = titems['bunit'].value[0]
            if 'telescop' in titems:
               telescope = titems['telescop'].value[0]
            if 'badpixel' in titems:
               badpixel = "%4.2f" % (titems['badpixel'].value[0] * 100)
            if 'restfreq' in titems:
               restfreq = "%4.6f GHz" % (titems['restfreq'].value[0] / 1E9)
            if 'vlsr' in titems:
               vlsr = "%.1f km/s (estimated)" % (titems['vlsr'].value[0])

            retval = header % (taskclass,tid,thetask.statusicons(),taskname,tid,taskargs,tid,fitsfile,fitsfile,casaimage,casaimage,source,restfreq,vlsr,beam,imsize,bunit,dmin,dmax,telescope,badpixel)

        if tlower == "cubespectrum_at":
           spectra = titems.get('spectra',None)
           if (spectra) != None:
               count = 0
               # task arguments are the same in all entries.
               taskargs = spectra.taskargs
               allspecs = ''
               for val in spectra.getValue():
                   # default bootstrap width is 12 columns. We are using 'span4' so
                   # thumbnail 'cell' is 4 columns. Therefore, if we have more than 
                   # 3 thumbnails, start a new row.
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = ENDROW + STARTROW
                   else: 
                      specval = ""
                   
                   position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
                   box = str(val[2])
                   xlabel = val[3]
                   image = val[4]
                   thumb = val[5]
                   caption = val[6]
                   casaimage = val[7]
                   specval = specval + (SPAN4VAL % (image, thumb, caption, caption, caption))
                   allspecs = allspecs + "\n" + specval
                   count = count + 1

               banner = '<br><h4>%s output for image %s</h4>' % (taskname, casaimage)
               allspecs = banner + allspecs
           else:
               allspecs = "<br><h4>%s produced no output for image %s </h4>" % (taskname, casaimage)

           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)

        if tlower == "regrid_at":
           the_item= titems.get('regrid',None)
           if the_item != None:
               allspecs = ""
               atable = admit.util.Table()
               atable.deserialize(the_item.getValue()[0])
               taskargs = the_item.taskargs
               if len(atable) == 0:
                   bigstr = "<h4>%s did nothing for the input image(s)</h4>\n" % taskname
               else:
                   tablestr = atable.html('class="table table-admit table-bordered table-striped"')
                   bigstr = STARTROW + tablestr + ENDROW
           else:
               bigstr = "<h4>%s wrote no summary output</h4>\n" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,bigstr,tid)
         
        if tlower == "cubesum_at":
           cubesum = titems.get('cubesum',None)
           if cubesum != None:
               allspecs = ""
               taskargs = cubesum.taskargs
               val = cubesum.getValue()
               image = val[0]
               thumb = val[1]
               caption = val[2]
               auximage = val[3]
               auxthumb = val[4]
               auxcaption = val[5]
               outcasaimage = val[6]
               casaimage = val[7]
               button = utils.getButton(outcasaimage,"viewimage","View in CASA")
               # can't have two buttons with same html ID, so add ".fits"
               button2 = utils.getButton(outcasaimage+".fits","exportimage","Export to FITS")
               specval = SPAN4VALB % (image, thumb, caption, caption, caption,button,button2)
               banner = "<br><h4>%s output for %s</h4>" % (taskname, casaimage)
               allspecs = banner + allspecs + "\n" + specval
           else:
               allspecs = "<h4>%s computed nothing for the input image</h4>" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)
           
        if tlower == "continuumsub_at":
           continuumsub = titems.get('continuumsub',None)
           if continuumsub != None:
               allspecs = ""
               taskargs = continuumsub.taskargs
               val = continuumsub.getValue()
               image = val[0]
               thumb = val[1]
               caption = val[2]
               if False:
                   auximage = val[3]
                   auxthumb = val[4]
                   auxcaption = val[5]
                   casaimage = val[6]
               specval = SPAN4VAL % (image, thumb, caption, caption, caption)
               banner = "<br><h4>%s output for %s</h4>" % (taskname, "casaimage")
               #banner = "<br><h4>%s output for %s</h4>" % (taskname, casaimage)
               allspecs = banner + allspecs + "\n" + specval
           else:
               allspecs = "<h4>%s no continuum subtracted for the input image</h4>" % taskname
           retval = header % (taskclass,tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)
               
        if tlower == "cubestats_at":
           sumentry = titems.get('rmsmethd',None)
           specval = ""
           if sumentry == None:
              rmsmethod = "unknown" 
              casaimage = "unknown"
              taskargs  = "unknown"
           else:
              rmsmethod = sumentry.value[0]
              casaimage = sumentry.value[1]
              taskargs = sumentry.taskargs

           sumentry = titems.get('chanrms', None)
           if sumentry == None:
              chanrms = "unknown"    
           else:
              chanrms = '%.3E' % sumentry.value[0]

           sumentry = titems.get('dynrange', None)
           if sumentry == None:
              dynrange = "unknown"    
           else:
              dynrange = '%.3E' % sumentry.value[0]

           sumentry = titems.get('datamean', None)
           if sumentry == None:
              datamean = "unknown"    
           else:
              datamean = '%.3E' % sumentry.value[0]

           sumentry = titems.get('spectra',None)
           if sumentry != None:
               val = sumentry.getValue()
               #@todo do something with position and box?
               position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
               box = str(val[2])
               xlabel = val[3]
               image = val[4]
               thumb   = val[5]
               caption = val[6]
               specval = specval + (SPAN4VAL % ( image, thumb, caption, caption, caption))

           sumentry = titems.get('peakpnt',None)
           if sumentry != None:
               val = sumentry.getValue()
               image   = val[0]
               thumb   = val[1]
               caption = val[2]
               specval = specval + (SPAN4VAL % ( image, thumb, caption, caption, caption))
            
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,casaimage,casaimage,rmsmethod,chanrms,dynrange,datamean,specval,tid)
           
        if tlower == "lineid_at":
           the_item = titems.get('linelist',None)
           if the_item == None:
               tablestr = "<h4>%s identified no spectral lines in this cube</h4>" % taskname
           else:
               atable = admit.util.Table()
               atable.deserialize(the_item.getValue()[0])
               if len(atable) == 0:
                   tablestr = "<h4>%s identified no spectral lines in this cube</h4>" % taskname
               else:
                   tablestr = atable.html('class="table table-admit table-bordered table-striped"')

           # output the static table that will be show if user is
           # viewing with file:// protocol.  If using http:// protocol,
           # then the live table will be shown. See etc/lineid_at.html
           bigstr = '<br><div class="row-fluid staticdisplay">' + tablestr + ENDROW
           spectra = titems.get('spectra',None)
           if spectra == None:
               retval = header % (taskclass, tid, thetask.statusicons(),taskname, tid, the_item.taskargs, tid, bigstr, tid)
           else:
               allspecs = ''
               count = 0
               for val in spectra.value:
                   # default bootstrap width is 12 columns. We are using 'span4' so
                   # thumbnail 'cell' is 4 columns. Therefore, if we have more than 
                   # 3 thumbnails, start a new row.
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = ENDROW + STARTROW
                   else: 
                      specval = ""
                   
                   position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
                   box = str(val[2])
                   xlabel = val[3]
                   image = val[4]
                   thumb = val[5]
                   caption = val[6]
                   casaimage = val[7]
                   
                   if self._imageIsSVG(image):
                       specval = specval + (SPANSVGVAL % ( image, thumb, caption, caption, caption))
                       self.makesvghtml(image,caption,outdir)
                   else:
                       specval = specval + (SPAN4VAL % ( image, thumb, caption, caption, caption))
                   allspecs = allspecs + "\n" + specval
                   count = count + 1
               bigstr = bigstr + STARTROW + allspecs + ENDROW
               retval = header % (taskclass, tid, thetask.statusicons(),taskname, tid, the_item.taskargs, tid, tid, bigstr, tid)

        if tlower == "moment_at":
           moments = titems.get('moments',None)
           allspecs = ""
           if moments != None:
               count = 0
               auximage = []
               auxthumb  = []
               auxcaption = []
               taskargs = moments.taskargs
               for val in moments.value:
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = STARTROW + ENDROW
                   else: 
                      specval = ""
                   
                   linename = val[0]
                   mom = str(val[1])
                   image    = val[2]
                   thumb    = val[3]
                   caption  = val[4]
                   auximage.append(val[5])
                   auxthumb.append(val[6])
                   auxcaption.append(val[7])
                   casaimage = val[8]
                   casamoment = image[:-4] # remove '.png' to get name of moment CASA format image
                   button = utils.getButton(casamoment,"viewimage","View in CASA")
                   # can't have two buttons with same html ID, so add ".fits"
                   button2 = utils.getButton(casamoment+".fits","exportimage","Export to FITS")
                   specval = specval + (SPAN4VALB % ( image, thumb, caption, caption, caption, button,button2))
                   allspecs = allspecs + "\n" + specval
                   count = count + 1

               banner = "<br><h4>%s output for %s</h4>" % (taskname, casaimage)
               allspecs = banner + allspecs
           else: 
               allspecs = "<br><h4>No moments were computed for this cube</h4>"

           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)

        if tlower == "pvslice_at":
           pvslices = titems.get('pvslices',None)
           if pvslices != None:
               for val in pvslices.value:
                   specval = STARTROW
                   slicetype = val[0]
                   sliceargs = str(val[1])
                   image    = val[2]
                   thumb    = val[3]
                   caption  = val[4]
                   if len(val) == 10:
                       overlayimage = val[5]
                       overlaythumb = val[6]
                       overlaycaption = val[7]
                       pvname = val[8] 
                       slicename = val[9] 
                       specval = specval + (SPAN4VAL % ( overlayimage, overlaythumb, overlaycaption, overlaycaption, overlaycaption))
                   else:
                       pvname = val[5] 
                       slicename = val[9] 
                   button = utils.getButton(pvname,"viewimage","View in CASA")
                   # can't have two buttons with same html ID, so add ".fits"
                   button2 = utils.getButton(pvname+".fits","exportimage","Export to FITS")
                   specval = specval + (SPAN4VALB % ( image, thumb, caption, caption, caption,button,button2))
                   specval = specval + ENDROW

               banner = "<br><h4>%s output for %s</h4>" % (taskname, slicename)
               specval = banner + specval
           else:
               specval = "<br><h4>No PV slices were computed for this cube</h4>"
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,pvslices.taskargs,tid,specval,tid)

        if tlower == "linecube_at":
           the_item = titems.get('linecube',None)
           if the_item != None:
               banner = "<h4>%s created the following cubes</h4>\n" % taskname
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>No Line Cubes were computed from the input cube</h4>"
               atable = admit.util.Table()
               atable.deserialize(summarydata[0])
               if len(atable) == 0:
                   tablestr = "<br><h4>No Line Cubes were computed from the input cube</h4>"
               else:
                   # create a column of "View in CASA" buttons and add to table
                   imnames = atable.getColumnByName("Output Cube")
                   buttons = []
                   buttons2 = []
                   for name in imnames:
                       buttons.append(utils.getButton(name,"viewimage","View in CASA"))
                       buttons2.append(utils.getButton(name+".fits","exportimage","Export to FITS"))
                   atable.addColumn(buttons)
                   # disable for now : atable.addColumn(buttons2)
                   # PJT  caused LineCube to fail?
                   #atable.columns[len(atable)-1] = ""
                   #atable.units[len(atable)-1]   = ""
                   tablestr = banner + atable.html('class="table table-admit table-bordered table-striped"')
           else:
               tablestr = "<br><h4>No Line Cubes were computed from the input cube</h4>"
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,tablestr,tid)

        if tlower == "pvcorr_at":
           the_item = titems.get('pvcorr',None)
           if the_item != None:
               val = the_item.getValue()
               image    = val[0]
               thumb    = val[1]
               caption  = val[2]
               pvcorrname = val[3] 
               specval = STARTROW + (SPAN4VAL % ( image, thumb, caption, caption, caption)) + ENDROW
               banner = "<br><h4>%s output for %s</h4>" % (taskname, pvcorrname)
               specval = banner + specval
           else:
               specval = "<br><h4>No PV correlation diagrams were computed from the input cube</h4>"
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,specval,tid)

        # @todo move table formatting to here.
        if tlower == "smooth_at":
           the_item = titems.get('smooth',None)
           if the_item != None:
               val = the_item.getValue()
               smoothname = val[0] # output bdp name
               enclosed   = str(val[1]) # smooth to enclosing beam? True/False
               bmaj = val[2] * 180.0*3600.0/math.pi
               bmin = val[3] * 180.0*3600.0/math.pi
               bpa  = val[4]
               velres = val[5]
               beam = "%5.2f\" x %5.2f\" PA @ %5.2f deg" % (bmaj,bmin,bpa)
           else:
               beam = velres = enclosed = smoothname  = "unknown"
               #topval +"<br><h4>No output from %s was registered?!</h4>"+ botval) % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,smoothname,smoothname,enclosed,beam,velres,tid)

        if tlower == "sfind2d_at":
           the_item = titems.get('sources',None) #SummaryEntry
           if the_item != None:
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>%s identified no sources</h4>" % taskname
               else:
                   atable = admit.util.Table()
                   atable.deserialize(summarydata[0])
                   multi_image = admit.util.MultiImage() 
                   multi_image.deserialize(summarydata[1])
                   aimage = multi_image.mimages["finderimage"] #klugey
                   #@todo Image.html()?
                   imstr = SPAN4VAL % ( aimage.images[bt.PNG], aimage.thumbnail, aimage.description, aimage.description,aimage.description)
                   if len(atable) == 0:
                       tablestr = "<br><h4>%s identified no sources</h4><br>%s" % (taskname,imstr)
                   else:
                       tablestr = STARTROW + imstr + (SPANXVAL % ("8",atable.html('class="table table-admit table-bordered table-striped"'))) + ENDROW
           else:
               tablestr = "<br><h4>%s identified no sources</h4>" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,tablestr,tid)

        if tlower == "overlapintegral_at":
           the_item = titems.get('overlap',None)
           if the_item != None:
               # summary info format:
               #[table,image,thumb,caption]
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>%s produced no output.</h4>" % taskname
               else:
                   atable = admit.util.Table()
                   atable.deserialize(summarydata[0])
                   if len(atable) == 0:
                       tablestr = "<br><h4>%s produced no output.</h4>" % taskname
                   else:
                       image = summarydata[1]
                       thumb = summarydata[2]
                       caption = summarydata[3]
                       tablestr = SPANXVAL % ("8",atable.html('class="table table-admit table-bordered table-striped"')) 
                       imstr = SPAN4VAL % (image, thumb, caption, caption, caption)
                       tablestr = STARTROW + tablestr + imstr + ENDROW
           else:
               tablestr = "<br><h4>%s produced no output.</h4>" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,tablestr,tid)

        if tlower == "principalcomponent_at":
        # PCA returns two two tables in a list [[table1 h,u,d],[table2 h,u,d]].
           tablestr = ''
           the_item = titems.get('pca',None) #SummaryEntry
           if the_item != None:
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>%s produced no output</h4>" % taskname
               else:
                   for s in summarydata:
                      atable = admit.util.Table()
                      atable.deserialize(s)
                      if len(atable) == 0:
                         tablestr = tablestr + "<h3>No covariance data available for this summary. Try lowering <i>covarmin</i> in the PrincipalComponent_AT task arguments.</h3>"
                      else:
                          tablestr = tablestr + atable.html('class="table table-admit table-bordered table-striped"')+os.linesep+os.linesep

           else:
               tablestr = "<br><h4>%s produced no output</h4>" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,tablestr,tid)

        if tlower == "template_at":
        # Template returns one table (in a list) and two plots.
           the_item = titems.get('template',None) #SummaryEntry
           tablestr = ''
           if the_item != None:
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>%s produced no output</h4>" % taskname
               else:
                   atable = admit.util.Table()
                   atable.deserialize(summarydata[0])
                   if len(atable) == 0:
                     tablestr = tablestr + "<h3>No data available for this summary.</h3>"
                   else:
                     tablestr = tablestr + atable.html('class="table table-admit table-bordered table-striped"')+os.linesep+os.linesep
           else:
               tablestr = "<br><h4>%s produced no output</h4>" % taskname

           # Output plots.
           allspecs = tablestr + "\n"
           spectra = titems.get('spectra',None)
           if (spectra) != None:
               count = 0
               # task arguments are the same in all entries.
               taskargs = spectra.taskargs
               for val in spectra.getValue():
                   # default bootstrap width is 12 columns. We are using 'span4' so
                   # thumbnail 'cell' is 4 columns. Therefore, if we have more than 
                   # 3 thumbnails, start a new row.
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = ENDROW + STARTROW
                   else: 
                      specval = ""
                   
                   position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
                   box = str(val[2])
                   xlabel = val[3]
                   image = val[4]
                   thumb = val[5]
                   caption = val[6]
                   casaimage = val[7]
                   specval = specval + (SPAN4VAL % (image, thumb, caption, caption, caption))
                   allspecs = allspecs + "\n" + specval
                   count = count + 1

               banner = '<br><h4>%s output for %s</h4>' % (taskname, casaimage)
               allspecs = banner + allspecs
           else:
               allspecs = allspecs + "<br><h4>No spectra were produced by %s</h4>" % taskname

           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)

        if tlower == "linesegment_at":
           the_item = titems.get('segments',None)
           if the_item == None:
               tablestr = "<h4>%s identified no spectral lines in this cube</h4>" % taskname
           else:
               atable = admit.util.Table()
               atable.deserialize(the_item.getValue()[0])
               if len(atable) == 0:
                   tablestr = "<h4>%s identified no spectral lines in this cube</h4>" % taskname
               else:
                   tablestr = atable.html('class="table table-admit table-bordered table-striped"')

           bigstr = '<br>' + STARTROW + tablestr + ENDROW
           spectra = titems.get('spectra',None)
           specval=""
           if spectra != None:
               allspecs = ''
               count = 0
               for val in spectra.value:
                   # default bootstrap width is 12 columns. We are using 'span4' so
                   # thumbnail 'cell' is 4 columns. Therefore, if we have more than 
                   # 3 thumbnails, start a new row.
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = ENDROW + STARTROW
                   else: 
                      specval = ""
                   
                   position = "(%s,%s)" % ( str(val[0]),str(val[1]) )
                   box = str(val[2])
                   xlabel = val[3]
                   image = val[4]
                   thumb = val[5]
                   caption = val[6]
                   casaimage = val[7]
                   if self._imageIsSVG(image):
                       specval = specval + (SPANSVGVAL % ( image, thumb, caption, caption, caption))
                       self.makesvghtml(image,caption,outdir)
                   else:
                       specval = specval + (SPAN4VAL % ( image, thumb, caption, caption, caption))

                   allspecs = allspecs + "\n" + specval
                   count = count + 1
               bigstr = bigstr + STARTROW + allspecs + ENDROW
               retval = header % (taskclass, tid, thetask.statusicons(),taskname, tid, the_item.taskargs, tid, bigstr, tid)

        if tlower == "bdpingest_at":
           the_item = titems.get('bdpingest',None) #SummaryEntry
           if the_item != None:
               summarydata = the_item.getValue()
               if summarydata == None or len(summarydata) == 0:
                   tablestr = "<br><h4>%s No information available about the ingested BDP</h4>" % taskname
               else:
                   atable = admit.util.Table()
                   atable.deserialize(summarydata[0])
                   if len(atable) == 0:
                       tablestr = "<br><h4>%s No information available about the ingested BDP</h4>" % taskname
                   else:
                       tablestr = atable.html('class="table table-bordered table-striped"')
           else:
               tablestr = "<br><h4>%s No information available about the ingested BDP</h4>" % taskname
           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,the_item.taskargs,tid,tablestr,tid)

        if tlower == "generatespectrum_at":
           spectra = titems.get('spectra',None)
           if (spectra) != None:
               count = 0
               # task arguments are the same in all entries.
               taskargs = spectra.taskargs
               allspecs = ''
               for val in spectra.getValue():
                   # default bootstrap width is 12 columns. We are using 'span4' so
                   # thumbnail 'cell' is 4 columns. Therefore, if we have more than 
                   # 3 thumbnails, start a new row.
                   if count != 0 and (count % MAX_THUMBNAILS_PER_ROW) == 0:
                      specval = ENDROW + STARTROW
                   else: 
                      specval = ""
                   
                   xlabel = val[0]
                   image = val[1]
                   thumb = val[2]
                   caption = val[3]
                   specval = specval + (SPAN4VAL % (image, thumb, caption, caption, caption))
                   allspecs = allspecs + "\n" + specval
                   count = count + 1

               banner = '<br><h4>%s output</h4>' % (taskname)
               allspecs = banner + allspecs
           else:
               allspecs = "<br><h4>%s produced no output</h4>" % (taskname)

           retval = header % (taskclass, tid,thetask.statusicons(),taskname,tid,taskargs,tid,allspecs,tid)

        return topval + retval + botval

    def __str__(self):
        print "Summary\n  metadata"
        for k,v in self._metadata.iteritems():
            print k
            for i in v:
                print str(i)
        print "\n  datatype\n"
        for k,v in self._datatype.iteritems():
            print k,v
        print "\n  description\n"
        for k,v in self._description.iteritems():
            print k,v
        return ""

    def _initialize(self, key, value):
        """Initialize a new key and value. This method is typically used when
           loading in $ADMIT/etc/summary_defs.tab. See _startup()
           
           Parameters
           ----------
           key: str
              Key to set, case insensitive.  Key must not yet exist.
           value: list
              Entry to set, [value, description string]
        """
        k = key.lower()
        if k in self._metadata:
            raise Exception,"key %s already exists" % k
        else:
            if isinstance(value, SummaryEntry):
                self._metadata[key.lower()] = [value]
            else:
                raise Exception, "Input value does not contain instance of SummaryEntry"

    def _checklist(self,value):
        """Check that a list contains only SummaryEntrys. If not,
           and exception is thrown.
        """
        badlist = []
        for i in range(0,len(value)):
           if not isinstance(value[i],SummaryEntry):
              badlist.append(i)
               
        if len(badlist) != 0:
             raise Exception, "Input value at index %s is not an instance of SummaryEntry" % str(badlist)


    def _startup(self):
        """Called by __init___ to instantiate a new Summary from file $ADMIT/etc/summary_defs.tab"""
        file = utils.admit_root() + os.sep + "etc" + os.sep + "summary_defs.tab"
        lines = [line.strip() for line in open(file)]
        for l in lines:
            if l.startswith('#'): continue
            (keyword,valtype,description) = l.split(None,2)
            p = SummaryEntry()
            self._initialize(keyword,p)
            self._datatype[keyword.lower()] = valtype.lower()
            self._description[keyword.lower()] = description


    def _getitems(self):
        """to allow iteration"""
        return self._metadata;

    def _test(self):
        """Self test"""
        try:
            tid=1
            self.insert("FITSNAME",SummaryEntry(value="foobar.fits",taskname="Ingest_AT",taskid=tid,taskargs="foobar.fits"))
            self.insert("CASANAME",SummaryEntry(value="foobar.im",taskname="Ingest_AT",taskid=tid))
            self.insert("TELESCOP",SummaryEntry(value="ALMA",taskname="Ingest_AT",taskid=tid))
            self.insert("OBJECT",SummaryEntry(value="PLUTO",taskname="Ingest_AT",taskid=tid))
            self.insert("NAXIS1",SummaryEntry(value=64,taskname="Ingest_AT",taskid=tid))
            self.insert("NAXIS2",SummaryEntry(value=65,taskname="Ingest_AT",taskid=tid))
            self.insert("NAXIS3",SummaryEntry(value=66,taskname="Ingest_AT",taskid=tid))
            tid += 1
            self.set("PVSLICES",SummaryEntry([["slit","sliceargs","figname","thumbnail","pvcaption","overlayname","overlaythumbname","overlaycaption","input_file"]],"PVslice_AT",taskid=tid, taskargs=""))
            tid += 1
            self.set("MOMENTS", value=SummaryEntry([
                        ['H2CS_103.0405', 0, 'blah_mom0.png', 'blah_mom0_thumb.png', 'Moment 0 of H2CS', 'blah_mom0_histo.png', 'blah_mom0_histo_thumb.png', 'histogram of mom0', 'blah.im' ], 
                        ['H2CS_103.0405', 1, 'blah_mom1.png', 'blah_mom1_thumb.png', 'Moment 1 of H2CS', 'blah_mom1_histo.png', 'blah_mom1_histo_thumb.png', 'histogram of mom1', 'blah.im' ]], taskname="Moment_AT", taskid=tid, taskargs=""))

            tid += 1
            self.set("MOMENTS", value=SummaryEntry([
                        ['X2CS_103.0405', 0, 'blah_mom0.png', 'blah_mom0_thumb.png', 'Moment 0 of X2CS', 'blah_mom0_histo.png', 'blah_mom0_histo_thumb.png', 'histogram of mom0', 'blah.im' ], 
                        ['X2CS_103.0405', 1, 'blah_mom1.png', 'blah_mom1_thumb.png', 'Moment 1 of X2CS', 'blah_mom1_histo.png', 'blah_mom1_histo_thumb.png', 'histogram of mom1', 'blah.im' ]], taskname="Moment_AT", taskid=tid, taskargs=""))

            # ensure replacement works
            self.insert("MOMENTS", value=SummaryEntry([
                        ['Q_103.0405', 0, 'blah_mom0.png', 'blah_mom0_thumb.png', 'Moment 0 of Q', 'blah_mom0_histo.png', 'blah_mom0_histo_thumb.png', 'histogram of mom0', 'blah.im' ], 
                        ['Q_103.0405', 1, 'blah_mom1.png', 'blah_mom1_thumb.png', 'Moment 1 of Q', 'blah_mom1_histo.png', 'blah_mom1_histo_thumb.png', 'histogram of mom1', 'blah.im' ]], taskname="Moment_AT", taskid=tid, taskargs="These are some arguments"))

            mid = self.getTaskID("moments")
            if mid[0] != tid:
               raise Exception, "Expected MOMENT taskid %d, got %d " % (tid,mid[0])
            # should throw exception: not an instance of SummaryEntry
            try :
                self._initialize("FOOBAR",["foo.fits","hey",200])
            except Exception, ex:  
               print "## Couldn't add FOOBAR:" + str(ex) + " (It's OK, this is expected)"
            tn = self.getTaskname("fitsname")[0]
            if tn != 'Ingest_AT':
               raise Exception, "Expected taskname Ingest_AT, got %s " % tn

            tid +=1
            self.set("chanrms",SummaryEntry([0.10, 'foobar.im'], 'CubeStats_AT', taskid=tid, taskargs=""))
            tid +=1
            self.insert("chanrms", SummaryEntry([0.08, 'co-1.im'], 'MARC1_AT', taskid=tid, taskargs=""))
            tid +=1
            self.insert("chanrms", SummaryEntry([0.04, 'co-2.im'], 'MARC2_AT', taskid=tid, taskargs=""))
            tid +=1
            self.insert("cubesum",SummaryEntry(['ngc253_fullcube_compact_spw3_clean.ce.csm.png', 'ngc253_fullcube_compact_spw3_clean.ce.csm_thumb.png', 'Integral (moment 0) of all emission in image cube ngc253_fullcube_compact_spw3_clean.ce.csm.png', 'ngc253_fullcube_compact_spw3_clean.ce.csm_histo.png', 'ngc253_fullcube_compact_spw3_clean.ce.csm_histo_thumb.png', 'Histogram of cube sum for image cube ngc253_fullcube_compact_spw3_clean.ce.csm.png', 'ngc253_fullcube_compact_spw3_clean.ce.im'],"CubeSum_AT",taskid=tid, taskargs=""))
            tid +=1
            self.insert("spectra", SummaryEntry([\
    [184, 150, '184,150,184,150', 'Channel', 'ngc253_fullcube_compact_spw3_clean.ce.csp_0.png', 'ngc253_fullcube_compact_spw3_clean.ce.csp_0_thumb.png', 'Average Spectrum in ngc253_fullcube_compact_spw3_clean.ce.im at centerbox[[184pix,150pix],[1pix,1pix]]', 'ngc253_fullcube_compact_spw3_clean.ce.im'],\
    [120, 120, '124,120,284,120', 'Channel', 'ngc253_fullcube_compact_spw3_clean.ce.csp_1.png', 'ngc253_fullcube_compact_spw3_clean.ce.csp_1_thumb.png', 'Average Spectrum in ngc253_fullcube_compact_spw3_clean.ce.im at centerbox[[120pix,120pix],[1pix,1pix]]', 'ngc253_fullcube_compact_spw3_clean.ce.im'],\
    [100, 100, '124,120,284,120', 'Channel', 'ngc253_fullcube_compact_spw3_clean.ce.csp_2.png', 'ngc253_fullcube_compact_spw3_clean.ce.csp_2_thumb.png', 'Average Spectrum in ngc253_fullcube_compact_spw3_clean.ce.im at centerbox[[100pix,100pix],[1pix,1pix]]', 'ngc253_fullcube_compact_spw3_clean.ce.im'],\
    [10, 10, '124,120,284,120', 'Channel', 'ngc253_fullcube_compact_spw3_clean.ce.csp_3.png', 'ngc253_fullcube_compact_spw3_clean.ce.csp_3_thumb.png', 'Average Spectrum in ngc253_fullcube_compact_spw3_clean.ce.im at centerbox[[10pix,10pix],[1pix,1pix]]', 'ngc253_fullcube_compact_spw3_clean.ce.im']],\
    "CubeSpectrum_AT",taskid=tid, taskargs=""))
            tid +=1
            testlist = []
            testtable = admit.util.Table()
            table_data = "{'_type': 'Table', '_order': ['description', 'planes', 'units', 'data', 'columns'], 'description': 'Identified Spectral Lines', 'planes': [], 'units': ['GHz', '', '', '', '', 'km/s', 'K', 'K', 'D^2', 'Jy/beam', 'km/s', 'km/s', '', '', '', ''], 'data': [[101.89242, 'CH3CHO_101.89242', 'CH3CHOv=0', 'Acetaldehyde', '3(1,3)-2(0,2)A++', 212.94533833637621, 2.772510051727295, 7.662539958953857, 2.297600030899048, -4.3369997478847351, -23.054661663623804, 59.015620206307695, 886, 899, -8324.4921623698665, 0], [101.96277, 'DNCO_101.96277', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=4-4', 0.0, 9.787079811096191, 14.680489540100098, 0.1711300015449524, 0, 0, 0, 0, 0, 0, 2], [101.96351, 'DNCO_101.96351', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=4-5', 0.0, 9.787079811096191, 14.680529594421387, 0.0017300000181421638, 0, 0, 0, 0, 0, 0, 2], [101.96369, 'DNCO_101.96369', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=6-5', 350.63413978966406, 9.787079811096191, 14.680540084838867, 5.056029796600342, 0.00084258543279315523, 114.63413978966406, 9.80037900830974, 830, 856, 1.6172691351514592, 2], [101.96369, 'DNCO_101.96369', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=5-4', 0.0, 9.787079811096191, 14.680540084838867, 4.106860160827637, 0, 0, 0, 0, 0, 0, 2], [101.96369, 'DNCO_101.96369', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=4-3', 0.0, 9.787079811096191, 14.680540084838867, 3.327440023422241, 0, 0, 0, 0, 0, 0, 2], [101.9644, 'DNCO_101.96440', 'DNCO', 'Isocyanic Acid', '5(0,5)-4(0,4),F=5-5', 0.0, 9.787079811096191, 14.680569648742676, 0.17112000286579132, 0, 0, 0, 0, 0, 0, 2], [102.06427, 'NH2CHO_102.06427', 'NH2CHO', 'Formamide', '5(1,5)-4(1,4)', 191.27283039192014, 12.78633975982666, 17.684619903564453, 62.7530403137207, 0.0028236083019267848, -44.727169608079862, 29.199261421990698, 788, 825, 5.4196694824471781, 0], [103.60365, 'H2CCCHCN_103.60365', 'H2CCCHCN', 'Cyanoallene', '20(3,17)-19(3,16)', 106.59189789323986, 57.259681701660156, 62.231849670410156, 971.4053344726562, 0.0016086832366196001, -129.40810210676014, 36.665300323861935, 28, 34, 5.5723163322792049, 0], [103.64586, '(CH2OH)2_103.64586', \"g'Ga-(CH2OH)2\", 'Ethylene Glycol', '6(2,4)v=0-5(1,5)v=0', 170.05896720851203, 7.461170196533203, 12.43535041809082, 4.974090099334717, 0.0022648186040296948, -65.94103279148797, 23.762130083968334, 0, 13, 7.8451030069810663, 0]], 'columns': ['frequency', 'uid', 'formula', 'fullname', 'transition', 'velocity', 'El', 'Eu', 'Linestrength', 'peakintensity', 'peakoffset', 'fwhm', 'startchan', 'endchan', 'sigma', 'blend']}"

            testtable.deserialize(table_data)
            self.insert("linelist",SummaryEntry(testtable.serialize(),"LineID_AT",taskid=tid, taskargs="vlsr=50"))
            self.insert("linelist",SummaryEntry(testtable.serialize(),"LineID_AT",taskid=tid+1, taskargs="vlsr=50"))
            linenames = self.getLinenames()
            testnames = [ 'CH3CHO_101.89242',
                     'DNCO_101.96277', 
                     'DNCO_101.96351',
                     'DNCO_101.96369', 
                     'DNCO_101.96369', 
                     'DNCO_101.96369',
                     'DNCO_101.96440',
                     'NH2CHO_102.06427', 
                     #'NH2CHO_102.21757',
                     #'CH3CH2CHO_102.46729', 
                     #'CH3CH2CHO_102.47868', 
                     #'CH3CCH_102.54798', 
                     #'CH2OHCHO_102.54978', 
                     #'H2CS_103.04055', 
                     #'CH2CHCHO_103.25137',
                     #'(CH3)2CO_103.29717',
                     #'(CH3)2CO_103.37708',
                     #'CH3CH2OH_103.48036', 
                     #'CH3SH_103.50410',
                     #'CH3COOH_103.54081',
                     #'CH2CHCN_103.57540',
                     'H2CCCHCN_103.60365',
                     '(CH2OH)2_103.64586']
            if testnames != linenames:
               raise Exception,"Expected line names did not match."
            return True
            print s.getLinefluxes()
        except Exception, ex:
            print str(ex)
            return False

###############################################################################
#    END SUMMARY CLASS                                                        #
###############################################################################


class SummaryEntry:
    """ Defines a single 'row' of a Summary data entry.  A Summary key can refer to a list of SummaryEntry.
        This class makes management of complicated data entries easier.  It was getting tough
        to slice and unzip all those lists!
    """
    def __init__(self,value=[],taskname="",taskid=-1,taskargs=""):
        if isinstance(value,list):
           self._value    = value
        else:
           self._value    = [value]
        self._taskname = taskname
        self._taskid   = taskid
        self._taskargs = taskargs
        self._type     = bt.SUMMARYENTRY

    def getValue(self):
        """Get the underlying data value from this SummaryEntry.  Value will be list
           containing zero or more items.

           Parameters
           ----------
           None

           Returns
           -------
           list
             A (possibly empty) list of SummaryEntry.
        """
        return self._value


    def getTaskname(self):
        """Get the name of the task that created this SummaryEntry.

           Parameters
           ----------
           None

           Returns
           -------
           str
             The string task name that produced the data value"""
        return self._taskname;


    def getTaskID(self):
        """Get the ID of the task that created this SummaryEntry.

           Parameters
           ----------
           None

           Returns
           -------
           int
             The integer task ID that produced the data value"""
        return self._taskid;

    def getTaskArgs(self):
        """Get the arguments of the task to display in the data browser web page.

           Parameters
           ----------
           None

           Returns
           -------
           str 
             The string task arguments"""
        return self._taskargs;



    def setTaskname(self,name):
        """Set the name of the task that created this SummaryEntry.

           Parameters
           ----------
           name : str 
              The task name that produced the data value

           Returns
           -------
           None
        """
        self._taskname = name;

    def setTaskID(self,taskid):
        """Set the ID of the task that created this SummaryEntry.

           Parameters
           ----------
           taskid : int 
              The task id number that produced the data value

           Returns
           -------
           None
        """
        self._taskid = taskid ;

    def setTaskArgs(self,args):
        """Set any arguments of the task that should be displayed in the data browser web page.

           Parameters
           ----------
           args : str 
              The task args that produced the data value

           Returns
           -------
           None
        """
        self._taskargs = args;

    #-------------------------------
    # Make the internal data be well-behaved properties.
    # See e.g. http://www.programiz.com/python-programming/property
    value = property(getValue, None, None, 'The underlying data value')
    taskname = property(getTaskname, setTaskname, None, 'The name of the task that created this SummaryEntry')
    taskid = property(getTaskID, setTaskID, None, 'The integer task ID that created this SummaryEntry')
    taskargs = property(getTaskArgs, setTaskArgs, None, 'The arguments of the task to display in the data browser web page.')
    #-------------------------------

    def unset(self):
        """Find out if this SummaryEntry instance has data or not.

           Parameters
           ----------
           None

           Returns
           -------
           bool
             True if this SummaryEntry has no data set"""
        return (self._taskname == "" or self._taskid == -1)

    def write(self,root):
        """ Method to write out the SummaryEntry data to XML

            Parameters
            ----------
            root : cElementTree node to attach to

            Returns
            -------
            None

        """
        snode = et.SubElement(root,"summaryEntry")
        snode.set("type",bt.SUMMARYENTRY)
        writer = XmlWriter.XmlWriter(self,["_value","_taskname","_taskid","_taskargs"],{"_value":bt.LIST,"_taskname":bt.STRING,"_taskid":bt.INT,"_taskargs":bt.STRING},snode,None)

    # Two SummaryEntrys are equal if their taskids are equal
    def __eq__(self,other):
        if(isinstance(other,self.__class__)):
           return self._taskid == other._taskid
        return False

    def __cmp__(self,other):
        if(isinstance(other,self.__class__)):
            if self._taskid < other._taskid:
               return -1
            if self._taskid == other._taskid:
               return 0
            if self._taskid > other._taskid:
               return 1
        return -1
        
    def __hash__(self):
        return self._taskid

    def __str__(self):
        return "SummaryEntry(value=%s, taskname=%s, taskid=%d, taskargs=%s)" % \
                (str(self._value), self._taskname, self._taskid,self._taskargs)
 
    # ensure that printing a list of SummaryEntry will print the
    # individual values and not just addresses.  
    # e.g. 'print str(listOfSummaryEntry)' does a useful and intuitive operation
    __repr__ = __str__


if __name__ == "__main__":
    s = Summary()
    s._test()
    qq = SummaryEntry("Hqwl","AT1",1,"blah")
    rr = SummaryEntry("Hrwl","AT1",1,"blah")
    ss = SummaryEntry("FOOS","AT2",1,"blah")
    tt = SummaryEntry("FOOT","AT3",2,"blah")
    print "qq == rr (True?):" + str(qq == rr)
    print "qq == ss (True?):" + str(qq == ss)
    print "ss == tt (False?):" + str(qq == tt)
    S1= set([qq,rr,tt])
    S2= set([ss,tt])
    print "S1=" + str(S1)
    print "S2=" + str(S2)
    if ss in S1:
        S1.remove(ss)
        S1.add(ss)
    print "S1u=" + str(S1)
    S3 = S1.union(S2)
    print "union=" + str(S3)
    print list(S3)
    print list(S3).sort()
    print s.getAllTaskIDs()
    print s.getTasknameForTaskID(120)
