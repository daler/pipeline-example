import time
import datetime
import os
import sys
import subprocess
import yaml
from helpers import Result, timeit


def fastq_to_other_files(config, extension):
    """
    Generates input/output files for each sample `extension`.  This is the
    primary mapping to go from fastq to analyzed data.

    output dirs are also created if necessary.

    extension can be a list

    """
    if isinstance(extension, basestring):
        extension = [extension]
    for sample in config['samples']:
        infile = sample['fastq']
        outdir = os.path.join(config['output dir'], sample['label'])
        if not os.path.exists(outdir):
            os.system('mkdir -p %s' % outdir)
        stub = os.path.join(outdir, sample['label'])
        outfiles = []
        for ext in extension:
            # add dot if needed
            if ext[0] != '.':
                ext = '.' + ext
            outfiles.append(stub + ext)
        if len(outfiles) == 1:
            outfiles = outfiles[0]
        yield infile, outfiles


@timeit
def bowtie(fastq, outfile, config):
    """
    Use bowtie to map `fastq`, saving the SAM file as `outfile`.  Ensures that
    '--sam' is in the parameters.
    """
    index = config['index']
    params = config['bowtie params'].split()
    if ('--sam' not in params) and ('-S' not in params):
        params.append('-S')

    cmds = ['bowtie']
    cmds.extend(params)
    cmds.append(index)
    cmds.append(fastq)
    print outfile
    logfn = outfile + '.log'
    p = subprocess.Popen(
            cmds, stdout=open(outfile, 'w'), stderr=open(logfn, 'w'),
            bufsize=1)
    stdout, stderr = p.communicate()
    return Result(
            infiles=fastq, outfiles=outfile, cmds=' '.join(cmds), log=logfn)


@timeit
def count(samfile, countfile, config):
    """
    Call htseq-count on the sam file, creating a table of read counts per gene
    """
    cmds = ['htseq-count']
    cmds += config['htseq params'].split()
    cmds += [samfile,
            config['gff']]
    p = subprocess.Popen(
            cmds, stdout=open(countfile, 'w'),
            stderr=subprocess.PIPE, bufsize=1)
    stdout, stderr = p.communicate()
    failed = p.returncode
    return Result(
            infiles=samfile,
            outfiles=countfile,
            stderr=stderr,
            failed=failed,
            cmds=' '.join(cmds))
