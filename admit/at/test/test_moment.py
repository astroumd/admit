#! /usr/bin/env casarun
# 
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
""" Right now you need to run this test inside of casapy

This test does the following:
    creates an admit class
    creates a moment AT
    sets some moment parameters
    adds the moment AT to the admit class
    runs admit (which in turn runs the needed AT's)
    writes the results out to disk
    reads them into a new admit instance
    prints out one of the BDP xml file names
    
    to run this test do the following:
        import admit.at.test.test_moment as tm
        tm.run(<filename>)    <filename> is the name of the image file to be processed (note for the time being you need to be in the directory containing the image file
"""
import admit.Admit as ad
import admit.at.Moment_AT as ma
import admit.bdp.SpwCube_BDP as spw
from admit.util.Image import Image
import admit.util.bdp_types as bt

def run(fileName):
    # instantiate the class
    a = ad.Admit()
    s = spw.SpwCube_BDP(taskid=1234,xmlFile="spw_test_object.bdp")
    
    image = Image({bt.CASA:fileName})
    s.image = image
    # instantiate a moment AT
    m = ma.Moment_AT()
    # add the moment AT to the admit class
    a.addtask(m)
    # set some moment parameters
    m.setkey("outfile","tester")
    m.setkey("moments",[0,1,2])
    print s.image.images
    m.addInput(s)
    # output filenames will be:    
    #   tester.integrated           mom=0
    #   tester.weighted_coord       mom=1
    #   weighted_dispersion_coord   mom=2


    # run admit (specifically the tasks that need it
    if False:
        m.execute()
    else:
        a.run()
    # save it out to disk (this will not be needed soon as I a working on
    # a way to write out the xml inside of the run commmand
    a.write()
    
    print "ALL DONE. NOW READING BACK"

    a2 = ad.Admit()   # read in the admit.xml and bdp.xml files

    # this should print out something reasonable ending in .xml
    #print a.tasks[0].out[0].xmlFile
    #print a2.tasks[0].out[0].xmlFile

    print "These pairs should match"
    for at in a.fm.tasks:
        print "FlowManager tasks ",a.fm.tasks
        print "FlowManager tasks ",a2.fm.tasks
        print "LEN ",len(a.fm.tasks[at].bdp_out)
        print "LEN ",len(a2.fm.tasks[at].bdp_out)
        print "Input ",a.fm.tasks[at].bdp_in[0].taskid
        print "Input ",a2.fm.tasks[at].bdp_in[0].taskid
        print "\n\n"
    
    
    print "Conn map ",a.fm._connmap
    print "Conn map ",a2.fm._connmap
    print "\n\n"
    
    print "Conn map ",a.fm._depsmap
    print "Conn map ",a2.fm._depsmap
    print "\n\n"
    
    for at in a.fm.tasks:
        for i in a.fm.tasks[at].bdp_out :
            if(i.xmlFile == a2.fm.tasks[at].bdp_out[0].xmlFile):
                print "File ",i.xmlFile
                print "File ",a2.fm.tasks[at].bdp_out[0].xmlFile
                print "\n\nPASS\n"
                print "running a2 again:"
                a2.run()
                return
    print "\n\nFAIL\n"

if __name__ == "__main__":
    import sys
    
    argv = ad.casa_argv(sys.argv)
    if len(argv) > 1:
        print "Working on ",argv[1]
        run(argv[1])
