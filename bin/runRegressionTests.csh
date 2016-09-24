#!/bin/csh -f
#
#
#
# Script to run all existing regression tests.
# Regression tests file names MUST begin with regressiontest_

if ($?ADMIT == 0) then
  source admit_start.csh
  echo python is "("`which python`")"
  echo "PYTHONPATH is ($PYTHONPATH)"
endif  

set tests1 = (test0.fits)
set tests2 = ()
set tests4 = (test0551.tab)


# normally this is a symlink to where you have the fits files
set testdata = $ADMIT/testdata
if (! -e $testdata) then
  echo FAIL:  the $testdata directory does not exist
  exit 1
else
  @ bad = 0
  foreach test ($tests1 $tests2)
    if (! -e $test) then
      echo FAIL: $test does not exist in $testdata
      @ bad++
    endif
  end
  if ($bad) exit 1
endif

# *.apar *.rout and small *.tab files are here
# fits files are in $ADMIT/testdata
set etc = $ADMIT/etc/data

@ bad = 0

foreach test ($tests1)
   if (! -e $test) ln -sf $testdata/$test
   if (-e $etc/$test.apar) cp $etc/$test.apar .
   runa1 $test
   grep REGRESSION $test.log > $test.rout
   diff $test.rout $etc
   if ($?) then
      echo FAIL for $test
      @ bad++
   else
      echo OK for $test
   endif
end

foreach test ($tests2)
   if (! -e $test) ln -sf $testdata/$test
   if (-e $etc/$test.apar) cp $etc/$test.apar .
   runa2 $test
   grep REGRESSION $test.log > $test.rout
   diff $test.rout $etc
   if ($?) then
      echo FAIL for $test
      @ bad++
   else
      echo OK for $test
   endif
end

foreach test ($tests4)
   if (! -e $test)         cp $etc/$test      .
   if (-e $etc/$test.apar) cp $etc/$test.apar .
   runa4 $test
   grep REGRESSION $test.log > $test.rout
   diff $test.rout $etc
   if ($?) then
      echo FAIL for $test
      @ bad++
   else
      echo OK for $test
   endif
end



  
echo "return with result ($bad)"
exit $bad

