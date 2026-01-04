# Contributing to Aragora

Thank you for your interest in contributing to Aragora! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the live dashboard)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/an0mium/aragora.git
cd aragora

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install
```

### Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- `GEMINI_API_KEY` - Google Gemini API
- `ANTHROPIC_API_KEY` - Anthropic Claude API
- `OPENAI_API_KEY` - OpenAI API (for Codex)
- `XAI_API_KEY` - xAI Grok API

## Code Style

### Python

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use docstrings for public functions and classes

### TypeScript/JavaScript

- Use TypeScript for new code
- Follow the existing code style
- Use ESLint configuration

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, atomic commits

3. **Run tests** before submitting:
   ```bash
   pytest tests/
   ```

4. **Update documentation** if needed

5. **Submit a pull request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes

## Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(debate): add conviction-weighted voting
fix(server): prevent path traversal in static file serving
docs(readme): update installation instructions
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aragora

# Run specific test file
pytest tests/test_debate.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Include both positive and negative test cases

## Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Report security vulnerabilities privately to the maintainers

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions in GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
