# CLAUDE.md - AIOCameDomotic Helper

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

## Project Structure
- Core API: `aiocamedomotic/came_domotic_api.py`
- Authentication: `aiocamedomotic/auth.py`
- Models: `aiocamedomotic/models/*.py`
- Constants: `aiocamedomotic/const.py`
- Error Classes: `aiocamedomotic/errors.py`