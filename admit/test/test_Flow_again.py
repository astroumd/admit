#! /usr/bin/env python
#
#
#   test_Flow_again.py : like test_Flow but then appending Flow11's at the end, 
#                        assuming nothing has changed. Can be re-run at nauseum.

import sys, os

from admit.AT import AT
import admit.Admit as admit
from admit.at.File_AT import File_AT
from admit.at.Flow11_AT  import Flow11_AT


if __name__ == '__main__':

    print "Flow11_again:"

    #  pick a directory where admit will do its work (or else use current directory)
    if len(sys.argv) > 1:
        a = admit.Admit(sys.argv[1])
    else:
        a = admit.Admit()

    print "=== test_Flow_again: first time, just create a File to bootstrap the flow"
    i1 = a.addtask(File_AT(file='Flow11-0.dat',touch=True,exist=False)) 
    print "NEW TASK",i1
    a.run()

    # Append one more Flow11 to whatever is already there.
    # To simulate re-running a typical ADMIT script, we still need to 
    # manually re-add ALL prior Flow11 tasks. It should also work to just
    # update the global task ID instead, but this isn't what a user would do...
    print "=== test_Flow_again: append a Flow11_AT to the end of the existing flow"

    # this assumes no tasks were deleted and taskid's were added from 0,1,2,...
    n = len(a)
    print "Found %d tasks" % n
    print "last filename: ",a[n-1][0].filename
    tid=1
    while tid <= n:
        stuple = [(tid-1, 0)]       # previous BDP output
        filename = 'Flow11-%d.dat' % tid
        print "new filename: ",filename
        i3 = a.addtask(Flow11_AT(file=filename,touch=True,exist=True), stuple)
        print "NEW TASK",i3
        if i3 < 0:
            raise Exception,"bad task adding in a re-run"
        tid += 1
    #
    a.run()
    a.write()
