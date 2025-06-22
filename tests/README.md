# Test Directory Structure

This directory contains all test files related to Telegram integration, Redis caching, and email functionality.

## 📁 Directory Structure

### `/telegram/` - Telegram Related Tests

- **Functional Tests**: Telegram Bot validation, user authentication, email change, etc.
- **Integration Tests**: GraphQL mutation tests, API integration tests
- **Validation Tests**: Data validation, format validation, error handling tests

### `/redis/` - Redis Cache Tests

- **Cache Tests**: Redis connection tests, data storage and retrieval tests
- **Integration Tests**: Django cache integration tests
- **Performance Tests**: Cache performance and optimization tests

### `/email/` - Email Functionality Tests

- **SMTP Tests**: Email server configuration tests
- **Sending Tests**: Email sending functionality tests
- **Configuration Tests**: Environment variable and configuration tests

## 🧪 Test Types

### Unit Tests

- Test individual functions and methods
- Mock external dependencies
- Fast execution and isolated testing

### Integration Tests

- Test component interactions
- Use real database and cache
- Validate end-to-end functionality

### Functional Tests

- Test complete user workflows
- Validate business logic
- Ensure feature completeness

## 🚀 Running Tests

### Run All Tests

```bash
# Run all tests in the directory
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=saleor
```

### Run Specific Test Categories

```bash
# Run Telegram tests only
python -m pytest tests/telegram/

# Run Redis tests only
python -m pytest tests/redis/

# Run Email tests only
python -m pytest tests/email/
```

### Run Individual Test Files

```bash
# Run specific test file
python -m pytest tests/telegram/test_telegram_validation.py

# Run with specific test function
python -m pytest tests/telegram/test_telegram_validation.py::test_telegram_validation
```

## 📋 Test Configuration

### Environment Setup

```bash
# Set test environment variables
export TESTING=True
export TELEGRAM_BOT_TOKEN="test_bot_token"
export EMAIL_URL="smtp://test:test@localhost:587"
export REDIS_URL="redis://localhost:6379/1"
```

### Test Database

- Tests use separate test database
- Database is created and destroyed for each test run
- No data persistence between test runs

### Mock Services

- External services are mocked in unit tests
- Real services used in integration tests
- Configurable mock behavior

## 🔧 Test Utilities

### Common Test Functions

```python
# Create test user
def create_test_user(email="test@example.com"):
    return User.objects.create_user(
        email=email,
        password="testpass123",
        first_name="Test",
        last_name="User"
    )

# Create test Telegram data
def create_test_telegram_data(user_id=123456789):
    return {
        "id": user_id,
        "first_name": "Test",
        "username": "testuser",
        "language_code": "en"
    }
```

### Test Fixtures

- Reusable test data and objects
- Defined in `conftest.py` files
- Automatically available to test functions

## 📊 Test Coverage

### Coverage Requirements

- Minimum 80% code coverage
- Critical paths must be fully covered
- Error handling paths must be tested

### Coverage Reports

```bash
# Generate coverage report
python -m pytest tests/ --cov=saleor --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Check Python path and module structure
2. **Database Errors**: Ensure test database is properly configured
3. **Environment Issues**: Verify environment variables are set correctly

### Debug Commands

```bash
# Run tests with debug output
python -m pytest tests/ -v -s

# Run single test with debugger
python -m pytest tests/telegram/test_telegram_validation.py::test_telegram_validation -s --pdb
```

## 📝 Writing Tests

### Test Structure

```python
def test_function_name():
    """Test description"""
    # Arrange - Set up test data
    test_data = create_test_data()

    # Act - Execute function being tested
    result = function_under_test(test_data)

    # Assert - Verify results
    assert result is not None
    assert result.status == "success"
```

### Best Practices

1. **Descriptive Names**: Use clear, descriptive test function names
2. **Single Responsibility**: Each test should test one thing
3. **Independent**: Tests should not depend on each other
4. **Fast**: Tests should run quickly
5. **Reliable**: Tests should be deterministic

### Test Data

- Use factories for creating test objects
- Keep test data minimal and focused
- Use realistic but simple data

## 🔍 Test Categories

### Telegram Tests

- **Validation Tests**: Test data validation logic
- **Authentication Tests**: Test user authentication flow
- **Integration Tests**: Test GraphQL mutations
- **Error Tests**: Test error handling scenarios

### Redis Tests

- **Connection Tests**: Test Redis connectivity
- **Storage Tests**: Test data storage and retrieval
- **Expiration Tests**: Test cache expiration logic
- **Performance Tests**: Test cache performance

### Email Tests

- **Configuration Tests**: Test email configuration
- **Sending Tests**: Test email sending functionality
- **Template Tests**: Test email templates
- **Error Tests**: Test email error handling

## 📈 Continuous Integration

### CI Configuration

- Tests run automatically on code changes
- Coverage reports generated automatically
- Test results reported to development team

### Pre-commit Hooks

- Tests run before code commits
- Prevents broken code from being committed
- Ensures code quality standards

## 🎯 Test Goals

### Quality Assurance

- Ensure code works as expected
- Prevent regressions
- Validate business requirements

### Documentation

- Tests serve as living documentation
- Show how to use the code
- Provide examples of expected behavior

### Confidence

- Enable safe refactoring
- Support continuous deployment
- Reduce production issues

## 📚 Related Documentation

### Test Documentation

- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage Documentation](https://coverage.readthedocs.io/)

### Project Documentation

- [Telegram Integration](docs/telegram/)
- [Redis Integration](docs/redis/)
- [Email Configuration](docs/email/)

## 🤝 Contributing

### Adding Tests

1. Write tests for new features
2. Ensure existing tests pass
3. Update test documentation
4. Submit pull request

### Test Review

- All new code must have tests
- Tests must pass before merging
- Coverage must meet requirements
- Tests must follow best practices
