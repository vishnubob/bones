def bootstrap():
    import sys
    import inspect
    from .. task import BoneTask
    from .. tools import __tools__ as toolmap
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    tasks = {}
    for (toolname, toolmod) in toolmap.items():
        for (name, cls) in toolmod.__dict__.items():
            if inspect.isclass(cls) and issubclass(cls, BoneTask) and (cls.__name__ != "BoneTask"):
                tasks[cls.TaskName] = cls
    ns["__tasks__"] = tasks
    del ns["bootstrap"]
bootstrap()
