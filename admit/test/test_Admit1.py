#! /usr/bin/env python
#
#
#    very simple Admit test, with no flow, showing saving and retrieving user variables
#    in a project using Admit.set() and Admit.get()
#    You can re-run this script several times, and watch a execution count variable (n)
#    increase for each re-run.
#    This script can also be told to run in another directory, relative or absolute,
#    and will create that directory.
#

import sys, os

import admit.Admit as admit


if __name__ == '__main__':

    if len(sys.argv) > 1:
        a = admit.Admit(sys.argv[1])
    else:
        a = admit.Admit()

    if a.new:
        print "Starting a new Admit (iteration n=0) in %s" % a.dir()
        a.set(n=1)
        a.set(a=1)
        a.set(b=[])
        print "n=",a.get('n'),type(a.get('n'))
    else:
        if a.has("n"):
            n = a.get("n")
        else:
            # should never happen
            n = 0
            raise ValueError, "admit.xml did not contain userData['n']"
        print "Reading previous admit.xml (iteration n=%d)" % n
        print "a=",a.get("a")
        b = a.get("b")
        b.append(n)
        a.set(b=b)
        print "b=",b
        if a.has("c"):
            print "c=",a.get("c")
        else:
            a.set(c='3')
        n = n + 1
        a.set(n=n)

    # harmless, since there isn't anything to run here
    a.run()
    print "len->",len(a)
    
    # write out the admit.xml
    a.write()

    print "Final waving from ",a.dir()
