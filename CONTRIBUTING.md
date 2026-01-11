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

## Adding a New Handler

Aragora uses modular HTTP handlers in `aragora/server/handlers/`. Each handler owns a set of endpoints.

### Handler Structure

Create a new file in `aragora/server/handlers/`:

```python
"""
Your Handler - Brief description.

Endpoints:
- GET /api/yourfeature - List items
- GET /api/yourfeature/{id} - Get specific item
- POST /api/yourfeature - Create item
"""

from typing import Any
from .base import BaseHandler, json_response, error_response, handle_errors
from .utils.rate_limit import rate_limit

class YourHandler(BaseHandler):
    """Handler for your feature endpoints."""

    ROUTES = [
        "/api/yourfeature",
        "/api/yourfeature/*",
    ]

    def can_handle(self, path: str, method: str) -> bool:
        """Check if this handler can handle the request."""
        return path.startswith("/api/yourfeature")

    @handle_errors
    @rate_limit(rpm=60)
    async def handle(self, path: str, method: str, handler: Any = None):
        """Route request to appropriate method."""
        if path == "/api/yourfeature" and method == "GET":
            return self._list_items()
        # ... more routing
        return None

    def _list_items(self):
        return json_response({"items": [], "total": 0})
```

### Registration

1. Import your handler in `aragora/server/handlers/__init__.py`:
   ```python
   from .yourfeature import YourHandler
   ```

2. Add to `ALL_HANDLERS` list (order matters - more specific handlers first):
   ```python
   ALL_HANDLERS = [
       # ... existing handlers
       YourHandler,
   ]
   ```

3. Set stability level in `HANDLER_STABILITY`:
   ```python
   HANDLER_STABILITY: dict[str, Stability] = {
       # ...
       "YourHandler": Stability.PREVIEW,  # Start as PREVIEW
   }
   ```

4. Add to `__all__` exports.

### Stability Levels

| Level | Meaning | Usage |
|-------|---------|-------|
| `STABLE` | Production-ready, API stable | Core features |
| `EXPERIMENTAL` | Works but may change | New features |
| `PREVIEW` | Early access, expect issues | Alpha features |
| `DEPRECATED` | Being phased out | Legacy code |

### Handler Testing

Create tests in `tests/test_handlers_yourfeature.py`:

```python
import pytest
from aragora.server.handlers.yourfeature import YourHandler

class TestYourHandler:
    def setup_method(self):
        self.handler = YourHandler({})

    def test_can_handle_routes(self):
        assert self.handler.can_handle("/api/yourfeature", "GET")
        assert not self.handler.can_handle("/api/other", "GET")

    def test_list_items(self):
        result = self.handler._list_items()
        assert result["total"] == 0
```

## Adding a Dashboard Page

Frontend pages live in `aragora/live/src/app/`.

### Page Structure

Create `aragora/live/src/app/yourfeature/page.tsx`:

```tsx
'use client';

import Link from 'next/link';
import dynamic from 'next/dynamic';
import { Scanlines, CRTVignette } from '@/components/MatrixRain';
import { AsciiBannerCompact } from '@/components/AsciiBanner';
import { ThemeToggle } from '@/components/ThemeToggle';
import { BackendSelector, useBackend } from '@/components/BackendSelector';
import { PanelErrorBoundary } from '@/components/PanelErrorBoundary';

const YourPanel = dynamic(
  () => import('@/components/YourPanel').then(m => ({ default: m.YourPanel })),
  { ssr: false, loading: () => <div className="animate-pulse h-96 bg-surface" /> }
);

export default function YourFeaturePage() {
  const { config } = useBackend();

  return (
    <>
      <Scanlines opacity={0.02} />
      <CRTVignette />
      <main className="min-h-screen bg-bg text-text">
        {/* Header, content, footer - see existing pages */}
        <PanelErrorBoundary panelName="Your Feature">
          <YourPanel apiBase={config.api} />
        </PanelErrorBoundary>
      </main>
    </>
  );
}
```

### Component Patterns

- Use `dynamic` imports for code splitting
- Wrap in `PanelErrorBoundary` for resilience
- Use `useBackend()` hook for API base URL
- Follow the cyberpunk/matrix visual theme

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
