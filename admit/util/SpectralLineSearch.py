""" .. _SpectralLineSearch:

    **SpectralLineSearch** --- Interface to spectral line searching.
    ----------------------------------------------------------------

    This module defines the SpectralLineSearch class.
"""
# system imports
import urllib2
import random

# admit imports
from admit.util import Splatalogue
from admit.util import logging
from admit.util import utils
from admit.util import LineData

class SpectralLineSearch(object):
    """ Class to act an as interface to the spectral line searching tools.
        It can search both the slsearch catalog and, if online, the
        splatalogue database.

        Parameters
        ----------
        online : bool
            Whether to use the online splatalogue database. If no internet
            connection is detected, then it will fall back on slsearch.
            Default: True.

        tier1freq : list
            A list of tier1 frequency coverage, to eliminate any matches
            that fall in the range of a tier1 line.

        Attributes
        ----------
        sls_kw : dict
            Dictionary to hold the keyword/value pairs for slsearch.

        sp_kw : dict
            Dictionary to hold the keyword/value paris for splatalogue.

    """
    def __init__(self, online=True, tier1freq=[]):
        self.online = online and self.check_online
        self.tier1freq = tier1freq
        self.sls_kw = {}
        self.sp_kw = {"exclude" : [],
                      "line_lists" : [],
                      "line_strengths" : [],
                      "energy_levels" : [],
                      "top20" : []}

    def setkeywords(self, minfreq, maxfreq, rrlevelstr, **kwargs):
        """ Method to set the keywords for the search(es)

            Parameters
            ----------
            minfreq : float
                The starting frequency of the search, in GHz.

            maxfreq : float
                The ending frequency of the search, in GHz.

            rrlevelstr : str
                A string representation of what recombination lines
                to allow in the results

            kwargs : dict
                Dictionary of keyword/value pairs for search options.
                Possibilities are (no default values for most):

                **tablename** : str
                    Output table name for slsearch.

                **outfile** : str
                    Output file name for slsearch.

                **rrlonly** : bool
                    Only return recombination lines.
                    (slsearch)

                **verbose** : bool
                    Be verbose in slsearch.

                **logfile** : str
                    Send slsearch results to the given log file.

                **append** : bool
                    Append to the slsearch log file.

                **no_atmospheric** : bool
                    If True will exclude atmospheric lines from the results.
                    Default: False
                    (splatalogue)

                **no_potential** : bool
                    If True will exclude potential species from the results.
                    Default: False
                    (splatalogue)

                **no_probable** : bool
                    If True will exclude probable species from the results.
                    Default: False
                    (splatalogue)

                **exclude** : list
                    Alternate method of excluding types, can contain any of
                    "atmospheric", "potential", or "probable"

                **include_only_nrao** or **only_NRAO_recommended** : bool
                    If True only NRAO recommended transitions will be returned.
                    Default: False
                    (splatalogue)

                **displayLovas** : bool
                    If True include results from the Lovas Line List.
                    Default: False
                    (splatalogue)

                **displaySLAIM** : bool
                    If True include results from the SLAIM molecular database.
                    Default: False
                    (splatalogue)

                **displayJPL** : bool
                    If True include results from the JPL database.
                    Default: False
                    (splatalogue)

                **displayCDMS** : bool
                    If True include results from the Cologne database.
                    Default: False
                    (splatalogue)

                **displayToyaMA** : bool
                    If True include results from the ToyaMA database.
                    Default: False
                    (splatalogue)

                **displayOSU** : bool
                    If True include results from the Ohio State database.
                    Default: False
                    (splatalogue)

                **displayLisa** : bool
                    If True include results from the the 13 methyl formate database.
                    Default: False
                    (splatalogue)

                **displayRFI** : bool
                    If True include RFI lines
                    Default: False
                    (splatalogue)

                **line_lists** : list
                    Alternate method to specify which database to search. Can contain any
                    of the following:
                    "Lovas", "SLAIM", "JPL", "CDMS", "ToyaMA", "OSU", "Lisa", "RFI"
                    (splatalogue)

                **ls1** : bool
                    If True then return the JPL line strength.
                    Default: False
                    (splatalogue)

                **ls2** : bool
                    If True then return the Smu^2 line strength.
                    Default: False
                    (splatalogue)

                **ls3** : bool
                    If True then return the S line strength.
                    Default: False
                    (splatalogue)

                **ls4** : bool
                    If True then return the Eistein A.
                    Default: False
                    (splatalogue)

                **ls5** : bool
                    If True then return the Lovas line strength.
                    Default: False
                    (splatalogue)

                **line_strengths** : list
                    Alternate way of specifying the line strength(s) to return.
                    Can be any of the following: "ls1", "ls2", "ls3", "ls4", "ls5"
                    (splatalogue)

                **el1** : bool
                    If True then return the lower state energy in cm^-1.
                    Default: False
                    (spltalogue)

                **el2** : bool
                    If True then return the lower state energy in K.
                    Default: False
                    (splatalogue)

                **el3** : bool
                    If True then return the upper state energy in cm^-1.
                    Default: False
                    (splatalogue)

                **el4** : bool
                    If True then return the upper state energy in K.
                    Default: False
                    (splatalogue)

                **energy_levels** : list
                    Alternate way of specifying the energy levels to return. Can contain
                    any of the following: "el1", "el2", "el3", "el4"
                    (splatalogue)

                **fel** : bool
                    If True exclude results where the frequency uncertainty
                    is more than 50 MHz.
                    Default: False
                    (splatalogue)

                **noHFS** : bool
                    If True then do not return hyperfine split lines, only the
                    main component.
                    Default: False
                    (splatalogue)

                **displayHFS** : bool
                    If True then return the hyperfine strengths of split lines.
                    Default: False
                    (splatalogue)

                **show_unres_qn** : bool
                    If True then return the unresolved quantum numbers.
                    Default: False
                    (splatalogue)

                **show_upper_degeneracy** : bool
                    If True then return the uper state degeneracy.
                    Default: False
                    (splatalogue)

                **show_molecule_tag** : bool
                    If True then return the molecule tag.
                    Default: False
                    (splatalogue)

                **show_lovas_labref** : bool
                    If True then return the Lovas lab reference.
                    Default: False
                    (splatalogue)

                **show_lovas_obsref** : bool
                    If True then return the Lovas observational reference.
                    Default: False
                    (splatalogue)

                **show_orderedfreq_only** : bool
                    If True then
                    Default: False
                    (splatalogue)

                **show_nrao_recommended** : bool
                    If True then return the NRAO recommended frequency.
                    (splatalogue)

                **top20** : list
                    Include the results from the given top20 lists. Possibilities are:
                    'comet', 'planet', 'ism_hotcore', 'ism_darkcloud', 'ism_diffusecloud'
                    (splatalogue)

                **comet** : bool
                    If True then return results most likely found in comets.
                    (splatalogue)

                **planet** : bool
                    If True then return results most likely found in planetary atmospheres.
                    (splatalogue)

                **ism_hotcore** : bool
                    If True then return results most liekly found in hot cores.
                    (splatalogue)

                **ism_darkcloud** : bool
                    If True then return results most likely found in dark clouds.
                    (splatalogue)

                **ism_diffusecloud** : bool
                    If True then return results most likely found in diffuse clouds.
                    (splatalogue)

                **band** : str
                    Which band to use for frequency range, will override any specified
                    frequency range.
                    (splatalogue)

                **species** : str
                    Limit the results to the given molecule

                **reconly** or **only_NRAO_recommended** : bool
                    Only return results with recommended NROA rest frequencies. This option
                    can remove duplicate records arising from the multiple databases inside
                    slsearch and splatalogue.
                    Default: False

                **chemnames** or **chemical_name** : str
                    Limit the results to the given molecule.

                **qns** or **transition** : str
                    Limit the results to the specified quantum numbers.

                **energy_type** : str
                    Energy units for both the el and eu keywords. Possibilities are
                    'K' for Kelvin, and 'cm' for inverse cm.

                **el** : list or float
                    If a list then the range of lower state energies to search between,
                    else it is treated as a lower limit. Note splatalogue only supports
                    a lower limit, so upper limit is ignored, but passed to slsearch.

                **eu** : list or float
                    If a list then the range of upper state energies to search between,
                    else it is treated as a lower limit. Note splatalogue only supports
                    a lower limit, so upper limit is ignored, but passed to slsearch.

                **smu2** : list or float
                    If a list then the range of line strengths to search between, in D^2,
                    else it is treated as a lower limit. Note splatalogue only supports
                    a lower limit, so upper limit is ignored, but passed to slsearch.

                **loga** : list or float
                    If a list then the range of line strengths to search between, in log
                    of the Einstein A,
                    else it is treated as a lower limit. Note splatalogue only supports
                    a lower limit, so upper limit is ignored, but passed to slsearch.

                **intensity** : list or float
                    If a list then the range of line strengths to search between, in JPL
                    intensity units,
                    else it is treated as a lower limit. Note splatalogue only supports
                    a lower limit, so upper limit is ignored, but passed to slsearch.

            Returns
            -------
            None

        """
        # set the mandatory, common keys
        # frequency limits
        self.sls_kw["freqrange"] = [minfreq, maxfreq]
        self.sp_kw["min_frequency"] = minfreq
        self.sp_kw["max_frequency"] = maxfreq

        # whether to return recombination lines
        if rrlevelstr == "OFF":
            self.sls_kw["rrlinclude"] = False
        else:
            self.sls_kw["rrlinclude"] = True
            #self.sp_kw["displayRecomb"] = "displayRecomb"

        # set keys that are specific to slsearch
        # output table name
        if "tablename" in kwargs:
            self.sls_kw["tablename"] = kwargs["tablename"]

        # output file name
        if "outfile" in kwargs:
            self.sls_kw["outfile"] = kwargs["outfile"]

        # only return recombination lines
        if "rrlonly" in kwargs:
            self.sls_kw["rrlonly"] = kwargs["rrlonly"]

        # be verbose in the search
        if "verbose" in kwargs:
            self.sls_kw["verbose"] = kwargs["verbose"]

        # send results to the given log file
        if "logfile" in kwargs:
            self.sls_kw["logfile"] = kwargs["logfile"]

        # append to the log file
        if "append" in kwargs:
            self.sls_kw["append"] = kwargs["append"]

        # set keys that are specific to splatalogue
        # exclude atmospheric lines
        if "no_atmospheric" in kwargs:
            self.sp_kw["exclude"].append("atmospheric")

        # exclude potential species
        if "no_potential" in kwargs:
            self.sp_kw["exclude"].append("potential")

        # exclude probable species
        if "no_probable" in kwargs:
            self.sp_kw["exclude"].append("probable")

        # allow a different way of excluding types
        if "exclude" in kwargs:
            for e in kwargs["exclude"]:
                self.sp_kw["exclude"].append(e)

        #if "known" in kwargs:
        #    self._kw["known"] = kwargs["known"]

        # include only the NRAO recommended transitions
        # can eliminate duplicates from splatalogue
        if "include_only_nrao" in kwargs or "only_NRAO_recommended" in kwargs:
            self.sp_kw["only_NRAO_recommended"] = "only_NRAO_recommended"

        # display results from the different lists
        if "displayLovas" in kwargs or "Lovas" in kwargs:
            self.sp_kw["line_lists"].append("Lovas")

        if "displaySLAIM" in kwargs or "SLAIM" in kwargs:
            self.sp_kw["line_lists"].append("SLAIM")

        if "displayJPL" in kwargs or "JPL" in kwargs:
            self.sp_kw["line_lists"].append("JPL")

        if "displayCDMS" in kwargs or "CDMS" in kwargs:
            self.sp_kw["line_lists"].append("CDMS")

        if "displayToyaMA" in kwargs or "ToyaMA" in kwargs:
            self.sp_kw["line_lists"].append("ToyaMA")

        if "displayOSU" in kwargs or "OSU" in kwargs:
            self.sp_kw["line_lists"].append("OSU")

        if "displayLisa" in kwargs or "Lisa" in kwargs:
            self.sp_kw["line_lists"].append("Lisa")

        if "displayRFI" in kwargs or "RFI" in kwargs:
            self.sp_kw["line_lists"].append("RFI")

        # alternate method of setting the line lists
        if "line_lists" in kwargs:
            for l in kwargs["line_lists"]:
                self.sp_kw["line_lists"].append(l)

        # set which line strengths to return
        for ls in ["ls1", "ls2", "ls3", "ls4", "ls5"]:
            if ls in kwargs:
                self.sp_kw["line_strengths"].append(ls)

        # alternate method
        if "line_strengths" in kwargs:
            for ls in kwargs["line_strengths"]:
                self.sp_kw["line_strengths"].append(ls)

        # set which energy labels to return
        for el in ["el1", "el2", "el3", "el4"]:
            if el in kwargs:
                self.sp_kw["energy_levels"].append(el)

        # alternate method
        if "energy_levels" in kwargs:
            for el in kwargs["energy_levels"]:
                self.sp_kw["energy_levels"].append(el)

        # exclude transitions with high uncertainty
        if "fel" in kwargs:
            self.sp_kw["fel"] = kwargs["fel"]

        # set other keywords
        for kw in ["noHFS", "displayHFS", "show_unres_qn", "show_upper_degeneracy"
                   "show_molecule_tag", "show_lovas_labref", "show_lovas_obsref",
                   "show_orderedfreq_only", "show_nrao_recommended"]:
            if kw in kwargs:
                self.sp_kw[kw] = kwargs[kw]

        # select a top20 list
        if "top20" in kwargs:
            for tp in kwargs["top20"]:
                self.sp_kw["top20"].append(tp)

        # altername method
        for tp in ['comet', 'planet', 'top20', 'ism_hotcore', 'ism_darkcloud', 'ism_diffusecloud']:
            if tp in kwargs:
                self.sp_kw[tp] = kwargs[tp]

        # set which band to use
        if "band" in kwargs:
            self.sp_kw["band"] = kwargs["band"]

        # set common keys
        # select a specific species
        if "species" in kwargs:
            self.sls_kw["species"] = kwargs["species"]
            self.sp_kw["sid[]"] = kwargs["species"]

        # select if only recombination lines should be returned
        if "reconly" in kwargs:
            self.sls_kw["reconly"] = kwargs["reconly"]
            self.sp_kw["only_NRAO_recommended"] = kwargs["reconly"]
        elif "only_NRAO_recommended" in kwargs:
            self.sls_kw["reconly"] = kwargs["only_NRAO_recommended"]
            self.sp_kw["only_NRAO_recommended"] = kwargs["only_NRAO_recommended"]

        # select a specific chemical name
        if "chemnames" in kwargs:
            self.sls_kw["chemnames"] = kwargs["chemnames"]
            self.sp_kw[""] = kwargs["chemnames"]

        # select specific quantum numbers
        if "qns" in kwargs:
            self.sls_kw["qns"] = kwargs["qns"]
            self.sp_kw["transition"] = kwargs["qns"]

        # set limits on the lower energy
        if "el" in kwargs:
            mult = 1.0
            if "energy_type" in kwargs and "K" not in kwargs["energy_type"].upper():
                mult = 1.42879
            if not isinstance(kwargs["el"], (list, tuple, set, float, int)):
                raise Exception("Improper format for 'el'")
            elif isinstance(kwargs["el"], (list, tuple, set)):
                if len(kwargs["el"]) == 1:
                    el = [kwargs["el"][0] * mult, 100000]
                else:
                    el = [kwargs["el"][0] * mult, kwargs["el"][1] * mult]
            else:
                el = [kwargs["el"] * mult, 100000]
            self.sls_kw["el"] = el
            self.sp_kw["energy_min"] = el[0]
            self.sp_kw["energy_max"] = el[1]
            self.sp_kw["energy_type"] = "el_k"
        # set limits on the upper energy
        elif "eu" in kwargs:
            mult = 1.0
            if "energy_type" in kwargs and "K" not in kwargs["energy_type"].upper():
                mult = 1.42879
            if not isinstance(kwargs["eu"], (list, tuple, set, float, int)):
                raise Exception("Improper format for 'eu'")
            elif isinstance(kwargs["eu"], (list, tuple, set)):
                if len(kwargs["eu"]) == 1:
                    eu = [kwargs["eu"][0] * mult, 100000]
                else:
                    eu = [kwargs["eu"][0] * mult, kwargs["eu"][1] * mult]
            else:
                eu = [kwargs["eu"] * mult, 100000]
            self.sls_kw["eu"] = eu
            self.sp_kw["energy_min"] = eu[0]
            self.sp_kw["energy_max"] = eu[1]
            self.sp_kw["energy_type"] = "eu_k"

        # set limits on the line strength
        if "smu2" in kwargs:
            if not isinstance(kwargs["smu2"], (list, tuple, set, float, int)):
                raise Exception("Improper format for 'smu2'")
            elif isinstance(kwargs["smu2"], (list, tuple, set)):
                if len(kwargs["smu2"]) == 1:
                    smu = [kwargs["smu2"][0], 100000]
                else:
                    smu = [kwargs["smu2"][0], kwargs["smu2"][1]]
            else:
                smu = [kwargs["smu2"], 100000]
            self.sls_kw["smu2"] = smu
            self.sp_kw["intensity_lower_limit"] = smu[0]
            self.sp_kw["intensity_type"] = "sijmu2"

        # set limits on the Einstein A
        elif "loga" in kwargs:
            if not isinstance(kwargs["loga"], (list, tuple, set, float, int)):
                raise Exception("Improper format for 'loga'")
            elif isinstance(kwargs["loga"], (list, tuple, set)):
                if len(kwargs["loga"]) == 1:
                    loga = [kwargs["loga"][0], 100000]
                else:
                    loga = [kwargs["loga"][0], kwargs["loga"][1]]
            else:
                loga = [kwargs["loga"], 100000]
            self.sls_kw["loga"] = loga
            self.sp_kw["intensity_lower_limit"] = loga[0]
            self.sp_kw["intensity_type"] = "aij"

        # set limits on the JPL intensity
        elif "intensity" in kwargs:
            if not isinstance(kwargs["intensity"], (list, tuple, set, float, int)):
                raise Exception("Improper format for 'intensity'")
            elif isinstance(kwargs["intensity"], (list, tuple, set)):
                if len(kwargs["intensity"]) == 1:
                    intensity = [kwargs["intensity"][0], 100000]
                else:
                    intensity = [kwargs["intensity"][0], kwargs["intensity"][1]]
            else:
                intensity = [kwargs["intensity"], 100000]
            self.sls_kw["intensity"] = intensity
            self.sp_kw["intensity_type"] = "cdms_jpl"
            self.sp_kw["intensity_lower_limit"] = intensity[0]

    def checktier1overlap(self, freq):
        """ Method to check for an overlap with tier1 lines.

            Parameters
            ----------
            freq : float
                The frequency to check if it is within an existing tier1
                frequency range

            Returns
            -------
            Boolean, True if freq is within a tier1 range, False otherwise

        """
        for f in self.tier1freq:
            if f[0] < freq < f[1]:
                return True
        return False

    def check_online(self):
        """ Method to check whether we are online or not. Just does a simple http
            request to www.cv.nrao.edu, the host of splatalogue

            Parameters
            ----------
            None

            Returns
            -------
            Boolean saying whether we are online (True) or not (False)

        """
        try:
            response = urllib2.urlopen('http://www.cv.nrao.edu', timeout=10)
            return True
        except urllib2.URLError:
            logging.error("Cannot reach splatalogue server, please check your internet connection.")
            raise Exception("Cannot reach splatalogue server, please check your internet connection.")

    def search(self, minfreq, maxfreq, rrlevelstr, allowExotics=False, **kwargs):
        """ Method to do the search and return the results. Regardless of the search
            method used the results will have the same format and units.

            Parameters
            ----------
            minfreq : float
                The starting frequency for the search, in GHz.

            maxfreq : float
                The ending frequency for the search, in GHz.

            rrlevelstr : str
                A string representation of the depth of recombination lines to return

            allowExotics : bool
                Whether or not to allow exotic atoms in the results (e.g. Ti).
                Default: False

            kwargs : dict
                Dictionary containing any keyword/value pairs for the search. Possibilities are:


        """
        # set keyword args
        self.setkeywords(minfreq, maxfreq, rrlevelstr, **kwargs)
        if self.online:
            try:
                return self.splatalogue(minfreq, maxfreq, rrlevelstr, allowExotics)
            except Exception:
                logging.info("Error raised in splatalogue call, trying slsearch")
                raise
        return self.slsearch(rrlevelstr, allowExotics)

    def slsearch(self, rrlevelstr, allowExotics):
        """ Method to search through the slsearch database. Search options must already
            have been set. Returns a formatted list of transitions, each item in the list
            is another list containing the following:

            #. Chemical formula

            #. Name

            #. Rest frequency

            #. Unique identifier

            #. Lower state energy in K

            #. Upper state energy in K

            #. Linestrength in D^2

            #. Mass of molecule (rough)

            #. Transition quantum numbers

            #. Cleanly formatted chemical formula for display purposes

            #. Number of non-standard isotopes in the molecule

            Parameters
            ----------
            rrlevelstr : str
                String representation of how deep to search for recombination lines. Possibilities
                are:

                + `off`      no recombination lines are allowed in the results.
                + `shallow`  only H and He, alpha and beta lines are allowed in the results.
                + `deep`     any recombination line is allowed in the results.

            allowExotics : bool
                Whether or not to allow exotic atoms in the molecules (e.g Ti)

            Returns
            -------
            A list of LineData objects, with each containing the data for a single transition.

        """
        try:
            from slsearch import slsearch
            import taskinit
        except:
            logging.info("WARNING: No CASA, slsearch is not available, no line identificaiton possible.")
            raise
        if "outfile" not in self.sls_kw:
            # @todo should really use tempfile, or $$; this is an accident in waiting
            # also, in the same namespace if a seed is the same, the accident is guarenteed; see genspec.py)
            flname = "/tmp/slsearch.%i" % (int(random.random() * 1000))
            utils.remove(flname)
            self.sls_kw["outfile"] = flname
        # do the search
        #print self.sls_kw
        #print flname
        slsearch(**self.sls_kw)
        # open the table and get the contents
        tb = taskinit.tbtool()
        tb.open(self.sls_kw["outfile"])
        numrows = tb.nrows()
        possible = []
        # convert the results to a list
        for row in range(numrows):
            species = tb.getcell("SPECIES", row)
            name = tb.getcell("CHEMICAL_NAME", row)
            freq = float(tb.getcell("FREQUENCY", row))
            qn = tb.getcell("QUANTUM_NUMBERS", row)
            linestr = float(tb.getcell("SMU2", row))
            el = float(tb.getcell("EL", row))
            eu = float(tb.getcell("EU", row))
            # only add it to the output list if it does not contain an exotic atom,
            # or if exotics are allowed
            if not utils.isexotic(species or allowExotics):
                if (not "RECOMBINATION" in name.upper() \
                   or ("RECOMBINATION" in name.upper()
                      and (rrlevelstr == "DEEP" or ("H" in species \
                          and ("alpha" in species or "beta" in species))))) \
                   and not self.checktier1overlap(freq):
                    possible.append(LineData(formula=species, name=name, frequency=freq,
                                    uid=utils.getplain(species) + "_%.5f" % freq,
                                    energies=[el, eu], linestrength=linestr, mass=utils.getmass(species),
                                    transition=qn, plain=utils.getplain(species),
                                    isocount=utils.isotopecount(species)))
        tb.close()
        # remove the temporary table
        utils.remove(self.sls_kw["outfile"])
        return possible

    def splatalogue(self, minfreq, maxfreq, rrlevelstr, allowExotics):
        """ Method to search through the slsearch database. Search options must already
            have been set. Returns a formatted list of transitions, each item in the list
            is another list containing the following:

            #. Chemical formula

            #. Name

            #. Rest frequency

            #. Unique identifier

            #. Lower state energy in K

            #. Upper state energy in K

            #. Linestrength in D^2

            #. Mass of molecule (rough)

            #. Transition quantum numbers

            #. Cleanly formatted chemical formula for display purposes

            #. Number of non-standard isotopes in the molecule

            Parameters
            ----------
            rrlevelstr : str
                String representation of how deep to search for recombination lines. Possibilities
                are:

                + `off`      no recombination lines are allowed in the results.
                + `shallow`  only H and He, alpha and beta lines are allowed in the results.
                + `deep`     any recombination line is allowed in the results.

            allowExotics : bool
                Whether or not to allow exotic atoms in the molecules (e.g Ti)

            Returns
            -------
            A list of LineData objects, with each containing the data for a single transition.

        """
        possible = []
        # initialize the interface class
        sp = Splatalogue.Splatalogue(**self.sp_kw)
        # do the search
        results = sp.query_lines(minfreq, maxfreq)
        # get the results
        lines = results.readlines()
        # the top row is the column headings as one long string
        # split the string into its individual components
        header = lines[0].split(":")
        # the indexes of the data are not guaranteed, so search for each needed one
        # by its known name, if splatalogue changes the column headings this will
        # break
        sidx = header.index("Species")
        cidx = header.index("Chemical Name")
        fidx = header.index("Freq-GHz")
        bfidx = header.index("Meas Freq-GHz")
        qidx = header.index("Resolved QNs")
        stidx = header.index("S<sub>ij</sub>&#956;<sup>2</sup> (D<sup>2</sup>)")
        elidx = header.index("E_L (K)")
        euidx = header.index("E_U (K)")
        # remove the header row so the rest can be iterated over
        del lines[0]
        # make sure all of the indexes are found
        if min(sidx, cidx, fidx, qidx, stidx, elidx, euidx, bfidx) < 0:
            raise Exception("Missing data") # need a better message
        # iterate over all the results
        for line in lines:
            # sploit into columns
            row = line.split(":")
            # see which frequency we have, prefering the 'Freq-GHz' column
            if not row[fidx]:
                freq = float(row[bfidx])
            else:
                freq = float(row[fidx])
            # process the result, dropping if needed
            if not utils.isexotic(row[sidx] or allowExotics):
                if (not "RECOMBINATION" in row[cidx].upper() \
                   or ("RECOMBINATION" in row[cidx].upper()
                      and (rrlevelstr == "DEEP" or ("H" in row[sidx] \
                          and ("alpha" in row[sidx] or "beta" in row[sidx]))))) \
                   and not self.checktier1overlap(row[fidx]):
                    possible.append(LineData(formula=row[sidx], name=row[cidx], frequency=freq,
                                    uid=utils.getplain(row[sidx]) + "_%.5f" % freq,
                                    energies=[float(row[elidx]), float(row[euidx])], linestrength=float(row[stidx]), mass=utils.getmass(row[sidx]),
                                    transition=row[qidx], plain=utils.getplain(row[sidx]),
                                    isocount=utils.isotopecount(row[sidx])))

        return possible
