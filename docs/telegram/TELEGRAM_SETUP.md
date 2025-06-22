# Telegram Bot Configuration Guide

## Environment Variable Configuration

To use Telegram authentication functionality, you need to configure the following environment variables in Django settings:

### 1. Add Configuration in settings.py

```python
# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
```

### 2. Environment Variable Setup

#### Development Environment (.env file)

```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Other required environment variables
EMAIL_URL=smtp://username:password@host:port/?tls=True
REDIS_URL=redis://localhost:6379/0
```

#### Production Environment

```bash
# Set in container environment variables
TELEGRAM_BOT_TOKEN=your_bot_token_here
EMAIL_URL=smtp://username:password@host:port/?tls=True
REDIS_URL=redis://redis:6379/0
```

## Getting Telegram Bot Token

1. Find @BotFather in Telegram
2. Send `/newbot` command
3. Follow the prompts to set bot name and username
4. BotFather will return a token, format similar to: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

## Usage Method

### GraphQL Mutation

```graphql
mutation TelegramTokenCreate($initDataRaw: String!) {
  telegramTokenCreate(initDataRaw: $initDataRaw) {
    token
    refreshToken
    csrfToken
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

### Frontend Call Example

```javascript
// Get initDataRaw from Telegram Web App
const initDataRaw = window.Telegram.WebApp.initData;

// Call GraphQL mutation
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
                    user { email firstName lastName }
                }
            }
        `,
    variables: { initDataRaw },
  }),
});

const result = await response.json();
const token = result.data.telegramTokenCreate.token;
```

## Testing

### Run Tests

```bash
# Run unit tests
python manage.py test saleor.graphql.account.tests.mutations.authentication.test_telegram_token_create

# Run real data tests
python manage.py test saleor.graphql.account.tests.mutations.authentication.test_telegram_token_create_real_data

# Run independent validation tests
python tests/telegram/test_telegram_validation.py
```

### Test Configuration

```bash
# Set test environment variables
export TELEGRAM_BOT_TOKEN="test_bot_token_123456789"
export EMAIL_URL="smtp://test:test@localhost:587"
export REDIS_URL="redis://localhost:6379/1"
```

## Troubleshooting

### Common Issues

1. **Invalid Bot Token**

   - Ensure `TELEGRAM_BOT_TOKEN` is set correctly
   - Verify the token is valid with Telegram API

2. **Data Validation Failures**

   - Check that initDataRaw is properly formatted
   - Ensure the data hasn't been tampered with

3. **User Creation Issues**
   - Check database permissions
   - Verify email generation logic

### Debug Steps

1. Run validation tests: `python tests/telegram/test_telegram_validation.py`
2. Check environment variables: `echo $TELEGRAM_BOT_TOKEN`
3. Review Django logs for detailed error messages
4. Test with real Telegram WebApp data

## Security Considerations

### Bot Token Protection

- Store bot token securely in environment variables
- Never commit bot token to version control
- Use different tokens for development and production

### Data Validation

- All Telegram data is cryptographically verified
- Uses HMAC-SHA256 for signature verification
- Prevents data tampering and forgery

### User Isolation

- Telegram users get unique email addresses
- Prevents conflicts with existing users
- Maintains data integrity

## Deployment

### Requirements

- Python 3.8+
- Django 3.2+
- `python-telegram-bot` library
- Valid Telegram Bot Token

### Environment Setup

```bash
# Install dependencies
pip install python-telegram-bot

# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Run tests to verify setup
python tests/telegram/test_telegram_validation.py
```

### Production Deployment

1. Set `TELEGRAM_BOT_TOKEN` in production environment
2. Ensure Redis is available for caching
3. Configure email settings for notifications
4. Run full test suite before deployment

## Monitoring

### Logs

- Monitor authentication attempts
- Track validation failures
- Log user creation events

### Metrics

- Response times for authentication
- Success/failure rates
- User creation statistics

### Alerts

- Set up alerts for validation failures
- Monitor bot token validity
- Track error rates

## Best Practices

### Development

- Use test bot tokens for development
- Enable detailed logging
- Run tests frequently

### Production

- Use production bot tokens
- Monitor performance and errors
- Keep dependencies updated

### Maintenance

- Regularly check bot status
- Monitor API usage
- Update documentation as needed
