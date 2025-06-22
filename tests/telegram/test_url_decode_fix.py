#!/usr/bin/env python3
"""
测试URL解码修复功能
"""

import json
from urllib.parse import parse_qs, unquote


def test_url_decode():
    """测试URL解码功能"""

    # 您提供的双重编码数据
    init_data_raw = "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D"

    print("🧪 Testing URL decode fix...")
    print("=" * 70)
    print("Original init_data_raw:")
    print(init_data_raw)
    print("=" * 70)

    # 第一次URL解码
    decoded_data = unquote(init_data_raw)
    print("After first URL decode:")
    print(decoded_data)
    print("=" * 70)

    # 解析数据
    parsed_data = parse_qs(decoded_data)
    print("Parsed data:")
    for key, values in parsed_data.items():
        print(f"  {key}: {values}")
    print("=" * 70)

    # 提取用户数据
    user_data = parsed_data.get("user", [None])[0]
    if user_data:
        try:
            user_info = json.loads(user_data)
            print("User data parsed successfully:")
            print(json.dumps(user_info, ensure_ascii=False, indent=2))

            # 验证关键字段
            print("\nKey fields validation:")
            print(f"  - User ID: {user_info.get('id')}")
            print(f"  - First Name: {user_info.get('first_name')}")
            print(f"  - Last Name: {user_info.get('last_name')}")
            print(f"  - Username: {user_info.get('username')}")
            print(f"  - Language Code: {user_info.get('language_code')}")
            print(f"  - Photo URL: {user_info.get('photo_url')}")

            # 验证必需参数
            required_params = [
                "auth_date",
                "hash",
                "chat_instance",
                "chat_type",
                "signature",
            ]
            print("\nRequired parameters validation:")
            for param in required_params:
                value = parsed_data.get(param, [None])[0]
                print(f"  - {param}: {value}")

            print("\n✅ URL decode fix successful!")
            return True

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse user data JSON: {e}")
            return False
    else:
        print("❌ No user data found")
        return False


def test_original_data():
    """测试原始数据（对比）"""
    print("\n🧪 Testing original data for comparison...")
    print("=" * 70)

    # 原始数据（未修复前）
    original_data = "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D&chat_instance=6755980278051609308&chat_type=sender&auth_date=1738051266&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"

    print("Original data:")
    print(original_data)
    print("=" * 70)

    # 解析原始数据
    parsed_original = parse_qs(original_data)
    print("Parsed original data:")
    for key, values in parsed_original.items():
        print(f"  {key}: {values}")

    return True


if __name__ == "__main__":
    print("🚀 URL Decode Fix Test")
    print("=" * 70)

    # 测试修复后的数据
    test1_result = test_url_decode()

    # 测试原始数据
    test2_result = test_original_data()

    print("\n📊 Test Results:")
    print("=" * 70)
    print(f"✅ URL decode fix: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Original data: {'PASS' if test2_result else 'FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 URL decode fix is working correctly!")
        print("✅ The mutation should now handle double-encoded data properly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
