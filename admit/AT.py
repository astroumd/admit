""" .. _AT-base-api:

    **Task** --- ADMIT task (AT) base.
    ----------------------------------

    This module defines the ADMIT task (AT) base class.
"""

# system level imports
import os.path
import copy
import xml.etree.cElementTree as et
import errno

# ADMIT imports
from admit.bdp.BDP import BDP
from admit.xmlio.DtdReader import DtdReader
import admit.util.bdp_types as bt
import admit.xmlio.XmlWriter as XmlWriter
import admit.util.PlotControl as PlotControl
from admit.util.AdmitLogging import AdmitLogging as logging


class AT(object):
    """ Base class for Admit Task (AT) objects.

        The ADMIT task base class implements generic interface features common
        to concrete ATs. Tasks are the basic execution unit in ADMIT and are
        responsible for operating on `BDPs`_ to perform calculations or
        otherwise transform them into new data products. Each task includes a
        unique set of keywords controlling its behavior.

        Parameters
        ----------
        keys : dictionary of str keywords with default values, optional.
          Task keyword settings; default keyword values vary by task.

          Currently the following keywords, defined by the base class, are 
          activated for each task:

          **alias** : str
            By default ATs will use an alias by appending the file basename
            they normally use with "-alias". For example, if an AT would
            normally transform "foo.im" to "foo.pv", with "alias=test" you
            would get "foo-test.pv".  The notable exception is Ingest_AT,
            where the alias replaces the (potentially long) cube file
            basename, i.e., "verylongsourcename.fits" becomes "alias.im".
            Must be unique for each concrete type of AT (will be appended with
            a unique suffix otherwise). Alias is a system keyword,
            inaccessible (via getkey()) after the task is instantiated.

          **taskid** : int
            Forces a pre-determined task ID number when instantiating the task.
            Normally left defaulted (-1, meaning auto-select), but useful in
            special circumstances. This is a system keyword, inaccessible (via
            getkey()) after the task is instantiated.

          **variflow** : bool
            Whether the flow emanating from an AT with variadic outputs should
            be dynamically adjusted according to the actual number of outputs.
            Normally left defaulted (`True`), but may be set to `False` if this
            will be managed separately or if the number of outputs is
            pre-determined for a particular instance. This is a system keyword,
            inaccessible (via getkey()) after the task is instantiated.

        keyvals : dictionary of new values for  the keywords, optional.
          These keyword value pairs can be fed in form the command line
          instantiation of the class.

        Attributes
        ----------
        _alias : str
          Task alias name. Appears in various filenames, HTML output, flow
          diagrams, etc.

        _taskid : int
          Task ID number (defaults to ``None``, normally set by FlowManager).

        _baseDir : str
          Project base directory (None if unknown).

        _bdp_in : list of BDPs_
          BDP input cache.

        _bdp_in_map : list of ints
          BDP IDs corresponding to those listed in _bdp_in.

        _bdp_out : list of BDPs_
          BDP output cache.

        _bdp_out_map : list of ints
          BDP IDs corresponding to those listed in _bdp_out.

        _keys : dict
          Task keyword dictionary.

        _link : int
          Link count (for multiflows).

        _type : str
          Concrete task type.

        _stale : boolean
          Whether the AT needs to be run (e.g., a keyword changed).

        _enabled : boolean
          Whether the AT is enabled; if set to False, the flow manager
          will not execute the local run method.

        _running : boolean
          Whether the AT is currently running (within the execute() method).
          Useful for crash recovery diagnostics.

        _plot_mode : int
          Plot mode, one of util.PlotControl plot mode (e.g., PlotControl.INTERACTIVE). Default: PlotControl.NOPLOT 

        _plot_type : int
          Plotting format, one of util.PlotControl plot type (e.g., PlotControl.PNG). Default: PlotControl.NONE

        _valid_bdp_in : List
          List of tuples indicating what types and how many BDPs_ are
          expected as input.

        _valid_bdp_out : List
          List of tuples indicating what types and how many BDPs_ are
          expected as output.

        _needToSave : boolean
          Whether this AT and underlying BDPs need to be saved to disk.

        _variflow : bool
          Whether sub-flows attached to the instance should be automatically
          cloned in the case of variadic output.


        See Also
        --------
        isAutoAlias

        Notes
        -----
        As a general rule the attributes of an AT should not be directly
        manipulated by the code in an AT---all are taken care of internally
        or accessed via methods (e.g., setkey).

        .. _BDPs: ../admit.bdp/BDP.html
    """

    def __init__(self, keys={}, keyvals={}):
        # (System) keywords and default values defined for all ATs.
        self._keys          = {"alias": '', "taskid": -1, "variflow": True}
        self._stale         = True                 # Does this AT need to be run
        self._enabled       = True                 # is this AT able to be run
        self._running       = False                # is this AT now running
        self._plot_mode     = PlotControl.NOPLOT   # no plotting
        self._plot_type     = PlotControl.NONE     # no plotting
        self._type          = self.__class__.__name__ # what type of AT is this
        self._bdp_out       = []                   # BDP's that are produced by this AT
        self._bdp_out_map   = []                   # list of uid's of _bdp_out
        self._bdp_out_zero  = []                   # list of optional types
        self._bdp_in        = []                   # BDP's that are used as inputs for this AT
        self._bdp_in_map    = []                   # list of uid's of _bdp_in
        self._valid_bdp_in  = []                   # the listing of valid input BDP types
        self._valid_bdp_out = []                   # the listing of valid output BDP types
        self._link          = 0                    # link counter
        self._loglevel      = logging.getEffectiveLevel()
        self._loggername    = ""

        # Set the initial values for the keywords.
        self._keys.update(keys)

        # Task alias.
        if keyvals.has_key('alias'):
            self._keys['alias'] = keyvals.pop('alias')
        self._alias = self._keys.pop('alias')

        # Task ID.
        if keyvals.has_key('taskid'):
            self._keys['taskid'] = keyvals.pop('taskid')
        self._taskid = self._keys.pop('taskid')

        # Variflow support.
        if keyvals.has_key('variflow'):
            self._keys['variflow'] = keyvals.pop('variflow')
        self._variflow = self._keys.pop('variflow')

        # Set any values for the keywords that were given at instantiation.
        self.setkey(keyvals)

        self._version = "0.0.0"                    # the version data
        self._needToSave = False                   # do we need to save this AT to disk

        #  it's ok to leave this off (since we don't need to write it to the XML files)
        #  but upon reading the parser doesn't grab it from Admit, so that needs to be fixed
        self._baseDir = "NONE"                       # addtask() will set this


    def __len__(self):
        """Return the current number of registered BDP_OUTs.

           Parameters
           ----------
           None

           Returns
           -------
           int
               Length of the _bdp_out list.
        """
        return len(self._bdp_out)

    def __contains__(self, index):
        """BDP outputs membership operator.

           Parameters
           ----------
           index : int
               BDP output index.

           Returns
           -------
           bool
               Membership result.
        """
        return self._bdp_out.__contains__(index)

    def __iter__(self):
        """BDP outputs iterator.

           Returns
           -------
           iterator
               BDP iterator.
        """
        return iter(self._bdp_out)

    def __getitem__(self, index):
        """Return an indexed _bdp_OUT:  AT._bdp_out[index].

           Parameters
           ----------
           index : int
               Index of the BDP to return.

           Returns
           -------
           BDP
               The BDP located at index.
        """
        if index >= len(self._bdp_out):
            msg = "AT::%d has bdp len %d, %d  %d" % (self._taskid, len(self._bdp_in), len(self._bdp_out), index)
            raise Exception(msg)
        return self._bdp_out[index]

    def __setitem__(self, index, bdp):
        """Sets (replaces) BDP output.

           Parameters
           ----------
           index : int
               BDP output index.

           bdp : BDP
               BDP reference.

           Returns
           -------
           None
        """
        self._bdp_out[index] = bdp

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + "\nAT :" + bt.format.END + bt.format.BOLD + self._type + bt.format.END
        for i, j in self.__dict__.iteritems():
            if isinstance(j, BDP):
                print str(j)
                continue
            print bt.format.BOLD + i + ": " + bt.format.END + str(j)
        for bdp in self._bdp_out:
            print bdp
        return "\n"

    def isAutoAlias(self, withEmpty=True, compat=None):
        """
        Whether the task alias appears to be auto-generated.

        The form of auto-generated aliases is a string ending in '@' followed
        by a decimal integer. Users should avoid defining aliases which look
        like ADMIT-generated aliases as they may be reset automatically, but
        are not actively prevented from doing so.

        Parameters
        ----------
        withEmpty : bool, optional
            Whether an empty alias is considered auto-generated.

        compat : str, optional
            An alias name to test for compatibility. If not ``None``, the alias
            stem (with its '@N' removed) must match the stem for `compat` for 
            this method to return ``True``.

        Returns
        -------
        bool
            Whether the task alias was auto-generated (or, optionally, empty)
            and compatible with `compat` (if specified).

        Notes
        -----
        It does not affect the result whether `compat` itself is an
        auto-generated alias; e.g., 'foo' and 'foo@1' are equivalent arguments.
        """
        if compat:
          at = compat.rfind('@')
          if at != -1 and compat[at+1:].isdigit(): compat = compat[:at]

        alias = self._alias
        if withEmpty and not alias and not compat: return True

        at = alias.rfind('@')
        return at != -1 and alias[at+1:].isdigit() and \
               (compat is None or alias[:at] == compat)

    def setloggername(self, name):
        """ Method to set the name of the logger for this AT instance

            Parameters
            ----------
            name : str
                The name of the logger for this AT

            Returns
            -------
            None

        """
        self._loggername = name

    def getloggername(self):
        """ Method to get the name of the logger for this AT instance

            Parameters
            ----------
            None

            Returns
            -------
            String containing the name of the logger.

        """
        return self._loggername

    def setlogginglevel(self, level):
        """ Method to set the logging level

            Parameters
            ----------
            level : int
                The logging level to use

            Returns
            -------
            None

        """
        if not isinstance(level, int):
            logging.error("Only integers can be given for log levels")
            return
        self._loglevel = level

    def get(self, attrib):
        """ Method to get the given attributes value

            Parameters
            ----------
            attrib : str
                The name of the attribute to get

            Returns
            -------
            varies, depends on the type of the attribute
            The value of the attribute, or None is it does not exist

        """
        return getattr(self, attrib, None)

    def set(self, item, val):
        """ Method to set protected attributes, rather than direct access

            Parameters
            ----------
            item : str
                The name of the variable to set

            val : varies
                The value to set the attribute to

            Returns
            -------
            None
        """
        if not hasattr(self, item):
            raise Exception("%s is not a valid key for %s." % (item, self.get("_type")))
        if type(getattr(self, item, None)) != type(val):
            raise Exception("You cannot change the data type of an AT keyword. Type for %s is %s" % (item, str(type(getattr(self, item)))))
        setattr(self, item, val)

    def getlogginglevel(self):
        """ Method to get the current logging level of the AT

            Parameters
            ----------
            None

            Returns
            -------
            int, the current logging level

        """
        return self._loglevel

    def geteffectivelevel(self):
        """ Method to get the effective logging level of the logging subsystem

            Parameters
            ----------
            None

            Returns
            -------
            int, the effective logging level
        """
        return logging.getEffectiveLevel()

    def seteffectivelevel(self, level):
        """ Method to set the effective logging level of the logging subsystem

            Parameters
            ----------
            level : int
                The logging level to use

            Returns
            -------
            None

        """
        logging.setLevel(level)

    def len2(self):
        """Returns the length of _bdp_in and _bdp_out in a tuple.

           If you just want the _bdp_out, the intrinsic len(my_at)
           Thus my_at.len2()[1] is the same as len(my_at).

           Returns
           -------
           Tuple
                Tuple contains 2 values, the length of _bdp_in and _bdp_out
        """
        return (len(self._bdp_in), len(self._bdp_out))

    def baseDir(self, path=None):
        """ Get/set project base directory.

            Unless empty, the base directory is guaranteed to end in os.sep.

            Parameters
            ----------
            path : str, optional
                New project base directory (ignored if None).

            Returns
            -------
            Updated project base directory.
        """
        if path is not None:
            if path and path[-1] != os.sep:
                path += os.sep
            self._baseDir = path
        return self._baseDir

    def reset(self, a):
        """ Performs an *in-place* shallow copy.

            Parameters
            ----------
            a : ADMIT Task
                Task reference to copy from.

            Returns
            -------
            None
        """
        self.__dict__ = a.__dict__.copy()

    def enabled(self, state=None):
        """Returns current task enabled setting, with optional reset.

           Parameters
           ----------
           state : bool, optional
               New value of enabled flag (default `None` keeps current value).

           Returns
           -------
           bool
               Whether task is enabled (prior to applying `state`, if provided).
        """
        enabled = self._enabled
        if state is not None:
            self._enabled = True if state else False
        return enabled

    def running(self, state=None):
        """Returns current task execution flag, with optional reset.

           Parameters
           ----------
           state : bool, optional
               New value of enabled flag (default `None` keeps current value).

           Returns
           -------
           bool
               Whether task is currently being executed (prior to applying
               `state`, if provided).
        """
        running = self._running
        if state is not None:
            self._running = True if state else False
        return running

    def markUpToDate(self):
        # why can't we call this setStale(False) so that we can grep a little easier
        """Resets _stale to indicate that the AT does not need to be run.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        self._stale = False
        for i,bdp in zip(range(len(self._bdp_out)),self._bdp_out):
            if bdp is not None:
                logging.info("BDP_OUT[%d] = %s %s" % (i,str(bdp._type),bdp.xmlFile))
            else:
                # probably never should happen?
                logging.info("BDP_OUT[%d] not connected" % i)
        

    def markChanged(self):
        # why can't we call this setStale(True) so that we can grep a little easier
        """Mark an AT that it's state was changed, so it would need to be
           rerun. The FlowManager will take care of any dependants that
           will need to be marked as well.
           Use "markUpToDate" if you want the opposite function.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        self._stale = True

    def isstale(self):
        """Returns whether the AT is out of date.

           Parameters
           ----------
           None

           Returns
           -------
           boolean
               True if the AT is out of date, else False.
        """
        return self._stale

    def id(self, strip=False):
        """Returns task ID number.

           Parameters
           ----------
           strip : bool, optional
               Whether to strip project ID (if any) from returned value
               (default: False).

           Returns
           -------
           int
               Task ID number.

           Notes
           -----
           Raises an exception if no ID assigned (freshly constructed tasks do
           not have an ID, it is set when the task is added to a project).
        """
        if self._taskid < 0:
          raise Exception("Task %s - '%s' has no task ID; "
                          "it must be added to a project first." %
                          (self._type, str(self._alias)))

        return self._taskid if not strip else self._taskid & 0xffffffff

    def link(self):
        """Increments the task link count.

           Returns
           -------
           None
        """
        self._link += 1

    def unlink(self):
        """Decrements the task link count.

           Returns
           -------
           None
        """
        if self._link != 0:
            self._link -= 1

    def setProject(self, pid):
        """
        Adds a project ID to task ID.

        Multiflows involve adding tasks belonging to other projects into a
        single flow, the multiflow. To prevent task ID collisions, tasks
        in multiflows embed a project number into the task ID.

        This method performs the actual embedding operation. The project ID
        is inserted beginning at bit 32 and replaces any previous project ID.
        Since Python integers are automatically multi-precision there is never
        danger of truncation of the project ID.

        Parameters
        ----------
        pid : int
            Project ID number.

        Returns
        -------
        None

        See Also
        --------
        getProject
        """
        self._taskid = (pid << 32) + (self._taskid & 0xffffffff)

    def getProject(self):
        """
        Retrieves project ID associated with the task.

        Multiflows involve adding tasks belonging to other projects into a
        single flow, the multiflow. To prevent task ID collisions, tasks
        in multiflows embed a project number into the task ID.

        This method returns the project ID attached to the task. This will be
        zero unless setProject() has been called---normally only by the
        ProjectManager when a project is added for use in a multiflow.

        Returns
        -------
        int
            Task project ID.

        See Also
        --------
        setProject

        Notes
        -----
        Project IDs are local to each multiflow. Hence the same task, linked in
        two independent multiflows, may have a different project ID in each.
        This has no effect on the task in its parent flow (for which this
        method will return zero).
        """
        return 0 if self._taskid < 0 else self._taskid >> 32


    def show(self):
        """Return the AT type.

           Parameters
           ----------
           None

           Returns
           -------
           string
               The type of the AT.
        """
        return self._type

    def dir(self, filename=None):
        """Absolute directory reference of the ADMIT project.

           Returns the absolute directory name of this ADMIT project
           or a derefenced filename address. Normally you will need
           such an absolute file or directory name when non-ADMIT tools
           are needed for I/O.  Also note that this project
           directory is guarenteed to end with the operating dependent
           directory separator (usually '/'). This way filenames can be constructed
           as follows:  **Admit.dir() + 'foobar.dat'**  or more conveniently
           **Admit.dir('foobar.dat')**

           Parameters
           ----------

           filename : string, optional
               Filename to be appended to the absolute directory name.
               This can include additional subdirectories.

           Returns
           -------
           string
               The directory name within which all ADMIT files reside.
        """
        if self._baseDir == "NONE":
            raise Exception("AT._baseDir was not initialized")
        if filename is None:
            return self._baseDir
        # note that self._baseDir is guaranteed to end in os.sep (unless "")
        return self._baseDir + filename

    def mkext(self, filename, ext, alias=""):
        """Return a new filename with a new extension with optional ADMIT alias.

           This will either append an extension to a (file)name
           without an extension, or replace one.  If an alias was set by
           this task, the alias will replace the alias found in
           the basename dash.

           You can also provide a local alias, instead of using the task
           alias.

           Examples:
                       ("x"  , "z"    )               -> "x.z"
                       ("x.y", "z"    )               -> "x.z"
                       ("x.y", "z", "a")              -> "x-a.z" 
        """
        # caveat:  does not work if the directory part has a . and the file does not
        #          e.g.  "a.dir/b/c"   would give   "a.ext" and that's very wrong
        loc = filename.rfind('.')
        if loc < 0:
            base = filename
        else:
            base = filename[:loc]
        # done
        if not alias:
            alias = self._alias
        if not alias:
            return "%s.%s" % (base, ext)
        else:
            # we have a new alias ; first check if base had an old alias
            loc1 = base.rfind('.')
            loc2 = base.rfind('-')
            if loc1 < 0:
                # no dot
                if loc2 < 0:
                    # no old alias
                    return "%s-%s.%s" % (base, alias, ext)
                else:
                    # replace alias
                    return "%s-%s.%s" % (base[:loc2], alias, ext)
            else:
                # dot
                if loc2 < loc1:
                    # dash was too early, no replace needed
                    return "%s-%s.%s" % (base, alias, ext)
                else:
                    # replace alias
                    return "%s-%s.%s" % (base[:loc2], alias, ext)
            # should never come here
            raise Exception,"mkext: no code path here"

    def mkdir(self, dirname):
        """Make a directory in the ADMIT hierarchy.
           Checks whether the directory already exists.
           It also allows an absolute path, in the classical UNIX sense, but
           this is normally not needed.

           Parameters
           ----------
           dirname : str
               Directory name.

           Notes
           -----
           .. todo:: this routine is identical to the one in Admit()
        """
        if dirname[0] == os.sep:
            # it's already an absolute path
            dname = dirname
        else:
            # make it relative to the admit
            dname = os.path.abspath(self._baseDir + dirname)

        if not os.path.exists(dname):
            try:
                os.makedirs(dname)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(dname):
                    pass
                else: raise
            # print "AT.mkdir: ", dname

    def summary(self):
        """Returns the summary dictionary from the AT, for merging
           into the ADMIT Summary object.   Derived classes should
           override this if they provide summary data.
        """
#        print "***********AT BASE CLASS summary()***********"
        return {}

    def userdata(self):
        """Returns the user dictionary from the AT, for merging
           into the ADMIT userdata object.   Derived classes should
           override this if they provide user data.
        """
        return {}

    def freeAlias(self, aliases, alias = None):
        """
        Deletes alias reservation, if present.

        Parameters
        ----------
        aliases : 2-tuple of dict of str to set of str 
            Reserved alias registry, keyed by alias base name (index 0) or AT
            type (index 1). For index 0, the value is the set of aliases
            created with that base name; for index 1, it is the set of default
            aliases created for ATs of that type. In both cases, the duplicate
            aliases are appended with '@N' for some integer N.

        alias : str, optional
            Alias name to release; default ``None`` means use the current AT's
            alias.

        Returns
        -------
        None
        """
        if alias is None: alias = self._alias
        if alias is not None:
          # Strip auto-generated suffix (if any) from name.
          at = alias.rfind('@')
          stem = alias[:at] if at != -1 and alias[at+1:].isdigit() else alias
          index, key = (0, stem) if stem != '' else (1, self._type)
          if key in aliases[index]:
            aliases[index][key].discard(alias)
            if not aliases[index][key]:
              del aliases[index][key]


    def setAlias(self, aliases, alias=None, auto=False):
        """ 
        Sets and registers the task alias, guaranteed unique among 
        registered aliases.

        Checks whether the input `alias` is already in use. If so, raises
        an exception unless the name appears auto-generated (or is empty), in
        which case the aliases is updated to ensure uniqueness. The latter are
        names appended with a string of the form '@N', where N is some decimal
        integer value. Resets the task alias name to the final result.

        Normally users should *not* call this function directly; user-defined
        aliases should be set via the AT constructor argument instead.

        Parameters
        ----------
        aliases : 2-tuple of dict of str to set of str 
            Reserved alias registry, keyed by alias base name (index 0) or AT
            type (index 1). For index 0, the value is the set of aliases
            created with that base name; for index 1, it is the set of default
            aliases created for ATs of that type. In both cases, the duplicate
            aliases are appended with '@N' for some integer N.

        alias : str, optional
            The (suggested) task alias name; default ``None`` uses
            the current `_alias` value.

        auto : bool, optional
            Whether to automatically append a unique '@N' suffix if the alias
            is already in use; otherwise, an exception will be raised (unless
            the alias already ends in '@N', which implies `auto` = ``True``).

        Returns
        -------
        str
            The assigned alias name.

        Notes
        -----
        Performs an iterative search for the first available name following the
        (estimated) final assigned alias for the AT of the given type.

        Users may specify an alias of the form 'foo@0' to indicate that a
        sequence of aliases 'foo@0', 'foo@1', ... be auto-generated as
        necessary. This can be useful in scripts where tasks are generated in
        loops and a predictable series of aliases is desired.
        """
        if alias is None:
          # In principle None could be treated separately from '', but isn't.
          alias = '' if self._alias is None else self._alias

        # Strip auto-generated suffix (if any) from name.
        at = alias.rfind('@')
        if at != -1 and alias[at+1:].isdigit():
          stem = alias[:at]
          count0 = int(alias[at+1:])
        else:
          stem = alias
          count0 = -1

        # Update the appropriate alias set.
        index, key = (0, stem) if stem != '' else (1, self._type)
        if key in aliases[index]:
          if alias and alias == stem and not auto:
            raise Exception("Explicit alias '%s' is already in use, "
                            "must be unique." % alias)
          else:
            # Find unused alias.
            used = aliases[index][key]
            count = len(used)
            while alias in used:
              alias = stem+'@'+str(count)
              count += 1
            used.add(alias)
        else:
          if not count0: alias = stem+'@0'
          aliases[index][key] = set([alias])

        self._alias = alias
        return alias

    def setkey(self, name="", value="", isinit=False):
        """
            Set keyword value.

            Two styles are possible:

            1. name = {key:val}            e.g. **setkey({"a":1})**

            2. name = "key", value = val     e.g. **setkey("a", 1)**

            This method checks the type of the keyword value, as it must
            remain the same. Also new keywords cannot be added.

            Parameters
            ----------

            name : dictionary or string, optional
                Dictionary of keyword value pairs, or a string containing
                a single key name; defaults to empty string.

            value : any, optional
                The (string) keyword value; defaults to empty string.

            isinit : bool
                Whether keyword is being set for the first time.

            Returns
            -------
            None
        """
        change = False
        # if we are given a dictionary then go through each entry
        if isinstance(name, dict):
            # check that the keys are valid first and that the data type is not changing
            for key in name:
                if not self.haskey(key):
                    raise Exception("%s is not a valid key for %s." % (key, self._type))
                if type(self._keys[key]) != type(name[key]):
                    if isinstance(self._keys[key], float) and isinstance(name[key], int):
                        name[key] = float(name[key])
                    else:
                        raise Exception("You cannot change the data type of an AT keyword. Type for %s is %s (expected %s)" % (key, str(type(name[key])), str(type(self._keys[key]))))
                if name[key] != self.getkey(key):
                    self._keys[key] = name[key]
                    change = True
        # if we were given a string
        elif not name == "":
            #2
            # check that the key is valid and not changing data type
            if not self.haskey(name):
                print "valid keys: ", self._keys
                raise Exception("%s is not a valid key for %s." % (name, self._type))
            if type(self._keys[name]) != type(value):
                if isinstance(self._keys[name], float) and isinstance(value, int):
                    value = float(value)
                else:
                    raise Exception("You cannot change the data type of an AT keyword. Type for %s is %s (expected %s)" % (name, str(type(value)), str(type(self._keys[name]))))
            if value != self.getkey(name):
                self._keys[name] = value
                change = True
        else:
            raise Exception("Invalid name parameter given, it must be a string or a dictionary of keys:values.")
        if change and not isinit:
            if isinstance(name,str):
              logging.info("Setting '%s' = %s for %s" %
                           (name, str(value), self._type))
            else:
              logging.info("Setting %s for %s" % (str(name), self._type))
            self.markChanged()

    def getkey(self, key):
        """Retrieval value for a key. If the key had not been set yet, 
           a default value can be returned, else None is returned.
           Notice no type checking has been done here, the caller is
           responsible for this.

           Parameters
           ----------
           key : string
              The key whose value is to be returned.

           Returns
           -------
           The value of the key.

           See also
           --------
           haskey
        """
        if self.haskey(key):
            return self._keys[key]
        raise Exception("Key %s does not exist in this AT (%s)" % (key, self._type))

    def haskey(self, key):
        """Query if a key exists for an AT.

           Parameters
           ----------
           key : string
               The key to check for existence.

           Returns
           -------
           Boolean
               True if the key exists, False otherwise.
        """
        return key in self._keys

    def checktype(self, item):
        """Check the type of an object to see if it is a BDP.

            Parameters
            ----------
            item : Any
                The item to check.

            Returns
            -------
            Boolean
                True if the item is a BDP, False otherwise.

        """
        if isinstance(item, BDP):
            return
        raise Exception("Item is not a BDP")

    def addoutput(self, item, slot=-1):
        """ Add a BDP output product to an AT. The BDP type will be validated
            before it is added to the output list.

            Parameters
            ----------
            item : BDP
                The BDP to be added to the output list.

            slot : int, optional
                The slot in the BDP to add it to. The BDP type must match the expected type for the slot.
                Default: -1 (i.e. insert into the first available slot)

            Returns
            -------
            None
        """
        # Set base directory.
        item.baseDir(self.baseDir())

        # check that it is a valid bdp output type for this AT
        self.checktype(item)
        found = False
        for bdp in self._valid_bdp_out:
            if isinstance(item, bdp[0]):
                found = True
                break
        if not found:
            raise Exception("Given BDP is not of a type specified in _valid_bdp_out.")
        found = False
        # If a slot was specified
        if slot > -1:
            # check if the slot is in the list
            if slot >= len(self._bdp_out):
                raise Exception("Specified slot does not exist")
            # if the slot is an optional BDP then check the type and replace
            if slot >= len(self._bdp_out_order_list):
                if isinstance(item, self._bdp_out[slot]):
                    self.addoutputbdp(item, slot)
                    return
                else:
                    raise Exception("You annot replace one BDP type with another in _bdp_out.")
            # if it is a required output type check the type and replace
            else:
                if isinstance(item, self._bdp_out_order_list[slot]):
                    self.addoutputbdp(item, slot)
                    return
                raise Exception("Specified slot is not of the expected BDP type.")
        # if no slot was specified then find where it belongs
        for i in range(len(self._bdp_out_order_list)):
            # if the slot is empty then insert the BDP
            if isinstance(item, self._bdp_out_order_list[i]):
                found = True
                if self._bdp_out[i] is None:
                    self.addoutputbdp(item, i)
                    return
        mark = -1
        # if it is an optional one find where it belongs
        for i in range(len(self._bdp_out_zero)):
            if isinstance(item, self._bdp_out_zero[i]):
                mark = i

        if mark == -1:
            raise Exception("No available slots for given BDP")
        # if it is the first one then just add it to the end
        if len(self._bdp_out) == self._bdp_out_length:
            self.addoutputbdp(item)
        # otherwise find its appropriate slot
        else:
            slot = len(self._bdp_out_order_list)+1
            for i in range(len(self._bdp_out_order_list), len(self._bdp_out)):
                for j in range(mark+1):
                    if isinstance(self._bdp_out[i], self._bdp_out_zero[j]):
                        slot = i + 1
            if slot >= len(self._bdp_out):
                self.addoutputbdp(item)
            else:
                self.addoutputbdp(item, slot, True)


    def addinput(self, item, slot=-1):
        """ Add a BDP input to an AT. The BDP type will be validated
            before it is added to the input list.

            Parameters
            ----------
            item : BDP
                The BDP to be added to the input list.

            slot : int, optional
                The slot in the BDP to add it to. The BDP type must match the expected type for the slot.
                Default: -1 (i.e. insert into the first available slot)

            Returns
            -------
            None
        """
        # first check that it is a valid bdp input type
        self.checktype(item)
        found = False
        for bdp in self._valid_bdp_in:
            if isinstance(item, bdp[0]):
                found = True
                break
        if not found:
            raise Exception("Given BDP is not of a type specified in _valid_bdp_in.")
        found = False
        # If a slot was specified
        if slot > -1:
            # check if the slot is in the list
            if slot >= len(self._bdp_in):
                raise Exception("Specified slot does not exist")
            # if the slot is an optional BDP then check the type and replace
            if slot >= len(self._bdp_in_order_list):
                if isinstance(item, self._bdp_in[slot]):
                    self.addinputbdp(item, slot)
                    return
                else:
                    raise Exception("You annot replace one BDP type with another in _bdp_in.")
            # if it is a required output type check the type and replace
            else:
                if isinstance(item, self._bdp_in_order_list[slot]):
                    self.addinputbdp(item, slot)
                    return
                raise Exception("In %s: Specified slot is not of the expected BDP type." % self._type)
        # if no slot was specified then find where it belongs
        for i in range(len(self._bdp_in_order_list)):
            if isinstance(item, self._bdp_in_order_list[i]):
                found = True
                if self._bdp_in[i] is None:
                    self.addinputbdp(item, i)
                    return
        mark = -1
        for i in range(len(self._bdp_in_zero)):
            if isinstance(item, self._bdp_in_zero[i]):
                mark = i

        if mark == -1:
            raise Exception("No available slots for given BDP")
        # if it is an optional one find where it belongs
        if len(self._bdp_in) == self._bdp_in_length:
            self.addinputbdp(item)
        # otherwise find its appropriate slot
        else:
            slot = len(self._bdp_in_order_list) + 1
            for i in range(len(self._bdp_in_order_list), len(self._bdp_in)):
                for j in range(mark+1):
                    if isinstance(self._bdp_in[i], self._bdp_in_zero[j]):
                        slot = i + 1
            if slot >= len(self._bdp_in):
                self.addinputbdp(item)
            else:
                self.addinputbdp(item, slot, True)
        # @todo isn't this normally called via FM.add() ?

    def addoutputbdp(self, item, slot=-1, insert=False):
        """ Add a BDP to the _bdp_out list.

            Parameters
            ----------
            item : BDP
                The BDP to add.

            slot : int, optional
                Where the BDP should be added to the list;
                default : -1

            insert : Boolean, optional
                Whether to insert into the middle of the list (not replace);
                defaults to False.

            Returns
            -------
            None

            Notes
            -----
            This method should not be called directly, use addoutput instead.
        """
        item.setkey("_taskid", self.id(True))
        if slot < 0:
            self._bdp_out.append(item)
            self._bdp_out_map.append(item.get("_uid"))
        else:
            if insert:
                self._bdp_out.insert(slot, item)
                self._bdp_out_map.insert(slot, item.get("_uid"))
            else:
                self._bdp_out[slot] = item
                self._bdp_out_map[slot] = item.get("_uid")
        if len(self._bdp_out) != len(self._bdp_out_map):
            raise Exception("Mismatch in _bdp_out size.")

    def addinputbdp(self, item, slot=-1, insert=False):
        """ Add a BDP to the _bdp_in list.

            Parameters
            ----------
            item : BDP
                The BDP to add.

            slot : int, optional
                Where the BDP should be added to the list;
                default : -1

            insert : Boolean, optional
                Whether to insert into the middle of the list (not replace);
                defaults to False.

            Returns
            -------
            None

            Notes
            -----
            This method should not be called directly, use addinput instead.
        """
        if slot < 0:
            self._bdp_in.append(item)
            self._bdp_in_map.append(item.get("_uid"))
        else:
            if insert:
                self._bdp_in.insert(slot, item)
                self._bdp_in_map.insert(slot, item.get("_uid"))
            else:
                self._bdp_in[slot] = item
                self._bdp_in_map[slot] = item.get("_uid")
        if len(self._bdp_in) != len(self._bdp_in_map):
            raise Exception("Mismatch in _bdp_out size.")

    def delinput(self, slot):
        """ Delete a specific BDP in the _bdp_in list.

            Parameters
            ----------
            slot : int
                The slot to remove the BDP from

            Returns
            -------
            None
        """
        if slot < len(self._bdp_in_order_list):
            self._bdp_in[slot].delete()
            self._bdp_in[slot] = None
            self._bdp_in_map[slot] = -1
        else:
            self._bdp_in[slot].delete()
            del self._bdp_in[slot]
            del self._bdp_in_map[slot]

    def deloutput(self, slot):
        """ Delete a specific BDP in the _bdp_out list.

            Parameters
            ----------
            slot : int
                The slot to remove the BDP from

            Returns
            -------
            None
        """
        if slot < len(self._bdp_out_order_list):
            self._bdp_out[slot].delete()
            self._bdp_out[slot] = None
            self._bdp_out_map[slot] = -1
        else:
            self._bdp_out[slot].delete()
            del self._bdp_out[slot]
            del self._bdp_out_map[slot]

    def clearinput(self):
        """ Clear the input BDP list.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        self._bdp_in = [None] * self._bdp_in_length
        self._bdp_in_map = [-1] * self._bdp_in_length

    def clearoutput(self, delete=True):
        """ Clear the output BDP list.

            Parameters
            ----------
            delete : bool
                If True then delete the output bdps.
                Default: True

            Returns
            -------
            None
        """
        if delete:
            for bdp in self._bdp_out:
                if bdp is not None:
                    bdp.delete()
                    del bdp
        self._bdp_out = [None] * self._bdp_out_length
        self._bdp_out_map = [-1] * self._bdp_out_length

    def set_bdp_out(self, bout=[]):
        """ Validate the _valid_bdp_out list and digest it into the appropriate
            attributes.

            Parameters
            ----------
            bout : list
                List containing tuples of the valid BDP outputs and their
                counts; defaults to empty list.

            Returns
            -------
            None
        """
        self._bdp_out_order_list = []     # ordered list of input types
        self._bdp_out_zero = []           # reset list of optional types
        self._bdp_out = []                # reset the _bdp_out list
        self._bdp_out_map = []            # reset the mapping
        # error check the input
        if not isinstance(bout, list):
            raise Exception("_valid_bdp_out is not in the proper form. See the dcoumentation for details.")
        haveopt = False
        # evaluate each entry
        for b in bout:
            if not isinstance(b, tuple):
                raise Exception("Entries in _valid_bdp_out are not all tuples as they must be.")
            if not issubclass(b[0], BDP):
                raise Exception("Invalid data type given in _valid_bdp_out, must be of type BDP.")
            # take care of the optional one (only one allowed)
            if b[1] == 0:
                if haveopt:
                    raise Exception("Only one type of optional output is allowed.")
                self._bdp_out_zero.append(b[0])
                haveopt = True
            # process the required ones
            else:
                # check the order
                if haveopt:
                    raise Exception("Optional outputs must be last.")
                # add an entry into the appropriate maps
                for _ in range(0, b[1]):
                    self._bdp_out.append(None)
                    self._bdp_out_order_list.append(b[0])
                    self._bdp_out_map.append(-1)
        self._bdp_out_length = len(self._bdp_out)
        self._valid_bdp_out = bout

    def set_bdp_in(self, bdpin=[]):
        """ Validate the _valid_bdp_in list and digest it into the appropriate
            attributes.

            Parameters
            ----------
            bdpin : list
                List containing tuples of the valid BDP inputs and their
                counts; defaults to empty list.

            Returns
            -------
            None
        """
        self._bdp_in_order_list = []     # ordered list of input types
        self._bdp_in_order_type = []     # ordered list of type (optional/required)
        self._bdp_in_zero = []           # list of optional types
        self._bdp_in = []                # reset the _bdp_in list
        self._bdp_in_map = []            # reset the mapping
        # error check the input
        if not isinstance(bdpin, list):
            raise Exception("_valid_bdp_in is not in the proper form. See the dcoumentation for details.")
        haveopt = False
        havezero = False
        # evaluate each entry
        for b in bdpin:
            if not isinstance(b, tuple):
                raise Exception("Entries in _valid_bdp_out are not all tuples as they must be.")
            if not issubclass(b[0], BDP):
                raise Exception("Invalid data type given in _valid_bdp_in, must be of type BDP.")
           # take care of the optional ones
            if b[2] == bt.OPTIONAL:
                haveopt = True
            # process the non-open ended ones
            if b[1] != 0:
                if havezero:
                    raise Exception("Improper order in _valid_bdp_in see documentation.")
                if b[2] == bt.REQUIRED and haveopt:
                    raise Exception("Improper order in _valid_bdp_in see documentation.")
                for _ in range(0, b[1]):
                    self._bdp_in.append(None)
                    self._bdp_in_order_list.append(b[0])
                    self._bdp_in_order_type.append(b[2])
                    self._bdp_in_map.append(-1)
            # take care of open ended ones
            else:
                havezero = True
                self._bdp_in_zero.append(b[0])
        self._bdp_in_length = len(self._bdp_in)
        self._valid_bdp_in = bdpin

    def getVersion(self):
        """ Return the version string.

            Parameters
            ----------
            None

            Returns
            -------
            String
                The version of the AT
        """
        return self._version

    def getdtd(self, fl):
        """ Method to write out the dtd data.

            Parameters
            ----------
            fl : file handle
                Open output file handle.

            Returns
            -------
            None

        """
        dtdRead = DtdReader(self._type + ".dtd")
        dtd = dtdRead.getDtd()
        for line in dtd:
            fl.write(line)

    def html(self, inheader):
        """ Method to represent the current AT in HTML format.

            Parameters
            ----------
            inheader : str
                Base header info for the html output

            Returns
            -------
            An html representation of the AT

        """
        SPANXVAL = '<div class="span%s">%s</div><!-- spanx -->'
        ENDROW = '</div><!-- row-fluid --> \n'
        STARTROW ='<div class="row-fluid">'
        outdir = self.dir()
        basedir = os.path.basename(outdir.rstrip(os.sep))
        if inheader == None:
            admitloc = utils.admit_root()
            admitetc = admitloc + os.sep + "etc"
            admitfile = admitetc + os.sep + "form_at.html"
            try:
                with open(admitfile,"r") as h:
                    header = h.read() 
            except:
                return "<h4> ***** failed to open %s ***** </h4>"% admitfile
        else:
            header = inheader

        h = '<!-- ##### BEGIN FORM DATA FOR %s ##### -->\n' % self._type
        num_bdp_in = len(self._bdp_in)
        num_bdp_out = len(self._bdp_out)
        h = h+'<h5><u>Input BDPs</u></h5>'
        tabstr = '<table width="80%" class="table table-admit table-bordered table-striped"><tbody><tr><th>Index</th><th>Type</th><th>File name</th></tr>'
        if num_bdp_in > 0:
            h = h+tabstr
        else:
            h = h + "None"
        for i in range(len(self._bdp_in)):
            if self._bdp_in[i] != None:
                 href = '<a href="http://admit.astro.umd.edu/admit/module/admit.bdp/%s.html">%s</a>' % (self._bdp_in[i]._type, self._bdp_in[i]._type)
                 h = h+"<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (i,href,self._bdp_in[i].xmlFile)
            else:
                 h = h+"<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (i,"None","None")
            
        h = h + '</tbody></table>'
        h = h+'<h5><u>Output BDPs</u></h5>'
        if num_bdp_out > 0:
            h = h+tabstr
        else:
            h = h + "None"
        for i in range(len(self._bdp_out)):
            if self._bdp_out[i] != None:
                 href = '<a href="http://admit.astro.umd.edu/admit/module/admit.bdp/%s.html">%s</a>' % (self._bdp_out[i]._type, self._bdp_out[i]._type)
                 h = h+"<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (i,href,self._bdp_out[i].xmlFile)
            else:
                 h = h+"<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (i,"None","None")
        h = h + '</tbody></table>'

        h = h+'<h5><u>Keywords</u></h5>'

        # squirrel away the task ID and task name for reference. the callback
        # method will use these.
        inp = '\n<!-- ********** Task ID and Task Name  ********** -->\n <input class="input-admitform"  type="hidden" value="%d" name="task[][taskid]"><br>\n' % self._taskid
        h = h + inp
        inp = '<input class="input-admitform"  type="hidden" value="%s" name="task[][taskname]"><br>\n<!-- *********** Task Keywords *********** -->' % self._type
        h = h + inp

        for k in self._keys:
           h = h + STARTROW
           l = '<label class="label-admitform">%s</label>' % k
           h = h + (SPANXVAL % ('2',l))
           # If the type is not string, use repr() to get the value.  This is because simply using
           # %s can cause floating point numbers to be truncated, which AT.setkey() later interprets as
           # a changed value causing a task to be re-run when it shouldn't be.  Why not use repr() on strings, too?
           # Because that causes the quotes to be transmitted in the json to the web form, which we 
           # don't want: It forces users to type quotes on string inputs (which Pedantic Python Peter prefers),
           # but complicates parsing on input in Admit.py _onpost().   You'd think ast.literal_eval would
           # solve this (see comments in _onpost()), but in fact it does not completely and there are
           # still downstream failures.   I do not wish to force our users to type quotes around string
           # inputs in the web form, nor do I wish to chase this parsing rabbit down the hole. 
           # mwp 2016-aug-23
           if type(self._keys[k]) == str:
               inp = '<input class="input-admitform"  type="text" value="%s" name="task[][%s]"><br>\n' % (self._keys[k],k)
           else:
               inp = '<input class="input-admitform"  type="text" value="%s" name="task[][%s]"><br>\n' % (repr(self._keys[k]),k)
           h = h + (SPANXVAL % ('6',inp))
           h = h + ENDROW
           
        h = h + '<!-- ##### END FORM DATA FOR %s ##### -->\n' % self._type
        if self.running():  
          taskclass = "crashed-admittask" 
        elif self.enabled():
          taskclass = "stale-admittask-form" if self.isstale() else "label-admittask-form"
        else:
          taskclass = "disabled-admittask-form" 

        retval = header % (taskclass, self._taskid, self.statusicons(), self._type,self._taskid,self._taskid,self._type, self._type, self._type, h , self._taskid)
        return retval

    #@todo move this to an htmlutils module
    def statusicons(self):
        """return some html icons representing the enabled/stale status of this task"""
        if not self._stale and self._enabled:
           iconhtml = '<i class="icon-ok"></i>'
           return iconhtml

        iconhtml = ''
        if self._stale:
           iconhtml += '<i class="icon-warning-sign"></i>'
        if not self._enabled:
           iconhtml += '<i class="icon-ban-circle"></i>'
        # If running() is true at the time statusicons() is called, the AT
        # must have crashed.
        if self.running():
           iconhtml += '<i class="icon-fire"></i>'
       
        return iconhtml


    def write(self, node):
        """ Method to write the AT to disk.

            Parameters
            ----------
            node : elementtree node
                The node to attach to (usually supplied by flowmanager)

            Returns
            -------
            node : elementtree node
                The modified node

            dtd : Text string of the dtd
        """
        root = et.SubElement(node, self._type)
        root.set("type", bt.AT)
        dtdRead = DtdReader(self._type + ".dtd")
        order = dtdRead.getOrder()
        dtd = dtdRead.getDtd()
        typs = dtdRead.getTypes()
        kys = dtdRead.getKeys()

        # call the writer
        XmlWriter.XmlWriter(self, order, typs, root, kys)

        # tell each BDP output to write also
        self.save()

        return node, dtd

    def save(self):
        """ Save (write) any BDPs connected to this AT.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        if not self._needToSave:
            return
        for i in self._bdp_out:
            if i is not None:
                #print self.dir(i.xmlFile)
                i.write(self.dir(i.xmlFile))
        self._needToSave = False

    def validatekeys(self):
        """ Method to error check all input keys. If an error is found an error message should be
            issued, not an exception. This allows for all values to be error checked before an
            ecpetion is raised. This method should return a bool where True means all key values
            are ok, and False otherwise. An exception will be raised by validatekeyvalues, which
            calls this method, if False is returned. The generic form of this method does not check
            anything, but should be overridden in individual AT's that need to check key values.

            Parameters
            ----------
            None

            Returns
            -------
            bool, True if all key values are ok, False otherwise.

        """
        return True

    def dryrun(self):
        """ Method to do a dry run of the AT, generally just checks input values for errors.

            Parameters
            ----------
            None

            Returns
            -------
            bool, True if all is ok, False otherwise

        """
        try:
           self.validatekeys()
        except:
            return False
        return True

    def run(self):
        """Runs the task.

           Running a task transforms its input BDPs into output BDPs according
           to its function. Following this call the output BDPs accurately
           reflect the current state of the task (keywords and BDP inputs).
           Each concrete AT must implement its own **run()** method.

           Returns
           -------
           None

           See Also
           --------
           execute
        """
        return

    def execute(self, args=None):
        """ Executes the task.

            Execution performs the following actions:
            0. Mark task running.
            1. Update BDP inputs (if `args` is given).
            2. Validate task keywords.
            3. Validate task BDP inputs.
            4. Call task `run()`_.
            5. Mark task up to date.
            6. Mark persistent BDP outputs out of date.
            7. Disable running attribute.

            Parameters
            ----------
               args : list of BDPs, optional
                   List of BDP inputs used by `run()`_ method; default is to use
                   the most recently supplied inputs.

            Returns
            -------
            None

            See Also
            --------
            run

            Notes
            -----
            If `args` is not given, the previously cached BDP inputs
            are reused; hence execution (input validation) will fail
            if required arguments are absent.

            .. _run(): #admit.AT.AT.run
        """
        self._running = True
        logging.heading("Executing %s - '%s' (V%s)" %
                        (self._type, self._alias, self._version))
        logging.reportKeywords(self._keys)

        temploglevel = self.geteffectivelevel()
        self.seteffectivelevel(self._loglevel)

        if args: # self._bdp_in = args
            self.clearinput()
            for a in args:
                self.addinput(a)


        self.validatekeys()
        validated, details = self.validateinput(True)
        if not validated:
            raise Exception("Inputs not validated: %s" % details)
        # @todo   review this if need, currently we clear (delete) all BDPs prior to running
        self.clearoutput()
        self.run()
        self.markUpToDate()
        self._needToSave = True
        self.seteffectivelevel(temploglevel)
        self._running = False

    def checkfiles(self):
        """ Check if the files from all the BDP_out's in an AT exist.
            Return the list of files not found.

            Parameters
            ----------
            None

            Returns
            -------
            None

            Notes
            -----
            In multiflows, BDPs for ATs linked from other projects 
            (distinguished by a non-zero value of getProject()) are 
            *not* (re)checked for existence; this occurs when the parent
            project is read.
        """
        # Skip ATs linked into multiflows.
        if self.getProject():
            return None

        if not self._enabled or self._stale:
            return None
        files = []
        for bdp in self._bdp_out:
            if bdp is None:
                raise Exception("Missing BDP output files(s) from %s" % (self._type))
            files += bdp.getfiles()

        for fl in files:
            #print "CHECKFILES: ", fl, self.dir(fl)
            if fl is None:
                continue
            if not os.path.exists(self.dir(fl)):
                self.markChanged()
                logging.warning("AT.checkfiles():: File not found: " + fl)
                return files

    def delete(self):
        """Method to delete the AT and underlying BDPs.

            It is recommended that any AT that stores images inside of lists, 
            dictionaries, tuples, etc. override this method with a customized
            version.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        for bdp in self_bdp_out:
          if bdp is not None:
              bdp.delete()
              del bdp


    def copy(self):
        """ Creates an independent duplicate of the task.

            The task ID of the duplicate will be unset and the alias marked
            to allow auto-updating.

            Parameters
            ----------
            aliases : dict of set of str
                Reserved alias registry.

            Returns
            -------
            Reference to the new (cloned) task.

            Notes
            -----
            The current implementation performs a deepcopy() and updates a few
            members.
        """
        a = copy.deepcopy(self)
        if not a.isAutoAlias(): a._alias += '@1'
        a._taskid = None
        a.clearinput()
        a.clearoutput(False)
        a.markChanged()
        return a

    def validateinput(self, describe=False):
        """
            Method to validate the _bdp_in's against a dictionary of expected
            types.

            Parameters
            ----------
            describe : bool, optional
                Whether to include a list of what was found (or not) in the
                return value (as the second item in a tuple).

            Returns
            -------
            bool
                False if anything is amiss, else True.
        """
        valid = True
        results = []
        for i in range(len(self._bdp_in_order_list)):
            state = bt.FOUND
            if self._bdp_in[i] is None:
                if self._bdp_in_order_type[i] == bt.REQUIRED:
                    valid = False
                state = bt.MISSING
            results.append([self._bdp_in_order_list[i], self._bdp_in_order_type[i], state])
        for i in range(len(self._bdp_in_order_list), len(self._bdp_in)):
            results.append([self._bdp_in[i], bt.OPTIONAL, bt.FOUND])
        if describe:
            return valid, results
        return valid

    def isequal(self, at):
        """Method to determine if two ATs are the same. Useful for testing.

            Parameters
            ----------
            at : AT
                The AT to compare against

            Returns
            -------
            Boolean
                Whether or not the ATs are equal

        """
        try:
            if at.get("_type") != self.get("_type"):
                logging.info("AT types are not the same: " + at.get("_type") + " vs " +self.get("_type"))
                return False
            for i in self.__dict__:
                if i == "_keys" or i == "_bdp_out" or i == "_bdp_in":
                    continue
                if cmp(getattr(self, i), getattr(at, i)) != 0:
                    logging.info("Attribute %s does not match" % (i))
                    return False
            for i in self._keys:
                if cmp(self.getkey(i), at.getkey(i)) != 0:
                    logging.info("Keyword %s does not match" % (i))
                    return False
        except:
            return False
        return True


    def merge(self, at, aliases=None):
        """
        Merges attributes from another task.

        The purpose of this method is to facilitate re-running of flows by
        transferring select attributes from one task to a compatible
        replacement task. To maintain transparency, attributes are overwritten
        only where necessary to preserve flow integrity; in particular, items
        such as keyword values and the task ID are never modified.

        Parameters
        ----------
        at : ADMIT task
            Task to merge with `self`.

        aliases : 2-tuple of dict of str to set of str 
            Reserved alias registry, keyed by alias base name (index 0) or AT
            type (index 1). For index 0, the value is the set of aliases
            created with that base name; for index 1, it is the set of default
            aliases created for ATs of that type. In both cases, the duplicate
            aliases are appended with '@N' for some integer N.

        Returns
        -------
        None

        Notes
        -----
        It is the caller's responsibility to set the alias as desired. Doing so
        locally (here) may result in unnecessary reassignments, causing tasks
        which are otherwise unaltered to be marked stale.

        The task enabled/disabled status is always copied from the input task.
        This is necessary for variflow maintenance but applied uniformly for
        simplicity.
        """
        if self._type != at._type:
          raise Exception("Task type mismatch: %s / %s" % \
                          (self._type, at._type))

        if self.getProject() != at.getProject():
          raise Exception("Task project mismatch: %d / %d" % \
                          (self.getProject(), at.getProject()))

        # Outputs may be stale, but they're the latest available.
        self.clearoutput(False)
        if at:
          for bdp in at:
            if bdp is not None:
              self.addoutput(bdp)
            else:
              at.markChanged()
              logging.warning("Null output BDP encountered merging "
                              "%s - '%s'; task will be marked stale" %
                              (at._type, at._alias))
          self._needToSave = True
          self.save()

        if self._keys == at._keys and self._variflow == at._variflow and \
           (self.isAutoAlias(compat=at._alias) or self._alias == at._alias):
          self._stale = at._stale
        else:
          self._stale = True

        self.enabled(at.enabled())

        self._summary = at.summary()
        for key in self._summary: self._summary[key].setTaskID(self.id(True))

        # Correct double counting of linked tasks. 
        if self.getProject(): self.unlink()


    def newId(self, tid):
        """
        Assigns the task a new ID number.

        Related attributes are updated accordingly.

        Parameters
        ----------
        tid : int
            New task ID.

        Returns
        -------
        int
            Assigned ID number.
        """
        if self._taskid != tid:
          self._taskid = tid
          if self:
            for bdp in self:
              if bdp is not None: bdp.setkey("_taskid", tid)
            self._needToSave = True
            self.save()

        return tid


    def bestMatch(self, at1, at2):
        """
        Determines the better match of two tasks to the current one.

        Type is most important, then alias, then keywords (most matching
        keywords, followed by most matching values).

        Parameters
        ----------
        at1 : AT
            First task.

        at2 : AT
            Second task.

        Returns
        -------
        int
            ID number of best matching task (in the case of a tie, the first
            task ID is returned).
        """
        score = [0, 0]
        for i in range(2):
          task = at1 if i == 0 else at2
          if task._type == self._type:             score[i] += 1000000000
          if task._alias == self._alias:           score[i] +=  100000000
          if self.isAutoAlias(compat=task._alias): score[i] +=  100000000
          for key in self._keys:
            if key in task._keys:
              score[i] += 10
              if self._keys[key] == task._keys[key]:
                score[i] += 1

        return at1.id() if score[0] >= score[1] else at2.id()

