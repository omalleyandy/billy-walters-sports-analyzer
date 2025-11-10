# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous delivery. The pipeline automatically validates code quality, runs tests, and checks for security issues on every pull request and push to main.

## Workflows

### Main CI Workflow (.github/workflows/ci.yml)

The main CI workflow consists of four jobs that run in parallel:

#### 1. Test Job
- **Matrix Strategy**: Runs on both Ubuntu and Windows with Python 3.11 and 3.12
- **Steps**:
  - Checkout code
  - Install uv package manager
  - Set up Python
  - Install dependencies with `uv sync`
  - Run pytest with coverage reporting
  - Upload coverage to Codecov (Ubuntu + Python 3.12 only)

#### 2. Lint Job
- **Platform**: Ubuntu with Python 3.12
- **Steps**:
  - Check code formatting with `ruff format --check`
  - Lint code with `ruff check`

#### 3. Type Check Job
- **Platform**: Ubuntu with Python 3.12
- **Steps**:
  - Run `pyright` for static type checking

#### 4. Security Job
- **Platform**: Ubuntu with Python 3.12
- **Steps**:
  - Run `pip-audit` to check for known vulnerabilities
  - Run TruffleHog to scan for secrets in code

## Dependabot Configuration (.github/dependabot.yml)

Dependabot automatically creates pull requests to update dependencies:

- **Python Dependencies**: Weekly updates on Mondays
- **GitHub Actions**: Weekly updates on Mondays
- **Pull Request Limits**: 10 for Python, 5 for GitHub Actions
- **Auto-labeling**: Adds `dependencies` label and ecosystem-specific labels
- **Conventional Commits**: Uses `chore(deps)` and `chore(ci)` prefixes

## Required Secrets

No secrets are required for the basic CI pipeline. Optional:

- `CODECOV_TOKEN`: For private repositories to upload coverage reports

## Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/yourusername/billy-walters-sports-analyzer/workflows/CI/badge.svg)
![Coverage](https://codecov.io/gh/yourusername/billy-walters-sports-analyzer/branch/main/graph/badge.svg)
```

## Local Development

Before pushing code, ensure it passes CI checks locally:

```bash
# Run tests
uv run pytest tests/ -v --cov=.

# Check formatting
uv run ruff format --check .

# Run linting
uv run ruff check .

# Type checking
uv run pyright
```

## Branch Protection Rules

Recommended branch protection settings for `main`:

1. Require pull request reviews before merging
2. Require status checks to pass before merging:
   - Test (all matrix combinations)
   - Lint and Format
   - Type Check
   - Security Scan
3. Require branches to be up to date before merging
4. Do not allow bypassing the above settings

## Troubleshooting

### Tests Failing in CI but Passing Locally
- Check Python version (CI runs on 3.11 and 3.12)
- Check OS differences (CI runs on Ubuntu and Windows)
- Verify dependencies are locked in uv.lock

### Formatting Failures
- Run `uv run ruff format .` locally before committing
- Ensure line length stays under 88 characters

### Type Check Failures
- Run `uv run pyright` locally
- Ensure all functions have type hints
- Check for Optional types that need explicit None checks

### Security Scan Failures
- TruffleHog found secrets: Remove and rotate the credential
- pip-audit found vulnerability: Update the affected package

## Maintenance

- Review and merge Dependabot PRs weekly
- Monitor CI run times and optimize if needed
- Update Python versions in matrix when new versions release
- Keep GitHub Actions up to date via Dependabot
