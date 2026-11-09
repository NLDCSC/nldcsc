## Git Workflow
- Never create commits or push branches/remotes unless explicitly asked. Leave changes in the working tree for the
  user to review, commit, and push.
- Do not revert or discard unrelated worktree changes.

## Testing Guidelines
- Keep verification proportional to the change. Prefer focused existing tests, syntax checks, or the relevant 
  build/lint command over broad test runs.
- Add tests for meaningful behavior and regressions, not solely to increase coverage or assert boilerplate.
- Structure each test with Arrange-Act-Assert: set up inputs, exercise the unit, then assert on the outcome, don't\
  interleave setup and assertions.
- Keep tests small and independent: one behavior per test, no shared mutable state between tests, and no ordering
  dependency between them.
- Isolate the unit under test, mock or fake external dependencies (databases, network, filesystem, other services)
  rather than exercising them for real, unless the test is explicitly an integration test. Then use testcontainers.
- Name tests for the behavior they verify (e.g. `test_returns_empty_list_when_input_is_none`), not for the function
  name alone.
- Cover edge cases explicitly: empty/None inputs, boundary values, and invalid types, not just the happy path.
- Use fixtures (pytest) or setUp/tearDown (unittest) to share setup across tests instead of duplicating it inline.
- Prefer pytest for new Python test suites — parameterization and fixtures make edge-case coverage and setup reuse 
  easier than plain `unittest`.

## Documentation Guidelines
- Update relevant user-facing documentation when behavior, configuration, setup, or workflows change.
- Include only information users need, explain it clearly in plain language, and keep it concise and accurate.
- Always start the documentation with a clear purpose and scope, and include examples of usage when appropriate.
- Documentation should start with a clear table of contents with links to the different sections to simplify looking 
  up certain content.

## Keeping This File Accurate
- After every implementation, verify that AGENTS.md is still accurate. Update it when project structure or workflows
  change.
- If AGENTS.md is generated (see the header of this file), edit the source files instead of the generated output.
