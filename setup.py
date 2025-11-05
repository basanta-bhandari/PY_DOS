from setuptools import setup, find_packages
import os


long_description = "An MS-DOS-like CLI OS made entirely in Python."
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    pass

setup(
    name="Py-DOS-B1",
    version="1.1.6",
    author="Basanta Bhandari",
    author_email="bhandari.basanta.47@gmail.com",
    description="An MS-DOS-like CLI OS made entirely in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/Py-DOS-B1", 
    

    packages=find_packages(),
    py_modules=["main", "utils"],
    

    entry_points={
        "console_scripts": [
            "boot=main:main",
            "pydos=main:main",  
        ],
    },
    
    
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