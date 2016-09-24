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



import sys, os

from admit.AT import AT
import admit.Admit as admit
from admit.at.File_AT import File_AT
from admit.at.FlowN1_AT  import FlowN1_AT


if __name__ == '__main__':

    #  pick where admit will do its work
    if len(sys.argv) > 1:
        # use the argument as a (new or existing) directory 
        a = admit.Admit(sys.argv[1])
    else:
        # use the current directory
        a = admit.Admit()

    print 'FlowN1:  new admit?',a.new

    a1 = File_AT()
    i1 = a.addtask(a1)
    a1.setkey('file','FlowN1-1.dat')
    a1.setkey('touch',True)

    a2 = File_AT()
    i2 = a.addtask(a2)
    a2.setkey('file','FlowN1-2.dat')
    a2.setkey('touch',True)

    a3 = File_AT()
    i3 = a.addtask(a3)
    a3.setkey('file','FlowN1-3.dat')
    a3.setkey('touch',True)

    a4 = File_AT()
    i4 = a.addtask(a4)
    a4.setkey('file','FlowN1-4.dat')
    a4.setkey('touch',True)

    bdps = [(i1,0),(i2,0),(i3,0),(i4,0)]

    a5 = FlowN1_AT()
    i5 = a.addtask(a5, bdps)
    a5.setkey('file','FlowN1-5.dat')     # should have a default, for now hardcode it
    a5.setkey('touch',True)
    #
    a.run()
    #
    a.write()

