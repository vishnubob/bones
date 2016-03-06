import os
from . process import *

__all__ = ["FastQC"]

class FastQC(Process):
    Command = "fastqc"
    Arguments = [
        ProcessArgument(name="outdir", argument="-o", type=str, required=True, help="Output directory"),
        ProcessArgument(name="seqfiles", required=True, type=list, help="One or more sequence files to process"),
    ]
