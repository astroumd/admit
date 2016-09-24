#! /usr/bin/env python
#
#
# boostrapping a new AT
#
# after the AT (and perhaps an asscociated BDP) have been added
#
# cp $ADMIT/doc/examples/HelloWorld_AT.py  $ADMIT/admit/at
# cp $ADMIT/doc/examples/HelloWorld_BDP.py $ADMIT/admit/bdp
# dtdGenerator

import sys, os



from admit.AT import AT
import admit.Admit as admit

from admit.at.File_AT import File_AT      
from admit.at.HelloWorld_AT  import HelloWorld_AT 


if __name__ == '__main__':

    a = admit.Admit()

    a1 = HelloWorld_AT()
    i1 = a.addtask(a1)
    a1.setkey('yourname','hubble')
    a1.setkey('planet','earth')


    a.run()
    a.write()
