import sys
import os.path

from setuptools import find_packages
from distutils.core import setup
from os import listdir

print (find_packages())
xaod_template_files = listdir('adl_func_backend/R21Code')
setup(name="functional_adl",
    version='1.0.0-alpha.1',
    packages=find_packages(exclude=['tests']),
    scripts=[],
    description="Functional Analysis Description Language",
    long_description='Implement backend and front end analysis languages',
    author="G. Watts (IRIS-HEP)",
    author_email="gwatts@uw.edu",
    maintainer="Gordon Watts (IRIS-HEP)",
    maintainer_email="gwatts@uw.edu",
    url="http://iris-hep.org",
    download_url="http://iris-hep.org",
    license="TBD",
    test_suite="tests",
    install_requires=["jinja2>=2.0.0", "requests>=2.0.0", "pandas>=0.24.0", "uproot>=3.7.0"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest>=3.9"],
    classifiers=[
        # "Development Status :: 1 - Planning",
        "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",
        # "Development Status :: 6 - Mature",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development",
        "Topic :: Data Analysis",
        "Topic :: Utilities",
    ],
    data_files=[('adl_func_backend/R21Code', [f'adl_func_backend/R21Code/{f}' for f in xaod_template_files])],
    platforms="Any",
)