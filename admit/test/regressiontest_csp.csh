#!/bin/csh -f
#

set tests = (test0551.tab)

if ($#argv > 0) then
  echo Running $* instead of $tests
  set tests = ($*)
endif

# *.apar *.rout and small *.tab files are here
# fits files are in $ADMIT/testdata
set etc = $ADMIT/etc/data

# normally this is a symlink to where you have the fits files
set testdata = $ADMIT/testdata
if (! -e $testdata) then
  echo FAIL:  the $testdata directory does not exist
  exit 1
else
  @ bad = 0
  foreach test ($tests)
    if (! -e $etc/$test) then
      echo FAIL: $test does not exist in $etc
      @ bad++
    endif
  end
  if ($bad) exit 1
endif

@ bad = 0

foreach test ($tests)
   cp $etc/$test .
   if (-e $etc/$test.apar) cp $etc/$test.apar .
   runa4 $test
   if ($?) then
     echo FAIL runa4 $test
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

