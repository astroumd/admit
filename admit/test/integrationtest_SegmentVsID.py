#! /usr/bin/env casarun
import sys, os
import argparse as ap
import datetime as dt
import tempfile

import admit
import matplotlib
import unittest
#matplotlib.use('Agg')


class IntegTestSegVsID(unittest.TestCase):

    def setUp(self):
        self.root = admit.utils.admit_root()
        self.testoutput = self.root+"/INTEGTESTRESULT"
        self.success   = "FAILED"
        self.testName = "Test LineSegment_AT vs. LineID_AT identifylines=False"

        self.transitions = [[["13COv=0", [110.15, 110.25], 6.0, 30.0, 5.0]],  # 0 single 13CO line

                       [["CH3CNv=0",[110.21, 110.5], 8.5, 15.0, 0.0]],   # 2 Methyl cyanide cluster

                       [["N2H+v=0", [93.1, 93.2], 15.5, 0.25, 0.0]],     # 4 narrow, blended hyperfines

                       [["COv=0", [115.2, 115.3], 5.5, 20.0, -30.0],     # 6 galactic emission type spectrum
                        ["COv=0", [115.2, 115.3], 5.0, 20.0, 30.0]],

                       [["COv=0", [115.2, 115.3], 5.5, 20.0, -30.0],     # 8 P-cygni type profile
                        ["COv=0", [115.2, 115.3], -5.0, 20.0, 30.0]],

                       [["(CH3)2COv=0", [240.0,242.0], 10.0, 5.0, 0.0],  # 10 complex molecules
                        ["CH3OCHOv=0", [240.0,242.0], 15.0, 3.0, 1.0],
                        ["CH3CH2CNv=0", [240.0,242.0], 20.0, 5.0, 0.0],
                        ["CH3OCH3", [240.0,242.0], 5.0, 5.0, 0.0],
                        ["CH3OHvt=0", [240.0,242.0], 20.0, 5.0, 0.0],
                        ["CH3OHvt=1", [240.0,242.0], 5.0, 5.0, 0.0]],

                       [["COv=0", [115.2, 115.3], 3.0, 30.0, -40.0 ],    # 12 outflow type spectrum
                        ["COv=0", [115.2, 115.3], 3.0, 30.0, 40.0 ],
                        ["COv=0", [115.2, 115.3], 6.0, 8.0, 15.0 ],
                        ["COv=0", [115.2, 115.3], 5.5, 8.0, -15.0 ],
                        ["COv=0", [115.2, 115.3], -3.5, 8.0, 0.0 ]],

                       [["CH3CH2CNv=0", [93.65,93.7], 8.0, 2.0, 0.0],
                        ["CH3OCH3", [93.65, 93.7], 6.5, 2.0, 0.0]],       # 14 blended lines from different molecules

                       [["H&alpha;", [99.02, 99.025], 4.0, 55.0, -10.0],
                        ["CH3CHOvt=1", [99.02, 99.025], 4.0, 5.0, 0.0]],   # 16 wide and narrow blended lines

                       [["N2H+v=0", [93.1, 93.2], -15.5, 0.25, 0.0]],     # 18 pure absorption

                       [["NH2CHO", [102.2, 102.25], 5.5, 17.0, -40.0],
                        ["NH2CHO", [102.2, 102.25], 5.0, 17.0, 40.0],
                        ["CH3CCHv=0", [102.5,102.55], 30.0, 17.0, -39.0],
                        ["CH3CCHv=0", [102.5,102.55], 25.0, 17.0, 39.0],
                        ["H2CS", [103.0,103.1], 6.5, 17.0, -40.0],
                        ["H2CS", [103.0, 103.1], 5.7, 17.0, 40.0],
                        ["DNCO", [101.9,102.1], 3.5, 10.0, 39.5]],        # 20 glactic emission with multiple non-tier 1 molecules

                       [["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 0.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 4.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -4.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -8.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 8.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -12.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 12.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 16.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -16.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 20.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -20.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, 24.0],
                        ["CH3CCHv=0", [102.547, 102.55], 6.5, 6.0, -24.0]],   # 22 wide plateau like line

                       [["NH2CHO", [102.2, 102.25], 3.5, 8.0, 1.0],
                        ["CH3CCHv=0", [102.5,102.55], 2.2, 4.0, -1.5],
                        ["H2CS", [103.0, 103.1], 4.5, 5.2, 0.0],
                        ["DNCO", [101.9,102.1], 3.0, 3.5, 0.5]],         # 24 few weak lines

                       [["CH3OCH3", [90.935, 90.94], 12.0, 0.5, 0.1]]    # 26 pure triplet of lines
                        ]
        self.delta = [0.5, 0.5, 0.005, 0.5, 0.5, 0.5, 0.1, 0.1, 0.2, 0.005, 0.4, 0.2, 0.5, 0.025]  #MHz
        self.contin = [0.5, 1.3, 0.1, 3.0, 1.2, 0.5, 0.1, 1.2, 2.0, 1.0, 10.0, 3.0, 0.0, 1.5, 2.5]  #SNR
        self.seed = [10, 25, 15, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
        self.freq = [110.25, 110.3, 93.175, 115.271, 115.3, 241.0, 115.26, 93.68, 99.0, 93.175, 102.5, 102.52, 102.55, 90.94] #GHz
        self.nchan = [1000, 500, 2000, 1000, 1000, 4000, 1000, 1000, 1000, 2100, 4000, 800, 4000, 1000]


        today = dt.date.today()
        date = "%i-%02i-%02i" % (today.year, today.month, today.day)
        plotmode = admit.PlotControl.BATCH # NOPLOT, BATCH, INTERACTIVE, SHOW_AT_END
        plottype = admit.PlotControl.PNG   # PNG, JPG, etc.
        loglevel = 50               # 10=DEBUG, 15=TIMING 20=INFO 30=WARNING 40=ERROR 50=FATAL
        self.outdir = tempfile.mkdtemp()
        self.admitdir = "%s/%s" % (self.outdir, date)
        print "##################  %s Project directory = %s  ################" % (self.__class__.__name__,self.admitdir)

        admit.util.utils.rmdir(self.outdir)

        self.a = admit.Project(self.admitdir,name='LineSegment vs. LineID', create=True, loglevel=loglevel)

        # Default ADMIT plotting environment
        self.a.plotparams(plotmode,plottype)

    def tearDown(self):
        f = open(self.testoutput,"a")
        f.write(self.success + " " + self.__class__.__name__  + "\n")
        f.close()
        self.cleanup()

    def cleanup(self):
        try:
            cmd = "/bin/rm -rf %s" % self.outdir
            os.system( cmd )
            os.system("/bin/rm -rf ipython*.log casapy*.log immoments.last exportfits.last admit.xml")
        except:
            pass

    def runTest(self):
        print "####  %s ####"% self.testName
        try:
            for i in range(len(self.transitions)):
                spec = self.a.addtask(admit.GenerateSpectrum_AT(seed=self.seed[i], nchan=self.nchan[i], contin=self.contin[i], delta=self.delta[i], freq=self.freq[i], transitions=self.transitions[i], alias="test_%i" % (i)))
                bdp_in   = [(spec,0)]
                csub     = [1,1]
                segment  ="ADMIT"
                numsigma = 2.0
                minchan  = 5
                maxgap   = 3
                vlsr     = 0.0  

                linesegment1 = self.a.addtask(admit.LineSegment_AT(segment=segment, csub=csub), bdp_in)
                self.a[linesegment1].setkey('numsigma',numsigma)
                self.a[linesegment1].setkey('minchan',minchan)
                self.a[linesegment1].setkey('maxgap',maxgap)

                lineid1 = self.a.addtask(admit.LineID_AT(vlsr=vlsr,segment=segment,csub=csub), bdp_in)
                self.a[lineid1].setkey('numsigma',numsigma)
                self.a[lineid1].setkey('minchan',minchan)
                self.a[lineid1].setkey('maxgap',maxgap)
                self.a[lineid1].setkey('identifylines',False)    

                print "################## RUNNING TRANSITION %d: %s ######################### " % (i, self.transitions[i][0][0])

                self.a.run()
               
                segtable = self.a.fm[linesegment1]._bdp_out[0].table
                linetable = self.a.fm[lineid1]._bdp_out[0].table
                number_of_segments = len(segtable)
                number_of_lines    = len(linetable)
                self.assertEqual(number_of_segments,number_of_lines,msg="Number of Line Segments doesn't match number of LineIDs")

                for rowindex in range(min(number_of_segments,number_of_lines)):
                    rowS = segtable.getRowAsDict(rowindex)
                    rowL = linetable.getRowAsDict(rowindex)
                    self.assertEqual(rowS,rowL,"Values for row %d of segment table and line table do not match" % rowindex)
            self.success = "OK"
        except Exception, e:
            m = "exception=%s, file=%s, lineno=%s" % ( sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno)
            self.success = "FAILED"
            traceback.print_exc()
            self.fail("%s failed with: %s" % (self.__class__.__name__ , m))


###############################################################################
# END CLASS                                                                   #
###############################################################################

suite = unittest.TestLoader().loadTestsFromTestCase(IntegTestSegVsID)
unittest.TextTestRunner(verbosity=1).run(suite)

