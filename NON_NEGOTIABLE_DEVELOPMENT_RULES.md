# Non-Negotiable Development Rules

These rules apply to all work across frontend and backend. They are mandatory and must be followed at all times.

## 1. Reuse Standard Infrastructure First
Always use the standard infrastructure setup from:

`/Users/puneetsharma/Workspace/projects/ai-lab/ai-infra/docker-compose.yml`

Before adding any new infrastructure, always check this file first.
If the required service already exists there, reuse it.
Do not create duplicate infrastructure.
Only add missing infrastructure locally when it is genuinely not available in the standard setup.

## 2. Never Commit to Git
Never commit code to Git.
Never push code to Git.
Never create commits, branches, or pull requests as part of the implementation workflow.
Local file changes are allowed.
Docker image build and Docker image push are allowed.
Git commit and Git push are forbidden.

## 3. TDD Is Mandatory
All development must follow test-driven development wherever practical.

For backend:
- write or update tests first
- implement the minimum code to make tests pass
- refactor safely after tests pass

For frontend:
- write or update component, logic, or integration tests alongside implementation
- validate key user flows
- verify interactive behavior, state handling, and rendering logic

No feature should be treated as complete without test coverage appropriate to its scope.

## 4. Dockerization Is Mandatory
All deliverables must be runnable in containers where applicable.
Backend services must always have a proper Dockerfile.
Frontend applications must also be containerized when part of the delivery workflow.
The solution is not complete until it can be built and run in Docker.

## 5. Docker Image Build Is Required
Do not stop at code completion.
Always build the Docker image for the service or application being worked on.
If the image does not build successfully, the work is not complete.

## 6. Docker Image Push Is Allowed
Docker image push is allowed when required by the workflow.
Do not confuse Docker registry push with Git push.
Docker push is permitted.
Git push is forbidden.

## 7. Keep Frontend and Backend Cleanly Structured
Code must be organized and maintainable.

Frontend should have clear separation between:
- pages
- components
- hooks
- services or API clients
- state management
- styling or theme system
- tests

Backend should have clear separation between:
- controllers or routes
- validation
- services
- domain logic
- repositories
- infrastructure adapters
- configuration
- tests

Do not mix concerns carelessly.
Do not place business logic in controllers or presentation code.

## 8. Reuse Existing Patterns Before Creating New Ones
Before introducing new abstractions, folders, helpers, patterns, or architectural styles, first inspect the codebase and reuse existing conventions where reasonable.
Do not invent unnecessary patterns.
Do not create parallel styles of implementation without clear need.

## 9. Configuration Must Be Externalized
All runtime configuration must come from:
- environment variables
- config files
- Docker Compose wiring
- clearly defined runtime settings

Do not hardcode secrets.
Do not hardcode URLs, database credentials, tokens, or service endpoints unless explicitly justified for local-only temporary use.

## 10. Input Validation Is Mandatory
All external input must be validated.

For backend:
- validate request payloads
- validate query params, path params, and config

For frontend:
- validate user input
- handle invalid states clearly
- do not trust uncontrolled or malformed data

## 11. Error Handling Must Be Explicit
Do not allow silent failures.
Do not swallow exceptions.
Do not hide broken states.

Frontend must show clean and meaningful error states.
Backend must return structured and useful error responses.
Logs must preserve enough detail for troubleshooting.

## 12. Logging Must Be Meaningful
Add meaningful logging where it helps operations and debugging.

Backend logs should include:
- startup information
- dependency connection status
- key processing steps
- failures and context

Frontend logging should be minimal and intentional.
Do not leave noisy debug logs in delivered code.
Use proper error reporting patterns instead of random console output.

## 13. UI and API Consistency Matter
Frontend and backend must align on:
- naming
- contracts
- request and response shape
- field meaning
- validation expectations
- status handling

Do not let frontend assumptions drift away from backend reality.

## 14. Keep the Color and UI System Consistent
Frontend must follow the defined UI instruction sets and theme rules.
Do not introduce random colors, spacing systems, component styles, or visual patterns.
Any new UI must remain consistent with the established product design language.

## 15. Accessibility and Readability Matter
Frontend must maintain readable typography, sensible contrast, clear interaction states, and keyboard-friendly behavior where relevant.
Do not sacrifice usability for visual styling.

## 16. Infra Additions Must Be Minimal
If infrastructure is missing from the shared standard setup, add only the minimum required locally.
Do not rebuild the infra stack from scratch.
Keep local additions aligned with the shared conventions and easy to remove later.

## 17. Local Run Must Work
The application must be runnable locally.
Do not leave the project in a partially wired state.
Frontend, backend, and required infra should be able to run together in a practical local workflow.

## 18. Health and Operational Readiness Matter
Backend services should provide health or readiness endpoints where appropriate.
Frontend should handle loading, empty, error, and success states properly.
Operational basics are part of the implementation, not optional extras.

## 19. No Fake Completion
Do not claim something is done unless it is actually implemented, tested, and build-validated.
If any part could not be completed, say so clearly.
Never pretend tests passed, images built, or integrations worked if they were not verified.

## 20. Final Delivery Must Include a Clear Summary
At the end of every task, provide:
- what was implemented
- what tests were added or updated
- what existing infrastructure was reused
- what infrastructure was added locally, if any
- what Docker image was built
- whether the image was pushed
- confirmation that no Git commit was made

## 21. These Rules Override Convenience
If there is any conflict between speed and discipline, follow these rules.
These rules are mandatory and non-negotiable.
