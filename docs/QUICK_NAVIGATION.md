# Quick Navigation Guide

## 🚀 Quick Start

### New User Onboarding

1. **Understand Features**: `docs/telegram/TELEGRAM_SETUP.md`
2. **View Examples**: `docs/telegram/TELEGRAM_USAGE_EXAMPLES.md`
3. **Run Tests**: `tests/telegram/simple_telegram_test_final.py`

### Developer Guide

1. **Implementation Details**: `docs/telegram/TELEGRAM_INTEGRATION_FINAL_SUMMARY.md`
2. **API Documentation**: `docs/telegram/TELEGRAM_EMAIL_CHANGE_GUIDE.md`
3. **Test Cases**: `tests/telegram/test_telegram_mutation_integration.py`

## 📁 Core File Locations

### Telegram Features

- **Main Implementation**: `saleor/graphql/account/mutations/authentication/`
- **Core Tests**: `tests/telegram/test_telegram_core_validation.py`
- **Integration Tests**: `tests/telegram/test_telegram_integration.py`
- **Usage Guide**: `docs/telegram/TELEGRAM_EMAIL_CHANGE_GUIDE.md`

### Redis Cache

- **Cache Implementation**: `saleor/core/cache/`
- **Redis Tests**: `tests/redis/test_redis_integration.py`
- **Verification Code Tests**: `tests/redis/test_redis_user_email_association.py`
- **Integration Documentation**: `docs/redis/REDIS_INTEGRATION_FINAL_SUMMARY.md`

### Email Features

- **Email Scripts**: `scripts/email/`
- **Email Tests**: `tests/email/`
- **Email Configuration Guide**: `docs/email/README.md`

## 🔧 Common Operations

### Run Tests

```bash
# Run all Telegram tests
python -m pytest tests/telegram/

# Run Redis cache tests
python -m pytest tests/redis/

# Run email feature tests
python -m pytest tests/email/

# Run simplified test
python tests/telegram/simple_telegram_test_final.py
```

### Configure Environment

```bash
# Configure Gmail SMTP
source scripts/email/setup_gmail_smtp.sh

# Configure environment variables
python scripts/email/env_config.py

# Check email configuration
python tests/email/check_saleor_email_config.py
```

### Debug Issues

```bash
# Debug Telegram email change
python tests/telegram/debug_telegram_email_change.py

# Debug Redis verification code
python tests/redis/debug_redis_verification.py

# Check verification code issue
python tests/telegram/check_verification_issue.py
```

## 📚 Documentation Navigation

### By Feature Category

- **Telegram Integration**: `docs/telegram/`
- **Redis Cache**: `docs/redis/`
- **Email Feature**: `docs/email/`

### By Type Category

- **Setup Guide**: `*SETUP.md`
- **Usage Guide**: `*GUIDE.md`
- **Implementation Summary**: `*IMPLEMENTATION*.md`
- **Deployment Checklist**: `*DEPLOYMENT*.md`

### By Stage Category

- **Development Stage**: `*IMPLEMENTATION*.md`
- **Testing Stage**: `*TEST*.md`
- **Deployment Stage**: `*DEPLOYMENT*.md`
- **Maintenance Stage**: `*SUMMARY*.md`

## 🎯 Common Tasks

### Add New Feature

1. Implement GraphQL mutation in `saleor/graphql/`
2. Add test cases in `tests/telegram/`
3. Update documentation in `docs/telegram/`
4. Add configuration scripts in `scripts/`

### Fix Issues

1. Diagnose using `debug_*.py` files
2. Run related tests to verify fixes
3. Update documentation to explain fixes
4. Add regression tests to prevent recurrence

### Deploy Updates

1. Check `*DEPLOYMENT*.md` documentation
2. Run pre-deployment tests
3. Use configuration scripts to set up environment
4. Verify deployed features

## 🔍 Search Techniques

### By File Name Search

```bash
# Find all Telegram-related files
find . -name "*telegram*" -type f

# Find all test files
find tests/ -name "test_*.py"

# Find all documentation files
find docs/ -name "*.md"
```

### By Content Search

```bash
# Search Telegram-related code
grep -r "telegram" saleor/graphql/

# Search Redis-related code
grep -r "redis" saleor/core/

# Search email-related code
grep -r "email" saleor/plugins/
```

## 📞 Get Help

### Documentation Resources

- **Project README**: `README.md`
- **Testing Instructions**: `tests/README.md`
- **Documentation Instructions**: `docs/README.md`
- **Script Instructions**: `scripts/README.md`

### Troubleshooting

- **Common Issues**: Check README files in each directory
- **Error Diagnosis**: Use `debug_*.py` scripts
- **Configuration Check**: Use `check_*.py` scripts

### Contact Support

- Check `CONTRIBUTING.md` for contribution guidelines
- Check `SECURITY.md` for security policies
- Refer to `CHANGELOG.md` for version changes
