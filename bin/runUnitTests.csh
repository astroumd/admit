#!/bin/csh -f
#
# Script to run all existing unit tests. Unit tests file names MUST begin
# with unittest_

onintr cleanup

if ($?ADMIT == 0) then
  source admit_start.csh
endif

if ( ! -e $ADMIT/tmp ) then
    mkdir $ADMIT/tmp
endif

set out=$ADMIT/tmp/admitunittest.log$$
set EXPECTEDOK = 21

echo "Running ADMIT unit tests."
echo "Detailed output will be written to $out"
echo > $out


cd $ADMIT
set runnables = ( `find admit -path \*test/unittest_\*.py ` )

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
