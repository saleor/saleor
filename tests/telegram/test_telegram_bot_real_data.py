#!/usr/bin/env python3
import json
import asyncio
from urllib.parse import parse_qs


async def test_telegram_bot_validation():
    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    print("🧪 开始Telegram WebApp数据验证...")
    print("=" * 60)
    from telegram import Bot
    from telegram.error import TelegramError

    # 验证bot token
    bot = Bot(token=bot_token)
    try:
        bot_info = await bot.get_me()
        print(f"✅ Bot验证通过: {bot_info.first_name} (@{bot_info.username})")
    except TelegramError as e:
        print(f"❌ Bot验证失败: {e}")
        return False

    # 解析init_data_raw
    parsed_data = parse_qs(init_data_raw)
    user_data = parsed_data.get("user", [None])[0]
    if not user_data:
        print("❌ 缺少user数据")
        return False

    user_info = json.loads(user_data)
    print(f"✅ 用户数据: {json.dumps(user_info, ensure_ascii=False, indent=2)}")

    # 检查关键字段
    required_fields = [
        "id",
        "first_name",
        "last_name",
        "username",
        "language_code",
        "photo_url",
    ]
    for field in required_fields:
        if field not in user_info:
            print(f"❌ 缺少字段: {field}")
            return False
    print("✅ 用户字段完整")

    # 检查auth_date, hash等
    for key in ["auth_date", "hash", "chat_instance", "chat_type", "signature"]:
        if key not in parsed_data:
            print(f"❌ 缺少参数: {key}")
            return False
    print("✅ 其他参数完整")

    print("🎉 所有验证通过！")
    return True


if __name__ == "__main__":
    result = asyncio.run(test_telegram_bot_validation())
    print("\n最终测试结果:", "通过" if result else "失败")
