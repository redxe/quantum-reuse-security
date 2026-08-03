from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="quantum-reuse-security",
    version="0.6.0",
    author="Vi Connelly",
    description="Deterministic branch-conditioned analysis for quantum qubit reuse security",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/redxe/quantum-reuse-security",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.1.0",
        "matplotlib>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
        ],
        "qiskit": [
            "qiskit>=0.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantum-reuse=quantum_reuse.cli:main",
        ]
    },
)
