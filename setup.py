"""
Setup script for WellSync AI system.

Handles project installation, dependency management,
and development environment setup.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="wellsync-ai",
    version="0.1.0",
    author="WellSync AI Team",
    author_email="team@wellsync.ai",
    description="Autonomous Multi-Agent Wellness Orchestration System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellsync-ai/wellsync-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "hypothesis>=6.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "hypothesis>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wellsync-ai=wellsync_ai.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "wellsync_ai": ["*.json", "*.yaml", "*.yml"],
    },
)