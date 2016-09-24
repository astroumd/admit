

# bootstrap method to get PIP installed
URL1 =   https://bootstrap.pypa.io/get-pip.py


CHECK = check_admit.py check_aplpy.py \
	check_numpy.py \
	check_astropy.py check_astroquery.py \
	check_radio_astro_tools.py


all:  check


check:
	@which python
	@which pip
	-@for i in $(CHECK); do \
	./$$i; done

check1:
	@which python
	@which pip
	-@for i in $(CHECK); do \
	casarun $$i; done


get1:
	wget $(URL1)

#       CASA recommended way
#       See --help for many more useful options
pip:
	casa-config --exec python get-pip.py
	@echo "==="
	@echo  If you are lucky, you can process with "make test-pip"

#       old way
pip1:
	@echo 'From within casa type: (e.g. casa --nogui --nologfile)'
	@echo "!python get-pip.py"


# for the lucky one where this works (e.g. Ubuntu)
# on the mac, you will need to copy  pip from the Python.framework tree into $CASA_ROOT/MacOS first

test-pip: pip
	pip install --upgrade setuptools
	pip install sphinx
	pip install numpydoc

