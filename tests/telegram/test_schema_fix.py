#!/usr/bin/env python3
"""
测试GraphQL schema构建是否正常
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

try:
    django.setup()
    print("✓ Django设置成功")
except Exception as e:
    print(f"✗ Django设置失败: {e}")
    sys.exit(1)

try:
    from saleor.graphql.api import schema

    print("✓ GraphQL schema构建成功")
    print(f"  Schema类型: {type(schema)}")
except Exception as e:
    print(f"✗ GraphQL schema构建失败: {e}")
    sys.exit(1)

try:
    # 测试导入我们的mutation
    from saleor.graphql.account.mutations.authentication.telegram_email_change_request import (
        TelegramEmailChangeRequest,
    )
    from saleor.graphql.account.mutations.authentication.telegram_email_change_confirm import (
        TelegramEmailChangeConfirm,
    )

    print("✓ Telegram邮箱变更mutation导入成功")
except Exception as e:
    print(f"✗ Telegram邮箱变更mutation导入失败: {e}")
    sys.exit(1)

print("\n🎉 所有测试通过！GraphQL schema构建正常。")
