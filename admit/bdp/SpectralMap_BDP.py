from Table_BDP import Table_BDP
import admit.util.bdp_types as bt

class SpectralMap_BDP(Table_BDP):
    def __init__(self,xmlFile=None):
        Table_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
