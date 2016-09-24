#! /usr/bin/env python

from admit.bdp import *
import admit.xmlio.dtdGenerator as dtdGenerator
import admit.xmlio.Parser as Parser
import numpy as np

if __name__ == "__main__" :
    dtdGenerator.generate()
    
    print "Creating initial class"
    cs = CubeStats.CubeStats()
    
    print "Setting initial values"
    cs.set("project","cx369")
    cs.set("mous","test")
    cs.set("sous","test2")
    cs.set("date","13-09-10")
    cs.set("UID","123456789")
    cs.set("xmlFile","cs.225.xml")
    cs.stats.setData([[1,2,3,4],[5,6,7,8]])
    cs.stats.setColumns(["col1","col2","col3","col4"])
    
    print "Writing xml file"
    cs.write()
    
    print "Reading xml file into new class"
    p = Parser.Parser(None,"cs.225.xml")
    b = p.parse()
    
    print "\n\nComparing classes"

    print cs.project,b.project
    if(cs.project == b.project) :
        print "   project OK"
    print cs.mous,b.mous
    if(cs.mous == b.mous) :
        print "   mous OK"
    print cs.sous,b.sous
    if(cs.sous == b.sous) :
        print "   sous OK"
    print cs.date,b.date
    if(cs.date == b.date) :
        print "   date OK"
    print cs.UID,b.UID
    if(cs.UID == b.UID) :
        print "   UID OK"
    print cs.xmlFile,b.xmlFile
    if(cs.xmlFile == b.xmlFile) :
        print "   xmlFile OK"
    print cs.stats.columns,b.stats.columns
    if(cs.stats.columns == b.stats.columns) :
        print "   Columns OK"
    print cs.stats.data,b.stats.data
    if((cs.stats.data == b.stats.data).all()) :
        print "   Data OK"
