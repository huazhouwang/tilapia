#!/usr/bin/env python3

from setuptools import setup

from wallet import version

with open("requirements.txt", "r") as f:
    requirements = (i.strip() for i in f)
    requirements = [i for i in requirements if i]


setup(
    name="MultiChainWallet",
    version=version.__VERSION__,
    python_requires=">=3.8",
    install_requires=requirements,
    author_email="huazhou19@gmail.com",
    license="MIT Licence",
    long_description="MultiChain Wallet",
)
