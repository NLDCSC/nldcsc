#!/usr/bin/env python3
import codecs
from itertools import chain
from pathlib import Path
from setuptools import find_packages, setup
from poetry.core.packages.dependency import Dependency
from poetry.factory import Factory


def reqs(deps: list[Dependency]):
    return [f"{dep.complete_name}{dep.constraint}" for dep in deps]


# -*- Long Description -*-
def long_description(readme_path: Path):
    try:
        return codecs.open(readme_path.as_uri(), "r", "utf-8").read()
    except OSError:
        return "Long description error: Missing README.md file"


def parse_poetry_reqs(poetry_reqs: dict[str, list[str]]):
    intall_reqs = poetry_reqs.pop("main", [])
    poetry_reqs["all"] = list(set(*chain(poetry_reqs.values())))

    return intall_reqs, poetry_reqs


def generate_meta():
    poetry = Factory().create_poetry()

    install, extras = parse_poetry_reqs(
        {
            group: reqs(poetry.package.dependency_group(group).dependencies)
            for group in poetry.package.dependency_group_names()
        }
    )

    return {
        "name": poetry.package.name,
        "packages": find_packages(exclude=["tests", "test_data"]),
        "version": str(poetry.package.version),
        "description": poetry.package.description,
        "long_description": long_description(poetry.package.readme),
        "long_description_content_type": "text/markdown",
        "author": poetry.package.author_name,
        "author_email": poetry.package.author_email,
        "url": poetry.package.repository_url,
        "license": poetry.package.license.name,
        "platforms": ["any"],
        "install_requires": install,
        "extras_require": extras,
        "python_requires": str(poetry.package.python_constraint),
        "include_package_data": True,
        "project_urls": poetry.package.custom_urls,
        "classifiers": poetry.package.classifiers,
    }


setup(**generate_meta())
