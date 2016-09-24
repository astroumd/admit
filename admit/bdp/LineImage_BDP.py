from Line_BDP import Line_BDP
from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

class LineImage_BDP(Line_BDP,Image_BDP):    
    def __init__(self,xmlFile=None):
        Line_BDP.__init__(self,xmlFile)
        Image_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
