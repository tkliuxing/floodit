from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='floodit',
      version=version,
      description="A game.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='game',
      author='Ronald Bai',
      author_email='ouyanghongyu@gmail.com',
      url='',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
