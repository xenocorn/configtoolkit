from setuptools import setup, find_packages
import shutil
import glob
import re

# [garbage collecting]
for f in glob.glob("*.egg-info"):
    shutil.rmtree(f)
try:
    shutil.rmtree("dist")
except IOError:
    pass
try:
    shutil.rmtree("build")
except IOError:
    pass

# [import values]
long_description = open("README.md", "r", encoding="utf8").read()

requirements = open("requirements.txt", "r", encoding="utf8").read().split("\n")

with open("configtoolkit/__init__.py", "r", encoding="utf8") as file:
    version = re.search(r'__version__ = "(.*?)"', file.read()).group(1)

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
