import os

from setuptools import setup, find_packages

from nldcsc import _version_from_git_describe

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

with open(os.path.join(HERE, "requirements.txt")) as fid:
    REQS = fid.read().splitlines()


setup(
    name="nldcsc",
    version=_version_from_git_describe(),
    packages=find_packages(exclude=("tests", "test_data")),
    url="",
    license="GNU General Public License v3.0",
    author="NLDCSC",
    description="Package with general devops code",
    long_description=README,
    long_description_content_type="text/markdown",
    package_data={"nldcsc": ["LICENSE", "VERSION"]},
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    install_requires=REQS,
)
