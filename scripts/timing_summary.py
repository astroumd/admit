#! /usr/bin/env python
#
# process log files with standard TIMING lines in them, somewhat hardcoded column numbers
# Example of use:
#     $ADMIT/scripts/timing_summary.py *.fits.log | $ADMIT/scripts/tabalign.py > timing_summary.txt
#     enscript -r1 -fCourier7 timing_summary.txt -o junk.ps

import os, sys

def readtable(file=sys.stdin):
    """ gobble the file
    """
    if file is not sys.stdin:
        fp = open(file,'r')
    else:
        fp = sys.stdin
    lines = fp.readlines()
    if file is not sys.stdin:
        fp.close()
    return lines


atorder = ['Ingest','CubeStats','CubeSum','CubeSpectrum','PVSlice','PVCorr','LineID','LineCube','Moment']
atlabel = ['IN.'   , 'CST.'    ,'CSM.'   ,'CSP.'        ,'PVS.'   ,'PVC.'  ,'LID.'  ,'LC.'     ,'MOM.']

# a typical line looks like
# ----------------------------------------------------------------------
# TIMING : Dtime: LineCube ADMIT [  1.66100000e+01   1.44538080e+09]
# TIMING : Dtime: LineCube BEGIN [ 0.  0.]
# TIMING : Dtime: LineCube start  [ 0.12        0.12479401]
# ...
# TIMING : Dtime: LineCube END [ 0.23        0.61518717]
# ----------------------------------------------------------------------
# BASICS: [shape] npts min max [128 128  50   1] 802816.0 -0.111259445548 1.53996837139
# --

def process(lines):
    cpulines = []
    cpusum1 = 0.0
    cpusum2 = 0.0
    cpu1 = {}
    cpu2 = {}
    shape = [0,0,0]
    for l in lines:
        w = l.split()
        if len(w) > 0:
            if w[0] == 'TIMING':
                if w[4] == 'END':
                    cpulines.append(l)
                    ctime1 = float(w[6])
                    ctime2 = float(w[7][:-1])
                    cpusum1 = cpusum1 + ctime1
                    cpusum2 = cpusum2 + ctime2
                    at    = w[3]
                    if cpu1.has_key(at):
                        cpu1[at] = cpu1[at] + ctime1
                        cpu2[at] = cpu2[at] + ctime2
                    else:
                        cpu1[at] = ctime1
                        cpu2[at] = ctime2
            if w[0] == 'BASICS:':
                # scrape out the [shape]
                nx = int(w[5][1:])
                ny = int(w[6])
                nz = int(w[7])
                shape = [nx,ny,nz]
    cpu1['SUM'] = cpusum1
    cpu2['SUM'] = cpusum2
    for at in atorder:
        if not cpu1.has_key(at):
            cpu1[at] = 0.0
            cpu2[at] = 0.0

    if False:                
        for l in cpulines:
            print l.strip()
        print cpu1
        print cpu2
        print cpusum1, cpusum2
    if False:
        for key in cpu1.keys():
            f = cpu1[key]/cpu2[key]
            print key,cpu1[key],cpu2[key],f
        print "Total: ",cpusum1,cpusum2,cpusum1/cpusum2
    return (cpu1,cpu2,shape)
#


def label(fname):
    loc = fname.find('.')
    if loc>0:
        flabel = fname[:loc]
    else:
        flabel = fname
    return flabel

def show1(fname,cpu1,cpu2,shape):
    flabel = label(fname)
    cpusum1 = cpusum2 = 0.0
    for key in cpu1.keys():
        cpusum1 = cpusum1 + cpu1[key]
        cpusum2 = cpusum2 + cpu2[key]
    print "#%s  cpu1  cpu2  cpu1/cpu2  cpu1/sum1 cpu2/sum2" % flabel,shape
    for key in atorder:
        if cpu1.has_key(key):
            c1 = cpu1[key]
            c2 = cpu2[key]
            if c2 > 0.0:
                f = c1/c2
            else:
                f = 0.0
            f1 = c1/cpusum1
            f2 = c2/cpusum2
        else:
            c1 = 0.0
            c2 = 0.0
            f = 0.0
            f1 = 0.0
            f2 = 0.0
        print "%s %.1f %.1f %.3f %.3f %.3f" % (key,c1,c2,f,f1,f2)
    print "Total: %.1f %.1f %.3f %.3f %.3f" % (cpusum1,cpusum2,cpusum1/cpusum2,1.0,1.0)

    

def show2(cpu1,cpu2):
    cpusum1 = cpusum2 = 0.0
    for key in cpu1.keys():
        cpusum1 = cpusum1 + cpu1[key]
        cpusum2 = cpusum2 + cpu2[key]
    print "AT  cpu1  cpu2  cpu1/cpu2  cpu1/sum1 cpu2/sum2"
    for key in cpu1.keys():
        f = cpu1[key]/cpu2[key]
        f1 = cpu1[key]/cpusum1
        f2 = cpu2[key]/cpusum2
        print key,cpu1[key],cpu2[key],f,f1,f2
    print "Total: ",cpusum1,cpusum2,cpusum1/cpusum2,1.0,1.0

def showfile1(fname,cpu,shape,normalize=False):
    msg = label(fname) + " " + str(shape)
    if normalize:
        for at in atorder:
            msg = msg + " %4.1f" % (cpu[at]/cpu['SUM']*100.0)
        msg = msg + " = 100.0" 
    else:
        for at in atorder:
            msg = msg + " %.3f" % cpu[at]
        msg = msg + " = %.1f" % cpu['SUM']
    print msg

def showfile2(fname,cpu1,cpu2,shape):
    msg = label(fname) + " " + str(shape)
    for at in atorder:
        if cpu2[at] > 0:
            f = cpu1[at]/cpu2[at]*100.0
        else:
            f = 0.0
        msg = msg + " %4.1f" % f
    msg = msg + " = 100.0" 
    print msg

def showheader(lis):
    msg = lis[0]
    for l in lis[1:]:
        msg = msg + " " + l
    print msg


if __name__ == '__main__':
    if len(sys.argv) == 1:
        lines = readtable()
    elif len(sys.argv) == 2:
        f = sys.argv[1]
        lines = readtable(f)
        (cpu1,cpu2,shape) = process(lines)
        show1(f,cpu1,cpu2,shape)
    else:
        cpu1 = []
        cpu2 = []
        fname = []
        shape = []
        for f in sys.argv[1:]:
            lines = readtable(f)
            (c1,c2,s) = process(lines)
            #show1(f,c1,c2)
            cpu1.append(c1)
            cpu2.append(c2)
            shape.append(s)
            fname.append(f)
        nf = len(cpu1)
        showheader(["file","nx","ny","nz"] + atlabel + ["=", "sum"])
        for i in range(nf):
            showfile1(fname[i],cpu1[i],shape[i])
        for i in range(nf):
            showfile1(fname[i],cpu1[i],shape[i],True)
        for i in range(nf):
            showfile1(fname[i],cpu2[i],shape[i])
        for i in range(nf):
            showfile1(fname[i],cpu2[i],shape[i],True)
        for i in range(nf):
            showfile2(fname[i],cpu1[i],cpu2[i],shape[i])
        showheader(["file","nx","ny","nz"] + atlabel + ["=", "sum"])






