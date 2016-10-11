import os, sys
import admit
"""
Utility methods for creating ADMIT recipes
==========================================
"""
def usage(progname,REQARGS,OPTARGS,KEYS,KEYDESC):
    """Print a standard usage statement given arguments and keywords.

       Parameters
       ----------
       progname : str 
         the calling program (recipe) name

       REQARGS : list
         the required non-keyword arguments

       OPTARGS : list
         the optional non-keyword arguments

       KEYS : dict
         the possible keywords 

       KEYDESC : dict
         string descriptions of KEYS

    """
    # Minimum required keyless arguments
    MINARGS = len(REQARGS)  

    # Number of optional keyless arguments  (max args = MINARGS+OPTARGS)
    # Note: rule is that if user provides one optional keyless argument,
    #       user must supply them all.  That's the only way to know
    #       which optional keyless argument is which.
    NUMOPTARGS = len(OPTARGS)  
    usagestr = progname + " "
    for a in REQARGS:
        usagestr = usagestr + a + " "
    if NUMOPTARGS >0:
        usagestr = usagestr + "[ "
        for a in OPTARGS:
            usagestr = usagestr + a + " "
        usagestr = usagestr + "] "
    if len(KEYS) > 0:
        usagestr = usagestr + "[ "
        for k in KEYS:
            usagestr = usagestr + k+"= "
        usagestr = usagestr + "] "
     
    print("Usage: %s " % usagestr)
    print("\t If you supply any optional keyless argument, you must supply them all\n")
    for k in KEYDESC:
        print("\t %s - %s" % (k,KEYDESC[k]))

    print("For detailed help, type '%s help'" % progname)
  
def _processargs(argv,REQARGS,OPTARGS,KEYS,KEYDESC,docstr):
    """Check command arguments and keywords, and possibly print a 
       usage statement.  See any ADMIT recipe for example usage.

       Parameters
       ----------
       argv : str 
         the calling program arguments list

       REQARGS : list
         the required non-keyword arguments

       OPTARGS : list
         the optional non-keyword arguments

       KEYS : dict
         the possible keywords 

       KEYDESC : dict
         string descriptions of KEYS

       docstr : str
         The calling program documentation string
    """
    if "help" in argv:
        print(docstr)
        return False

    # Minimum required keyless arguments
    MINARGS = len(REQARGS)  

    numargs = len(argv)-1 # Don't include argv[0]
    if numargs < MINARGS:
        usage(argv[0],REQARGS,OPTARGS,KEYS,KEYDESC)
        return False

    # Process argv backwards to get any key=val first.
    # This loop is only entered when recipe was called on 
    # the command line.
    for arg in argv[numargs:0:-1]:
        x = arg.split('=',1)
#        print "DOING x %s" % arg
        if len(x) == 2:
           KEYS[x[0]] = x[1]
           argv.pop()
        else:
           break


    # now we are left with the keyless arguments in argv
    # and keys in KEYS.  If this script is called on command
    # line, the key values are strings so recipe writer must 
    # do a conversion to expected native type.  If coming in
    # via admit_recipe, the values have whatever type the caller
    # used.

    return True
