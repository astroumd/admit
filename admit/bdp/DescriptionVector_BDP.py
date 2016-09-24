from BDP import BDP
import admit.util.bdp_types as bt

class DescriptionVector_BDP(BDP):
    def __init__(self,xmlFile=None):
        BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
