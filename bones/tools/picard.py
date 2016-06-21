import os
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
        "dpkg": ["wget", "unzip"]
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
            "echo 'java -jar /usr/local/share/picard/picard.jar $@' >> /usr/local/bin/picard",
            "chmod 755 /usr/local/bin/picard",
        ]
        return script
