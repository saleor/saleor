/* eslint-disable */
const CheckerPlugin = require('fork-ts-checker-webpack-plugin');

module.exports = (baseConfig, env, config) => {
  config.module.rules.push({
    test: /\.tsx?$/,
    exclude: /node_modules/,
    loader: "ts-loader",
    options: {
      experimentalWatchApi: true,
      transpileOnly: true
    }
  });
  config.optimization.removeAvailableModules = false;
  config.optimization.removeEmptyChunks = false;
  config.optimization.splitChunks = false;
  config.resolve.extensions.push(".ts", ".tsx");
  config.plugins.push(new CheckerPlugin());
  return config;
};
