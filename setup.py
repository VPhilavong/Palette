from setuptools import setup, find_packages

setup(
    name="code-palette",
    version="0.1.0",
    description="AI-powered component generator for design systems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="VPhilavong",
    author_email="vphilavong@example.com",
    url="https://github.com/VPhilavong/palette",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "click>=8.1.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "jinja2>=3.1.0",
        "pathlib2>=2.3.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "palette=palette.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    include_package_data=True,
    package_data={
        "palette": ["utils/*.js", "generation/templates/*.j2"],
    },
)