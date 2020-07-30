#
# reminders how to compile and install ADMIT related things
# WARNING:  VERSION is defined twice:  admit/version.py and historically in VERSIONS
#       git ci admit/version.py VERSIONS

SITE = teuben@chara.astro.umd.edu:public_html/admit/dist
URL  = http://www.astro.umd.edu/~teuben/admit/dist
VERSION = `python admit/version.py`
PY = 2.7

#
GITROOT = https://github.com/astroumd/admit.git

# locally at UMD:  /local/ftp/pub/admit/testdata
FTP = ftp://ftp.astro.umd.edu/pub/admit/testdata

# sample testdata needed for a mininum integration and regression test
DATA = test0.fits test253_spw3.fits test253_cont.fits

# use wget1 or wgetc (caching)
WGET = wget1

help:
	@echo Reminders/Helpers to build/distribute ADMIT:
	@echo "SITE     = $(SITE)"
	@echo "CASAPATH = $(CASAPATH)"
	@echo "VERSION  = $(VERSION)"
	@echo "PY       = $(PY)"
	@echo "URL      = $(URL)/admit-$(VERSION)-py$(PY).egg"
	@echo "targets:"
	@echo "  build                               build the egg"
	@echo "  dist                                scp egg to SITE"
	@echo "  install_local                       install into your current python from local egg"
	@echo "  install_url                         install into your current python from URL egg"
	@echo "  casa (uses PP and CASAPATH)         install into your current CASA"
	@echo "  home (uses HP and HOME/python/)     install in a testing version"
	@echo " "
	@echo "First time:"
	@echo "  make config"
	@echo "  source admit_start.csh"
	@echo " "
	@echo "Maintenance targets:"
	@echo "  make version                        git checkin the files needed when version number changed"
	@echo "  make dtd                            run dtdGenerator when new AT's or BDP's were added"
	@echo "  make buildbot                       run what the buildbot does,but in your environment"
	@echo ""
	@echo "Data:"
	@echo "  DATA = $(DATA)"


.PHONY:  build dist doc

clean: cleanpyc
	@echo No real clean yet ...
	-rm -rf configure admit_start.csh admit_start.sh
	$(MAKE) -C doc clean

cleanpyc:
	find admit -name \*.pyc -print -exec rm '{}' \;

build:
	python setup.py bdist_egg

dist:
	scp dist/admit-$(VERSION)-py$(PY).egg $(SITE)

tar-old:
	autoconf
	(cd ..; tar zcf admit-git.tar.gz admit)

ADIR = admit_$(VERSION)
EDIR = /chara/bimawww/docs/
export:
	rm -rf $(ADIR)
	(git clone $(GITROOT) $(ADIR); cd $(ADIR); autoconf; make docs2rm; cd ..; tar zcf $(ADIR).tar.gz $(ADIR))
	@echo "FOR AN OFFICIAL EXPORT RUN:"
	@echo "RUN: cp $(ADIR).tar.gz $(EDIR)"
	@echo "RUN: (cd $(EDIR); ln -sf $(ADIR).tar.gz admit.tar.gz)"
	@echo "or"
	@echo "RUN: scp $(ADIR).tar.gz chara.astro.umd.edu:$(EDIR)"
	@echo "RUN: ssh chara.astro.umd.edu ln -sf $(EDIR)/$(ADIR).tar.gz $(EDIR)/admit.tar.gz"

# only for export !!
docs2rm:	docs
	cp -a doc/sphinx/_build docs
	rm -rf doc

tar:
	@echo Writing $(ADIR).tar.gz
	(tar zcf $(ADIR).tar.gz $(ADIR))
	@echo "FOR AN OFFICIAL EXPORT RUN:"
	@echo "RUN: cp $(ADIR).tar.gz $(EDIR)"
	@echo "RUN: (cd $(EDIR); ln -sf $(ADIR).tar.gz admit.tar.gz)"

install:
	@echo "Pick one of the following (you may need to prepend with 'sudo'):"
	@echo " install_local"
	@echo " install_url"

install_local:
	easy_install dist/admit-$(VERSION)-py$(PY).egg

install_url:
	easy_install $(URL)/admit-$(VERSION)-py$(PY).egg

# special install (both lib/ and python/ can be symlinks to the right version)
PP = $(CASAPATH)/lib/python/site-packages/ 

casa:
	@if [ -d $(PP) ]; then \
	  PYTHONPATH=$(PP) easy_install --prefix=$(CASAPATH) dist/admit-$(VERSION)-py$(PY).egg; \
	else \
	  echo PYTHONPATH PP=$(PP) does not seem to exist;\
	  echo CASAPATH=$(CASAPATH) also needs to be set;\
	  echo Cannot easy_install ADMIT this way.;\
	fi

ls1:
	ls $(PP)
	@echo "PP=$(PP)"

MYPYTHON = $(HOME)/python

HP = $(MYPYTHON)/lib/python$(PY)/site-packages

home:
	@if [ -d $(HP) ]; then \
	  PYTHONPATH=$(HP) easy_install --prefix=$(MYPYTHON) dist/admit-$(VERSION)-py$(PY).egg; \
	else \
	  @echo PYTHONPATH PP=$(PP) does not seem to exist. Cannot easy_install ADMIT.;\
	fi

ls2:
	ls $(HP)
	@echo "HP=$(HP)"


config:
	autoconf
	./configure

admit_start.csh: admit_start.csh.in
	./configure

admit_start.sh: admit_start.sh.in
	./configure


#  quick access to datasets

data:
	mkdir -p data

# testdata itself is normally symbolic link to where you keep test0.fits etc.
# this way you can force getting some data
testdata: data
	@mkdir -p testdata
	-@for f in $(DATA); do\
	(cd testdata; ../bin/$(WGET) $(FTP)/$$f); done

# a much quicker one minute verson of testdata + bench on test0.fits
RLOG = "REGRESSION : MOM0FLUX: x.CO_115.27120 27240.3 25534.1 35.0141 2790.42 2790.42 58.6513"
bench:
	@mkdir -p testdata
	(cd testdata; ../bin/$(WGET) $(FTP)/test0.fits; ../bin/runa1 test0.fits)
	grep MOM0FLUX testdata/test0.fits.log
	@echo $(RLOG)
	@echo These last two lines should be identical

# reflow, should work but not do any work
benchr:
	(cd testdata; cp test0.admit/admit0.py . ; /usr/bin/time ./admit0.py)

# 

# deprecate
bench1:	data data/bench1

# deprecate
data/bench1:
	(cd data; wget -O - $(FTP)/bench1.tar.gz | tar zxf -)

# deprecate
test1: bench1
	python tests/test1.py

# deprecate
n253: 
	(cd data; $(WGET) $(N253))

#  default python, without CASA
python0:
	python bin/python-env
#  this will only run if you've properly installed CASA; it will hang on mac now
python1:
	casarun bin/python-env
#  same as python1, but this will also work on mac
python2:
	casa-config --exec bin/python-env

# deprecate 
bench2:	data data/bench2

# deprecate
data/bench2:
	(cd data; wget -O - $(FTP)/bench2.tar.gz | tar zxf -)

# deprecate
test2: bench2
	python tests/test2.py

# test0.fits is the same as foobar.fits
# deprecate
test0: data
	(cd data; wget $(FTP)/test0.fits)

# deprecate
foobar:	data 
	(cd data; wget $(FTP)/foobar.fits; sed s/NGC3256/ngc3256/ foobar.fits > foobar2.fits)

# do a new version check in
# These files have version info
version:
	git admit/version.py VERSIONS

# when new AT's or BDP's were added; there is also a module to do
# this from within python, but this is a quick command line version
# if you have bad code in your AT or BDP directory, it can also fail
dtd:
	bin/dtdGenerator
	git status

# here's a cheat/reminder. You currently need pip and sphinx to build documentation
# if this fails, look at the INSTALL.dev file for possible options
pip:
	make -C integration-test pip test-pip

# some commands can go here that will eventually go in "unit"
# to check if all tests can be re-run, "make unit0" twice in a row

# Note added Sep 2016:  unit0 now fails, due to a casa dependency that slipped into Admit.py ?
#                       @todo this casa dependency should be fixed in 1.2+ or 2.0+

unit0_clean:
	(cd admit/test ; rm -rf test1 test2 test3 test4 test5 test6 test7)
unit0: 
	@echo Rogue unit tests, use unit0_clean to start from a clean slate
	(cd admit/test ; ./test_Admit1.py      test1)
	(cd admit/test ; ./test_Flow.py        test2)
	(cd admit/test ; ./test_Flow_many.py   test3)
	(cd admit/test ; ./test_Flow_again.py  test4)
	(cd admit/test ; ./test_Flow1N.py      test5)
	(cd admit/test ; ./test_FlowN1.py      test6)
	(cd admit/test ; ./test_FlowMN.py      test7)

unit00:
	-(cd data; ../admit/at/test/test_file.py foobar.fits)
	-(cd data; ../admit/at/test/test_ingest.py foobar.fits)

# supposed to roughly do what buildbot does 
buildbot: unit integration docs


##########################################################################
# DO NOT CHANGE THE FOLLOWING TARGET NAMES THAT THE BUILDBOT DEPENDS ON. #
##########################################################################

# Run any existing unit tests
unit:
	bin/runUnitTests.csh

integration:
	bin/runIntegrationTests.csh  

regression:
	bin/runRegressionTests.csh 


linetest:
	bin/runLineIDTest.csh

# Two types of documentation:  the PDF manuals in doc, and the HTML generated via sphinx)
# 

# unpack CSS and javascript resources needed for the data browser
resources:
	@echo No longer needed.
#	mkdir -p resources
#	tar zxf etc/htmlresources.tgz
#	cp -p etc/live.js resources/js/live.js
#	cp -p etc/admit.css resources/css/admit.css

html:
	($(MAKE) -C doc/sphinx html) 2>&1 | \
	  grep -vF "WARNING: toctree references unknown document" | \
	  grep -vF "WARNING: toctree contains reference to nonexisting document"
	@echo The doctest html is here:
	echo " $(ADMIT)/doc/sphinx/_build/html/doctest.html"
	@echo Point your browser to the root of all documention:
	@echo " $(ADMIT)/doc/sphinx/_build/html/index.html"

#       if building modules fails due to casa[] in peter's sandbox (bad Moment_AT reference?)
#       nbody else seems to have this?
hack1:
	rm admit/at/__init__.py admit/at/__init__.pyc ; touch admit/at/__init__.py

# Extra style files for Sphinx not readily found on RHEL 7 (in particular).
TEXINPUTS = ":$(ADMIT)/doc/sphinx/texinputs"

pdf:
	TEXINPUTS=$(TEXINPUTS) $(MAKE) -C doc ADMIT.pdf

doc:
	TEXINPUTS=$(TEXINPUTS) $(MAKE) -C doc all

# This has to be called docs NOT doc.  Don't change it!
docs: doc html 
#pdf

all: config docs
