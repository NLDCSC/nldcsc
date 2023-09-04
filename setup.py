#!/usr/bin/env python3
import codecs
import os
from itertools import chain

from setuptools import setup, find_packages

__NAME__ = "nldcsc"
__VERSION__ = "0.0.1"

# -*- Extras -*-

MODULES = {
    "loggers",
}

# -*- Requirements -*-


def _strip_comments(l):
    return l.split("#", 1)[0].strip()


def _pip_requirement(req):
    if req.startswith("-r "):
        _, path = req.split()
        return reqs(*path.split("/"))
    return [req]


def _reqs(*f):
    return [
        _pip_requirement(r)
        for r in (
            _strip_comments(l)
            for l in open(os.path.join(os.getcwd(), "requirements", *f)).readlines()
        )
        if r
    ]


def reqs(*f):
    """Parse requirement file.

    Example:
        reqs('default.txt')          # requirements/default.txt
        reqs('modules', 'redis.txt')  # requirements/modules/redis.txt
    Returns:
        List[str]: list of requirements specified in the file.
    """
    return [req for subreq in _reqs(*f) for req in subreq]


def extras(*p):
    """Parse requirement in the requirements/modules/ directory."""
    return reqs("modules", *p)


def install_requires():
    """Get list of requirements required for installation."""
    return reqs("default.txt")


def extras_require():
    """Get map of all extra requirements."""
    module_requirements = {x: extras(x + ".txt") for x in MODULES}

    # add an 'all' value to install all requirements for all modules
    module_requirements["all"] = list(set(chain(*module_requirements.values())))

    return module_requirements


# -*- Long Description -*-


def long_description():
    try:
        return codecs.open("README.md", "r", "utf-8").read()
    except OSError:
        return "Long description error: Missing README.md file"


setup(
    name=__NAME__,
    packages=find_packages(exclude=["tests", "test_data"]),
    version=__VERSION__,
    description="Package with general devops code",
    long_description=long_description(),
    author="NLDCSC",
    author_email="NLDCSC@invalid.com",
    url="https://github.com/NLDCSC/nldcsc",
    license="GNU General Public License v3.0",
    platforms=["any"],
    install_requires=install_requires(),
    extras_require=extras_require(),
    python_requires=">=3.8",
    include_package_data=True,
    project_urls={
        "Code": "https://github.com/NLDCSC/nldcsc",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Framework :: NLDCSC Devops",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
