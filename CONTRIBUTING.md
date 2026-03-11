# Contributing to Nova Memory 2.0

Thank you for your interest in contributing to Nova Memory 2.0! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

Please be respectful and constructive in all interactions with community members.

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/nova-memory.git
   cd nova-memory
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/mbugus94-lang/nova-memory.git
   ```

### Setup Development Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[all,dev]"

# Or use the setup script
python setup_helper.py --full --test
# Or on macOS/Linux:
chmod +x setup.sh
./setup.sh --full --test
```

## Development Workflow

### Create Feature Branch

```bash
# Update main branch
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `test/description` - Test additions
- `refactor/description` - Code refactoring

### Development Process

1. **Make Changes**: Edit files as needed

2. **Run Tests**:
   ```bash
   # Run all tests
   pytest -v

   # Run with coverage
   pytest --cov=. --cov-report=html
   ```

3. **Format Code**:
   ```bash
   black .
   isort .
   ```

4. **Lint Code**:
   ```bash
   flake8 .
   pylint $(find . -name '*.py' | grep -v venv)
   ```

5. **Type Check** (optional but recommended):
   ```bash
   mypy .
   ```

### Using Make Commands

On macOS/Linux, use convenient make commands:

```bash
make test          # Run tests
make format        # Format code
make lint          # Check code quality
make type-check    # Check types
make clean         # Clean up
```

See `make help` for all available commands.

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use meaningful variable/function names
- Add docstrings to all classes and functions
- Aim for 80-100 character line length

### Example Docstring

```python
def your_function(param1: str, param2: int) -> bool:
    """
    Short description of what the function does.
    
    More detailed explanation if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is invalid
        
    Example:
        >>> result = your_function("test", 42)
        >>> print(result)
        True
    """
    # Implementation
    return True
```

### Type Hints

Use type hints for better code clarity:

```python
from typing import Optional, List, Dict

def process_data(
    items: List[str],
    config: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """Process items with optional configuration."""
    pass
```

### Comments

- Use clear, meaningful comments
- Explain the "why", not the "what"
- Keep comments up-to-date with code

```python
# Good: Explains intent
result = [x for x in items if x > threshold]  # Filter outliers

# Avoid: States the obvious
x = x + 1  # Increment x
```

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

```bash
# Good
git commit -m "feat: add memory versioning support"
git commit -m "fix: resolve database locking issue on Windows"
git commit -m "docs: update installation guide"

# Avoid
git commit -m "fix stuff"
git commit -m "WIP"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style (formatting, missing semicolons, etc)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Build process, dependencies, etc

### Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill in the PR template with:
# - Description of changes
# - Motivation and context
# - Type of change (bugfix/feature/etc)
# - Testing performed
# - Related issues
```

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Changes have been tested locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No unnecessary files committed
- [ ] Passes CI/CD checks

## Reporting Bugs

### Bug Report Template

When reporting a bug, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Exact steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS and version
   - Python version
   - Nova Memory version
   - Relevant packages
6. **Logs**: Include relevant error messages/logs
7. **Attachments**: Screenshots, logs, etc if helpful

### Example Bug Report

```
Title: Database locked error when running multiple instances

Description:
Nova Memory throws a database locked error when two instances 
access the same database simultaneously.

Steps to Reproduce:
1. Start API server on default port
2. In another terminal, run: python main.py
3. Observe database lock error

Expected: Concurrent access should be handled gracefully
Actual: "database is locked" error

Environment:
- OS: Windows 11
- Python: 3.10.5
- Nova Memory: 2.0.0
```

## Feature Requests

### Feature Request Template

When proposing a feature:

1. **Title**: Clear, descriptive title
2. **Description**: What is the feature? Why is it needed?
3. **Use Cases**: Who would use this? How?
4. **Proposed Solution**: If you have ideas
5. **Alternatives**: Other approaches considered
6. **Additional Context**: Examples, references, etc

## Testing Guidelines

### Write Tests

Add tests for all new features and bug fixes:

```python
import pytest
from your_module import your_function

def test_your_function_basic():
    """Test basic functionality."""
    result = your_function("input")
    assert result == "expected_output"

def test_your_function_edge_case():
    """Test edge cases."""
    result = your_function("")
    assert result is None
    
def test_your_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        your_function(None)
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_file.py::test_function

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Documentation

### Update Documentation When:
- Adding new features
- Changing existing behavior
- Fixing bugs related to documentation

### Documentation Files:
- `README.md` - Main project documentation
- `INSTALL.md` - Installation guide
- `CONTRIBUTING.md` - This file
- Docstrings in code - Function/class documentation

## Questions?

- Open an issue for questions
- Check existing issues/discussions
- Review documentation
- Ask in GitHub Discussions

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Project CHANGELOG
- Special mention in releases

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Nova Memory 2.0! 🎉
