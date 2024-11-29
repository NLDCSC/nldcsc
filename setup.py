#!/usr/bin/env python3
import codecs
from itertools import chain
from pathlib import Path
from setuptools import find_packages, setup
from poetry.core.packages.dependency import Dependency
from poetry.factory import Factory


def parse_group_deps(pyproject_data: dict):
    """
    Get the group deps from the pyproject data.

    To get the group dep data we need to follow a specific path that may or may not exist.
    This function walks through the path and always returns a dict.

    Args:
        pyproject_data (dict): the pyproject data parsed by poetry.

    Returns:
        dict: dict containing the group dependencies
    """
    path = ["tool", "nldcsc", "group", "dependencies"]

    cursor = pyproject_data
    for p in path:
        cursor = cursor.get(p, {})

        if not isinstance(cursor, dict):
            return {}
    return cursor


def reqs(deps: list[Dependency]):
    """
    Format the poetry Dependency to the proper requirement format.

    Args:
        deps (list[Dependency]): list of dependencies.

    Returns:
        list[str]: list of properly formatted requirement strings.
    """

    return [
        f"{dep.complete_name}{'' if any(c in str(dep.constraint) for c in '>=<') else '=='}{dep.constraint}"
        for dep in deps
    ]


# -*- Long Description -*-
def long_description(readme_path: Path):
    """
    Try and read the long description from the readme file.

    Args:
        readme_path (Path): path to the readme file.

    Returns:
        str: Content of the readme file.
    """
    try:
        return codecs.open(readme_path.name, "r", "utf-8").read()
    except OSError:
        return "Long description error: Missing README.md file"


def resolve_group_deps(
    poetry_reqs: dict[str, list[str]], group_deps: dict[list[str]], group: str
) -> set[str]:
    """
    Follow the stream of group deps until a Root or multiple roots are found.

    When a root is found all requirements of that root are added to this group as dependency.

    Args:
        poetry_reqs (dict[str, list[str]]): poetry requirements data object.
        group_deps (dict[list[str]]): dependencies of all groups.
        group (str): group to resolve.

    Returns:
        set[str]: set with the requirements for the given group.
    """
    deps = set(poetry_reqs.get(group, []))

    for dep in group_deps.get(group, []):
        deps.update(resolve_group_deps(poetry_reqs, group_deps, dep))

    return deps


def parse_poetry_reqs(poetry_reqs: dict[str, list[str]], group_deps: dict[list[str]]):
    """
    Read the poetry requirements add parse them to the proper format for setup().

    Further this function creates additional extras if defined in the group deps. 'All' is always created.

    Args:
        poetry_reqs (dict[str, list[str]]): poetry requirements data object.
        group_deps (dict[list[str]]): dependencies of all groups.

    Raises:
        RecursionError: If a circular dependency exists a RecursionError is raised.

    Returns:
        tuple: contains the install_reqs (Always needed for this package), and the optional extras.
    """
    for dep in group_deps:
        try:
            poetry_reqs[dep] = list(resolve_group_deps(poetry_reqs, group_deps, dep))
        except RecursionError:
            raise RecursionError(
                f"You probably have a circular dependency for group {dep}"
            )

    intall_reqs = poetry_reqs.pop("main", [])
    poetry_reqs["all"] = list(set(chain(*poetry_reqs.values())))

    return intall_reqs, poetry_reqs


def generate_meta():
    """
    Generates all the meta info for setup()

    Returns:
        dict: dict that can be used as kwargs for setup()
    """
    poetry = Factory().create_poetry()

    install, extras = parse_poetry_reqs(
        {
            group: reqs(poetry.package.dependency_group(group).dependencies)
            for group in poetry.package.dependency_group_names()
        },
        parse_group_deps(poetry.pyproject.data),
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
        "entry_points": {
            "console_scripts": [
                "nldcsc = nldcsc.cli:cli"
            ]
            
        }
    }


setup(**generate_meta())
