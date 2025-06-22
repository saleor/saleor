#!/usr/bin/env python3
"""
Environment variable management script
Supports reading from .env file in development environment and container environment variables in production
"""

import os
import sys
from pathlib import Path
from typing import Optional


class EnvConfig:
    """Environment variable configuration manager"""

    def __init__(self, env_file_path: str = ".env"):
        self.env_file_path = env_file_path
        self.is_production = self._is_production_environment()

    def load_env_file(self) -> bool:
        """Load environment variables from .env file"""
        if not os.path.exists(self.env_file_path):
            print(f"⚠ .env file does not exist: {self.env_file_path}")
            return False

        try:
            with open(self.env_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Set environment variable (if not already set)
                        if key and not os.environ.get(key):
                            os.environ[key] = value

            print(
                f"✓ Successfully loaded environment variables from {self.env_file_path}"
            )
            return True

        except Exception as e:
            print(f"✗ Failed to load .env file: {e}")
            return False

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value"""
        return os.environ.get(key, default)

    def set_env(self, key: str, value: str) -> None:
        """Set environment variable"""
        os.environ[key] = value

    def _is_production_environment(self) -> bool:
        """Determine if it's a production environment"""
        # Check common production environment indicators
        production_indicators = [
            "PRODUCTION",
            "STAGING",
            "DEPLOYMENT",
            "DOCKER",
            "KUBERNETES",
            "AWS",
            "GCP",
            "AZURE",
        ]

        for indicator in production_indicators:
            if os.environ.get(indicator):
                return True

        return False

    def setup_environment(self) -> bool:
        """Setup environment based on current environment type"""
        if self.is_production:
            print(
                "🔧 Production environment detected, using container environment variables"
            )
            return True
        else:
            print("🔧 Development environment detected, loading from .env file")
            return self.load_env_file()


def main():
    """Main function"""
    print("🚀 Starting environment configuration...")

    # Initialize environment configuration
    env_config = EnvConfig()

    # Setup environment
    success = env_config.setup_environment()

    if success:
        print("✅ Environment configuration completed successfully")

        # Display key environment variables
        print("\n📋 Key Environment Variables:")
        key_vars = ["TELEGRAM_BOT_TOKEN", "EMAIL_URL", "REDIS_URL", "DATABASE_URL"]
        for var in key_vars:
            value = env_config.get_env(var)
            if value:
                # Mask sensitive values
                if "PASSWORD" in var or "TOKEN" in var or "SECRET" in var:
                    masked_value = (
                        value[:8] + "*" * (len(value) - 12) + value[-4:]
                        if len(value) > 12
                        else "***"
                    )
                    print(f"   {var}: {masked_value}")
                else:
                    print(f"   {var}: {value}")
            else:
                print(f"   {var}: Not set")
    else:
        print("❌ Environment configuration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
