"""Setup script for Smart-Splitter."""

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("smart_splitter_specs.md", "r") as f:
    long_description = f.read()

setup(
    name="smart-splitter",
    version="0.1.0",
    description="Intelligent PDF document splitting and classification system for construction legal disputes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Smart-Splitter Development Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Legal",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "smart-splitter=smart_splitter.main:main",
        ],
    },
)