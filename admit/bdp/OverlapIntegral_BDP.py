from Image_BDP import Image_BDP
from Table_BDP import Table_BDP
from admit.util.Line import Line
import admit.util.bdp_types as bt

class OverlapIntegral_BDP(Image_BDP,Table_BDP):
    def __init__(self,xmlFile=None):
        Image_BDP.__init__(self,xmlFile)
        Table_BDP.__init__(self,xmlFile)
        self.line1 = Line()
        self.line2 = Line()
        self._version= "0.1.0"
