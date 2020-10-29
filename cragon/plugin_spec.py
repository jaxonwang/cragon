import pluggy
import importlib
import os
import sys
from typing import List

hookspec = pluggy.HookspecMarker("cragon")

"""
All this function are executed strictly before or after the corresponding
events.
"""


@hookspec
def done(exeinfo):
    """Called when the task managed by Cragon is finished and return 0"""


@hookspec
def fail(exeinfo):
    """Called when the task managed by Cragon is failed and
    probably will failed when rerun"""


@hookspec
def rerunnable_fail(exeinfo):
    """Called when the task managed by Cragon fails and
    could succeed when rerun, ie. Not enough memory"""


@hookspec
def start(exeinfo):
    """Called when the task managed by Cragon just starts"""


@hookspec
def restart(exeinfo):
    """Called when the task managed by Cragon restarts from checkpoint"""


@hookspec
def checkpoint(exeinfo):
    """Called when the task managed by Cragon just starts checkpointing"""


@hookspec
def checkpoint_done(exeinfo):
    """Called when the task managed by Cragon finishs checkpointing"""


def get_plugin_hook(modules):
    pm = pluggy.PluginManager("cragon")
    pm.add_hookspecs(sys.modules[__name__])
    for m in modules:
        pm.register(m)
    return pm.hook


def load_plugin_modules(pymodules: List[str]):
    modules = []
    storedsyspath = sys.path[:]
    try:
        for pymodule in pymodules:
            p = os.path.dirname(pymodule)
            # remove the ext .py
            m_name = os.path.basename(pymodule).split(".")[0]
            sys.path = [p]
            m = importlib.import_module(m_name)
            modules.append(m)
    finally:
        sys.path = storedsyspath
    return modules
