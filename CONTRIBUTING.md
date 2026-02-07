# Contributing to SensusAI

Thank you for your interest in contributing to SensusAI! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/SensusAI.git
   cd SensusAI
   ```

3. **Set up development environment**
   ```bash
   ./scripts/setup.sh
   ```

4. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

```bash
# All tests
make test

# Specific service
make test-ai
make test-collector

# With coverage
cd ai-service && pytest --cov=app
```

### Code Quality

```bash
# Lint
make lint

# Format
make lint-fix

# Type checking (Python)
cd ai-service && mypy app
```

### Running Locally

```bash
# Start services
make up

# View logs
make logs

# Send test data
make send-test-data
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add anomaly detection for network metrics
fix: correct database connection timeout
docs: update API documentation
test: add tests for Redis consumer
refactor: simplify authentication middleware
```

## Pull Request Process

1. **Update tests** - Add/update tests for your changes
2. **Update documentation** - Update README, ARCHITECTURE.md if needed
3. **Run tests and linting** - Ensure all checks pass
4. **Create pull request** with clear description
5. **Address review comments**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing done

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Project Structure

```
SensusAI/
├── collector/          # Go service
│   ├── main.go
│   └── main_test.go
├── ai-service/         # Python service
│   ├── app/
│   └── tests/
├── k8s/                # Kubernetes manifests
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

## Coding Standards

### Python (AI Service)
- **Style**: Follow PEP 8
- **Formatter**: Black (line length: 100)
- **Type hints**: Use for function signatures
- **Docstrings**: Google style

### Go (Collector)
- **Style**: Follow Go conventions
- **Formatter**: gofmt
- **Error handling**: Always check errors
- **Testing**: Table-driven tests

## Adding New Features

1. **Check existing issues** - Avoid duplicates
2. **Create an issue** - Discuss approach
3. **Implement**:
   - Write tests first (TDD)
   - Keep changes focused
   - Update documentation
4. **Submit PR**

## Reporting Bugs

Use GitHub Issues with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, versions)
- Logs/screenshots

## Questions?

- Open a GitHub issue
- Check [ARCHITECTURE.md](./ARCHITECTURE.md)
- Review existing PRs

Thank you for contributing! 🚀
