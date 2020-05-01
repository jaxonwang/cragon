import os
import distutils
import glob

from pathlib import Path
from setuptools import setup, Extension
from distutils.command.build import build as build_orig

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DMTCP_s = "dmtcp"
DMTCP_DIR = os.path.join(ROOT_DIR, DMTCP_s)
DMTCP_PLUGIN_s = "dmtcp_plugin"
DMTCP_PLUGIN_DIR = os.path.join(ROOT_DIR, DMTCP_PLUGIN_s)

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
        distutils.dir_util.copy_tree(d, os.path.join(target_dir, d))

    os.chdir(cwd)

def buildDMTCPplugin(build_cmd):
    cwd = os.getcwd()
    target_dir = str(Path(build_cmd.build_base).absolute())
    os.chdir(DMTCP_PLUGIN_DIR)
    #make
    make_cmd = ["make"]
    if build_cmd.parallel:
        make_cmd += ["-j", str(build_cmd.parallel)]
    build_cmd.spawn(make_cmd)
    files = glob.glob("*.so")
    for f in files:
        distutils.file_util.copy_file(f, os.path.join(target_dir, "lib"))
    os.chdir(cwd)

class build(build_orig):
    def run(self):
        buildDMTCP(self)
        buildDMTCPplugin(self)
        super().run()

setup(
    name="cragon",
    version="0.0.1",
    packages=['cragon'],
    cmdclass={
        'build': build,
    }
)


