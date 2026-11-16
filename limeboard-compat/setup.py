# SPDX-License-Identifier: MIT
"""Installs limeboard_compat.pth next to the modules: setuptools has no
setting for files at the root of site-packages."""
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyWithPth(build_py):
    def run(self):
        super().run()
        self.copy_file("limeboard_compat.pth", self.build_lib + "/limeboard_compat.pth")


setup(cmdclass={"build_py": BuildPyWithPth})
