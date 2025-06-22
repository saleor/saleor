#!/usr/bin/env python3
"""
调试Telegram邮箱变更问题
分析为什么找不到待处理的邮箱变更请求
"""

import json
import hmac
import hashlib
from urllib.parse import parse_qs, unquote
from datetime import datetime, timedelta


def decode_init_data_raw(init_data_raw):
    """解码initDataRaw并分析内容"""
    print("=== 解码initDataRaw ===")
    print(f"原始数据长度: {len(init_data_raw)}")

    # 第一次解码
    first_decode = unquote(init_data_raw)
    print(f"第一次解码后长度: {len(first_decode)}")

    # 检查是否还需要第二次解码
    if "%" in first_decode:
        second_decode = unquote(first_decode)
        print(f"第二次解码后长度: {len(second_decode)}")
        final_data = second_decode
    else:
        final_data = first_decode

    print(f"最终解码结果: {final_data[:200]}...")

    # 解析参数
    try:
        params = parse_qs(final_data)
        print("\n解析的参数:")
        for key, values in params.items():
            if key == "user":
                try:
                    user_data = json.loads(values[0])
                    print(f"  {key}: {user_data}")
                    return user_data
                except json.JSONDecodeError:
                    print(f"  {key}: {values[0]}")
            else:
                print(f"  {key}: {values[0] if values else ''}")
    except Exception as e:
        print(f"解析参数失败: {e}")

    return None


def simulate_verification_cache():
    """模拟验证码缓存逻辑"""
    print("\n=== 模拟验证码缓存逻辑 ===")

    # 模拟内存存储
    verification_codes = {}

    # 模拟存储验证码
    telegram_id = 5861990984
    old_email = "telegram_5861990984@telegram.local"
    new_email = "88888888@qq.com"
    verification_code = "624421"

    cache_key = f"email_change_verification:{telegram_id}"
    cache_data = {
        "verification_code": verification_code,
        "old_email": old_email,
        "new_email": new_email,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
    }

    verification_codes[cache_key] = cache_data
    print(f"存储验证码: {cache_key}")
    print(f"缓存数据: {cache_data}")

    # 模拟查找验证码
    stored_data = verification_codes.get(cache_key)
    if stored_data:
        print(f"✅ 找到缓存数据")
        print(f"   验证码: {stored_data['verification_code']}")
        print(f"   旧邮箱: {stored_data['old_email']}")
        print(f"   新邮箱: {stored_data['new_email']}")
        print(f"   过期时间: {stored_data['expires_at']}")

        # 检查是否过期
        expires_at = datetime.fromisoformat(
            stored_data["expires_at"].replace("Z", "+00:00")
        )
        if datetime.now() > expires_at:
            print("❌ 验证码已过期")
        else:
            print("✅ 验证码未过期")
    else:
        print("❌ 未找到缓存数据")

    return verification_codes


def check_actual_cache():
    """检查实际的缓存状态"""
    print("\n=== 检查实际缓存状态 ===")

    try:
        # 尝试导入实际的缓存模块
        import sys
        import os

        sys.path.append(os.path.join(os.getcwd(), "saleor"))

        from graphql.account.mutations.authentication.telegram_email_change_request import (
            _verification_codes,
            _verification_lock,
        )

        with _verification_lock:
            print(f"当前缓存中的键: {list(_verification_codes.keys())}")

            # 查找特定用户的缓存
            telegram_id = 5861990984
            cache_key = f"email_change_verification:{telegram_id}"

            if cache_key in _verification_codes:
                cache_data = _verification_codes[cache_key]
                print(f"✅ 找到用户缓存: {cache_data}")
            else:
                print(f"❌ 未找到用户缓存: {cache_key}")

                # 显示所有缓存内容
                print("所有缓存内容:")
                for key, data in _verification_codes.items():
                    print(f"  {key}: {data}")

    except ImportError as e:
        print(f"无法导入缓存模块: {e}")
    except Exception as e:
        print(f"检查缓存失败: {e}")


def analyze_problem():
    """分析问题原因"""
    print("\n=== 问题分析 ===")

    print("可能的原因:")
    print("1. 验证码已过期（10分钟有效期）")
    print("2. 缓存键不匹配")
    print("3. 请求邮箱变更和确认邮箱变更之间有时间间隔")
    print("4. 服务重启导致内存缓存丢失")
    print("5. 清理过期验证码时误删了有效缓存")

    print("\n建议的解决方案:")
    print("1. 重新请求邮箱变更获取新的验证码")
    print("2. 检查缓存键的生成逻辑")
    print("3. 增加缓存持久化（如Redis）")
    print("4. 增加调试日志记录缓存操作")


def main():
    """主函数"""
    print("开始调试Telegram邮箱变更问题")
    print("=" * 60)

    # 解码initDataRaw
    init_data_raw = "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D"

    user_data = decode_init_data_raw(init_data_raw)

    if user_data:
        print(f"\n用户ID: {user_data.get('id')}")
        print(f"用户名: {user_data.get('username')}")
        print(f"姓名: {user_data.get('first_name')} {user_data.get('last_name')}")

    # 模拟验证码缓存
    simulate_verification_cache()

    # 检查实际缓存
    check_actual_cache()

    # 分析问题
    analyze_problem()

    print("\n" + "=" * 60)
    print("调试完成")


if __name__ == "__main__":
    main()
