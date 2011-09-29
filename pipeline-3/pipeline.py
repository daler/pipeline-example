#!/usr/bin/python

from ruffus import *
import yaml
import os
import tasks
import helpers

# Config ---------------------------------------------------------------------
# Set up command line option handling, logger creation, and load config file
options = helpers.get_options()
logger_proxy, logging_mutex = helpers.make_logger(options, __file__)
config = yaml.load(open(options.config).read())


def report(result):
    """Wrapper around Result.report"""
    result.report(logger_proxy, logging_mutex)


# Pipeline -------------------------------------------------------------------
@files(list(tasks.fastq_to_other_files(config, extension='.clipped')))
def clip(infile, outfile):
    result = tasks.clip(infile, outfile, config)


@transform(clip, suffix('.clipped'), '.clipped.bowtie.sam')
def map(infile, outfile):
    result = tasks.bowtie(infile, outfile, config)
    report(result)

try:
    filter_bed = config['filter bed']
except KeyError:
    filter_bed = None

if filter_bed is not None:
    @transform(
            map, suffix('.clipped.bowtie.sam'), '.clipped.bowtie.sam.filtered')
    def filter(infile, outfile):
        result = tasks.filter(infile, outfile, config)
        report(result)
    parent_task = filter
    parent_suffix = '.clipped.bowtie.sam.filtered'
else:
    parent_task = map
    parent_suffix = '.clipped.bowtie.sam'


@transform(map, suffix('.bowtie.sam'), '.bowtie.sam.count')
def count(infile, outfile):
    result = tasks.count(infile, outfile, config)
    report(result)
# ----------------------------------------------------------------------------

helpers.run(options)
