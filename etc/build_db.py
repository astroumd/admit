import shutil
from slsearch import slsearch
import taskinit
import sqlite3 as sql
import admit.util.util as util
import os

# the molecules/atoms to search for
# dict keys are molecule name (must match what slsearch has for species exactly)
# dict value is a list of the following:
#   number of lines found (should start at 0)
#   boolean for hyperfine lines (True of the molecule has any hyperfine lines, or if it has degenerate lines)
#   minimum Smu^2 to allow for transitions
#   maximum upper state energy in K for transitions
data = {"COv=0":    [0,False,0.0,10000.0],
        "13COv=0":  [0,False,0.0,10000.0],
        "C17O":     [0,False,0.0,10000.0],
        "HCO+v=0":  [0,False,0.0,10000.0],
        "HDO":      [0,False,0.0,10000.0],
        "CCHv=0":   [0,True,0.0,10000.0],
        "CNv=0":    [0,True,0.01,10000.0],
        "HCNv=0":   [0,True,0.0,10000.0],
        "HNCv=0":   [0,False,0.0,10000.0],
        "13CN":     [0,True,0.15,10000.0],
        "H13CNv=0": [0,True,0.0,10000.0],
        "HN13C":    [0,False,0.0,10000.0],
        "N2H+v=0":  [0,True,0.0,10000.0],
        "C18O":     [0,False,0.0,10000.0],
        "H13CO+":   [0,False,0.0,10000.0],
        "DCO+v=0":  [0,False,0.0,10000.0],
        "H2CO":     [0,True,1.0,200.0],
        "DCNv=0":   [0,True,0.0,10000.0],
        "CSv=0":    [0,False,0.0,10000.0],
        "SiOv=0":   [0,False,0.0,10000.0],
        "SO3&Sigma;v=0":[0,False,1.0,10000.0],
        "HC3Nv=0":  [0,True,0.1,10000.0],
        "13CSv=0":  [0,False,0.0,10000.0],
        "C34Sv=0":  [0,False,0.0,10000.0],
        "H-atom":   [0,False,0.0,10000.0]}

trans_num = 5   # key for linking between main table and hyperfine table

def build_db(mol,hfs,smu,eu):
    """ Method to search through slsearch for all transitions from
    the given molecule.

    Parameters
    ----------
    mol : str
        The name of the molecule to search for (must match exactly the entries in slsearch)

    hfs : bool
        Whether or not there is nyperfine splitting in the molcule

    smu : float
        The minimum line strength to use when searching

    eu : float
        The maximum upper state energy to use when searching (in K)

    Returns
    -------
    Int containing the number of transitions found

    """
    global trans_num
    # do the search
    slsearch(outfile="temp.db",freqrange=[35.0,950.0],species=mol,reconly=True,rrlinclude=False,smu2=[smu,10000000.0],eu=[0.0,eu])
    # open the generated CASA table
    tb = taskinit.tb
    tb.open("temp.db")
    # open the main db
    con = sql.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)),"transitions.db"))
    cur = con.cursor()
    numrows = tb.nrows()
    rows = []
    cc = 0
    # if there is htperfine splitting
    if hfs:
        trows = {}
        hrows = {}
        count = 1
        # build up a list of the data
        for row in range(numrows):
            species = tb.getcell("SPECIES",row)
            name = tb.getcell("CHEMICAL_NAME",row)
            freq = float(tb.getcell("FREQUENCY",row))
            qn = tb.getcell("QUANTUM_NUMBERS",row)
            linestr = float(tb.getcell("SMU2",row))
            el = float(tb.getcell("EL",row))
            eu = float(tb.getcell("EU",row))
            trows[count] = [util.getplain(species),name,freq,qn,linestr,el,eu]
            hrows[count] = [freq,qn,linestr,el,eu]
            count += 1
        # loop over all of the list
        # print all of the results and query the user
        # User input is as follows:
        # Main_line:hf1,hf2,hf3
        # where Main_line is index of the strongest hyperfine component of a related group of hyperfine lines
        #  and hfX are the indices of the other hyperfine lines that are related to the main line
        #
        # alternate use:
        # D:Num1,Num2,QNS
        #
        # to merge degenerate lines into a single line, Num1 and Num2 are the indices to merge
        # and QNS is the new quantum numbers in a modified format (i.e. replace , with ; it will get
        # fixed on ingestion to the table)
        while True:
            hfs = []
            for r,v in trows.iteritems():
                print r,": ",v
            i = raw_input("HFS: ")
            #print i
            if i == "":
                break
            #print "SPLITTING"
            t = i.split(":")
            if "D" in t[0]:
                t1 = t[1].split(",")
                h = [t1[0],t1[1]]
                tra = t1[2]
                tra = tra.replace(";",",")
                l = trows[int(h[0])]
                l.append(0)
                l[3] = tra
                print l
                lrows =[tuple(l)]
                print lrows
                cur.executemany("insert into Transitions values(?,?,?,?,?,?,?,?)",lrows)
                con.commit()
                del hrows[int(h[1])]
                del hrows[int(h[0])]
                del trows[int(h[0])]
                del trows[int(h[1])]
            else:
                #print t
                lead = int(t[0])
                t1 = t[1].split(",")
                #print t1
                l = trows[lead]
                l.append(trans_num)
                rows.append(tuple(l))
                cc += 1
                del trows[lead]
                del hrows[lead]
                #print len(t1)
                for h in t1:
                    if h == '':
                        continue
                    #print h
                    cc += 1
                    hh = hrows[int(h)]
                    hh.insert(0,trans_num)
                    del hrows[int(h)]
                    del trows[int(h)]
                    hfs.append(tuple(hh))
                trans_num += 5
                #print rows[-1]
                #print hfs
                # add the hyperfine lines, using trans_num to link them to the main line
                if len(hfs) > 0:
                    cur.executemany("insert into HFS values (?,?,?,?,?,?)",hfs)
                    con.commit()            
        #rows.append((util.getplain(species),name,freq,qn,linestr,el,eu))
    # if there are no hyperfine lines then just ingest everything
    else:
        for row in range(numrows):
            species = tb.getcell("SPECIES",row)
            name = tb.getcell("CHEMICAL_NAME",row)
            freq = float(tb.getcell("FREQUENCY",row))
            qn = tb.getcell("QUANTUM_NUMBERS",row)
            linestr = float(tb.getcell("SMU2",row))
            el = float(tb.getcell("EL",row))
            eu = float(tb.getcell("EU",row))
            rows.append((util.getplain(species),name,freq,qn,linestr,el,eu,0))
        cc += numrows
    tb.close()
    # add the transitions
    cur.executemany("insert into Transitions values(?,?,?,?,?,?,?,?)",rows)
    con.commit()
    con.close()
    shutil.rmtree("temp.db")
    return cc
total = 0

# only uncomment this is recreating the database from scratch

"""
con = sql.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)),"transitions.db"))
cur = con.cursor()
cur.execute("create table HFS(TRANSITION INTEGER, FREQUENCY REAL, QUANTUM_NUMBERS TEXT, LINE_STR REAL, LOWER_ENERGY REAL, UPPER_ENERGY REAL)")
cur.execute("create table Transitions(SPECIES TEXT, NAME TEXT, FREQUENCY REAL, QUANTUM_NUMBERS TEXT, LINE_STR REAL, LOWER_ENERGY REAL, UPPER_ENERGY REAL, HFS INTEGER)")
con.commit()
con.close()
"""
for k,v in data.iteritems():
    print k
    print v
    try:
        data[k][0] += build_db(k,v[1],v[2],v[3])

    except:
        shutil.rmtree("temp.db")
        raise

    # report the number of transitions ingested
    print k,data[k]
    total += data[k][0]

print "\n",total
