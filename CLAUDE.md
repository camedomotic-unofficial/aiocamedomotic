# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIOCameDomotic is a Python library that provides an asynchronous API for interacting with CAME Domotic home automation systems. The library abstracts away the complexity of the CAME API, offers automatic session management, and is primarily developed for integration with Home Assistant but usable independently.

## Build & Development Commands

- Install with dependencies: `poetry install`
- Install with specific groups: `poetry install --with tests,code-quality,docs`
- Run tests: `pytest`
- Run specific test: `pytest tests/aiocamedomotic/test_auth.py::TestAuthInit::test_init`
- Run tests with coverage: `pytest --cov=aiocamedomotic --cov-report=term-missing --cov-report=html`
- Format code: `ruff format aiocamedomotic tests` (CI checks with `ruff format aiocamedomotic --check`)
- Lint code: `ruff check aiocamedomotic` and `pylint aiocamedomotic tests` (CI runs `pylint --disable=W,R,C aiocamedomotic`)
- Type check: `mypy aiocamedomotic`
- Build docs: `cd docs && make html` (or `python -m sphinx -b html source build/html` if `make` is unavailable)

## Code Style Guidelines

- **License headers**: Every new source file (code, tests, docs, config, workflows) starts with the two-line SPDX header, in the file's native comment style. Do not use the long Apache boilerplate — the full license text lives only in `LICENSE`. Python/YAML/TOML example:

  ```python
  # SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
  # SPDX-License-Identifier: Apache-2.0
  ```

  (RST files use `..` comments, Markdown uses a `<!-- ... -->` block.)
- **Imports**: Standard library first, third-party next, project imports last
- **Formatting**: `ruff format` (Black-compatible style), line length 88, 4-space indentation
- **Types**: Use type hints for all functions, return values, and parameters
- **Naming**:
  - Classes: PascalCase (e.g., `CameDomoticAPI`)
  - Functions/methods: snake_case, async methods prefixed with `async_`
  - Private methods: prefixed with underscore (e.g., `_attempt_login`)
  - Constants: UPPER_SNAKE_CASE (typically in const.py)
- **Error Handling**: Custom exceptions from base `CameDomoticError`, specific try/except blocks
- **Documentation**: Docstrings for all public classes/methods with parameters, return values, and exceptions. When adding a new model module, export its public names in `aiocamedomotic/models/__init__.py` (imports plus sorted `__all__`): `docs/source/api_reference.rst` documents the models package through a single `.. automodule:: aiocamedomotic.models` directive, so do **not** add per-module `.. automodule::` entries
- **Testing**: Pytest with mocks, fixtures, parameterization, and freezegun for time-dependent tests
- **Comments**: never mention in comments of code, commits, PRs, etc. that have been generated with the help of Claude or any other AI tool

## Project Architecture

- **Core Components**:
  - `CameDomoticAPI` (in came_domotic_api.py): Main interface for interacting with CAME Domotic systems
  - `Auth` (in auth.py): Handles authentication and session management with the CAME API
  - Device Models (in models/*.py): Represent different types of devices with their operations
  - Error Classes (in errors.py): Custom exceptions for different failure scenarios
- **Asynchronous Design**: Library uses asyncio and aiohttp for non-blocking operations
- **Data Flow**: API client authenticates via Auth module → interacts with devices via appropriate models

## Project Structure

- Core API: `aiocamedomotic/came_domotic_api.py`
- Authentication: `aiocamedomotic/auth.py`
- Models: `aiocamedomotic/models/*.py`
- Error Classes: `aiocamedomotic/errors.py`

## Branch naming convention

To allow proper autolabeling of changes, please name your branches as follows:

- `feature/*` or `features/*`: for feature enhancements or new features
- `fix/*`: for fixes to existing features
- `test/*` or `tests/*`: for changes to the unit tests or their configuration
- `doc/*` or `docs/*`: for changes to the documentation
- `action/*` or `actions/*`: for changes to the CI/CD pipelines
- `chore/*`: for any other change not directly related to a user feature

## Exception Hierarchy

All custom exceptions inherit from `CameDomoticError` (in errors.py):

- `CameDomoticServerNotFoundError`: Host not available
- `CameDomoticAuthError`: Authentication failures (ACK codes 1, 3)
- `CameDomoticServerError`: Other server errors; includes `create_ack_error()` factory method

## Unit Test Conventions

- **Test organization**: Tests are grouped into classes by feature area (e.g., `TestAuthLogin`, `TestAPILights`, `TestLight`). Each test method takes `self` as the first parameter.
- **Fixtures**: All shared fixtures live in `tests/aiocamedomotic/conftest.py`. Do not define fixtures elsewhere.
- **Reference data**: `mocked_requests.py` and `mocked_responses.py` are reference files documenting real API request/response formats. Do not modify, reorder, or add edge-case variants to them. Import from `mocked_responses.py` for happy-path tests; keep edge-case test data inline in the test file.
- **One concern per test**: Each test function should verify a single scenario. Do not combine "empty list" and "missing key" into one test.
- **Mocking pattern**: Use `@patch.object(Auth, "method_name")` decorators on test methods. With `@patch` decorators on class methods, the mock is injected before the fixture parameters (e.g., `async def test_foo(self, mock_send_command, auth_instance)`).
- **Async tests**: pytest-asyncio is configured in `auto` mode (`asyncio_mode = "auto"` in pyproject.toml), so `async def` tests run automatically without `@pytest.mark.asyncio` for tests discovered inside classes. Use `@pytest.mark.asyncio` only for standalone async test functions.

## Testing with Real Servers

Tests can run against a real CAME Domotic server (skipped by default):

1. Copy `tests/aiocamedomotic/test_config.ini.example` to `test_config.ini`
2. Fill in server credentials (host, username, password)
3. Set `RUN_TESTS_ON_REAL_SERVER = True` in `test_real.py`
4. Run: `pytest tests/aiocamedomotic/test_real.py -v`

**Never commit** `test_config.ini` or leave `RUN_TESTS_ON_REAL_SERVER = True`.

## API Reference

The full documentation of the CAME Domotic API that this library wraps is in `local_only/llms.md` (summary) and `local_only/llms-full.md` (full details).

## LLM Documentation Files

The files `llms.txt` and `llms-full.txt` are auto-generated by a GitHub Action (`build-llms-docs.yml`) after merging to `main`. Do not edit them manually.

## Publishing a New Release

When the user asks to publish a new release of the library, follow this process:

1. **Propose the version bump first**: Before launching anything, review the changes since the last release (e.g., `git log <last-tag>..main --oneline` and the merged PRs) and the project's release history, then ask the user whether to cut a **minor**, **patch**, or — as a residual case — **major** version, stating which one you recommend and why. Follow semantic versioning: bug fixes and dependency bumps → patch; new features or new device support → minor; breaking API changes → major.
2. **Launch the workflow**: Run the `Build and publish` workflow (`.github/workflows/build-publish.yml`) on the `main` branch, e.g.:

   ```bash
   gh workflow run build-publish.yml --ref main \
     -f version=<patch|minor|major> \
     -f publish_to_test=true \
     -f publish_to_production=true
   ```

   By default, set both `publish_to_test` and `publish_to_production` to `true` unless the user requests otherwise. The workflow bumps the version in `pyproject.toml` (via an auto-merged PR), tags the release, builds the package, publishes to TestPyPI/PyPI, and creates a **draft** GitHub release with auto-generated notes.
3. **Rewrite the release notes**: Once the workflow has completed and the draft release exists, edit the draft on GitHub (e.g., `gh release edit <tag> --notes-file ...`) to rewrite its description from the point of view of the **end user of the library**: explain what changed in terms of features, fixes, and behavior they will notice, rather than listing raw commits or internal chores. Keep the contributor/changelog links that GitHub generated. Leave the release as a draft unless the user explicitly asks to publish it.

## Other notes

- The `main` git branch is protected, to merge you must create a new branch and raise a PR
- Never mention in comments (commits, PRs, etc.) Claude or any other AI tool
- Python 3.12, 3.13 and 3.14 are supported
- Library is available under Apache License 2.0
