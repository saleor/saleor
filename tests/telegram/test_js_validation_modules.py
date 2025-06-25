#!/usr/bin/env python3
"""
Test various JavaScript modules for Telegram validation
"""

import json
import subprocess
import sys
import os


def test_js_module(module_name, test_function):
    """Test a JavaScript module for Telegram validation"""
    print(f"🧪 Testing {module_name}...")

    # Create Node.js script
    node_script = f"""
{test_function}

// Test data
const botToken = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA";
const initDataRaw = "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D&chat_instance=6755980278051609308&chat_type=sender&auth_date=1738051266&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c";

try {{
    const result = testValidation(initDataRaw, botToken);
    console.log(JSON.stringify({{ success: true, result }}));
}} catch (error) {{
    console.log(JSON.stringify({{ success: false, error: error.message }}));
}}
"""

    # Write script to temporary file
    script_path = f"/tmp/test_{module_name.replace('/', '_')}.js"
    with open(script_path, "w") as f:
        f.write(node_script)

    try:
        # Run Node.js script
        result = subprocess.run(
            ["node", script_path], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return {"available": False, "error": f"Node.js error: {result.stderr}"}

        # Parse result
        try:
            data = json.loads(result.stdout.strip())
            return {"available": True, "result": data}
        except json.JSONDecodeError:
            return {
                "available": False,
                "error": f"Invalid JSON response: {result.stdout}",
            }

    except subprocess.TimeoutExpired:
        return {"available": False, "error": "Timeout"}
    except FileNotFoundError:
        return {"available": False, "error": "Node.js not found"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def test_telegram_apps_sdk():
    """Test @telegram-apps/sdk"""
    test_function = """
const { validate } = require('@telegram-apps/sdk');

function testValidation(initDataRaw, botToken) {
    return validate(initDataRaw, botToken);
}
"""
    return test_js_module("@telegram-apps/sdk", test_function)


def test_validate_telegram_webapp_data():
    """Test @nanhanglim/validate-telegram-webapp-data"""
    test_function = """
const validate = require('@nanhanglim/validate-telegram-webapp-data');

function testValidation(initDataRaw, botToken) {
    return validate(initDataRaw, botToken);
}
"""
    return test_js_module("@nanhanglim/validate-telegram-webapp-data", test_function)


def test_telegram_webapp_validation():
    """Test telegram-webapp-validation"""
    test_function = """
const { validate } = require('telegram-webapp-validation');

function testValidation(initDataRaw, botToken) {
    return validate(initDataRaw, botToken);
}
"""
    return test_js_module("telegram-webapp-validation", test_function)


def test_custom_hmac_implementation():
    """Test custom HMAC implementation in JavaScript"""
    test_function = """
const crypto = require('crypto');

function validateTelegramData(initDataRaw, botToken) {
    // Parse initDataRaw
    const params = new URLSearchParams(initDataRaw);
    const hash = params.get('hash');

    if (!hash) {
        throw new Error('Missing hash parameter');
    }

    // Remove hash and sort parameters
    params.delete('hash');
    const sortedParams = Array.from(params.entries()).sort();

    // Create data check string
    const dataCheckString = sortedParams.map(([key, value]) => `${key}=${value}`).join('\\n');

    // Calculate HMAC-SHA256
    const secretKey = crypto.createHmac('sha256', 'WebAppData').update(botToken).digest();
    const calculatedHash = crypto.createHmac('sha256', secretKey).update(dataCheckString).digest('hex');

    // Verify hash
    if (calculatedHash !== hash) {
        throw new Error('Invalid signature');
    }

    // Parse user data
    const userData = JSON.parse(params.get('user') || '{}');

    return {
        valid: true,
        user: userData,
        auth_date: params.get('auth_date'),
        chat_instance: params.get('chat_instance'),
        chat_type: params.get('chat_type')
    };
}

function testValidation(initDataRaw, botToken) {
    return validateTelegramData(initDataRaw, botToken);
}
"""
    return test_js_module("custom-hmac", test_function)


def main():
    """Test all available JavaScript modules"""
    print("🔍 Testing JavaScript modules for Telegram validation")
    print("=" * 60)

    modules = [
        ("@telegram-apps/sdk", test_telegram_apps_sdk),
        (
            "@nanhanglim/validate-telegram-webapp-data",
            test_validate_telegram_webapp_data,
        ),
        ("telegram-webapp-validation", test_telegram_webapp_validation),
        ("Custom HMAC Implementation", test_custom_hmac_implementation),
    ]

    results = {}

    for module_name, test_func in modules:
        print(f"\n📦 Testing {module_name}...")
        result = test_func()
        results[module_name] = result

        if result["available"]:
            print(f"   ✅ Available")
            if result["result"].get("success"):
                print(f"   ✅ Validation successful")
            else:
                print(f"   ❌ Validation failed: {result['result'].get('error')}")
        else:
            print(f"   ❌ Not available: {result['error']}")

    print("\n📊 Summary:")
    print("=" * 60)

    available_modules = []
    for module_name, result in results.items():
        status = "✅ Available" if result["available"] else "❌ Not available"
        print(f"   {module_name}: {status}")

        if result["available"]:
            available_modules.append(module_name)

    print(f"\n🎯 Available modules: {len(available_modules)}")
    for module in available_modules:
        print(f"   - {module}")

    if available_modules:
        print(
            f"\n💡 Recommendation: Use '{available_modules[0]}' for JavaScript validation"
        )
    else:
        print(
            f"\n⚠️  No JavaScript modules available. Stick with Python implementation."
        )


if __name__ == "__main__":
    main()
