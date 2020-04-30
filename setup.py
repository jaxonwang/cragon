import os

from pathlib import Path
from distutils.dir_util import copy_tree
from setuptools import setup, Extension
from distutils.command.build import build as build_orig

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DMTCP_s = "dmtcp"
DMTCP_DIR = os.path.join(ROOT_DIR, DMTCP_s)

def buildDMTCP(build_cmd):
    cwd = os.getcwd()
    target_dir = str(Path(build_cmd.build_base).absolute())
    os.chdir(DMTCP_DIR)
    # conf
    if not os.path.isfile("Makefile"):
        configure_shell = os.path.join(DMTCP_DIR, "configure")
        build_cmd.spawn([configure_shell])
    #make
    make_cmd = ["make"]
    if build_cmd.parallel:
        make_cmd += ["-j", str(build_cmd.parallel)]
    build_cmd.spawn(make_cmd)
    #copy
    out_dirs = ["bin", "lib"]
    for d in out_dirs:
        copy_tree(d, os.path.join(target_dir, d))

    os.chdir(cwd)

class build(build_orig):
    def run(self):
        buildDMTCP(self)
        super().run()

setup(
    name="cragon",
    version="0.0.1",
    packages=['cragon'],
    cmdclass={
        'build': build,
    }
)


