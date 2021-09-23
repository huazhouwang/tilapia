#!/usr/bin/env python3

import os
import pathlib

from pkg_resources import parse_requirements
from setuptools import find_packages, setup

from tilapia import version

directory = pathlib.Path(__file__).parent

requirements = directory.joinpath("requirements.txt").read_text()
requirements = [str(r) for r in parse_requirements(requirements)]

packages = ["tilapia", *(f"tilapia.{pkg}" for pkg in find_packages("tilapia"))]
is_packaging_api = os.environ.get("IS_PACKAGING_API") == "True"
if is_packaging_api:
    api_requirements = directory.joinpath("requirements-api.txt").read_text()
    requirements.extend(str(r) for r in parse_requirements(api_requirements))
    entry_points = {"console_scripts": ["tilapia = tilapia.api.__main__:main"]}
else:
    entry_points = None
    packages = [pkg for pkg in packages if not pkg.startswith("tilapia.api")]

setup(
    name="Tilapia",
    version=version.__VERSION__,
    author="__huazhou",
    author_email="huazhou19@gmail.com",
    url="https://github.com/huazhouwang/tilapia",
    python_requires=">=3.8",
    install_requires=requirements,
    packages=packages,
    entry_points=entry_points,
    long_description=directory.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    keywords="multi-chain wallet cryptocurrencies btc eth python",
    license="MIT Licence",
)
