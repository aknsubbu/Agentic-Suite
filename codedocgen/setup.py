from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="codedocgen",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AutoGen Code Documentation Generator using Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codedocgen",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pyautogen>=0.2.0",
        "requests>=2.25.0",
        "questionary>=1.10.0",
        "pyyaml>=6.0",
        "colorama>=0.4.4",
    ],
    entry_points={
        "console_scripts": [
            "codedocgen=codedocgen.cli:main",
        ],
    },
)
