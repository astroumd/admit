""" .. _splatalogue:

    **Splatalogue** --- Module for performing splatalogue queries.
    --------------------------------------------------------------

    Module to search Splatalogue.net via splat, modeled loosely on
    ftp://ftp.cv.nrao.edu/NRAO-staff/bkent/slap/idl/
    :author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
    :updated for CASA:  Brian Kent <bkent@nrao.edu>
    :updated for ADMIT: Douglas Friedel <friedel@illinois.edu>

    Dependencies for python requests and astropy modules have been removed.
"""
import urllib
import urllib2
import json
import re

from admit.util.AdmitLogging import AdmitLogging as logging

column_headings_map = {'Log<sub>10</sub> (A<sub>ij</sub>)': 'log10(Aij)',
                       'E_U (K)': 'EU_K',
                       'Resolved QNs': 'QNs',
                       'S<sub>ij</sub>': 'Sij', }


def clean_column_headings(header, renaming_dict=column_headings_map):
    """ Rename column headings to shorter version that are easier for display
        on-screen / at the terminal

        Parameters
        ----------
        header : dict
            A dictionary of the header keywords

        renaming_dict : dict
            A dictionary containing the old names (as the key) and the new
            names (as the value)

        Returns
        -------
        The new header.
    """
    for key in renaming_dict:
        header = [renaming_dict[key] if i == key else i for i in header]

    return header


class SpeciesLookuptable(dict):
    """ Simple class that extends the dictionary class so that keys can be searched

    """

    def find(self, s, flags=0, return_dict=True):
        """
        Search dictionary keys for a regex match to string s

        Parameters
        ----------
        s : str
            String to compile as a regular expression

        return_dict : bool
            Return a dictionary if true or just the matching values if false.
            Default: True

        flags : int
            re (regular expression) flags. Default: 0

        Returns
        -------
        Subset of parent dictionary if return_dict, else list of values
        corresponding to matches
        """

        R = re.compile(s, flags)

        out = SpeciesLookuptable(dict((k, v) for k, v in self.items() if R.search(k)))

        if return_dict:
            return out
        else:
            return out.values()

def species_lookuptable(filename='species.json'):
    """ Method to read in a file and turn it into a searchable dictionary

        Parameters
        ----------
        filename : str
            The name of the file to read. Default: 'species.json'

        Returns
        -------
        A lookup table with the contents of the input file

    """
    with open(filename, 'r') as f:
        J = json.load(f)

    lookuptable = SpeciesLookuptable(dict((v, k) for d in J.values() for k, v in d.items()))

    return lookuptable


class Splatalogue(object):
    """ Class for searching for lines in the online Splatalogue database.
        The resulting Splatalogue tables can be returned as a list of dictionaries.

        Parameters
        ----------
        kwargs : dict
            The keyword value pairs of the arguments, possible keywords are:

            **min_frequency** : float
                Lower limit of frequency search range in GHz. Default: 0.0

            **max_frequency** : float
                Upper limit of frequency search range in GHz. Defualt: 100000.0

            **band** : str
                The frequency band to search in. 'min/max_frequency' and 'band' are mutually
                exclusive. If both are given then 'band' is preferred. Possibles are

                "any": All bands

                "alma3": ALMA Band 3 (84-116 GHz)

                "alma4": ALMA Band 4 (125-163 GHz)

                "alma5": ALMA Band 5 (163-211 GHz)

                "alma6": ALMA Band 6 (211-275 GHz)

                "alma7": ALMA Band 7 (275-373 GHz)

                "alma8": ALMA Band 8 (385-500 GHz)

                "alma9": ALMA Band 9 (602-720 GHz)

                "alma10": ALMA Band 10 (787-950 GHz)

                "pf1": GBT PF1 (0.29-0.92 GHz)

                "pf2": GBT PF2 (0.91-1.23 GHz)

                "l": GBT/VLA L (1-2 GHz)

                "s": GBT/VLA S (1.7-4 GHz)

                "c": GBT/VLA C (3.9-8 GHz)

                "x": GBT/VLA X (8-12 GHz)

                "ku": GBT/VLA Ku (12-18 GHz)

                "kfpa": GBT KFPA (18-27.5 GHz)

                "k": VLA K (18-26.5 GHz)

                "ka": GBT/VLA Ka (26-40 GHz)

                "q": GBT/VLA Q (38-50 GHz)

                "w": GBT W (67-93.3 GHz)

                "mustang": GBT Mustang (80-100 GHz)

                Default: 'any'

            **top20** : list
                Limit results to the given top20 list(s). Possibles are:

                'comet': molecules most likely found in comets

                'planet': molecules most likely planetary atmospheres

                'top20': most common molecules

                'ism_hotcore': molecules most likely found in hot cores

                'ism_darkcloud': molecules most likely found in dark clouds

                'ism_diffusecloud': molecules most likely found in diffuse clouds

                Default: None

            **chemical_name** : str
                Limit results to the specified chemical, by name. Default: ''

            **line_lists** : list
                Which line list(s) to use for the search. Possibles are:

                'Lovas': Search the Lovas/NIST list of molecules

                'SLAIM': Search the SLAIM list of molecules

                'JPL': Search the Jet Propulsion Lab list of molecules

                'CDMS': Search the Cologne database of molecules

                'ToyoMA': Search the ToyoMA list of moleules

                'OSU': Search the Ohio State list of molecules

                'Recomb': Search for recombination lines

                'Lisa': Search the TopModel list

                'RFI': Search for radio frequency interference lines

                Default: ['Lovas', 'SLAIM', 'JPL', 'CDMS', 'ToyoMA', 'OSU', 'Recomb', 'Lisa', 'RFI']

            **line_strengths** : list
                Which line strength units should be reported, several can be given.
                Possibles are:

                'ls1': JPL/CDMS

                'ls2': Sijmu^2

                'ls3': Sij

                'ls4': Aij

                'ls5': Lovas/SLAIM

                Default: ('ls1', 'ls2', 'ls3', 'ls4', 'ls5')

            **energy_levels** : list
                Which energies should be reported. Possibles are:

                'el1': Lower state in cm^-1

                'el2': Lower state in K

                'el3': Upper state in cm^-1

                'el4': Upper state in K

                Default: ['el1', 'el2', 'el3', 'el4']

            **exclude** : list
                Which types of molecules to exclude from the search. Possibles are:

                'potential': Species that may be found in the ISM

                'atmospheric': Species know to be in the Earth's atmosphere

                'probable': Species that might be found in the ISM

                Default: ['potential', 'atmospheric', 'probable']

            **version** : str
                Which Splatalogue interface is being used. Default: 'v2.0'

            **only_NRAO_recommended** : bool
                Only return lines that are recommended by NROA. Can eliminate duplicate
                lines from multiple databases. Default: False

            **export** : bool
                Wherther splatalogue should return an export formatted list rather than HTML.
                Default: True

            **export_limit** : int
                The maximum number of lines to return. Default: 10000

            **noHFS** : bool
                Whether or not to suppress hyperfine components in the results.
                Default: False

            **displayHFS** : bool
                Whether or not to return the hyperfine line strength.
                Default: False

            **show_unres_qn** : bool
                Whether or not to return the unresolved quantum numbers. Typically in a
                machine readable format. Default: False

            **show_upper_degeneracy** : bool
                Whether or not th return the upper state degeneracy of each transition.
                Default: False

            **show_molecule_tag** : bool
                Whether or not to return the molecule tag. Default: False

            **show_qn_code** : bool
                Whether or not to return the quantum number encoding (the encoding of
                'show_unres_qn'). Default: False

            **show_lovas_labref** : bool
                Whether or not to return the lab reference frequency from the Lovas/NIST list.
                Default: False

            **show_lovas_obsref** : bool
                Whether or not to return the observational reference from the Loval/NIST list.
                Default: False

            **show_orderedfreq_only** : bool
                Default: False

            **show_nrao_recommended** : bool
                Whether or not to return the NRAO recommended rest frequency. Default: False

            **chem_re_flags** : int
                Default: 0

            **energy_min** : float
                Minimum lower/upper state energy to search for. Units are specified in
                'energy_type'. Default None

            **energy_max** : float
                Maximum lower/upper state energy to search for. Units are specified in
                'energy_type'. Default None

            **energy_type** : str
                The energy units for the 'energy_min' and 'energy_max' columns. Possibles are:

                'el_cm1': Lower state in cm^-1

                'el_k': Lower state in K

                'eu_cm1': Upper state in cm^-1

                'eu_k': Upper state in K

                Default: None

            **intensity_lower_limit** : float
                Lower limit for the transition strength, units are specified in 'intensity_type'.
                Default: None

            **intensity_type** : str
                The units for the 'intensity_lower_limit' parameter. Possibles are:

                'cdms_jpl': Cologne database/JPL intensity units

                'aij': Einstein A units

                'sijmu2': Smu^2, line strength times the square of the relevant dipole
                    moment

                Default: None

            **transition** : str
                Seach for a specific transition (i.e. '(1-0)''). Default: None

            **fel** : bool
                Whether or not to remove results that have an uncertainty of over 50 MHz.
                Default: False

            Attributes
            ----------
            None

        Examples
        --------

        >>> from splatalogue import Splatalogue
        >>> sp = Splatalogue  #Create an object of type Splatalogue

        >>> # Query by frequency range in units of GHz
        >>> sp.query_lines(min_frequency=114.0, max_frequency=116.0)

        >>> # Query by frequency range and chemical name
        >>> sp.query_lines(min_frequency=114.0, max_frequency=116.0, chemical_name=" CO ")

        >>> # Query by frequency range (no keywords needed and chemical name)
        >>> sp.query_lines(0.1,1000.0, chemical_name='Ethylene Glycol')

        >>> # Query by line list and energy
        >>> sp.query_lines(218.40, 218.50, energy_max=300, energy_type='eu_k', line_lists='JPL')

        >>> # Parse response into a list of dictionaries and store in result
        >>> result = sp.parse_response()

    """

    #SLAP_URL = 'http://find.nrao.edu/splata-slap/slap'  #NOT USED
    QUERY_URL = 'http://www.cv.nrao.edu/php/splat/c_export.php'
    TIMEOUT = 60
    versions = ('v1.0', 'v2.0')
    LINES_LIMIT = 10000
    ALL_LINE_LISTS = ('Lovas', # Lovas/NIST list http://physics.nist.gov/PhysRefData/
                      'SLAIM', # SLAIM List http://physics.nist.gov/cgi-bin/micro/table5/start.pl
                      'JPL',   # JPL list http://spec.jpl.nasa.gov/
                      'CDMS',  # Cologne database http://www.ph1.uni-koeln.de/vorhersagen/
                      'ToyoMA',# Toyama Atlas http://www.sci.u-toyama.ac.jp/phys/4ken/atlas/
                      'OSU',   # Ohio state list
                      'Recomb', # recombination lines
                      'Lisa',  # 13 Methyl formate list
                      'RFI')   # RFI lines
    TOP20_LIST = ('comet', 'planet', 'top20', 'ism_hotcore', 'ism_darkcloud', 'ism_diffusecloud')
    FREQUENCY_BANDS = {"any":"Any",
                       "alma3":"ALMA Band 3 (84-116 GHz)",
                       "alma4":" ALMA Band 4 (125-163 GHz)",
                       "alma5":" ALMA Band 5 (163-211 GHz)",
                       "alma6":"ALMA Band 6 (211-275 GHz)",
                       "alma7":"ALMA Band 7 (275-373 GHz)",
                       "alma8":"ALMA Band 8 (385-500 GHz)",
                       "alma9":"ALMA Band 9 (602-720 GHz)",
                       "alma10":"ALMA Band 10 (787-950 GHz)",
                       "pf1":"GBT PF1 (0.29-0.92 GHz)",
                       "pf2":"GBT PF2 (0.91-1.23 GHz)",
                       "l":"GBT/VLA L (1-2 GHz)",
                       "s":"GBT/VLA S (1.7-4 GHz)",
                       "c":"GBT/VLA C (3.9-8 GHz)",
                       "x":"GBT/VLA X (8-12 GHz)",
                       "ku":" GBT/VLA Ku (12-18 GHz)",
                       "kfpa":"GBT KFPA (18-27.5 GHz)",
                       "k":"VLA K (18-26.5 GHz)",
                       "ka":" GBT/VLA Ka (26-40 GHz)",
                       "q":"GBT/VLA Q (38-50 GHz)",
                       "w":"GBT W (67-93.3 GHz)",
                       "mustang":"GBT Mustang (80-100 GHz)", }

    def __init__(self, **kwargs):
        """ Initialize a Splatalogue query class with default arguments set.
            Frequency specification is required for *every* query, but any
            default keyword arguments (see `query_lines`) can be overridden
            here.
        """
        self.data = self._default_kwargs()
        self.set_default_options(**kwargs)

    def set_default_options(self, **kwargs):
        """ Method to modify the default options.

            Parameters
            ----------
            kwargs : dict
                See the class description for the key words and their meaning

            Returns
            -------
            None
        """
        self.data.update(self._parse_kwargs(**kwargs))

    def get_species_ids(self, restr=None, reflags=0):
        """ Get a dictionary of "species" IDs, where species refers to the molecule
            name, mass, and chemical composition.

            Parameters
            ----------
            restr : str
                String to compile into an re, if specified.   Searches table for
                species whose names match. Default: None

            reflags : int
                Flags to pass to `re`. Default: 0

            Returns
            -------
            The id of the species
        """
        # loading can be an expensive operation and should not change at runtime:
        # do it lazily
        if not hasattr(self, '_species_ids'):
            self._species_ids = species_lookuptable()

        if restr is not None:
            return self._species_ids.find(restr, reflags)
        else:
            return self._species_ids

    def _default_kwargs(self):
        kwargs = dict(min_frequency=0.0,  #GHz
                      max_frequency=100000.0,  #GHz (100000 GHZ = 100 THz)
                      chemical_name='',
                      line_lists=self.ALL_LINE_LISTS,
                      line_strengths=('ls1', 'ls2', 'ls3', 'ls4', 'ls5'),
                      energy_levels=('el1', 'el2', 'el3', 'el4'),
                      exclude=('potential', 'atmospheric', 'probable'),
                      version='v2.0',
                      only_NRAO_recommended=False,
                      export=True,
                      export_limit=self.LINES_LIMIT,
                      noHFS=False, displayHFS=False, show_unres_qn=False,
                      show_upper_degeneracy=False, show_molecule_tag=False,
                      show_qn_code=False, show_lovas_labref=False,
                      show_lovas_obsref=False, show_orderedfreq_only=False,
                      show_nrao_recommended=False,)
        return self._parse_kwargs(**kwargs)


    def _parse_kwargs(self, min_frequency=None, max_frequency=None,
                      band='any', top20=None, chemical_name=None,
                      chem_re_flags=0, energy_min=None, energy_max=None,
                      energy_type=None, intensity_lower_limit=None,
                      intensity_type=None, transition=None, version=None,
                      exclude=None, only_NRAO_recommended=None,
                      line_lists=None, line_strengths=None, energy_levels=None,
                      export=None, export_limit=None, noHFS=None,
                      displayHFS=None, show_unres_qn=None,
                      show_upper_degeneracy=None, show_molecule_tag=None,
                      show_qn_code=None, show_lovas_labref=None,
                      show_lovas_obsref=None, show_orderedfreq_only=None,
                      show_nrao_recommended=None, fel=None):

        # set the payload of the http request
        payload = {'submit': 'Search',
                   'frequency_units': 'GHz',
                  }

        # set the band or frequency ranges
        if band != 'any':
            if band not in self.FREQUENCY_BANDS:
                raise ValueError("Invalid frequency band.")
            if min_frequency is not None or max_frequency is not None:
                logging.warning("Band was specified, so the frequency specification is overridden")
            payload['band'] = band
        elif min_frequency is not None and max_frequency is not None:
            if min_frequency > max_frequency:
                min_frequency, max_frequency = max_frequency, min_frequency

            #ASSUMES UNITS OF GHz
            payload['from'] = min_frequency
            payload['to'] = max_frequency

        # select the top20 list if given
        if top20 is not None and len(top20) > 0:
            if top20 in self.TOP20_LIST:
                payload['top20'] = top20
            else:
                raise ValueError("Top20 is not one of the allowed values")
        # set the chemical name if given
        elif chemical_name in ('', {}, (), [], set()):
            # include all
            payload['sid[]'] = []
        elif chemical_name is not None:
            # encode the chemical names to species id's
            species_ids = self.get_species_ids(chemical_name, chem_re_flags)
            if len(species_ids) == 0:
                raise ValueError("No matching chemical species found.")
            payload['sid[]'] = list(species_ids.values())

        # set the min an max energy range and untis
        if energy_min is not None:
            payload['energy_range_from'] = float(energy_min)
        if energy_max is not None:
            payload['energy_range_to'] = float(energy_max)
        if energy_type is not None:
            payload['energy_range_type'] = energy_type

        # set the minimum intensity and units
        if intensity_type is not None:
            payload['lill'] = 'lill_' + intensity_type
            if intensity_lower_limit is not None:
                payload[payload['lill']] = intensity_lower_limit

        # set the specific transition
        if transition is not None:
            payload['tran'] = transition

        # set the version id
        if version in self.versions:
            payload['version'] = version
        elif version is not None:
            raise ValueError("Invalid version specified.  Allowed versions are {vers}".format(vers=str(self.versions)))

        # set which types to exclude
        if exclude is not None:
            for e in exclude:
                payload['no_' + e] = 'no_' + e

        # set the NRAO recommended frequencies option
        if only_NRAO_recommended:
            payload['include_only_nrao'] = 'include_only_nrao'

        # set any line lists to use
        if line_lists is not None and len(line_lists) > 0:
            if type(line_lists) not in (tuple, list):
                raise TypeError("Line lists should be a list of linelist names.  See Splatalogue.ALL_LINE_LISTS")
            for L in self.ALL_LINE_LISTS:
                kwd = 'display' + L
                if L in line_lists:
                    payload[kwd] = kwd
                else:
                    payload[kwd] = ''

        # set which line strengths to return
        if line_strengths is not None:
            for LS in line_strengths:
                payload[LS] = LS

        # set which energy levels and units to return
        if energy_levels is not None:
            for EL in energy_levels:
                payload[EL] = EL

        # set other query parameters
        for b in "noHFS,displayHFS,show_unres_qn,show_upper_degeneracy,show_molecule_tag,show_qn_code,show_lovas_labref,show_orderedfreq_only,show_lovas_obsref,show_nrao_recommended,fel".split(","):
            if locals()[b]:
                payload[b] = b

        # default arg, unmodifiable...
        payload['jsMath'] = 'font:symbol,warn:0'
        payload['__utma'] = ''
        payload['__utmc'] = ''

        # if we are exporting, set the format
        if export:
            payload['submit'] = 'Export'
            payload['export_delimiter'] = 'colon'  # or tab or comma
            payload['export_type'] = 'current'
            payload['offset'] = 0
            payload['range'] = 'on'
            if export_limit is not None:
                payload['limit'] = export_limit
            else:
                payload['limit'] = self.LINES_LIMIT

        return payload

    def _validate_kwargs(self, min_frequency=None, max_frequency=None,
                         band='any'):
        """ Check that either min_frequency + max_frequency or band are specified.

        """
        if band == 'any':
            if min_frequency is None or max_frequency is None:
                raise ValueError("Must specify either min/max frequency or a valid Band.")

    def query_lines(self, min_frequency=None, max_frequency=None, **kwargs):
        """ Query Splatalogue for transitions between min_frequency and max_frequency
            with the given kwargs.

            Parameters
            ----------
            min_frequency : float
                The starting frequency for the search in GHz. Default: None

            max_frequency : float
                The ending frequency for the search in GHz. Default: None

            kwargs : dict
                Any additional arguments for the search.

            Returns
            -------
            response : `requests.Response`
                The response of the HTTP request.
        """
        # have to chomp this kwd here...
        if "min_frequency" in kwargs:
            min_frequency = kwargs["min_frequency"]
        if "max_frequency" in kwargs:
            max_frequency = kwargs["max_frequency"]
        get_query_payload = (kwargs.pop('get_query_payload')
                             if 'get_query_payload' in kwargs
                             else False)
        self._validate_kwargs(min_frequency=min_frequency,
                              max_frequency=max_frequency, **kwargs)

        if hasattr(self, 'data'):
            data_payload = self.data.copy()
            data_payload.update(self._parse_kwargs(min_frequency=min_frequency,
                                                   max_frequency=max_frequency,
                                                   **kwargs))
        else:
            data_payload = self._default_kwargs()
            data_payload.update(self._parse_kwargs(min_frequency=min_frequency,
                                                   max_frequency=max_frequency,
                                                   **kwargs))

        if get_query_payload:
            return data_payload

        #Need to pass True so that the sid[] list is handled correctly
        urlparams = urllib.urlencode(data_payload, True)

        response = urllib2.urlopen(self.QUERY_URL + '?%s' % urlparams, timeout=self.TIMEOUT)

        self.response = response

        return response

    def parse_response(self):
        """ Parse a response (of type urllib2.urlopen) into a list of dictionaries.

            Parameters
            ----------
            None

            Returns
            -------
            A dictonary of the response
        """

        result = []

        response = self.response

        try:
            csvstring = response.read()
            tablelist = csvstring.split('\n')
            header = tablelist[0]
            headerlist = header.split(':')
            headerlist = clean_column_headings(headerlist, renaming_dict=column_headings_map)

            #Populate list of dictionaries
            for row in tablelist[1:-1]:
                rowlist = row.split(':')
                rowdict = {}
                for i in range(0, len(rowlist)):
                    rowdict[headerlist[i]] = rowlist[i]
                result.append(rowdict)
        except:
            logging.warning("Problem parsing result")

        self.result = result

        return result
