# InsightIQ

**Enterprise Customer Intelligence Platform**

InsightIQ is a production-grade SaaS platform for customer intelligence,
analytics, segmentation, churn prediction, forecasting, and reporting.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Docker](#docker)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [License](#license)

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  Backend API │────▶│  PostgreSQL  │
│  React + Vite│     │ FastAPI/Pyd. │     │   (Primary)  │
└──────────────┘     └──────────────┘     └──────────────┘
```

- **Frontend**: Single-page application built with React 19, TypeScript, and
  Vite. Tailwind CSS for styling. TanStack Query for server-state management.
- **Backend**: Modular FastAPI application following clean architecture
  principles. SQLAlchemy ORM with Alembic migrations. Pydantic v2 for
  validation.
- **Database**: PostgreSQL 16 (primary data store).
- **Infrastructure**: Docker Compose for local development. GitHub Actions
  for CI.

## Repository Structure

```
insightiq/
├── .github/workflows/    # CI/CD pipeline definitions
├── backend/
│   └── app/
│       ├── api/          # Route handlers (to be implemented)
│       ├── config/       # Application configuration
│       ├── core/         # Core domain logic
│       ├── database/     # SQLAlchemy engine & session
│       ├── dependencies/ # FastAPI dependency injection
│       ├── exceptions/   # Custom exception classes
│       ├── logging/      # Logging configuration
│       ├── middleware/    # ASGI middleware
│       ├── models/       # SQLAlchemy ORM models
│       ├── repositories/ # Data access layer
│       ├── schemas/      # Pydantic request/response schemas
│       ├── services/     # Business logic layer
│       ├── tasks/        # Background / scheduled tasks
│       ├── utils/        # Shared utilities
│       └── main.py       # FastAPI application entry point
├── datasets/             # Sample / reference datasets
├── docs/                 # Project documentation
├── frontend/
│   └── src/
│       ├── assets/       # Static assets (images, fonts)
│       ├── components/   # Reusable UI components
│       ├── contexts/     # React context providers
│       ├── hooks/        # Custom React hooks
│       ├── layouts/      # Page layout components
│       ├── pages/        # Route-level page components
│       ├── routes/       # Route definitions
│       ├── services/     # API client & data fetching
│       ├── styles/       # Global styles & Tailwind config
│       ├── types/        # TypeScript type definitions
│       ├── utils/        # Utility functions
│       └── main.tsx      # Application entry point
├── ml_pipeline/          # ML experimentation modules
├── scripts/              # Operational / automation scripts
├── tests/                # End-to-end and integration tests
├── .editorconfig
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── nginx.conf
├── package.json
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── SECURITY.md
```

## Technology Stack

### Backend

| Component       | Technology                         |
|-----------------|------------------------------------|
| Language        | Python 3.12                        |
| Framework       | FastAPI 0.115+                     |
| ORM             | SQLAlchemy 2.0+                    |
| Migrations      | Alembic 1.13+                      |
| Validation      | Pydantic 2.8+                      |
| Database        | PostgreSQL 16                      |
| Testing         | pytest 8.3+, pytest-cov            |
| Linting         | Ruff 0.6+                          |
| Formatting      | Black 24.10+                       |
| Type Checking   | Mypy 1.11+                         |

### Frontend

| Component       | Technology                         |
|-----------------|------------------------------------|
| Language        | TypeScript 5.6+                    |
| Framework       | React 19                           |
| Build Tool      | Vite 5.4+                          |
| Styling         | Tailwind CSS 3.4+                  |
| State Mgmt      | TanStack Query 5+                  |
| Routing         | React Router 7+                    |
| Charts          | Chart.js 4+, Plotly.js             |
| HTTP Client     | Axios 1.7+                         |
| Testing         | Vitest 2.1+, Testing Library       |
| Linting         | ESLint 9+                          |
| Formatting      | Prettier 3.3+                      |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or Docker)
- Docker & Docker Compose (optional, for containerised setup)

### Local Development (without Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/insightiq.git
   cd insightiq
   ```

2. **Set up the backend:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend:**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

7. **Start the frontend (in a separate terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

8. Open http://localhost:5173 in your browser.

### Docker Setup (recommended)

```bash
docker compose up -d
```

This starts the API (port 8000), frontend (port 5173), and PostgreSQL
(port 5432).

## Development

### Pre-commit Hooks

Install pre-commit hooks to automatically lint and format code before
committing:

```bash
pre-commit install
```

The hooks run Ruff, Black, Prettier, and general checks on every commit.

### Code Quality

```bash
# Backend linting & formatting
ruff check backend/
ruff format --check backend/
black --check backend/

# Frontend linting & formatting
cd frontend
npm run lint
npm run format:check
```

## Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test

# With coverage
pytest --cov=backend
cd frontend && npm run test:coverage
```

## Docker

### Services

| Service   | Port  | Description                          |
|-----------|-------|--------------------------------------|
| `api`     | 8000  | FastAPI backend (with hot-reload)    |
| `frontend`| 5173  | Vite dev server (with HMR)           |
| `db`      | 5432  | PostgreSQL 16 database               |

### Commands

```bash
docker compose up -d              # Start all services
docker compose down               # Stop all services
docker compose logs -f            # Tail logs
docker compose exec api bash      # Open shell in API container
docker compose exec db psql -U postgres insightiq  # Open database shell
```

## CI/CD

Continuous Integration is handled by GitHub Actions:

- **Lint**: Ruff (Python) + ESLint (TypeScript)
- **Type Check**: Mypy (Python) + TypeScript compiler
- **Test**: pytest (Python) + Vitest (TypeScript)
- **Build**: Vite production build

The workflow runs on every push to `main` and on every pull request.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of
conduct, development workflow, and the process for submitting pull requests.

## License

This project is licensed under the MIT License — see the
[LICENSE](LICENSE) file for details.