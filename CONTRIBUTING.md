# Contributing to TRICKSTER-ORACLE

Thank you for your interest in contributing to Trickster Oracle! This is an educational project focused on transparent, interpretable probabilistic analytics.

## 🎯 Project Philosophy

Before contributing, please understand our core principles:

1. **Educational First**: We build tools to help people understand probability, not to promote gambling
2. **Transparency Over Accuracy**: We prioritize interpretability and explainability over raw prediction power
3. **Conservative Communication**: We use analytical language and always include appropriate caveats
4. **Scientific Rigor**: We implement well-documented statistical methods, not black boxes

## 📋 How to Contribute

### 1. Read the Documentation

- [README.md](./README.md) - Project overview and scope
- [GLOSSARY.md](./GLOSSARY.md) - **CRITICAL**: Terminology guidelines
- [ROADMAP.py](./ROADMAP.py) - Development plan and phases

### 2. Set Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Gahenax/TRIKSTER-ORACLE.git
cd TRIKSTER-ORACLE

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Run tests
pytest

# Frontend setup (when available)
cd ../frontend
npm install
npm run dev
```

### 3. Choose a Task

Check existing GitHub Issues for:
- `good-first-issue` - Beginner-friendly tasks
- `help-wanted` - Community contributions welcome
- `phase-N` - Tasks aligned with roadmap phases

Or propose new features via GitHub Discussions.

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Naming conventions:
- `feature/` - New functionality
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 5. Make Changes

Follow our coding standards:

#### Python (Backend)
- **Style**: Black formatter (line-length=100)
- **Linting**: Ruff
- **Type Hints**: Required for all public functions
- **Docstrings**: Required for all modules and public functions
- **Tests**: Required for all new features

```python
def calculate_probability(rating_a: float, rating_b: float) -> float:
    """
    Calculate win probability using ELO formula.
    
    Args:
        rating_a: ELO rating of competitor A
        rating_b: ELO rating of competitor B
        
    Returns:
        Probability that A wins (0.0 to 1.0)
        
    Example:
        >>> calculate_probability(1600, 1400)
        0.76
    """
    # Implementation
```

#### JavaScript/TypeScript (Frontend)
- **Style**: Prettier
- **Linting**: ESLint
- **Type Safety**: TypeScript strict mode
- **Components**: Functional components with hooks

#### Terminology Compliance
**This is non-negotiable. All contributions MUST follow GLOSSARY.md.**

Before submitting:
1. Run: `python backend/app/core/explain.py` (will validate terminology)
2. Search your code for forbidden terms: `bet`, `pick`, `odd`, `guaranteed`, etc.
3. Ensure UI text includes disclaimers and caveats

### 6. Write Tests

All new features require tests:

```bash
# Backend tests
cd backend
pytest app/tests/test_your_feature.py -v

# Ensure determinism for simulations
def test_engine_determinism():
    result1 = simulate_event(event, seed=42)
    result2 = simulate_event(event, seed=42)
    assert result1 == result2
```

Test coverage expectations:
- Core engine: 100%
- API endpoints: 90%+
- UI components: 80%+

### 7. Run Quality Checks

```bash
# Format code
black backend/app --line-length 100

# Lint
ruff check backend/app

# Type check
mypy backend/app

# Run all tests
pytest backend/app/tests/ -v --cov
```

### 8. Commit Your Changes

Use conventional commit format:

```bash
git commit -m "feat: add support for basketball ELO model"
git commit -m "fix: correct CI calculation for small sample sizes"
git commit -m "docs: update README with deployment instructions"
git commit -m "test: add determinism tests for risk module"
```

Commit message prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `chore:` - Maintenance tasks

For roadmap tasks, use format: `T#.# — Description`
Example: `T1.1 — Implement Monte Carlo engine with deterministic seeding`

### 9. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

**Title**: Clear, concise description
**Description**:
```markdown
## What
Brief description of changes

## Why
Problem being solved or feature being added

## How
Technical approach summary

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] No forbidden terminology (checked GLOSSARY.md)
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or migration guide provided)
```

## 🚫 What NOT to Contribute

We will reject contributions that:

1. **Use gambling/betting language** → Check GLOSSARY.md
2. **Promise prediction accuracy** → We estimate, never guarantee
3. **Remove caveats/disclaimers** → Transparency is non-negotiable
4. **Add external betting APIs** → This is educational, not a betting tool
5. **Implement "guaranteed winner" logic** → Violates project philosophy
6. **Skip tests** → Quality over speed
7. **Use proprietary/closed-source models** → We prioritize interpretability

## 🐛 Reporting Bugs

Use GitHub Issues with template:

```markdown
**Describe the bug**
Clear description of what's wrong

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 11]
- Python version: [e.g., 3.11.5]
- Browser: [e.g., Chrome 120]

**Additional context**
Screenshots, logs, etc.
```

## 💡 Suggesting Features

Use GitHub Discussions for:
- New sports to support
- Additional statistical models
- UI/UX improvements
- Performance optimizations
- Educational content ideas

**Before suggesting**, check:
1. Does it align with educational goals?
2. Does it increase transparency or decrease it?
3. Is it feasible for a demo/MVP?

## 🤝 Code of Conduct

- Be respectful and professional
- Assume good intent
- Provide constructive feedback
- Focus on ideas, not people
- Help newcomers learn

## 📚 Resources

- [ROADMAP.py](./ROADMAP.py) - Full development plan
- [GLOSSARY.md](./GLOSSARY.md) - Terminology guide
- [Monte Carlo Simulation (Wikipedia)](https://en.wikipedia.org/wiki/Monte_Carlo_method)
- [ELO Rating System](https://en.wikipedia.org/wiki/Elo_rating_system)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)

## ❓ Questions?

- **General questions**: GitHub Discussions
- **Bug reports**: GitHub Issues
- **Security issues**: Email gahenax@gahenaxaisolutions.com
- **Roadmap questions**: See ROADMAP.py or create Discussion

## 🙏 Thank You!

Every contribution, no matter how small, helps make probabilistic analysis more accessible and understandable. We appreciate your time and effort!

---

**Remember**: Our mission is education and transparency. Every line of code should serve that goal.
