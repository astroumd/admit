#!/usr/bin/env python
# run admit recipes in $ADMIT/admit/scripts directory. 

#import admit.scripts as recipes ## Really???
"""
   **recipe** --- Executes a pre-defined ADMIT recipe (script).
   ------------------------------------------------------------

   This module implements a uniform interface for executing pre-defined ADMIT
   recipes.
"""

import os
import fnmatch
import importlib
import admit.util

def recipe(*args,**kwargs):
    """Function to run an ADMIT recipe. The parameters are passed without
       any keywords. The first parameter must be the name of the recipe
       and subsequent parameters the arguments of that recipe in order.
    
       Parameters
       ----------
       recipe_name: str
          The name of the recipe
       args 
          The rest of the keyword-less arguments
       kwargs
          Any keywords this recipe understand
 
       Notes
       ----------
       Example: admit.recipe("LineMoment","test0.fits")
                admit.recipe("LineMoment","test0.fits",minchan=10)
    """
    scriptsdir = admit.util.utils.admit_root() + os.sep + "admit" + os.sep + "scripts"
    mod = "admit.scripts."
    print args
    print kwargs
    try:
          therecipe = importlib.import_module(mod+args[0])
          print therecipe
    except:
       print "Recipe %s not found. Available recipes are:" % args[0]
       flist = []
       pattern = '*.py'
       for filename in os.listdir(scriptsdir):
           if fnmatch.fnmatch(filename, pattern) and filename != 'recipe.py' and filename !='__init__.py':
               flist.append(os.path.splitext(filename)[0])
       for name in flist:
          print "     %s" % name
       return

    if hasattr(therecipe,'KEYS'):
       therecipe.KEYS.update(kwargs)
    therecipe._run(args)

if __name__ == "__main__":
   recipe("Line_Moment","test0.fits")
   recipe("XXX","junk","hey",1,"forest")
