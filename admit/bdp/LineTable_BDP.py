from Line_BDP import Line_BDP
from Table_BDP import Table_BDP
import admit.util.bdp_types as bt

class LineTable_BDP(Line_BDP,Table_BDP):    
    def __init__(self,xmlFile=None):
        Line_BDP.__init__(self,xmlFile)
        Table_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
