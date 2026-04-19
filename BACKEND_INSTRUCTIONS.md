# Backend Instruction Set
## Enterprise Delivery Rules for Backend Services

## Objective
Build backend services in a disciplined, production-style way using standard infrastructure, strong engineering practices, and strict delivery rules.

The backend implementation must be:
- clean
- modular
- test-driven
- containerized
- deployment-ready
- consistent with the existing standard infrastructure setup

---

## 1. Mandatory Infrastructure Rule

Always use the standard infrastructure setup from:

`/Users/puneetsharma/Workspace/projects/ai-lab/ai-infra/docker-compose.yml`

This is the default infrastructure source of truth.

### Required behavior
- Before introducing any new infrastructure dependency, first check whether it already exists in the standard infra setup above.
- Reuse existing infrastructure services and conventions wherever possible.
- Do not create duplicate infrastructure unnecessarily.
- If a required infra service is not available in the standard infra setup, then add the missing service in the local project setup only as needed.
- Any added infrastructure must follow the same style and structure as the standard infra setup.

### Infra-first principle
Always prefer:
- standard infra reuse
- consistency with existing setup
- minimal deviation
- clear service naming
- stable containerized runtime

---

## 2. Technology and Delivery Rules

### General Backend Expectations
The backend must always be created with:
- clear project structure
- modular service boundaries
- configuration-driven behavior
- proper environment variable handling
- strong logging
- exception handling
- health endpoints where relevant
- container support
- clean API contracts

### Non-Negotiable Engineering Principles
Always:
- use TDD
- write tests before or alongside implementation
- keep services runnable locally in Docker
- ensure backend can be built into an image
- ensure image can be pushed to Docker
- never commit anything to Git
- never perform Git commit operations
- never create or push Git commits even if asked
- local code changes are allowed
- Docker image build and Docker image push are allowed

---

## 3. TDD Rule

Backend development must always follow TDD.

### Required TDD flow
For every feature, bug fix, or enhancement:
1. understand the requirement clearly
2. define expected behavior
3. write or update failing tests first
4. implement the minimum code needed to pass the tests
5. refactor while keeping tests green
6. run the full relevant test suite
7. verify edge cases and error handling

### Testing expectations
Always include:
- unit tests
- service or business logic tests
- API/integration tests where appropriate
- negative path tests
- edge case coverage
- validation tests
- error handling tests

Tests should be:
- readable
- deterministic
- isolated
- meaningful
- maintainable

---

## 4. Docker and Image Rules

Every backend service must be containerized properly.

### Required behavior
- always create a proper Dockerfile for the backend service
- ensure the image builds successfully
- ensure the service can run with the existing or extended Docker Compose setup
- ensure dependencies are externalized via configuration
- ensure the image is suitable for local run and registry push

### Image handling rules
- always build the Docker image
- always tag the Docker image clearly
- push the image to Docker when requested or when part of the defined workflow
- do not skip image creation
- do not rely on source-only delivery if a runnable image is expected

### Strict restriction
- never commit to Git
- never push code to Git
- never create Git commits
- never assume Git operations are part of the workflow
- Docker image push is allowed
- Git commit/push is forbidden

---

## 5. Infra Reuse and Extension Rules

When the backend needs infra such as:
- databases
- vector databases
- object storage
- cache
- graph database
- LLM serving
- queue or messaging
- observability support

Always first check the standard infra file:
`/Users/puneetsharma/Workspace/projects/ai-lab/ai-infra/docker-compose.yml`

### Decision rule
- if the required infra already exists there, use it
- if the required infra is missing, add it in the project-local compose only
- keep names, ports, env style, and volume conventions aligned with the standard infra style

### Examples
Reuse if available:
- MSSQL
- Redis
- Neo4j
- MinIO
- Ollama
- Qdrant

Add locally only if missing:
- app-specific database
- message broker
- tracing collector
- specialty parser service
- one-off worker infra

---

## 6. Backend Architecture Rules

The backend should be structured with clear separation of concerns.

### Expected layers
Use clear layer boundaries such as:
- controller / route layer
- request validation layer
- service layer
- domain / business logic layer
- repository / persistence layer
- infrastructure / adapter layer
- configuration layer
- test layer

### Rules
- keep business logic out of controllers
- keep infrastructure concerns isolated
- avoid tightly coupling service code to framework details
- prefer interfaces or abstractions where appropriate
- make modules independently understandable
- design for maintainability, not shortcuts

---

## 7. API Design Rules

For backend APIs:
- design clean and predictable endpoints
- use explicit request and response schemas
- validate all inputs
- return meaningful error responses
- include health and readiness endpoints where appropriate
- support observability-friendly logs and error tracing
- keep naming consistent and domain-oriented

### API quality expectations
- no vague endpoint naming
- no hidden behavior
- no unvalidated payloads
- no silent failures
- no raw exception leaks

---

## 8. Configuration Rules

All configuration must be externalized.

Use:
- environment variables
- config files where appropriate
- Docker Compose env wiring
- safe defaults for local development

Do not:
- hardcode secrets
- hardcode infra endpoints unnecessarily
- mix local machine paths directly into business logic
- bury config values in source code

---

## 9. Logging and Error Handling

Always include:
- structured logging where practical
- meaningful log messages
- startup logs
- infra connection logs
- error logs with context
- retry-safe failure visibility

Error handling must:
- be explicit
- avoid silent swallowing
- surface useful diagnostics
- keep user-facing errors clean
- preserve internal troubleshooting detail in logs

---

## 10. Database and Persistence Rules

When working with persistence:
- define schema or model expectations clearly
- handle migrations or initialization cleanly
- isolate repository logic
- test persistence behavior
- validate query behavior and edge cases
- ensure containerized runtime compatibility

If using shared infra from the standard compose, configure services to connect cleanly using compose service names and env variables.

---

## 11. Project Execution Rules for Claude / AI Agent

When implementing backend work, always follow this execution order:

1. inspect the existing codebase and project structure
2. inspect the standard infra file at  
   `/Users/puneetsharma/Workspace/projects/ai-lab/ai-infra/docker-compose.yml`
3. determine whether required infra already exists
4. define the implementation plan
5. write tests first
6. implement backend code
7. add or update Dockerfile
8. add or update Docker Compose integration only if needed
9. run tests
10. build Docker image
11. push Docker image when part of the workflow
12. never commit to Git

---

## 12. Rules for Missing Infrastructure

If required infrastructure is not available in the standard infra setup:
- add only the missing pieces
- do not rebuild the whole infra from scratch
- keep additions minimal and consistent
- document why the new infra was needed
- make the new service containerized and compose-ready
- keep project infra additions isolated and easy to remove later if absorbed into the shared infra

---

## 13. Quality Bar

The final backend must be:
- test-covered
- containerized
- reproducible
- infra-aware
- easy to run locally
- consistent with shared infra standards
- ready for Docker image build and push
- not committed to Git

---

## 14. Forbidden Actions

Never do the following:
- never commit code to Git
- never push code to Git
- never create branches unless explicitly required for local organization and still without commit
- never bypass tests without stating it clearly
- never hardcode secrets
- never create duplicate infra without checking the standard infra first
- never skip Docker image creation for backend delivery

---

## 15. Delivery Summary Rule

For every completed backend task, provide:
- what was implemented
- what tests were added or updated
- what infra was reused from the standard compose
- what infra was added locally, if any
- Docker image name and tag used
- whether image was built
- whether image was pushed
- explicit confirmation that no Git commit was made
