from setuptools import setup, find_packages
from configtoolkit import __version__ as version

long_description = open("README.md", "r", encoding="utf8").read()

requirements = open("requirements.txt", "r", encoding="utf8").read().split("\n")

setup(
    name="configtoolkit",
    version=version,
    author="XenoCorn",
    description="Another configuration library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xenocorn/configtoolkit",
    packages=find_packages(),
    install_requires=requirements,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: BSD License",
    ],
)
