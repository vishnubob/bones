import os

class PicardCommand(dict):
    Command = "__command__"

    def __call__(self):
        args = ["%s=%s" for kv in self.items()]
        args = str.join(' ', args)
        cmd = "%s %s" % (self.Command, args)
        os.shell(cmd)

class MarkDuplicates(PicardCommand):
    Command = "MarkDuplicates"
