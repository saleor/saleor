# Testing

## Running tests

- Run tests using `pytest`
- Attach `--reuse-db` argument to speed up tests by reusing the test database
- Select tests to run by passing test file path as an argument
- Enter virtual environment before executing tests

## Writing tests

- Use given/when/then structure for clarity
- Use `pytest` fixtures for setup and teardown
- Declare test suites flat in file. Do not wrapp in classes
