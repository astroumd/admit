"""**Manager** --- Multiflow project manager.
   ------------------------------------------

   This module defines the ProjectManager class.
"""
import os
import admit
from admit.Admit import Admit as Project

# ==============================================================================

class ProjectManager():
    """
    Manages parent projects feeding a multiflow project.

    Parameters
    ----------
    baseDirs: list of str
        Starting parent project directories.

    Attributes
    ----------
    _projects: dict of ADMITs
        Parent project dictionary, keyed by project ID (a positive integer).

    _baseDirs: dict of project base directories
        Project directory dictionary, keyed by project ID (a positive integer).

    Notes
    -----
    Managed projects are numbered sequentially beginning with one.
    A project ID of zero is reserved for the parent project containing this
    instance. Individual projects can be accessed by indexing the manager
    object using the corresponding project ID number.
    """
    def __init__(self, baseDirs=[]):
        """
        Constructor.
        """
        self._projects = {}
        self._baseDirs = {}
        for d in baseDirs: self.addProject(d)


    def __len__(self):
        """
        Number of projects under control of ProjectManager.

        Returns
        -------
        int
            Number of contained projects.
        """
        return len(self._projects)


    def __contains__(self, pid):
        """
        Project membership operator.

        Parameters
        ----------
        pid : int
            Project ID number.

        Returns
        -------
        bool
            Membership result.
        """
        return self._projects.__contains__(pid)


    def __iter__(self):
        """
        Project iterator.

        Returns
        -------
        iterator
            Project iterator.
        """
        return iter(self._projects)


    def __getitem__(self, pid):
        """
        Obtains project reference.

        Parameters
        ----------
        pid : int
            Project ID number.

        Returns
        -------
        ADMIT object
            ADMIT project reference.
        """
        return self._projects[pid]


    def __setitem__(self, pid, project):
        """
        Sets new project.

        Parameters
        ----------
        pid : int
            Project ID number.

        project : ADMIT project
            Project reference.

        Returns
        -------
        None
        """
        # Check if pid exists...
        for at in project.fm: at.setProject(pid)
        self._projects[pid] = project


    def addProject(self, baseDir):
        """
        Adds a project.

        The project must be completely up to date to be accepted.

        Parameters
        ----------
        baseDir : str
            ADMIT project base directory.

        Returns
        -------
        int
            Project ID number, else -1 if the project was rejected
            (not up-to-date).

        Notes
        -----
        The up-to-date requirement is a safety feature. Managed projects are
        assumed to be quasi-static since tasks linked from it must provide
        valid BDP output at the root of the associated multiflow.
        """
        # Ignore attempts to re-add same project.
        # This will commonly occur when re-running a multiflow script.
        for pid in self._baseDirs:
          if baseDir == self._baseDirs[pid]: return pid

        #project = admit.Project(baseDir)
        project = Project(baseDir)
        stale = project.fm.find(lambda at: at.isstale() == True)
        if not stale:
          pid = 1+len(self._projects)
          project.project_id = pid
          self._projects[pid] = project
          self._baseDirs[pid] = baseDir

          # Embed project ID in tasks to indicate project ownership.
          for tid in project.fm: project.fm[tid].setProject(pid)
        else:
          print "PM.addProject(): Project", baseDir, \
                "out of date; not added."
          pid = -1

        return pid


    def removeProject(self, pid):
        """
        Removes a project.

        The project should not have any tasks still linked in the multiflow.
        Verifying this is the responsibility of the caller (multiflow project).

        Parameters
        ----------
        pid : int
            Project ID number.

        Returns
        -------
        bool
            True if the project was removed successfully, else False.

        Notes
        -----
        This is a low-level interface not normally called by users.
        """
        if pid in self:
            self[pid].write()  # Commit any unsaved changes.
            self._projects.pop(pid)
            return True
        else:
            print "PM.removeProject: Unknown project ID", pid
            return False


    def write(self):
        """
        Writes project XML files.

        Project IDs are temporarily reset to zero to avoid polluting
        the parent project XML files.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        Parent projects should be rewritten when a multiflow is run in case
        linked tasks were updated.
        """
        for pid in self:
          project = self[pid]
          project.project_id = 0
          for tid in project.fm: project.fm[tid].setProject(0)

          project.write()
          project.project_id = pid
          for tid in project.fm: project.fm[tid].setProject(pid)


    def getProjectId(self, baseDir):
        """
        Retrieves project ID number given the base directory.

        Parameters
        ----------
        baseDir: str
            Project base directory.

        Returns
        -------
        int
            Project ID number, else -1 if project not found.
        """
        for pid in self:
          if self._baseDirs[pid] == baseDir: return pid

        return -1


    def getProjectDir(self, pid):
        """
        Retrieves project base directory given its ID number.

        Parameters
        ----------
        pid: int
            Project ID number.

        Returns
        -------
        str
            Project base directory, else None if project not found.
        """
        if pid in self:
            return self._baseDirs[pid]
        else:
            return None


    def findTask(self, pid, isMatch):
        """
        Finds AT(s) by arbitrary matching criterion.

        Parameters
        ----------
        pid: int
            ADMIT project ID number.

        isMatch: bool functor(AT)
            Match function (returns True/False given an AT argument). 

        Returns
        -------
        list of ATs
            ADMIT task reference(s) matching the criterion; may be empty.
        """
        return self[pid].fm.find(isMatch)


    def findTaskAlias(self, pid, alias):
        """
        Finds AT(s) by alias.

        Parameters
        ----------
        pid: int
            ADMIT project ID number.

        alias: str
            Matching task alias.

        Returns
        -------
        list of ATs
            ADMIT task reference(s) matching the alias; may be empty.
        """
        return self.findTask(pid, lambda at: at._alias == alias)


    def script(self, py, baseDir, proj = 'p'):
        """
        Generates a Python script recreating the current project manager.

        Parameters
        ----------
        py : file
            Open, writable Python file object.

        baseDir : str
            Master project base directory (ending in '/').

        proj : str, optional
            Project variable name; defaults to 'p'.

        Returns
        -------
        None

        Notes
        -----
        This is a low-level method normally called only by Admit.script().
        """
        if len(self) == 0: return

        baseDir = os.path.dirname(baseDir[:-1])
        py.write("\n# Managed projects.\n"
                 "pm = %s.getManager()\n" % proj)
        pids = self._baseDirs.keys()
        pids.sort()
        for pid in pids:
          pdir = self[pid].dir()[:-1]
          ht = os.path.split(pdir)
          if ht[0] == baseDir: pdir = ht[1]
          py.write("pm.addProject('%s')\n" % pdir)
