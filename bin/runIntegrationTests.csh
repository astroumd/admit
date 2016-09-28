#!/bin/csh -f
# Script to run all existing integration tests. Unit tests file names MUST begin
# with integrationtest_

onintr cleanup 

if ($?ADMIT == 0) then
  source admit_start.csh
endif  

setenv MPLBACKEND "module://Agg"

# All integration tests write a single line to this $ADMIT/INTEGTESTRESULT.
# (Hardcoded in the test scripts).
set resultsfile = "$ADMIT/INTEGTESTRESULT"
/bin/rm -rf $resultsfile

if ( ! -e $ADMIT/tmp ) then
    mkdir $ADMIT/tmp
endif

set out=$ADMIT/tmp/admitintegtest.log$$
set EXPECTEDOK = 9

echo "Running ADMIT integration tests."
echo "Detailed output will be written to $out"
echo > $out

cd $ADMIT
set runnables = ( ` find admit -path \*test/integrationtest_\*.\*  | grep -v \~` )

@ result = 0
@ numok = 0
foreach r ( $runnables  )
   $r >>& $out
   echo -n .
end
  
echo 
if ( -e $resultsfile ) then 
       @ result = `grep -cs FAILED $resultsfile`
       @ numok = `grep -cs OK $resultsfile`
       cat $resultsfile
       /bin/rm -rf $resultsfile
       echo 
endif
#echo "return with result ($result)"
echo "$numok out of $EXPECTEDOK tests PASSED."
echo "$result tests FAILED."
exit $result

cleanup:
/bin/rm -rf $out $resultsfile
