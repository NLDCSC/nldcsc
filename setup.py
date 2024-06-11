#!/usr/bin/env python3
import codecs
import os
import re
from itertools import chain

from setuptools import setup, find_packages

__NAME__ = "nldcsc"

# -*- Distribution Meta -*-

re_meta = re.compile(r"__(\w+?)__\s*=\s*(.*)")
re_doc = re.compile(r'^"""(.+?)"""')


def _add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, attr_value.strip("\"'")),)


def _add_doc(m):
    return (("doc", m.groups()[0]),)


def parse_dist_meta():
    """Extract metadata information from ``$dist/__init__.py``."""
    pats = {re_meta: _add_default, re_doc: _add_doc}
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, __NAME__, "__init__.py")) as meta_fh:
        distmeta = {}
        for line in meta_fh:
            if line.strip() == "# -eof meta-":
                break
            for pattern, handler in pats.items():
                m = pattern.match(line.strip())
                if m:
                    distmeta.update(handler(m))
        return distmeta


# -*- Extras -*-

MODULES = {
    "auth",
    "datatables",
    "flask_managers",
    "flask_middleware",
    "flask_plugins",
    "http_apis",
    "httpx_apis",
    "loggers",
    "sql_migrations",
    "sso",
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
    if len(f) == 2:
        if os.getcwd().endswith("modules") and f[0] == "modules":
            f = [f[1]]
        if not os.getcwd().endswith("modules") and f[0] == ".":
            f = ("modules", f[1])
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
        reqs('.', 'loggers.txt')  # requirements/modules/loggers.txt -> this is a reference in a requirements file
        like -r ./loggers.txt
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


meta = parse_dist_meta()

setup(
    name=__NAME__,
    packages=find_packages(exclude=["tests", "test_data"]),
    version=meta["version"],
    description="Package with general devops code",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author=meta["author"],
    author_email="NLDCSC@invalid.com",
    url="https://github.com/NLDCSC/nldcsc",
    license="GNU General Public License v3.0",
    platforms=["any"],
    install_requires=install_requires(),
    extras_require=extras_require(),
    python_requires=">=3.10",
    include_package_data=True,
    project_urls={
        "Code": "https://github.com/NLDCSC/nldcsc",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
