#! /usr/bin/env python
#
#
#    like test_Flow.py, but re-run with a subdir option
#

import sys, os


from admit.AT import AT
import admit.Admit as admit

from admit.at.File_AT import File_AT      
from admit.at.Flow11_AT  import Flow11_AT 

if __name__ == '__main__':

    touch = True
    exist = True
    rerun = True
    subdir = False
    subdir = True       # broken on a re-run if you enable this

    #  pick where admit will do its work, the given argument directory or current directory
    if len(sys.argv) > 1:
        a = admit.Admit(sys.argv[1])
    else:
        a = admit.Admit()

    print 'Flow11:  new admit?',a.new
    if not a.new:
        print 'LEN:',len(a)
        print "a[0]._keys:",a[0]._keys
        print "a[1]._keys:",a[1]._keys
        a.run()
        print "run done"
        a.write()
        sys.exit(0)

    a1 = File_AT()
    i1 = a.addtask(a1)
    a1.setkey('file','Flow11-0.dat')
    a1.setkey('touch',True)
    a1.setkey('exist',False)
    print "a1._keys:",a1._keys

    a2 = Flow11_AT()
    i2 = a.addtask(a2, [(i1,0)])
    if subdir:
        # this is to test if subdirectories work  (26-apr, fails to work again on 2nd run)
        a.mkdir('test')
        a2.setkey('file','test/Flow11-1.dat') 
    else:
        a2.setkey('file','Flow11-1.dat') 
    a2.setkey('touch',touch)
    a2.setkey('exist',exist)

    # 
    a.run()
    print "a1.len2=",a1.len2()
    print "a2.len2=",a2.len2()
    #
    a.write()
    #
    # these are the same:
    #print "a1=",a1
    #print "a.fm[0]=",a.fm[0]

    print "Final waving from ",a.dir()
