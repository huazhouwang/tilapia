#!/usr/bin/env python3
import pathlib

from pkg_resources import parse_requirements
from setuptools import find_packages, setup

from wallet import version

directory = pathlib.Path(__file__).parent

requirements = directory.joinpath("requirements.txt").read_text()
requirements = [str(r) for r in parse_requirements(requirements)]


setup(
    name="Tilapia",
    version=version.__VERSION__,
    author="__huazhou",
    author_email="huazhou19@gmail.com",
    url="https://github.com/huazhouwang/tilapia",
    python_requires=">=3.8",
    install_requires=requirements,
    packages=find_packages("."),
    license="MIT Licence",
    long_description=directory.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    keywords="multi-chain wallet cryptocurrencies btc eth python",
)
