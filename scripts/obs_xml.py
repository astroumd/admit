#! /usr/bin/env python
#
#  This example script will parse the OBS_<projectUID>.xml file that can be found
#  in the top level directory of a project tree, e.g. in
#               2015.1.00665.S/OBS_uid___A001_X1ed_X66c.xml
#
#
#  This method was used as a hack, to get a quick idea of the VLSR is, if no other means
#  where available (until this will appear in the FITS header)
#  Proposed FITS keywords relevant to ADMIT (as taken from V1.8 from ALMAFITSnames.pdf)
#
#  LINTRN     Line transition, e.g. "12CO(1-0)"
#  OBJECT     Source name (some confusion as this is now blank, where the FIELD is used)
#  RESTFRQ    restfreq (or middle of band) if there is a line
#  ZSOURCE    redshift  (no word on optical/radio,    optical presumably)
#  SPECSYS    required to be 'LSRK'
#
#  To repeat again: this is a hack, as this OBS file in normally not available to users.
#
#  Caveats:
#   - ephemeris sources show up with sourceName=Ephemeris
#  Bugs:
#   - NRAO uses the generator castor classes in Java for parsing the APDM data structures
#     and seems to ignore the fact that UTF-8 should not allow special characters such as \b0.
#     Their header uses UTF-8, and can crash this python DOM reader; replace the first
#     line with    sed s/UTF-8/ISO-8859-1/
#   

import sys
import xml.dom.minidom


def obs_xml(filename):
    """ parse an APDM confirming OBS_<project_UID>.xml file 
    
    ADMIT only needs a few things
    - source name (confirming via lookup, there is no  guarentee them to be the same)
    - VLSRK (sometimes this will need a conversion from helio, radio/optical)

    Note the difference in camel case between the two types of nodes

    <ObsProject>
       <ObsProgram>
          <ScienceGoal>
             <SpectralSetupParameters>
                <ScienceSpecralWindow>
                   <index>
                   <transitionName>
                   <centerFrequency>
                   <splatalogId>            [optional]
             <TargetParameters>
                <sourceName>
                <sourceVelocity>
                   <centerVelocity>
    
    """
    # @todo  stream this into a tempfile using
    #              sed s/UTF-8/ISO-8859-1/
    #        and then parse it to bypass potential non-standard characters
    top = xml.dom.minidom.parse(filename)
    opt = top.getElementsByTagName("ObsProject")
    if len(opt) != 1:
        print "ObsProject bad len: ",len(opt)
        return
    opm = opt[0].getElementsByTagName("ObsProgram")
    if len(opm) != 1:
        print "ObsProgram bad len: ",len(opm)
        return
    sg = opm[0].getElementsByTagName("ScienceGoal")
    print "# Found %d science goals" % len(sg)
    for i in range(len(sg)):
        sgi = sg[i]
        print "### ScienceGoal-%d: %s" % (i+1,sgi.getElementsByTagName("name")[0].childNodes[0].data)

        tp  = sgi.getElementsByTagName("TargetParameters")
        if len(tp) == 1:
            sn = tp[0].getElementsByTagName("sourceName")[0].childNodes[0].data
            #print "# sourceName: ",sn
            sv = tp[0].getElementsByTagName("sourceVelocity")
            vel = "0.0"
            vu = "N/A"    # default: km/s ?
            dt = "N/A"    # ?
            rs = "N/A"    # ?
            if len(sv) == 1:
                cv = sv[0].getElementsByTagName("centerVelocity")
                vel = cv[0].childNodes[0].data
                #print "# sourceVelocity: ",vel
                if cv[0].hasAttribute("unit"):
                    vu = cv[0].getAttribute("unit")

                if sv[0].hasAttribute("dopplerCalcType"):
                    dt = sv[0].getAttribute("dopplerCalcType")
                    #print "# dopplerCalcType: ",dt
                if sv[0].hasAttribute("referenceSystem"):
                    rs = sv[0].getAttribute("referenceSystem")
                    #print "# referenceSystem: ",rs
            else:
                print "# No sourceVelocity available"
            print "#vlsr  %s  %s  # %s doppler: %s  ref: %s" % (sn,vel,vu,dt,rs)
                
        else:
            print "Skipping.... no TargetParameters"
            
        ssp = sgi.getElementsByTagName("SpectralSetupParameters")
        if len(ssp) == 1:
            ssw = ssp[0].getElementsByTagName("ScienceSpectralWindow")
            for sswi in ssw:
                tn = sswi.getElementsByTagName("transitionName")[0].childNodes[0].data
                cf = sswi.getElementsByTagName("centerFrequency")[0].childNodes[0].data
                #print "  transitionName: ",tn
                #print "  centerFrequency: ",cf
                sid = sswi.getElementsByTagName("splatalogId")
                if len(sid) == 1:
                    si = sid[0].childNodes[0].data
                    #print "  splatalogId: ",si
                else:
                    si = "0"
                print "%s   %s    # splatalogid=%s" % (cf,tn,si)
        else:
            print "Skipping.... no SpectralSetupParameters"
        

#  main program:

for ff in sys.argv[1:]:
    obs_xml(ff)
    
