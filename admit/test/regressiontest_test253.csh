#!/bin/csh -f
#

#set tests = (test0.fits)
set tests = (test253_spw3.fits)

if ($#argv > 0) then
  echo Running $* instead of $tests
  set tests = ($*)
endif  

# normally this is a symlink to where you have the fits files
set testdata = $ADMIT/testdata
if (! -e $testdata) then
  echo FAIL:  the $testdata directory does not exist
  exit 1
else
  @ bad = 0
  foreach test ($tests)
    if (! -e $testdata/$test) then
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

foreach test ($tests)
   if (! -e $test) ln -sf $testdata/$test
   if (-e $etc/$test.apar) cp $etc/$test.apar .
   runa1 $test
   if ($?) then
     echo FAIL runa1 $test
     @ bad++
     continue
   endif
   grep REGRESSION $test.log > $test.rout
   diff $test.rout $etc
   if ($?) then
      echo FAIL for $test
      @ bad++
      continue
   else
      echo OK for $test
   endif
end
  
echo "return with result ($bad)"
exit $bad

