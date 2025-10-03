from setuptools import setup, find_packages
import os

# Get the long description from README
long_description = "An MS-DOS-like CLI OS made entirely in Python."
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    pass

setup(
    name="Py-DOS-B1",
    version="1.1.3",
    author="Basanta Bhandari",
    author_email="bhandari.basanta.47@gmail.com",
    description="An MS-DOS-like CLI OS made entirely in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/Py-DOS-B1",  # Add your repo URL
    
    # Use packages instead of py_modules for better reliability
    packages=find_packages(),
    py_modules=["main", "utils"],
    
    # Entry points - this is the critical part
    entry_points={
        "console_scripts": [
            "boot=main:main",
            "pydos=main:main",  # Alternative command name
        ],
    },
    
    # Alternative method using scripts (fallback)
    scripts=["scripts/boot.py"] if os.path.exists("scripts/boot.py") else [],
    
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
    install_requires=[],
    
    # Include additional files
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
    
    # Keywords for better discoverability
    keywords="dos, cli, terminal, simulator, shell",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/basanta-bhandari/Py-DOS-B1/issues",
        "Source": "https://github.com/basanta-bhandari/Py-DOS-B1/",
    },
)