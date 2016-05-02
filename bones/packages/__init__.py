def bootstrap():
    import sys
    import inspect
    from .. package import Package
    from .. tools import __tools__ as toolmap
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    packages = {}
    for (toolname, toolmod) in toolmap.items():
        for (name, cls) in toolmod.__dict__.items():
            if inspect.isclass(cls) and issubclass(cls, Package) and (cls.__name__ != "Package"):
                packages[cls.PackageName] = cls
    ns["__packages__"] = packages
    del ns["bootstrap"]
bootstrap()
