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
    creates a helloworld AT
    sets some helloworld parameters
    adds the helloworld AT to the admit class
    runs admit (which in turn runs the needed AT's)
    writes the results out to disk
    reads them into a new admit instance
    prints out one of the BDP xml file names

    to run this test do the following:
        import admit.at.test.test_helloworld as th
        th.run()
"""
import os
loc = os.path.dirname(os.path.realpath(__file__))
cmd = "cp %s/../../../doc/examples/HelloWorld_AT.py %s/../." % (loc,loc)
os.system(cmd)
cmd = "cp %s/../../../doc/examples/HelloWorld_BDP.py %s/../../bdp/." % (loc,loc)
os.system(cmd)
import admit.xmlio.dtdGenerator as dtd
dtd.generate()
import admit.Admit as ad
import admit.at.HelloWorld_AT as hw
import admit.at.Ingest_AT as ia
import admit.util.bdp_types as bt

def run():
    # instantiate the class
    a = ad.Admit()

    # instantiate a moment AT
    h = hw.HelloWorld_AT()
    # add the moment AT to the admit class
    a.addtask(h)
    # set some moment parameters
    h.setkey("yourname","Bill")
    h.setkey("planet","Mars")

    # run admit (specifically the tasks that need it)
    h.execute()
    # save it out to disk (this will not be needed soon as I a working on
    # a way to write out the xml inside of the run commmand
    a.write()

    a2 = ad.Admit()   # read in the admit.xml and bdp.xml files

    cmd = "rm -f %s/../HelloWorld_AT.p*" % (loc)
    os.system(cmd)
    cmd = "rm -f %s/../../bdp/HelloWorld_BDP.p*" % (loc)
    os.system(cmd)
    dtd.generate()

    print "These pairs should match"
    for at in a.fm:
        print "FlowManager task ",a.fm[at]
        print "FlowManager task ",a2.fm[at]
        print "LEN ",len(a.fm[at]._bdp_out)
        print "LEN ",len(a2.fm[at]._bdp_out)
        print "Input ",a.fm[at]._bdp_in[0]._taskid
        print "Input ",a2.fm[at]._bdp_in[0]._taskid
        print "\n\n"


    print "Conn map ",a.fm._connmap
    print "Conn map ",a2.fm._connmap
    print "\n\n"

    print "Conn map ",a.fm._depsmap
    print "Conn map ",a2.fm._depsmap
    print "\n\n"

    for at in a.fm:
        for i in a.fm[at].bdp_out :
            if(i.xmlFile == a2.fm[at]._bdp_out[0]._xmlFile):
                print "File ",i.xmlFile
                print "File ",a2.fm[at]._bdp_out[0]._xmlFile
                print "\n\nPASS\n"
                return
    print "\n\nFAIL\n"

if __name__ == "__main__":
    import sys

    argv = ad.casa_argv(sys.argv)
    if len(argv) > 1:
        print "Working on ",argv[1]
        run(argv[1])
