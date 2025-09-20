#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Py-DOS-B1",
    version="1.0.0",
    author="Basanta Bhandari",
    author_email="bhandari.basanta.47@gmail.com",
    description="A DOS-like operating system simulator with classic commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["main", "utils"],
    entry_points={
        "console_scripts": [
            "boot=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)