import os
import operator
import subprocess

from .. utils import *
from .. process import *

__all__ = ["FreeBayes"]

class FreeBayes(object):
    def __init__(self, reference):
        self.reference = reference

    def call(self, bamfn, output=None, ploidy=1, **args):
        args = args if args != None else dict()
        if ploidy and "-p" not in args:
            args["-p"] = ploidy
        args = list(map(str, reduce(operator.add, args.items(), tuple())))
        cmd = ["freebayes", "-f", self.reference] + args + [bamfn]
        if output == None:
            output = os.splitext(bamfn)[0] + ".vcf"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        with open(output, 'w') as fout:
            fout.write(proc.stdout.read())
        proc.wait()
        if proc.returncode != 0:
            msg = "The command '%s' did not exit cleanly (return code = %d)" % (str.join(' ', cmd), proc.returncode)
            raise RuntimeError, msg
        return output
