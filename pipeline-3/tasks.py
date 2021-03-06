import time
import datetime
import os
import sys
import subprocess
import yaml
import tempfile
from helpers import Result, timeit


def fastq_to_other_files(config, extension):
    """
    generates input/output files for each sample
    `extension`.  This is the primary mapping to go from fastq to analyzed
    data.

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


@timeit
def clip(fastq, clipped_fastq, config):
    adapter = config['adapter']
    clipping_report = clipped_fastq + '.clipping_report'
    if adapter is None:
        fout = open(clipped_fastq, 'w')
        fout.write(open(fastq).read())
        fout.close()

        fout = open(clipping_report, 'w')
        fout.write(
                'No adapter specified; %s is a copy of %s' % (
                    clipped_fastq, fastq))
        fout.close()
        return Result(
                fastq, (clipped_fastq, clipping_report))

    cmds = ['fastx_clipper',
            '-i', fastq,
            '-o', clipped_fastq,
            '-n',  # *keep* Ns
            '-a', adapter,
            '-v',  # report to stdout
            ]
    p = subprocess.Popen(
            cmds, stdout=open(clipping_report, 'w'), stderr=subprocess.PIPE,
            bufsize=1)
    stdout, stderr = p.communicate()
    failed = False
    if p.returncode or not os.path.exists(clipped_fastq):
        failed = True

    return Result(
            fastq, (clipped_fastq, clipping_report), stdout=stdout,
            stderr=stderr, failed=failed, cmds=' '.join(cmds))


def sam2bam(sam, bam):
    cmds = ['samtools',
            'view',
            '-S', '-b',
            sam]
    p = subprocess.Popen(
            cmds, stdout=open(bam, 'w'), stderr=subprocess.PIPE, bufsize=1)
    stdout, stderr = p.communicate()
    return Result(sam, bam, stderr=stderr, cmds=' '.join(cmds))


def bam2sam(bam, sam):
    cmds = ['samtools',
            'view', '-h',
            bam]
    p = subprocess.Popen(
            cmds, stdout=open(sam, 'w'), stderr=subprocess.PIPE, bufsize=1)
    stdout, stderr = p.communicate()
    return Result(sam, bam, stderr=stderr, cmds=' '.join(cmds))


@timeit
def filter(sam, outfile, config):
    bam = tempfile.mktemp()
    filtered_bam = tempfile.mktemp()

    result0 = sam2bam(sam, bam)

    cmds1 = ['intersectBed',
            '-abam', bam,
            '-b', config['filter bed'],
            '-v']

    p = subprocess.Popen(
            cmds1, stdout=open(filtered_bam, 'w'),
            stderr=subprocess.PIPE, bufsize=1)
    stdout1, stderr1 = p.communicate()
    result2 = bam2sam(filtered_bam, outfile)
    #os.unlink(bam)
    #os.unlink(filtered_bam)
    failed = p.returncode
    cmds = '\n'.join([result0.cmds, ' '.join(cmds1), result2.cmds])
    stderr = '\n'.join([result0.stderr, stderr1, result2.stderr])
    return Result(
            sam, outfile, failed=failed, cmds=cmds, stderr=stderr)
