from setuptools import setup

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "An MS-DOS-like CLI OS made entirely in Python."

setup(
    name="Py-DOS-B1",
    version="1.1.7",
    author="Basanta Bhandari",
    author_email="bhandari.basanta.47@gmail.com",
    description="An MS-DOS-like CLI OS made entirely in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basanta-bhandari/PY_DOS",  # fixed: was placeholder "your-username"

    py_modules=["main", "utils"],  # both modules exist and are used

    entry_points={
        "console_scripts": [
            "boot=main:main",
            "pydos=main:main",
        ],
    },

    # removed: scripts=["scripts/boot.py"] — scripts/ directory does not exist

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.7",
    install_requires=["psutil", "readchar"],

    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },

    keywords="dos, cli, terminal, simulator, shell",

    project_urls={
        "Bug Reports": "https://github.com/basanta-bhandari/Py-DOS-B1/issues",
        "Source": "https://github.com/basanta-bhandari/Py-DOS-B1/",
    },
)