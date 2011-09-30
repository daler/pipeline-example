Example pipeline
================
When writing a bioinformatics pipeline, new functionality or new
parameters are frequently needed.  This repository contains an example of
how one might use the Python pipeline framework ruffus_ to iteratively
develop a pipeline with minimal refactoring.

Python package requirements:

    * pyYAML
    * ruffus
    * HTSeq

Other requirements (must be on the path):

    * FASTX-toolkit
    * bowtie
    * samtools
    * BEDTools

All example data, including fastq files and bowtie indexes, are in the ``test``
directory.

Description
-----------
There are 3 pipelines of increasing complexity.  They are separated into
different directories, ``pipeline-1``, ``pipeline-2``, and ``pipeline-3`` so
they can be easily diffed to see what changes have been made betwen them.

All pipelines share the original data, in the ``test/`` dir.

Each directory contains:

    * a ``ruffus`` pipeline (``pipeline.py``)
    * a config file in YAML format (``config.yaml``)
    * a module of tasks (``tasks.py``)
    * a module of helper functions and classes (``helpers.py``)

Each pipeline is run with::

    ./pipeline.py --config config.yaml -vv

A flowchart can be created with::

    ./pipeline.py --config config.yaml --flowchart flowchart.png


All results data are placed in the ``run1`` subdirectory (this location is
configured in each ``config.yaml`` file).



pipeline-1
~~~~~~~~~~
**pipeline-1** has 2 tasks: mapping, then counting


pipeline-2
~~~~~~~~~~
**pipeline-2** adds an adapter clipping step before mapping.  The changes from
``pipeline-1`` are as follows:

    * An "adapter" parameter was added to the config file

    * The ``clip()`` function was added to ``pipeline-2.py``, and the downsteam
      ``map()`` task in that same file was made to depend on the new ``clip()`` by
      moving the input FASTQ files decorator to ``clip()`` and adding
      a ``@transform`` decorator to ``map()``.

    * The actual work gets done in ``tasks.clip()``; since this function get
      the ``options`` object it will see the adapter that was added to the
      config file, and will clip it.

pipeline-3
~~~~~~~~~~
**pipeline-3** adds the ability to toggle an optional filtering step right
after mapping so that (for example) reads in repetitive regions will be masked
out when counting.  The changes from ``pipeline-2`` are as follows:

    * A "filter bed" parameter was added to the config file

    * Conditional code is added to the pipeline that reads the config file
      and sets up the task flow as needed.  Specifically:

        #. A new task is created that only runs if the "filter" parameter evaluates to True.
        #. The "parent task" is assigned so that the downstream ``count()``
           task will know which one to depend on
        #. The parent and result suffixes are assigned so that result filenames
           encode whether or not filtering occurred.
        #. The arguments to ``count()``'s ``@transform`` decorator are modified
           to use the new variable for parent task, parent suffix, and result
           suffix.

    * The actual work gets done in ``tasks.filter()``.  It deals with the
      awkwardness of converting SAM to BAM so that ``intersectBed`` can work
      with it, and then back again from BAM to SAM so that the pipeline can
      work the same whether or not filtering was requested

Note in particular that the ``count`` task never changes, despite the new
upstream clipping and filtering tasks.  Even though things are happening
upstream (including renaming of file extensions), the ruffus framework
takes care of the dependencies and provides ``count`` with the right files.
All ``count`` needs is a SAM file.

Implementation notes
--------------------

* ``helpers.py`` contains useful functions and classes.  One of these, the
  ``Result`` class, is used to pass information about calls that have been
  made.  It holds input and output files, stdout and stderr, failure codes, the actual
  commands, and a log file.  All of these are optional, since not all tasks
  will need them.

* The ``Result.report`` method prints a nice report for each task, including
  stdout/stderr/commands for debugging if the task failed.

* Functions in ``tasks.py`` return ``Result`` objects that encapsulate all
  the calling information.

* The ``@helpers.timeit`` decorator is used to attach the elapsed time of each
  task to the ``Results`` object it returns.  This can be very helpful when
  benchmarking your pipeline.

* Each function typically takes a config object -- in this case, 
  a dictionary created from the ``config.yaml`` file.  This simplifies calls
  from the pipeline to the tasks module, since you don't have to specify args
  and kwargs differently for each task.

* Each task defined in the ``pipeline.py`` file does minimal work -- typically
  it just passes the input/output files, plus a config object, to the relevant
  ``tasks.py`` task.

.. _ruffus: http://code.google.com/p/ruffus/
