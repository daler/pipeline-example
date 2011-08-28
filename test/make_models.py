
import gdc
# see https://github.com/daler/gdc

params = dict(chrom_start=1, chrom='chr1', scalar=50, read_length=25, debug=True)

FASTA = 'example.fasta'
SAM = 'example.sam'
BAM = 'example.bam'
GFF = 'example.gff'
FASTQ = 'example.fastq'

g1 = gdc.GenomeModel(**params)
g2 = gdc.GenomeModel(**params)

modelfns = ['example.model.1', 'example.model.2']
for i, modelfn in enumerate(modelfns):
    i += 1
    g = gdc.GenomeModel(**params)
    model = open(modelfn).read().splitlines(True)
    g.parse(model)

    fout = open(SAM + '.%s' % i, 'w')
    fout.write(g.reads.to_sam(FASTA))
    fout.close()

    fout = open(FASTQ + '.%s' % i, 'w')
    fout.write(g.reads.to_fastq(FASTA))
    fout.close()

    fout = open(GFF, 'w')
    fout.write(g.features.to_gff())
    fout.close()

    import subprocess
    cmds = ['samtools', 'view', '-S', '-b', '-T', FASTA, SAM + '.%s' % i]

    p = subprocess.Popen(
            cmds, stdout=open(BAM + '.%s' % i, 'w'), stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode:
        print stderr
