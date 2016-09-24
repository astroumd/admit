"""**Flow11_AT** --- Test task copying a File_BDP to the output.
   -------------------------------------------------------------
   
   This module defines the Flow11_AT class.
"""
#! /usr/bin/env python

# python system things you need
import sys, os

# admit things you always need
import admit.Admit as admit
from admit.Summary import SummaryEntry
from admit.AT import AT
import admit.util.bdp_types as bt

# depending on what BDP's and AT's you need, import them here
from admit.bdp.File_BDP import File_BDP
from admit.at.File_AT import File_AT


#
#  Flow11_AT is the most simple one-BDP-in one-BDP-out AT.
#  See also HelloWorld_AT() for a nicely annotated one
#  in our standard admit+python style
#  
#  This AT is also supposed to work without CASA, hence
#  the first line being     '#! /usr/bin/env python' 
#
#  It also contains some routines for testing, and commented out
#  code to compare system call vs. native call. Leave those in 
#  please, but the default code is optimized for speed (native
#  calls)
#

class Flow11_AT(AT):
    """Flow11_AT will change one File_BDP into another File_BDP,
    purely to test or emulate a flow. It will also implement an
    example how parameters are added back from the AT to ADMIT
    using the summary feature.

    See also :ref:`Flow-AT-Design` for the design document that
    describes the Flow family.

    Together with Flow1N_AT and FlowN1_AT these are AT's that take
    File_BDP's as input (1 or N), and produce File_BDP's 
    as output (1 or N). 

    Input files pointed to in the BDP's do not have to exist, but the
    AT can be forced to check for those (**exist=True**).

    Output files listed in the BDP's can be ignored, but can also
    be created as 0-length files (**touch=True**).

    The use of "**exist**" and "**touch**" thus symmetrizes the way how
    the Flow*_AT's can be used to emulate the dependancy of a flow
    on file existence and/or creation.

    Flow11_AT adds the following to ADMIT summary::

       datamin: real
          The datamin parameter of foobar.

       datamax: real
          The datamin parameter of foobar.

       rmsmethd: dictionary
          A list describing the rms method.


    **Keywords**

      **file**: string
          Output filename created, from which the BDP is named as well
          as "<file>.bdp".  The BDP is always created. The file itself
          will depend on the touch= keyword.
          If the filename is blank, it will generate an output filename
          by appending _11 to the input filename.

      **touch**: bool
          Create a 0-length file that the output BDP will point to [True].

      **exist**: bool
          Input file that belongs to a BDP must exist to pass [True].

    **Input BDPs**

      **File_BDP**: count: 1
          Test input.

    **Output BDPs**

      **File_BDP**: count: 1
          Test output.
    """

    def __init__(self,**keyval):
        keys = {"file" : "",      
                "touch": True,   
                "exist": True}   
        AT.__init__(self,keys,keyval)
        self._version   = "1.0.0"
        self.set_bdp_in ([(File_BDP,1,bt.REQUIRED)])
        self.set_bdp_out([(File_BDP,1)])

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.  
        """
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}

    def userdata(self):
        """Returns the user data dictionary from the AT, for merging
           into the ADMIT user data object.  
        """
        if hasattr(self,"_userdata"):
            return self._userdata
        else:
            return {}


    def run(self):
        """ **run Flow11_AT** """

        def touch1(fname):
            """ a native python "touch" barely adds overhead 
                (maybe 0.2" on 10000 operations)
                This is a fast helper function of run
            """
            print "run:: TOUCH1",fname
            if os.path.exists(fname):
                os.utime(fname,None)
            else:
                open(fname,'a').close()

        def exist1(fname):
            """ ensure that a file exists.
                This is a fast helper function of run
            """
            if not os.path.exists(fname):
                raise Exception,'run::Flow11_AT: file %s does not exist' % fname
            else:
                print "run::Flow11_AT file %s exists" % fname

        # make room for BDP's
        self.clearoutput()

        # make sure there is 1 input BDP   (using self.valid_bdp will clean up this code)
        # do we need this with self._valid_bdp_in ???
        if len(self._bdp_in) != 1:
            raise Exception,"run::Flow11_AT: need one BDP_in (%d given)" % len(self._bdp_in)

        # report 
        print "run::Flow11_AT  Input filename: ",self._bdp_in[0].filename

        # handle exist= to see if the file needs to exist to run this code
        exist = self.getkey('exist')
        if exist: self._bdp_in[0].checkfiles()

        # get the output filename for the output BDP (no automatic naming here)
        filename = self.getkey('file')
        if filename == None:
            raise Exception,'run::Flow11_AT  no file= given, there is no default yet'
        if len(filename) == 0:
          # derive from input file
          alias = self._alias
          filename = self._bdp_in[0].filename + ('-'+alias if alias else '_11')

        # create the output BDP
        bdp1 = File_BDP(filename)
        bdp1.filename = filename
        bdp1.alpha    = 1.0                # you can add some attribute, but it won't be saved in the BDP
        self.addoutput(bdp1)

        # handle touch= to ensure the output file exists or has been modified
        if self.getkey('touch'): bdp1.touch()

        self._userdata = {}
        self._userdata['mwptest'] = ['Eye', 8, 'Pi']
        self.summarize()
        # run() all done!

    def summarize(self):
        """Convenience function to populate dictionary for
           items to add to the ADMIT Summary.
        """
        self._summary = {}

        # finally, set some parameters for the ADMIT summary
        abc_list= ['robust', 'chauvenet', 21.3, 123]
        self._summary['datamin'] = SummaryEntry(3.14159,"Flow11_AT",taskid=self.id(True))
        self._summary['datamax']  = SummaryEntry(2.71828,"Flow11_AT",taskid=self.id(True))
        self._summary['rmsmethd'] = SummaryEntry(abc_list,"Flow11_AT",taskid=self.id(True))
        print "Flow11_AT taskid = %d" % self.id(True)

        
    # class function(s) for just Flow11 now follow:
    # you can also make them functions inside of run
    def touch2(self,fname):
        """ a native python "touch" barely adds overhead 
        (maybe 0.2" on 10000 operations)
        This is a helper member function of the class,
        compare this with touch1, which is a local
        helper function to run().
        """
        print "run:: TOUCH2",fname

        if os.path.exists(fname):
            os.utime(fname,None)
        else:
            open(fname,'a').close()

