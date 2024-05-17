# Installation

## Requirements

To use `example_package`, you need to have Python 3.11 or higher installed.
We also recommend using a virtual environment to install the package's dependencies.

## Installing using `pip`

If the package is hosted on PyPI, direct users to install the package using `pip`:

```bash
pip install example_package
```

This will install the latest release version of the package.

## Installing from Source

To install `example_project` directly from its [GitHub repository](<https://github.com/TeiaLabs/example_project>), run the following command:

```bash
pip install git+https://github.com/TeiaLabs/example_project.git
```

## Installing from Source (Development)

If you are interested in contributing to AIPrompts or want to use the latest development versions, you can:

1. Clone the repository
2. Navigate to the repository folder
3. Check which dependencies you will require to run the package according to your needs (`requirements-<name>.txt` files in root folder)
4. Install the package in development mode (providing optional dependencies as needed)

To install AIPrompts in development mode without any optional dependencies, run the following command:

```bash
pip install -e .
```

If you want to contribute to the documentation and also run the tests, the following command would be needed:

```bash
pip install -e .[docs,test]
```
