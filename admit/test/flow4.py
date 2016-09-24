#! /usr/bin/env python
#
#  Flow with one junction coming back w/ dependency
#  b0 is first created,  b1 and b2 next, b3 is combined 
#  out of b1 and b2 together.  Read this diagram left
#  to right.
#
#  BDP centric flow (read it left to right)
#
#      /--b1--\
#    b0        b3
#      \--b2--/
#
#  AT centric flow (read it left to right)
#   
#      /--a2--\
#    a1        a4
#      \--a3--/
#
import sys, os
import admit2 as admit

a = admit.ADMIT()

if False:
    # liberal notation, you can see the AT's, although you don't need them
    # you do need the ATI's for the connection map tuples.
    a1 = admit.AT_file("flow4a")
    i1 = a.add(a1)
    a1.run()
    b0 = a1[0]

    a2 = admit.AT_flow("flow4b")         # this sets the bdp_out's
    i2 = a.add(a2, [(i1,0)] )            # this sets the bdp_in's
    a2.run()
    b1 = a2[0]

    a3 = admit.AT_flow("flow4c")
    i3 = a.add(a3, [(i1,0)] )
    a3.run()
    b2 = a3[0]

    a4 = admit.AT_flow21("flow4d")
    i4 = a.add(a4, [(i2,0),(i3,0)])
    a4.run()
    b3 = a4[0]
else:
    # most compact notation, only the ATI's (i1..i4) are needed
    # this shows how all the tasks are set up (this may not always be possible)
    # and then executed using ADMIT.run()

    i1 = a.add(admit.AT_file("flow4a") )
    i2 = a.add(admit.AT_flow("flow4b"),     [(i1,0)] )
    i3 = a.add(admit.AT_flow("flow4c"),     [(i1,0)] )
    i4 = a.add(admit.AT_flow21("flow4d"),   [(i2,0),(i3,0)])
    #
    if True:
        print "LEN: ",len(a)
        for i in range(len(a)):
            print "LEN(%d): %s" % (i,a[i].len2())
            a[i].set('touch=1')
    #
    a.run()
    if True:
        print "All done.  Now lets try running again, now 4c and 4d should be re-created"
        a[i3].set('touch=1')
        a.run()

a.show()
