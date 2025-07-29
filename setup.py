"""Setup script for Steam Manifest Tool."""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = [
    line.strip()
    for line in (this_directory / "requirements.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]

setup(
    name="steam-manifest-tool",
    version="3.5.0",
    author="Steam Manifest Team",
    author_email="dev@steammanifest.tool",
    description="A modern tool for fetching and managing Steam game manifest files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/steam-manifest/tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "steam-manifest=src.steam_manifest.cli.main:main",
            "steam-extract=src.steam_manifest.tools.extractor:extract_repository_info",
            "steam-clean=src.steam_manifest.tools.cleaner:clean_repository_history",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
