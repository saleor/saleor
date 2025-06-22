# Script Directory Structure

This directory contains all scripts related to Telegram integration, email configuration, and environment setup.

## 📁 Directory Structure

### `/telegram/` - Telegram Related Scripts

- **Configuration Scripts**: Telegram Bot configuration, environment variable setup
- **Deployment Scripts**: Automated deployment, service startup, monitoring scripts
- **Maintenance Scripts**: Data cleanup, log analysis, performance optimization

### `/email/` - Email Functionality Scripts

- **SMTP Configuration Scripts**: Mail server configuration, environment variable setup
- **Email Test Scripts**: Email sending test, configuration verification
- **Monitoring Scripts**: Email service monitoring, error reporting

## 🔧 Script Description

### Telegram Scripts

- `setup_telegram_bot.sh` - Telegram Bot configuration script
- `deploy_telegram_service.sh` - Telegram service deployment script
- `monitor_telegram.sh` - Telegram service monitoring script

### Email Scripts

- `setup_gmail_smtp.sh` - Gmail SMTP configuration script
- `setup_qq_smtp.sh` - QQ email SMTP configuration script
- `test_email_config.sh` - Email configuration test script
- `env_config.py` - Environment configuration management script

## 🚀 Usage Method

### Configuration Scripts

```bash
# Configure Telegram Bot
source scripts/telegram/setup_telegram_bot.sh

# Configure Gmail SMTP
source scripts/email/setup_gmail_smtp.sh

# Configure QQ email SMTP
source scripts/email/setup_qq_smtp.sh
```

### Deployment Scripts

```bash
# Deploy Telegram service
bash scripts/telegram/deploy_telegram_service.sh

# Start monitoring
bash scripts/telegram/monitor_telegram.sh
```

### Test Scripts

```bash
# Test email configuration
bash scripts/email/test_email_config.sh

# Run environment configuration
python scripts/email/env_config.py
```

## 📋 Script Function

### Configuration Script Function

- **Environment Variable Setup**: Automatically set necessary environment variables
- **Configuration Verification**: Verify the correctness and completeness of configuration
- **Error Handling**: Provide detailed error information and solution suggestions

### Deployment Script Function

- **Automated Deployment**: One-click deployment of related services
- **Service Management**: Start, stop, restart services
- **Health Check**: Check service operation status

### Monitoring Script Function

- **Performance Monitoring**: Monitor service performance and resource usage
- **Error Reporting**: Collect and report error information
- **Log Analysis**: Analyze log files to provide statistical information

## 🔍 Script Parameters

### General Parameters

- `--help` - Display help information
- `--verbose` - Detailed output mode
- `--dry-run` - Trial run mode, no actual operation
- `--config` - Specify configuration file path

### Specific Parameters

- `--bot-token` - Telegram Bot Token
- `--email-host` - SMTP server address
- `--email-user` - Email username
- `--email-password` - Email password

## 📝 Configuration Example

### Telegram Configuration

```bash
#!/bin/bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_WEBHOOK_URL="https://your-domain.com/webhook"
export TELEGRAM_SECRET_TOKEN="your_secret_token"
```

### Email Configuration

```bash
#!/bin/bash
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_HOST_USER="your_email@gmail.com"
export EMAIL_HOST_PASSWORD="your_app_password"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
```

## 🔧 Fault Tolerance

### Common Problems

1. **Permission Problem**: Ensure that the script has execution permission `chmod +x script.sh`
2. **Path Problem**: Ensure that the script is run in the correct directory
3. **Dependency Problem**: Ensure that the required dependencies are installed

### Debugging Method

- Use `--verbose` parameter to get detailed output
- Check the return value and error information of the script
- View related log files

## 📚 Related Documentation

### Configuration Documentation

- **Telegram Configuration**: `docs/telegram/TELEGRAM_SETUP.md`
- **Email Configuration**: `docs/email/EMAIL_CONFIG_GUIDE.md`
- **Environment Configuration**: `docs/telegram/TELEGRAM_DEPLOYMENT_CHECKLIST.md`

### Test Documentation

- **Script Test**: `tests/telegram/` and `tests/email/`
- **Integration Test**: View documentation in each test directory

## 🤝 Contribution Guide

### Script Development

- Use bash or Python to write scripts
- Add detailed comments and documentation
- Implement error handling and parameter verification
- Provide usage examples and test cases

### Script Maintenance

- Periodically update scripts to meet new needs
- Fix known problems and bugs
- Optimize script performance and reliability
- Maintain script backward compatibility

# Environment Variable Configuration

## Required Environment Variables

```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Email configuration (using EMAIL_URL)
EMAIL_URL=smtp://username:password@host:port/?tls=True

# Redis configuration
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
