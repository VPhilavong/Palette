from setuptools import setup, find_packages

setup(
    name="code-palette",
    version="0.1.0",
    description="Design-to-Code UI/UX Agent for React + Tailwind components",
    author="SAIL Project",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "jinja2>=3.1.0",
        "pathlib2>=2.3.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "code-palette=src.cli:main",
        ],
    },
    python_requires=">=3.9",
)