# Telegram Email Change Updated Implementation Guide

## 📋 Implementation Overview

This guide introduces the updated implementation of Telegram email change functionality with enhanced Redis integration and improved security features.

## 🔧 Updated Implementation Files

### Core Implementation

- **`saleor/graphql/account/mutations/authentication/telegram_email_change_request.py`** - Enhanced email change request with Redis storage
- **`saleor/graphql/account/mutations/authentication/telegram_email_change_confirm.py`** - Enhanced email change confirmation with Redis validation

### Test Files

- **`tests/telegram/test_telegram_email_change_simple.py`** - Updated integration test
- **`tests/telegram/test_telegram_email_change_complete.py`** - Complete workflow test

## 🚀 Enhanced Features

### 1. Redis Integration

**Storage Method**: Redis cache with automatic expiration

```python
def store_verification_code_in_redis(telegram_id, old_email, new_email, verification_code, user_id):
    """Store verification code in Redis with 10-minute expiration"""
    cache_data = {
        'verification_code': verification_code,
        'old_email': old_email,
        'new_email': new_email,
        'telegram_id': telegram_id,
        'user_id': user_id,
        'created_at': timezone.now().isoformat(),
        'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
    }
    redis_cache.set(cache_key, cache_data, timeout=600)
```

### 2. Enhanced Security

**Data Integrity Validation**:

```python
def validate_verification_data_integrity(cache_data, telegram_id, user):
    """Validate completeness and consistency of verification code data"""
    # Telegram ID consistency check
    # User ID consistency check
    # Email format validation
    # Data integrity verification
```

### 3. Improved Error Handling

**Comprehensive Error Types**:

- Telegram validation errors
- Redis connection errors
- Email configuration errors
- Verification code errors
- Data integrity errors

## 📧 Email Configuration

### Environment Variable Configuration

## Required Environment Variables

```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Email Configuration (using EMAIL_URL)
EMAIL_URL=smtp://username:password@host:port/?tls=True

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

## Development Environment Configuration

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export EMAIL_URL="smtp://username:password@host:port/?tls=True"
export REDIS_URL="redis://localhost:6379/0"
```

## Production Environment Configuration

```bash
# Set in container environment
TELEGRAM_BOT_TOKEN=your_bot_token_here
EMAIL_URL=smtp://username:password@host:port/?tls=True
REDIS_URL=redis://redis:6379/0
```

## 🔧 Configuration Steps

### 1. Environment Setup

```bash
# Set required environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export EMAIL_URL="smtp://username:password@host:port/?tls=True"
export REDIS_URL="redis://localhost:6379/0"
```

### 2. Service Restart

```bash
# Restart Django service to apply new configuration
python manage.py runserver
```

### 3. Test Configuration

```bash
# Run test script to verify configuration
python tests/telegram/test_telegram_email_change_simple.py
```

## 🛡️ Security Features

### 1. Telegram Data Validation

- HMAC-SHA256 signature verification
- Bot token validation
- User data integrity check

### 2. Email Verification

- 6-digit verification code generation
- 10-minute expiration time
- Redis cache storage with user association

### 3. Data Consistency

- User ID validation
- Email format validation
- Uniqueness check

## 📝 Usage Examples

### JavaScript Frontend

```javascript
// Email change request
const requestEmailChange = async (initDataRaw, oldEmail, newEmail) => {
  const response = await fetch("/graphql/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: `
        mutation TelegramEmailChangeRequest(
          $initDataRaw: String!
          $oldEmail: String!
          $newEmail: String!
        ) {
          telegramEmailChangeRequest(
            initDataRaw: $initDataRaw
            oldEmail: $oldEmail
            newEmail: $newEmail
          ) {
            user {
              email
              firstName
              lastName
            }
            verificationCode
            expiresAt
            errors {
              field
              message
              code
            }
          }
        }
      `,
      variables: {
        initDataRaw,
        oldEmail,
        newEmail,
      },
    }),
  });

  return response.json();
};

// Email change confirmation
const confirmEmailChange = async (
  initDataRaw,
  oldEmail,
  newEmail,
  verificationCode
) => {
  const response = await fetch("/graphql/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: `
        mutation TelegramEmailChangeConfirm(
          $initDataRaw: String!
          $oldEmail: String!
          $newEmail: String!
          $verificationCode: String!
        ) {
          telegramEmailChangeConfirm(
            initDataRaw: $initDataRaw
            oldEmail: $oldEmail
            newEmail: $newEmail
            verificationCode: $verificationCode
          ) {
            user {
              email
              firstName
              lastName
            }
            success
            token
            errors {
              field
              message
              code
            }
          }
        }
      `,
      variables: {
        initDataRaw,
        oldEmail,
        newEmail,
        verificationCode,
      },
    }),
  });

  return response.json();
};
```

## 🔍 Troubleshooting

### Common Issues

1. **SMTP Configuration Error**

   - Check EMAIL_URL format
   - Verify SMTP credentials
   - Test email sending manually

2. **Redis Connection Error**

   - Check REDIS_URL configuration
   - Verify Redis service is running
   - Test Redis connection

3. **Telegram Validation Error**
   - Check TELEGRAM_BOT_TOKEN
   - Verify bot token is valid
   - Check initDataRaw format

### Debug Commands

```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $EMAIL_URL
echo $REDIS_URL

# Test Redis connection
redis-cli ping

# Test email configuration
python tests/email/test_smtp_config.py
```

## 📚 Additional Resources

- [Telegram WebApp Documentation](https://core.telegram.org/bots/webapps)
- [Saleor GraphQL Documentation](https://docs.saleor.io/docs/3.x/developer/graphql-api)
- [Django Email Configuration](https://docs.djangoproject.com/en/stable/topics/email/)
