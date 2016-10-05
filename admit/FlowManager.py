""".. _FlowManager-api:

   **Flow** --- Project task flow manager.
   ---------------------------------------

   This module defines the FlowManager class.
"""

import copy, sys, types
import admit

# ==============================================================================

class FlowManager():
    """ Manages the flow of data products between ADMIT tasks.

        The flow manager maintains the tree of ADMIT tasks (ATs) constituting
        a data flow. Tasks communicate through basic data products (BDPs)
        that flow between tasks, which combine and transform them into new
        BDPs according to their function. This class implements the bookkeeping
        to track task connections and inter-dependencies. A central concept
        is the task connection 4-tuple, ``(si, sp, di, dp)``, connecting a
        source task (ID ``si``) output BDP (port ``sp``) to a destination
        task (ID ``di``) input BDP (port ``dp``). The primary concern of the
        flow manager is to organize and maintain this connection information
        to permit efficient execution and modification of data flows.

        The flow manager includes limited functionality supporting
        self-modifying variadic flows (variflows). In a variflow, at least one
        AT produces a variable number of outputs, whether from instance to
        instance or between runs of the same instance. This presents a problem
        for defining the sub-flow emanating from a variadic AT, as every
        concrete flow must assume a fixed number of outputs from each AT to
        define the connection map. To support variflows, the flow manager will
        automatically clone or prune (disable) sub-flows attached to the
        variadic output ports of an AT, each time the AT is executed, according
        to the actual number of BDPs present. When additional parallel
        sub-flows are needed, the sub-flow(s) attached to the *first* variadic
        output port is cloned and connected to the new, extra outputs. (If 
        the port already has *any* ATs attached to it, the existing sub-flow(s)
        are enabled but no cloning is performed.) If fewer sub-flows are
        needed, the excess tasks are simply disabled (i.e., not removed).

        Parameters
        ----------
        connmap : triple-nested dictionary of 4-tuples, optional
            Initial value of the `_connmap` attribute
            (defaults to an empty dictionary).

        bdpmap : dictionary of list of 2-tuples, optional
            Initial value of the `_bdpmap` attribute
            (defaults to an empty dictionary).

        depsmap : dictionary of sets, optional
            Initial value of the `_depsmap` attribute
            (defaults to an empty dictionary).

        varimap : double-nested dictionary of list of sets, optional
            Initial value of the `_varimap` attribute
            (defaults to an empty dictionary).

        tasklevs : dictionary of int, optional
            Initial value of the `_tasklevs` attribute
            (defaults to an empty dictionary).

        tasks : dictionary of task references, optional
            Initial value of the `_tasks` attribute
            (defaults to an empty dictionary).


        Attributes
        ----------
        _connmap : triple-nested dictionary of 4-tuples
            Organizes connection 4-tuples in a 3-level dictionary hierarchy;
            `_connmap[si][di][dp]` is a connection 4-tuple ``(si, sp, di, dp)``
            connecting source task ID ``si``, BDP output port ``sp``, to
            destination task ``di``, input ``dp``.

        _bdpmap : dictionary of list of 2-tuples
            Relates BDP outputs from source tasks with the BDP inputs to
            connected destination tasks; `_bdpmap[di]` is a list of 2-tuples
            ``(si, sp)``, one for each BDP input port, describing the source
            of the corresponding BDP.

        _depsmap : dictionary of sets
            Maintains the task dependency levels needed by the `run()`_ method;
            `_depsmap[level]` is the set of task IDs residing at the
            dependency ``level``. Lower level tasks must execute prior to
            higher level tasks to satisfy dependency requirements; tasks at the
            same level may be executed in any order (even concurrently).

        _varimap : double-nested dictionary of list of sets
            Tracks variadic sub-flows and their controlling (variadic) root
            task; `_varimap[si][sp]` is a list of sub-flow task IDs, each 
            stored as a set (one per sub-flow), emanating from task ID ``si``,
            (variadic) output port ``sp``.

        _tasklevs : dictionary of int
            Maintains task dependency information in a complementary (inverse)
            manner to `_depsmap`; `_tasklevels[id]` is the dependency level
            for task ``id``.

        _tasks : dictionary of task references
            Holds references to all ADMIT tasks in the flow, keyed by task id;
            `_tasks[id]` is an ADMIT task reference.

        _aliases : 2-tuple of dictionary of task aliases
            Reserved alias registry, keyed by alias base name (index 0) or AT
            type (index 1). For index 0, the value is an integer count of
            aliases created with that base name; for index 1, it is the number
            of default aliases created for ATs of that type. In both cases, the
            duplicate aliases are appended with '@N' for some integer N.
            Not present in XML.

        _taskid : int
            Task ID counter, used to ensure unqiue task IDs within the flow.
            Not present in XML.

        Notes
        -----
        All internal state is kept up to date by `add()`_ and `remove()`_
        so that it is valid at all times. Hence `_connmap`, `_depsmap`, etc.
        should never be modified by any other methods, either inside or
        outside of FlowManager (the leading underscore emphasizes this
        intent).

        .. _add():    #admit.FlowManager.FlowManager.add
        .. _remove(): #admit.FlowManager.FlowManager.remove
        .. _run():    #admit.FlowManager.FlowManager.run
    """

    def __init__(self, connmap=None, bdpmap=None, depsmap=None, varimap=None,
                       tasklevs=None, tasks=None):
        """Constructor.
        """
        # _connmap: nested dictionary of connection tuples (si,sp,di,dp).
        # _connmap[si][di][dp] is a connection tuple of the form (si,sp,di,dp):
        #
        #   si is the source      task ID:          tasks[si];
        #   sp is the source      task output port:   bdp_out[sp];
        #   di is the destination task ID:          tasks[di];
        #   dp is the destination task input  port:   bdp_in[dp];
        #
        # The nested structure allows for efficient searching.
        self._connmap = {} if connmap == None else connmap

        # _bdpmap: Task source to destination BDP port dictionary.
        # _bdpmap[id] is a list of source connections for each BDP input.
        #
        # For example, _bdpmap[3] = [(1,0), (2,3)] means:
        #  Task #3, BDP input 0 comes from task #1, BDP output 0
        #  Task #3, BDP input 1 comes from task #2, BDP output 3
        #
        # The _bdpmap[id] list is the same as the stuples argument to add()
        # for task #id. This structure is essentially the inverse of connmap
        # and is used to efficiently manage connection changes due to
        # add()/remove().
        self._bdpmap = {} if bdpmap == None else bdpmap

        # _depsmap: dictionary of task dependency levels.
        # _depsmap[lev] is a set of task IDs sharing dependency level lev.
        #
        # For example: { 0:set([1, 2]), 1:set([3, 4]) }
        # Level 0 tasks (IDs 1 and 2) execute first (maybe in parallel)
        # Level 1 tasks (IDs 3 and 4) execute next  (maybe in parallel)
        self._depsmap = {} if depsmap == None else depsmap

        # _varimap: nested dictionary of variadic sub-flows.
        # _varimap[si][sp] is a list of set of task IDs for each sub-flow.
        #
        # For example: { 0:{0:[set([1]), set([2])]}, 1:{2:[set([3, 4])]} }
        # Task IDs 0 and 1 are variadic.
        # Task 0 controls two variflows, each with one (managed) task attached
        #        to (variadic) BDP output port 0.
        # Task 1 controls one variflow with two tasks, at least attached
        #        to (variadic) BDP output port 2.
        self._varimap = {} if varimap == None else varimap

        # _tasklevs: task dependency level dictionary.
        # _tasklevs[id] is the dependency level for task ID #id.
        #
        # This structure is essentially the inverse of _depsmap and is used
        # to efficiently manage dependency changes due to add()/remove().
        self._tasklevs = {} if tasklevs == None else tasklevs

        # _tasks: task dictionary.
        # _tasks[id] is a reference to the AT task ID #id.
        self._tasks = {} if tasks == None else tasks

        # _aliases: task alias dictionary.
        self._aliases = ({},{})

        # Task ID counter.
        self._taskid = 0


    def _find_id(self, index, unique=True):
        """
        Converts logical index to task ID.

        Indexing by alias name or task ID is supported.
        This interface converts to a task ID. If the alias is not unique in the
        flow, an exception is thrown.

        Parameters
        ----------
        index : int or str
            Task ID number or alias name.

        unique : bool, optional
            Whether precisely one match is allowed (otherwise, the first found
            is returned).

        Returns
        -------
        int
            Task ID number.
        """
        if type(index) == types.StringType:
          matches = self.find(lambda at: at._alias == index)
          if not matches or (len(matches) > 1 and unique):
            raise Exception("Found %d matches for alias '%s' in flow" %
                            (len(matches), index))
          else:
            return matches[0].id()
        else:
          return index


    def __len__(self):
        """Number of tasks under control of FlowManager.

           Returns
           -------
           int
               Number of tasks in the flow (including any disabled tasks).
        """
        return len(self._tasks)


    def __contains__(self, index):
        """Flow tasks membership operator.

           Parameters
           ----------
           index : int or str
               Task ID number or alias name.

           Returns
           -------
           bool
               Membership result.
        """
        return self._tasks.__contains__(self._find_id(index))


    def __iter__(self):
        """Flow tasks iterator.

           Returns
           -------
           iterator
               Task iterator.
        """
        return iter(self._tasks)


    def __getitem__(self, index):
        """Gets flow task reference.

           Parameters
           ----------
           index : int or str
               Task ID number or alias name.

           Returns
           -------
           AT
               ADMIT task reference.
        """
        return self._tasks[self._find_id(index)]


    def __setitem__(self, index, value):
        """Sets new flow task.

           Parameters
           ----------
           index : int or str
               Task ID number or alias name.

           value : AT
               Task reference.

           Returns
           -------
           None

           Notes
           -----
           This is a low-level method and must not be used directly by external
           users.
        """
        self._tasks[self._find_id(index)] = value


    def __delitem__(self, index):
        """Deletes flow task.

           Parameters
           ----------
           index : int or str
               Task ID number or alias name.

           Returns
           -------
           None

           Notes
           -----
           This is a low-level method and must not be used directly by external
           users.
        """
        self._tasks.__delitem__(self._find_id(index))

    def __str__(self):
        for k,v in self._tasks.iteritems():
            print v
        return ""

    def run(self, dryrun=False):
        """ Executes the flow, but only tasks that are out of date.

            Runs all stale, enabled tasks in the correct order, accounting for
            their inter-dependencies. This will reduce to a no-op for tasks
            whose outputs are up-to-date (not dependent on stale tasks). The
            (global) project summary is updated on-the-fly as tasks are
            executed and must contain a valid Summary object on entry.

            Parameters
            ----------
            dryrun : bool, optional
                Whether to perform a dry run (else a live run); defaults to
                ``False``.

            Returns
            -------
            None
        """
        if dryrun: self.dryrun()

        for dl in self._depsmap.values():
          # Tasks at each level are independent and could be run in parallel.
          # For now, run them in task ID order for the sake of predictability.
          dl = list(dl)
          dl.sort()
          for si in dl:
            task = self._tasks[si]
            if task.isstale() and task.enabled():
              # Set BDP input arguments.
              args = []
              for conn in self._bdpmap[si]:
                args.append(self._tasks[conn[0]][conn[1]])

              # Run task.
              self.stale(si, True)
              task.execute(args)

              # Update project summary.
              summary = task.summary()
              for key in summary:
                admit.Project.summaryData.insert(key,summary[key])

              # Update variadic flows.
              vm = self._varimap
              if si in vm and vm[si]:
                # Variadic output port range.
                bport = len(task._valid_bdp_out) - 1
                eport = len(task._bdp_out)

                # Delete obsolete, managed sub-flows.
                # Exception: prototype (port 0) sub-flows are enabled/disabled.
                for sp in vm[si]:
                  if sp >= eport and sp != 0:
                    for flow in vm[si][sp]:
                      for di in flow:
                        if di in self: self.remove(di)
                        if di in vm: del vm[di]
                  else:
                    for flow in vm[si][sp]:
                      for di in flow:
                        self[di].enabled(sp < eport)
                        if di in self._varimap:
                          for tid in self.downstream(di):
                            self[tid].enabled(sp < eport)

                for sp in vm[si].keys():
                  if sp > 0 and sp >= eport: del vm[si][sp]

                # Clone new sub-flows onto dangling output ports.
                # Prototype flows must be attached to *first* variadic output.
                if bport in self._varimap[si]:
                  for sp in range(bport+1, eport):
                    if sp not in self._varimap[si]:
                      for flow in self._varimap[si][bport]:
                        # idmap relates original task IDs to cloned task IDs.
                        # Process tasks in dependency order to fill this.
                        idmap = {}
                        tasks = list(flow)
                        tasks.sort(key=lambda tid: self._tasklevs[tid])

                        for di in tasks:
                          task = self[di].copy()

                          # Shift connections attached to variadic outputs
                          # and translate cloned task IDs.
                          stuples = []
                          for tup in self._bdpmap[di]:
                            sat = self[tup[0]]
                            if tup[0] in idmap: tup = (idmap[tup[0]], tup[1])
                            if len(sat._bdp_out_zero) == 1 and sat._variflow \
                               and tup[1] >= len(sat._valid_bdp_out)-1:
                              tup = (tup[0], tup[1] + sp-bport)
                            stuples.append(tup)

                          idmap[di] = self.add(task, stuples)

                          # For variadic clones, replicate their variflows.
                          if di in self._varimap:
                            vid = idmap[di]
                            self._varimap[vid] = {}
                            for dp in self._varimap[di]:
                              self._varimap[vid][dp] = []
                              for vflow in self._varimap[di][dp]:
                                self._varimap[vid][dp].append(set())
                                for tid in vflow:
                                  task = self[tid].copy()
                                  stuples = []
                                  for tup in self._bdpmap[tid]:
                                    if tup[0] in idmap:
                                      tup = (idmap[tup[0]], tup[1])
                                    stuples.append(tup)
                                  idmap[tid] = self.add(task, stuples)
                                  self._varimap[vid][dp][-1].add(idmap[tid])


    def connectInputs(self):
        """
        Connects input BDPs to all tasks in the flow.

        Connections are made regardless of whether tasks are out of date or
        disabled. Missing inputs are ignored. This method also updates the
        stale flag on each task.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for dl in self._depsmap.values():
          for d in dl:
            # Set BDP input arguments (if available).
            task = self._tasks[d]
            task.clearinput()
            for conn in self._bdpmap[d]:
              src = self._tasks[conn[0]]
              if conn[1] < len(src) and src[conn[1]] is not None:
                task.addinput(src[conn[1]])

            # Update stale flag for child tasks.
            if task.isstale(): self.stale(d, True)


    def dryrun(self):
        """Performs a dry run.

           Dry runs provide a summary of which tasks are in the flow,
           which are stale (out-of-date), and the order in which they will be
           executed in a live run.

           Returns
           -------
           None
        """
        counter = 0
        for t in self._tasks:
            at = self._tasks[t]
            print 'AT', counter, "(id %d)" % t, "=", at._type
            for bin in at._bdp_in:
                print "BDP input:", bin._type
            for bout in at._bdp_out:
                print "BDP output:", bout._type
            print
            counter = counter + 1


    def inFlow(self, a, stuples = None):
        """
        Determines whether a compatible task exists in the flow.

        A task is compatible with another if:
        1. It has the identical concrete type.
        2. It has the same task ID.
        3. It has identical source connections (if supplied).

        Parameters
        ----------
        a : ADMIT task
            Task reference.

        stuples : list of 2-tuples, optional
            List of source connection 2-tuples, one per BDP input port
            (default `None` bypasses the connection check).

        Returns
        -------
        True if a compatible task exists in the flow, else False.

        See Also
        --------
        add
        """
        if a.id() in self._tasks:
          if type(a) == type(self[a.id()]):
            if stuples == None or stuples == self._bdpmap[a.id()]:
              return True

        return False


    def add(self, a, stuples = None, dtuples = None):
        """Appends or inserts an AT into the task flow.

           Appending a task creates a new leaf---a task whose BDP outputs (if
           any) are not connected to any tasks; in this case, `dtuples` can
           be omitted. Insertion implies that one or more of the tasks's
           outputs feeds back into the flow, in which case `dtuples` will be
           non-empty.

           Parameters
           ----------
           a : AT
               ADMIT task to append/insert into the flow.

           stuples : list of 2-tuples, optional
               List of source connection 2-tuples, one per BDP input port.  For
               example, ``[(si0,sp0), (si1,sp1)]`` if the task requires two BDP
               inputs, the first (input port 0) from task ``si0``, BDP output
               ``sp0`` and the second (input port 1) from task ``si1``, BDP
               output ``sp1``. Defaults to `None` (no upstream tasks).

           dtuples : list of 4-tuples, optional
               List of destination connection 4-tuples ``(si, sp, di, dp)``.
               The number of connections varies but will be zero for leaf
               (i.e., appended) tasks. The source task ID in these tuples must
               match the input task ID ``a.id``, as it is the source for all
               `dtuples` connections. For example, [(1, 0, 2, 1), (1, 0, 3, 2)]
               if this task (id #1) disseminates its BDP output (port 0) to
               two downstream task inputs (#2 port 1 and #3 port 2). Defaults
               to `None` (no downstream tasks).

           Returns
           -------
           int
               Input task ID on success, else -1 (error detected).

           See Also
           --------
           remove
           replace

           Notes
           -----
           Usually all but the root task(s) will have a non-empty `stuples`
           list.

           As a convenience, in the ``stuples`` and ``dtuples`` arguments the
           task alias may be used in place of the integer task ID. Also, for 
           the ``stuples`` argument (only), a destination port of zero may be
           omitted (implied); i.e., ``(si, 0)`` may be replaced with ``si`` (or
           the alias name).
        """
        errstr = "ERROR: FlowManager.add():"

        # Converts alias names to task id in a list of tuples.
        # The implementation preserves project IDs within literal task IDs.
        def norm_tuples(tuples):
          rtn = []
          for t in tuples:
            if type(t) == types.TupleType:
              t0 = self[t[0]].id() if type(t[0]) == types.StringType else t[0]
              if len(t) == 2:
                rtn.append((t0, t[1]))
              else:          
                t2 = self[t[2]].id() if type(t[2]) == types.StringType else t[2]
                rtn.append((t0, t[1], t2, t[3]))
            else:
              if type(t) == types.StringType: t = self[t].id()
              rtn.append((t, 0))

          return rtn

        # Assign flow-unique task ID and alias.
        if not a.getProject():
          a.setAlias(self._aliases)
          a.newId(self._taskid)
          self._taskid += 1

        # Convenience values.
        bm, cm, dm = self._bdpmap, self._connmap, self._depsmap
        tl = self._tasklevs

        # Loop over stuples (the sources of BDP inputs to this task).
        di, dp = a._taskid, 0
        lv = 0
        bm[di] = []
        siset = set([])
        for t in ([] if stuples is None else norm_tuples(stuples)):
            si, sp = t
            siset.add(si)

            # Check source task is valid.
            if not si in self:
              print errstr, "no source task %d." % si
              return -1

            # This sequence reliably populates the triple-nested dictionary.
            if not cm.has_key(si): cm[si] = {}
            if not cm[si].has_key(di): cm[si][di] = {}
            cm[si][di][dp] = (si, sp, di, dp)
            dp += 1

            # Save source ports for dependency management.
            bm[di].append(t)

            # Track task dependency level.
            if lv <= tl[si]: lv = tl[si] + 1

        # Add AT to task list.
        self._tasks[a._taskid] = a

        # Set dependency level.
        if not dm.has_key(lv): dm[lv] = set()
        dm[lv].add(di)
        tl[di] = lv

        # New variflow root?
        if len(a._bdp_out_zero) == 1 and a._variflow:
          if dtuples:
            msg = "Cannot insert (only append) variadic AT."
            admit.logging.error(msg)
            raise Exception(msg)
          else:
            self._varimap[di] = {}

        # Variadic subflow containing the new task (if any).
        # vi = (controlling task ID, task output port, subflow)
        vi = (-1, -1, set([di]))

        # Attach subflow if task is directly connected to a variadic AT port.
        for si in siset & set(self._varimap.keys()):
          if vi[0] < 0 or tl[si] < tl[vi[0]]:
            vat = self[si]
            vp  = len(vat._valid_bdp_out) - 1

            # Determine associated (highest-numbered) source port.
            sp = -1
            conn = self._connmap[si][di]
            for dp in conn:
              sport = conn[dp][1]
              if sport > sp: sp = sport

            if sp >= vp:
              if vi[0] < 0:
                if si not in self._varimap:     self._varimap[si] = {}
                if sp not in self._varimap[si]: self._varimap[si][sp] = []

              self._varimap[si][sp].append(vi[2])
              vi = (si, sp, self._varimap[si][sp][-1])

        # Merge variflows connected through the new task.
        for si in self._varimap:
          # vp is the first (base) variadic port number
          vp  = len(self[si]._valid_bdp_out) - 1

          # sport is the highest numbered port directly attached to task di
          sport = -1
          if si in cm and di in cm[si]:
            for dp in cm[si][di]:
              if cm[si][di][dp][1] > sport:
                sport = cm[si][di][dp][1]

          for sp in self._varimap[si]:
            for flow in self._varimap[si][sp]:
              if (siset & flow) and (vi[1] < 0 or vi[1] == sp) \
                                and (vi[1] < 0 or sport >= vp) \
                                and flow is not vi[2]:
                if vi[0] < 0 or tl[si] < tl[vi[0]]:
                  # Previous flow merges into current one.
                  flow.update(vi[2])
                  vi[2].clear()
                  vi = (si, sp, flow)
                else:
                  # Current flow merges into previous one.
                  vi[2].update(flow)
                  flow.clear()

            # Remove any merged (cleared) flow slots.
            i = 0
            for flow in self._varimap[si][sp]:
              if not flow: del self._varimap[si][sp][i]
              else:        i += 1

        # Check for recursion.
        dtuples = [] if dtuples is None else norm_tuples(dtuples)
        leaf = set()
        for t in dtuples: leaf.add(t[2])
        if not self.downstream(di, leaf):
          print errstr, "task", di, "introduces recursion."
          return -1

        # Loop over dtuples (the destinations of BDP outputs from this task).
        for t in dtuples:
            si, sp, di, dp = t

            # Check destination task is valid.
            if di not in self:
              print errstr, "no destination task %d." % di
              return -1

            # Remove existing connection.
            t0  = bm[di][dp]
            si0 = t0[0]
            cm[si0][di].pop(dp)
            if not len(cm[si0][di]): cm[si0].pop(di)

            # Add new connection.
            if not cm.has_key(si): cm[si] = {}
            if not cm[si].has_key(di): cm[si][di] = {}
            cm[si][di][dp] = t
            bm[di][dp] = (si, sp)

            # Update dependency level if necessary.
            if tl[di] <= lv:
                for tid in self.downstream(di):
                    # Remove old level.
                    l0 = tl[tid]
                    dm[l0].remove(tid)
                    if not len(dm[l0]): dm.pop(l0)

                    # Increment dependency level.
                    l1 = l0 + 1
                    tl[tid] = l1
                    if not dm.has_key(l1): dm[l1] = set()
                    dm[l1].add(tid)

        return a._taskid


    def remove(self, id, keepRoot = False, delFiles = True):
        """ Removes an AT and its downstream tasks.

            Deletes an entire sub-flow starting from the specified root task.

            Parameters
            ----------
            id : int
                Task ID of root AT to be removed.

            keepRoot : bool, optional
                Whether to preserve the root AT, `id`, and remove only its
                descendents.

            delFiles : bool, optional
                Whether to delete BDP data when removing tasks.

            Returns
            -------
            None

            See Also
            --------
            add
            replace

            Notes
            -----
            This method does *not* remove any variflow-related metadata as this
            would disrupt the flow management performed by veriflows
            themselves. User removal of tasks within variadic flows is only
            supported via editing and re-running of script files.
        """
        # Convenience values.
        bm, cm, dm = self._bdpmap, self._connmap, self._depsmap
        tl = self._tasklevs

        for si in self.downstream(id):
            if keepRoot and si == id: continue

            # Remove task as BDP connection source.
            cm.pop(si, None)

            # Remove task as BDP connection destination.
            for t in bm[si]:
                si0 = t[0]
                if cm.has_key(si0):
                    cm[si0].pop(si, None)
                    if not len(cm[si0]): cm.pop(si0)

            # Remove output BDPs.
            for bdp in self[si]:
                if bdp is not None:
                    bdp.delete(delFiles)

            # Remove any summary information.
            admit.Project.summaryData.delItemsByTaskID(si)

            # Remove task and its flow metadata.
            self._tasks.pop(si)
            dm[tl[si]].remove(si)
            if not dm[tl[si]]: dm.pop(tl[si])
            tl.pop(si)
            bm.pop(si)


    def replace(self, id, a, stuples = None):
        """ Replaces one task with another, removing the original.

            The replacement task must have the same output signature (i.e,
            produce the same types/number of output BDPs)---otherwise the
            existing task could not be removed---but `stuples` may be specified
            if the inputs differ.

            Parameters
            ----------
            id : int
                Task ID of AT to be removed.

            a : AT
                Task to insert into the flow.

            stuples : list of 2-tuples, optional
                Source connection 2-tuples ``(si, sp)`` for `a`. The special
                default value None indicates that the existing task's sources
                should be reused verbatim.

            Returns
            -------
            None

            See Also
            --------
            add
            remove
        """
        # Matching input signature by default.
        if stuples == None: stuples = self._bdpmap[id]

        # Form new destination connections list.
        dtuples = []
        if self._connmap.has_key(id):
          for di in self._connmap[id].keys():
            for t in self._connmap[id][di].values():
              dtuples.append( (a._taskid, t[1], t[2], t[3]) )

        # Add the new task, then remove the old one.
        self.add(a, stuples, dtuples)
        self.remove(id)


    def clone(self, id, flow = None, idmap = None):
        """ Clones the flow emanating from a given root task (included).

            Creates an independent, parallel sub-flow duplicating the
            action of the original. If `flow` is `None`, the sub-flow emanating
            from task `id` (inclusive) is duplicated. Otherwise, the sub-flow 
            defined by `flow = (fm, tid)`, where `fm` is a FlowManager instance
            and task `tid` (contained in `fm`) is the root of the sub-flow, is
            duplicated and spliced into the current flow, using task `id` as
            its root instead---i.e., task `tid` is identified with `id` and the
            tasks *following* `tid` are cloned and appended to `id`. In the
            latter case, task `id` is *not* duplicated; the new sub-flow is
            merely appended to it. 

            Parameters
            ----------
            id : int
                Task ID of the existing sub-flow root task.

            flow : 2-tuple, optional
                Tuple (fm, tid) describing an external sub-flow; `fm` is a 
                FlowManager object and `tid` the ID of a task within it.

            idmap : dict of int key-values, optional
                Dictionary mapping root task IDs in `flow` to corresponding
                tasks in `self`.
                
            Returns
            -------
            int
                Task ID of the new (possibly cloned) root task.

            Notes
            -----
            If an external `flow` is provided that is not autonomous (i.e.,
            one or more of its ATs receives inputs from ATs outside the
            sub-flow), the `idmap` argument is required and must map task IDs
            from `flow` to `self` for all ATs outside the sub-flow. This
            informs the method how to identify parent tasks between flows.
        """
        # Copy external flow/id?
        fid = (self, id) if flow is None else flow

        # Convenience values.
        bm, cm = fid[0]._bdpmap, fid[0]._connmap

        # Follow flow, cloning and adding tasks.
        # The idmap translates original to cloned task IDs;
        #   root holds the task IDs of the current-level sub-flow root(s)
        #   dups holds the task IDs of already duplicated sub-flow ATs
        if idmap is None: idmap = {}
        root = set([fid[1]])
        dups=set([])
        while len(root):
          # Leaf tasks are those immediately dependent on current root(s).
          leaf = set()

          for si in root:
            if si in dups: continue

            if cm.has_key(si): leaf.update(cm[si].keys())

            # Create cloned source BDP map.
            # Only source IDs present in idmap require updating.
            stuples = []
            for t in bm[si]:
              if t[0] in idmap:
                # Cloned BDP input connection.
                t = (idmap[t[0]], t[1])
              else:
                # BDP input lies outside of the (external) sub-flow.
                if fid[0] is not self and si != fid[1]:
                  raise Exception, "clone: input sub-flow is not autonomous"

              stuples.append(t)

            if flow is None or si != fid[1]:
              # Duplicate task and add to current flow.
              task = fid[0]._tasks[si].copy()
              task.baseDir(self._tasks[id].baseDir())
              idmap[si] = self.add(task, stuples)
              dups.add(si)
            else:
              # Root task not duplicated between flows.
              idmap[si] = id

          root = leaf

        return idmap[fid[1]]


    def find(self, isMatch):
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
        Tasks at the same dependency level are scanned in an unspecified order.
        (Such tasks are all independent of each other.)

        Examples
        --------
        To find all ATs with ID less than 100 in flow `fm`:

        >>> fm.find(lambda at: at.id() < 100)
        """
        matches = []
        for level in self._depsmap:
          for tid in self._depsmap[level]:
            task = self._tasks[tid]
            if isMatch(task): matches.append(task)

        return matches


    def downstream(self, id, leaf = None):
        """ Determines the ATs downstream of a task (includes itself).

            The downstream tasks constitute the sub-flow emanating from the
            specified root task (also considered part of the sub-flow).

            Parameters
            ----------
            id : int
                Root task ID.

            leaf : set of int, optional
                Initial set of leaf task IDs.

            Returns
            -------
            set
                Set of AT task IDs (including the root, `id`) on success,
                else an empty list if recursion is detected.

            Notes
            -----
            Recursion through task `id` is detected. This is used by **add()**
            to prevent the creation of cyclic flows.
        """
        cm = self._connmap

        # Collect the set of downstream tasks, one level at a time.
        if leaf is None: leaf = set()
        flow = set()
        root = set([id])
        while len(root):
            flow.update(root)

            for si in root:
              if cm.has_key(si): leaf.update(cm[si].keys())

            if id in leaf: return []  # Recursion through id.
            root = leaf
            leaf = set()

        return flow


    def show(self):
        """Displays formatted internal FlowManager state.

           Pretty-prints the current contents of the instance to the screen
           (standard output).

           Returns
           -------
           None
        """
        print "\n======== Begin FlowManager State ========"
        print "\n---- Connection map ----"
        for si in self._connmap:
            for di in self._connmap[si]:
                print "Task %d => %d:" % (si, di), self._connmap[si][di]

        print "\n---- BDP map ----"
        for id in self._bdpmap:
            print "Task %d:" % id, self._bdpmap[id]

        print "\n---- Dependency map ----"
        for i in self._depsmap:
            print "Level %d:" % i, self._depsmap[i]

        print "\n---- Variflow map ----"
        for si in self._varimap:
          for sp in self._varimap[si]:
            print "Task %d port %d:" % (si, sp), self._varimap[si][sp]

        print "\n---- Tasks (level) ----"
        for tid in self:
            task = self[tid]
            attr = "[stale" if task.isstale() else ""
            if not task.enabled():
              attr += ("[" if not attr else ",") + "disabled"
            if task.id() in self._varimap:
              attr += ("[" if not attr else ",") + "variadic"
            if attr: attr += "]"
            print "Task %d (%d):" % (tid, self._tasklevs[tid]), \
                  self[tid]._type, "- '%s' " % self[tid]._alias, attr
            print "  BDP  in:    map =", task._bdp_in_map
            for bdp in self[tid]._bdp_in:
                if bdp != None:
                    print "    [Name: %s Type: %s Uid: %d Tid: %d]" % (bdp.show(), bdp._type, bdp._uid, bdp._taskid)
            print "  BDP out:    map =", task._bdp_out_map
            for bdp in self[tid]._bdp_out:
                if bdp != None:
                    print "    [Name: %s Type: %s Uid: %d Tid: %d]" % (bdp.show(), bdp._type, bdp._uid, bdp._taskid)
            print

        print "======== End FlowManager State ========"


    def showsetkey(self,outfile=None):
        """ Display keysettings for all tasks, meant to be used to
            write a template file for rerunning an admit
        """
        fp = outfile and open(outfile,'w') or sys.stdout
        fp.write("# Default keywords in this flow:\n\n")
        for tid in self:
            fp.write("\n")
            stale ="[stale]" if self[tid].isstale() else "" 
            fp.write("### Task %d (%d): %s %s\n" % (tid,  self._tasklevs[tid], self[tid]._type,stale))
            fp.write("#   BDP name info could be displayed here too....\n\n")
            for key in self[tid]._keys.keys():
                val = self[tid]._keys[key]
                if type(val) == type('str'):
                    if len(val) == 0:  val = "''"
                msg = "# a[%d].setkey('%s'," % (tid,key) + str(val) + ")"
                fp.write("%s\n" % msg)
        fp.write("\n")
        if fp is not sys.stdout:
            fp.close()
        
    def verify(self):
        """ Verifies the internal state of the FlowManager.

            Verification searches for internal inconsistencies in the flow
            bookkeeping, which to improve runtime efficiency is partially
            redundant.

            Returns
            -------
            bool
                ``True`` if the FlowManager state is valid, else ``False``.
        """
        ok = True
        errstr = "ERROR: FlowManager.verify():"

        # Convenience values.
        bm, cm, dm = self._bdpmap, self._connmap, self._depsmap
        tl = self._tasklevs

        # Check tasks exist precisely once in the dependency map and levels.
        # This will detect cyclic flows among other things.
        nTasks = 0
        for dl in dm.values(): nTasks += len(dl)
        if nTasks != len(self._tasks) or nTasks != len(tl):
          print errstr, "Task count mismatch: " \
                "%d tasks, %d in _depsmap, %d in _tasklevs." \
                % (len(self._tasks), nTasks, len(tl))
          ok = False

        for id in self._tasks:
          if id != self._tasks[id]._taskid:
            print errstr, "Task ID mismatch: " \
                  "tasks[%d] ID is %d."  % (id, self._tasks[id]._taskid)
            ok = False

          if not tl.has_key(id):
            print errstr, "Task %d is not in _tasklevs." % id
            ok = False
            continue

          if not id in dm[tl[id]]:
            print errstr, "Task %d is not in _depsmap level %d." % (id, tl[id])
            ok = False

        # Check consistency of _connmap and _bdpmap.
        for di in bm:
          dp = 0
          for si, sp in bm[di]:
            if not cm.has_key(si):
              print errstr, "Task %d is not a source in _connmap." % si
              ok = False
              continue

            if not cm[si].has_key(di):
              print errstr, "Task %d is not a destination of %d in _connmap." \
                    % (di, si)
              ok = False
              continue

            if not cm[si][di].has_key(dp):
              print errstr, "Task %d input %d is not a destination" \
                    "of %d in _connmap." % (di, dp, si)
              ok = False
              continue

            conn = (si, sp, di, dp)
            if cm[si][di][dp] != conn:
              print errstr, "Connection mismatch: found %s, expected %s." \
                    % (cm[si][di][dp], conn)
              ok = False

            dp += 1

        for si in cm:
          for di in cm[si]:
            for dp in cm[si][di]:
              t = cm[si][di][dp]
              sp = t[1]
              if t[0] != si or t[2] != di or t[3] != dp:
                print errstr, "Connection mismatch: found %s, expected %s." \
                      % (t, (si, sp, di, dp))
                ok = False

              if not (bm.has_key(di) and len(bm[di]) > dp):
                print errstr, "BDP connection %s not found." % ((di, dp),)
                ok = False
              else:
                if bm[di][dp] != (si, sp):
                  print errstr, "BDP connection %s mismatch: " \
                        "found %s, expected %s." \
                        % ((di, dp), bm[di][dp], (si, sp))
                  ok = False

        if ok : print "FlowManager.verify(): okayed %d tasks." % nTasks
        return ok


    def stale(self, id, direct = True):
        """ Sets the stale flag of an AT and its downstream ATs.

            Stale tasks will be re-run upon execution of the flow, updating
            their output BDPs in the process; tasks not so marked are skipped
            to minimize running time.

            Parameters
            ----------
            id : int
                Root task ID.

            direct : bool, optional
                Whether to mark only direct descendants stale (else the entire
                sub-flow); defaults to ``True``.

            Returns
            -------
            None
        """
        if direct:
            if self._connmap.has_key(id): flow = self._connmap[id].keys()
            else:                         flow = []
            flow.append(id)
        else:                             flow = self.downstream(id)

        for i in flow: self._tasks[i].markChanged()


    def diagram(self, dotfile):
        """ Generates dot (graphviz) diagram for the current flow.

            Parameters
            ----------
            dotfile : str
                Output dot file name.

            Returns
            -------
            None
        """
        dot = open(dotfile, mode='w')
        dot.write("digraph flow {\n")

        # Loop over tasks in dependency order and connect them in the diagram.
        # The loop logic is similar to that in run().
        for dl in self._depsmap.values():
          # Try to improve repeatability by sorting IDs.
          dl = list(dl)
          dl.sort(key=lambda tid0: self._tasklevs[tid0])

          # These colors are intended to match those
          # in the cascading style sheet for the html view
          # in etc/resources/css/admit.css.  They can be slightly
          # different shades if the flow is variadic or not (which is
          # not tracked in html view).
          for tid in dl:
            task  = self._tasks[tid]
            if task.id() in self._varimap:
              if task.running():
                color = "#bf080f"
              elif task.enabled():
                color = "darkorange" if task.isstale() else "#99dd99"
              else:
                color = "#d06080" if task.isstale() else "#d07070"
            else:
              if task.running():
                color = "#cf181f"
              elif task.enabled():
                color = "orange" if task.isstale() else "#aaeeaa"
              else:
                color = "#e07090" if task.isstale() else "#e08080"

            dot.write(
            '  task%d [shape=box,style="rounded,filled",color="%s",label="%s\\n\'%s\'"]\n' \
            % (tid, color, task._type.replace("_AT",""), task._alias) 
            )

            for conn in self._bdpmap[tid]:
              dot.write(
                '  task%d -> task%d [style=bold,fontsize=9,label=" %d"];\n' \
                % (conn[0], tid, conn[1])
              )

        dot.write("}\n")
        dot.close()


    def script(self, py, proj = 'p', tcube = None):
        """
        Generates a Python script recreating the current flow.

        Parameters
        ----------
        py : file
            Open, writable Python file object.

        proj : str, optional
            Project variable name; defaults to 'p'.

        tcube : int, optional
            Task ID of Ingest_AT to set input file=cubefile; defaults to `None`.

        Returns
        -------
        None

        Notes
        -----
        This is a low-level method normally called only by Admit.script().
        """
        if len(self) == 0: return

        py.write("\n# Flow tasks.\n")

        # Loop over tasks in dependency order and connect them in the script.
        # The loop logic is similar to that in run().
        idmap = {}
        n = 0
        for dl in self._depsmap.values():
          # To increase regularity, order by ID number.
          dl = list(dl)
          dl.sort()

          for tid in dl:
            task  = self[tid]
            idmap[tid] = n  # Renumber task IDs sequentially.

            # Determine non-default keywords.
            exec("at = admit.%s()" % task._type)
            keys = at._keys.keys()
            keys.sort()
            if task.isAutoAlias():
              args= "" 
              sep = ""
            else:
              args= "alias='%s'" % task._alias
              sep = ", "
            if task._variflow != at._variflow:
              args += sep + 'variflow=' + repr(task._variflow)
              sep = ", "
            for key in keys:
              if task.getkey(key) != at.getkey(key):
                args += sep + key + "="
                if tid == tcube and key == 'file':
                  args += 'cubefile'
                else:
                  args += repr(task.getkey(key))
                sep = ", "

            # Simplify input tuples.
            # Use task alias when defined, otherwise the task ID.
            tuples = ""
            sep = ""
            for t in self._bdpmap[tid]:
              alias = self[t[0]]._alias
              t0 = 't' + str(idmap[t[0]]) if self[t[0]].isAutoAlias() else \
                   repr(alias)
              if t[1] == 0: tuples += sep + t0
              else:         tuples += sep + '(' + t0 + ',' + str(t[1]) + ')'
              sep = ", "

            py.write(
            "t%-2d = %s.addtask(admit.%s(%s)" % (n, proj, task._type, args)
            )
            py.write(")\n" if tuples == "" else ", [%s])\n" % tuples)

            n += 1


    def sameLineage(self, tid, tid0, flow0, twins, match):
        """
        Determines whether two tasks in different flows have identical ancestry.

        Ancestry is determined by the type and number of parents, the
        associated port connections, and likewise for all grandparents, etc.

        Parameters
        ----------
        tid : int
            Task ID in current flow.

        tid0 : int
            Task ID in `flow0`.

        flow0 : FlowManager
            Flow in which to search for matching task.

        twins : dict of ints
            Mapping of previously matched task IDs in `flow0` (keys) to
            corresponding IDs in the current flow (values).

        match : int (or None)
            Current best-match task ID in `flow0` known to have lineage
            compatible with `tid`.

        Returns
        -------
        bool
            Whether `tid0` task has lineage compatible with `tid` and is the
            better-matching task (compared to `match`).

        Notes
        -----
        - Fix stale setting when parent keywords have changed *between flows*,
          even though each task is individually up to date.
        """
        tid1 = tid0 if match is None else match

        # The set of all tasks to compare for common ancestry.
        ancestors = set([(tid0, tid1, tid)])
        score = 0

        while ancestors:
          tup = ancestors.pop()
          if flow0[tup[0]]._type != self[tup[2]]._type: return False
          if tup[0] != tup[1]:
            if self[tup[2]].bestMatch(flow0[tup[0]], flow0[tup[1]]) == tup[0]:
              score += 1
            else:
              score -= 1

          bmap0 = flow0._bdpmap[tup[0]]
          bmap1 = flow0._bdpmap[tup[1]]
          bmap  =  self._bdpmap[tup[2]]

          # Check source connections match.
          if len(bmap0) != len(bmap): return False
          for i in range(len(bmap0)):
            if bmap0[i][1] != bmap[i][1]: return False
            ancestors.add((bmap0[i][0], bmap1[i][0], bmap[i][0]))

        # Everything matched (superior to `match`)...
        return score >= 0


    def findTwin(self, tid, flow0, twins):
        """
        Attempts to find corresponding task in another flow.

        For tasks to correspond they must be of identical types with identical
        lineage. The latter means that the two tasks have identical parents
        (the same number of inputs connected to the same ports on tasks of
        identical type), grandparents, etc.

        Parameters
        ----------
        tid : int
            Task ID in current flow.

        flow0 : FlowManager
            Flow in which to search for matching task.

        twins : dict of ints
            Mapping of previously matched task IDs in `flow0` (keys) to
            corresponding IDs in the current flow (values).

        Returns
        -------
        int or None
            Valid `flow0` task ID on success, else ``None``.
        """
        # Common ancestry implies corresponding tasks always occupy the same
        # dependency level. This greatly reduces the search domain.
        level = self._tasklevs[tid]
        if level in flow0._depsmap:
          match = None
          for tid0 in flow0._depsmap[level]:
            if not twins.has_key(tid0):
              # Find all tasks with same ancestors; return the closest match.
              if self.sameLineage(tid, tid0, flow0, twins, match):
                match = tid0
            elif twins[tid0] == tid:
              return tid0

          return match


    def mergeTasks(self, summary, flow0, summary0, twins, final):
        """
        Merges task settings from another flow.

        Compares the tasks in `flow0` to `self`; tasks of the same type, 
        at the same dependency level and with equivalent BDP input trees, are
        identified and relevant settings transferred into the current flow.
        Any task in the current flow which cannot be matched with a `flow0`
        task according to these criteria is passed unaltered. Each task in
        `flow0` may be merged with at most one task in the current flow.

        Parameters
        ----------
        summary : SummaryData
            Summary data for current flow.

        flow0 : FlowManager
            Flow from which to merge task stale settings.

        summary0 : SummaryData
            Original summary data for `flow0`.

        twins : dict of ints
            Task IDs of all known pairs of identified (merged) tasks.

        final : bool
            Whether this will be the last call to this method for the current
            flow. If so, any unattached variflow branches will be merged.

        Returns
        -------
        None

        Notes
        -----
        This is a low-level method normally called only by Admit.mergeFlow().

        In support of incremental flow construction, it is permissible to merge
        a flow multiple times; individual tasks will be merged at most once.
        """
        def addSummary(tid0, tid1):
            entries = summary0.getItemsByTaskID(tid0)
            for key in entries:
              value = entries[key]
              if type(value) == types.ListType:
                for entry in value:
                  entry = copy.copy(entry)
                  if entry.taskid == tid0:
                    entry.setTaskID(tid1)
                    summary.insert(key,entry)
              else:
                entry = copy.copy(value)
                entry.setTaskID(tid1)
                summary.insert(key,entry)

        for level in self._depsmap:
          for tid in self._depsmap[level]:
            task = self[tid]
            tid0 = self.findTwin(tid, flow0, twins)

            if tid0 is not None:
              if not twins.has_key(tid0):
                task.merge(flow0[tid0], self._aliases)
                twins[tid0] = tid
                addSummary(tid0, task.id(True))
                  
        if final:
          # Process auto-generated aliases. This is done after all tasks
          # have been processed to minimize gratuitous reassignments
          # (which force tasks to be marked stale).
          for tid0 in twins:
            task0 = flow0[tid0]
            task = self[twins[tid0]]
            if task.isAutoAlias(compat=task0._alias):
              task.freeAlias(self._aliases)
          #
          for tid0 in twins:
            task0 = flow0[tid0]
            task = self[twins[tid0]]
            if task.isAutoAlias(compat=task0._alias):
              if task.setAlias(self._aliases, task0._alias) != task0._alias:
                task.markChanged()

          # Check for new tasks in protoype variadic sub-flows. If present,
          # mark the root stale so the sub-flows are recomputed. This assumes
          # the script contains *only* protoype flows; if re-running a script,
          # the user must manually add the task to *all* branches present.
          #
          for si in flow0._varimap:
            if si in twins and 0 in flow0._varimap[si] \
                           and 0 in self._varimap[twins[si]]:
              # Tasks in the new prototype flow.
              proto = set()
              for subflow in self._varimap[twins[si]][0]: proto |= subflow
              #
              for subflow in flow0._varimap[si][0]:
                for tid in subflow:
                  if tid in twins: proto.discard(twins[tid])
              #
              # If there are new (unmatched) tasks, mark the root stale so
              # that the variadic branches have a chance to regenerate.
              if proto: self[twins[si]].markChanged()

          # Process variadic sub-flows.
          for si in flow0._varimap:
            # Can't reintroduce tasks if the variadic root has disappeared!
            if si in twins:
              root = self[twins[si]]
              for sp in flow0._varimap[si]:
                for subflow in flow0._varimap[si][sp]:
                  # Subflow task IDs are in a set (unordered) but need to 
                  # be added in dependency order to maximize success.
                  tids = list(subflow)
                  tids.sort(key=lambda tid0: flow0._tasklevs[tid0])

                  for tid0 in tids:
                    if not twins.has_key(tid0):
                      if not sp:
                        # Missing tasks from the prototype flow? The user
                        # deleted them. To be safe, mark the root stale so the
                        # sub-flows get repopulated from the new prototype,
                        # and don't transfer the outdated sub-flows (below).
                        root.markChanged()
                      elif not root._stale:
                        # Reintroduce task iff all required inputs exist.
                        stuples = []
                        for stuple0 in flow0._bdpmap[tid0]:
                          if twins.has_key(stuple0[0]):
                            # Translate input to new flow.
                            stuples.append((twins[stuple0[0]], stuple0[1]))
                          else:
                            break

                        if len(stuples) == len(flow0._bdpmap[tid0]):
                          # Ok, all inputs present.
                          task = flow0[tid0]
                          twins[tid0] = self.add(task, stuples)
                          addSummary(tid0, task.id(True))
