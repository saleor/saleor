#!/usr/bin/env python3
"""
测试修复后的 Telegram 认证功能
"""

import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

import django

django.setup()

from django.test import override_settings
from saleor.graphql.account.mutations.authentication.telegram_token_create import (
    validate_telegram_data,
)


def test_telegram_data_validation():
    """测试 Telegram 数据验证"""

    # 你提供的 initDataRaw 数据
    init_data_raw = "auth_date=1750755749&hash=f4ad8d5f2aedb3445a71f6f315abcdcd8a8b7b17fe295660399e142f0708fb2f&signature=&start_param=&user=%7B%22added_to_attachment_menu%22%3Afalse%2C%22allows_write_to_pm%22%3Afalse%2C%22first_name%22%3A%221645481993%22%2C%22id%22%3A1645481993%2C%22is_bot%22%3Afalse%2C%22is_premium%22%3Afalse%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22Sven%28Mi%29%22%2C%22language_code%22%3A%22zh%22%2C%22photo_url%22%3A%22%22%2C%22provider%22%3A%22matrix%22%2C%22extra%22%3A%7B%22hs%22%3A%22mt.social%22%7D%7D"

    print("=" * 60)
    print("测试 Telegram 数据验证")
    print("=" * 60)
    print(f"原始数据: {init_data_raw}")
    print()

    try:
        # 使用模拟的 bot token 进行测试
        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_for_validation"):
            result = validate_telegram_data(init_data_raw)
            print("✅ 验证成功!")
            print(
                f"用户信息: {json.dumps(result['user'], indent=2, ensure_ascii=False)}"
            )
            print(f"认证日期: {result['auth_date']}")
            print(f"聊天实例: {result.get('chat_instance', 'N/A')}")
            print(f"聊天类型: {result.get('chat_type', 'N/A')}")
            print(f"签名: {result.get('signature', 'N/A')}")

    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

        # 如果是 ValidationError，显示详细信息
        if hasattr(e, "message_dict"):
            print("详细错误信息:")
            for field, errors in e.message_dict.items():
                print(f"  {field}: {errors}")
        elif hasattr(e, "message"):
            print(f"错误消息: {e.message}")


def test_parse_init_data():
    """测试解析 initDataRaw 数据"""
    from urllib.parse import parse_qs, unquote

    init_data_raw = "auth_date=1750755749&hash=f4ad8d5f2aedb3445a71f6f315abcdcd8a8b7b17fe295660399e142f0708fb2f&signature=&start_param=&user=%7B%22added_to_attachment_menu%22%3Afalse%2C%22allows_write_to_pm%22%3Afalse%2C%22first_name%22%3A%221645481993%22%2C%22id%22%3A1645481993%2C%22is_bot%22%3Afalse%2C%22is_premium%22%3Afalse%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22Sven%28Mi%29%22%2C%22language_code%22%3A%22zh%22%2C%22photo_url%22%3A%22%22%2C%22provider%22%3A%22matrix%22%2C%22extra%22%3A%7B%22hs%22%3A%22mt.social%22%7D%7D"

    print("=" * 60)
    print("测试数据解析")
    print("=" * 60)

    # URL 解码
    decoded_data = unquote(init_data_raw)
    print(f"解码后数据: {decoded_data}")
    print()

    # 解析参数
    parsed_data = parse_qs(decoded_data)
    print("解析后的参数:")
    for key, values in parsed_data.items():
        print(f"  {key}: {values[0] if values else 'None'}")
    print()

    # 检查必需参数
    required_params = ["auth_date", "hash", "signature"]
    missing_params = []

    for param in required_params:
        if param not in parsed_data:
            missing_params.append(param)
        elif not parsed_data[param][0]:
            print(f"⚠️  参数 {param} 存在但为空")

    if missing_params:
        print(f"❌ 缺少必需参数: {missing_params}")
    else:
        print("✅ 所有必需参数都存在")

    # 检查可选参数
    optional_params = ["chat_instance", "chat_type"]
    for param in optional_params:
        if param in parsed_data:
            print(f"✅ 可选参数 {param}: {parsed_data[param][0]}")
        else:
            print(f"⚠️  可选参数 {param} 不存在")


if __name__ == "__main__":
    print("开始测试 Telegram 认证修复...")
    print()

    test_parse_init_data()
    print()
    test_telegram_data_validation()

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
