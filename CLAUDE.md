# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIOCameDomotic is an unofficial Python library that provides an asynchronous API for interacting with CAME Domotic home automation systems. The library abstracts away the complexity of the CAME API, offers automatic session management, and is primarily developed for integration with Home Assistant but usable independently.

## Build & Development Commands

- Install with dependencies: `poetry install`
- Install with specific groups: `poetry install --with tests,code-quality,docs`
- Run tests: `pytest`
- Run specific test: `pytest tests/aiocamedomotic/test_auth.py::test_init`
- Run tests with coverage: `pytest --cov=aiocamedomotic --cov-report=term-missing --cov-report=html`
- Format code: `black .`
- Lint code: `pylint aiocamedomotic tests`
- Type check: `mypy aiocamedomotic`
- Build docs: `cd docs && make html`

## Code Style Guidelines

- **Imports**: Standard library first, third-party next, project imports last
- **Formatting**: Black with default settings, 4-space indentation
- **Types**: Use type hints for all functions, return values, and parameters
- **Naming**:
  - Classes: PascalCase (e.g., `CameDomoticAPI`)
  - Functions/methods: snake_case, async methods prefixed with `async_`
  - Private methods: prefixed with underscore (e.g., `_attempt_login`)
  - Constants: UPPER_SNAKE_CASE (typically in const.py)
- **Error Handling**: Custom exceptions from base `CameDomoticError`, specific try/except blocks
- **Documentation**: Docstrings for all public classes/methods with parameters, return values, and exceptions
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

## Testing with Real Servers

Tests can run against a real CAME Domotic server (skipped by default):

1. Copy `tests/aiocamedomotic/test_config.ini.example` to `test_config.ini`
2. Fill in server credentials (host, username, password)
3. Set `SKIP_TESTS_ON_REAL_SERVER = False` in `test_real.py`
4. Run: `pytest tests/aiocamedomotic/test_real.py -v`

**Never commit** `test_config.ini` or leave `SKIP_TESTS_ON_REAL_SERVER = False`.

## Other notes

- The `master` git branch is protected, to merge you must create a new branch and raise a PR
- Never mention in comments (commits, PRs, etc.) Claude or any other AI tool
- Python 3.12 and 3.13 are supported
- Library is available under Apache License 2.0
