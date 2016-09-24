#!/bin/csh -f

echo admit=$ADMIT
#####################################################################
# The purpose of this test is to simulate a developer creating
# new AT and BDP and going through the steps required to 
# add it to source tree and test it.  This first section
# copies hello_world AT and BDP into source tree and creates the DTDs.
#####################################################################
cp $ADMIT/doc/examples/HelloWorld_AT.py $ADMIT/admit/at/HelloWorld_AT.py
cp $ADMIT/doc/examples/HelloWorld_BDP.py $ADMIT/admit/bdp/HelloWorld_BDP.py
\rm $ADMIT/admit/bdp/__init__.pyc
\rm $ADMIT/admit/at/__init__.pyc
$ADMIT/bin/dtdGenerator

#####################################################################
# now run the actual integration test
#####################################################################

$ADMIT/admit/at/test/runtest_helloworld.py

########################################################################
# now restore the source tree to the way it was before the test was run.
# Be sure to remove the pyc in addition to the py.
########################################################################

\rm $ADMIT/admit/bdp/HelloWorld_BDP.*
\rm $ADMIT/admit/at/HelloWorld_AT.*
\rm $ADMIT/admit/bdp/__init__.pyc
\rm $ADMIT/admit/at/__init__.pyc
grep -v Hello $ADMIT/admit/at/__init__.py > /tmp/atinit$$
mv /tmp/atinit$$ $ADMIT/admit/at/__init__.py
grep -v Hello $ADMIT/admit/bdp/__init__.py > /tmp/bdpinit$$
mv /tmp/bdpinit$$ $ADMIT/admit/bdp/__init__.py
$ADMIT/bin/dtdGenerator
