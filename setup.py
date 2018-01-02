from setuptools import setup, find_packages

version = '0.1'

APP = ['floodit/floodit.py']
DATA_FILES = []
OPTIONS = {}

setup(name='floodit',
      version=version,
      description="A game.",
      long_description="""""",
      classifiers=[],   # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='game',
      author='Ronald Bai',
      author_email='ouyanghongyu@gmail.com',
      url='',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "pygame"
      ],
      app=APP,
      data_files=DATA_FILES,
      options={'py2app': OPTIONS},
      setup_requires=['py2app'],
      )
