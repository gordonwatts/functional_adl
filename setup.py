import sys
import os.path

from setuptools import find_packages
from setuptools import setup

# TODO: find_packages returns an empty array, what is missing?
print (find_packages())
setup(name="functional_adl",
    version='0.1.0-alpha.1',
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
    install_requires=[],
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
        "Topic :: Utilities",
    ],
    platforms="Any",
)