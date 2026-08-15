# Contributing to InsightIQ

Thank you for considering contributing to InsightIQ! This document outlines the
process for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project and everyone participating in it is governed by the
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By participating, you are expected
to uphold this code.

## Getting Started

1. Fork the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/insightiq.git
   ```
3. Set up the development environment:
   ```bash
   # Backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Frontend
   cd frontend
   npm install
   ```
4. Configure pre-commit hooks:
   ```bash
   pre-commit install
   ```
5. Copy environment template:
   ```bash
   cp .env.example .env
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes following the coding standards below.
3. Write or update tests as needed.
4. Run the full test suite locally before pushing.
5. Push your branch and open a pull request.

## Coding Standards

### Python (Backend)

- Follow **PEP 8** conventions.
- Code is formatted with **Black** (line length: 100).
- Linted with **Ruff** — all rules under the `B`, `E`, `F`, `I`, `N`, `W`
  categories are enforced.
- Type hints are required for all function signatures.
- Docstrings follow **Google-style** conventions.

### TypeScript / React (Frontend)

- Follow the project's **ESLint** and **Prettier** configuration.
- Use **functional components** with hooks (no class components).
- Prefer named exports over default exports.
- Co-locate tests with source files (`Component.test.tsx`).

### General

- Keep changes focused and atomic. One feature per commit.
- Write meaningful commit messages following
  [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:` – new feature
  - `fix:` – bug fix
  - `refactor:` – code change that neither fixes a bug nor adds a feature
  - `docs:` – documentation only
  - `test:` – adding or updating tests
  - `chore:` – maintenance tasks

## Testing

### Backend

- **pytest** for all Python tests.
- Run tests with:
  ```bash
  pytest
  ```
- Aim for at least 80% code coverage.

### Frontend

- **Vitest** + **Testing Library** for React component tests.
- Run tests with:
  ```bash
  cd frontend && npm test
  ```

## Pull Request Process

1. Ensure all CI checks pass (lint, type-check, test).
2. Update documentation if your changes introduce new behaviour.
3. Add a changelog entry under the `[Unreleased]` section in `CHANGELOG.md`.
4. Request review from at least one maintainer.
5. Squash commits before merging.

## Reporting Issues

- Use the GitHub issue tracker.
- Provide a clear and descriptive title.
- Include steps to reproduce, expected behaviour, and actual behaviour.
- Attach logs or screenshots where applicable.