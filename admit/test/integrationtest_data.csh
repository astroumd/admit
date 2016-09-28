#! /bin/csh -f 
#
# at UMD:   /n/chara/admit/testdata

echo integrationtest_data.csh:


# Location of the test data. Can be a symlink to a read-only location
# but more typically in $ADMIT/testdata
set testdata = $ADMIT/testdata

#  list of files to be tested in $testdata
#  These should be pairs of spectral line data and matching continuum data
set specdata = ( test253_spw3.fits )
set contdata = ( test253_cont.fits )
set recipe   = Archive_Pipeline


# -- no need to change anything below --

if ($#argv > 0) then
  set data = ($*)
endif

if (! -e $testdata) then
  echo 'No $ADMIT/testdata/'
  echo Symlink this to your testdata repo, it can be read-only.
  echo Or do "'make testdata'" to download it
  echo "FAILED $0" >> $ADMIT/INTEGTESTRESULT
  exit 1
endif

if ( $#specdata != $#contdata ) then
  echo "Error: Number of spectral cubes ($#specdata) must match number of continuum images ($#contdata)"
  echo "FAILED $0" >> $ADMIT/INTEGTESTRESULT
  exit 1
endif



if (! -e $ADMIT/data) mkdir $ADMIT/data
cd $ADMIT/data


set nfail = 0

@ i = 1
foreach ff ($specdata)
  echo Testing $recipe on $specdata[$i] , $contdata[$i]
  set fc=$contdata[$i]
  if (! -e $ff) then
    if (-e $testdata/$ff) then
       ln -s $testdata/$ff
    else
       echo $ff not in $testdata.
       @ nfail++
       continue
    endif
  endif
  if (! -e $fc) then
    if (-e $testdata/$fc) then
       ln -s $testdata/$fc
    else
       echo $fc not in $testdata.
       @ nfail++
       continue
    endif
  endif

  set adir = ${ff:r}.admit
  /bin/rm -rf $adir

  # Run standard admit recipe on the data
  admit_recipe $recipe $ff $fc 
  @ nfail += $status

  # Now make sure the generated admit0.py executes successfully.
  # It should do execute no tasks since the flow is up to date.
  $adir/admit0.py
  @ nfail += $status

end

# needed for grepping in bin/runIntegrationTests.csh
if ($nfail > 0 ) then 
  echo "FAILED $0" >> $ADMIT/INTEGTESTRESULT
else
  echo "OK $0"  >> $ADMIT/INTEGTESTRESULT
endif

exit $nfail
