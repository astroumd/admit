Multiflow Projects
==================

Standard ADMIT projects involve the analysis of individual FITS cubes by way
of user-created data flows---pipelines (or trees) composed of `ADMIT tasks`_
(ATs), each manipulating `data products`_ (BDPs) in a well-defined manner. In
some cases, however, one wishes to combine results from several sources or
observations (each with their own unique flow) into a single data flow; e.g.,
to calculate the `OverlapIntegral`_ of several `Moment`_ maps, or to apply a
specific analysis sequence to similar BDPs spanning several projects, without
having to modify each project individually. Projects whose flows involve data
products from multiple projects are called *multiflows* in ADMIT (not to be
confused with `Multiflow Computer <http://www.multiflowthebook.com/>`_, R.I.P.).

Multiflows are constructed by *linking* one or more tasks from other projects
into the multiflow project, thereby allowing any of their outputs to be data
inputs to the flow. Linked tasks always reside at the root of a multiflow and
their own inputs can not be modified (as they are already determined by their
parent flow). In normal flows, by contrast, only ATs taking *no* BDP inputs
(e.g., `Ingest`_) may appear as roots of the flow. Otherwise, multiflows are
constructed and operate similarly to other flows.

At the Python scripting level, a *linked* task is simply a task reference
obtained from an existing AT via a call to its `link()`_ method. One can
then `add()`_ the cloned object to another (now multiflow) project as usual,
except that no source connections may be specified. Note that linking an AT
also locks its parent flow in the sense that no operation resulting in removal
of the original AT (or tasks it depends upon) will be permitted, as this would
render the dependent multiflow project non-functional. Deleting a linked task
from the multiflow project will `unlink()`_ the AT and unlock its parent
project (if it no longer contains any linked tasks).

Data localization in multiflows requires special attention. In normal (uniflow)
projects, all data products are written to a single ADMIT project directory,
typically named in parallel with the corresponding FITS cube at the root of
the flow. If linked ATs are modified in a multiflow (by changing one or more
of their keyword values), the tasks will be re-executed when the flow is run.
Data outputs from linked tasks, however, are always written to their original,
parent project directories. Other tasks in the multiflow write their data to
the *working project* directory, which may be either the multiflow project
directory or a parent project directory as described below. Note that
executing a linked task from a multiflow will mark its dependent tasks (if
any) in the parent project as out of date, but will *not* re-execute them;
this minimizes multiflow run time.

ADMIT supports two basic types of multiflows:

(1) **N-to-1** flows, where data products from *N* projects are combined in
    a single multiflow.

(2) **1-to-N** flows, where a single multiflow is automatically applied to
    compatible data products residing in *N* individual flows.

These are discussed in more detail in the following sections.

N-to-1 Multiflows
-----------------

In this class of multiflows, the project will contain *N* linked ATs at
the root of the flow. It does not matter whether the linked tasks are all
from a single parent project, distinct parents, or somewhere in between,
except that linked ATs from the same parent project should not depend on each
other (unless such ATs are treated read-only in the multiflow). Once added to
the multiflow, the flow can be extended, executed and manipulated like any
other flow. The results of this type of multiflow are written to the multiflow
project directory---i.e., the *working project* is the multiflow project.

1-to-N Multiflows
-----------------

This type of multiflow is essentially a template or generator flow that is
automatically applied to each AT in a list of tasks, as if the user had
manually duplicated and attached the sub-flow to each AT in its parent project.
To construct a template multiflow, one first constructs an *N*-to-1 multiflow 
(where *N* = 1 here), using any one of the ATs present in the task list
(or any AT of compatible type) as the linked AT at the root of the flow.
After the standard *N*-to-1 multiflow is created and (optionally) tested,
the resulting flow can be sequentially applied to a list of tasks (with
arbitrary parent projects) in an automated, batch processing mode.  All tasks
in the list must have output signatures (numbers and types of BDPs) compatible
with the prototype (linked) task used to initiate the multiflow. In batch mode,
the *working project* is the parent project of the current AT and all
associated flow output is written to its originating project directory.
Outside of batch match, executing the flow will direct output to the multiflow
project directory (as for any other *N*-to-1 multiflow).


.. _add():           module/admit/Admit.html#admit.Admit.Admit.add
.. _Admit Tasks:     module/admit/AT.html
.. _data products:   module/admit.bdp/BDP.html
.. _Ingest:          module/admit.at/Ingest_AT.html
.. _link():          module/admit/AT.html#admit.AT.AT.link
.. _Moment:          module/admit.at/Moment_AT.html
.. _OverlapIntegral: module/admit.at/OverlapIntegral_AT.html
.. _unlink():        module/admit/AT.html#admit.AT.AT.unlink

.. sectionauthor:: Kevin P. Rauch <rauch@astro.umd.edu>
