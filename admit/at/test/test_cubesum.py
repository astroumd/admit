""" Right now you need to run this test inside of casapy

This test does the following:
    creates an admit class
    creates a cubesum AT
    sets some parameters
    adds the cubesum AT to the admit class
    runs admit (which in turn runs the needed AT's)
    writes the results out to disk
    reads them into a new admit instance
    prints out one of the BDP xml file names
    
    to run this test do the following:
        import admit.at.test.test_cubesum as tm
        tm.run(<filename>)    <filename> is the name of the image file to be processed (note for the time being you need to be in the directory containing the image file
"""
import admit.Admit as ad
import admit.at.CubeSum_AT as mcs

def run(fileName):
    # instantiate the class
    a = ad.Admit()
    # instantiate a moment AT
    c = mcs.CubeSum_AT()
    # set some moment parameters
    c.setParameter("imagename",fileName)
    c.setParameter("outfile","tester_sum")
    c.setParameter("moments",[0])

    # add the moment AT to the admit class
    a.addTask(c)
    # run admit (specifically the tasks that need it
    c.run()
    # save it out to disk (this will not be needed soon as I a working on
    # a way to write out the xml inside of the run commmand
    a.write()

    a2 = ad.Admit()   # read in the admit.xml and bdp.xml files

    # this should print out something reasonable ending in .xml
    for i in a.tasks[0].products :
        if(i.xmlFile == a2.tasks[0].products[0].xmlFile):
            print "\n\nPASS\n"
            return
    
    print "\n\nFAIL\n"
