# Contributing to Rasch Counter Bot

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Docker (optional)

### Development Setup

1. **Fork va Clone**
```bash
git clone https://github.com/your-username/rasch_counter.git
cd rasch_counter
```

2. **Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. **Dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Environment Variables**
```bash
export TELEGRAM_TOKEN="your_bot_token"
export ADMIN_USER_ID="your_telegram_id"
```

## 📝 Git Workflow

### Branch Strategy
- `main` - Production ready code
- `develop` - Development branch
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical fixes

### Commit Convention
```
type(scope): description

Examples:
feat(bot): add new command handler
fix(model): correct Rasch calculation
docs(readme): update installation guide
test(utils): add error handling tests
refactor(database): simplify connection logic
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code formatting
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

### Pull Request Process

1. **Create Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

2. **Make Changes**
- Write clean, readable code
- Add tests for new features
- Update documentation
- Follow existing code style

3. **Test Your Changes**
```bash
# Run tests
pytest tests/ -v

# Run linting
flake8 src/ tests/
black --check src/ tests/
isort --check-only src/ tests/

# Run security checks
bandit -r src/
```

4. **Commit Changes**
```bash
git add .
git commit -m "feat(bot): add amazing new feature"
```

5. **Push and Create PR**
```bash
git push origin feature/amazing-feature
```

## 🧪 Testing

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_rasch_model.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests
- Test files should be in `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

## 📋 Code Standards

### Python Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small and focused

### File Organization
```
src/
├── bot/           # Telegram bot logic
├── models/        # Rasch model implementation
├── data_processing/ # Data processing utilities
├── utils/         # Helper functions
└── config/        # Configuration
```

### Error Handling
- Use try-except blocks appropriately
- Log errors with context
- Provide meaningful error messages
- Use the `@handle_errors` decorator

## 🔧 Development Tools

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Formatting
```bash
# Format code
black src/ tests/
isort src/ tests/

# Check formatting
black --check src/ tests/
isort --check-only src/ tests/
```

### Linting
```bash
# Run linter
flake8 src/ tests/

# Security check
bandit -r src/
```

## 🐛 Bug Reports

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

## 💡 Feature Requests

When requesting features:
- Describe the use case
- Explain why it's needed
- Provide examples if possible
- Consider implementation complexity

## 📞 Getting Help

- Create an issue for questions
- Join our discussions
- Check existing documentation

## 🎯 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release
5. Deploy to production

---

Thank you for contributing! 🎉
