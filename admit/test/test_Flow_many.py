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

# performance (on nemo2):                time test_Flow_many.py > /dev/null
#            touch=False                        touch=True
#     100    ...
#    1000    1.421u 0.159s 0:01.59 98.7%        1.596u  2.703s 0:04.31         (run after the loop)
#            1.547u 0.203s 0:01.75 99.4%        2.195u  2.885s 0:05.12 99.0%   (run inside loop)
#   10000   41.225u 2.012s 0:43.42 99.5%       44.822u 35.575s 1:20.89 99.3%   (run after the loop)	
#           79.907u 2.015s 1:22.09 99.7%                                       (run inside loop)
#
# (10000,True) is the default bench, thus nemo2 goes in 1:21
#                                       inferno goes in 1:53 (yipes, and /dev/shm didn't help)
#                                        subaru         1:52
#
# Perhaps a puzzle remaining:
# 44.617u 32.582s 1:18.29 98.5%	0+0k 4000+1285208io 0pf+0w        with jprev=j reset forgotten
# 10.900u 37.063s 0:49.00 97.8%	0+0k 9176+165632io 47pf+0w        proper serial operation
# 45.870u 36.884s 1:24.04 98.4%	0+0k  544+1285208io 7pf+0w
#
# On Mar 11 the benchmark ran faster:
# 10000      8.204u 0.927s 0:09.18 99.3%       11.022u 42.730s 0:54.09 99.3%    os.system()
#            8.111u 0.935s 0:09.07 99.6%        8.034u 1.201s 0:09.27 99.5%     self.touch()
import sys, os

from admit.AT import AT
import admit.Admit as admit
from admit.at.File_AT import File_AT
from admit.at.Flow11_AT  import Flow11_AT


if __name__ == '__main__':
    n = 10
    touch = True
    exist = True

    print "Flow11_many:"

    #  pick where admit will do its work
    if len(sys.argv) > 1:
        # use the argument as a (new or existing) directory 
        a = admit.Admit(sys.argv[1])
    else:
        # use the current directory
        a = admit.Admit()

    print "a.new: ",a.new

    i = range(n+1)                           # dummy array to hold the task ID's

    i[0] = a.addtask( File_AT() )            # first task: File_AT bootstrap
    a[i[0]].setkey('file','Flow11-0.dat')
    a[i[0]].setkey('touch',touch)
    a[i[0]].setkey('exist',False)
    jprev = i[0]

    for j in range(1,n+1):                   # loop over a chain of Flow11_AT's
        i[j] = a.addtask( Flow11_AT(), [(jprev,0)] )
        a[i[j]].setkey('file','Flow11-%d.dat' %j)
        a[i[j]].setkey('touch',touch)
        # comment out the next line for the puzzling behavior
        jprev = j
        # a.run()
        #
    print "RUN"
    a.run()
    #
    print "WRITE"
    a.write()
    print 'Flow11:  done!'
