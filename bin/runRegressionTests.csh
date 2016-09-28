#!/bin/csh -f
#
# Script to run all existing regression tests. Tests file names MUST begin
# with regressiontest_

onintr cleanup

if ($?ADMIT == 0) then
  source admit_start.csh
endif

if ( ! -e $ADMIT/tmp ) then
    mkdir $ADMIT/tmp
endif

set out=$ADMIT/tmp/admitregressiontest.log$$
set EXPECTEDOK = 2

echo "Running ADMIT regression tests."
echo "Detailed output will be written to $out"
echo > $out


# regression tests need big data, they need to be in $ADMIT/testdata
# (or this needs to be a symlink)
# See also the --with-testdata flag to configure
# The work is done in $ADMIT/data

if (! -e $ADMIT/testdata) then
  echo "There is no $ADMIT/testdata directory"
  echo "Symlink this to your testdata repo, or grab what you need from"
  echo "      ftp://ftp.astro.umd.edu/pub/admit/testdata"
  echo "or use the "
  echo "      make testdata"
  echo "make target to grab the important ones for the tests"
  exit 1
else
  echo OK, $ADMIT/testdata exists
endif

set runnables = ( `find $ADMIT/admit -path \*test/regressiontest_\*.csh ` )
cd $ADMIT/data

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
