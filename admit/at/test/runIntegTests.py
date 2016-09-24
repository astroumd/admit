#! /usr/bin/env casarun

# Run all existing integration tests in the current directory.
# By doing the imports inside a single casarun , we save the overhead of 
# starting up casa for each integration test.

import admit.util.utils


# Dynamically find any modules named integrationtest_*.py and
# import them. 

for filename in admit.util.utils.find_files('.','integrationtest_*.py'):
    mymodule = os.path.basename(filename).split('.')[0]
    print "### Running %s " % (mymodule)
    __import__( mymodule )


