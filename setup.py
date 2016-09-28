#
#    setup.py file for putting ADMIT into CASA's python module tree
#
import os
from setuptools import setup
# pjt
from setuptools.command.install import install
from setuptools.command.install_scripts import install_scripts
from distutils import log # needed for outputting information messages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def aversion():
    import admit.version
    return admit.version.__version__

#  using this causes 'setup.py install' loose the egg versioning
class OverrideInstall(install):
    def run(self):
        log.info("Running ADMIT OverrideInstall")
        mode = 0755
        install.run(self)    # insure that we run what normally gets installed
                             # then overriding with our private magic ..
        # add the execution bit... .since we are abusing the system and placing
        # '/usr/bin/env casarun' scripts in some of the packages directories!
        for filepath in self.get_outputs():
            if filepath[-3:] == '.py':
                log.info("Changing permissions of %s to %s" %  (filepath, oct(mode)))
                os.chmod(filepath, mode)

# the required stuff (the version= also should be in the Makefile, for proper labeling)
# as for packages, 'admit/at/test' etc. is not included, so you cannot run tests
# also 'xmlio/dtd/admit.dtd' is not found, this required another attention
setup(
    name = "admit",
    version = aversion(),
    author = "Peter Teuben",
    author_email = "teuben@gmail.com",
    description = ("A test setup.py for ADMIT."),
    license = "BSD",
    keywords = "example documentation tutorial",
    url = "http://admit.astro.umd.edu/wiki/index.php/ADMIT",
    scripts=['bin/admit','bin/casarun','bin/admit_root','bin/admit_root.py',
             'bin/runa1','bin/runa2','bin/runa4','bin/admit_recipe','bin/admit_export','bin/admit_pipeline'],
    # packages=['admit', 'admit/at', 'admit/bdp','admit/gui', 'admit/util','admit/xmlio','etc'],
    packages=['etc', 'admit', 'admit/at', 'admit/bdp', 'admit/xmlio',
              'admit/recipes',
              'admit/test',
              'admit/util',
              'admit/util/continuumsubtraction',
              'admit/util/continuumsubtraction/spectral',
              'admit/util/continuumsubtraction/spectral/algorithms',
              'admit/util/filter',
              'admit/util/peakfinder',
              'admit/util/segmentfinder'],

    include_package_data = True,
    package_data = {'admit': ['xmlio/dtd/*.dtd', 'util/*.json'],
                    'etc': ['*.*', 'data/*',
                            'resources/css/*.*',
                            'resources/fancybox/source/*.*',
                            'resources/fancybox/source/helpers/*.*',
                            'resources/img/*.*',
                            'resources/js/*.js']},

    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Beta",
        "Topic :: Astronomy :: Scientific/Engineering :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    cmdclass={'install': OverrideInstall},       # BUG/FEATURE:  adding this will remove egg versioning
)
