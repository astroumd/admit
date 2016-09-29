:orphan:

Examples of various rst directives
===================================
`Here's a cheatsheet. <http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html>`_

.. comment lines are lines that start with .. and have no directive (see below) as first word

Code
----

Example:

.. code:: python

  import parser
  b = parser.Parser("myfile.xml")

.. code:: python

  def my_function():
      "just a test"
      print 8/2

end example.

Include a python file:


.. literalinclude:: ../../admit/test/admit4.py
   :language: python
   :linenos:



end include

Math
----

.. math::
  (project_{out},AT_{out},BDP_{out},project_{in},AT_{in},BDP_{in})


Image
-----

.. image:: images/connection.png
    :scale: 50 %

Figure
------

A figure

.. figure:: images/connection.png
    :height: 283 px
    :width: 443 px
    :scale: 110 %
    :alt:  Example Flow.
    :align: center

    **Figure 1:** The connection in this diagram connects two ATs, `a1` and `a2`,
    inside a single project `p0`.   The output BDP of `a1` is an
    input BDP of `a2`, i.e., :math:`b1 \equiv b2`.   A given output
    BDP may be the input to an arbitrary number of ATs, but can be the
    output one and only one AT.   For virtual projects, the first and
    fourth indices in the tuple, `i1` and `i2`, would differ.
.. this doesn't work and in fact makes the entire figure disappear
..    :target: `Figure 1`_

Notes, See Also, Todo
---------------------

.. note:: This is a note box.  I have found that you have to end the note with a ".." comment indicator on the following line or the note absorbed everything below it at the same indent level.
..

Normal text here.

..  spaces matter a lot. Lists and indentations are determined by it.

Design Style AT1
----------------

*Description*

A description of purpose of this AT.

*Use Case*

At least one example use case that demonstrates how this AT
fits in a typical flow.

*Input BDPs*

Description of input BDP(s), but note that the detailed contents of the BDPs are described elsewhere.

* **SomeName1_BDP** - bla bla

* **SomeName2_BDP** - bla bla

*Input Keywords*

Description of required and optional keywords.

* **key1** - bla bla

* **key2** - bla bla

*Output BDPs*

Description of output BDP(s), and their optional output graphics. The
naming convention of output BDP(s) is also useful to add here, as they
are normally automated (some AT's allow you to set them explicitly).

* **SomeName1_BDP** - bla bla 
* **SomeName2_BPD** - bla bla

*Procedure*

The procedure the AT uses to achieve its goals.


*CASA Tasks Used*

What CASA tasks (or tools) it uses.

* **task1** - bla bla
* **task2** - bla bla
* **tool3** - bla bla

Design Style AT2
----------------

 *Description*

 Some description. 

 *Use Case*

 Some use case

 *Input BDPs*

 * **SomeName1** - bla bla

 * **SomeName2** - bla bla

 *Input Keywords*

 * **key1** - bla bla

 * **key2** - bla bla

 *Output BDPs*
 
 * **SomeName1** - bla bla 
 
 * **SomeName1** - bla bla

 *Procedure*

 The procedure

 *CASA Tasks Used*

 * **task1** - bla bla
 * **task2** - bla bla

User Guide Examples
-------------------

And here we will add some user guide examples.

.. toctree::

   casapython

   
.. seealso:: This is a see-also box.

.. todo:: This is a to-do box. (why is it not in a box??)

