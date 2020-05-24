import os
import distutils
import glob

from setuptools import setup, Extension
from distutils.command.build import build as build_orig
from setuptools.command.build_ext import build_ext as build_ext_orig

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DMTCP_s = "dmtcp"
DMTCP_DIR = os.path.join(ROOT_DIR, DMTCP_s)
DMTCP_PLUGIN_s = "dmtcp_plugin"
DMTCP_PLUGIN_DIR = os.path.join(ROOT_DIR, DMTCP_PLUGIN_s)


class DMTCPPlugin(Extension):

    def __init__(self, name):
        super().__init__(name, sources=[])

    @staticmethod
    def buildDMTCPplugin(build_cmd):
        cwd = os.getcwd()
        os.chdir(DMTCP_PLUGIN_DIR)
        # make
        make_cmd = ["make"]
        if build_cmd.debug:
            make_cmd += ["debug"]
        if build_cmd.parallel:
            make_cmd += ["-j", str(build_cmd.parallel)]
        build_cmd.spawn(make_cmd)

        plugin_out_dir = "." if not build_cmd.debug else "debug"
        files = glob.glob(os.path.join(plugin_out_dir, "*.so"))
        files = [os.path.abspath(f) for f in files]

        os.chdir(cwd)

        # copy to build/lib../cragon/lib
        dst = os.path.join(build_cmd.build_lib, "cragon", "lib")
        if not os.path.isdir(dst):
            os.mkdir(dst)
        for f in files:
            distutils.file_util.copy_file(f, dst)


class build_ext(build_ext_orig):
    def run(self):
        super().run()

    def build_extension(self, ext):
        if isinstance(ext, DMTCPPlugin):
            ext.buildDMTCPplugin(self)
        else:
            super().build_extension(ext)


class build(build_orig):

    def buildDMTCP(self):
        cwd = os.getcwd()
        os.chdir(DMTCP_DIR)
        # conf
        if not os.path.isfile("Makefile"):  # TODO allow user to config
            configure_shell = os.path.join(DMTCP_DIR, "configure")
            self.spawn([configure_shell])
        # make
        make_cmd = ["make"]
        if self.parallel:
            make_cmd += ["-j", str(self.parallel)]
        self.spawn(make_cmd)

        os.chdir(cwd)

        # copy to build/lib../lib
        dmtcp_out_dirs = ["bin", "lib"]
        for d in dmtcp_out_dirs:
            distutils.dir_util.copy_tree(
                os.path.join(
                    DMTCP_s, d), os.path.join(
                    self.build_lib, "cragon", d))

    def run(self):
        super().run()
        self.buildDMTCP()


setup(
    name="cragon",
    version="0.0.1",
    url="https://github.com/jaxonwang/cragon",
    author="JX Wang",
    author_email="jxwang92@gmail.com",
    install_requires=["Click"],
    packages=['cragon'],
    ext_modules=[DMTCPPlugin("dmtcp_plugin")],
    cmdclass={
        'build': build,
        'build_ext': build_ext,
    },
    entry_points={
        'console_scripts': ['cragon=cragon.command_line:main'],
    },
)
