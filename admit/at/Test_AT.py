"""**Test_AT** --- Task for testing various ADMIT features.
   --------------------------------------------------------

   This module defines the Test_AT class.
"""
from admit.AT import AT
import admit.util.bdp_types as bt
from admit.bdp.BDP import BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.PVCorr_BDP import PVCorr_BDP
from admit.bdp.SpwCube_BDP import SpwCube_BDP
from admit.bdp.Moment_BDP import Moment_BDP
from admit.bdp.Line_BDP import Line_BDP
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.Table_BDP import Table_BDP

class Test_AT(AT):
    def __init__(self):
        AT.__init__(self)
        self.valid_BDP = []                   # the listing of valid input BDP types
        self.bdp_out_types = []               # the listing of output bdp types
        """
            Format for valid input BDP type dictionary:
                (Moment_BDP, 1,bt.REQUIRED)      Moment_BDP is a required input
                (SpwCube_BDP,1,bt.OPTIONAL)      SpwCube_BDP is an optional input
                (Moment_BDP, 3,bt.REQUIRED)      3 Moment_BDP's are required (*0 means any number)
                (bt.ONE_OF,  [bt.MOMENT_BDP,bt.SPWCUBE_BDP]) 
                                                 One of Moment_BDP or SpwCube_BDP is required
                (bt.IF_THEN, {bt.MOMENT_BDP: bt.IMAGE_BDP,
                              bt.TABLE_BDP:bt.CUBESTATS_BDP})
                                                 If a Moment_BDP is found then an Image_BDP must
                                                 also be supplied. If a Table_BDP is found then a
                                                 CubeStats_BDP must also be supplied. Only one of
                                                 the pairs can be supplied
            Note that in order to properly process, derived classes must be listed before
                base classes (i.e. Moment_BDP must be listed before Image_BDP) in valid_BDP
        """
    
        
    def validateinput(self,describe = False):
        """
            Method to validate the BDP_in's against a dictionary of expected types.
            Returns False if anything is amiss.
            If describe == True then the return is a tuple containing True/False and
            a list of what was found/not found.
        """
        valid = [False] * len(self.valid_BDP)
        counted = [False] * len(self.bdp_in)
        results = []
        count = 0
        for key in self.valid_BDP :
            if(callable(key[0]) and issubclass(key[0],BDP)):
                num_needed = key[1]
                num_found = 0

                bdp = key[0]
                for i in range(0,len(self.bdp_in)) :    # iterate over the input items
                    if(issubclass(self.bdp_in[i],bdp) and not counted[i]) :
                        counted[i] = True
                        num_found += 1
                if((num_found == num_needed and num_needed > 0) or (num_found > 0 and num_needed == 0)) :
                    results.append(bdp().type + ": Found")
                    valid[count] = True
                elif(num_found == 0) :
                    if(key[2] == bt.REQUIRED):
                        results.append(bdp().type + ": Missing input BDP")
                    else :     # assume it is optional
                        results.append(bdp().type + ": Optional bdp not found")
                        valid[count] = True
                elif(num_found > num_needed):
                    results.append(bdp().type + ": Too many found(%i), %i needed" % (num_found,num_needed))
                else :
                    results.append(bdp().type + ": Too few found(%i), %i needed" % (num_found,num_needed))

            elif(bt.ONE_OF in key[0]):
                line = "["
                found = 0
                for bdp in key[1] :  # iterate over the list
                    line += bdp().type + ","
                    for i in range(0,len(self.bdp_in)) :    # iterate over the input items
                        if(issubclass(self.bdp_in[i],bdp)) :
                            counted[i] = True
                            found += 1
                line = line[:-1] + "]"
                if(found == 0) :
                    results.append(line + ": Missing one of these input BDP's")
                elif(found == 1) :
                    results.append(line + ": Found")
                    valid[count] = True
                else :
                    results.append(line + ": Too many input BDP's found(%i), only 1 accepted of these types" % (found))
            elif(bt.IF_THEN in key[0]) :
                found = 0
                for main in key[1] :
                    last = key[1][main]
                    foundmain = False
                    foundlast = 0
                    for i in range(0,len(self.bdp_in)) :    # iterate over the input items
                        if(issubclass(self.bdp_in[i],main)) :
                            counted[i] = True
                            foundmain = True
                            found += 1
                    if(foundmain) :
                        for i in range(0,len(self.bdp_in)) :    # iterate over the input items
                            if(issubclass(self.bdp_in[i],last) and not counted[i]) :
                                counted[i] = True
                                foundlast +=1
                        if(foundlast == 0) :
                            results.append(last().type + ": Missing input BDP")
                        elif(foundlast == 1 ):
                            results.append(main().type + ":" + last().type + ": Found")
                            valid[count] = True
                        else :
                            results.append(last().type + ": Too many found (%i), only one allowed" % (foundlast))
                if(found == 0) :
                    valid[count] = False
                    line = ""
                    for k,v in key[1].iteritems() :
                        line += " %s:%s or" % (k().type,v().type)
                    line = line[:-3]
                    results.append("Missing BDP pair:%s" % line)
                elif(found > 1) :
                    valid[count] = False
                    line = ""
                    for k,v in key[1].iteritems() :
                        line += " %s:%s or" % (k().type,v().type)
                    line = line[:-3]
                    results.append("Only 1 BDP pair allowed:%s" % line)
            else :
                raise Exception,"Improperly formatted valid_BDP"
            count += 1
        if(not all(counted)) :
            valid[0] = False
            line = "Unexpected input BDPs: "
            for i in range(0,len(counted)) :
                if(not counted[i]) :
                    line += self.bdp_in[i]().type + ","
            line = line[:-1]
            results.append(line)
        if(describe) :
            return all(valid),results
        return all(valid)
    
    def test1(self):  # optional
        self.valid_BDP = [(Image_BDP,1, bt.OPTIONAL),
                          (Table_BDP,3, bt.OPTIONAL),
                          (Line_BDP, 0, bt.OPTIONAL)]
        print self.validateinput(True),"\n"                  # PASS
        self.bdp_in = [Image_BDP]
        print self.validateinput(True),"\n"                  # PASS
        self.bdp_in = [Image_BDP,Image_BDP]
        print self.validateinput(True),"\n"                  # FAIL
        self.bdp_in = [Image_BDP,Table_BDP]
        print self.validateinput(True),"\n"                  # FAIL
        self.bdp_in = [Image_BDP,Table_BDP,Table_BDP,Table_BDP]
        print self.validateinput(True),"\n"                  # PASS
        self.bdp_in = [PVCorr_BDP,PVCorr_BDP,PVCorr_BDP,PVCorr_BDP,PVCorr_BDP]
        print self.validateinput(True),"\n"                  # FAIL
        self.bdp_in = [PVCorr_BDP,Moment_BDP,PVCorr_BDP,PVCorr_BDP,PVCorr_BDP,PVCorr_BDP]
        print self.validateinput(True),"\n"                  # FAIL
    
    def test2(self):  # required
        self.valid_BDP = [(Image_BDP,1, bt.REQUIRED),
                          (Table_BDP,3, bt.REQUIRED),
                          (Line_BDP, 0, bt.REQUIRED)]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP,Image_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP,Table_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP,Table_BDP,Table_BDP,Table_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Line_BDP,Line_BDP,Line_BDP,Line_BDP,Line_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP,Table_BDP,Table_BDP,Table_BDP,Line_BDP,Line_BDP]
        print self.validateinput(True),"\n"                 # PASS
   
    def test3(self):  # if then
        self.valid_BDP = [(bt.IF_THEN, {Moment_BDP: Image_BDP,
                                       Table_BDP:CubeStats_BDP})]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP,Moment_BDP]
        print self.validateinput(True),"\n"                 # PASS
        self.bdp_in = [Image_BDP,Moment_BDP,CubeStats_BDP]
        print self.validateinput(True),"\n"                 # FAIL

        
    def test4(self):  # one of
        self.valid_BDP = [(bt.ONE_OF, [Line_BDP,Image_BDP,Table_BDP])]
        print self.validateinput(True),"\n"                 # FAIL
        self.bdp_in = [Image_BDP]
        print self.validateinput(True),"\n"                 # PASS
        self.bdp_in = [Image_BDP,Line_BDP]
        print self.validateinput(True),"\n"                 # FAIL


