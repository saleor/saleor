const path = require("path");
const merge = require("webpack-merge");

const baseConfig = require("./config/webpack/config.base");
const devConfig = require("./config/webpack/config.dev");
const prodConfig = require("./config/webpack/config.prod");
const workerConfig = require("./config/webpack/config.worker");

const sourceDir = path.join(__dirname, "./src");
const distDir = path.join(__dirname, "./dist");

module.exports = (env, argv) => {
  const devMode = argv.mode !== "production";
  const sw = !!argv["service-worker"];
  const paths = { sourceDir, distDir };

  const base = baseConfig(paths);
  const worker = workerConfig(paths);
  const dev = sw
    ? merge(base, worker, devConfig(paths))
    : merge(base, devConfig(paths));
  const prod = merge(base, worker, prodConfig(paths));

  return devMode ? dev : prod;
};
