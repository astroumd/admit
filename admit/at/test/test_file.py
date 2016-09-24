#! /usr/bin/env python
# 
#
#   you can either use the "import" method from within casapy
#   or use the casarun shortcut to run this from a unix shell
#   with the argument being the casa image file to be processed
#
#   Typical test usage:
#       ./test_file.py   test123
#   This will produce admit.xml and test123 (0 length file) 
#   and test123.bdp.
#

import admit.Admit as ad
from admit.at.File_AT import File_AT

def run(fileName=None, touch=False):
    # instantiate ADMIT
    a = ad.Admit()

    # Instantiate the class.  This can be done in two ways, both will
    # work, it just depends if you need 'a0' ('i0' you always need)
    if True:
        # the AT, then the ATI
        a0 = File_AT()
        i0 = a.addtask(a0)
    else:
        # get the ATI via ADMIT, but then grab AT reference for convenience 
        i0 = a.addtask(File_AT())
        a0 = a[i0]
    
    # set some keys
    a0.setkey('file', fileName)
    a0.setkey('touch', False)
    a0.setkey('exist', True)


    # run the task(s). This also can be done in two ways.
    if False:
        # run only this one task, but it bypassed some checks in FlowManager
        # so for example, calling it twice, will run it twice
        # after running, explicit BDPs would need to be saved
        a0.run()
        a0[0].write()
    else:
        # run the whole ADMIT flow, although it's just one task (a0)
        # but calling it twice, 2nd run would not run the task since 
        a.run()
        a.write()

if __name__ == "__main__":
    import sys
    
    #argv = ad.casa_argv(sys.argv)
    argv = sys.argv
    if len(argv) > 1:
        print "Working on ",argv[1]
        if len(argv) == 2:
            run(argv[1])
        else:
            run(argv[1], True)
