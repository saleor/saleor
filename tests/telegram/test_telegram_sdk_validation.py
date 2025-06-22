#!/usr/bin/env python3
"""
测试@telegram-apps/sdk的validate函数
"""

import json
import subprocess


def test_telegram_sdk_validation():
    """测试使用@telegram-apps/sdk验证Telegram数据"""

    # 真实的bot token
    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"

    # 真实的initDataRaw数据
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    print("🧪 Testing @telegram-apps/sdk validate function...")
    print("=" * 60)
    print(f"🤖 Bot Token: {bot_token[:20]}...")
    print(f"📦 Init Data Raw: {real_init_data_raw[:100]}...")
    print()

    # 创建Node.js脚本来调用SDK
    node_script = f"""
const {{ validate }} = require('@telegram-apps/sdk');

const initDataRaw = '{real_init_data_raw}';
const botToken = '{bot_token}';

console.log('Testing with real data...');
console.log('initDataRaw length:', initDataRaw.length);
console.log('botToken length:', botToken.length);

try {{
    const result = validate(initDataRaw, botToken);
    console.log('✅ Validation result:', result);
    console.log(JSON.stringify({{ success: true, result }}));
}} catch (error) {{
    console.log('❌ Validation failed:', error.message);
    console.log(JSON.stringify({{ success: false, error: error.message }}));
}}
"""

    try:
        # 执行Node.js脚本
        print("🚀 Executing Node.js script...")
        result = subprocess.run(
            ["node", "-e", node_script], capture_output=True, text=True, timeout=10
        )

        print(f"📊 Return code: {result.returncode}")
        print(f"📤 Stdout: {result.stdout}")
        if result.stderr:
            print(f"📥 Stderr: {result.stderr}")

        if result.returncode != 0:
            print("❌ Node.js execution failed")
            return False

        # 解析结果
        output = result.stdout.strip()
        if not output:
            print("❌ No output from Node.js script")
            return False

        # 查找JSON输出
        lines = output.split("\n")
        json_line = None
        for line in lines:
            if line.startswith("{") and line.endswith("}"):
                json_line = line
                break

        if not json_line:
            print("❌ No JSON output found")
            return False

        try:
            data = json.loads(json_line)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON output: {e}")
            return False

        if data.get("success"):
            print("✅ Telegram validation successful!")
            print(f"📋 Result: {data.get('result')}")
            return True
        else:
            print(f"❌ Telegram validation failed: {data.get('error')}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Node.js execution timeout")
        return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_wrong_bot_token():
    """测试错误的bot token"""
    print("\n🧪 Testing with wrong bot token...")
    print("=" * 60)

    # 错误的bot token
    wrong_bot_token = "wrong_bot_token"

    # 真实的initDataRaw数据
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    # 创建Node.js脚本
    node_script = f"""
const {{ validate }} = require('@telegram-apps/sdk');

const initDataRaw = '{real_init_data_raw}';
const botToken = '{wrong_bot_token}';

try {{
    const result = validate(initDataRaw, botToken);
    console.log(JSON.stringify({{ success: true, result }}));
}} catch (error) {{
    console.log(JSON.stringify({{ success: false, error: error.message }}));
}}
"""

    try:
        result = subprocess.run(
            ["node", "-e", node_script], capture_output=True, text=True, timeout=10
        )

        output = result.stdout.strip()
        if output:
            try:
                data = json.loads(output)
                if not data.get("success"):
                    print("✅ Correctly rejected wrong bot token")
                    return True
                else:
                    print("❌ Should have rejected wrong bot token")
                    return False
            except json.JSONDecodeError:
                print("❌ Invalid JSON output")
                return False
        else:
            print("❌ No output from Node.js script")
            return False

    except Exception as e:
        print(f"❌ Error testing wrong bot token: {e}")
        return False


if __name__ == "__main__":
    print("🚀 @telegram-apps/sdk Validation Test")
    print("=" * 60)

    # 测试真实数据
    test1_result = test_telegram_sdk_validation()

    # 测试错误的bot token
    test2_result = test_wrong_bot_token()

    print("\n📊 Test Results:")
    print("=" * 60)
    print(f"✅ Real data validation: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Wrong token rejection: {'PASS' if test2_result else 'FAIL'}")

    if test1_result and test2_result:
        print(
            "\n🎉 All tests passed! @telegram-apps/sdk validation is working correctly."
        )
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
