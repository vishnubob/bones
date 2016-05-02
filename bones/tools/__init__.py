def bootstrap():
    import os
    import sys
    import glob
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    tooldir = os.path.split(__file__)[0]
    files = glob.glob(os.path.join(tooldir, "*.py"))
    modules = set([os.path.splitext(os.path.split(fn)[-1])[0] for fn in files if "__init__" not in fn])
    tools = {}
    for modname in modules:
        fqname = "bones.tools.%s" % modname
        try:
            mod = __import__(fqname, fromlist=["*"])
        except:
            msg = "Error importing %s\n" % fqname
            sys.stderr.write(msg)
            raise
        tools[modname] = ns[modname] = mod
    del ns["bootstrap"]
    ns["__tools__"] = tools
bootstrap()
