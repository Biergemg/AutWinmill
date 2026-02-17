from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="windmill-platform-cli",
    version="1.0.0",
    author="Windmill Platform Team",
    author_email="team@windmill-platform.io",
    description="Enterprise CLI for Windmill Platform automation management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/windmill-platform/wmctl",
    py_modules=["wmctl"],
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "PyYAML>=6.0",
        "rich>=13.0.0",
        "cryptography>=3.4.0",
        "hvac>=1.0.0",
        "redis>=4.0.0",
        "boto3>=1.26.0",
        "kubernetes>=25.0.0",
        "docker>=6.0.0",
        "tabulate>=0.9.0",
        "python-dateutil>=2.8.0",
        "jinja2>=3.1.0",
        "jsonschema>=4.0.0",
        "pydantic>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.991",
            "ruff>=0.0.200",
            "pre-commit>=2.20.0",
        ],
        "test": [
            "responses>=0.22.0",
            "freezegun>=1.2.0",
            "faker>=15.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wmctl=wmctl:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="windmill automation platform cli enterprise devops kubernetes",
    project_urls={
        "Bug Reports": "https://github.com/windmill-platform/wmctl/issues",
        "Source": "https://github.com/windmill-platform/wmctl",
        "Documentation": "https://docs.windmill-platform.io",
    },
)