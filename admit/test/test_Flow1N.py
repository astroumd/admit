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


if __name__ == '__main__':
    n = 3
    touch = True
    subdir = False
    subdir = True

    #  pick where admit will do its work, any cmdline argument will be the dirname
    if len(sys.argv) > 1:
        a = admit.Admit(sys.argv[1])
    else:                                 # or else the current directory
        a = admit.Admit()

    print 'Flow11:  new admit?',a.new

    a1 = File_AT()
    i1 = a.addtask(a1)
    a1.setkey('file','Flow1N.dat')
    a1.setkey('touch',touch)

    a2 = Flow1N_AT()
    i2 = a.addtask(a2, [(i1,0)])
    a2.setkey('n',n)
    a2.setkey('touch',touch)
    a2.setkey('subdir',subdir)
    #
    if True:
        # continue with a Flow11 for each BDP created by Flow1N
        from admit.at.Flow11_AT  import Flow11_AT
        a.run()            # need to run the flow, otherwise #BDP's unknown
        n1 = len(a2)       # of course n1 = n, but we don't know this
        a3 = range(n1)     # a list of AT's
        i3 = range(n1)     # a list of ATID's
        for i in range(n1):
            a3[i] = Flow11_AT()
            i3[i] = a.addtask(a3[i], [(i2,i)])
            a3[i].setkey('touch',touch)
    #
    a.run()
    #
    a.write()

