# Telegram WebApp Integration Implementation Summary

## Overview

This document summarizes the complete solution for implementing Telegram WebApp user authentication in Saleor, including user query, creation, and token generation functionality.

## Implemented Features

### 1. User Query Functionality

- Store Telegram user ID through the `external_reference` field
- Use format: `telegram_{telegram_id}`
- Support user lookup through GraphQL `customers` query

### 2. User Creation Functionality

- Create users without email verification and password
- Automatically generate unique email: `telegram_{telegram_id}@telegram.local`
- Set random password (users won't use it)
- Use `external_reference` to associate Telegram user ID

### 3. Token Generation Functionality

- Generate JWT access token
- Generate JWT refresh token
- Generate CSRF token
- Support user authentication and session management

## Core Implementation Files

### Main Files

- `saleor/graphql/account/mutations/authentication/telegram_token_create.py`

### Key Features

#### 1. Telegram Data Validation

```python
async def validate_telegram_data_async(init_data_raw, bot_token):
    """Use python-telegram-bot to asynchronously validate Telegram initDataRaw data"""
    # Support double URL encoding parsing
    decoded_data = unquote(init_data_raw)
    parsed_data = parse_qs(decoded_data)
    # Validate user data and required parameters
```

#### 2. User Lookup

```python
@classmethod
def find_user_by_telegram_id(cls, telegram_id):
    """Find user by telegram_id"""
    try:
        user = models.User.objects.get(external_reference=f"telegram_{telegram_id}")
        return user
    except models.User.DoesNotExist:
        return None
```

#### 3. User Creation

```python
@classmethod
def create_user_without_email_password(cls, telegram_data):
    """Create user without email and password"""
    user_info = telegram_data['user']
    telegram_id = user_info['id']

    email = f"telegram_{telegram_id}@telegram.local"
    external_reference = f"telegram_{telegram_id}"

    user = models.User.objects.create(
        email=email,
        first_name=user_info.get('first_name', ''),
        last_name=user_info.get('last_name', ''),
        is_active=True,
        is_confirmed=True,
        external_reference=external_reference,
        password=make_password(random_password)
    )
```

#### 4. Token Generation

```python
@classmethod
def generate_token_for_user(cls, user):
    """Generate token and refresh token for user"""
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    csrf_token = _get_new_csrf_token()

    return {
        'token': access_token,
        'refresh_token': refresh_token,
        'csrf_token': csrf_token
    }
```

## GraphQL Mutation

### Interface Definition

```graphql
mutation TelegramTokenCreate($initDataRaw: String!) {
  telegramTokenCreate(initDataRaw: $initDataRaw) {
    token
    refreshToken
    csrfToken
    user {
      id
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

### Usage Example

```javascript
const response = await fetch("/graphql/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: `
      mutation TelegramTokenCreate($initDataRaw: String!) {
        telegramTokenCreate(initDataRaw: $initDataRaw) {
          token
          refreshToken
          csrfToken
          user {
            id
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
      initDataRaw: window.Telegram.WebApp.initDataRaw,
    },
  }),
});
```

## Data Storage Structure

### User Table Fields

- `email`: `telegram_{telegram_id}@telegram.local`
- `external_reference`: `telegram_{telegram_id}`
- `first_name`: Telegram user first name
- `last_name`: Telegram user last name
- `is_active`: `True`
- `is_confirmed`: `True`

### Private Metadata

```json
{
  "telegram_id": 123456789,
  "telegram_username": "username",
  "telegram_language_code": "zh-CN",
  "telegram_photo_url": "https://...",
  "bot_info": {
    "id": 123456789,
    "first_name": "BotName",
    "username": "botusername"
  },
  "chat_instance": "chat_instance_id",
  "chat_type": "private",
  "auth_date": "1234567890",
  "created_via_telegram": true
}
```

## Configuration Requirements

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```
