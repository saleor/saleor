#!/usr/bin/env node
/**
 * Test Telegram WebApp data validation
 */

import validate from "@nanhanglim/validate-telegram-webapp-data";

// Real bot token
const botToken = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA";

// Real initDataRaw data
const realInitDataRaw =
  "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D" +
  "&chat_instance=6755980278051609308" +
  "&chat_type=sender" +
  "&auth_date=1738051266" +
  "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ" +
  "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c";

console.log("🧪 Testing @nanhanglim/validate-telegram-webapp-data...");
console.log("=".repeat(60));
console.log(`🤖 Bot Token: ${botToken.substring(0, 20)}...`);
console.log(`📦 Init Data Raw: ${realInitDataRaw.substring(0, 100)}...`);
console.log();

try {
  console.log("🚀 Validating with real data...");
  const result = validate(realInitDataRaw, botToken);
  console.log("✅ Validation successful!");
  console.log("📋 Result:", result);

  // Test with wrong bot token
  console.log("\n🧪 Testing with wrong bot token...");
  const wrongResult = validate(realInitDataRaw, "wrong_bot_token");
  console.log("❌ Should have failed with wrong token");
} catch (error) {
  console.log("❌ Validation failed:", error.message);

  // Test with wrong bot token
  console.log("\n🧪 Testing with wrong bot token...");
  try {
    const wrongResult = validate(realInitDataRaw, "wrong_bot_token");
    console.log("❌ Should have failed with wrong token");
  } catch (wrongError) {
    console.log("✅ Correctly rejected wrong bot token:", wrongError.message);
  }
}
