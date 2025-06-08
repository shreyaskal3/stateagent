from setuptools import setup, find_packages

setup(
    name="stateagent",
    version="0.1.0",
    description="A library for building reliable, state-driven LLM workflows using the State+CRUD pattern",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Shreyas Kale",
    author_email="shreyaskale11@gmail.com",
    url="https://github.com/shreyaskal3/stateagent",
    project_urls={
        "Homepage": "https://github.com/shreyaskal3/stateagent",
        "Repository": "https://github.com/shreyaskal3/stateagent",
    },
    packages=find_packages(include=["stateagent", "stateagent.*"]),
    install_requires=[
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "examples": [
            "python-dotenv>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    license="MIT",
    python_requires=">=3.8",
)