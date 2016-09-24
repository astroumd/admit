import admit.util.bdp_types as bt
from Table_BDP import Table_BDP
from Image_BDP import Image_BDP

class FeatureList_BDP(Image_BDP,Table_BDP):
    def __init__(self,xmlFile=None):
        Table_BDP.__init__(self,xmlFile)
        Image_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
