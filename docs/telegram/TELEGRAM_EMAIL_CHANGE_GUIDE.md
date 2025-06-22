# Telegram Email Change Functionality Usage Guide

## 📋 Function Overview

This guide introduces the complete implementation of Telegram email change functionality, including two main steps: email change request and confirmation.

## 🔧 Implementation Files

### Core Implementation

- **`saleor/graphql/account/mutations/authentication/telegram_email_change_request.py`** - Email change request
- **`saleor/graphql/account/mutations/authentication/telegram_email_change_confirm.py`** - Email change confirmation

### Test Files

- **`tests/telegram/test_telegram_email_change_simple.py`** - Simplified test
- **`tests/telegram/test_telegram_email_change_complete.py`** - Complete test

## 🚀 Usage Method

### 1. Email Change Request

```graphql
mutation TelegramEmailChangeRequest($initDataRaw: String!, $newEmail: String!) {
  telegramEmailChangeRequest(initDataRaw: $initDataRaw, newEmail: $newEmail) {
    success
    message
    errors {
      field
      message
      code
    }
  }
}
```

**Parameter Description:**

- `initDataRaw`: Raw data provided by Telegram WebApp
- `newEmail`: New email address

**Return Result:**

- `success`: Whether successful
- `message`: Operation message
- `errors`: Error information (if any)

### 2. Email Change Confirmation

```graphql
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
    success
    message
    user {
      email
      firstName
      lastName
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Parameter Description:**

- `initDataRaw`: Raw data provided by Telegram WebApp
- `oldEmail`: Old email address
- `newEmail`: New email address
- `verificationCode`: Email verification code

**Return Result:**

- `success`: Whether successful
- `message`: Operation message
- `user`: Updated user information
- `errors`: Error information (if any)

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
- Redis cache storage

### 3. Data Consistency

- User ID validation
- Email format validation
- Uniqueness check

## 📝 Usage Examples

### JavaScript Frontend

```javascript
// Email change request
const requestEmailChange = async (initDataRaw, newEmail) => {
  const response = await fetch("/graphql/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: `
        mutation TelegramEmailChangeRequest($initDataRaw: String!, $newEmail: String!) {
          telegramEmailChangeRequest(initDataRaw: $initDataRaw, newEmail: $newEmail) {
            success
            message
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
            success
            message
            user {
              email
              firstName
              lastName
            }
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
