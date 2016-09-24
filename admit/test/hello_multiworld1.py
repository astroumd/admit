#!/usr/bin/env python
#
# Hello multiworld (type 1) test script.
#
# Run unittest_multiflow1.py first to create projects p1, p2;
# otherwise no tasks will be found and the script will fail.
#
import admit
import admit.at as at

# Create multiflow project.
mflow = admit.Project("mflow")
pm    = mflow.getManager()

# Add projects with tasks to link.
proj1 = pm.addProject("p1")
proj2 = pm.addProject("p2")

# Find some tasks and link them into the multiflow.
stuples = []
#
ats = pm.findTaskAlias(proj1, "at1")
tid = mflow.addtask(ats[0])
stuples.append((tid, 0))

ats = pm.findTaskAlias(proj2, "at2")
tid = mflow.addtask(ats[0])
stuples.append((tid, 0))

# Combine outputs from the linked tasks into a new task.
tid = mflow.addtask(at.FlowN1(file="FlowN1.dat", touch=True), stuples)

# Process the multiflow.
mflow.run()
mflow.write()
