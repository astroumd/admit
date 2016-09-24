from admit.at.HelloWord_AT import HelloWorld_AT
import admit.util.bdp_types as bt
from admit.bdp.HelloWorld_BDP import HelloWorld_BDP

"""HelloWorld2
   ----------

   Defines the HelloWorld2 class.
"""

# =================================================================

class HelloWorld2_AT(HelloWorld_AT):
    """ Derived AT class example
        Derived classes go about it slightly differently
    """
    def __init__(self,**keyval):
        """ Constructor
        """
        # set up the keys for the derived class
        keys = {"moon":""}
        # initialize the base class, do not add the new keys yet or they will be lost
        HelloWorld_AT.__init__(self)
        # add the new keys and set any values given, again
        #  keyval cannot name any new keys, just define values
        self.addkeys(keys,keyval)
        # set the attributes that are static
        self._version = "1.0.0"
        self._valid_bdp_out =[(HelloWorld_BDP,1)])


    def run(self):
        HellowWorld_AT.run()
        filename = "test.txt"
        hw = HelloWorld_BDP()
        hw.moon = self.getkey("moon")
        self.addoutput(hw)

