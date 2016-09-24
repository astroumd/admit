"""HelloWorld
   ----------

   Defines the HelloWorld class.
"""
from admit.AT import AT
from admit.bdp.HelloWorld_BDP import HelloWorld_BDP

class HelloWorld_AT(AT):
    """ Basic example of an ADMIT Task

        Parameters
        ----------
        keyval : keyword - value pairs passed to the constructor for ease
            of assignment.

        Attributes
        ----------
        None
    """
    def __init__(self,**keyval):
        # set the key words up with default values
        keys = {"yourname": "",
                "planet"  : ""}
        AT.__init__(self,keys,keyval)
        self._version = "1.0.0"

        # must call even if task takes no input bdp, so that
        # various internal AT values are set correctly
        self.set_bdp_in() 

        self.set_bdp_out([(HelloWorld_BDP,1)])
        self._bdp_in_order_list = []
        self._bdp_in_order_type = []

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.  
        """
        if hasattr(self,"_summary"):
            return self._summary
        else:
            return {}


    def run(self):
        # Destroy old output BDPs before rebuilding the output BDP list.
        # Omit this call if you will reuse existing BDPs.
        self.clearoutput()

        filename = "test.txt"
        hw = HelloWorld_BDP()
        hw.yourname = self.getkey("yourname")
        hw.planet = self.getkey("planet")
        if self.getkey("planet") == "Earth" :
            hw.star = "Sol"
        else:
            hw.star = "Unknown"
        hw.favoritefile = filename
        self.addoutput(hw)

