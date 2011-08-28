Example pipeline
================
When writing a bioinformatics pipeline, new functionality or new
parameters are frequently needed.  This repository contains an example of
how one might use the Python pipeline framework ruffus_ to iteratively
develop a pipeline with minimal refactoring.

Requirements:  pyYAML, ruffus and HTSeq Python packages; FASTX-toolkit, bowtie,
samtools, and BEDTools all need to be on the path.

Description
-----------
There are 3 pipelines of increasing complexity.  They are separated into
different directories so they can be easily diffed to see what changes
have been made.  All pipelines share the original data, in the `test/`
dir.

Each directory contains a `ruffus` pipeline, `pipeline.py`, a config file
in YAML format, `config.yaml`, and a module of tasks, `tasks.py`.

Each pipeline is run with::

    ./pipeline.py --config config.yaml -vv

A flowchart can be created with::

    ./pipeline.py --config config.yaml --flowchart flowchart.png


All results data are placed in the `run1` subdirectory (this location is
configured in each `config.yaml` file).

* **pipeline-1** has 2 tasks: mapping, then counting

* **pipeline-2** adds an adapter clipping step before mapping.

    * an "adapter" parameter is added to the config file

    * a `clip` pipeline task is added, and the downsteam `map` task is
      made to depend on the new `clip`

    * the actual work gets done in `tasks.clip()`


* **pipeline-3** adds the ability to toggle an optional filtering step to
  pipeline-2, right after the mapping step and before the counting step.

    * a "filter bed" parameter is added to the config file

    * conditional code is added to the pipeline that reads the config file
      and sets up the task flow as needed

    * the actual work gets done in `tasks.filter()` (with some awkwardness
      of converting SAM to BAM so that `intersectBed` can work with it,
      and back again from BAM to SAM so that the pipeline can work the
      same whether or not filtering is requested

Note in particular that the `count` task never changes, despite the new
upstream clipping and filtering tasks.  Even though things are happening
upstream (including renaming of file extensions), the ruffus framework
takes care of the dependencies and provides `count` with the right files.
All `count` needs is a SAM file.

Implementation notes
--------------------

Functions in `tasks.py` return `Result` objects, which contain info about
the calls that have been made (input and output files, stdout and stderr,
failure codes, the actual commands, and a log file -- all optional).  

Each function also typcially takes a config object, in this case,
a dictionary created from the `config.yaml` file.  This simplifies calls
from the pipeline to the tasks module.

Each pipeline task does minimal work -- typically it just passes the
input/output files, plus a config object, to the relevant task.


.. _ruffus: http://code.google.com/p/ruffus/
