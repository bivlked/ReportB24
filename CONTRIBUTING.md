# Contributing to ReportB24

🎉 **Thank you for your interest in contributing to ReportB24!** 🎉

We welcome contributions from developers of all skill levels. Whether you're fixing a bug, adding a feature, improving documentation, or suggesting enhancements, your contributions help make ReportB24 better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Contributing Code](#contributing-code)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security Considerations](#security-considerations)
- [Community and Support](#community-and-support)
- [Recognition](#recognition)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand what actions will and will not be tolerated.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (we officially support Python 3.8-3.12)
- **pip** (Python package installer)
- **Git** for version control
- **Virtual environment tools** (venv, virtualenv, or conda)

### Development Environment Setup

1. **Fork and Clone the Repository**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/ReportB24.git
   cd ReportB24
   ```

2. **Create a Virtual Environment**
   ```bash
   # Using venv (recommended)
   python -m venv .venv
   
   # Activate the virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Install development dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Set Up Configuration**
   ```bash
   # Copy example configuration files
   cp .env-example .env
   cp config.ini.example config.ini
   
   # Edit .env with your Bitrix24 credentials (for testing)
   # Never commit real credentials!
   ```

5. **Run Tests to Verify Setup**
   ```bash
   pytest
   # Should show: 261 passed, X warnings
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please:

1. **Check existing issues** to see if the bug has already been reported
2. **Update to the latest version** to see if the issue persists
3. **Test in a clean environment** to isolate the issue

**When creating a bug report**, include:

- **Clear title** describing the issue
- **Steps to reproduce** the bug
- **Expected vs actual behavior**
- **Environment details**: OS, Python version, ReportB24 version
- **Log output** or error messages (with sensitive data removed)
- **Screenshots** if relevant

**Use the bug report template**: [Create Bug Report](../../issues/new?template=bug_report.md)

### Suggesting Enhancements

We welcome feature requests and enhancement suggestions! Before submitting:

1. **Check existing feature requests** in the issues
2. **Consider if the feature fits** the project's scope and goals
3. **Think about implementation** and potential impacts

**When suggesting enhancements**, include:

- **Clear description** of the proposed feature
- **Use case scenarios** where this would be helpful
- **Proposed implementation** approach (if you have ideas)
- **Alternative solutions** you've considered
- **Mock-ups or examples** if applicable

**Use the feature request template**: [Create Feature Request](../../issues/new?template=feature_request.md)

### Contributing Code

#### Types of Contributions We Welcome

- 🐛 **Bug fixes**
- ✨ **New features** (please discuss in an issue first)
- 📚 **Documentation improvements**
- 🧪 **Test coverage improvements**
- 🔧 **Performance optimizations**
- 🌐 **Internationalization/localization**
- 🎨 **Code quality improvements**

#### Before You Start Coding

1. **Create or comment on an issue** to discuss your planned changes
2. **Wait for maintainer feedback** for significant changes
3. **Check if someone else is already working** on the same issue

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

```
feature/webhook-url-validation
fix/excel-generation-encoding
docs/api-reference-update
refactor/config-reader-improvements
test/bitrix24-client-coverage
```

### Step-by-Step Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test files
   pytest tests/test_your_module.py
   
   # Check test coverage
   pytest --cov=src
   ```

4. **Format your code**
   ```bash
   # Format with Black
   black src tests
   
   # Sort imports
   isort src tests
   
   # Lint with flake8
   flake8 src tests
   ```

5. **Commit your changes**
   ```bash
   # Use conventional commit format
   git commit -m "feat: add webhook URL validation
   
   - Add comprehensive URL validation for Bitrix24 webhooks
   - Include proper error messages for invalid URLs
   - Add unit tests for validation logic
   
   Closes #123"
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a PR on GitHub with a clear description.

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some specific preferences:

- **Line length**: 88 characters (Black default)
- **String quotes**: Double quotes for strings, single quotes for dict keys
- **Import order**: Standard library, third-party, local imports
- **Docstrings**: Google-style docstrings for all public functions/classes

### Code Formatting Tools

- **Black**: Code formatting (required)
- **isort**: Import sorting (required)
- **flake8**: Linting (warnings should be addressed)
- **mypy**: Type checking (recommended for new code)

### Type Hints

Use type hints for new code:

```python
from typing import Dict, List, Optional

def process_invoices(data: List[Dict[str, str]]) -> Optional[str]:
    """Process invoice data and return Excel file path."""
    pass
```

### Security Considerations

- **Never commit credentials** or sensitive data
- **Use `.env` files** for configuration secrets
- **Validate all user inputs** thoroughly
- **Follow secure coding practices**
- **Mask sensitive data** in logs and error messages

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(config): add automatic secret migration from config.ini to .env
fix(excel): resolve encoding issues with Russian characters
docs(readme): update installation instructions for Python 3.12
test(client): add integration tests for Bitrix24Client
```

## Testing Guidelines

### Test Requirements

- **All new features** must include tests
- **Bug fixes** should include regression tests
- **Maintain 95%+ test coverage** for new code
- **Tests must pass** on all supported Python versions

### Test Structure

```
tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
├── fixtures/            # Test data and fixtures
└── conftest.py          # Pytest configuration
```

### Writing Tests

```python
import pytest
from src.your_module import YourClass

class TestYourClass:
    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        instance = YourClass()
        result = instance.method()
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case handling."""
        instance = YourClass()
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration

# Run tests in parallel
pytest -n auto
```

## Documentation

### Types of Documentation

- **Code comments**: For complex logic
- **Docstrings**: For all public functions/classes
- **README.md**: Project overview and quick start
- **API documentation**: Generated from docstrings
- **User guides**: Step-by-step tutorials

### Documentation Standards

- **Write clear, concise documentation**
- **Include code examples** where helpful
- **Update docs** when changing functionality
- **Use proper Markdown formatting**
- **Include Russian translations** for user-facing content

## Community and Support

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community chat
- **Pull Request Reviews**: Code discussion and feedback

### Getting Help

If you need help with your contribution:

1. **Check the documentation** and existing issues
2. **Ask in GitHub Discussions** for general questions
3. **Comment on relevant issues** for specific problems
4. **Reach out to maintainers** via GitHub for urgent matters

### Response Times

- **Bug reports**: Response within 2-3 business days
- **Feature requests**: Response within 1 week
- **Pull requests**: Initial review within 1 week
- **Questions**: Response within 2-3 business days

## Recognition

We appreciate all contributions! Contributors will be:

- **Listed in CONTRIBUTORS.md** file
- **Mentioned in release notes** for significant contributions
- **Credited in commit messages** and pull requests
- **Thanked publicly** in our community channels

### Hall of Fame

Check out our amazing contributors in [CONTRIBUTORS.md](CONTRIBUTORS.md)!

## Final Notes

### Before Your First Contribution

- Read through this guide completely
- Set up your development environment
- Start with a small issue to get familiar with the workflow
- Don't hesitate to ask questions!

### Project Goals

Remember that ReportB24 aims to be:

- **Secure**: Protecting sensitive business data
- **Reliable**: Stable and consistent performance
- **User-friendly**: Easy to set up and use
- **Well-documented**: Clear instructions and examples
- **Community-driven**: Welcoming to contributors

**Thank you for contributing to ReportB24!** 🚀

Your contributions help businesses generate better reports and streamline their workflows. Together, we're building something valuable for the community.

---

**Questions?** Feel free to reach out by [creating an issue](../../issues/new) or starting a [discussion](../../discussions).

**Ready to contribute?** Check out our [good first issues](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to get started! 