#!/bin/bash

# Saleor Gmail SMTP Configuration Script
# This script is used to set Gmail SMTP environment variables

echo "🚀 Setting up Gmail SMTP configuration..."

# Set EMAIL_URL environment variable (recommended method)
export EMAIL_URL="smtp://ikun.ldea@gmail.com:mxrracprjnuunwwd@smtp.gmail.com:587/?tls=True"

echo "✅ EMAIL_URL has been set"
echo "EMAIL_URL: $EMAIL_URL"

# Verify environment variable
if [ -n "$EMAIL_URL" ]; then
    echo "✅ EMAIL_URL environment variable set successfully"
else
    echo "❌ EMAIL_URL environment variable setting failed"
    exit 1
fi

# Display configuration information
echo ""
echo "📧 Gmail SMTP Configuration Information:"
echo "   SMTP Server: smtp.gmail.com"
echo "   Port: 587"
echo "   TLS: Enabled"
echo "   Username: ikun.ldea@gmail.com"
echo "   Password: [Set]"

# Test configuration
echo ""
echo "🧪 Testing configuration..."
echo "To test the configuration, please run:"
echo "python tests/email/test_gmail_smtp.py"

# Show permanent setup commands
echo ""
echo "💡 To permanently set environment variables, add the following command to ~/.bashrc or ~/.zshrc:"
echo "export EMAIL_URL=\"smtp://ikun.ldea@gmail.com:mxrracprjnuunwwd@smtp.gmail.com:587/?tls=True\""

echo ""
echo "✨ Gmail SMTP configuration setup completed!"
