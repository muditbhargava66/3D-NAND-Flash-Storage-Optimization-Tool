# Contributing to 3D NAND Optimization Tool

Thank you for your interest in contributing to the 3D NAND Optimization Tool! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Branching Strategy](#branching-strategy)
5. [Commit Guidelines](#commit-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Testing](#testing)
8. [Code Style](#code-style)
9. [Documentation](#documentation)
10. [Issue Tracking](#issue-tracking)
11. [License](#license)

## Code of Conduct

Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md) to foster an inclusive and respectful community.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/YOUR_USERNAME/3D-NAND-Flash-Storage-Optimization-Tool.git
   cd 3d-nand-optimization-tool
   ```
3. Add the original repository as a remote to keep your fork in sync:
   ```
   git remote add upstream https://github.com/muditbhargava66/3D-NAND-Flash-Storage-Optimization-Tool.git
   ```
4. Create a new branch for your changes:
   ```
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # For Unix/Linux
   venv\Scripts\activate.bat  # For Windows
   ```

2. Install development dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```
   pip install -e .
   ```

4. Make sure the tests pass:
   ```
   pytest tests/
   ```

## Branching Strategy

- `main`: The main branch contains the stable version of the code.
- `develop`: The development branch contains the latest changes.
- Feature branches: Create branches from `develop` for new features or bug fixes.

Use the following naming convention for branches:
- `feature/feature-name`: For new features
- `bugfix/bug-name`: For bug fixes
- `hotfix/issue-name`: For critical fixes to production code
- `docs/documentation-change`: For documentation updates

## Commit Guidelines

1. Write clear, concise commit messages in the imperative mood (e.g., "Add feature" not "Added feature").
2. Reference issue numbers in your commit messages when applicable.
3. Keep commits focused on specific changes to make review easier.
4. Use the following format:
   ```
   [Module] Short description (50 chars or less)

   More detailed description if necessary.

   References #issue_number
   ```

Example:
```
[ECC] Implement advanced BCH error correction algorithm

This commit implements the BCH algorithm with Galois Field arithmetic
for better error correction capabilities.

References #42
```

## Pull Request Process

1. Update your branch with the latest changes from the upstream repository:
   ```
   git fetch upstream
   git rebase upstream/develop
   ```

2. Ensure all tests pass:
   ```
   pytest tests/
   ```

3. Make sure your code follows the project's code style (see [Code Style](#code-style)).

4. Push your changes to your fork:
   ```
   git push origin feature/your-feature-name
   ```

5. Submit a pull request to the `develop` branch of the main repository.

6. Describe your changes in detail in the pull request, including:
   - The purpose of the changes
   - Any relevant issues that are fixed
   - Any breaking changes
   - Any new dependencies

7. Wait for reviewers to provide feedback and address any requested changes.

## Testing

- Write tests for all new features and bug fixes.
- Run the test suite before submitting a pull request.
- Use pytest to run tests:
  ```
  pytest tests/
  ```
- For more comprehensive testing, use tox:
  ```
  tox
  ```

- Make sure your tests cover both normal usage and edge cases.
- Mock external dependencies when appropriate.

## Code Style

We follow the PEP 8 style guide for Python code with some modifications. The project uses the following tools for code style enforcement:

- Black: For code formatting
- Flake8: For linting
- isort: For import sorting
- mypy: For type checking

You can apply these tools using tox:
```
tox -e format  # Formats code using Black and isort
tox -e lint    # Checks code with Flake8
tox -e type    # Runs type checking with mypy
```

Or run all checks at once:
```
tox -e check
```

## Documentation

- Document all public modules, classes, methods, and functions.
- Use docstrings following the Google style.
- Update documentation when changing functionality.
- Include examples in docstrings when appropriate.

For example:
```python
def function_name(param1, param2):
    """
    Brief description of the function.
    
    Args:
        param1 (type): Description of param1.
        param2 (type): Description of param2.
        
    Returns:
        return_type: Description of the return value.
        
    Raises:
        ExceptionType: When and why this exception is raised.
        
    Example:
        >>> function_name(1, 2)
        3
    """
    pass
```

## Issue Tracking

- Check if an issue already exists before creating a new one.
- Use issue templates when available.
- Provide detailed information when creating issues:
  - Steps to reproduce
  - Expected behavior
  - Actual behavior
  - System information

Use the following labels for issues:
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation-related changes
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed

## License

By contributing to the 3D NAND Optimization Tool, you agree that your contributions will be licensed under the project's [MIT License](../LICENSE).

## Additional Resources

- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

Thank you for contributing to the 3D NAND Optimization Tool project! Your efforts help make this project better for everyone.