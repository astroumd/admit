#! /usr/bin/env python
#
#
#    similar to test_FM, but in the official ADMIT environment
#    these are meant to be able to run without CASA, ie. in a
#    vanilla python environment
#
#    you might need to run
#          rm ../at/__init__.py ../at/__init__.pyc ; touch ../at/__init__.py
#    before, and reset this file using
#          dtdGenerator
#    if CASA sits in the way

# performance (on nemo2):                time test_Flow_5.py > /dev/null
#            touch=False                        touch=True
#     100    ...
#    1000    0.582u 0.096s 0:00.68 98.5%       0.794u  2.267s 0:03.19 95.6%
#   10000    4.004u 0.522s 0:04.57 98.9%       5.401u 22.515s 0:28.56 97.7%
#           
#
# (10000,True) is the default bench, thus nemo2 goes in 1:21
#                                       inferno goes in 1:53 (yipes, and /dev/shm didn't help)
#                                        subaru         1:52
#


import sys, os

from admit.AT import AT
import admit.Admit as admit
from admit.at.File_AT import File_AT
from admit.at.Flow1N_AT  import Flow1N_AT
from admit.at.FlowN1_AT  import FlowN1_AT
from admit.at.FlowMN_AT  import FlowMN_AT


if __name__ == '__main__':
    # @todo   some are hardcoded, not ready for scaling tests
    m = 3     
    n = 4     

    touch = True
    subdir = True

    # pick between two_step True (old method)  and False (new method)
    two_step = False
    two_step = True

    #  pick where admit will do its work
    if len(sys.argv) > 1:
        # use the argument as a (new or existing) directory 
        a = admit.Admit(sys.argv[1])
    else:
        # use the current directory
        a = admit.Admit()

    print 'FlowMN:  new admit?',a.new

    if two_step:
        # this will use Flow1N_AT and FlowN1_AT

        # first create a single File_BDP
        a1 = File_AT()
        i1 = a.addtask(a1)
        a1.setkey('file','FlowMN-0.dat')
        a1.setkey('touch',touch)

        # turn 1 into M
        a2 = Flow1N_AT()
        i2 = a.addtask(a2, [(i1,0)])
        a2.setkey('n',m)
        a2.setkey('file','FlowMN-1.dat')
        a2.setkey('touch',touch)
        a2.setkey('subdir',subdir)

        # get a list of BDP's for the next step, but we need to run the flow first
        a.run()
        n = len(a2)
        if n != m: print "BAD"
        bdps=[]
        for i in range(n):
            bdps.append( (i2,i) )

        # bring the M back to 1
        a3 = FlowN1_AT()
        i3 = a.addtask(a3,bdps)
        a3.setkey('file','FlowMN-3.dat')
        a3.setkey('touch',touch)


    else:
        # this will use a single FlowMN_AT
        a1 = File_AT()
        i1 = a.addtask(a1)
        a1.setkey('file','FlowMN-1.dat')
        a1.setkey('touch',True)

        a2 = File_AT()
        i2 = a.addtask(a2)
        a2.setkey('file','FlowMN-2.dat')
        a2.setkey('touch',True)

        bdps = [(i1,0),(i2,0)]
        m = len(bdps)

        a3 = FlowMN_AT()
        i3 = a.addtask(a3, bdps)
        a3.setkey('file','FlowMN-3.dat')     # should have a default, for now hardcode it
        a3.setkey('touch',True)
        a3.setkey('n',n)

    #
    a.run()
    #
    a.write()

    #
    print "All done. We actually used m=%d n=%d with two_step=%s" % (m,n,two_step)
