#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xsdflatten",
    version="1.0.0",
    author="Roman Dvořák",
    author_email="roman.dvorak@fzu.cz",
    maintainer="Roman Dvořák",
    maintainer_email="roman.dvorak@fzu.cz",
    description="Python 3 script to flatten an XSD schema into a single document",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FZU-AV-CR/xsdflatten",
    py_modules=["xsdflatten"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: XML",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "xsdflatten=xsdflatten:main",
        ],
    },
)