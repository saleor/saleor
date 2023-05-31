import { defineConfig } from "vitest/config";
import { config as dotenvConfig } from "dotenv";

dotenvConfig({ path: ".env.local" });
export default defineConfig({
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["dotenv/config"],
  },
});
