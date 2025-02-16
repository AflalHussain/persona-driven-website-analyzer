from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="website-analyzer",
    version="0.1.0",
    author="Aflal Hussain",
    author_email="aflalibnhussain@gmail.com",
    description="A persona-driven website analysis system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AflalHussain/Persona-driven-web-crawler-and-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "analyze-website=examples.basic_analysis:main",
            "custom-analysis=examples.custom_persona:main",
        ],
    },
) 