#! /usr/bin/env python
#
#  A large flow (timings from Peter's laptop)
#  % time flow1N-at.py > /dev/null
#
#            touch=1                                touch=0                     no 2nd (dummy) run
#  10:     0.179u  0.136s 0:00.31  96.7%	
#  100:    0.278u  0.922s 0:01.19 100.0%
#  200:    0.759u  1.741s 0:02.49 100.0%
#  400:    3.482u  3.288s 0:06.74 100.2%    3.341u 1.724s 0:05.05 100.1%    1.804u 1.604s 0:03.39 100.2%
#  1000:  48.771u  8.919s 0:57.69  99.9%   46.988u 4.251s 0:51.24  99.9%   23.860u 4.683s 0:28.54 100.0%
#  2000: 383.488u 16.440s 6:40.07  99.9%  378.568u 9.225s 6:28.04  99.9%

import sys, os
import admit2 as admit

# number of flow() calls
n = 1000

a = admit.ADMIT('flow1N')

# grow a series of ATi's (AT index)
ati=[]
ati.append(a.add(admit.AT_file("flow1N-0")))
for i in range(1,n+1):
    ati.append( a.add(  admit.AT_flow("flow1N-%d" % i) ,  [(ati[i-1],0)] ))
    a[ati[i]].set('touch=0')
a.run()

if False:
    print "And again"
    a.run()

