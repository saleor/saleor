/* eslint-disable */
const { CheckerPlugin } = require("awesome-typescript-loader")

module.exports = (baseConfig, env, config) => {
  config.module.rules.push({
    test: /\.tsx?$/,
    exclude: /node_modules/,
    loader: "awesome-typescript-loader",
    options: {
      reportFiles: [
        "saleor/**/*.{ts,tsx}"
      ],
      useCache: true
    }
  });
  config.resolve.extensions.push(".ts", ".tsx");
  config.plugins.push(new CheckerPlugin());
  return config;
};
