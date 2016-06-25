import os
from .. package import Package
from .. process import *

class PicardCommand(dict):
    Command = "__command__"

    def __call__(self):
        args = ["%s=%s" for kv in self.items()]
        args = str.join(' ', args)
        cmd = "%s %s" % (self.Command, args)
        os.shell(cmd)

class MarkDuplicates(PicardCommand):
    Command = "MarkDuplicates"

class CollectInsertSizeMetrics(Process):
    Command = "picard-tools"
    Arguments = [
        ProcessArgument(name="command", type=str, required=True, default="CollectInsertSizeMetrics"),
        ProcessArgument(name="HISTOGRAM_FILE", type=str, help="File to write insert size Histogram chart to"),
        ProcessArgument(name="DEVIATIONS", type=float, help="Input paired-end reverse fastq file"),
        ProcessArgument(name="output-pe1", argument="-o", type=str, help="Output trimmed forward fastq file"),
        ProcessArgument(name="output-pe2", argument="-p", type=str, help="Output trimmed reverse fastq file"),
        ProcessArgument(name="pe-combo", argument="-c", type=bool, help="Interleaved input paired-end fastq"),
        ProcessArgument(name="output-combo", argument="-m", type=bool, help="Output interleaved paired-end fastq file"),
        ProcessArgument(name="output-combo-all", argument="-M", type=bool, help="Output interleaved paired-end fastq file including discarded reads"),
        ProcessArgument(name="qual-type", argument="-t", type=str, default="sanger", required=True, help="Quality score type [solexa | illumina | sanger]"),
        ProcessArgument(name="output-single", argument="-s", type=str, help="Output trimmed singles fastq file"),
        ProcessArgument(name="qual-threshold", argument="-q", type=int, default=20, help="Threshold for trimming based on average quality in a window"),
        ProcessArgument(name="length-threshold", argument="-l", type=int, default=20, help="Threshold to keep a read based on length after trimming"),
        ProcessArgument(name="no-fiveprime", argument="-x", type=bool, help="Don't trim from 5'"),
        ProcessArgument(name="gzip-output", argument="-g", type=bool, help="Output gzipped files"),
        ProcessArgument(name="truncate-n", argument="-n", type=int, help="Truncate the first N bases of every read"),
    ]

class PackagePicard(Package):
    PackageName = "picard"
    Depends = {
        "dpkg": ["wget", "unzip"],
        "packages": ["java"]
    }
    Version = "2.4.1"

    def script(self):
        script = [
            "cd /usr/local/share",
            "wget https://github.com/broadinstitute/picard/releases/download/${PKG_VERSION}/picard-tools-${PKG_VERSION}.zip",
            "unzip picard-tools-${PKG_VERSION}.zip",
            "rm picard-tools-${PKG_VERSION}.zip",
            "ln -s picard-tools-${PKG_VERSION} picard-tools",
            "echo '#!/usr/bin/env bash' > /usr/local/bin/picard",
            "echo 'java ${PICARD_JVM} -jar /usr/local/share/picard-tools/picard.jar $@' >> /usr/local/bin/picard",
            "chmod 755 /usr/local/bin/picard",
        ]
        return script

def build_barcode_file(dd):
    header = ["barcode_sequence_1", "barcode_sequence_2", "barcode_name", "library_name"]
    content = str.join('\t', header) + '\n'
    for sample in dd.sample_sheet.data:
        row = [sample["index"], sample["index2"], sample["Sample_ID"], dd.runinfo["Run"]["Id"]]
        content += str.join('\t', row) + '\n'
    return content

def build_multiplex_file(dd, outdir=None, lane=1):
    # Header
    header = ["OUTPUT_PREFIX", "BARCODE_1", "BARCODE_2"]
    content = str.join('\t', header) + '\n'
    # Undetermined
    prefix = "Undetermined_S0_L%03d" % lane
    if outdir:
        prefix = os.path.join(outdir, prefix)
    row = [prefix, "N", "N"]
    content += str.join('\t', row) + '\n'
    # Samples
    for (idx, sample) in enumerate(dd.sample_sheet.data):
        prefix = "%s_S%d_L%03d_R" % (sample["Sample_ID"], idx + 1, lane)
        if outdir:
            prefix = os.path.join(outdir, prefix)
        row = [prefix, sample["index"], sample["index2"]]
        content += str.join('\t', row) + '\n'
    return content

#path = "/home/giles/data/160602_M04168_0018_000000000-AU0H8/"
#path = "/home/giles/data/151106_M04168_0003_000000000-AHK4J"
"""
dd = DataDirectory(path)
outdir = "/tmp/barcodes"
if not os.path.exists(outdir):
    os.mkdir(outdir)

barcodes_txt = "/tmp/barcodes/barcodes.txt"
metrics_txt = "/tmp/barcodes/metrics.txt"
multiplex_txt = "/tmp/barcodes/multiplex.txt"

with open(barcodes_txt, 'w') as fh:
    fh.write(build_barcode_file(dd))

with open(multiplex_txt, 'w') as fh:
    fh.write(build_multiplex_file(dd, outdir=outdir))

arguments = [
    "ExtractIlluminaBarcodes",
    "BASECALLS_DIR=%s" % dd.basecalls_path,
    "LANE=1",
    "RS=%s" % build_read_structure(dd),
    "BARCODE_FILE=%s" % barcodes_txt,
    "METRICS_FILE=%s" % metrics_txt,
    "NUM_PROCESSORS=0", 
    "OUTPUT_DIR=%s" % outdir,
]

cmd = plumbum.cmd.picard[arguments]
print cmd
print(cmd())

arguments = [
    "IlluminaBasecallsToFastq",
    "BASECALLS_DIR=%s" % dd.basecalls_path,
    "LANE=1",
    "RS=%s" % build_read_structure(dd),
    "BARCODES_DIR=%s" % outdir,
    "MULTIPLEX_PARAMS=%s" % multiplex_txt,
    "NUM_PROCESSORS=0",
    "MACHINE_NAME=%s" % dd.runinfo["Instrument"],
    "FLOWCELL_BARCODE=%s" % dd.runinfo["Flowcell"],
    "RUN_BARCODE=%s" % dd.runinfo["Run"]["Number"],
    "MAX_READS_IN_RAM_PER_TILE=100000",
]

cmd = plumbum.cmd.picard[arguments]
cmd = cmd.with_env(JAVA_TOOL_OPTIONS="-Xmx8G")
print cmd
print(cmd())
"""
