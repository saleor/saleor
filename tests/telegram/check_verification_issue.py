#!/usr/bin/env python3
"""
分析验证码问题的脚本
"""

import json
import urllib.parse
from datetime import datetime


def decode_init_data(init_data_raw):
    """解码initDataRaw获取Telegram用户信息"""
    try:
        # URL解码
        decoded = urllib.parse.unquote(init_data_raw)
        print(f"✅ URL解码成功")
        print(f"   解码后长度: {len(decoded)}")

        # 解析参数
        params = {}
        for param in decoded.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value

        # 解析user参数
        if "user" in params:
            user_str = urllib.parse.unquote(params["user"])
            print(f"✅ 解析user参数: {user_str}")

            # 尝试解析JSON
            try:
                user_data = json.loads(user_str)
                telegram_id = user_data.get("id")
                print(f"✅ 获取Telegram ID: {telegram_id}")
                return telegram_id
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return None
        else:
            print(f"❌ 未找到user参数")
            return None

    except Exception as e:
        print(f"❌ 解码失败: {e}")
        return None


def analyze_error_response():
    """分析错误响应"""
    print("🔍 分析错误响应...")

    error_response = {
        "data": {
            "telegramEmailChangeConfirm": {
                "user": None,
                "success": False,
                "errors": [
                    {
                        "field": "verification_code",
                        "message": "{'verification_code': ['No pending email change request found']}",
                        "code": "INVALID",
                    }
                ],
            }
        }
    }

    print(f"✅ 错误分析:")
    print(f"   错误字段: verification_code")
    print(f"   错误代码: INVALID")
    print(f"   错误消息: No pending email change request found")
    print(f"   用户: null")
    print(f"   成功: false")

    return error_response


def identify_possible_causes():
    """识别可能的原因"""
    print("\n🔍 识别可能的原因...")

    causes = [
        {
            "原因": "验证码已过期",
            "描述": "验证码有10分钟有效期，可能已经过期",
            "解决方案": "重新调用 telegramEmailChangeRequest mutation",
        },
        {
            "原因": "验证码已被使用",
            "描述": "验证码只能使用一次，使用后会被清除",
            "解决方案": "重新调用 telegramEmailChangeRequest mutation",
        },
        {
            "原因": "验证码不匹配",
            "描述": "传入的验证码与Redis中存储的验证码不匹配",
            "解决方案": "检查邮箱中的验证码是否正确",
        },
        {
            "原因": "Redis连接问题",
            "描述": "Redis服务未运行或连接配置错误",
            "解决方案": "检查Redis服务状态和配置",
        },
        {
            "原因": "用户不存在",
            "描述": "对应的Telegram用户不存在于数据库中",
            "解决方案": "先创建用户或检查用户创建流程",
        },
        {
            "原因": "请求流程中断",
            "描述": "没有先调用 telegramEmailChangeRequest mutation",
            "解决方案": "先调用请求mutation，再调用确认mutation",
        },
    ]

    print(f"📋 可能的原因:")
    for i, cause in enumerate(causes, 1):
        print(f"   {i}. {cause['原因']}")
        print(f"      描述: {cause['描述']}")
        print(f"      解决方案: {cause['解决方案']}")
        print()

    return causes


def check_workflow():
    """检查完整的工作流程"""
    print("\n🔍 检查完整的工作流程...")

    workflow = [
        {
            "步骤": "1. 用户登录",
            "描述": "用户通过Telegram WebApp登录",
            "状态": "✅ 已完成",
        },
        {
            "步骤": "2. 发起邮箱变更请求",
            "描述": "调用 telegramEmailChangeRequest mutation",
            "状态": "❓ 需要确认",
        },
        {
            "步骤": "3. 发送验证码邮件",
            "描述": "系统发送验证码到新邮箱",
            "状态": "❓ 需要确认",
        },
        {
            "步骤": "4. 用户输入验证码",
            "描述": "用户在新邮箱中获取验证码",
            "状态": "✅ 已完成",
        },
        {
            "步骤": "5. 确认邮箱变更",
            "描述": "调用 telegramEmailChangeConfirm mutation",
            "状态": "❌ 失败",
        },
    ]

    print(f"📋 工作流程检查:")
    for step in workflow:
        print(f"   {step['步骤']}: {step['状态']}")
        print(f"      描述: {step['描述']}")
        print()

    return workflow


def provide_solutions():
    """提供解决方案"""
    print("\n🔍 提供解决方案...")

    solutions = [
        {
            "方案": "方案1: 重新发起邮箱变更请求",
            "步骤": [
                "1. 调用 telegramEmailChangeRequest mutation",
                "2. 检查邮箱是否收到新的验证码",
                "3. 使用新验证码调用 telegramEmailChangeConfirm",
            ],
            "适用场景": "验证码过期或已被使用",
        },
        {
            "方案": "方案2: 检查Redis服务",
            "步骤": [
                "1. 确认Redis服务正在运行",
                "2. 检查Redis连接配置",
                "3. 验证Django缓存设置",
            ],
            "适用场景": "Redis连接问题",
        },
        {
            "方案": "方案3: 检查用户状态",
            "步骤": [
                "1. 确认用户存在于数据库中",
                "2. 检查用户邮箱格式",
                "3. 验证用户权限",
            ],
            "适用场景": "用户不存在或权限问题",
        },
        {
            "方案": "方案4: 调试模式测试",
            "步骤": ["1. 启用详细日志", "2. 逐步调试验证流程", "3. 检查每个步骤的状态"],
            "适用场景": "需要深入调试",
        },
    ]

    print(f"💡 解决方案:")
    for i, solution in enumerate(solutions, 1):
        print(f"   {solution['方案']}")
        print(f"      适用场景: {solution['适用场景']}")
        print(f"      步骤:")
        for step in solution["步骤"]:
            print(f"        {step}")
        print()

    return solutions


def create_test_scenario():
    """创建测试场景"""
    print("\n🔍 创建测试场景...")

    test_scenario = {
        "步骤1": {
            "mutation": "telegramEmailChangeRequest",
            "参数": {
                "initDataRaw": "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D",
                "oldEmail": "telegram_5861990984@telegram.local",
                "newEmail": "88888888@qq.com",
            },
            "期望结果": "发送验证码邮件到新邮箱",
        },
        "步骤2": {
            "mutation": "telegramEmailChangeConfirm",
            "参数": {
                "initDataRaw": "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D",
                "verificationCode": "新验证码",
                "oldEmail": "telegram_5861990984@telegram.local",
                "newEmail": "88888888@qq.com",
            },
            "期望结果": "邮箱变更成功，返回用户信息和token",
        },
    }

    print(f"🧪 测试场景:")
    for step_name, step_data in test_scenario.items():
        print(f"   {step_name}: {step_data['mutation']}")
        print(f"      期望结果: {step_data['期望结果']}")
        print()

    return test_scenario


def main():
    """主分析函数"""
    print("🔍 开始分析验证码问题...")
    print("=" * 70)

    # 测试参数
    init_data_raw = "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D"
    verification_code = "251404"
    old_email = "telegram_5861990984@telegram.local"
    new_email = "88888888@qq.com"

    print(f"📋 问题参数:")
    print(f"   验证码: {verification_code}")
    print(f"   旧邮箱: {old_email}")
    print(f"   新邮箱: {new_email}")

    # 1. 解码initDataRaw
    print(f"\n🔍 步骤1: 解码initDataRaw")
    print("-" * 50)
    telegram_id = decode_init_data(init_data_raw)

    if not telegram_id:
        print("❌ 无法获取Telegram ID，分析终止")
        return

    # 2. 分析错误响应
    print(f"\n🔍 步骤2: 分析错误响应")
    print("-" * 50)
    analyze_error_response()

    # 3. 识别可能的原因
    print(f"\n🔍 步骤3: 识别可能的原因")
    print("-" * 50)
    identify_possible_causes()

    # 4. 检查工作流程
    print(f"\n🔍 步骤4: 检查工作流程")
    print("-" * 50)
    check_workflow()

    # 5. 提供解决方案
    print(f"\n🔍 步骤5: 提供解决方案")
    print("-" * 50)
    provide_solutions()

    # 6. 创建测试场景
    print(f"\n🔍 步骤6: 创建测试场景")
    print("-" * 50)
    create_test_scenario()

    print(f"\n" + "=" * 70)
    print(f"📊 分析总结:")
    print(f"=" * 70)
    print(f"   Telegram ID: {telegram_id}")
    print(f"   问题: 验证码数据不存在或已过期")
    print(f"   主要原因: 需要重新发起邮箱变更请求")

    print(f"\n💡 立即行动:")
    print(f"   1. 重新调用 telegramEmailChangeRequest mutation")
    print(f"   2. 检查邮箱 88888888@qq.com 是否收到验证码")
    print(f"   3. 使用新验证码调用 telegramEmailChangeConfirm")
    print(f"   4. 确保在10分钟内完成验证")


if __name__ == "__main__":
    main()
