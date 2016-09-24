#! /usr/bin/env casarun
# 
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
#   Typical test usage:
#       ./test_ingest.py   test123.fits  [dummy]
#   This will produce admit.xml and
#   cim (the casa converted fits) with matching cim.bdp
#
#   mkcd new
#   ln -s ../../../../data/foobar.fits
#   ../test_ingest.py foobar.fits both
#   $ADMIT/admit/at/test/test_ingest.py foobar.fits both


import admit.Admit as ad
from admit.at.Ingest_AT import Ingest_AT

def run(fileName, method):
    """
    Ingest using ADMIT, and return the ADMIT instance for any
    further analysis
    method:    if blank, only ingest, otherwise use spectrum or stats or both
    """
    # instantiate ADMIT, we can only handle .fits files here
    loc = fileName.rfind('.')
    adir = fileName[:loc] + '.admit'

    a = ad.Admit(adir)
    a.plotmode(0)
    # just set an ADMIT variable
    a.set(foobar=1)
    print 'admit::foobar =',a.get('foobar')

    # Instantiate the AT, add it to ADMIT, and set some Ingest parameters
    a0 = Ingest_AT(file=fileName)
    i0 = a.addtask(a0)

    # run and save
    a.run()
    a.write()

    # inspect BDP? This will be a SpwCube_BDP
    b0 = a0[0]
    print 'BDP_0 has the following images:',b0.image.images

    if True:
        # enable if you want to check if indeed nothing happens here
        print "BEGIN running again"
        a.run()
        print "END running again"


    if method == "moment":
        from admit.at.Moment_AT import Moment_AT
        a1 = Moment_AT()
        i1 = a.addtask(a1, [(i0,0)])
        a1.setkey('moments',[0,1,2])
    elif method == "stats":
        from admit.at.CubeStats_AT import CubeStats_AT
        a1 = CubeStats_AT()
        i1 = a.addtask(a1, [(i0,0)])
    elif method == "spectrum":
        from admit.at.CubeSpectrum_AT import CubeSpectrum_AT
        a1 = CubeSpectrum_AT()
        a1.setkey('pos',[70,70])
        i1 = a.addtask(a1, [(i0,0)])
    elif method == "both":
        # cubestats will pass its maxpos= to cubespectrum
        from admit.at.CubeStats_AT import CubeStats_AT
        from admit.at.CubeSpectrum_AT import CubeSpectrum_AT
        a1 = CubeStats_AT()
        i1 = a.addtask(a1, [(i0,0)])
        a2 = CubeSpectrum_AT()
        i2 = a.addtask(a2, [(i0,0),(i1,0)])
    else:
        print "No method ",method

    print "Final run"
    a.run()
    a.write()
    print "All done. admit.xml written" 
    return a

if __name__ == "__main__":
    import sys
    
    argv = ad.casa_argv(sys.argv)
    if len(argv) > 1:
        if len(argv) == 2:
            # only one argument:  just ingest
            print "Ingesting ",argv[1]
            a = run(argv[1],False)
        else:
            print "Ingesting and running a sample %s on %s" % (argv[2],argv[1])
            a = run(argv[1],argv[2])
        print "One more run, of nothing we hope."
        a.run()
