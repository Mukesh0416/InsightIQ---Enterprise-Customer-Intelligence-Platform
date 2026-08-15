# Development Guidelines

## 1. Project Structure Guidelines

The repository should be organized to support clear separation of concerns, maintainability, and scalability for a multi-team SaaS platform.

### Repository Structure

- Root-level configuration files for tooling, dependency management, and CI/CD
- Separate frontend and backend directories to isolate concerns
- Shared documentation under a docs folder
- Environment and deployment configuration in dedicated folders
- Tests colocated near the code they validate

### Suggested Top-Level Structure

```text
/README.md
/docs/
/frontend/
/backend/
/infrastructure/
/.github/workflows/
/docker/
/tests/
```

### Backend Structure

```text
/backend/app/
  /api/
  /core/
  /services/
  /repositories/
  /schemas/
  /models/
  /dependencies/
  /auth/
  /middleware/
  /utils/
  /exceptions/
  /tasks/
  /tests/
```

### Frontend Structure

```text
/frontend/src/
  /components/
  /pages/
  /features/
  /hooks/
  /services/
  /stores/
  /types/
  /utils/
  /styles/
  /tests/
```

### Guidelines

- Keep modules focused on a single responsibility
- Prefer feature-based grouping when a module contains related domain logic
- Avoid circular dependencies
- Keep infrastructure concerns out of domain code
- Ensure new folders and modules are introduced only when they improve clarity

---

## 2. Folder Naming Conventions

Use lowercase, descriptive names and prefer kebab-case or snake_case consistently where the stack expects it.

### General Rules

- Use lowercase for all folder names
- Use hyphen-separated names for general-purpose folders when appropriate
- Use domain-oriented names instead of generic names
- Avoid ambiguous abbreviations unless widely accepted

### Recommended Examples

- auth/
- analytics/
- datasets/
- notifications/
- reporting/
- admin/
- tests/
- utils/

### Avoid

- Auth/
- AnalyticsModule/
- dataSets/
- misc/

---

## 3. File Naming Standards

Use descriptive names that communicate purpose without adding unnecessary verbosity.

### Python

- Use snake_case for files and modules
- Example: user_service.py, dataset_validator.py

### TypeScript / React

- Use camelCase for files that export functions or components
- Example: authFlow.ts, userTable.tsx
- Use PascalCase for React component files: UserProfileCard.tsx

### General Rules

- Name files after the primary responsibility they contain
- Avoid files with vague names such as utils.ts unless the module is genuinely general-purpose
- Keep test files aligned with the module under test, such as user_service_test.py or UserProfileCard.test.tsx

---

## 4. Python Coding Standards (PEP8)

All Python code should follow PEP 8 and the project’s agreed conventions.

### Style Rules

- Use 4 spaces for indentation
- Keep lines under 88 characters where possible
- Use snake_case for functions, methods, variables, and modules
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Avoid wildcard imports
- Prefer explicit imports over implicit ones

### Formatting

- Use Ruff or Black for formatting consistency
- Run linting before merge
- Prefer type hints for function signatures and public methods

### Example Conventions

```python
from typing import Optional

class DatasetService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def get_dataset(self, dataset_id: str) -> Optional[dict]:
        return self.repository.find_by_id(dataset_id)
```

### Additional Rules

- Avoid deeply nested logic
- Keep functions small and focused
- Prefer composition over inheritance where practical
- Use dependency injection for services and repositories
- Avoid using mutable default arguments

---

## 5. TypeScript Coding Standards

TypeScript should be written in a clear, strongly typed, maintainable style.

### Style Rules

- Use TypeScript for all frontend code
- Prefer strict mode in tsconfig
- Use interfaces or type aliases for domain models
- Avoid any unless absolutely necessary
- Use descriptive names for props, hooks, and state values

### Component Guidelines

- Keep components focused and reusable
- Prefer functional components and hooks
- Avoid large inline component logic
- Keep component props typed and minimal

### Example

```ts
interface UserCardProps {
  userName: string;
  role: string;
  isActive: boolean;
}

export function UserCard({ userName, role, isActive }: UserCardProps) {
  return <div>{userName}</div>;
}
```

### Additional Rules

- Prefer early returns over deeply nested conditionals
- Use enums or const objects for fixed sets of values
- Keep side effects inside hooks or service layers
- Avoid mixing business logic directly into UI components

---

## 6. API Development Standards

The backend API should be consistent, versioned, predictable, and easy to consume.

### API Design Principles

- Use RESTful conventions
- Version APIs under /api/v1/
- Keep endpoints resource-oriented
- Use plural nouns for collections
- Use consistent response structures
- Return clear and consistent error objects

### Request/Response Rules

- Validate all input at the API boundary
- Use explicit status codes
- Avoid leaking internal implementation details in responses
- Document public endpoints clearly
- Keep request and response payloads consistent across similar resources

### Response Format

- Standard success payload should include metadata where appropriate
- Standard errors should include status, error code, message, and details

### API Documentation

- Public APIs must be documented using OpenAPI-compatible documentation
- Keep examples current and representative of real behavior

---

## 7. Database Standards

Database access must be safe, predictable, and maintainable.

### Principles

- Use PostgreSQL as the system of record
- Prefer explicit migrations over manual schema changes
- Keep schema changes versioned
- Avoid direct edits in production environments
- Use transactions for multi-step writes where appropriate

### SQLAlchemy Rules

- Use ORM models consistently for application logic
- Keep repository logic separate from service logic
- Avoid long, complex queries inside route handlers
- Use indexes for frequently queried fields

### Data Guidelines

- Use UUIDs for primary keys where appropriate
- Avoid storing denormalized data unless it is necessary for performance
- Enforce constraints at the database layer when possible
- Treat data integrity as a priority

---

## 8. Error Handling Guidelines

Error handling must be consistent across the codebase and provide actionable feedback.

### General Rules

- Never allow unhandled exceptions to escape without being transformed into a safe response
- Catch exceptions at the boundary where they can be meaningfully handled
- Use domain-specific exception classes where useful
- Return user-friendly messages while preserving internal diagnostics for logs

### Principles

- Fail fast for invalid input
- Do not expose stack traces in user-visible responses
- Capture enough context for debugging without exposing secrets
- Handle expected failures explicitly

### Recommended Pattern

- Validation errors: 400 or 422
- Authentication failures: 401 or 403
- Resource not found: 404
- Conflict: 409
- Internal failures: 500 with safe message

---

## 9. Logging Standards

Logging should support debugging, operations, and compliance needs in a structured and consistent manner.

### Log Levels

- INFO: Normal progress and useful lifecycle events
- WARNING: Recoverable issues or suspicious but non-blocking conditions
- ERROR: Failures that need investigation
- CRITICAL: Severe failures that could affect availability or integrity

### Structured Logging

- Use structured logs with consistent fields such as:
  - timestamp
  - level
  - service
  - request_id
  - user_id
  - organization_id
  - event
  - message

### Logging Rules

- Do not log secrets, passwords, tokens, or sensitive PII unless explicitly required and secured
- Log the action that occurred, not just the exception
- Include correlation IDs for request tracing
- Avoid noisy logs in hot paths unless necessary

### Example

```json
{
  "timestamp": "2026-07-30T12:00:00Z",
  "level": "ERROR",
  "service": "backend",
  "event": "dataset_validation_failed",
  "request_id": "req-123",
  "message": "Dataset validation failed due to malformed rows"
}
```

---

## 10. Configuration Management

Configuration must be centralized, explicit, and environment-aware.

### Rules

- Keep configuration in environment-based sources or dedicated config modules
- Do not hardcode secrets in source files
- Use validated configuration objects in application startup
- Keep defaults secure and documented
- Separate development, test, staging, and production values

### Good Practices

- Provide example environment files for local setup
- Fail fast if required configuration is missing
- Keep configuration changes reviewable and versioned

---

## 11. Environment Variables

Environment variables must be used for all environment-specific values.

### Required Categories

- Application settings
- Database connection values
- Authentication secrets
- Storage and file system settings
- ML job configuration
- External service credentials

### Examples

- APP_ENV
- DATABASE_URL
- SECRET_KEY
- JWT_ALGORITHM
- JWT_ACCESS_TOKEN_EXPIRE_MINUTES
- AWS_S3_BUCKET or equivalent storage target
- REDIS_URL if caching is introduced

### Rules

- Do not commit real secrets
- Use .env.example as the documented template
- Validate values on startup
- Avoid using environment variables for large or complex configuration when a file or service is more appropriate

---

## 12. Git Branching Strategy

Use a GitFlow-inspired workflow to structure development and release work.

### Branches

- main: production-ready code
- develop: integration branch for ongoing development
- feature/*: new features or substantial enhancements
- bugfix/*: non-critical fixes that are not urgent
- hotfix/*: production-critical fixes
- release/*: stabilization branches for upcoming releases

### Workflow Rules

- Branch from develop for new features
- Merge feature branches back into develop through pull requests
- Use hotfix branches from main when production issues require urgent repair
- Merge hotfixes into both main and develop
- Use release branches for final stabilization before production deployment

---

## 13. Commit Message Convention

Use Conventional Commits for consistent history and changelog-friendly messages.

### Recommended Format

```text
<type>(<scope>): <short summary>
```

### Types

- feat: new feature
- fix: bug fix
- docs: documentation update
- test: test-related change
- refactor: code restructuring without behavior change
- perf: performance improvement
- ci: CI/CD workflow change

### Examples

- feat(auth): add login endpoint support
- fix(dataset): handle invalid file upload errors
- docs(api): update endpoint documentation
- test(auth): add login flow unit tests
- refactor(service): simplify validation orchestration
- perf(analytics): reduce dashboard query latency
- ci(deploy): add staging deployment workflow

---

## 14. Pull Request Guidelines

Pull requests should be small, reviewable, and clearly scoped.

### Requirements

- Create PRs against the correct target branch
- Keep PRs focused on a single concern whenever possible
- Include a clear title and summary
- Link related issues or work items
- Provide testing evidence and rollout notes where relevant
- Ensure all required checks pass before requesting review

### PR Checklist

- Code compiles or is otherwise valid
- Tests are added or updated where appropriate
- Documentation is updated when behavior changes
- Security and performance implications are considered
- No secrets or debug code are included

---

## 15. Code Review Checklist

Code review should focus on correctness, maintainability, security, and clarity.

### Review Checklist

- Does the change solve the intended problem?
- Is the code easy to understand and maintain?
- Are responsibilities clearly separated?
- Are edge cases handled?
- Are tests covering the change?
- Are error cases handled appropriately?
- Are security and privacy concerns addressed?
- Is the change consistent with project conventions?
- Are dependencies and configuration needs clearly documented?

### Review Expectations

- Be constructive and specific
- Ask questions rather than making assumptions
- Prefer actionable feedback
- Avoid style-only nitpicks when the broader intent is sound

---

## 16. Testing Standards

Testing is required at every level of the software lifecycle.

### Unit Testing

- Write unit tests for business logic, validators, reducers, services, and utilities
- Favor deterministic tests with clear setup and teardown
- Keep tests focused on behavior rather than implementation details

### Integration Testing

- Test interactions between backend services, repositories, and external dependencies
- Verify integration points such as auth, dataset workflows, and processing jobs

### API Testing

- Validate request/response behavior for public endpoints
- Test success, validation, authorization, and error paths

### ML Validation

- Validate model assumptions and output quality
- Track baseline metrics and regression thresholds
- Verify that model outputs remain explainable and reviewable

### Frontend Testing

- Test component rendering, validation, navigation, and state transitions
- Prefer tests for critical user journeys over exhaustive UI snapshots

### Coverage Requirements

- Target at least 80% coverage for critical modules
- Prioritize coverage on authentication, data validation, analytics logic, and ML workflows
- Do not accept untested changes for high-risk functionality

---

## 17. Documentation Standards

Documentation should be kept current and useful for both technical and non-technical stakeholders.

### README

- Provide an overview of the project and its goals
- Include setup instructions and environment prerequisites
- Document how to run the project locally
- Reference architecture and contribution guidance

### API Docs

- Keep endpoint docs updated with request/response examples
- Ensure auth, error handling, and versions are documented

### Architecture Docs

- Keep high-level design and system diagrams current
- Document major modules, integration boundaries, and deployment assumptions

### Inline Comments

- Use comments to explain why something is done, not what the code obviously does
- Avoid redundant comments in self-explanatory code

### Docstrings

- Use docstrings for public functions, classes, and modules where they add clarity
- Follow a consistent structure and provide practical context

---

## 18. Dependency Management

Dependencies must be managed carefully to avoid instability and unnecessary complexity.

### Rules

- Pin or lock versions for reproducible builds
- Review new dependencies carefully before adding them
- Prefer well-supported and well-documented libraries
- Avoid introducing unnecessary transitive dependencies
- Keep dependency updates intentional and reviewable

### Python

- Manage Python dependencies through a versioned requirements or project configuration file

### Frontend

- Use package management and lockfiles consistently
- Review bundle impact and compatibility when introducing new packages

---

## 19. Security Best Practices

Security must be treated as a first-class engineering concern.

### Core Practices

- Use HTTPS in all production deployments
- Store secrets in secure secret management systems
- Validate and sanitize all inputs
- Apply least-privilege access controls
- Enforce authentication and role-based access throughout the app
- Use secure password and token handling practices

### Additional Guidelines

- Avoid exposing raw stack traces in responses
- Restrict admin features to appropriate roles
- Use secure session and refresh token handling
- Scan dependencies regularly and address vulnerabilities promptly
- Apply secure defaults for configuration and deployment

---

## 20. Performance Best Practices

Performance should be designed into the product from the start.

### General Guidelines

- Optimize the critical path first: upload, validation, analytics, and reporting
- Avoid unnecessary network calls and duplicated requests
- Use pagination and filtering for large datasets and lists
- Cache data where it is safe and beneficial
- Profile performance when latency grows or user workflows slow down

### Frontend

- Keep components efficient and avoid excessive re-renders
- Defer non-critical UI work where possible
- Use loading states for asynchronous work

### Backend

- Keep database queries efficient and indexed
- Avoid N+1 query patterns
- Use background task processing for long-running jobs where appropriate

---

## 21. ML Development Standards

Machine learning workflows must be reproducible, observable, and auditable.

### Rules

- Keep training and inference logic separate where possible
- Use versioned datasets, features, and model metadata where practical
- Document model assumptions and limitations
- Validate outputs before presenting them to users
- Keep model explainability and reviewability in mind from the start

### Practices

- Use clear experiment tracking and logging for ML runs
- Separate development from production model artifacts
- Avoid shipping models without evaluation metrics
- Ensure predictions and insights are understandable to business users

---

## 22. Data Validation Standards

Data validation is a core business capability and must be reliable.

### Principles

- Validate input data at ingestion and before processing
- Detect duplicate, missing, malformed, and inconsistent values
- Surface findings in a human-readable way
- Preserve traces of validation outputs for auditing and review

### Rules

- Validate both structure and content where supported
- Provide severity levels for issues such as warnings and errors
- Allow users to review validation results before analysis proceeds
- Ensure failures are explicit and actionable

---

## 23. CI/CD Standards

Continuous integration and delivery should support quality, reliability, and repeatability.

### CI Requirements

- Run linting, formatting checks, and unit tests on pull requests
- Enforce build validation for frontend and backend
- Run security and dependency checks where appropriate
- Fail fast on broken changes

### CD Requirements

- Deploy using repeatable and versioned pipelines
- Separate development, staging, and production workflows
- Support rollback procedures
- Keep deployment logs and health checks accessible

### GitHub Actions Expectations

- Use workflow files for build, test, and deployment steps
- Apply environment protections to production deployments
- Require approvals or checks before production rollout where relevant

---

## 24. Release Process

Releases should be planned, tested, and executed deliberately.

### Release Checklist

- Confirm the release scope and target milestone
- Validate that all acceptance criteria are met
- Run regression and smoke tests
- Review deployment readiness and rollback plan
- Tag the release and document notable changes
- Deploy to staging first, then production
- Monitor health metrics after deployment

### Release Notes

- Include summary of changes
- Highlight breaking changes or migration considerations
- Document known issues and follow-up tasks

---

## 25. Summary

These guidelines establish a practical engineering standard for InsightIQ across architecture, development, testing, documentation, security, deployment, and release management. The goal is to ensure the platform remains maintainable, secure, scalable, and consistent as it grows from MVP to enterprise-grade production service.
