"""**Project** --- ADMIT project.
   ------------------------------

   This module defines the Admit project class.
"""


# system imports
import time
import xml.etree.cElementTree as et
import fnmatch, os, os.path
import zipfile
import copy
import numpy as np
import threading
import sys
import errno
import datetime
import webbrowser
import ast
import textwrap
import traceback
import subprocess
#import Queue
#from multiprocessing.dummy import Pool as ThreadPool 
import signal

# ADMIT imports
import admit
import admit.version 
import admit.xmlio.Parser as Parser
import admit.Summary as Summary
import admit.util.utils as utils
import admit.util.AdmitHTTP
import admit.util.PlotControl as PlotControl
from admit.xmlio.DtdReader import DtdReader
import admit.util.bdp_types as bt
from admit.util.AdmitLogging import AdmitLogging as logging
from admit.util import LineData

# ==============================================================================

class Admit(object):
    """
    Container for an ADMIT project.   The project is normally based on one
    single FITS cube (in some cases two, where the ingest stage needs a
    primary beam to correct the science cube with), although this is not
    a restriction to ADMIT.

    A FITS cube results in an ADMIT directory, within which you will
    find an admit.xml file describing the project, it's data products (BDP's)
    and the AT's (tasks) that generated the BDP's.

    If input file/directory are given or admit.xml is located in the current
    directory then they are loaded into the class, else a new (empty) class is
    instantiated.

    Parameters
    ----------
    baseDir : str
        Base directory for XML files (the "ADMIT directory").

    name : str
        Alias name.

    basefile : str
        Base XML file name (default: admit.xml).

    create : bool
        Whether to create any needed directories.

    dataserver : bool
        Whether to start the data browser server.

    loglevel : int
        The integer log level from the Python *logging* module.  One of:
 
        - logging.CRITICAL    = 50
        - logging.ERROR       = 40
        - logging.WARNING     = 30
        - logging.INFO        = 20
        - logging.DEBUG       = 10
 
        Default is logging.INFO.

    commit : bool, optional
        Whether to commit XML-backed flows immediately; default is ``True``.
        Set to ``True`` if the flow will *not* be reconstructed (as in a recipe
        script) before use; this is usually the case for interactive mode. Set
        to ``False`` in (most) scripts, which reconstruct the flow each time.

    Attributes
    ----------
    baseDir : str
        Base directory for XML files (the "ADMIT directory").
        Guaranteed to end in os.sep.

    baseFile : str
        Base XML file name, usually admit.xml.

    currDir : str
        Current working directory (at construction).

    fm : FlowManager
        Project flow manager instance.

    new : bool
        Whether the project is new or constructed from an existing XML file.

    pm : ProjectManager
        Project manager instance.

    pmode : int
        Plotting mode.

    ptype : int
        Plotting type.

    count : int
        Flow counter how many times the flow has been run (stored in userData)

    project_id : int
        Static project identification number

    summaryData : instance of admit.Summary
        AT summary data

    userData : dict
        Additional, user-defined data.

    _data_browser_port : int
        Port number that the localhost http server for the data
        browser (aka data GUI) will use.  This attribute is set
        by the operating system.

    _data_server : bool
        Whether to start the data browser server.

    _server : HTTP server
        Data HTTP server.

    Notes
    -----
    .. todo::

      1. in the current implementation every directory, admit or not-admit, can
      be made an admit directory (i.e. contain a root admit.xml)

      2. we really don't need a basefile= in the argument list

    """

    project_id = 0        # Class static project ID counter.
    loginit = False       # whether or not the logger has been innitialized

    def __init__(self, baseDir=None, name='none', basefile=None, create=True, dataserver=False,
                 loglevel=logging.INFO, commit=True):
        #
        # IMPORTANT note for dtd's:   if you add items for admit.xml here,
        # don't forget to edit dtdGenerator.py and run bin/dtdGenerator
        #

        
        # baseDir  : should be a directory, always needed
        # name     : some ID, deprecate?
        # basefile : should be admit.xml, why change it?
        # create   : create any new directory that's needed

        # global ID
        # [KPR] This doesn't actually work as the ID is "global" only to
        #       individual scripts. The ProjectManager overrides it.
        # @todo   can we remove this?
        self.project_id  = Admit.project_id
        Admit.project_id = Admit.project_id + 1

        # Project manager instance.
        self.pm = admit.Manager()

        # Timing info
        self.dt = utils.Dtime("ADMITrun")

        # default to zero to let OS pick an open port
        self._data_browser_port = 0
        # start the server for the data browser or not
        self._data_server = dataserver
        # old admit2 things to keep it working
        self.name = name
        self.plotparams()
        self.loglevel = loglevel
        # new Admit things
        self.userData = {}                # user added data, anything can go in here; use get/set
        self.summaryData = Summary.Summary()      # summary added data, the my_AT.summary() will provide these
        self._fm0 = None                  # flow manager as read from XML
        self.fm = admit.Flow()            # flow manager
        self.pm = admit.Manager()         # project manager
        self.new = False                  # is this a new admit object or are we building it from an xml
        self.astale = 0                   # export hack (will be True if lightweight tar file is built)
        self.count = 0                    # keep track how many times this admit has been run
        self._server = None               # data HTTP server
        # location information
        self.baseDir = None               # base directory for xml files ('the admit directory')
        self.baseFile = None              # base file name, usually admit.xml
        self.currDir = os.getcwd()        # remember where we started (deprecate, we don't need it now)
        #self.queue = Queue.Queue()
        #self.pool = ThreadPool(1)

        if baseDir != None:
            if baseDir[0] == os.sep:
                baseDir = os.path.abspath(baseDir)
                #print "Absolute ADMIT"
            else:
                baseDir = os.path.abspath(self.currDir + os.sep + baseDir)
                #print "Relative ADMIT"
        else:
            baseDir = os.path.abspath(self.currDir + os.sep)
            #print "Local ADMIT"
        #print "ADMIT(%s): CWD=%s" % (baseDir, self.currDir)
        print "ADMIT basedir   = %s" % (baseDir)
        print "ADMIT root      = %s" % (utils.admit_root())
        print "ADMIT version   = %s" % (self.version())

        self._loggername = baseDir.replace("/", ".")
        if self._loggername.startswith("."):
            self._loggername = self._loggername[1:]

        # look for admit.xml or admit.zip files
        if os.path.exists(baseDir):                # does basedir even exist yet
            if os.path.isfile(baseDir):            # basedir is actually a file (should we allow this?)
                loc = baseDir.rfind(os.sep)
                # separate out the base directory and the base file
                if loc == -1:
                    self.baseDir = ""
                    self.baseFile = baseDir
                else:
                    self.basedir = baseDir[:loc+1]
                    self.baseFile = baseDir[loc+1:]
            elif os.path.isdir(baseDir):           # basedir is a directory
                if baseDir[-1] == os.sep:
                    self.baseDir = baseDir
                else:
                    self.baseDir = baseDir + os.sep

                self.baseFile = "admit.xml" if basefile == None else basefile
                self.new = not os.path.exists(self.baseDir + self.baseFile)
            else:
                raise Exception("basedir %s not a file or directory? " % baseDir)

            if zipfile.is_zipfile(self.baseDir + self.baseFile):           # detect if the file is a zip file

                with zipfile.ZipFile(self.baseDir + self.baseFile, 'r') as z:
                    z.extractall(self.basedir)
                if not os.path.exists(self.basedir + "admit.xml"):
                    raise Exception("No admit.xml file located in ", self.basedir)
                self.baseFile = "admit.xml"
        else:                                                             # we are working with a new basedir
            #create = False
            if create:
                self.mkdir(baseDir)
            self.new = True
            if baseDir[-1] == os.sep:
                self.baseDir = baseDir
            else:
                self.baseDir = baseDir + os.sep
            self.baseFile = "admit.xml"
        logging.init(self._loggername, baseDir + os.sep + "admit.log", self.loglevel)
        if not Admit.loginit:
            # @todo should this be in logging? for now, do here
            logging.addLevelName(logging.TIMING,     "TIMING")
            logging.addLevelName(logging.REGRESSION, "REGRESSION")
            Admit.loginit = True

        if not self.new:                           # load the existing files/data
            # @todo the AT's need the self.baseDir
            #       until then checkfiles() will complain the BDP.getfiles() don't exist on a re-run
            # notice admit is passed to the Parser
            parser = Parser.Parser(self, self.baseDir, self.baseFile)
            parser.parse()
            self._fm0 = parser.getflowmanager()
            self._fm0._summaryData = parser.getSummary()
            self._fm0._twins = {}             # dict of merged tasks

            # Re-initialize project manager.
            for pid in parser.projmanager:
                # Managed projects must be fully formed and up to date.
                parser.projmanager[pid].mergeFlow()
                self.pm.addProject(parser.projmanager[pid])

            # Replace linked ATs in multiflows with their master copies.
            # Only the latter contain validated BDP data.
            for tid in self._fm0:
                at = self._fm0[tid]
                pid = at.getProject()
                if pid:
                    # This task is linked from another project.
                    if pid in self.pm:
                        tid0 = at.id(True)
                        if tid0 in self.pm[pid].fm:
                            # Copy master AT reference.
                            self._fm0[tid] = self.pm[pid].fm[at.id(True)]
                        else:
                            raise Exception('No task #%d in project #%d' % (tid0, pid))
                    else:
                        raise Exception('No linked project #%d' % pid)

            if commit: self.mergeFlow()

        #print "ADMIT.baseDir = ", self.baseDir
        if self.baseDir[-1:] != os.sep:
            raise Exception('ADMIT.basedir=%s does not end with %s' % (self.baseDir, os.sep))

        # data server for locahost web browing
        if self._data_server:
            self.startDataServer()
        else:
            self._data_url = None

        signal.signal(signal.SIGUSR1, self._signal_handler)
        self._pid = os.getpid()

        if self.userData.has_key('flowcount'):
            self.count = self.userData['flowcount'] + 1
        else:
            self.count = 1
        self.userData['flowcount'] = self.count
        print "ADMIT flowcount = %d stale = %d" % (self.count,self.astale)

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + "ADMIT :" + bt.format.END
        print self.fm
        return ""

    def __del__(self):
        logging.shutdown()


    def __len__(self):
        """ Returns the numbers of tasks in the project.
        """
        return len(self.fm)

    def __contains__(self, tid):
        """Flow tasks membership operator.

           Parameters
           ----------
           tid : int
               Task ID number or alias name.

           Returns
           -------
           bool
               Membership result.
        """
        return self.fm.__contains__(tid)

    def __iter__(self):
        """Flow tasks iterator.

           Returns
           -------
           iterator
               Task iterator.
        """
        return iter(self.fm)

    def __getitem__(self, tid):
        """
        Returns an AT, referred by its task ID (an integer >= 0).

        Parameters
        ----------
        tid : int
            Task ID number or alias name.

        Returns
        -------
        AT
          Reference to AT with ID `tid`.

        Notes
        -----
        A BDP (bdp_out) can be accessed by indexing the task, i.e.,
        admit[task_id][bdp_out_id] returns a BDP.
        """
        return self.fm[tid]

    def version(self):
        """return version of ADMIT
        """
        return admit.version.__version__
    
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
        logging.setLevel(level)

    def getlogginglevel(self):
        """ Method to return the current logging level

            Parameters
            ----------
            None

            Returns
            -------
            An int representing the current logging level
        """
        return logging.getEffectiveLevel()

    def mkdir(self, dirname):
        """Make a directory in the ADMIT hierarchy, if it doesn't exist yet.
           It also allows an absolute path, in the classical unix sense, but
           this is normally not needed.

           Parameters
           ----------
           dirname : str
               Directory name.

           Returns
           -------
           None
        """
        if dirname[0] == os.sep:
            # it's already an absolute path
            dname = dirname
        else:
            # make it relative to the admit
            dname = os.path.abspath(self.baseDir + dirname)

        if not os.path.exists(dname):
            try:
                os.makedirs(dname)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(dname):
                    pass
                else: raise
            #print "ADMIT.mkdir: ",dname

    def getFlow(self):
        """
        Returns flow manager instance.

        Parameters
        ----------
        None

        Returns
        -------
        FlowManager
            Flow manager instance.
        """
        return self.fm

    def getManager(self):
        """
        Returns project manager instance.

        Parameters
        ----------
        None

        Returns
        -------
        ProjectManager
            Project manager instance.
        """
        return self.pm

    def plotparams(self, plotmode=PlotControl.BATCH, plottype=PlotControl.PNG):
        """ Determines if plots are saved and in what format.
            These are based on simple matplotlib diagrams.
            Common output formats are png and pdf.
            Note: this only applies to new AT's started in a flow,
            to change existing parameters in a re-run for example,
            you will need to manually change the AT._plot_mode
            and AT._plot_type

            Parameters
            ----------
            plotmode : int
                Plotting mode.  Default: PlotControl.BATCH

            plottype : int  
                Plot format type.  Default: PlotControl.PNG.

            Returns
            -------
            None

            See Also
            --------
            util.PlotControl plot modes and types.
        """
        #if plotmode < 0:
        #    return (self.pmode,self.ptype)
        self.pmode = plotmode
        self.ptype = plottype
        #AT._plot_mode = plotmode
        #AT._plot_type = plottype
        # nasty cheat, need to formalize a safer method to talk to APlot
        # @todo this also means the XML reader will not properly pass this on
        #aplot.APlot.pmode = plotmode
        # aplot.APlot.ptype = plottype
        #print "plotmode: pmode=%d ptype=%s" % (self.pmode,self.ptype)

    def addtask(self, a, stuples=None, dtuples=None):
        """
        Add an AT to the project.

        Also adjusts the connection mapping between tasks.
        Usually all but the first task---typically, Ingest_AT---will have
        'stuples' (a List of Source Tuples (task-id,bdp-id)). A source 2-tuple
        consists of a task ID (``task-id``, such as returned by this method) and
        BDP output slot number (``bdp-id``, zero-based). If the output slot is
        zero (the tuple refers to the *first* BDP output from the task), then
        the tuple can be replaced by the task ID for convenience---e.g.,
        stuples = [(t1,0), (t2,1)] is equivalent to
        stuples = [t1, (t2,1)].

        Support for re-running scripts: this method will ignore attempts to
        re-add a task of the same type and ID to the existing flow, if the
        project has been restored from XML. Between invocations, scripts may be
        edited to append new tasks to the flow, but not remove or insert them.
        Keywords for existing ATs may also be changed by the script; if changes
        are found, the existing task will be marked out-of-date.

        Parameters
        ----------
        a : AT
            ADMIT task to append/insert into the flow.

        stuples : list of 2-tuples, optional
            List of source connection 2-tuples, one per BDP input port.

        dtuples : list of 4-tuples, optional
            List of destination connection 4-tuples.

        Returns
        -------
        int
            Input task ID on success, else -1 (error detected).

        See Also
        --------
        add (FlowManager)
        """
        # need to check if fm has been installed
        # a.check() - was deprecated
        # task should inherit these from ADMIT
        # @todo  some (pmode) could be changed without hard
        #        others (baseDir) probably not a good idea unless you cd around
        a._plot_mode = self.pmode
        a._plot_type = self.ptype
        a.setloggername(self._loggername)

        if not a.getProject():
            # Reset base directory for local tasks only.
            a.baseDir(self.baseDir)
        else:
            # Increment link count for tasks from other projects.
            a.link()
            if stuples != None:
                raise Exception("addtask: cannot specify stuples for linked task")
        # now add the BDP_in's to the AT
        # note the BDP_out's are generated later, and cannot be added via fm.add() at this stage
        #
        return self.fm.add(a, stuples, dtuples)


    def findtask(self, isMatch):
        """
        Finds ATs in the flow matching a criterion.

        Applies the function `isMatch` to all ATs in the flow, in proper
        dependency order, accumulating matching ATs in a list (the return
        value). Downstream ATs are guaranteed to follow their predecessors in
        this list. Often `isMatch` may be conveniently expressed as a lambda
        function.

        Parameters
        ----------
        isMatch : bool functor(AT)
            Function object taking one AT as input and returning a Boolean.

        Returns
        -------
        list of ATs
            ATs testing True using `isMatch`.

        Notes
        -----
        This method is a wrapper for `FlowManager.find()
        <FlowManager.html#admit.FlowManager.FlowManager.find>`_.

        Examples
        --------
        To find all ATs with ID less than 100 in project `p`:

        >>> p.find(lambda at: at.id() < 100)
        """
        return self.fm.find(isMatch)

    def dir(self):
        """See AT.dir() but placed here for convenience as well.

           Parameters
           ----------
           None

           Returns
           -------
           str
               Base directory.
        """
        return self.baseDir

    def exit(self, exit):
        """ Early cleanup and exit if exit > 0

            Parameters
            ----------
            exit : int
                The exit code to exit with (must be > 0)

            Returns
            -------
            None
        """
        if exit > 0:
            self.run()
            logging.error("exit %d" % exit)
            os._exit(exit)     # quick exit, return status 'exit'
            #sys.exit(exit)    # exit back to CASA, which then becomes confused and return status 0
        else:
            logging.info("exit %d" % exit)
            os._exit(0)

    def mergeFlow(self, finalize = True):
        """
        Merges tasks from the XML-derived flow (if any).

        When projects are restored to memory from persistent XML files, that
        task flow is initially held in stasis while the (possibly modified)
        flow is being reconstructed, typically by re-running a script. This
        reconstruction phase lasts from the point where the XML is read up to
        the first call to this method with `finalize` set (most typically, the
        first call to run(), which calls this method internally). Calling this
        method during reconstruction compares the old flow to the newly
        constructed flow and tasks present unaltered in the new flow (i.e.,
        same BDP inputs and keyword values as before) are marked up to date, if
        they were up to date in the original flow. Other relevant attributes
        are transferred as appropriate.

        Parameters
        ----------
        finalize : bool, optional
            Whether to discard the XML-derived flow after merge analysis,
            preventing future merge attempts.

        Returns
        -------
        None

        Notes
        -----
        It is permissible to add or remove arbitrary tasks from the flow, in an
        arbitrary order, while reconstructing it. Tasks unaffected by the
        changes (if any) will not be re-executed gratuitously.

        After finalization, the old flow is forgotten and subsequent calls will
        have no effect (and likewise for fresh projects not backed by XML).
        """
        if self._fm0:
#          print "-- fm0 -- "
#          self._fm0.show()
#          print "-- fm (pre) -- "
#          self.fm.show()
          if self.fm:
            # A non-empty flow has been constructed.
            self.fm.mergeTasks(self.summaryData,
                               self._fm0,
                               self._fm0._summaryData,
                               self._fm0._twins, finalize)
          else:
            # No new flow; just restore the old one as-is.
            self.summaryData = self._fm0._summaryData
            del self._fm0._summaryData
            del self._fm0._twins
            self.fm = self._fm0
            self._fm0 = None

            # Ensure new task IDs don't overwrite existing ones!
            if self.fm: self.fm._taskid = 1 + max(self.fm._bdpmap.keys())

        if finalize:
          if self._fm0:
            # Remove orphaned BDPs attached to any remaining unmatched tasks.
            # These tasks are gone from the flow.
            for tid0 in self._fm0:
              if not self._fm0._twins.has_key(tid0):
                task = self._fm0[tid0]
                logging.warning("Task %s - '%s' no longer in flow; deleting "
                                "associated BDP data:" %
                                (task._type, task._alias))
                for bdp in self._fm0[tid0]:
                  if bdp is not None:
                    logging.warning("     BDP Name: %s  Type: %s  Uid: %d" %
                                    (bdp.show(), bdp._type, bdp._uid))
                    bdp.delete()

            self._fm0 = None

#        print "-- fm (post) -- "
#        self.fm.show()



#    def __run__(self, write=True):
#        print "******************DOING RUN IN THREADPOOL*************************"
#        writeargs = [write]
#        self.pool.map(self.__run__,writeargs)
#        print "******************DONE RUN IN THREADPOOL*************************"

    def _signal_handler(self,num,stack):
        print 'Received signal %d in %s' % (num, threading.currentThread())
        sys.stdout.flush()
        sys.stderr.flush()
        self.run()

    def dryrun(self):
        self.fm.dryrun()


    def run(self, write=True, commit=True):
        """
        Runs the project flow.

        Run those pieces of the pipeline flow
        deemed out of date. After the run, the flow
        tasks  gather their summary into ADMIT's summaryData,
        ensuring that summaryData always is consistent with the
        current flow, and does not contain remnants from orphans.

        Parameters
        ----------
        write : bool, optional
          Whether to write the project XML files after running the flow;
          default is ``True``.

        commit: bool, optional
          Whether to commit the current flow after merging flow tasks with
          the XML-derived flow (if present). Set to ``False`` during incremental
          run()/addtask() flow reconstruction. Once a flow is committed, all
          requests to add or remove flow tasks will vest immediately. Default
          is ``True``.

        Returns
        -------
        None

        See Also
        --------
        mergeFlow

        Notes
        -----
        This method supports intelligent re-running of projects read from XML.
        Task flows may be reconstructed (as in a script) in any order, from the
        point where the XML is read up to the first call to run() (with
        commit=True). Tasks present (unaltered) in the new flow and marked up
        to date in the XML will not be re-executed.
        """
        # For multiflows, re-run parent projects first. This ensures all
        # linked tasks (which could depend on each other, if linked from the 
        # same parent) are processed in the correct order.
        logging.info("ADMIT run() called [flowcount %d]" % self.count)
        for pid in self.pm:
            self.pm[pid].run()

        # Merge XML-backed flow, if any.
        self.mergeFlow(commit)

        # Make current project summary globally available to ATs.
        # It will be updated on-the-fly in FlowManager.run().
        admit.Project.summaryData = self.summaryData
        try:
          self.fm.run()
        except:
          logging.error("Project run() failed; %s : saving state..." % str(sys.exc_info()))
          self.write()
          raise

#        print "-- fm (run) -- "
#        self.fm.show()

        self.userdata()
        if write: self.write()  # includes HTML update

        cpu = self.dt.end()
        logging.info("ADMIT run() finished [flowcount %d] [cpu %g %g ]" % (self.count,cpu[0],cpu[1]))

    def print_summary(self):
        """Print out summary data

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        print "############## SUMMARY DATA ###############"
        self.summaryData.show()

    def userdata(self):
        """Collects current AT userdata. **warning:** No check is done for duplicate keys!

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        for tid in self.fm:
            self.userData.update(self.fm[tid].userdata())

    def updateHTML(self):
        """Writes out HTML views of this object.
           It is expected that summary() has been called first.

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        admitresources = utils.admit_root() + os.sep + "etc" + os.sep + "resources"
        d = self.dir() + "resources"
        #grmph, this gets CVS directory too. need to remove separately
        cmd = "rm -rf %s && cp -r %s %s" % (d, admitresources, d)
        os.system(cmd)
        # rm CVS
        for (path,dirs,files) in os.walk(d):
            if path.endswith("CVS"):
               utils.remove(path)

        dotfile = self.dir()+'admit.dot'
        self.fm.diagram(dotfile)
        # Attempt to create a PNG from the dot file.
        # summary.html() will look for this. Ignore
        # if 'dot' is not on system (retval nonzero)
        #
        # Command must be in a list because shell=True is a security hazard.
        # See https://docs.python.org/2/library/subprocess.html#using-the-subprocess-module
        cmd = ["dot", "-Tpng", "-o", self._dotdiagram(), dotfile]
        try:
            retval = subprocess.call(cmd)
            if retval !=0: diagram = ""
        except:
            diagram = ""

        self.summaryData.html(self.dir(), self.fm, self._dotdiagram())
        self.atToHTML()
        self.logToHTML()


    def atToHTML(self):
        """Write individual AT data to the html form"""
        self.fm.connectInputs() # throws exception
        admitloc = utils.admit_root()
        admitetc = admitloc + os.sep + "etc"
        admitfile = admitetc + os.sep + "form_at.html"
        admit_headfile = admitetc+os.sep+"form_head.html"
        admit_tailfile = admitetc+os.sep+"form_tail.html"

        # self.dir() has trailing slash, need to strip it or
        # basename() returns ''
        # python basename() behavior different from Unix!!
        outdir = self.dir()
        basedir = os.path.basename(outdir.rstrip(os.sep))

        # Spit out the boiler plate header that is the same for
        # all form.html files.
        try:
            with open(admit_headfile,"r") as h:
                header = h.read() % (basedir,basedir)
            outfile = outdir +  "form.html"
            f = open(outfile,"w")
            f.write(header)
        except:
            return
        try:
            with open(admitfile,"r") as h:
                header = h.read() 
        except:
            return

        xx = '\n'
        for tid in self.fm:
            xx = xx + self.fm[tid].html(header)

        f.write(xx)

        # Spit out the boiler plate tail that is the same for
        # all form.html files.
        try:
            with open(admit_tailfile,"r") as h:
                tail = h.read() % datetime.datetime.now() 
            f.write(tail) 
        except:
            f.close()
            return

        f.close()

    def logToHTML(self):
        """Write the admit.log to an html file"""
        admitloc = utils.admit_root()
        admitetc = admitloc + os.sep + "etc"
        admitfile = admitetc + os.sep + "log_template.html"

        outdir = self.dir()
        basedir = os.path.basename(outdir.rstrip(os.sep))
        admitlog = outdir + "admit.log"
        outfile = outdir +  "log.html"

        try:
            with open(admitfile,"r") as h:
                template = h.read() 
            with open(admitlog,"r") as l:
                logtext = l.read() 
            with open(outfile,"w") as f:
                f.write(template % (basedir, basedir, logtext, datetime.datetime.now()) )
                f.close()
        except Exception, e:
            print e
            return



    def script(self, pyfile):
        """
        Generates a Python script regenerating the current project.

        The resulting script is intended to recreate the project results from
        scratch and to be run from the *parent* of the project directory.
        Running the script over existing project results is unpredictable and
        not supported.

        Parameters
        ----------
        pyfile : str
            Output Python script file name.

        Returns
        -------
        None
        """
        py = open(pyfile, mode='w')
        dirs = os.path.split(self.dir()[:-1])
        py.write("#!/usr/bin/env casarun\n"
                 "#\n"
                 "# This script was auto-generated by ADMIT version %s"
                 " and may be overwritten;\n"
                 "# copy before editing. It expects to run from %s/.\n"
                 "# If you need to start from scratch:   rm -rf %s\n"
                 "#\n" % (self.version(),dirs[0],dirs[1]))

        # If we're processing only one FITS cube, let the user specify a
        # different one on the command line.
        tcube = []
        for tid in self.fm._depsmap[0]:
          if self[tid]._type == 'Ingest_AT': tcube.append(tid)

        if len(tcube) == 1:
          tcube = tcube[0]
          py.write("# This flow processes a single data cube. "
                   "To process other cubes in the same\n"
                   "# way, call this script with another cube file "
                   "as the command line argument:\n"
                   "# %% admit0.py CUBEFILE\n"
                   "#\n"
                   "import os, sys\n"
                   "import admit\n\n"
                   "# Command line processing.\n"
                   "argv = admit.utils.casa_argv(sys.argv)\n"
                   "if len(argv) < 2:\n"
                   "  cubefile = '%s'\n"
                   "  projdir = '%s'\n"
                   "else:\n"
                   "  cubefile = argv[1]\n"
                   "  projdir = os.path.splitext(argv[1])[0] + '.admit'\n\n"
                   "# Master project.\n"
                   "p = admit.Project(projdir, commit=False)\n"
                   % (self[tcube].getkey('file'), dirs[1]))
        else:
          tcube = None
          py.write("import admit\n\n"
                   "# Master project.\n"
                   "p = admit.Project('%s', commit=False)\n" % (dirs[1]))

        self.pm.script(py, self.dir())
        self.fm.script(py, tcube=tcube)

        py.write("\n# Update project.\n"
                 "p.run()\n")
        py.close()
        os.chmod(pyfile, 0o755);


    def show(self):
        """ Prints project state.

            Parameters
            ----------
            None

            Returns
            -------
            None

            Notes
            -----
            Currently only display FlowManager contents.
        """
        print "==== ADMIT(%s) ====" % (self.name)
        self.fm.show()

    def browse(self):
        """Open a web browser tab with the URL of this admit project"""
        try:
            webbrowser.open_new_tab(url=self._data_url)
        except Exception, e:
            logging.warning("Couldn't open URL '%s' because %s" % (self._data_url,e))

    def showsetkey(self, outfile=None):
        """ Show current keys for tasks
            For now on screen, but meant to aid writing a template file for rerun 

            Parameters
            ----------
            outfile : str
                The name of the output file

            Returns
            -------
            None
        """
        self.fm.showsetkey(outfile)

    def set(self, **kwargs):
        """ Sets keys and values in userData.

            Parameters
            ----------
            kwargs : dictionary like
                Command line arguments for the function, can be a=x,b=y or
                \*\*{a:x, b:y} format

            Returns
            -------
            None
        """
        self.userData.update(kwargs)

    def check(self):
        """ Check all project BDPs for name collisions.
        Also identifies orphaned branches of the tree.
        A topological sort is needed as well, if they are not in the correct
        execution order.

        See Also
        --------
        UNIX tsort(1) program.
        """
        pass

    def get(self, key):
        """Get a global ADMIT parameter.

           Parameters
           ----------
           key : str
               User-defined data keyword.

           Returns
           -------
           str
               User-defined (userData) keyword value.

           Notes
           -----
           .. todo::
               This method should mirror the way we do this in the AT
               (setkey/getkey)
        """
        if key in self.userData:
            return self.userData[key]
        else:
            print "ADMIT: %s not a valid userData key" % key

    def has(self, key):
        """Query if a global user key exists for this admit project.

           Parameters
           ----------
           key : str
               User-defined data keyword.

           Returns
           -------
           bool
              True if keyword is present in userData, else False.
        """
        return key in self.userData

    def print_methods(self):
        """ Print all the methods of this object and their doc string(s).

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        print '\n* Methods *'
        for names in dir(self):
            attr = getattr(self, names)
            if callable(attr):
                print names, ':', attr.__doc__

    def print_attributes(self):
        """ Print all the attributes of this object and their value(s).

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        print '* Attributes *'
        for names in dir(self):
            attr = getattr(self, names)
            if not callable(attr):
                print names, ':', attr

    def print_all(self):
        """ Calls all the methods of this object.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        for names in dir(self):
            attr = getattr(self, names)
            if callable(attr) and names != 'print_all' and names != '__init__':
                attr() # calling the method

    def discover(self, mode=None, rootdir='.'):
        """Project data discovery.

           Parameters
           ----------
           mode : TBD
               Discovery mode.

           rootdir : str, optional
               Search root directory.

           Returns
           -------
           list
               Search results.
        """
        print "query_dir() and find_files() are the worker functions"
        print "discover not implemented yet"
        pp = []
        return pp

    #def query_dir(self,here=None):
    #    """
    #    Drill down and find directories in which ADMIT exists.

    #    Parameters
    #    ----------
    #    here : str, optional
    #        Directory to begin search; defaults to current directory.

    #    Returns
    #    -------
    #    list
    #        Search results.
    #    """
    #    dlist = []
    #    if here == None:
    #        path = "."
    #    else:
    #        path = here
    #    n = 0
    #    for path, dirs, files in os.walk(path):
    #        # better not to loop, but os.path() for existence
    #        n = n + 1
    #        for f in files:
    #            if f == self.parfile: dlist.append(path)
    #    logging.debug("Queried " + str(n) + " directories, found " + 
    #        str(len(dlist)) + " with a parfile")
    #    return dlist

    def find_bdp(self):
        """Find all bdp's in the current admit.

           Parameters
           ----------
           None

           Returns
           -------
           list
               All \*.bdp files within the admit hierarchy.
        """
        len1 = len(self.dir())
        matches = []
        for root, dirnames, filenames in os.walk(self.dir()):
            for filename in fnmatch.filter(filenames, '*.bdp'):
                matches.append(os.path.join(root, filename)[len1:])
        #print "BDPs:",matches
        return matches

    def find_files(self, pattern="*.fits"):
        """
        Find files containing a wildcard pattern.

        Parameters
        ----------
        pattern : str, optional
            File name wildcard pattern.

        Returns
        -------
        list
            File names matching the pattern.
        """
        #@todo this should call util.find_files instead.
        flist = []
        for filename in os.listdir('.'):
            if fnmatch.fnmatch(filename, pattern):
                flist.append(filename)
        return flist

    def setdir(self, dirname, create=True):
        """
        Changes current working directory. The directory is
        assumed to contain parameter file.

        .. note:: Deprecated.
            See pushd()/popd() for a better version.

        Parameters
        ----------
        dirname : str
            Directory to work in.

        create : bool, optional
            Whether to create the directory if it doesn't exist.


        Notes
        -----
        .. todo::
          the new mkdir() and self.baseDir are the way to work in ADMIT
        """
        def mkdir_p(path):
            #if not os.path.isdir(dirname):
            #    os.makedirs(dirname)
            #
            try:
                os.makedirs(path)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else: raise
        self.p = dirname
        self.pwd = os.getcwd()
        if create:
            mkdir_p(dirname)
        os.chdir(dirname)
        logging.debug("ADMIT::setdir %s" % dirname)

    def tesdir(self):
        """
        Revert back from previous setdir (not recursive yet).

        .. note:: Deprecated.
            See pushd()/popd() for a better version.
        """
        os.chdir(self.currDir)

    #def walkdir(self,dlist):
    #    """Walks through directory list, printing what it finds

    #       Parameters
    #       ----------
    #       dlist : list of str
    #           Directory names to traverse.

    #       Returns
    #       -------
    #       None
    #    """
    #    print "Walkdir ", dlist
    #    for d in dlist:
    #        self.setdir(d)
    #        print "d: ", d
    #        par = pp.ParFile()
    #        print par.get('fits')
    #        print par.keys()
    #        self.tesdir()

    def read(self):
        """Reads a project.

           Notes
           -----
           Not implemented.
        """
        pass

    def export(self, mode):
        """
        Prepare Admit for (archive) export. This means it has to loop over the BDP's
        and decide which items are going to copied over to admit.userData{}, as admit.xml
        is the only file external agents should have to look at.

        See also the script "admit_export" which is currently doing this work.

        Parameters
        ----------
        mode : str
            Export mode.

        Returns
        -------
        None

        Notes
        -----
        Not implemented.
        """
        print "Export: ", mode


    def write(self):
        """ Writes out the admit.xml file, admit0.py script and
            project html files.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        self.writeXML()
        self.updateHTML()

    def writeXML(self, script = True):
        """ Writes out the admit.xml file and admit0.py script.

            Reading the XML file occurs in the constructor.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        # For multiflows, rewrite parent project XML files in case
        # any linked tasks were updated.
        self.pm.write()

        # get the dtd files, which acts as a guide
        dtdRead = DtdReader("admit.dtd")
        dtd = dtdRead.getDtd()

        dtdlist = {}
        # create the root node
        root = et.Element("ADMIT")

        # write out the each data member
        unode = et.SubElement(root, "userData")
        unode.set("type", bt.DICT)
        nd = []
        st = []
        attr = copy.deepcopy(self.userData)
        for k, v in attr.iteritems():
            if isinstance(v, np.ndarray):
                nd.append(k)
                attr[k] = np.ndarray.tolist(v)
            elif isinstance(v, set):
                st.append(k)
                attr[k] = list(v)
        unode.set("ndarray", str(nd))
        unode.set("set", str(st))
        temptext = str(attr)
        tt = ""
        tlist = textwrap.wrap(temptext, width=10000)
        for l in tlist:
            tt += l + "\n"
        unode.text = tt

        # write out the summary data
        self.summaryData.write(root)

        pnode = et.SubElement(root, "project_id")
        pnode.set("type", bt.INT)
        pnode.text = str(self.project_id)

        nnode = et.SubElement(root, "name")
        nnode.set("type", bt.STRING)
        temptext = self.name
        tt = ""
        tlist = textwrap.wrap(temptext, width=10000)
        for l in tlist:
            tt += l + "\n"

        nnode.text = tt

        fnode = et.SubElement(root, "flowmanager")
        fnode.set("type", bt.DICT)                      #HERE
        attr = copy.deepcopy(self.fm)

        pmnode = et.SubElement(root, "pmode")
        pmnode.set("type", bt.INT)
        pmnode.text = str(self.pmode)

        ptnode = et.SubElement(root, "ptype")
        ptnode.set("type", bt.INT)
        ptnode.text = str(self.ptype)

        llnode = et.SubElement(root, "loglevel")
        llnode.set("type", bt.INT)
        llnode.text = str(self.loglevel)

        llnode = et.SubElement(root, "astale")
        llnode.set("type", bt.INT)
        llnode.text = str(self.astale)

        lnnode = et.SubElement(root, "_loggername")
        lnnode.set("type", bt.STRING)
        temptext = self._loggername
        tt = ""
        tlist = textwrap.wrap(temptext, width=10000)
        for l in tlist:
            tt += l + "\n"
        lnnode.text = tt

        fnode.set("ndarray", str([]))
        fnode.set("set", str([]))
        tasks = {}       # make a simplified version of the connection map for writing out, it will be reconstructed on read in
        for tid in self.fm:
            tasks[tid] = None
        temptext = str({"connmap" : self.fm._connmap,
                        "bdpmap"  : self.fm._bdpmap,
                        "depsmap" : str(self.fm._depsmap),
                        "varimap" : str(self.fm._varimap),
                        "tasklevs": self.fm._tasklevs,
                        "tasks"   : tasks})

        tt = ""
        tlist = textwrap.wrap(temptext, width=10000)
        for l in tlist:
            tt += l + "\n"
        fnode.text = tt


        pmnode = et.SubElement(root, "projmanager")
        pmnode.set("type", bt.DICT)
        pmnode.set("ndarray", str([]))
        pmnode.set("set", str([]))
        temptext = str(self.pm._baseDirs)
        tt = ""
        tlist = textwrap.wrap(temptext, width=10000)
        for l in tlist:
            tt += l + "\n"
        pmnode.text = tt


        #print 'Flow',fnode.text
        for tid in self.fm:
            root, tdtd = self.fm[tid].write(root)
            dtdlist[self.fm[tid]._type] = tdtd
        # generate a string from the nodes
        rough_string = et.tostring(root, 'utf-8')

        # make the text human readable
        temp = rough_string.replace(">", ">\n")
        temp = temp.replace("</", "\n</")

        # open the output file
        outFile = open(self.baseDir + "admit.xml", 'w')
        # write out the header
        outFile.write("<?xml version=\"1.0\" ?>\n")

        # write out the dtd info at the top
        outFile.write("<!DOCTYPE ADMIT [\n\n")
        for line in dtd:
            outFile.write(line)
        for d in dtdlist:
            for l in dtdlist[d]:
                outFile.write(l)
        outFile.write("]>\n\n")
        # write out the data
        outFile.write(temp)

        outFile.close()

        if script:
            # Don't name script 'admit.py' to avoid confusing 'import admit'.
            self.script(self.dir() + 'admit0.py')

    def clean(self):
        """ Method to delete orphan bdp's (files and underlying data)

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        files = utils.getFiles(self.dir())

        for task in self.fm._tasks.values():
            delfiles = []
            for bdp in task._bdp_out:
                if bdp is None:
                    continue
                for i, file in enumerate(files):
                    if file.endswith(bdp.xmlFile + ".bdp"):
                        delfiles.append(i)
            delfiles.sort()    
            delfiles.reverse()
            for d in delfiles:
                del files[d]

        for file in files:
            bdp = utils.getBDP(file)
            print "DELETING",bdp.xmlFile
            bdp.delete()
            del bdp

    def startDataServer(self):
        """Starts the data HTTP server.
           On a separate thread, start the http server on localhost:_data_browser_port
           that will allow web browsing of data products.   Also attempt
           to open a browser window at that URL. When this method returns,
           the variable self._data_browser_port will have the value of
           the port returned by the OS.  
           See util.AdmitHTTP.AdmitHTTPServer

           Parameters
           ----------
           None

           Returns
           -------
           None
        """
        if self._server != None:
            print "A data server for this Admit object is already running on localhost:%d" % self._data_browser_port
            return

        server_address = ("localhost", self._data_browser_port)
        try:
            self._server = admit.util.AdmitHTTP.AdmitHTTPServer(server_address, docroot=self.baseDir, postcallback = self._onpost )
            self._data_browser_port = self._server.server_address[1]
        except:
            print "Failed to get a port for the data browser."
            return

        threadName = "%s:%d" % (self.baseDir, self._data_browser_port)
        thread = threading.Thread(name=threadName, target=self._serveforever, args=())
        thread.setDaemon(True)
        thread.start()
        # create the attribute but we don't wish to save it in admit.xml
        self._data_url = 'http://localhost:%d' % self._data_browser_port
        print "Your data server is started on %s. Attempting to open a browser page with that URL. \nThe data server will halt when you quit your CASA session or otherwise destroy this ADMIT object." % self._data_url
        # open page in new tab if possible
        self.browse()

    def url(self):
        """Print the URL for the data browser

        Parameters
        ----------
        None

        Returns
        -------
        String representing localhost url on which data can be viewed.
        """
        return self._data_url

    def export(self,level=0,casa=True,fits=False,out=None):
    #   """export this Project to a gzipped tar file"""
       if out == None: out=self._defaulttarfile()
    
    def _defaulttarfile(self):
       """return an export file name baseDir.tar.gz for this project
       """
       return self.baseDir+".tar.gz"  # option for ZIP?

    #def runqueue(self):
    #    try:
    #        print "callback queue get"
    #        callback = self.queue.get(False)
    #    except Queue.Empty:
    #        pass
    #    print "got"
    #    callback()

    def _onpost(self, payload):
        """This is the callback function when a user edits ADMIT key words
        via form.html.  It will cycle through the tasks and call setkeys,
        then call admit.run().

        Parameters
        ----------
        payload: dict
            The data coming from the server.

        Returns
        -------
        None (maybe should return boolean if something failed?)

        Notes
        -----
        Should not be called directly.
        """

        #@todo: make this method a dictionary of methods?
        command = payload["command"]
        logging.info("Got command %s from browser" % command)
        if command == "run":
            #print "got command run"
            try:
                for t in payload['task']:
                   taskid = int(t["taskid"])
                   for key in t:
                       # skip the hidden form inputs, which are only to
                       # sort out what task this is, and any other non-matching keys
                       if not self.fm[taskid].haskey(key):
                          continue
                       
                       # Everything coming back from the web form is unicode.
                       # ast.literal_eval solves this, except for strings!
                       # (which would need nested quotes).  
                       # So first decode the value to a string. We don't need to
                       # decode the key to a string because python dictionaries
                       # with support unicode key access.
                       value_enc = t[key].encode('utf8')
                       # Then do type-checking
                       # of the AT's key to decide whether to invoke ast.literal_eval.  
                       # Note this may also be useful if the web form serialization 
                       # is ever upgraded to preserve types (requires use of :types 
                       # in form)
                       # See https://github.com/marioizquierdo/jquery.serializeJSON
                       
                       #print "key=%s, val=%s type:%s" % (key,t[key],type(t[key])) 
                        
                       if type(value_enc) == type(self.fm[taskid]._keys[key]):
                           #print "straight setkey"
                           self.fm[taskid].setkey(key,value_enc)
                       else:
                           #print "AST key=%s, val=%s" % (key,ast.literal_eval(t[key]) )
                           self.fm[taskid].setkey(key,ast.literal_eval(t[key]))
            except Exception, e:
               print "Bummer, got exception %s" % e
               traceback.print_exc()
               return
            
            try:
               logging.info("Re-running admit...")
               print "[you may have hit return here]"
               #self.queue.put(self.run)
               #self.runqueue()
               os.kill(self._pid,signal.SIGUSR1)
               #self.run(write=True)
               #formurl = self._data_url+"/form.html"
               #webbrowser.open(url=formurl,new=0)
               if payload["firefox"] == True:
                   #print "Damn you, Firefox!"
                   formurl = self._data_url+"/form.html"
                   webbrowser.open(url=formurl,new=0)
               return
            except Exception, e:
               print "got exception on run %s" % e
               traceback.print_exc()

        elif command == "dryrun":
            try:
                for t in payload['task']:
                   taskid = int(t["taskid"])
                   for key in t:
                       # skip the hidden form inputs, which are only to
                       # sort out what task this is, and any other non-matching keys
                       if not self.fm[taskid].haskey(key):
                          continue
                       
                       value_enc = t[key].encode('utf8')
                       if type(value_enc) == type(self.fm[taskid]._keys[key]):
                           #print "straight setkey"
                           self.fm[taskid].setkey(key,value_enc)
                       else:
                           #print "AST key=%s, val=%s" % (key,ast.literal_eval(t[key]) )
                           self.fm[taskid].setkey(key,ast.literal_eval(t[key]))
            # update all downstream stale flags, so that they
            # get marked in the HTML file.
                       self.fm.connectInputs()
            except Exception, e:
               print "Bummer, got exception %s" % e
               traceback.print_exc()
               return
            
            try:
                #self.fm.dryrun()
                self.write()
                if payload["firefox"] == True:
                    #print "damn you, Firefox!"
                    formurl = self._data_url+"/form.html"
                    webbrowser.open(url=formurl,new=0)
                return
            except Exception, e:
                print "got exception on dryrun %s" % e
                traceback.print_exc()
                return

        elif command == "linelistbdp":
            try:
                taskid = payload["taskid"]
                # replace the data in the Linelist bdp table
                llbdp = self.fm[taskid]._bdp_out[0]
                # this is an array of LineData objects
                llbdp.table.data = np.array([], dtype=object)
                rows = payload["rows"]
                # @TODO the spectral image may no longer be correct,
                # if we are forcing or rejecting lines
                for t in rows:
                    if t['disposition'] != 'reject':
                       #print 'keeping %s' % t['uid']
                       # add the columns in order as a single array.
                       # Note the contents of t[] are all unicode strings so
                       # we have to convert to regular strings and floats
                       # as appropriate
                       #print float(t["frequency"]), t["uid"].encode("utf8"), t["formula"].encode("utf8"), t["name"].encode("utf8"), t["transition"].encode("utf8"), float(t["velocity_raw"]), float(t["elower"]), float(t["eupper"]), float(t["linestrength"]), float(t["peakintensity_raw"]), float(t["peakoffset_raw"]), float(t["fwhm_raw"]), t["startchan"], t["endchan"], float(t["peakrms"]), t["blend"]

                       llbdp.addRow(LineData(
                            frequency=float(t["frequency"]), 
                            uid=t["uid"].encode("utf8"), 
                            formula=t["formula"].encode("utf8"),
                            name=t["name"].encode("utf8"), 
                            transition=t["transition"].encode("utf8"), 
                            velocity=float(t["velocity_raw"]),
                            energies=[float(t["elower"]), float(t["eupper"])], 
                            linestrength=float(t["linestrength"]), 
                            peakintensity=float(t["peakintensity_raw"]),
                            peakoffset=float(t["peakoffset_raw"]), 
                            fwhm=float(t["fwhm_raw"]), 
                            chans=[ float(t["startchan"]), float(t["endchan"])], 
                            peakrms=float(t["peakrms"]), 
                            blend=int(t["blend"])))
                llbdp.write(self.dir()+llbdp.xmlFile)

                # all tasks following LineID_AT are now stale.
                self._markstalefrom(taskid)

                # replace the data table in the summary
                titems = self.summaryData.getItemsByTaskID(taskid);
                the_item = titems.get('linelist',None)
                if the_item != None:
                   the_item.getValue()[0] = llbdp.table.serialize()
            
                self.write()

            except Exception, e:
                print "got exception on LineList_BDP write: %s" % e
                traceback.print_exc()
                return
        elif command == "view":
            #print "got command view"
            try:
                fullpath = str(self.dir()+payload["filename"])
                logging.info("Opening file: %s" % fullpath)
                import casa
                axes = {'x':'x','y':'y','z':'z'}
                casa.imview(raster=fullpath,axes=axes)
            except Exception, e:
                print "got exception on viewer launch: %s" % e
                traceback.print_exc()
                return

        elif command == "forcereject":
                taskid = payload["taskid"]
                rows = payload["rows"]
                #if "uuid" in payload:
                #    uid = payload["uuid"]
                #else:
                #    print "couldn't find uuid"
                #    uid=None
                # @TODO the spectral image may no longer be correct,
                # if we are forcing or rejecting lines

                # these are a lists of tuples
                currentforce = self.fm[taskid].getkey('force')
                currentreject = self.fm[taskid].getkey('reject')

                # we append the submitted force/reject to the existing keyword
                for t in rows:
                    if t['disposition'] == 'force':
                       currentforce.append( (float(t["frequency"]), t["uid"].encode("utf8"), t["formula"].encode("utf8"),\
                                    t["name"].encode("utf8"), t["transition"].encode("utf8"), \
                                    float(t["velocity_raw"]), float(t["startchan"]), float(t["endchan"])))
                    elif t['disposition'] == 'reject':
                       if t['frequency'].encode('utf8') == "None":
                           currentreject.append((t['name'].encode('utf8'), None))
                       else:
                           currentreject.append((t['name'].encode('utf8'), float(t['frequency'])))
                    else: # for 'accept' do nothing
                       continue

                # remove duplicates
                currentforce = list(set(currentforce))
                currentreject = list(set(currentreject))

                self.fm[taskid].setkey('force',currentforce)
                self.fm[taskid].setkey('reject',currentreject)
                self._markstalefrom(taskid)
                # in this case the root task is also stale
                self.fm[taskid].markChanged()
                if len(currentforce) != 0:
                    logging.info("Set force = %s for task %d" % (self.fm[taskid].getkey('force'),taskid))
                if len(currentreject) != 0:
                    logging.info("Set reject = %s for task %d" % (self.fm[taskid].getkey('reject'),taskid))
                self.writeXML()
                # don't rewrite the lineIDeditor file because we just want to update the JSON
                # and not lose the user's edits
                #if uid == -1 or uid == '-1': uid = None
                self.summaryData.html(self.dir(), self.fm, self._dotdiagram(), False)
                self.atToHTML()
                self.logToHTML()

        elif command == "exportfits":
            try:
                casaimage = self.dir(str(payload["casaimage"]))
                fitsimage = self.dir(str(payload["fitsimage"]))
                logging.info("exporting CASA image %s to FITS %s" % (casaimage,fitsimage))
                # @todo add a checkbox or something to html to select overwrite 
                # this requires some customization of the input tag, e.g.
                #http://duckranger.com/2012/06/pretty-file-input-field-in-bootstrap/
                #http://www.abeautifulsite.net/whipping-file-inputs-into-shape-with-bootstrap-3/ [bootstrap 3 only]
                #http://stackoverflow.com/questions/11235206/twitter-bootstrap-form-file-element-upload-button
                import casa
                casa.exportfits(casaimage,fitsimage,overwrite=False)
            except Exception, e:
                print "got exception on exportfits: %s" % e
                traceback.print_exc()
                return

        else:
            print "Unrecognized command %s" % command


    def _dotdiagram(self):
        """Returns the default dot diagram file name.

           Parameters
           ----------
           None
        """
        return self.dir()+'admit.png'

    def _markstalefrom(self,taskid):
        """Mark as stale all tasks downstream from given taskid, not including
           the root task.

           Parameters
           ----------
           taskid: int
               The task ID of the root task.

           Returns
           -------
           None 
        """
        nowstale = self.fm.downstream(taskid)
        for tid in nowstale:
            # don't mark the root LineID_AT as stale
            if tid == taskid:
               continue
            # but mark all it's children as stale
            self.fm[tid].markChanged()

    def _serveforever(self):
        """
        Method passed to thread by startDataServer.

        Notes
        -----
        Should not be called directly.
        """
        self._server.serve_forever()

    def setAstale(self, astale, verbose=False, dryrun = False):
        """
        Method to toggle the stale flags on all tasks based on a global admit stale
        for the sole purpose of admit_export to work.  It is dangerous to call this
        routine when not all tasks are either stale or not stale.

        This function needs to be called with True first, so it makes a stale backup,
        then during the 2nd False call, the stale backup is pushed back.
        
        @todo This is a patch solution for admit 1.1 - general solution needed
        """
        cnt0 = len(self.fm._tasks.keys())
        cnt1 = 0  # stale
        cnt2 = 0  # running? (if it did, those crashed)
        cnt3 = 0  # enabled
        if astale:
            self.old = {}
        for t in self:
            if self[t].isstale():  cnt1 += 1
            if self[t].running():  cnt2 += 1
            if self[t].enabled():  cnt3 += 1
            if astale:
                self.old[t] = self[t].isstale()
            
        if dryrun:
            print "ADMIT_STALE: %d/%d were stale ; %d running, %d enabled, current setting is %d" % (cnt1,cnt0,cnt2,cnt3,self.astale)
            return
        if verbose:
            print "ADMIT_STALE: %d/%d were stale ; setting to %d" % (cnt1,cnt0,astale)
        if astale:
            self.astale = 1
            for t in self:
                self[t].markChanged()
        else:
            self.astale = 0
            for t in self:
                if self.old[t]:
                    self[t].markChanged()
                else:
                    self[t].markUpToDate()

if __name__ == "__main__":
    print "MAIN not active yet, but this is where it will go"
