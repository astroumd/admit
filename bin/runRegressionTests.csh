#!/bin/csh -f
# Script to run all existing regression tests. Unit tests file names MUST begin
# with regressiontest_

onintr cleanup

set out=/tmp/admitregressiontest.log$$
set EXPECTEDOK = 2

echo "Running ADMIT regression tests."
echo "Detailed output will be written to $out"
echo > $out

if ($?ADMIT == 0) then
  source admit_start.csh
endif

# regression tests need big data, they need to be in $ADMIT/testdata
# (or this needs to be a symlink)
# See also the --with-testdata flag to configure
# The work is done in $ADMIT/data

if (! -e $ADMIT/testdata) then
  echo 'No $ADMIT/testdata/'
  echo Symlink this to your testdata repo, it can be read-only
  exit 1
else
  echo OK, $ADMIT/testdata exists
endif

# ensure working directory exist
mkdir -p $ADMIT/data
cd $ADMIT/data
echo Working in $ADMIT/data

set runnables = ( `find $ADMIT -path \*test/regressiontest_\*.csh ` )
@ result = 0
foreach r ( $runnables  )
   $r >>& $out
   @ result += $?
   echo -n .
end
  
set numok=`grep -cs OK $out`
set numfail=`grep -cs FAIL $out`

echo 
echo "$numok out of $EXPECTEDOK tests PASSED."
echo "$numfail tests FAILED."
#echo "return with result ($result)"
exit $result

cleanup:
/bin/rm -rf $out
