#! /usr/bin/env python
#
#
#    similar to test_FM, but in the official ADMIT environment
#    these are meant to be able to run without CASA, ie. in a
#    vanilla python environment, hence the first line in this
#    script.
#
#    Note here you cannot run a series of AT's, you need to
#    chain them via Admit()
#
#  test_Flow:        File + Flow11
#  test_Flow_many:   File + N x Flow11
#  test_FlowN1:      N x File  + FlowN1
#  test_Flow1N:      File  + Flow1N x N + subdir option with another N x Flow11
#  test_FlowMN:

import sys, os


# admit/__init__.py:
# from AT          import AT          as Task
# from Admit       import Admit       as Project
if True:
    from admit.AT import AT
    import admit.Admit as admit
else:
    import admit


if True:
    # here we need "a1 = File_AT()"
    from admit.at.File_AT import File_AT      
    from admit.at.Flow11_AT  import Flow11_AT 
else:
    # here we need "a1 = at.File()" 
    import admit.at as at
    


if __name__ == '__main__':

    touch = True
    exist = True
    rerun = True
    subdir = False
    #subdir = True       #?  fails when enabled on re-run, but see test_Flow0.py

    #  pick where admit will do its work, the given argument directory or current directory
    if len(sys.argv) > 1:
        a = admit.Admit(sys.argv[1])
    else:
        a = admit.Admit()

    print 'Flow11:  new admit?',a.new
    if rerun and not a.new:
        print 'LEN:',len(a)
        # with Parser.py version 1.26 the following lines are wrong
        # with                   1.28 it's fixed
        print "a[0]._keys:",a[0]._keys
        print "a[1]._keys:",a[1]._keys
        a.run()
        #
        #   for a True/False combo below this will fail
        #   but will also show stale=True/False and then
        #   still runs Flow11, so perhaps that debug output is flawed??
        #   so lets fix the addinput() reporting error first
        if True:
            a[0].setkey('file','Flow11-0a.dat')
            print "a[0]._keys:",a[0]._keys
        if False:
            a[1].setkey('file','Flow11-1a.dat')
            print "a[1]._keys:",a[1]._keys
        a.run()
        print 'LEN:',len(a)
        a.write()
        print "USERDATA: ", a.userData
        sys.exit(0)

    a1 = File_AT()
    #a1 = File_AT(file='Flow11-0.dat',touch=touch,exist=False)                # alternative-1
    #i1 = a.addtask(File_AT(file='Flow11-0.dat',touch=touch,exist=False))     # alternative-2
    i1 = a.addtask(a1)
    a1.setkey('file','Flow11-0.dat')
    a1.setkey('touch',True)
    a1.setkey('exist',False)
    print "a1._keys:",a1._keys

    a2 = Flow11_AT()
    i2 = a.addtask(a2, [(i1,0)])
    if subdir:
        # this is to test if subdirectories work
        # @todo doesn't work yet on re-run, see test_Flow0.py, but it works if you continue in the same script
        a.mkdir('test')
        a2.setkey('file','test/Flow11-1.dat') 
    else:
        a2.setkey('file','Flow11-1.dat') 
    a2.setkey('touch',touch)
    a2.setkey('exist',exist)

    a3 = Flow11_AT()
    i3 = a.addtask(a3, [(i2,0)])
    a3.setkey('file','Flow11-2.dat') 
    a3.setkey('touch',touch)
    a3.setkey('exist',exist)

    #
    a.run()
    a.run()
    print "a1.len2=",a1.len2()
    print "a2.len2=",a2.len2()
    #
    a.write()
    print "USERDATA: " , a.userData
    #
    # these are the same:
    #print "a1=",a1
    #print "a.fm[0]=",a.fm[0]

    print "Final waving from ",a.dir()
