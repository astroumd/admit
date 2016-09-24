from Table_BDP import Table_BDP
from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

class PeakPointPlot_BDP(Table_BDP,Image_BDP):
    def __init__(self,xmlFile=None):
        Image_BDP.__init__(self,xmlFile)
        Table_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
