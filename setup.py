from setuptools import find_packages, setup

APP = ["floodit/__main__.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "packages": ["pygame"],
    "plist": {
        "CFBundleName": "Flood it!",
        "CFBundleShortVersionString": "0.2.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="floodit",
    version="0.2.0",
    description="A flood-fill puzzle game.",
    author="Ronald Bai",
    author_email="ouyanghongyu@gmail.com",
    license="GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=["pygame"],
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
